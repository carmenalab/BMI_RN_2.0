from setuptools import setup, Extension
import os
from sys import platform as _platform
import platform as pl

if _platform == 'win32' and pl.release() == 'XP':
	library_list = ['dsound', 'winmm', 'Wsock32', 'kernel32',
	'user32','gdi32','winspool','comdlg32','advapi32','shell32',
	'ole32','oleaut32','uuid','odbc32','odbccp32', 'PlexClient', 'nidaqmxbase', 'python27']
	libraryDirs = ['lib']
	pre_defs = [('__LITTLE_ENDIAN__', None), ('__WINDOWS_DS__', None), ('__WINDOWS_MM__', None)]
	MAIN_SOURCES = ['src/BMI_RN.cpp','src/plex_utils.cpp', 'src/cursor.cpp', 'src/reward.cpp',
	'src/RtAudio.cpp', 'src/Stk.cpp', 'src/RtWvOut.cpp', 'src/Mutex.cpp', 'src/Noise.cpp', 
	'src/SineWave.cpp','src/feedback.cpp']
	INCLUDES = ['include']

elif _platform == 'win32' and pl.release() == '7':
	library_list = ['ksuser', 'winmm', 'Wsock32', 'kernel32',
	'user32','gdi32','winspool','comdlg32','advapi32','shell32',
	'ole32','oleaut32','uuid','odbc32','odbccp32', 'PlexClient', 'nidaqmxbase', 'python27']
	libraryDirs = ['lib']
	pre_defs = [('__LITTLE_ENDIAN__', None), ('__WINDOWS_WASAPI__', None), ('__WINDOWS_MM__', None)]
	MAIN_SOURCES = ['src/BMI_RN.cpp','src/plex_utils.cpp', 'src/cursor.cpp', 'src/reward.cpp',
	'src/RtAudio.cpp', 'src/Stk.cpp', 'src/RtWvOut.cpp', 'src/Mutex.cpp', 'src/Noise.cpp', 
	'src/SineWave.cpp','src/feedback.cpp']
	INCLUDES = ['include']

elif _platform == 'win32' and pl.release() == '10':
	library_list = ['ksuser', 'winmm', 'Wsock32', 'kernel32',
	'user32','gdi32','winspool','comdlg32','advapi32','shell32',
	'ole32','oleaut32','uuid','odbc32','odbccp32', 'PlexClient', 'nidaqmxbase', 'python27']
	libraryDirs = ['lib']
	pre_defs = [('__LITTLE_ENDIAN__', None), ('__WINDOWS_WASAPI__', None), ('__WINDOWS_MM__', None)]
	MAIN_SOURCES = ['src/BMI_RN.cpp','src/plex_utils.cpp', 'src/cursor.cpp', 'src/reward.cpp',
	'src/RtAudio.cpp', 'src/Stk.cpp', 'src/RtWvOut.cpp', 'src/Mutex.cpp', 'src/Noise.cpp', 
	'src/SineWave.cpp','src/feedback.cpp']
	INCLUDES = ['include']


module1 = Extension('BMI_RN', sources = MAIN_SOURCES, 
	language = 'c++', include_dirs = INCLUDES, 
	library_dirs = libraryDirs, libraries = library_list,
	define_macros = pre_defs)

setup(name = "BMI_RN",
	  package_data = {'':['*.dll']},
      version = "2.0",
      author = "Ryan Neely",
      author_email = "ryan_neely@berkeley.edu",
      ext_modules = [module1])
