Ryan Neely
11/10/15
ryan_neely@berkeley.edu

BMI_RN is a python extension to perform basic I/O with the Plexon 
MAP system, as well as generate audio feedback tones and some basic
DI/O functionality with the NIDAQ USB card. The meat of the code is 
written in C++ to make data acquisition as fast as possible. 

Installation:
This package was written and tested only on Python2.7 (both 32 and 64bit).
You MUST have the Plexon Rasputin software suite installed, 
as well as the NI DAQmxBase system, both of which are available online.
The package installs with setuptools, meaning compilation should go 
smoothly as long as you have the standard MSVC++ compiler for python
installed (also available online). Obviously due to these dependencies 
this package will only compile on Windows. 

The BMI_RN module contains several core functions:

-start_feedback(midpoint, interval):
this function starts feedback playback. The 'midpoint' arg
is the starting frequency (and possible the local min for a 
gravity term in a later release). The 'interval' term specifies
your expected sample interval in order to generate smoothed 
transitions between frequency tones. 

__FEEDBACK FUNCTIONS__

-set_feedback(val):
this function takes a float argument and changes the current
feedback frequency to 'val.'

-stop_feedback():
sets the current playback frequency to 0 (basically a mute function)

-resume_feedback(val):
resumes the feedback at a frequency given by 'val'. Assumes
'start_feedback' has already been called.

-play_noise():
plays a 3-second white noise burst.

__PLEXON FUNCTIONS__
-get_sorted_units():
returns a list of strings corresponding to the names 
of all units currently sorted in the sort client.

-get_cursor_val(e1_names, e2_names, num_e1, num_e2, we1, we2, interval):
returns the current cursor value based on the following:
e1_names: names of the sorted units in ensemble 1;
e2_names: names of the sorted units in ensemble 2;
num_e1: number of e1 units;
num_e2: number of e2 units;
we1: weight applied to ensemble e1
we2: weight applied to ensemble e2
interval: length of sample interval to get spike counts in

return value equals we1(counts of all e1 spikes in interval) - we2(counts of all e2 spikes in interval)

-get_e_vals(e1_names, e2_names, num_e1, num_e2, interval):
similar to the above function, but it returns 2 values which are
the raw counts of e1 and e2 respectively. No weight parameters are needed.

-send_event(chan):
trigger an event on the plexon recording on channel 'chan'

-trig_nidaq(dev, port):
pulse the DIO on nidaq device 'dev' and port 'port'