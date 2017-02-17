##a script to collect a baseline data as well as calculate weights
##for ensembles based on a given chance rate.

import BMI_RN as br
import h5py
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import scipy.stats
import time
import gmm
import multiprocessing


##a function to send random rewards
def random_reward(session_len):
	##convert to seconds
	session_len = session_len * 60
	##counter to store the current session length
	counter = 0
	##while you haven't exceeded the session length:
	while counter < session_len:
		#get a random time to pause for
		pause = np.random.randint(40, 80)
		##pause
		time.sleep(pause)
		##send a signal to behavior box
		br.trig_nidaq_ex(1,2,0,1000)
		##increment the counter based on the pause duration
		counter += pause
	print "Reward cycle complete!"

"""
collect_baseline: a function to collect and save baseline ensemble data
Args:
-e1_list; e2_list: list of strings corresponding to the sort names
	of units for ensembles 1 and 2
-samp_int: the time interval in ms to sample spike counts (bin size)
-duration: the desired length of baseline collection, in minutes
-f_name: a file path to save the baseline data in HDF5 format
"""
def collect_baseline(e1_list, e2_list, samp_int, smooth_int, duration, f_name):
	##figure out how many samples to take
	#basline duration in ms:
	base_ms = duration*60.0*1000.0
	num_samples = int(base_ms/samp_int)
	##allocate an array to store data
	baseline_data_e1 = np.zeros(num_samples)
	baseline_data_e2 = np.zeros(num_samples)
	##start collecting the data
	br.connect_client()
	br.set_cursor_params(tuple(e1_list), tuple(e2_list), len(e1_list), len(e2_list),
		samp_int, smooth_int)
	br.start_cursor()
	##start a thread to send reward signals
	reward_p = multiprocessing.Process(target = random_reward, args = (duration,))
	reward_p.start()
	for i in range(num_samples):
		baseline_data_e1[i], baseline_data_e2[i] = br.get_e1_e2()
		time.sleep(samp_int/1000.0)
	print "baseline collection complete"
	f = h5py.File(f_name, 'w-')
	f.create_dataset("baseline_data_e1", data = baseline_data_e1)
	f.create_dataset("baseline_data_e2", data = baseline_data_e2)
	f.close()
	br.stop_cursor()
	br.disconnect_client()
	print "baseline data saved"

def set_targets(f_in, prob_t1, prob_t2, min_freq, max_freq, samp_int, smooth_int, 
	timeout, timeout_pause):
	f, (ax1, ax2) = plt.subplots(1, 2)
	##load the baseline data
	f = h5py.File(f_in, 'r')
	data = np.asarray(f['baseline_data_e1'])-np.asarray(f['baseline_data_e2'])
	f.close()
	##calculate the gaussian mixture model
	x, pdf, pdf_individual = gmm.generate_gmm(data)
	##determine the x-values of the targets with the given percentages
	t1 = gmm.prob_under_pdf(x, pdf, prob_t1)
	t2 = gmm.prob_under_pdf(x, pdf, prob_t2)
	idx_mid = np.argmax(pdf)
	mid = x[idx_mid]
	#fig, ax = plt.subplots()
	ax1.hist(data+np.random.normal(0, 0.1*data.std(), data.size), 50, 
		normed = True, histtype = 'stepfilled', alpha = 0.4)
	ax1.plot(x, pdf, '-k')
	ax1.plot(x, pdf_individual, '--k')
	ax1.text(0.04, 0.96, "Best-fit Mixture",
        ha='left', va='top', transform=ax1.transAxes)
	ax1.set_xlabel('Cursor Value (E1-E2)')
	ax1.set_ylabel('$p(x)$')
	##find the points where t1 and t2 lie on the gaussian
	idx_t2 = np.where(x>t2)[0][0]
	x_t2 = t2
	y_t2 = pdf[idx_t2]
	idx_t1 = np.where(x>t1)[0][0]
	x_t1 = t1
	y_t1 = pdf[idx_t1]
	y_mid = pdf[idx_mid]
	ax1.plot(x_t1, y_t1, 'o', color = 'g')
	ax1.plot(x_t2, y_t2, 'o', color = 'g')
	ax1.plot(mid, y_mid, 'o', color = 'g')
	ax1.set_title("Firing rate histogram and gaussian fit")
	ax1.annotate('T1: ('+str(round(x_t1, 3))+')', xy=(x_t1, y_t1), xytext=(40,20), 
            textcoords='offset points', ha='center', va='bottom',
            bbox=dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.3),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.5', 
                            color='red'))
	ax1.annotate('T2: ('+str(round(x_t2, 3))+')', xy=(x_t2, y_t2), xytext=(-40,20), 
            textcoords='offset points', ha='center', va='bottom',
            bbox=dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.3),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.5', 
                            color='red'))
	ax1.annotate('Base: ('+str(round(mid, 3))+')', xy=(mid, y_mid), xytext=(-100,-20), 
            textcoords='offset points', ha='center', va='bottom',
            bbox=dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.3),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.5', 
                            color='red'))
	##get the control function
	p = map_to_freq(t2, mid, t1, min_freq, max_freq)
	##run a simulation
	num_t1, num_t2, num_miss = sim_bmi(f_in, samp_int, smooth_int, t1, t2, mid, timeout, timeout_pause, p)
	print "Simulation results:\nNumber of T1: " + str(num_t1) + "\nNumber of T2: " + str(num_t2) + "\nNumber of Misses: " + str(num_miss)
	print "Calculated T2 value is " + str(round(t2, 5))
	print "Calculated mid value is " + str(round(mid, 5))
	print "Calculated T1 value is " + str(round(t1, 5))
	##plot the control function
	plot_cursor_func(t2, mid, t1, min_freq, max_freq, ax2)
	#plt.show()
	return t2, mid, t1, num_t1, num_t2, num_miss


"""
sim_bmi: a function to run a simulation on baseline data to calculate the number of 
theoretical t1, t2, and misses
Args:
"""
def sim_bmi(f_in, samp_int, smooth_int, t1, t2, midpoint, timeout, timeout_pause, p_func):
	##load the baseline data
	f = h5py.File(f_in, 'r')
	data = np.asarray(f['baseline_data_e1'])-np.asarray(f['baseline_data_e2'])
	f.close()
	##get the timeout duration in samples
	timeout_samps = int((timeout*1000.0)/samp_int)
	timeout_pause_samps = int((timeout_pause*1000.0)/samp_int)
	##"global" variables
	num_t1 = 0
	num_t2 = 0
	num_miss = 0
	back_to_baseline = 1
	##run through the data and simulate BMI
	i = 0
	clock = 0
	while i < (data.shape[0]-1):
		cursor = data[i]
		##check for a target hit
		if cursor >= t1:
			num_t1+=1
			i += int(4000/samp_int)
			back_to_baseline = 0
			##wait for a return to baseline
			while cursor >= midpoint and i < (data.shape[0]-1):
				#advance the sample
				i+=1
				##get cursor value
				cursor = data[i]
			##reset the clock
			clock = 0
		elif cursor <= t2:
			num_t2+=1
			i += int(4000/samp_int)
			back_to_baseline = 0
			##wait for a return to baseline
			while cursor >= midpoint and i < (data.shape[0]-1):
				#advance the sample
				i+=1
				##get cursor value
				cursor = data[i]
			##reset the clock
			clock = 0
		elif clock >= timeout_samps:
			##advance the samples for the timeout duration
			i+= timeout_pause_samps
			num_miss += 1
			##reset the clock
			clock = 0
		else:
			##if nothing else, advance the clock and the sample
			i+= 1
			clock+=1
	##save and share the results
	f = h5py.File(f_in, 'r+')
	try:
		f.create_dataset(str(t1)+"_"+str(t2)+"sim_results", data = np.array([num_t1, num_t2, num_miss]))
	except RuntimeError:
		print "Already saved this data." 
	f.close()
	return num_t1, num_t2, num_miss

##a function to plot the cursor function
def plot_cursor_func(t2, mid, t1, min_freq, max_freq, ax2):
	x = np.linspace(t2-1, t1+1, 1000)
	func = map_to_freq(t2, mid, t1, min_freq, max_freq)
	#fig, ax = plt.subplots()
	ax2.plot(t2, min_freq, 'o', color = 'r')
	ax2.plot(mid, np.floor((max_freq-min_freq)/2), 'o', color = 'r')
	ax2.plot(t1, max_freq, 'o', color = 'r')
	ax2.plot(x, func(x), '-', color = 'g')
	ax2.annotate('T1: ('+str(round(t1, 3))+')', xy=(t1, max_freq), xytext=(-20, 20), 
            textcoords='offset points', ha='center', va='bottom',
            bbox=dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.3),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.5', 
                            color='red'))
	ax2.annotate('T2: ('+str(round(t2, 3))+')', xy=(t2, min_freq), xytext=(-20,20), 
            textcoords='offset points', ha='center', va='bottom',
            bbox=dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.3),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.5', 
                            color='red'))
	ax2.annotate('Base: ('+str(round(mid, 3))+')', xy=(mid, np.floor((max_freq-min_freq)/2)), xytext=(-20,20), 
            textcoords='offset points', ha='center', va='bottom',
            bbox=dict(boxstyle='round,pad=0.2', fc='yellow', alpha=0.3),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.5', 
                            color='red'))
	ax2.set_ylabel("Feedback frequency")
	ax2.set_xlabel("Cursor value (E1-E2)")
	ax2.set_title("Cursor-frequency map", fontsize = 18)

##function to map ensemble values to frequency values
def map_to_freq(t2, mid, t1, min_freq, max_freq):
	fr_pts = np.array([t2, mid, t1])
	freq_pts = np.array([min_freq, np.floor(((1.0*max_freq)+min_freq)/2), max_freq])
	z = np.polyfit(fr_pts, freq_pts, 2)
	p = np.poly1d(z)
	return p

## a function to return the mean ensemble values for E1 and E2 calculated from 
##the baseline
def ensemble_means(f_in):
	try:
		f = h5py.File(f_in,'r')
		e1_mean = np.asarray(f['baseline_data_e1']).mean()
		e2_mean = np.asarray(f['baseline_data_e2']).mean()
		f.close()
	except IOError: ##case where no baseline has been saved yet
		e1_mean = 0
		e2_mean = 0
	return e1_mean, e2_mean


