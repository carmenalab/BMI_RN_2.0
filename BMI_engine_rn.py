##BMI_engine_rn.py
##defines the control scheme for BMI behavior

##C++ extension for data acquisition
import BMI_RN as br
from multiprocessing import Process, Value, Array
import time
import numpy as np
import BMI_baseline as baseline
import os

#global variables dictionary
global_vars = {
	"e1_list":[],
	"e2_list":[],
	"samp_int":0,
	"smooth_int":0,
	"timeout":0,
	"timeout_pause":0,
	"t1":0,
	"t2":0,
	"mid":0,
	"abet_dev":1,
	"t1_port":(2,0),
	"t2_port":(2,1),
	"start_trigger":(0,0),
	"video_trigger":(0,1),
	"trial_trigger":(0,2),
	"t1_event":11,
	"t2_event":12,
	"miss_event":10,
	"min_freq":400,
	"max_freq":15000,
	"save_file":r"D:\data\test.txt",
	"reward_time":1000,
	"e1_mean":0,
	"e2_mean":0
}


##global state variable to be shared between processes
engage = Value('i', 0)
time_remaining = Value('i', 0)
num_t1 = Value('i', 0)
num_t2 = Value('i', 0)
num_miss = Value('i', 0)
peg_e1 = Value('i', 0)
peg_e2 = Value('i', 0)

"""
set_globals: a function to set global variables.
Args:
-e1_list; e2_list: list of strings corresponding to the sort names
	of units for ensembles 1 and 2
-we1; we2: weight values to apply to the raw spike counts of e1_list
	and e2, respectively
-samp_int: the time interval in ms to sample spike counts (bin size)
-smooth_int: the window size, in samples, to smooth/average the spike counts
-midpoint: the starting frequency value of the auditory cursor
-timeout: timeout clock peroid in seconds
-timeout_pause: the amount of time to wait after the clock times out
-t1; t2: cursor values of target 1 and 2
"""
def set_globals(e1_list, e2_list, samp_int, smooth_int, timeout, timeout_pause, t1, 
	t2, mid, min_freq, max_freq, save_file, e1_mean, e2_mean):
	global global_vars
	global_vars['e1_list'] = e1_list
	global_vars['e2_list'] = e2_list
	global_vars['samp_int'] = samp_int
	global_vars['smooth_int'] = smooth_int
	global_vars['mid'] = mid
	global_vars['timeout'] = timeout
	global_vars['timeout_pause'] = timeout_pause
	global_vars['t1'] = t1
	global_vars['t2'] = t2
	global_vars['mid'] = mid
	global_vars['max_freq'] = max_freq
	global_vars['min_freq'] = min_freq
	global_vars['save_file'] = os.path.normpath(save_file)
	global_vars['e1_mean'] = e1_mean
	global_vars['e2_mean'] = e2_mean




"""
init_BMI: a function to initialize BMI and start the relevant processes. 
Args:
-e1_list; e2_list: list of strings corresponding to the sort names
	of units for ensembles 1 and 2
-we1; we2: weight values to apply to the raw spike counts of e1_list
	and e2, respectively
-samp_int: the time interval in ms to sample spike counts (bin size)
-smooth_int: the window size, in samples, to smooth/average the spike counts
-midpoint: the starting frequency value of the auditory cursor
-timeout: timeout peroid in seconds
-timeout_pause: the amount of time to wait after the clock times out
-t1; t2: cursor values of target 1 and 2
"""
def start_BMI(e1_list, e2_list, samp_int, smooth_int, timeout, timeout_pause, 
	t1, t2, mid, min_freq, max_freq, save_file, e1_mean, e2_mean):
	global engage
	global time_remaining
	global global_vars
	global num_t1
	global num_t2
	global num_miss
	global peg_e1
	global peg_e2
	##activate state variables
	engage.value = 1
	##set global variables
	set_globals(e1_list, e2_list, samp_int, smooth_int, timeout, timeout_pause, t1, t2, 
		mid, min_freq, max_freq, save_file, e1_mean, e2_mean)
	##initialize the processes to link feedback and cursor state
	##cursor function 
	decoder_p = Process(target = decoder, args = (global_vars, engage, time_remaining, 
		peg_e1, peg_e2, num_t1, num_t2, num_miss))
	#timeout clock function
	timer_p = Process(target = timeout_clock, args = (engage, time_remaining))
	##start the processes
	##trigger the recording
	# br.trig_nidaq_ex(global_vars['abet_dev'],global_vars['start_trigger'][0],global_vars['start_trigger'][1],100)
	# br.trig_nidaq_ex(global_vars['abet_dev'],global_vars['video_trigger'][0],global_vars['video_trigger'][1],100)
	decoder_p.start()
	timer_p.start()

##function to stop BMI
def stop_BMI():
	global engage
	engage.value = 0

##functions:
"""
decoder- a function to acquire and the BMI cursor Value
from the MAP server, and check for target hits.
"""
def decoder(var_dict, engage_var, timer_var, peg_e1_var, peg_e2_var, num_t1, num_t2, num_miss):
	##open the file to save the data
	fileout = open(var_dict['save_file'],'w')
	##initialize the timer
	timer_var.value = var_dict['timeout']
	br.connect_client()
	#set cursor and feedback parameters, and start the module threads
	br.set_cursor_params(tuple(var_dict['e1_list']), tuple(var_dict['e2_list']), len(var_dict['e1_list']),
		len(var_dict['e2_list']), var_dict['samp_int'], var_dict['smooth_int'])
	br.start_cursor()
	br.start_feedback(1000, var_dict['max_freq'], var_dict['min_freq'], var_dict['samp_int'])
	##get the function variable to map cursor state to frequency (based on baseline calculations)
	map_func = baseline.map_to_freq(var_dict['t2'], var_dict['mid'], var_dict['t1'], 
		var_dict['min_freq'], var_dict['max_freq'])
	##chack the global engage variable
	br.trig_nidaq_ex(global_vars['abet_dev'],global_vars['start_trigger'][0],global_vars['start_trigger'][1],100)
	br.trig_nidaq_ex(global_vars['abet_dev'],global_vars['video_trigger'][0],global_vars['video_trigger'][1],100)
	br.trig_nidaq_ex(var_dict['abet_dev'],var_dict['trial_trigger'][0],var_dict['trial_trigger'][1],100)
	while engage_var.value != 0:
		##acquire the cursor value and set the feedback accordingly
		time.sleep(var_dict['samp_int']/1000.0)
		E1,E2 = calc_cursor(peg_e1_var, peg_e2_var, var_dict['e1_mean'], var_dict['e2_mean'])
		cursor = E1-E2
		fb = map_func(cursor)
		br.set_feedback(fb)
		##write this data to file
		fileout.write(str(E1)+","+str(E2)+","str(fb)+"\n") ##this will save E1 and E2 vals, feedback val on a line for each sample
		##check for T1
		if cursor >= var_dict['t1']:
			##create a timestamp
			br.send_event(var_dict['t1_event'])
			##trigger ABET
			br.trig_nidaq_ex(var_dict['abet_dev'], var_dict['t1_port'][0],
				var_dict['t1_port'][1],var_dict['reward_time'])
			##save to the log file
			fileout.write("T1\n")
			##pause feedback
			br.stop_feedback()
			##increment the score
			num_t1.value += 1
			print "T1!"
			##pause for reward
			time.sleep(3)
			##resume feedback
			e1,e2 = calc_cursor(peg_e1_var, peg_e2_var, var_dict['e1_mean'], var_dict['e2_mean'])
			br.resume_feedback(map_func(e1-e2))
			##check for back to baseline
			while cursor >= var_dict['mid']:
				E1,E2 = calc_cursor(peg_e1_var, peg_e2_var, var_dict['e1_mean'], var_dict['e2_mean'])
				cursor = E1-E2
				br.set_feedback(map_func(cursor))
				time.sleep(var_dict['samp_int']/1000.0)
			print "Back to baseline"
			##reset clock
			timer_var.value = var_dict['timeout']
			br.trig_nidaq_ex(var_dict['abet_dev'],var_dict['trial_trigger'][0],var_dict['trial_trigger'][1],100)
		##check for T2
		elif cursor <= var_dict['t2']:
			##create a timestamp
			br.send_event(var_dict['t2_event'])
			##trigger ABET
			br.trig_nidaq_ex(var_dict['abet_dev'], var_dict['t2_port'][0], 
				var_dict['t2_port'][1], var_dict['reward_time'])
			##save to the log file
			fileout.write("T2\n")
			##pause feedback
			br.stop_feedback()
			##increment the score
			num_t2.value += 1
			print "T2!"
			##pause for reward
			time.sleep(3)
			##resume feedback
			e1,e2 = calc_cursor(peg_e1_var, peg_e2_var, var_dict['e1_mean'], var_dict['e2_mean'])
			br.resume_feedback(map_func(e1-e2))
			##check for back to baseline
			while cursor <= var_dict['mid']:
				E1,E2 = calc_cursor(peg_e1_var, peg_e2_var, var_dict['e1_mean'], var_dict['e2_mean'])
				cursor = E1-E2
				br.set_feedback(map_func(cursor))
				time.sleep(var_dict['samp_int']/1000.0)
			print "Back to baseline"
			##reset clock
			timer_var.value = var_dict['timeout']
			br.trig_nidaq_ex(var_dict['abet_dev'],var_dict['trial_trigger'][0],var_dict['trial_trigger'][1],100)
		##check for timeout
		elif timer_var.value <= 0:
			##create a timestamp
			br.send_event(var_dict['miss_event'])
			##pause feedback
			br.stop_feedback()
			##increment the score
			num_miss.value += 1
			##play white noise
			br.play_noise()
			##save to the log file
			fileout.write("Timeout\n")
			print "Timeout!"
			##pause for given timeout
			time.sleep(var_dict['timeout_pause'])
			##resume feedback
			e1,e2 = calc_cursor(peg_e1_var, peg_e2_var, var_dict['e1_mean'], var_dict['e2_mean'])
			br.resume_feedback(map_func(e1-e2))
			##reset clock
			timer_var.value = var_dict['timeout']
			br.trig_nidaq_ex(var_dict['abet_dev'],var_dict['trial_trigger'][0],var_dict['trial_trigger'][1],100)
	br.stop_cursor()
	br.stop_feedback()
	br.disconnect_client()
	fileout.close()
	br.trig_nidaq_ex(global_vars['abet_dev'],global_vars['video_trigger'][0],global_vars['video_trigger'][1],100)
	print "BMI stopped!"

##a function to compute the cursor value
def calc_cursor(peg_e1,peg_e2,e1_mean,e2_mean):
	E1, E2 = br.get_e1_e2()
	if peg_e1.value:
		E1 = e1_mean
	if peg_e2.value:
		E2 = e2_mean
	return E1,E2


"""
timeout_clock: a function to implement a timeout clock, lol
Args:
-var_dict: global dictionary of variables
-engage_var: global variable to signal task engagement
-timeout_var: global variable to signal a timeout
"""
def timeout_clock(engage_var, timeout_var):
	while engage_var.value == 1:
		##decrement the timer variable
		timeout_var.value -= 1
		time.sleep(1)

##functions to interact with the GUI
def get_t1():
	return num_t1.value

def get_t2():
	return num_t2.value

def get_miss():
	return num_miss.value

def fix_e1_on():
	global peg_e1
	peg_e1.value = 1

def fix_e1_off():
	global peg_e1
	peg_e1.value = 0

def fix_e2_on():
	global peg_e2
	peg_e2.value = 1

def fix_e2_off():
	global peg_e2
	peg_e2.value = 0

