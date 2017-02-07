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
	line = log.readline()
	
