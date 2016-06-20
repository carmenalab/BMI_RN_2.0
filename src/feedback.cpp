//functions to produce the auditory feedback for BMI

#include "feedback.h"

//Parameters for sound generation
//constructor
FeedbackParams::FeedbackParams(void)
{
	//initialize state var
	trigger = false;
}

//functions to get/set frequency
void FeedbackParams::set_current_freq(float f)
{
	current_freq = f;
}

float FeedbackParams::get_current_freq(void)
{
	return current_freq;
}

void FeedbackParams::set_new_freq(float f)
{
	new_freq = f;
}

float FeedbackParams::get_new_freq(void)
{
	return new_freq;
}

//function to get/set sample interval
void FeedbackParams::set_interval(int i)
{
	interval = i;
}

int FeedbackParams::get_interval(void)
{
	return interval;
}

//functions to get/set midpoint value
void FeedbackParams::set_midpoint(float m)
{
	midpoint = m;
}

float FeedbackParams::get_midpoint(void)
{
	return midpoint;
}

//functions to get/set start and stop trigger
void FeedbackParams::set_trigger(bool t)
{
	trigger = t;
}

bool FeedbackParams::get_trigger(void)
{
	return trigger;
}

namespace stk{

//This tick() function handles the computation of 
// the audio tone samples. It is called automatically when the 
//system is ready for a new buffer of audio samples
extern "C" int tick( void *outputBuffer, void *inputBuffer, unsigned int nBufferFrames, double streamTime, RtAudioStreamStatus status, void *dataPointer )

{
	//make a pointer to the data pointer; cast it as a
	//SineWave object type because our data will be a sine wave
	SineWave *sine = (SineWave *) dataPointer;
	//pointer to the output buffer; cast it as a StkFloat type
	StkFloat *samples = (StkFloat *) outputBuffer;
	//generate the samples
	for (unsigned int i = 0; i < nBufferFrames; i++)
	{
		*samples++ = sine->tick();
	}
	return 0;
}


DWORD WINAPI play_feedback(LPVOID lpParam)
{
	//cast input parameters
	FeedbackParams *params = (FeedbackParams*)lpParam;
	//create sinewave and RTaudio objects
	SineWave sine;
	RtAudio dac;
	//set the sample rate
	Stk::setSampleRate(44100.0);
	//figure out how many bytes in an StkFloat and set up the RtAudio stream
	RtAudio::StreamParameters parameters;
	//set the dav to output to the default audio controller
	parameters.deviceId = dac.getDefaultOutputDevice();
	//set channels to 1
	parameters.nChannels = 1;
	//get the size of RtAudio float type
	RtAudioFormat format = (sizeof(StkFloat) == 8) ? RTAUDIO_FLOAT64 : RTAUDIO_FLOAT32;
	unsigned int bufferFrames = RT_BUFFER_SIZE;
	sine.setFrequency(params -> get_current_freq());
	
	//pull data from the callback function
	try
	{
		dac.openStream( &parameters, NULL, format, (unsigned int)Stk::sampleRate(), &bufferFrames, &tick, (void *)&sine );
	}
	catch (RtAudioError &error)
	{
		error.printMessage();
		goto cleanup;
	}

	try 
	{
		dac.startStream();
	} 

	catch (RtAudioError &error)
	{
		error.printMessage();
		goto cleanup;
	}

	 // Block waiting here.
	while (params -> get_trigger() == true)
	{
		sine.setFrequency(params -> get_current_freq());
	}

  	// Shut down the output stream.
  	try 
  	{
    	dac.closeStream();
  	}
  	catch ( RtAudioError &error ) 
  	{
    	error.printMessage();
  	}
	cleanup:

	return NULL;
}

DWORD WINAPI audio_slide(LPVOID lpParam)
{
	//cast input parameters
	FeedbackParams* params = (FeedbackParams*)lpParam;
	//a variable to store the frequency increment
	float increment;
	//variable to store the number of audio samples per data sample. Underestimating the
	//number of samples to account for processing lag
	int numPoints = params -> get_interval();

	while(params -> get_trigger() == true)
	{	
		//check to see if the new frequency and old freq are different
		if (params -> get_current_freq() != params -> get_new_freq())
		{
			//slide the audio value up to match
			increment = (params -> get_new_freq() - params -> get_current_freq())/numPoints;
			for (int i = 0; i < numPoints; i++)
			{
				float v = params -> get_current_freq() + increment;
				params -> set_current_freq(v);
				Sleep(1);
			}
		}
	}
	return NULL;
}

//function to start a playback thread
extern "C" void init_feedback(FeedbackParams *params)
{
	//start a thread to execute sound playback 
	//thread variables
	DWORD playerId; 
	HANDLE playerThread;

	playerThread = CreateThread(
	NULL, // default security attributes
	0, // use default stack size
	play_feedback, // thread function
	params, // argument to thread function (global cursor struct)
	0, // use default creation flags
	&playerId); // returns the thread identifier)

	if (playerThread == NULL)
	printf("CreateThread() failed, error: %d.\n", GetLastError());

	//start a thread to execute slides between cursor values
	//thread variables
	DWORD slideId; 
	HANDLE slideThread;

	slideThread = CreateThread(
	NULL, // default security attributes
	0, // use default stack size
	audio_slide, // thread function
	params, // argument to thread function (global cursor struct)
	0, // use default creation flags
	&slideId); // returns the thread identifier)

	if (slideThread == NULL)
	printf("CreateThread() failed, error: %d.\n", GetLastError());
}

//function to play a noise burst with input value = number of seconds to play for
DWORD WINAPI noise_thread(LPVOID lpParam)
{
	Stk::setSampleRate(44100.0);
	Stk::showWarnings(true);

	int nFrames = 100000;
	Noise noiseBurst;
	RtWvOut *dac = 0;
	try 
	{
    	// Define and open the default realtime output device for one-channel playback
    	dac = new RtWvOut( 1 );
  	}
 	catch ( StkError & ) 
 	{
    	exit( 1 );
  	}

  	noiseBurst.setSeed();

  	for ( int i=0; i<nFrames; i++ ) 
  	{
    	try 
    	{
      		dac->tick( noiseBurst.tick() );
     	}
    	catch ( StkError & ) 
    	{
      	goto cleanup;
    	}
  	}
 	cleanup:
  	delete dac;

  	return NULL;
}

//function to start noise burst thread
extern "C" void noise_burst(void)
{
	//start a thread to execute sound playback 
	//thread variables
	DWORD noiseId; 
	HANDLE noiseThread;

	noiseThread = CreateThread(
	NULL, // default security attributes
	0, // use default stack size
	noise_thread, // thread function
	NULL, // argument to thread function (global cursor struct)
	0, // use default creation flags
	&noiseId); // returns the thread identifier)

	if (noiseThread == NULL)
	printf("CreateThread() failed, error: %d.\n", GetLastError());
}
} //stk namespace