##function to animate/plot a log

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.animation as animation


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


        # self.t = np.linspace(0, 80, 400)
        # self.x = np.cos(2 * np.pi * self.t / 10.)
        # self.y = np.sin(2 * np.pi * self.t / 10.)
        # self.z = 10 * self.t

        ax1.set_ylabel('Cursor value',fontsize=14)
        ax1.set_xlabel('Bins',fontsize=14)
        ax1.set_ylim(t2_val-0.15,t1_val+0.15)
        ax1.set_xlim(-2000/bin_size, 2) ##this should give us 2 secs of data visible
        self.line1 = Line2D([], [], color='black',linewidth=2) ##our cursor line
        self.line1t1 = Line2D([], [], color='red', linewidth=3,alpha=0.5) ##the T1 line crossing
        self.line1t2 = Line2D([], [], color='black', linewidth=3,alpha=0.5) ##the T2 line crossing
        ax1.add_line(self.line1)
        ax1.add_line(self.line1t1)
        ax1.add_line(self.line1t2)
        ax1.set_aspect('equal', 'datalim')

        ax2.set_xlabel('Sum of E1 spikes',fontsize=14)
        ax2.set_ylabel('Bins',fontsize=14)
        self.line2 = Line2D([], [], color='green',linewidth=2)
        ax2.add_line(self.line2)
        ax2.set_xlim(-2000/bin_size, 2)
        ax2.set_ylim(0, 15)

        ax3.set_xlabel('Bins',fontsize=14)
        ax3.set_ylabel('Sum of E2 spikes',fontsize=14)
        self.line3 = Line2D([], [], color='blue',linewidth=2)
        ax3.add_line(self.line3)
        ax3.set_xlim(-2000/bin_size, 2)
        ax3.set_ylim(0, 15)

        animation.TimedAnimation.__init__(self, fig, interval=bin_size, blit=True)

    def _draw_frame(self, framedata):
        i = framedata
        head = i - 1
        head_slice = (self.t > self.t[i] - 1.0) & (self.t < self.t[i])

        self.line1.set_data(self.x[:i], self.y[:i])
        self.line1t1.set_data(self.x[head_slice], self.y[head_slice])
        self.line1t2.set_data(self.x[head], self.y[head])

        self.line2.set_data(self.y[:i], self.z[:i])

        self.line3.set_data(self.x[:i], self.z[:i])

        self._drawn_artists = [self.line1, self.line1a, self.line1e,
                               self.line2, self.line3]

    def new_frame_seq(self):
        return iter(range(self.t.size))

    def _init_draw(self):
        lines = [self.line1, self.line1t1, self.line1t2,
                 self.line2, self.line3]
        for l in lines:
            l.set_data([], [])

    ##a sub-function to parse a single line in a log, 
    ##and return the cursor val and frequency components seperately.
    def read_line(string):
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
            freq = string[comma_idx[1]+1:-1]
        return float(E1_val), float(E2_val), float(freq)

    ##this function parses a log into numpy arrays, including "pauses" for
    ##T1, T2, and timeouts
    def parse_log(self):
        ##init some lists to store the data;
        ##we don't really know how long this log will be
        ##so its hard to pre-allocate
        e1 = []
        e2 = []
        log = open(self.log_path,'r')






ani = SubplotAnimation()
# ani.save('test_sub.mp4')
plt.show()