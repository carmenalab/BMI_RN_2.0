# this program makes a sweep in frequency for auditory feedback while instructing
# plexton to record the neuronal data
# plexton has to have enable event005 and 006

__author__ = 'Nuria'


# C++ extension for data acquisition

import msvcrt
import time
import h5py
import numpy as np
import matplotlib.pyplot as plt


def frequency_sweep(freq_init, freq_final, duration, f_name, samp_interval):
    import BMI_RN as br
    # check if the file name exist
    try:
        f = h5py.File(f_name, 'w-')
    except IOError:
        print(" OOPS!: The file already existed please try with another file name")
        return
    # duration in ms of the recording
    dura_ms = duration * 60.0 * 1000.0
    # number of samples depending on the sample interval (bin)
    num_samples = int(dura_ms / samp_interval)
    # allocates a vector for the whole recording for frequency and time
    frequency_data = np.zeros(num_samples)
    time_data = np.zeros(num_samples)
    freq = freq_init
    # connects to plexton
    br.connect_client()
    # sets initial frequency
    br.start_feedback(freq_init, samp_interval)
    # sends event to know when it starts recording in plexton
    br.send_event(5)
    flag_up = 1
    flag_early_stop = 0
    # to use the proper sleep time
    t = time.time()
    t2 = t  # t2 will be updated inside the loop to see how long has taken the computations
    for i in range(num_samples):
        # increments the frequency on the audio feedback
        br.set_feedback(freq)
        # stores frequency and time in array
        frequency_data[i] = freq
        time_data[i] = time.time()-t
        # for debug purposes print(str(freq) + '...' + str(elapsed))
        # waits until next sample time - time that the program needed to do the rest
        elapsed = time.time() - t2
        time.sleep(samp_interval / 1000.0 - elapsed)
        # increments the frequency up or down depending on flag
        t2 = time.time()
        if freq <= freq_init:
            flag_up = 1
        if freq >= freq_final:
            flag_up = 0
        if flag_up:
            freq += 10
        else:
            freq += -10
        # this looks for keyboard input to stop the loop
        # if there is a hit of the keyboard
        if msvcrt.kbhit():
            # if the esc was pressed
            if ord(msvcrt.getch()) == 27:
                flag_early_stop = 1
                break

    # stop commands
    br.stop_feedback()
    br.send_event(6)  # stop recording
    br.disconnect_client()
    if flag_early_stop:
        print("The program detected and early stop from keyboard")
    print("The program has stopped and the plexton has stopped recording")

    # saving commands
    f.create_dataset("f_data", data=frequency_data)
    f.create_dataset("t_data", data=time_data)
    f.close()
    sentence = "The frequency data has been saved in the file: " + f_name
    print(sentence)


def plot_data(f_freq, f_spikes, spk_channel, sig, samp_interval):
    import plxread
    # f_freq is the file of the frequencies
    # spikes the plx file
    # spk_channel is the channel that we want to plot
    # sig is the unit we want to see

    # open the hdf5 file that contains the frequency
    f = h5py.File(f_freq, 'r')
    # gets the data from file
    ar_freq = np.asarray(f['f_data'])
    # to adjust the amount of values or ar_freq and time
    mul_value = 1000/samp_interval
    # import the spikes data
    data_spikes = plxread.import_file(f_spikes, spike_channel=spk_channel)
    cha_spikes = data_spikes.get(sig)
    # to be sure that the unit exist
    if np.size(cha_spikes) == 1:
        print("Oops the unit you have selected can not be retrieved")
        return
    # import the events that set the start and end of the recording
    start_rec = data_spikes.get('Event005')
    end_rec = data_spikes.get('Event006')
    # cuts the array to use only the data from when there was recording of frequency
    cha_spikes = cha_spikes[cha_spikes > start_rec]
    cha_spikes = cha_spikes[cha_spikes < end_rec]
    # allocates memory for a vector of spikes where indexes are time
    ar_spikes = np.zeros(np.size(ar_freq))
    # sets the vector ar_spikes to 1 if there is a spike in that time moment
    for i in range(np.size(cha_spikes)):
        # sets the index (it is actually the time where the spike happened) of the array of spikes
        # the not very elegant idea is to avoid the arrays to mismatch for the hist plot
        temp_index = int(round((cha_spikes[i]-start_rec[0])*mul_value))
        # value - 1 since it starts the array in 0 not in 1
        if temp_index <= np.size(ar_spikes):
            ar_spikes[temp_index - 1] += 1
    plt.hist(ar_freq, weights=ar_spikes, bins=100)