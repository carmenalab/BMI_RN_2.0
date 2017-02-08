//master functions to control BMI funcions via Python

#include "plex_utils.h"
#include "cursor.h"
#include <Python.h>
#include "feedback.h"
#include "reward.h"
#include <string>
#include <stdlib.h>

//initialize a FeedbackParams object to control sound output
FeedbackParams feedback_params;
//initialize a CursorParams object
CursorParams cursor_params;

//a function to open a connection to the plexon server
static PyObject* connect_client(PyObject* self, PyObject* args)
{
	int result;
	result = open_client();
	if(result ==1)
	{
		PyGILState_STATE state1 = PyGILState_Ensure();
		PySys_WriteStdout("Client connected.\n");
		PyGILState_Release(state1);
	}
	if(result==0)
	{
		PyGILState_STATE state1 = PyGILState_Ensure();
		PySys_WriteStdout("Client connection failed; check MAP!\n");
		PyGILState_Release(state1);
	}
	PyGILState_STATE state = PyGILState_Ensure();
	Py_INCREF(Py_None);
	PyGILState_Release(state);
	return Py_None;
}

//a function to close the connection to the plexon server
static PyObject* disconnect_client(PyObject* self, PyObject* args)
{
	close_client();
	PyGILState_STATE state = PyGILState_Ensure();
	Py_INCREF(Py_None);
	PyGILState_Release(state);
	return Py_None;
}

//A function that returns a python list of all units currently sorted in SortClient
static PyObject* get_sorted_units(PyObject* self, PyObject* args)
{
	//open a client connection
	int result = open_client();
	//PyObject to return
	PyObject *converted_names_list;
	//SortData object to pass to function
	SortData *sorted_unit_data = new SortData;
	//compute sorted data
	get_sort_data(sorted_unit_data);
	//convert the string array to a python object
	converted_names_list = convert_string_array(sorted_unit_data->unit_names, sorted_unit_data->sorted_units);
	//close client connection
	close_client();
	delete sorted_unit_data;
	return Py_BuildValue("O", converted_names_list);
}

//function to send an event trigger
static PyObject* send_event(PyObject* self, PyObject* args)
{
	int chan;
	//parse arguments from python
	 if (!PyArg_ParseTuple(args, "i", &chan))
		return NULL;
	send_user_event(chan);
	PyGILState_STATE state = PyGILState_Ensure();
	Py_INCREF(Py_None);
	PyGILState_Release(state);
	return Py_None;
}

//function to set the cursor parameters
static PyObject* set_cursor_params(PyObject* self, PyObject* args)
{
	PyObject* e1_names;
	PyObject* e2_names;
	int num_e1; 
	int num_e2;
	int samp_int;
	int smooth_int;
	//parse arguments from python
	 if (!PyArg_ParseTuple(args, "OOiiii", &e1_names, &e2_names, 
	 	&num_e1, &num_e2, &samp_int, &smooth_int))
		return NULL;
	//convert tuple of names to C-friendly array
	std::string* e1_names_c = new std::string[num_e1];
	std::string* e2_names_c = new std::string[num_e2];
	PyGILState_STATE state1 = PyGILState_Ensure();
	pystr_tuple_to_c_array(e1_names, e1_names_c, num_e1);
	pystr_tuple_to_c_array(e2_names, e2_names_c, num_e2);
	PyGILState_Release(state1);
	//set parameters
	cursor_params.set_e1_names(e1_names_c);
	cursor_params.set_e2_names(e2_names_c);
	cursor_params.set_num_e1(num_e1);
	cursor_params.set_num_e2(num_e2);
	cursor_params.set_samp_int(samp_int);
	cursor_params.set_smooth_int(smooth_int);
	cursor_params.params_var(true);
	PyGILState_STATE state = PyGILState_Ensure();
	Py_INCREF(Py_None);
	PyGILState_Release(state);
	return Py_None;
}

//function to start the thread to begin calculating the cursor value
static PyObject* start_cursor(PyObject* self, PyObject* args)
{
	//check to see if the parameters have been set
	if (cursor_params.params_set() == false)
	{
		PyGILState_STATE state1 = PyGILState_Ensure();
		PySys_WriteStdout("Set parameters first!.\n");
		PyGILState_Release(state1);
	}
	else
	{
		cursor_params.set_engage(true);
		init_cursor(&cursor_params);
	}
	PyGILState_STATE state = PyGILState_Ensure();
	Py_INCREF(Py_None);
	PyGILState_Release(state);
	return Py_None;
}

static PyObject* stop_cursor(PyObject* self, PyObject* args)
//check to see if the parameters have been set
{	
	if (cursor_params.is_engaged() == false)
	{
		PyGILState_STATE state1 = PyGILState_Ensure();
		PySys_WriteStdout("Already stopped.\n");
		PyGILState_Release(state1);
	}
	else
	{
		cursor_params.set_engage(false);
	}
	PyGILState_STATE state = PyGILState_Ensure();
	Py_INCREF(Py_None);
	PyGILState_Release(state);
	return Py_None;
}
//function to return the cursor value
static PyObject* get_cursor_val(PyObject* self, PyObject* args)
{
	if (cursor_params.is_engaged() == true)
	{
		return Py_BuildValue("f", cursor_params.get_cursor_val());
	}
	else
	{
		return Py_BuildValue("f", 0.0);
	}
}

//function to return the cursor value
static PyObject* get_e_vals(PyObject* self, PyObject* args)
{
	PyObject* e1_names;
	PyObject* e2_names;
	int num_e1;
	int num_e2;
	int e1_counts = 0;
	int e2_counts = 0;
	int interval;
	//parse arguments from python
	 if (!PyArg_ParseTuple(args, "OOiii", &e1_names, &e2_names, 
	 	&num_e1, &num_e2, &interval))
		return NULL;
	//convert the python strings to C string arrays
	std::string* e1_names_c = new std::string[num_e1];
	std::string* e2_names_c = new std::string[num_e2];
	pystr_tuple_to_c_array(e1_names, e1_names_c, num_e1);
	pystr_tuple_to_c_array(e2_names, e2_names_c, num_e2);
	//get the cursor value
	get_raw_ensembles(e1_names_c, e2_names_c, num_e1, num_e2, &e1_counts, &e2_counts, interval);
	delete[] e1_names_c;
	delete[] e2_names_c;
	return Py_BuildValue("ii", e1_counts, e2_counts);
}

//function to start audio feedback playback	
static PyObject* start_feedback(PyObject* self, PyObject* args)
{
	float midpoint;
	int interval;
	//parse arguments from python
	 if (!PyArg_ParseTuple(args, "fi", &midpoint, &interval))
		return NULL;
	//initialize parameter values
	feedback_params.set_midpoint(midpoint);
	feedback_params.set_current_freq(midpoint);
	feedback_params.set_new_freq(midpoint);
	feedback_params.set_interval(interval);
	feedback_params.set_trigger(true);
	//start the feedback thread
	init_feedback(&feedback_params);
	PyGILState_STATE state = PyGILState_Ensure();
	Py_INCREF(Py_None);
	PyGILState_Release(state);
	return Py_None;
}

//function to change the frequency of the audio feedback
static PyObject* set_feedback(PyObject* self, PyObject* args)
{
	float val;
	//parse arguments from python
	 if (!PyArg_ParseTuple(args, "f", &val))
		return NULL;
	feedback_params.set_new_freq(val);
	PyGILState_STATE state = PyGILState_Ensure();
	Py_INCREF(Py_None);
	PyGILState_Release(state);
	return Py_None;
}

//function to stop audio playback (actually sets freq to inaudible; doesn't actually stop)
static PyObject* stop_feedback(PyObject* self, PyObject* args)
{
	feedback_params.set_current_freq(0);
	feedback_params.set_new_freq(0);
	//return nothing
	PyGILState_STATE state = PyGILState_Ensure();
	Py_INCREF(Py_None);
	PyGILState_Release(state);
	return Py_None;
}

//resume audio playback to a given freq
static PyObject* resume_feedback(PyObject* self, PyObject* args)
{
	float val;
	//parse arguments from python
	 if (!PyArg_ParseTuple(args, "f", &val))
		return NULL;
	feedback_params.set_new_freq(val);
	feedback_params.set_current_freq(val);
	PyGILState_STATE state = PyGILState_Ensure();
	Py_INCREF(Py_None);
	PyGILState_Release(state);
	return Py_None;
}

//play a noise burst
static PyObject* play_noise(PyObject* self, PyObject* args)
{
	noise_burst();
	PyGILState_STATE state = PyGILState_Ensure();
	Py_INCREF(Py_None);
	PyGILState_Release(state);
	return Py_None;
}

//send a TTL pulse to the behavior box
static PyObject* trig_nidaq(PyObject* self, PyObject* args)
{
	int devNum;
	int portNum;
	int lineNum;
	//parse arguments from python
	 if (!PyArg_ParseTuple(args, "iii", &devNum, &portNum, &lineNum))
		return NULL;
	//pass args to the function
	trigger_abet(devNum, portNum, lineNum);
	PyGILState_STATE state = PyGILState_Ensure();
	Py_INCREF(Py_None);
	PyGILState_Release(state);
	return Py_None;
}

//Send a pulse of a specific duration to the NI device
static PyObject* trig_nidaq_ex(PyObject* self, PyObject* args)
{
	int devNum;
	int portNum;
	int lineNum;
	int duration;
	//parse arguments from python
	 if (!PyArg_ParseTuple(args, "iiii", &devNum, &portNum, &lineNum, &duration))
		return NULL;
	//pass args to the function
	trigger_abet_ex(devNum, portNum, lineNum, duration);
	PyGILState_STATE state = PyGILState_Ensure();
	Py_INCREF(Py_None);
	PyGILState_Release(state);
	return Py_None;
}

//read the status of a NIDAQ DIO port
static PyObject* read_nidaq(PyObject* self, PyObject* args)
{
	int devNum;
	int portNum;
	int result;
	//parse arguments from python
	 if (!PyArg_ParseTuple(args, "ii", &devNum, &portNum))
		return NULL;
	//pass args to the function
	result = read_abet(devNum, portNum);
	return Py_BuildValue("i", result);
}

//Utils:
static PyMethodDef BMIRNmethods[] = {
	{"connect_client", connect_client, METH_VARARGS,
		"Opens a MAP server connection"},
	{"disconnect_client", disconnect_client, METH_VARARGS,
		"Closes a MAP server connection"},
	{"set_feedback", set_feedback, METH_VARARGS,
		"Change the feedback frequency value"},
	{"play_noise", play_noise, METH_VARARGS,
		"Play a white noise burst"},
	{"start_feedback", start_feedback, METH_VARARGS,
		"Start the audio feedback"},
	{"stop_feedback", stop_feedback, METH_VARARGS,
		"Shut down the audio playback"},
	{"resume_feedback", resume_feedback, METH_VARARGS,
		"Resumes the audio playback"},
	{"get_sorted_units", get_sorted_units, METH_VARARGS,
		"Returns a list of sorted units"},
	{"set_cursor_params", set_cursor_params, METH_VARARGS,
		"Set the parameters for calculating cursor values"},
	{"start_cursor", start_cursor, METH_VARARGS,
		"Initialize the thread to begin calculating cursor values"},
	{"stop_cursor", stop_cursor, METH_VARARGS,
		"Kill an active cursor thread"},
	{"get_cursor_val", get_cursor_val, METH_VARARGS,
		"Returns the current cursor value"},
	{"get_e_vals", get_e_vals, METH_VARARGS,
		"Returns the e1 and e2 ensemble counts for a given interval"},
	{"send_event", send_event, METH_VARARGS,
		"Sends a user event on a given channel"},
	{"trig_nidaq", trig_nidaq, METH_VARARGS,
	 	"Briefly pulses the DI/O on the nidaq"},
	{"trig_nidaq_ex", trig_nidaq_ex, METH_VARARGS,
		"Sends a pulse to the nidaq with a specified duration"},
	{"read_nidaq", read_nidaq, METH_VARARGS,
	 	"Reads a DIO sample from a nidaq port"},
	{NULL, NULL, 0, NULL} //sentinal
};

PyMODINIT_FUNC initBMI_RN(void)
{
	(void) Py_InitModule("BMI_RN", BMIRNmethods);
}