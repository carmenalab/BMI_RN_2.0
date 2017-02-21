##The main BMI module 

import numpy as np
import RatUnits4 as ru
import Tkinter as Tk
import time
from progressbar import *
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import BMI_baseline
import BMI_engine_rn
import BMI_RN as br
import playback
import os

br.connect_client()
##trigger the nidaq channels to make sure they are set at 0
br.trig_nidaq(BMI_engine_rn.global_vars['abet_dev'],BMI_engine_rn.global_vars['start_trigger'][0],
	BMI_engine_rn.global_vars['start_trigger'][1])
br.trig_nidaq(BMI_engine_rn.global_vars['abet_dev'],BMI_engine_rn.global_vars['video_trigger'][0],
	BMI_engine_rn.global_vars['video_trigger'][1])
br.trig_nidaq(BMI_engine_rn.global_vars['abet_dev'],BMI_engine_rn.global_vars['trial_trigger'][0],
	BMI_engine_rn.global_vars['trial_trigger'][1])
br.trig_nidaq(BMI_engine_rn.global_vars['abet_dev'],BMI_engine_rn.global_vars['t1_port'][0],
	BMI_engine_rn.global_vars['t1_port'][1])
br.trig_nidaq(BMI_engine_rn.global_vars['abet_dev'],BMI_engine_rn.global_vars['t2_port'][0],
	BMI_engine_rn.global_vars['t2_port'][1])

# implement the default mpl key bindings
##GLOBAL VARIABLES

##Metadata save location
metaFolder = "D:\data\metadata"

##Plexon file save location
plxFolder = "/Volumes/RYAN'S EHD/Data/R7/plx_files"

##for troubleshooting: COMMENT BEFORE REAL USE!!!!
#sortedUnits = ['sig001a','sig002a','sig008a','sig009a','sig010a','sig012a','sig018a','sig019b','sig021a','sig025a','sig026a','sig029a']

##a list of sorted units form the SortClient
sortedUnits = list(br.get_sorted_units())

###############################################################################
###############################################################################
#GUI stuff

#class to create a new Tkinter Frame with all the needed listbox functionality
class UnitListBox(object):
	##take as arguments the master list and master unit list box to work from
	##and the frame that everything will become part of (should be initialized and 
	##packed before creating this object), text for the label,
    ##and whether or not to make an entry box
	def __init__(self, masterList, masterListBox, homeFrame, labelText, entry = False, entryText = None):
		self.masterList = masterList
		self.masterListBox = masterListBox
		self.entry = entry
		self.entryText = entryText
		#list to store current contents of listbox
		self.unitList = []
		##make the label
		self.title = Tk.Label(homeFrame, text = labelText).pack(side = "top")
		##make the entrybox if specced
		if self.entry:
			self.entryString = Tk.StringVar()
			self.entryObj = Tk.Entry(homeFrame,textvariable=self.entryString)
			if self.entryText != None:
				self.entryString.set(self.entryText)
			self.entryObj.pack(side = 'top')
		##make the listbox
		self.LB = Tk.Listbox(homeFrame, height = 10, selectmode = 'browse')
		self.LB.pack(side = 'top', padx = 10)
		##make the buttons
		self.RmvBUT = Tk.Button(homeFrame, text = "Remove selected")
		self.RmvBUT.pack(side = 'bottom')
		self.AddBUT = Tk.Button(homeFrame, text = "Add selected")
		self.AddBUT.pack(side = 'bottom')
		self.config_buttons()
	
	#add a unit from the master list, and remove it from the master list
	def Add(self):
		idx = int(self.masterListBox.curselection()[0])
		self.LB.insert('end', self.masterList[idx])
		self.unitList.append(self.masterList.pop(idx))
		self.masterListBox.delete(idx)
	
	#remove a unit and add it back to the master list
	def Rmv(self):
		idx = int(self.LB.curselection()[0])
		self.masterListBox.insert('end', self.unitList[idx])
		self.masterList.append(self.unitList.pop(idx))
		self.LB.delete(idx)

	##function to set up button functionality
	def config_buttons(self):
		self.RmvBUT.config(command = self.Rmv)
		self.AddBUT.config(command = self.Add)

#class for making entry string boxes/titles
class entryBox(object):
	def __init__(self, homeFrame, labelText, preset):
		self.homeFrame = homeFrame
		self.labelText = labelText
		self.preset = preset
		self.entryString = Tk.StringVar()
		self.entryObj = Tk.Entry(homeFrame, textvariable = self.entryString)
		self.title = Tk.Label(self.homeFrame, text = self.labelText)
		self.entryString.set(self.preset)
		self.title.pack(side = 'top')
		self.entryObj.pack(side = 'top')

##initialize the main window
mainWin = Tk.Tk()
mainWin.wm_title("BMI_RN v.2.0")
###################################################
###################################################
#Sorted Units listbox (not using class creation)
sortedFrame = Tk.Frame(mainWin)
sortedFrame.grid(row = 1, column = 0)
##create a listbox with all of the active sorted units
##add a scrollbar to this listbox
sortedLB = Tk.Listbox(sortedFrame, height = 10, selectmode = 'browse')
sortedLB.pack(side = "bottom", fill= "y")
sortedScroll = Tk.Scrollbar(sortedFrame, orient = "vertical")
sortedScroll.config(command = sortedLB.yview)
sortedScroll.pack(side = "right", fill = "y")
sortedLB.config(yscrollcommand = sortedScroll.set)
for unit in sortedUnits:
	sortedLB.insert('end', unit)
sortedLabel = Tk.Label(sortedFrame, text = "Active Units").pack(side = 'top')

###################################################
###################################################
#Ensembles 1 and 2 listboxes using UnitListBox class

#frames
e1Frame = Tk.Frame(mainWin)
e1Frame.grid(row = 1,column = 1)
e2Frame = Tk.Frame(mainWin)
e2Frame.grid(row = 1,column = 2)

e1 = UnitListBox(sortedUnits, sortedLB, e1Frame, "E1 Units", entry = False)
e2 = UnitListBox(sortedUnits, sortedLB, e2Frame, "E2 Units", entry = False)

###################################################
###################################################
#Add'l unit group listboxes from UnitListBox class

#frames
g1Frame = Tk.Frame(mainWin)
g1Frame.grid(row = 2, column = 0)
g2Frame = Tk.Frame(mainWin)
g2Frame.grid(row = 2, column =1)
g3Frame = Tk.Frame(mainWin)
g3Frame.grid(row = 2, column =2)

g1 = UnitListBox(sortedUnits, sortedLB, g1Frame, "Group 1 Units", entry = True, entryText = "type group name 1")
g2 = UnitListBox(sortedUnits, sortedLB, g2Frame, "Group 2 Units", entry = True, entryText = "type group name 2")
g3 = UnitListBox(sortedUnits, sortedLB, g3Frame, "Group 3 Units", entry = True, entryText = "type group name 3")

###################################################
###################################################
##Methods, entry boxes, and buttons to save metadata

metaDataFrame = Tk.Frame(mainWin)
metaDataFrame.grid(row = 1, column = 3)

#string for animal name
animalData = entryBox(metaDataFrame, "Animal Name", "type animal name here")

#string for filename
fileNameData = entryBox(metaDataFrame, "File Name", "type file name here")

#string for baseline filename
baselineFile = entryBox(metaDataFrame, "Baseline path", "D:/data/test/D00_baseline.hdf5")

#string for control units
controlCellsData = entryBox(metaDataFrame, "Control Cells", "type control region here")

#button to call save_metadata
saveMetaButton = Tk.Button(metaDataFrame, text = "Save MetaData")

##method to, uh, save metadata
def save_metadata():
	##create a session data object from the RatUnits module
	metaData = ru.Session(animalData.entryString.get(), metaFolder, 
		fileNameData.entryString.get(), controlCellsData.entryString.get(), t1Entry.entryString.get(),
		t2Entry.entryString.get(), t1_pEntry.entryString.get(), t2_pEntry.entryString.get(), t1simVar.get(),
		t2simVar.get(), misssimVar.get())
	##set all of the various unit/list pairs for the dictionary
	metaData.set_units("e1_units", e1.unitList)
	metaData.set_units("e2_units", e2.unitList)
	metaData.set_units(g1.entryString.get(), g1.unitList)
	metaData.set_units(g2.entryString.get(), g2.unitList)
	metaData.set_units(g3.entryString.get(), g3.unitList)
	##leave empty lists for the LFP; not sure how I want to handle this now so 
	#leaving it to be filled in manually
	metaData.set_lfp(g1.entryString.get(), [])
	metaData.set_lfp(g2.entryString.get(), [])
	metaData.set_lfp(g3.entryString.get(), [])
	metaData.set_event("t1", t1Entry.entryString.get())
	metaData.set_event("t2", t2Entry.entryString.get())
	metaData.set_event("MISS", "Event10")
	metaData.save_data()

saveMetaButton.configure(command = save_metadata)
saveMetaButton.pack(side = "top")

################################################################
################################################################
#BMI control panel

#new Frames
BMIVarsFrame = Tk.Frame(mainWin)
BMIVarsFrame.grid(row = 2, column = 4)

BMIVarsFrame2 = Tk.Frame(mainWin)
BMIVarsFrame2.grid(row = 2, column = 3)

##Entry Boxes
minFreqEntry = entryBox(BMIVarsFrame2, "Minimum Frequency (Hz)", '400')

maxFreqEntry = entryBox(BMIVarsFrame2, "Maximum Frequency (Hz)", '15000')

sampleRateEntry = entryBox(BMIVarsFrame2, "Sample Interval (ms)", '100')

windowEntry = entryBox(BMIVarsFrame2, "Smoothing window (num samples)", "10")

t1Entry = entryBox(BMIVarsFrame2, "T1", '3')

midpointEntry = entryBox(BMIVarsFrame2, "Midpoint", '0')

t2Entry = entryBox(BMIVarsFrame2, "T2", '-3')

t1_pEntry = entryBox(BMIVarsFrame2, "T1 percent", '.985')

t2_pEntry = entryBox(BMIVarsFrame2, "T2 percent", '.015')

timeLimitEntry = entryBox(BMIVarsFrame2, "Time Limit (s)", '30')

timeOutEntry = entryBox(BMIVarsFrame2, "Timeout (s)", '10')

baselineDurationEntry = entryBox(BMIVarsFrame2, "Baseline Duration (min)", '15')

saveFileEntry = entryBox(BMIVarsFrame2, "Save file", "D:/data/test/log.txt")

#buttons
setVarsButton = Tk.Button(BMIVarsFrame2, text = "Set BMI Variables")
setVarsButton.pack(side = 'top')

startButton = Tk.Button(BMIVarsFrame, text = "Start BMI")
startButton.pack(side = 'top')

stopButton = Tk.Button(BMIVarsFrame, text = "Stop BMI")
stopButton.pack(side = 'top')

baselineButton = Tk.Button(BMIVarsFrame, text = "Collect Baseline")
baselineButton.pack(side = "top")

adaptButton = Tk.Button(BMIVarsFrame, text = "Calculate targets")
adaptButton.pack(side = "top")

updateScoreButton = Tk.Button(BMIVarsFrame, text = "Update Score")
updateScoreButton.pack(side = "top")

plotButton = Tk.Button(BMIVarsFrame, text = "Start Plot")
plotButton.pack(side = "top")

startPbButton = Tk.Button(BMIVarsFrame, text = "Start playback")
startPbButton.pack(side = "top")

stopPbButton = Tk.Button(BMIVarsFrame, text = "Stop playback")
stopPbButton.pack(side="top")

pegE1Var = Tk.IntVar()
pegE1Check = Tk.Checkbutton(BMIVarsFrame, text = "Fix E1", 
	variable = pegE1Var)
pegE1Check.pack(side='top')

pegE2Var = Tk.IntVar()
pegE2Check = Tk.Checkbutton(BMIVarsFrame, text = "Fix E2", 
	variable = pegE2Var)
pegE2Check.pack(side='top')

scoreLabelVar = Tk.StringVar()
scoreLabel = Tk.Label(BMIVarsFrame, textvariable = scoreLabelVar)
scoreLabel.pack(side = "top")
scoreLabelVar.set("Current Score (t1, t2, miss)")
t1Var = Tk.StringVar()
t1Label = Tk.Label(BMIVarsFrame, textvariable = t1Var)
t1Label.pack(side = "top")
t2Var = Tk.StringVar()
t2Label = Tk.Label(BMIVarsFrame, textvariable = t2Var)
t2Label.pack(side = "top")
missVar = Tk.StringVar()
missLabel = Tk.Label(BMIVarsFrame, textvariable = missVar)
missLabel.pack(side = "top")

simLabelVar = Tk.StringVar()
simLabel = Tk.Label(BMIVarsFrame, textvariable = simLabelVar)
simLabel.pack(side = "top")
simLabelVar.set("Sim Results (t1, t2, miss)")
t1simVar = Tk.StringVar()
t1simLabel = Tk.Label(BMIVarsFrame, textvariable = t1simVar)
t1simLabel.pack(side = "top")
t2simVar = Tk.StringVar()
t2simLabel = Tk.Label(BMIVarsFrame, textvariable = t2simVar)
t2simLabel.pack(side = "top")
misssimVar = Tk.StringVar()
misssimLabel = Tk.Label(BMIVarsFrame, textvariable = misssimVar)
misssimLabel.pack(side = "top")


def start_BMI():
	if len(e1.unitList) == 0 or len(e2.unitList) == 0:
		print "Set ensembles first!!"
	else:
		##collect data from GUI
		min_freq = float(minFreqEntry.entryString.get())
		max_freq = float(maxFreqEntry.entryString.get())
		mid = float(midpointEntry.entryString.get())
		e1_list = list(e1.unitList)
		e2_list = list(e2.unitList)
		t1 = float(t1Entry.entryString.get())
		t2 = float(t2Entry.entryString.get())
		samp_int = int(sampleRateEntry.entryString.get())
		smooth_int = int(windowEntry.entryString.get())
		timeout = int(timeLimitEntry.entryString.get())
		timeout_pause = int(timeOutEntry.entryString.get())
		save_file = saveFileEntry.entryString.get()
		e1_mean,e2_mean = BMI_baseline.ensemble_means(baselineFile.entryString.get())
		#set params
		BMI_engine_rn.start_BMI(e1_list, e2_list, samp_int, smooth_int, timeout, timeout_pause, 
			t1, t2, mid, min_freq, max_freq, save_file, e1_mean, e2_mean)

def stop_BMI():
	BMI_engine_rn.stop_BMI()

def update_score():
	t1Var.set(BMI_engine_rn.get_t1())
	t2Var.set(BMI_engine_rn.get_t2())
	missVar.set(BMI_engine_rn.get_miss())

def update_sim_score(t1, t2, miss):
	t1simVar.set(str(t1))
	t2simVar.set(str(t2))
	misssimVar.set(str(miss))

def set_params():
	if len(e1.unitList) == 0 or len(e2.unitList) == 0:
		print "Set ensembles first!!"
	else:
		##collect data from GUI
		min_freq = float(minFreqEntry.entryString.get())
		max_freq = float(maxFreqEntry.entryString.get())
		mid = float(midpointEntry.entryString.get())
		e1_list = list(e1.unitList)
		e2_list = list(e2.unitList)
		t1 = float(t1Entry.entryString.get())
		t2 = float(t2Entry.entryString.get())
		samp_int = int(sampleRateEntry.entryString.get())
		smooth_int = int(windowEntry.entryString.get())
		timeout = int(timeLimitEntry.entryString.get())
		timeout_pause = int(timeOutEntry.entryString.get())
		save_file = saveFileEntry.entryString.get()
		e1_mean,e2_mean = BMI_baseline.ensemble_means(baselineFile.entryString.get())
		#set params
		BMI_engine_rn.set_globals(e1_list, e2_list, samp_int, smooth_int, timeout, timeout_pause, t1, 
			t2, mid, min_freq, max_freq, save_file, e1_mean, e2_mean)
		playback.set_globals(samp_int,smooth_int,timeout,timeout_pause,save_file,max_freq,min_freq)

def collect_baseline():
	BMI_baseline.collect_baseline(list(e1.unitList), list(e2.unitList), 
		int(sampleRateEntry.entryString.get()), int(windowEntry.entryString.get()), 
		int(baselineDurationEntry.entryString.get()), baselineFile.entryString.get())

##function to try and approximate a 30% success rate for both targets
##given baseline data. Function basically simulates BMI for the baseline period.
def set_targets():
	##collect data from GUI
	f_in = os.path.normpath(baselineFile.entryString.get())
	min_freq = float(minFreqEntry.entryString.get())
	max_freq = float(maxFreqEntry.entryString.get())
	e1_list = list(e1.unitList)
	e2_list = list(e2.unitList)
	t1_perc = float(t1_pEntry.entryString.get())
	t2_perc = float(t2_pEntry.entryString.get())
	samp_int = int(sampleRateEntry.entryString.get())
	smooth_int = int(windowEntry.entryString.get())
	timeout = int(timeLimitEntry.entryString.get())
	timeout_pause = int(timeOutEntry.entryString.get())
	t2, mid, t1, num_t1, num_t2, num_miss = BMI_baseline.set_targets(f_in, t1_perc, t2_perc, min_freq, max_freq, samp_int, smooth_int, 
	timeout, timeout_pause)
	t1Entry.entryString.set(str(round(t1, 5)))
	t2Entry.entryString.set(str(round(t2, 5)))
	midpointEntry.entryString.set(str(round(mid, 5)))
	update_sim_score(num_t1, num_t2, num_miss)
	matplotlib.pyplot.show()

def start_plot():
	root = Tk.Tk()
	#make a real-time graph to visualize cursor data
	fig = matplotlib.figure.Figure()
	ax = fig.add_subplot(111)
	ymin = float(t2Entry.entryString.get())
	ymax = float(t1Entry.entryString.get())
	ax.set_ylim(ymin,ymax)
	ax.set_title("Real-time Cursor Position")
	ax.set_ylabel("Cursor Value")
	ax.set_xlabel("Time (s)")

	x = np.linspace(0,5,500)

	buff = np.zeros(500)        # x-array

	def animate(data):
	    line.set_ydata(data)  # update the data
	    return line,

	def generate_data():
	  while True:
	    buff[0:-1] = buff[1:]
	    buff[-1] = br.get_cursor_val()
	    yield buff

	canvas = FigureCanvasTkAgg(fig, master=root)
	canvas.get_tk_widget().grid(row = 1, column = 4)


	line, = ax.plot(x, buff)
	ani = animation.FuncAnimation(fig, animate, generate_data, interval=10)

def startPlayback():
	samp_int = int(sampleRateEntry.entryString.get())
	smooth_int = int(windowEntry.entryString.get())
	timeout = int(timeLimitEntry.entryString.get())
	timeout_pause = int(timeOutEntry.entryString.get())
	save_file = saveFileEntry.entryString.get()
	max_freq = float(maxFreqEntry.entryString.get())
	min_freq = float(minFreqEntry.entryString.get())
	playback.start_playback(samp_int,smooth_int,timeout,timeout_pause,save_file,max_freq,min_freq)

def stopPlayback():
	playback.stop_playback()

def peg_e1():
	if pegE1Var.get():
		br.connect_client()
		BMI_engine_rn.fix_e1_on()
		br.send_event(8)
		br.disconnect_client()
	elif not pegE1Var.get():
		BMI_engine_rn.fix_e1_off()

def peg_e2():
	if pegE2Var.get():
		br.connect_client()
		BMI_engine_rn.fix_e2_on()
		br.send_event(9)
		br.disconnect_client()
	elif not pegE2Var.get():
		BMI_engine_rn.fix_e2_off()


setVarsButton.configure(command = set_params)
startButton.configure(command = start_BMI)
stopButton.configure(command = stop_BMI)
baselineButton.configure(command = collect_baseline)
adaptButton.configure(command = set_targets)
updateScoreButton.configure(command = update_score)
plotButton.configure(command = start_plot)
startPbButton.configure(command = startPlayback)
stopPbButton.configure(command = stopPlayback)
pegE1Check.configure(command = peg_e1)
pegE2Check.configure(command = peg_e2)

########################################################################
########################################################################












