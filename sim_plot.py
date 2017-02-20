##function to animate/plot a log

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.animation as animation
import re


class SubplotAnimation(animation.TimedAnimation):
    def __init__(self,t1_val,t2_val,mid_val,log_path,
        bin_size=100,target_pause=3,timeout_pause=10):
        ##set up our figure
        fig = plt.figure()
        ax1 = fig.add_subplot(2, 1, 2)
        ax2 = fig.add_subplot(2, 2, 1)
        ax3 = fig.add_subplot(2, 2, 2)

        self.t1_val = t1_val
        self.t2_val = t2_val
        self.mid_val = mid_val
        self.log_path = log_path
        self.bin_size = bin_size
        self.target_pause = target_pause
        self.timeout_pause = timeout_pause
        ##now get the data arrays from the log file
        self.e1,self.e2,self.cval = self.parse_log()
        self.x = np.arange(-2000/self.bin_size,0)
        self.t = np.arange(self.e1.size)
        self.t1 = np.ones(self.e1.size)*t1_val
        self.t2 = np.ones(self.e2.size)*t2_val
        self.mid = np.ones(self.e1.size)*mid_val
        self.show_n = 2000/self.bin_size ##number of bins to show (here it's 2 sec worth)

        ##add labels, etc
        ax1.set_ylabel('Value, A.U.',fontsize=14)
        ax1.yaxis.set_label_position("right")
        ax1.set_xlabel('Bins',fontsize=14)
        ax1.set_ylim(t2_val-0.15,t1_val+0.15)
        ax1.set_xlim(-self.show_n, 2) ##this should give us 2 secs of data visible
        ax1.set_title("Cursor value",fontsize=14,weight='bold')
        ##add the lines to this plot for the cursor
        self.line1 = Line2D([], [], color='black',linewidth=2) ##our cursor line
        self.line1t1 = Line2D([], [], color='red', linewidth=3,alpha=0.5,label="Rewarded target") ##the T1 line crossing
        self.line1t2 = Line2D([], [], color='black', linewidth=3,alpha=0.5,label="Unrewarded target") ##the T2 line crossing
        self.line1mid = Line2D([], [], color='black', linewidth=1,label="Baseline") ##the mid line crossing
        ax1.add_line(self.line1)
        ax1.add_line(self.line1t1)
        ax1.add_line(self.line1t2)
        ax1.add_line(self.line1mid)
        ax1.set_yticks([self.t2_val,self.mid_val,self.t1_val])
        ax1.set_yticklabels(['Unewarded','Baseline','Rewarded'])
        for ticklabel in ax1.get_xticklabels():
            ticklabel.set_fontsize(14)
        for ticklabel in ax1.get_yticklabels():
            ticklabel.set_fontsize(14)
        #legend=ax1.legend(bbox_to_anchor=(1.2, 1))
        #legend.get_frame().set_facecolor('none')

        #ax1.set_aspect('equal', 'datalim')

        ##add the stuff for the E1 plot
        ax2.set_ylabel('Sum of E1 spikes',fontsize=14)
        ax2.set_xlabel('Bins',fontsize=14)
        ax2.set_title("Ensemble 1 value",fontsize=14,weight='bold')
        self.line2 = Line2D([], [], color='green',linewidth=2)
        ax2.add_line(self.line2)
        ax2.set_xlim(-self.show_n, 2)
        ax2.set_ylim(0, np.nanmax(self.e1)+1)
        for ticklabel in ax2.get_xticklabels():
            ticklabel.set_fontsize(14)
        for ticklabel in ax2.get_yticklabels():
            ticklabel.set_fontsize(14)

        ##add the stuff for the E2 plot
        ax3.set_xlabel('Bins',fontsize=14)
        ax3.set_ylabel('Sum of E2 spikes',fontsize=14)
        ax3.set_title("Ensemble 2 value",fontsize=14,weight='bold')
        self.line3 = Line2D([], [], color='blue',linewidth=2)
        ax3.add_line(self.line3)
        ax3.set_xlim(-self.show_n, 2)
        ax3.set_ylim(0, np.nanmax(self.e2)+1)
        ax3.yaxis.tick_right()
        ax3.yaxis.set_label_position("right")
        for ticklabel in ax3.get_xticklabels():
            ticklabel.set_fontsize(14)
        for ticklabel in ax3.get_yticklabels():
            ticklabel.set_fontsize(14)

        animation.TimedAnimation.__init__(self, fig, interval=bin_size, blit=True)

    def _draw_frame(self, framedata):
        
        i = framedata

        self.line1.set_data(self.x[:], self.cval[i-self.show_n:i])
        self.line1t1.set_data(self.x[:], self.t1[i-self.show_n:i])
        self.line1t2.set_data(self.x[:], self.t2[i-self.show_n:i])
        self.line1mid.set_data(self.x[:], self.mid[i-self.show_n:i])

        self.line2.set_data(self.x[:], self.e1[i-self.show_n:i])

        self.line3.set_data(self.x[:], self.e2[i-self.show_n:i])

        self._drawn_artists = [self.line1, self.line1t1, self.line1t2, self.line1mid,
                               self.line2, self.line3]

    def new_frame_seq(self):
        return iter(np.arange(self.show_n, self.t.size))

    def _init_draw(self):
        lines = [self.line1, self.line1t1, self.line1t2,
                 self.line2, self.line3]
        for l in lines:
            l.set_data([], [])

    ##a sub-function to parse a single line in a log, 
    ##and return the cursor val and frequency components seperately.
    def read_line(self,string):
        label = None
        timestamp = None
        if string is not '':
            ##figure out where the commas are that separate E1 and E2
            comma_idx = [m.start() for m in re.finditer(',',string)]
            ##the E1 val is everything in front of comma 1
            E1_val = string[:comma_idx[0]]
            ##the E2 val is everything in between comma 1 and 2
            E2_val = string[comma_idx[0]+1:comma_idx[1]]
            ##the frequency is everything after but not the return character
            freq = string[comma_idx[1]+1:]
        return float(E1_val), float(E2_val), float(freq)

    ##this function parses a log into numpy arrays, including "pauses" for
    ##T1, T2, and timeouts
    def parse_log(self):
        ##compute some vars to save space later
        target_pause_bins = (self.target_pause*1000)/self.bin_size
        timeout_pause_bins = (self.timeout_pause*1000)/self.bin_size
        ##init some lists to store the data;
        ##we don't really know how long this log will be
        ##so its hard to pre-allocate
        e1 = []
        e2 = []
        cval = []
        log = open(self.log_path,'r')
        ##get the data from each line, excluding the return charageter
        line = log.readline()[:-1]
        while (line != ""): ##go until you run out of lines
            if line == "T1" or line == "T2": ##case target hit
                ##this is a "pause" for a certain number of seconds, so just add NaN
                for i in range(target_pause_bins): ##number of bins per pause time
                    e1.append(np.nan)
                    e2.append(np.nan)
                    cval.append(np.nan)
            elif line == "Timeout": ##case for timeout
                for i in range(timeout_pause_bins):
                    e1.append(np.nan)
                    e2.append(np.nan)
                    cval.append(np.nan)
            else: ##case for normal operation
                E1, E2, freq = self.read_line(line)
                e1.append(E1)
                e2.append(E2)
                cval.append(E1-E2)
            line = log.readline()[:-1]
        e1 = np.asarray(e1)
        e2 = np.asarray(e2)
        cval = np.asarray(cval)
        return e1, e2, cval

ani = SubplotAnimation(1.2,-1.2,0,r"C:\Users\Ryan\Desktop\log.txt")
plt.show()

