//BMI_reward.h
//header file for BMI_reward.cpp
#ifndef __REWARD_H__
#define __REWARD_H__


#include "NIDAQmxBase.h"
#include <windows.h>
#include <stdio.h>

#define DAQmxErrChk(functionCall) { if( DAQmxFailed(error=(functionCall)) ) { goto Error; } }

//arg should be in format "Dev1/port0"
int writePort (char *chan, int val);

//arg should be in format "Dev1/port0"
int readPort (char *chan);

//Trigger the behavior box. Arguments are a device number and a device channel number.
extern "C" void trigger_abet(int device, int port);

//Trigger the nidaq for a particular pulse duration. Same as above + the duration arg in ms
extern "C" void trigger_abet_ex(int device, int port, int duration);

//Get the value of the NIDAQ DIO device
extern "C" int read_abet(int device, int port);

#endif