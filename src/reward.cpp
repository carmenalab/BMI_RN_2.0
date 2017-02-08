///Functions to handle NIDAQ DIO, and reward-related activities

#include "reward.h"

//arg should be in format "Dev1/port0"
int writePort (char *chan, int val)
{
   // Task parameters
   int32       error = 0;
   TaskHandle  taskHandle = 0;
   char        errBuff[2048];


   // Write parameters
   uInt32      w_data [1];
   int32       written;


   // Create Digital Output (DO) Task and Channel
   DAQmxErrChk (DAQmxBaseCreateTask ("", &taskHandle));
   DAQmxErrChk (DAQmxBaseCreateDOChan(taskHandle,chan,"",DAQmx_Val_ChanForAllLines));

   // Start Task (configure port)
   DAQmxErrChk (DAQmxBaseStartTask (taskHandle));

   //  Write val to port(s)
   //  Only 1 sample per channel supported for static DIO
   //  Autostart ON

   w_data[0] = val;

   DAQmxErrChk (DAQmxBaseWriteDigitalU32(taskHandle,1,1,10.0,DAQmx_Val_GroupByChannel,w_data,&written,NULL));


Error:

   if (DAQmxFailed (error))
      DAQmxBaseGetExtendedErrorInfo (errBuff, 2048);

   if (taskHandle != 0)
   {
      DAQmxBaseStopTask (taskHandle);
      DAQmxBaseClearTask (taskHandle);
   }

   if (error)
      printf ("DAQmxBase Error %ld: %s\n", error, errBuff);

   return 0;
}

int readPort (char *chan)
{
   // Task parameters
   int32       error = 0;
   TaskHandle  taskHandle = 0;
   char        errBuff[2048];

   // Read parameters
   uInt32      r_data [1];
   int32       read;
   int         result;

   // Create Digital Input (DI) Task and Channel
   DAQmxErrChk (DAQmxBaseCreateTask ("", &taskHandle));
   DAQmxErrChk (DAQmxBaseCreateDIChan(taskHandle,chan,"",DAQmx_Val_ChanForAllLines));

   // Start Task (configure port)
   DAQmxErrChk (DAQmxBaseStartTask (taskHandle));

   // Read from port
   DAQmxErrChk (DAQmxBaseReadDigitalU32(taskHandle,1,10.0,DAQmx_Val_GroupByChannel,r_data,1,&read,NULL));



Error:

   if (DAQmxFailed (error))
      DAQmxBaseGetExtendedErrorInfo (errBuff, 2048);

   if (taskHandle != 0)
   {
      DAQmxBaseStopTask (taskHandle);
      DAQmxBaseClearTask (taskHandle);
   }

   if (error)
      printf ("DAQmxBase Error %ld: %s\n", error, errBuff);
   
   result = r_data[0];
   return result;
}


//Trigger the behavior box. Arguments are a device number and a device channel number.
extern "C" void trigger_abet(int device, int port, int line)
{
   //base string format
   char argString[] = "Devx/porty/linez";
   //value to write; will depend on line to write to
   int val = two_pow(line); 
   //convert input integers to strings
   char devNum[2];
   char portNum[2];
   char lineNum[2];
   _itoa(device, devNum, 10);
   _itoa(port, portNum, 10);
   _itoa(line, lineNum, 10);
   //place the device/port numbers into the base string
   argString[3] = devNum[0];
   argString[9] = portNum[0];
   argString[15] = lineNum[0];
   //send a reward signal to the NIDAQ
   //(ABET recognizes the trigger only when you set
   //a "1" followed shortly by a "0")
   writePort(argString,val);
   Sleep(10);
   writePort(argString,0);
}

//Trigger the behavior box; this time specifying a pulse duration (in ms). 
//Arguments are a device number and a device channel number.
extern "C" void trigger_abet_ex(int device, int port, int line, int duration)
{
   //base string format
   char argString[] = "Devx/porty/linez";
   //value to write; will depend on line to write to
   int val = two_pow(line); 
   //convert input integers to strings
   char devNum[2];
   char portNum[2];
   char lineNum[2];
   _itoa(device, devNum, 10);
   _itoa(port, portNum, 10);
   _itoa(line, lineNum, 10);
   //place the device/port numbers into the base string
   argString[3] = devNum[0];
   argString[9] = portNum[0];
   argString[15] = lineNum[0];
   //send a reward signal to the NIDAQ
   //(ABET recognizes the trigger only when you set
   //a "1" followed shortly by a "0")
   writePort(argString,val);
   Sleep(duration);
   writePort(argString,0);
}

//Get the value of the NIDAQ DIO device
extern "C" int read_abet(int device, int port)
{
   int result;
   //base string format
   char argString[] = "Devx/porty";
   //convert input integers to strings
   char devNum[2];
   char portNum[2];
   _itoa(device, devNum, 10);
   _itoa(port, portNum, 10);
   //place the device/port numbers into the base string
   argString[3] = devNum[0];
   argString[9] = portNum[0];
   //read from the NIDAQ device
   result = readPort(argString);
   return result;
}


///A stupid little function to do exponetiation because I'm
///too dumb to figure out another way
int two_pow(int line)
{
   int result = 1;
   if (line > 0)
   {
   result = 2;
      for (int i=0; i<line-1; i++)
      {
         result = result*2;
      } 
   }
   return result;
}