///A function to return a cursor value from the plexon system

#include "cursor.h"

//define class member functions
//constructor
CursorParams::CursorParams(void)
{
	//initialize state variables
	engage = false;
	params = false;
	cursorMutex = CreateMutex(        
		NULL,              // default security attributes
        FALSE,             // initially not owned
        NULL);             // unnamed mutex)
}

float CursorParams::get_cursor_val(void)
{
	float f;
	WaitForSingleObject((cursorMutex), INFINITE);
	__try{
		f = cursor_val;
	}
	__finally{
		ReleaseMutex((cursorMutex));
	}	
	return f;
}
void CursorParams::set_cursor_val(float v)
{
	WaitForSingleObject((cursorMutex), INFINITE);
	__try{
		cursor_val = v;
	}
	__finally{
		ReleaseMutex((cursorMutex));
	}	
}
int CursorParams::get_samp_int(void)
{
	return samp_int;
}
void CursorParams::set_samp_int(int i)
{
	samp_int = i;
}
int CursorParams::get_smooth_int(void)
{
	return smooth_int;
}
void CursorParams::set_smooth_int(int i)
{
	smooth_int = i;
}
std::string* CursorParams::get_e1_names(void)
{
	return e1_names;
}
std::string* CursorParams::get_e2_names(void)
{
	return e2_names;
}
void CursorParams::set_e1_names(std::string *names)
{
	e1_names = names;
}
void CursorParams::set_e2_names(std::string *names)
{
	e2_names = names;
} 
int CursorParams::get_num_e1(void)
{
	return num_e1;
}
void CursorParams::set_num_e1(int i)
{
	num_e1 = i;
}
int CursorParams::get_num_e2(void)
{
	return num_e2;
}
void CursorParams::set_num_e2(int i)
{
	num_e2 = i;
}
bool CursorParams::is_engaged(void)
{
	return engage;
}
void CursorParams::set_engage(bool b)
{
	engage = b;
}
bool CursorParams::params_set(void)
{
	return params;
}
void CursorParams::params_var(bool b)
{
	params = b;
}

//this function takes in an array a value, and the array length and checks
//to see if any of the array members match the value.
//if so, it reurns the index of the matching array element. 
//Otherwise, the function returns -1.
//NOTE: if the value argument is in the array more than once, 
//this function will still only return the index value of its
//FIRST occurance.
extern "C" int check_if_member(int* input_array, int value, int array_len)
{
	//index value to store and return
	int index = -1;
	//run through the array and compare values
	for(int i = 0; i < array_len; i++)
	{
		//if the value matches, store the index and stop indexing
		if(input_array[i] == value)
		{
			index = i;
			break;
		}
	}
	return index;
}


//a function to calculate "e1 and e2" summed spike counts given two arrays of unit indices (e1 and e2)
extern "C" void get_ensemble_counts(PL_Event* data, int *e1_counts, int *e2_counts, 
	int*e1_indices, int*e2_indices, int num_e1, int num_e2, int num_events)
{
	int current_unit_number;
	int e1_index;
	int e2_index;
	//** step through the array of MAP events, counting only the spike timestamps
    //You get a random smattering of events here, that aren't in any particular order.
    //So, you need to determine if each one is actually a spike event.
    for (int i = 0; i < num_events; i++)
    {
        //** is this the timestamp of a sorted spike?
        //and, is the unit in our list of units to store data from?
        //Here we are checking if the current event is a) a spike ts (PL_singlewftype)
        //b) if it is a sorted unit (on a given channel, unsorted spikes are 0, and 
        //a,b,c,d = 1,2,3,4). What we are NOT checking in this instance is the channel
        //number, which is represented by a short value that we COULD check by calling 
        //pServerEventBuffer.Channel
    	current_unit_number = get_unit_index((data[i].Channel-1), (data[i].Unit-1));
    	e1_index = check_if_member(e1_indices, current_unit_number, num_e1);
    	e2_index = check_if_member(e2_indices, current_unit_number, num_e2);
    	if (data[i].Type == PL_SingleWFType && //** spike timestamp
          data[i].Unit >= 1 &&               //** 1,2,3,4 = a,b,c,d units, unsorted spikes have Unit == 0
          e1_index != -1) //is part of the e1 ensemble
      
      {  
		  *e1_counts+=1;
      }
      if (data[i].Type == PL_SingleWFType && //** spike timestamp
          data[i].Unit >= 1 &&               //** 1,2,3,4 = a,b,c,d units, unsorted spikes have Unit == 0
          e2_index != -1) //is in the e2 ensemble
      
      {  
		  *e2_counts+=1;
      }
  	}
}

//a function to get the cursor value; taking into account the weights of the ensembles over a given
//time interval
extern "C" int get_cursor(std::string* e1_names, std::string* e2_names, 
	int num_e1, int num_e2, int interval)
{
	//WINAPI types to store high-resolution time stamps
	LARGE_INTEGER StartingTime, EndingTime, ElapsedMilliseconds;
	LARGE_INTEGER Frequency;
	int time_lost;
	//get the system processor time frequency value
	QueryPerformanceFrequency(&Frequency);
	//start a client connection
	//open_client();
	//clear the buffer
	clear_buffer_c();
	//start the high resolution clock
	QueryPerformanceCounter(&StartingTime);
	//set vars
	int max_channels = MAX_CHANNELS;
	int max_units_per_channel = MAX_UNITS_PER_CHANNEL;
	int max_read_events = MAX_READ_EVENTS;
	int cursor_val;
	//variables to store counts
	int e1_counts = 0;
	int e2_counts = 0;
	//variables to store unit info
	int* e1_indices = new int[num_e1];
	int* e2_indices = new int[num_e2];
	//convert string names to unit numbers
	get_unit_numbers_from_names(e1_names, e1_indices, num_e1);
	get_unit_numbers_from_names(e2_names, e2_indices, num_e2);
	//allocate memory to store hardware data
	PL_Event* data_buffer = (PL_Event*)malloc(sizeof(PL_Event)*max_read_events);
	//pause for the requested duration minus the time lost parsing the names
	//figure out how much time has elapsed
	QueryPerformanceCounter(&EndingTime);
	ElapsedMilliseconds.QuadPart = EndingTime.QuadPart-StartingTime.QuadPart;
	ElapsedMilliseconds.QuadPart *= 1000;
	ElapsedMilliseconds.QuadPart /= Frequency.QuadPart;
	time_lost = ElapsedMilliseconds.QuadPart;
	if(time_lost < interval)
	{
		Sleep(interval-time_lost);
	}
	//get the data from the hardware
	get_data(max_read_events, data_buffer);
	//get e1 and e2 values
	get_ensemble_counts(data_buffer, &e1_counts, &e2_counts, e1_indices, 
		e2_indices, num_e1, num_e2, max_read_events);
	cursor_val = (e1_counts)-(e2_counts);
	delete[] e1_indices;
	delete[] e2_indices;
	free(data_buffer);
	return cursor_val;
}

//a function to collect raw e1/e2 ensemble values
extern "C" void get_raw_ensembles(std::string* e1_names, std::string* e2_names, 
	int num_e1, int num_e2, int* ve1, int* ve2, int interval)
{
	//WINAPI types to store high-resolution time stamps
	LARGE_INTEGER StartingTime, EndingTime, ElapsedMilliseconds;
	LARGE_INTEGER Frequency;
	int time_lost;
	//get the system processor time frequency value
	QueryPerformanceFrequency(&Frequency);
	//start a client connection
	//open_client();
	//clear the buffer
	clear_buffer_c();
	//start the high resolution clock
	QueryPerformanceCounter(&StartingTime);
	//set vars
	int max_channels = MAX_CHANNELS;
	int max_units_per_channel = MAX_UNITS_PER_CHANNEL;
	int max_read_events = MAX_READ_EVENTS;
	//variables to store unit info
	int* e1_indices = new int[num_e1];
	int* e2_indices = new int[num_e2];
	//convert string names to unit numbers
	get_unit_numbers_from_names(e1_names, e1_indices, num_e1);
	get_unit_numbers_from_names(e2_names, e2_indices, num_e2);
	//allocate memory to store hardware data
	PL_Event* data_buffer = (PL_Event*)malloc(sizeof(PL_Event)*max_read_events);
	//pause for the requested duration minus the time lost parsing the names
	//figure out how much time has elapsed
	QueryPerformanceCounter(&EndingTime);
	ElapsedMilliseconds.QuadPart = EndingTime.QuadPart-StartingTime.QuadPart;
	ElapsedMilliseconds.QuadPart *= 1000;
	ElapsedMilliseconds.QuadPart /= Frequency.QuadPart;
	time_lost = ElapsedMilliseconds.QuadPart;
	if(time_lost < interval)
	{
		Sleep(interval-time_lost);
	}
	//get the data from the hardware
	get_data(max_read_events, data_buffer);
	//get e1 and e2 values
	get_ensemble_counts(data_buffer, ve1, ve2, e1_indices, 
		e2_indices, num_e1, num_e2, max_read_events);
	delete[] e1_indices;
	delete[] e2_indices;
	free(data_buffer);
}

DWORD WINAPI cursor_thread(LPVOID lpParam)
{
	/* initialize random seed: */
  	//srand (time(NULL));
	//cast input parameters
	CursorParams* params = (CursorParams*)lpParam;
	int *buffer;
	int val;
	float smoothed_val;
	//create a buffer
	buffer = new int[params->get_smooth_int()];
	//fill with zeros
	for(int i = 0; i < params->get_smooth_int(); i++)
	{
		buffer[i] = 0;
	}
	while (params -> is_engaged() == true)
	{
		//val = rand() %100;
		val = get_cursor(params->get_e1_names(), params->get_e2_names(), 
			params->get_num_e1(),params->get_num_e2(), params->get_samp_int());
		advance_buffer(buffer, params->get_smooth_int(), val);
		smoothed_val = arr_mean(buffer, params->get_smooth_int());
		params->set_cursor_val(float(smoothed_val));
	}
	delete[] buffer;
	return NULL;
}

//function to start a cursor thread
extern "C" void init_cursor(CursorParams *params)
{
	//start a thread to execute sound playback 
	//thread variables
	DWORD cursorId; 
	HANDLE cursorThread;

	cursorThread = CreateThread(
	NULL, // default security attributes
	0, // use default stack size
	cursor_thread, // thread function
	params, // argument to thread function (global cursor struct)
	0, // use default creation flags
	&cursorId); // returns the thread identifier)

	if (cursorThread == NULL)
	printf("CreateThread() failed, error: %d.\n", GetLastError());
}
