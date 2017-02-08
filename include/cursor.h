///A function to return a cursor value from the plexon system

#ifndef __CURSOR_H__
#define __CURSOR_H__
#include <windows.h>
#include <Python.h>
#include <iostream>
#include "Plexon.h"
#include <string>
#include <stdlib.h>
#include "plex_utils.h"
#include <time.h>

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

class CursorParams{
public:
	//default constructor
	CursorParams(void);
	//functions to get and set parameters
	float get_e1_val(void);
	float get_e2_val(void),
	void set_e1_val(float v);
	void set_e2_val(float v);
	int get_samp_int(void);
	void set_samp_int(int i);
	int get_smooth_int(void);
	void set_smooth_int(int i);
	std::string* get_e1_names(void);
	std::string* get_e2_names(void);
	void set_e1_names(std::string *names);
	void set_e2_names(std::string *names); 
	int get_num_e1(void);
	void set_num_e1(int i);
	int get_num_e2(void);
	void set_num_e2(int i);
	bool is_engaged(void);
	void set_engage(bool b);
	bool params_set(void);
	void params_var(bool b);
	HANDLE cursorMutex;
private:
	//cursor variables
	float e1_val;
	float e2_val;
	int samp_int;
	int smooth_int;
	std::string* e1_names;
	std::string* e2_names;
	int num_e1;
	int num_e2;
	bool params;
	bool engage;
};

//this function takes in an array a value, and the array length and checks
//to see if any of the array members match the value.
//if so, it reurns the index of the matching array element. 
//Otherwise, the function returns -1.
//NOTE: if the value argument is in the array more than once, 
//this function will still only return the index value of its
//FIRST occurance.
extern "C" int check_if_member(int* input_array, int value, int array_len);

//a function to calculate "e1 and e2" summed spike counts given two arrays of unit indices (e1 and e2)
extern "C" void get_ensemble_counts(PL_Event* data, int *e1_counts, int *e2_counts, 
	int*e1_indices, int*e2_indices, int num_e1, int num_e2, int num_events);

//function to return the value of the cursor 
extern "C" int get_cursor(std::string* e1_names, std::string* e2_names, 
	int num_e1, int num_e2, int interval);

//a function to collect raw e1/e2 ensemble values
extern "C" void get_raw_ensembles(std::string* e1_names, std::string* e2_names, 
	int num_e1, int num_e2, int* ve1, int* ve2, int interval);

DWORD WINAPI cursor_thread(LPVOID lpParam);

//function to start a cursor thread
extern "C" void init_cursor(CursorParams *params);

#endif