//utilities for interfacing with the plexon system

#include "plex_utils.h"

//function to open the client connection w/plexon MAP
extern "C" int open_client(void)
{
	//client type: Sort Client registers with type = 256, 
	//electrode type = 1; 0 is also a possible argument
	int client_type;
	//a value to store the result of the client initialization
	int h;
	//an int to store success or failure of connection
	int result;
	
	client_type = CLIENT_TYPE;
	
	//initialize client
	h = PL_InitClient(client_type, NULL);
	
	//return a success/failure message
	if(h > 0)
	{
		result = 1;
	}
	else
	{
		result = 0;
	}
	return result;
}

//function to close connection w/Plexon MAP
extern "C" void close_client(void)
{
	//close client
	PL_CloseClient();

	const char* result;
	result = "Connection to client closed.";
}

//function to clear the hardware buffer
extern "C" void clear_buffer_c(void)
{
	int events = 1;
	//call the "get timestamp" function, which clears the hardware buffer
	PL_Event* temp = (PL_Event*)malloc(sizeof(PL_Event)*events);
	//store it in a temp memory block 
	PL_GetTimeStampStructures(&events, temp);
	free(temp);
}

//function to call plexon API and put all event data into memory
extern "C" void get_data(int max_events, PL_Event* buffer)
{
	
	//** call the Server to get all the MAP events since the last time we called PL_GetTimeStampStructures
    //here you call this function, whose implementation is hidden. BUT, you feed it the address of a memory
    //location containing the max number of events that can be returned, as well as the pointer to the
    //start of the block of PL_Event objects. Then, I'm guessing it fills in all of the events with events
    //that occurred since the last call to this function.
	PL_GetTimeStampStructures(&max_events, buffer);
	
}

//send an event trigger to hardware
extern "C" void send_user_event(int chan)
{
	//send event
	PL_SendUserEvent(chan);
}

//helper function to calculate the mean of a double array
//input vals are a pointer to the array, and the length of the array
extern "C" float arr_mean(int* d, int length)
{
	//variable to store the sum
	float total = 0;
	//result var
	float result;
	for (int i = 0; i < length; i++)
	{
		total +=float(d[i]);
	}
	result = total/length;
	return result;
}

//a function to shift a buffer and append new data. Args are a pointer to the buffer,
//the length of the buffer, and the value of the new data to append. 
extern "C" void advance_buffer(int* buffer, int buff_len, int new_data)
{
	//shift the buffer
	for(int i = 0; i < buff_len-1; i++)
	{
		buffer[i] = buffer[i+1];
	}
	//append the new data
	buffer[buff_len-1] = new_data;
}

//takes a python tuple of strings and converts it to a C array of strings
extern "C" void pystr_tuple_to_c_array(PyObject *tuple_of_strings, std::string *unit_names, int num_items)
{
	for(int i = 0; i < num_items; i++)
	{
		//grab i-th item, doesn't work well if tuple has only one item so need to handle that
		PyObject* py_string = PyTuple_GetItem(tuple_of_strings, i);
		//convert to cpp string
		std::string cpp_string = PyString_AsString(py_string);
		//add to c array
		unit_names[i] = cpp_string;
	}

}


//simple function which takes in a standard plexon unit string 
//such as "sig002a" and returns its number designation (from 0 to 511)
extern "C" int unit_string_to_num(std::string unit_name)
{
		//unit number; a=1, b=2 etc
		int unit_num;
		//channel number
		int chan_num;
		//full unit number designation to return
		int full_unit_number;
		//get just the channel info from the string
		std::string channel = unit_name.substr(3,3);
		//get just the unit number from the string
		std::string unit = unit_name.substr(6);
		//convert to an int and subtract 1 (plexon starts at 1, our array starts at 0)
		chan_num = atoi(channel.c_str()) -1;
		//get the unit number
		//not sure if these definitions are necessary
		std::string a = "a";
		std::string b = "b";
		std::string c = "c";
		if (unit==a)
		{
			unit_num = 0;
		}
		else if (unit==b)
		{
			unit_num = 1;
		}
		else if (unit==c)
		{
			unit_num = 2;
		}
		else
		{
			unit_num = 3;
		}
		//generate the value that can be used to index the array
		full_unit_number = get_unit_index(chan_num, unit_num);
		//return the result
		return full_unit_number;
}

//function which takes in an array of unit name strings, an empty array for unit numbers, and
//the number of units in each string, and fills the empty array with the number corrsponding
//to the input strings.
extern "C" void get_unit_numbers_from_names(std::string* unit_names, int * unit_nums, int num_units)
{
	for(int i = 0; i < num_units; i++)
	{
		int unit_num = unit_string_to_num(unit_names[i]);
		unit_nums[i] = unit_num;
	}
}

//a function to create a python list of strings from a C array of strings
extern "C" PyObject *convert_string_array(std::string c_array[], int length)
{
	PyObject *item;
	PyObject *pylist = PyTuple_New(length);
	for(int p = 0; p<length; p++)
	{
		const char * g = c_array[p].c_str();
		//PySys_WriteStdout(g);
		item = PyString_FromString(g);
		PyTuple_SetItem(pylist, p, item);
	}
	return pylist;
}


//crazy simple function to convert a channel number and a unit number
//into a index value. Creating a function to do this so I don't make 
//any silly mistakes.
//basic idea is to take a channel number (ie 4) and a unit number (1,2,3,4 = a,b,c,d)
//and get a channel index number which indexes the unit out of 512 possible sorted units.
extern "C" int get_unit_index(int chan_num, int unit_num)
{
	int unit_index = (chan_num*4) + unit_num;
	return unit_index;
}

//a function to poll the server and return both the string names and unit
//indices of the currently sorted units. These are stored in a SortData struct.
extern "C" void get_sort_data(SortData* data)
{
	//total possible channels
	int num_chans = 128;
	//total number of channels with 1 or more sorted units
	int total_active_channels = 0;
	//total number of units sorted across all channels
	int total_sorted_units = 0;
	//pointer to pass to the plexon API function.
	//Using calloc so that values are initialized to 0
	int* unit_counts;
	unit_counts = (int*)calloc(num_chans, sizeof(int));
	
	//call function to return a 1x128 array of the number of
	//units sorted on each existing channel
	PL_GetNumUnits(unit_counts);
	data->units_per_chan = unit_counts;
	
	//figure out how many channels have sorted units, 
	//as well as how many units are sorted overall (better way to do this??)
	for(int i = 0; i < num_chans; i++)
	{
		if(unit_counts[i] != 0)
		{
			total_active_channels++;
			total_sorted_units += unit_counts[i];
		}
	}
	data->active_channels = total_active_channels;
	data->sorted_units = total_sorted_units; 

	//figure out the indices of channels with sorted units
	int* sorted_chan_indices = new int[total_active_channels];
	int n = 0;
	for(int j = 0; j < num_chans; j++)
	{
		if(unit_counts[j] != 0)
		{
			sorted_chan_indices[n] = j;
			n++;
		}
	}
	data->chan_indices = sorted_chan_indices;

	//string array to hold all of the generated strings
	std::string* unit_names = new std::string[total_sorted_units];

	//array to hold indices of sorted units
	int* sorted_unit_indices = new int[total_sorted_units];

	//conter to advance the index through unit_names
	int y = 0;

	//run through all the sorted channels and generate the strings for unit names
	for(int f = 0; f < total_active_channels; f++)
	{
		//get the f-th index of the channels with sorted spikes
		int current_index = sorted_chan_indices[f];
		//how many units are sorted on that channel
		int units_sorted = unit_counts[current_index];
		//generate the string base to add to later
		std::string name_string = "sig";
		//the number of zeros to add to the name based on the channel number
		std::string zero_pad;
		//the letter index of the unit
		std::string unit_letter;
		//the length of the name base string
		int name_len = 3;
		//figure out the zero padding based on the channel number
		if(current_index <= 8)
		{
			zero_pad = "00";
			name_len += 2;
		}
		else if(current_index <= 98)
		{
			zero_pad = "0";
			name_len += 1;
		}
		else
		{
			zero_pad = "";
		}
		//add zero padding to the string
		name_string.insert(3,zero_pad);
		//convert the channel number to an int
		char intStr[3]; 
		_itoa(current_index+1, intStr, 10); //*****
		std::string channel_string = std::string(intStr);
		//add the channel number to the string
		name_string.insert(name_len, channel_string);
		//add a dummy unit number to the string (will be replaced later)
		name_string.insert(6, "x");
		//go through all the units sorted on the current channel,
		//add the unit letter index to the string, and finally add the 
		//whole damn thing to the main string array
		for(int x = 0; x < units_sorted; x++)
		{
			//add the c-array index of the units a la get_counts
			sorted_unit_indices[y] = current_index*4 + x;
			//add the unit letter designation
			switch(x)
			{
				case 0:
					unit_letter = "a";
					name_string.replace(6,1,unit_letter);
					unit_names[y] = name_string;
					y++;
					break;
				case 1:
					unit_letter = "b";
					name_string.replace(6,1,unit_letter);
					unit_names[y] = name_string;
					y++;
					break;
				case 2:
					unit_letter = "c";
					name_string.replace(6,1,unit_letter);
					unit_names[y] = name_string;
					y++;
					break;
				case 3:
					unit_letter = "d";
					name_string.replace(6,1,unit_letter);
					unit_names[y] = name_string;
					y++;
					break;
			}
		}
	}
	data->unit_indices = sorted_unit_indices;
	data->unit_names = unit_names;
	const char * w = data->unit_names[3].c_str();
}