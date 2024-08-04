#!/usr/bin/env python3

######################
# IMPORTS
######################

import os
import yaml
import pandas as pd


#####################
# SETUP
#####################

def parameter_consistency_check(configurations):
    parameter = configurations["parameter"]
    threshold = configurations["threshold"]
    if configurations["hourly"]:
        if not isinstance(threshold, list) or len(threshold) !=2:
            print("error, 'hourly' set to True, 'threshold' should be a list of two values")
            return False

        if threshold[0] > 24:
            print("error, a day contains 24 hours only")
            return False
        if threshold[1] > 60:
            print("error, an hour contains 60 minutes only")
            return False
        if (threshold[0] < 0) or (threshold[1] < 0):
            print("error, time parameter set to negative")
            return False
        if (threshold[0] == 0) or (threshold[1] == 0):
            print("warning, thresholds set to 0")
    else:
        if not isinstance(threshold, int):
            print("error, 'hourly' set to False, 'threshold' should be an integer")
            return False

        if (threshold < 0):
            print("error, time parameter set to negative")
            return False
        if (threshold == 0):
            print("warning, threshold sets to 0")

    
    if parameter == "HR" and threshold > 1440:
        print("error, a day contains 1440 minutes only")
        return False

    # TODO
    
    return True


def get_files(data_path,configurations):
    # For Fitabase only
    HR_suffix = "fitbitWearTimeViaHR"
    Cal_suffix = "minuteCaloriesNarrow"
    Step_suffix = "minuteStepsNarrow"
    Step_d_suffix = "dailySteps"    
    Align_suffix = "dailyCalories"
    Synch_suffix = "syncEvents"    
    
    # getting paths of interest
    HR_paths = []
    Cal_paths = []
    Step_paths = []
    Step_d_paths = []
    Align_paths = []
    Synch_paths = []
    for file in sorted(os.listdir(path)):
        if ".csv" in file:
            if HR_suffix in file:
                HR_paths.append(os.path.join(path,file))
            if Cal_suffix in file:
                Cal_paths.append(os.path.join(path,file))       
            if Step_suffix in file:
                Step_paths.append(os.path.join(path,file))
            if Step_d_suffix in file:
                Step_d_paths.append(os.path.join(path,file))         
            if Align_suffix in file:
                Align_paths.append(os.path.join(path,file))
            if Synch_suffix in file:
                Synch_paths.append(os.path.join(path,file))    
    #TODO NAT

####################
# MAIN CHECK
####################
def ActiWearCheck(data_path,configurations):
    """
    data_path : None or string
    if None, take the files in the current directory.
    if string, take the files in the indicated path.

    configuration: a dict containing the following entries:
    parameter: 'HR', 'calories', 'steps', 'all'
    if 'HR', take the daily data from fitabase (suffixe=fitbitWearTimeViaHR) and look at the number of minute with HR data 
    if 'steps', take the daily data from fitabase (suffixe=minuteStepsNarrow) and sum the steps over the day.
    if 'calories', take the minute PAEE data from fitabase (suffixe=minuteCaloriesNarrow) and look at the number of active minutes, i.e., over RMR, per day
 
    threshold: int.
    number of required minute per day to count the day as worn. Between 0 and 1440. 
    for hourly == True
    threshold[0], number of hours per day to be considered. Between 0 and 24.
    threshold[1], number of minutes per hour to be considered. Between 0 and 60. 
 
    hourly: True, False (default).
    for parameter = 'calories', parameter = 'steps' , parameter = 'all'
    if True, take the minute PAEE data from fitabase (suffixe=minuteCaloriesNarrow) and look at the number of active minutes, i.e., over RMR, for a given number of hours per day.

    waking: True, False (default).
    if True, only considered hours between 5:00-22:59.
    
    forced_steps_minutes: True, False (default)
    if True, resample the minute files to compute daily steps. Prone to errors when hourly=False.
    
    alignement_check: True, False (default) 
    test the difference between data from daily files and daily summary resampled from from minute files.
    Currently only supported for parameter == 'calories' or 'all'.
    
    alignement_arg: float, between 0.01-1 (default=0.90), 
    minimum threshold above wich data are considered aligned.
    the default 0.90, considered acceptable a 10% difference (or less) between data from daily files and daily summary resampled from from minute files.

    synch_check: True, False (default),
    test whether interval between synch was bigger than minute data memory capacity.
    
    synch_arg: a list of lists as follows,
    [['device name' (string), number of day before data lost (int)]].
    set to the default values 5.
    
    """

    if data_path is None:
        data_path = os.getcwd()

    if not check_configuration_integrity(configurations):
        return
        
    print(configurations)

def read_configurations(config_path):
    with open(config_path, 'r') as yml:
        config = yaml.safe_load(yml)
    return config

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dataFilepath', type=str, default=None, help = "Path to data files")
    parser.add_argument('-c', '--configFilename', type=str, default='conf/default_conf.yaml', help = "Path to configuration file")
    args = parser.parse_args()

    configurations = read_configurations(args.configFilename)
    
    ActiWearCheck(args.dataFilepath,configurations)
