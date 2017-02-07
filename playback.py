###playback.py
### a function to play back frequency data (and log events to plexon)

import BMI_RN as br
import os
from multiprocessing import Process, Value, Array

##a dictionary of global variables
global_vars = {
	"samp_int":0,
	"smooth_int":0,
	"timeout":0,
	"timeout_pause":0,
	"t1_event":11,
	"t2_event":12,
	"miss_event":10,
	"log_file":r"D:\data\log.txt"
}

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
	return cval, freq

### a function to run the simulation. Meant to be run in a separate process.
def playback(var_dict,engage_var):
	log = open(var_dict["log_file"],'r')
	##initalize the feedback value
	freq = 1000
	##start the feedback process
	br.start_feedback(freq, var_dict['samp_int'])
	line = log.readline()[:-1] ##get the text for this line, excluding the return char
	while line != "" ##case where you've reached the end of the log
		##sleep for the sample interval
		time.sleep(var_dict['samp_int']/1000.0)
		if line == "T1": ##case where a target 1 has been hit
			br.send_event(var_dict['t1_event'])
			print "T1!"
			time.sleep(3)
			##resume feedback from the last freq value
			br.resume_feedback(freq)
		elif line == "T2": ##case for target 2
			br.send_event(var_dict['t2_event'])
			print "T2!"
			time.sleep(3)
			##resume feedback from the last feedback value
			br.resume_feedback(freq)
		elif line == "Timeout": ##case for timeout (miss)
			br.send_event(var_dict['miss_event'])
			br.stop_feedback()
			br.play_noise()
			print "Timeout!"
			time.sleep(var_dict['timout_pause'])
			##resume feedback
			br.resume_feedback(freq)
		else: ##case where this is a cursor/frequency value set
			##get the cursor and frequency values
			cval,freq = read_line(line)
			##set the frequency
			br.set_feedback(freq)
	br.stop_feedback()
	print "End of log file"
	return None

