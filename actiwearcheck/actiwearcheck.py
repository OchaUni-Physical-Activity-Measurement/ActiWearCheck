#!/usr/bin/env python3

######################
# IMPORTS
######################

import os
import yaml
import pandas as pd

######################
# GLOBAL VARIABLE
######################

_all_parameters = ["HR", "calories", "steps"]
######################
# SETUP
######################

def check_configuration_integrity(configurations, paths):
    """
    Convenience function to check that settings are meaningful and found files are consistent

    configurations: dictionary of configurations

    paths: dictionary of path lists. Each list corresponds to a type of file, described by one of the keys
    such as "HR", "Cal", "Step", "Step_d", "Align", and "Synch"
    """
    #TODO: auto generate the key list?

    parameter = configurations["parameter"]
    # Just in case configuration was built/loaded differently
    if "all" in parameter:
        configurations["parameter"] = _all_parameters
        parameter = _all_parameters
    if not isinstance(parameter, list):
        configurations["parameter"] = [configurations["parameter"]]
        parameter = [parameter]
    threshold = configurations["threshold"]
    for key in threshold:
        th = threshold[key]
        if key == "hourly":
            if not isinstance(th, list) or len(th) !=2:
                print("error, 'hourly' set to True, 'threshold' should be a list of two values")
                return False

            if th[0] > 24:
                print("error, a day contains 24 hours only")
                return False
            if th[1] > 60:
                print("error, an hour contains 60 minutes only")
                return False
            if (th[0] < 0) or (th[1] < 0):
                print("error, time parameter set to negative")
                return False
            if (th[0] == 0) or (th[1] == 0):
                print("warning, thresholds set to 0")
        else:
            if not isinstance(th, int):
                print(f"error, threshold for {key} should be an integer")
                return False

            if (th < 0):
                print("error, time parameter set to negative")
                return False
            if (th == 0):
                print("warning, threshold sets to 0")

    
    if "HR" in parameter and threshold["base"] > 1440:
        print("error, a day contains 1440 minutes only")
        return False


    if "HR" in parameter:
        if len(paths["HR"]) == 0:
            print("HR data files not found")
            return False
    if "calories" in parameter:
        if len(paths["Cal"]) == 0:
            print("EE data files not found")
            return
    if "steps" in parameter:
        if len(paths["Step"]) == 0:
            print("Step data files not found")
            return
     
    # checking configuration for "alignment_check and alignment_arg"
    if configurations["alignment_check"] == False:
        print("Not checking data alignment")
    else:
        alignment_arg = configurations["alignment_arg"]
        if alignment_arg > 1:
            print("error, 'alignment_arg' should be a float between 0 and 1")
            return False
        if alignment_arg < 0:
            print("error, 'alignment_arg' should be a float between 0 and 1")
            return False
        if "calories" not in parameter:
            print("warning. data alignment check currently only supported for calories data, 'alignement_arg' set to 1.0")
            configurations["alignment_arg"] = 1.0
            
        if len(paths["Align"]) != len(paths["Cal"]):
            print("error the number of dailyCalories and minuteCalories files is different")
            return False
    
    return True




def get_files(data_path,debug=False):
    # For Fitabase only
    suffixes = {"fitbitWearTimeViaHR": "HR", "minuteCaloriesNarrow": "Cal", 
        "minuteStepsNarrow": "Step", "dailySteps": "Step_d", "dailyCalories": "Align", "syncEvents": "Synch"}    
    # getting paths of interest
    paths = {"HR": [], "Cal": [], "Step": [], "Step_d": [], "Align": [], "Synch": []}
    
    for file in sorted(os.listdir(data_path)):
        if ".csv" in file:
            for key in suffixes:
                if key in file: # TODO Check with Julien: actually should be at the end of the file?
                    paths[suffixes[key]].append(os.path.join(data_path,file))
            
    #TODO CHECK
    # if parameter == "steps":
    #     if hourly == True and forced_steps_minutes == False :
    #         Step_paths = Step_paths
    #     elif hourly == False and forced_steps_minutes == False :
    #         Step_paths = Step_d_paths 
    #         Steps_suffix = Step_d_suffix
    #         if waking:
    #             waking = False
    #             print("waking was desactivated, analysis not possible with daily data summaries")
    #     elif forced_steps_minutes:
    #         hourly = False
    #         Step_paths = Step_paths
    #     else:
    #         print("problems related to step settings, please check alignement between 'parameter' and 'forced_steps_minutes' ")

    if debug:
        print("HR paths : ", paths["HR"])
        print("Cal paths : ", paths["Cal"])
        print("Step paths : ", paths["Step"])
    
    return paths


####################
# MAIN CHECK
####################
def ActiWearCheck(data_path,configurations,debug=False):
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
        

    files = get_files(data_path,debug=debug)

    if debug:
        files

    # data_out = {} #???

    if not check_configuration_integrity(configurations, files):
        return

    if debug:
        print(configurations)

    if "HR" in configurations["parameter"]:
        all_HR_data = {} # TODO: strange; should be a list, and then concatenate at the end   
        for file in files["HR"]:
            if debug:
                print("Analyzing", file)
            id_ = os.path.basename(file)[1:] # TODO: Ask julien about the first character (0 or 1)
            id_=id_.split("_")[0]
            series="TotalMinutesWearTime"
            data=pd.read_csv(file).set_index("Day")
            data.index = pd.to_datetime(data.index)
            data["ID"] = id_
            data=data[["ID",series]]
            if configurations["waking"]:    
                data=data.between_time('5:00','22:59')
            data['HR-worn'] = data[series] >= configurations["threshold"]["base"]
            #data["HR-worn"] = data[series].apply(worn_continue)
            all_HR_data[id_] = data
            if debug:
                print("one file finished")
        if debug:
            for indiv in all_HR_data:
                print(all_HR_data[indiv])



def read_configurations(config_path):
    with open(config_path, 'r') as yml:
        config = yaml.safe_load(yml)
    if config["parameter"] == "all" or "all" in config["parameter"]:
        config["parameter"] = _all_parameters
    return config

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dataFilepath', type=str, default=None, help = "Path to data files")
    parser.add_argument('-c', '--configFilename', type=str, default='conf/default_conf.yaml', help = "Path to configuration file")
    args = parser.parse_args()

    configurations = read_configurations(args.configFilename)
    
    ActiWearCheck(args.dataFilepath,configurations, debug=True)
