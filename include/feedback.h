//functions to produce the auditory feedback for BMI

#ifndef __FEEDBACK_H__
#define __FEEDBACK_H__

#include "SineWave.h"
#include "RtAudio.h"
#include "Stk.h"
#include <iostream>
#include <windows.h>
#include <time.h>
#include <stdlib.h>
#include "RtWvOut.h"
#include <math.h>
#include "Noise.h"

class FeedbackParams{
public:
	//default constructor
	FeedbackParams(void);
	//functions to get/set frequency
	void set_current_freq(float f);
	float get_current_freq(void);
	void set_new_freq(float f);
	float get_new_freq(void);
	//function to get/set sample interval
	void set_interval(int i);
	int get_interval(void);
	//functions to get/set midpoint value
	void set_midpoint(float m);
	float get_midpoint(void);
	//functions to get/set start and stop trigger
	void set_trigger(bool t);
	bool get_trigger(void);

private:
	//sound variables
	float current_freq;
	float new_freq;
	int interval;
	float midpoint;
	bool trigger;
};

//This tick() function handles the computation of 
// the audio tone samples. It is called automatically when the 
//system is ready for a new buffer of audio samples
extern "C" int tick( void *outputBuffer, void *inputBuffer, unsigned int nBufferFrames, double streamTime, RtAudioStreamStatus status, void *dataPointer );

//thread function to slide the audio freq between two cursor values
DWORD WINAPI audio_slide(LPVOID lpParam);

///function to handle playback
DWORD WINAPI play_feedback(LPVOID lpParam);

//function to start a playback thread
extern "C" void init_feedback(FeedbackParams *params);

//function to play a noise burst
DWORD WINAPI noise_thread(LPVOID lpParam);

//function to start noise burst thread
extern "C" void noise_burst(void);

#endif