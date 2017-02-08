###playback.py
### a function to play back frequency data (and log events to plexon)

import BMI_RN as br
import os
from multiprocessing import Process, Value, Array
import time


##a dictionary of global variables
global_vars = {
	"samp_int":0,
	"smooth_int":0,
	"timeout":0,
	"timeout_pause":0,
	"reward_time":1000,
	"abet_dev":1,
	"t1_port":(2,0),
	"t2_port":(2,1),
	"start_trigger":(0,0),
	"video_trigger":(0,1),
	"trial_trigger":(0,2),
	"t1_event":11,
	"t2_event":12,
	"miss_event":10,
	"log_file":r"D:\data\log.txt"
}

##trigger the nidaq channels to make sure they are set at 0
br.trig_nidaq(global_vars['abet_dev'],global_vars['start_trigger'][0],global_vars['start_trigger'][1])
br.trig_nidaq(global_vars['abet_dev'],global_vars['video_trigger'][0],global_vars['video_trigger'][1])
br.trig_nidaq(global_vars['abet_dev'],global_vars['trial_trigger'][0],global_vars['trial_trigger'][1])
br.trig_nidaq(global_vars['abet_dev'],global_vars['t1_port'][0],global_vars['t1_port'][1])
br.trig_nidaq(global_vars['abet_dev'],global_vars['t2_port'][0],global_vars['t2_port'][1])

##global state variable to be shared between processes
engage = Value('i', 0)

###A function to set the variables in the global variables dictionary
def set_globals(samp_int,smooth_int,timeout,timeout_pause,log_file):
	global global_vars
	global_vars["samp_int"] = samp_int
	global_vars["smooth_int"] = smooth_int
	global_vars["timeout"] = timeout
	global_vars["timeout_pause"] = timeout_pause
	global_vars["log_file"] = os.path.normpath(log_file)

##a sub-function to parse a single line in a log, 
##and return the cursor val and frequency components seperately.
def read_line(string):
	label = None
	timestamp = None
	if string is not '':
		##figure out where the comma is that separates
		##the timestamp and the event label
		comma_idx = string.index(',')
		##the cursor val is everything in front of the comma
		cval = string[:comma_idx]
		##the frequency is everything after but not the return character
		freq = string[comma_idx+1:-1]
	return float(cval), float(freq)

###A function to spawn a process to run the playback. Input args are taken from start_BMI
def start_playback(samp_int,smooth_int,timeout,timeout_pause,log_file):
	global engage
	##activate the state variable
	engage.value=1
	##set the global variables
	set_globals(samp_int,smooth_int,timeout,timeout_pause,log_file)
	##initialize the process to run the playback function
	playback_p = Process(target=playback,args=(global_vars,engage))
	##start the process
	playback_p.start()
	##trigger the recording
	br.trig_nidaq_ex(global_vars['abet_dev'],global_vars['start_trigger'][0],global_vars['start_trigger'][1],100)
	br.trig_nidaq_ex(global_vars['abet_dev'],global_vars['video_trigger'][0],global_vars['video_trigger'][1],100)

###a function to stop playback
def stop_playback():
	global engage
	engage.value = 0


### a function to run the simulation. Meant to be run in a separate process.
def playback(var_dict,engage_var):
	log = open(var_dict["log_file"],'r')
	##initalize the feedback value
	freq = 1000.0
	##connect to plexon
	br.connect_client()
	##start the feedback process
	br.start_feedback(freq, var_dict['max_freq'], var_dict['min_freq'], var_dict['samp_int'])
	br.trig_nidaq_ex(var_dict['abet_dev'],var_dict['trial_trigger'][0],var_dict['trial_trigger'][1],100) ##trigger the trial for video display
	line = log.readline()[:-1] ##get the text for this line, excluding the return char
	while (line != "") and (engage_var.value != 0): ##case where you've reached the end of the log or the poison pill has been set
		##sleep for the sample interval
		time.sleep(var_dict['samp_int']/1000.0)
		if line == "T1": ##case where a target 1 has been hit
			br.send_event(var_dict['t1_event'])
			br.trig_nidaq_ex(var_dict['abet_dev'], var_dict['t1_port'][0],
				var_dict['t1_port'][1],var_dict['reward_time'])
			print "T1!"
			br.stop_feedback()
			time.sleep(3)
			##resume feedback from the last freq value
			br.resume_feedback(freq)
			br.trig_nidaq_ex(var_dict['abet_dev'],var_dict['trial_trigger'][0],var_dict['trial_trigger'][1],100)
		elif line == "T2": ##case for target 2
			br.send_event(var_dict['t2_event'])
			br.trig_nidaq_ex(var_dict['abet_dev'], var_dict['t2_port'][0], 
				var_dict['t2_port'][1], var_dict['reward_time'])
			print "T2!"
			br.stop_feedback()
			time.sleep(3)
			##resume feedback from the last feedback value
			br.resume_feedback(freq)
			br.trig_nidaq_ex(var_dict['abet_dev'],var_dict['trial_trigger'][0],var_dict['trial_trigger'][1],100)
		elif line == "Timeout": ##case for timeout (miss)
			br.send_event(var_dict['miss_event'])
			br.stop_feedback()
			br.play_noise()
			print "Timeout!"
			time.sleep(var_dict['timeout_pause'])
			##resume feedback
			br.resume_feedback(freq)
			br.trig_nidaq_ex(var_dict['abet_dev'],var_dict['trial_trigger'][0],var_dict['trial_trigger'][1],100)
		else: ##case where this is a cursor/frequency value set
			##get the cursor and frequency values
			cval,freq = read_line(line)
			##set the frequency
			br.set_feedback(freq)
		line = log.readline()[:-1] 
	br.stop_feedback()
	print "End of log file"
	return None

