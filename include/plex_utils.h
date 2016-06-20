//utilities for interfacing with the plexon system
#ifndef __PLEX_UTILS_H__
#define __PLEX_UTILS_H__

#include <windows.h>
#include <Python.h>
#include <iostream>
#include "Plexon.h"
#include <string>
#include <stdlib.h>

//data structure to store information about what/how many units are sorted 
struct SortData
{
	int         active_channels;
	int         sorted_units;
	int         *units_per_chan;
	int         *chan_indices;
	std::string *unit_names;
	int         *unit_indices; //the index of the sorted units in the c-array returned by get_counts
	
	//using an explicit destructor to handle deletion of dynamically allocated arrays that will be passed in
	~SortData(){ 
    if (units_per_chan) delete[] units_per_chan;
    if (chan_indices) delete[] chan_indices;
    if (unit_names) delete[] unit_names;
	if (unit_indices) delete[] unit_indices;
  }
};

//The max number of events to read for each
//ping of the server
#define MAX_READ_EVENTS 		(500000)
//size of waveforms
#define MAX_WF_LENGTH   		(56)
//SortClient registers with type = 256
#define CLIENT_TYPE     		(256)
//MAP limits on channel count
#define MAX_CHANNELS			(128)
//Plexon convention- 4 units per channel
#define MAX_UNITS_PER_CHANNEL  	(4)

//function to open the client connection w/plexon MAP
extern "C" int open_client(void);

//function to close connection w/Plexon MAP
extern "C" void close_client(void);

//function to clear the hardware buffer
extern "C" void clear_buffer_c(void);

//function to call plexon API and put all event data into memory
extern "C" void get_data(int max_events, PL_Event* buffer);

//send an event trigger to hardware
extern "C" void send_user_event(int chan);

//a function to shift a buffer and append new data. Args are a pointer to the buffer,
//the length of the buffer, and the value of the new data to append. 
extern "C" void advance_buffer(int* buffer, int buff_len, int new_data);

//helper function to calculate the mean of a double array
//input vals are a pointer to the array, and the length of the array
extern "C" float arr_mean(int* d, int length);

//takes a python tuple of strings and converts it to a C array of strings
extern "C" void pystr_tuple_to_c_array(PyObject *tuple_of_strings, std::string *unit_names, int num_items);

//simple function which takes in a standard plexon unit string 
//such as "sig002a" and returns its number designation (from 0 to 511)
extern "C" int unit_string_to_num(std::string unit_name);

//function which takes in an array of unit name strings, an empty array for unit numbers, and
//the number of units in each string, and fills the empty array with the number corrsponding
//to the input strings.
extern "C" void get_unit_numbers_from_names(std::string* unit_names, 
	int * unit_nums, int num_units);

//a function to create a python list of strings from a C array of strings
extern "C" PyObject *convert_string_array(std::string c_array[], int length);

//a function to poll the server and return both the string names and unit
//indices of the currently sorted units. These are stored in a SortData struct.
extern "C" void get_sort_data(SortData* data);

//crazy simple function to convert a channel number and a unit number
//into a index value. Creating a function to do this so I don't make 
//any silly mistakes.
//basic idea is to take a channel number (ie 4) and a unit number (1,2,3,4 = a,b,c,d)
//and get a channel index number which indexes the unit out of 512 possible sorted units.
extern "C" int get_unit_index(int chan_num, int unit_num);

#endif