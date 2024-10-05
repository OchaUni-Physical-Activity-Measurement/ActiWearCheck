#!/usr/bin/env python3

######################
# IMPORTS
######################

import os
import yaml
import pandas as pd
import time

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

    method = configurations["method"]
    # Just in case configuration was built/loaded differently
    if "all" in method:
        configurations["method"] = configurations["all_methods"]
        method = configurations["all_methods"]
    if not isinstance(method, list):
        configurations["method"] = [configurations["method"]]
        method = [method]
    for key in method: # check settings are valid
        th = configurations[key] # get the relevant settings
        if key == "calories_hourly":
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
                print("error, time method set to negative")
                return False
            if (th[0] == 0) or (th[1] == 0):
                print("warning, thresholds set to 0")
        else:
            if not isinstance(th, int):
                print(f"error, threshold for {key} should be an integer")
                return False

            if (th < 0):
                print("error, time method set to negative")
                return False
            if (th == 0):
                print("warning, threshold sets to 0")


    if "hr_continue" in method:
        if configurations["hr_continue"] > 1440:
            print("error, a day contains 1440 minutes only")
            return False
        if configurations["waking"]:
            print("error, option 'waking' is not compatible with HR")
            return False
        if len(paths["hr"]) == 0:
            print("HR data files not found")
            return False
    if "calories_continue" in method or "calories_hourly" in method:
        if len(paths["calories_minutes"]) == 0:
            print("EE data files not found")
            return False
    if configurations["steps"]:
        if len(paths["steps_day"]) == 0:
            print("Step data files not found")
            # TODO: add the fallback on minute files (with a warning)
            return False
     
    # checking configuration for "minute_day and minute_day_param"
    if not configurations["minute_day"]:
        print("Not checking data alignment")
    else:
        alignment_arg = configurations["minute_day_param"]
        if alignment_arg > 1:
            print("error, 'minute_day_param' should be a float between 0 and 1")
            return False
        if alignment_arg < 0:
            print("error, 'minute_day_param' should be a float between 0 and 1")
            return False
        if "calories_continue" not in method and "calories_hourly" not in method:
            print("WARNING: data alignment check currently only supported for calories data, calory and step files will be used.")
            
        if len(paths["calories_day"]) != len(paths["calories_minutes"]):
            print("error the number of dailyCalories and minuteCalories files are different")
            return False
        if len(paths["steps_day"]) != len(paths["steps_minutes"]):
            print("error the number of dailySteps and minuteSteps files are different")
            return False
        if len(paths["steps_day"]) != len(paths["calories_day"]):
            print("error the number of steps and calories files are different")
            return False
    
    return True




def get_files(data_path,configurations,debug=False):
    # For Fitabase only
    suffixes = {}
    paths = {}
    suf = configurations["fitabase_suffixes"]
    for key in suf:
        suffixes[suf[key]] = key   
        # getting paths of interest
        paths[key] = []
    
    for file in sorted(os.listdir(data_path)):
        if ".csv" in file:
            for key in suffixes:
                if key in file: # TODO Check with Julien: actually should be at the end of the file?
                    paths[suffixes[key]].append(os.path.join(data_path,file))
            
    #TODO CHECK
    # if method == "steps":
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
    #         print("problems related to step settings, please check alignement between 'method' and 'forced_steps_minutes' ")

    if debug:
        for key in paths:
            print(f"{key} paths: {paths[key]}")
    
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
    method: 'HR', 'calories', 'steps', 'all'
    if 'HR', take the daily data from fitabase (suffixe=fitbitWearTimeViaHR) and look at the number of minute with HR data 
    if 'steps', take the daily data from fitabase (suffixe=minuteStepsNarrow) and sum the steps over the day.
    if 'calories', take the minute PAEE data from fitabase (suffixe=minuteCaloriesNarrow) and look at the number of active minutes, i.e., over RMR, per day
 
    threshold: int.
    number of required minute per day to count the day as worn. Between 0 and 1440. 
    for hourly == True
    threshold[0], number of hours per day to be considered. Between 0 and 24.
    threshold[1], number of minutes per hour to be considered. Between 0 and 60. 
 
    hourly: True, False (default).
    for method = 'calories', method = 'steps' , method = 'all'
    if True, take the minute PAEE data from fitabase (suffixe=minuteCaloriesNarrow) and look at the number of active minutes, i.e., over RMR, for a given number of hours per day.

    waking: True, False (default).
    if True, only considered hours between 5:00-22:59.
    
    forced_steps_minutes: True, False (default)
    if True, resample the minute files to compute daily steps. Prone to errors when hourly=False.
    
    alignement_check: True, False (default) 
    test the difference between data from daily files and daily summary resampled from from minute files.
    Currently only supported for method == 'calories' or 'all'.
    
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
        

    files = get_files(data_path,configurations,debug=debug)

    if debug:
        files

    data_out = {} # separate by ID, just in case some subjects are available for some methods but not the other and vice-versa 

    if not check_configuration_integrity(configurations, files):
        return

    if debug:
        print(configurations)

    if "hr_continue" in configurations["method"]:
           
        for file in files["hr"]:
            if debug:
                print("Analyzing", file)
            id_ = os.path.basename(file)
            id_=id_.split("_")[0]
            series= configurations["fitabase_series"]["hr"]
            data=pd.read_csv(file).set_index("Day")
            data.index = pd.to_datetime(data.index)
            data["ID"] = id_
            data=data[["ID",series]]
            data['HR-worn'] = data[series] >= configurations["hr_continue"]
            data_out[id_] = [data]
            if debug:
                print("one file finished")


    
    # QUESTION: alignment should probably be done separately?
    if "calories_continue" in configurations["method"] or "calories_hourly" in configurations["method"] or configurations["minute_day"]:
        align_count = 0
        for file in files["calories_minutes"]:
            if debug:
                print(file)
            id_ = os.path.basename(file)
            id_=id_.split("_")[0]
            series=configurations["fitabase_series"]["calories"]
            data_min=pd.read_csv(file).set_index("ActivityMinute")
            data_min.index = pd.to_datetime(data_min.index,format="%m/%d/%Y %I:%M:%S %p")
            data_min['RMR'] = data_min.resample('D')[series].transform('min')
            data=data_min.resample("D").sum()
            if configurations["minute_day"]:              
                data_align_min = data   
            data["ID"] = id_   
            data=data[["ID",series]]
          
            if "calories_hourly" in configurations["method"]:
            # Taken from Method 2 (Matt, see below)
                data_min['minAboveRMR'] = (data_min[series] > data_min['RMR']).astype(int)
                data_min['hourAboveRMR'] = data_min['minAboveRMR'].resample('h').sum() >= configurations["calories_hourly"][1]
                if configurations["waking"]:
                    data['hourAboveRMR'] = data_min.between_time('5:00','22:59')['hourAboveRMR'].resample('D').sum().to_frame()    
                else:
                    data['hourAboveRMR'] = data_min['hourAboveRMR'].resample('D').sum().to_frame()    
                data['Cal-worn (per hour)'] = data['hourAboveRMR'] >= configurations["calories_hourly"][0]  
            
            if "calories_continue" in configurations["method"]:
                if configurations["waking"]:    
                    data['nMinAboveRMR'] = data_min.between_time('5:00','22:59')[data_min[series] > data_min['RMR']].resample('D').count()[series]
                else:
                    data['nMinAboveRMR'] = data_min[data_min[series] > data_min['RMR']].resample('D').count()[series]
                data['Cal-worn'] = data['nMinAboveRMR'] >= configurations["calories_continue"]
            
            if configurations["minute_day"]:
                data_align_day = pd.read_csv(files["calories_day"][align_count]).set_index("ActivityDay")
                data_align_day.index = pd.to_datetime(data_align_day.index)

                data_step_min = pd.read_csv(files["steps_minutes"][align_count]).set_index("ActivityMinute")
                data_step_min.index = pd.to_datetime(data_step_min.index,format="%m/%d/%Y %I:%M:%S %p")
                data_step_min=data_step_min.resample("D").sum()

                data_step_day = pd.read_csv(files["steps_day"][align_count]).set_index("ActivityDay")
                data_step_day.index = pd.to_datetime(data_step_day.index)

                
                
                data_align = pd.merge(data_align_min, data_align_day, left_index=True, right_index=True)
                data_align = data_align.rename(columns={series+"_x": series+" resampled (from min files)", series+"_y": series+" from day files"})
                data_step = pd.merge(data_step_min, data_step_day, left_index=True, right_index=True)
                if debug:
                    print("alignment data")
                    print(pd.concat([data_step,data_align],axis=1))
                # Perform the comparison after alignment
                data_align['diff'] = (data_align[series+" resampled (from min files)"].astype('float') / data_align[series+" from day files"].astype('float')) >= configurations["minute_day_param"]
                data_step['diff'] = (data_step[configurations["fitabase_series"]["steps"]].astype("float") / data_step[configurations["fitabase_series"]["steps_day"]].astype("float")) >= configurations["minute_day_param"]
                data["day/min calory alignment"] = data_align['diff']
                data["day/min step alignment"] = data_step["diff"]
                # print(data)



                align_count+=1
            if "calories_continue" not in configurations["method"] and "calories_hourly" not in configurations["method"]:
                data.drop(columns=[series], inplace=True) # We are only here for alignment
                
            if id_ in data_out:
                data.drop(columns=["ID"], inplace=True) # We already know it
                data_out[id_].append(data)
            else:
                data_out[id_] = [data]  
            if debug:                                          
                print("one file finished")

        if configurations["steps"]:
            for file in files["steps_day"]:
                if debug:
                    print(file)
                data = pd.read_csv(file).set_index("ActivityDay")
                data.index = pd.to_datetime(data.index)

                id_ = os.path.basename(file)
                id_=id_.split("_")[0]
                series=configurations["fitabase_series"]["steps_day"]
                data["ID"] = id_   
                data["Stepped"] = data[series] >= configurations["steps_param"]
                if debug:
                    print(data)
                if id_ in data_out:
                    data.drop(columns=["ID"], inplace=True) # We already know it
                    data_out[id_].append(data)
                else:
                    data_out[id_] = [data]  
                if debug:                                          
                    print("one file finished")


    # Finished reading the files
    if debug:
        for indiv in data_out:
            print(data_out[indiv])

    # check that all data are consistent
    if len(set([len(data_out[_id]) for _id in data_out])) != 1:
        print("Warning: inconsistent number of data types across individuals")
        print([(_id, len(data_out[_id])) for _id in data_out])

    id_list = sorted(data_out.keys())
    frames = []
    for _id in id_list:
        f = pd.concat(data_out[_id], axis=1)
        if configurations["drop_na"]:
            f.dropna(inplace=True)
        frames.append(f)

        if configurations["subjectwise_output"]:
            f.to_csv(configurations["output_basename"]+str(_id)+".csv")
    return pd.concat(frames)




def read_configurations(config_path):
    with open(config_path, 'r') as yml:
        config = yaml.safe_load(yml)
    if config["method"] == "all" or "all" in config["method"]:
        config["method"] = config["all_methods"]
    return config

if __name__ == "__main__":
    start_time = time.time()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dataFilepath', type=str, default=None, help = "Path to data files")
    parser.add_argument('-c', '--configFilename', type=str, default='conf/default_conf.yaml', help = "Path to configuration file")
    args = parser.parse_args()

    configurations = read_configurations(args.configFilename)
    
    result = ActiWearCheck(args.dataFilepath,configurations, debug=configurations["debug"])

    if not configurations["subjectwise_output"]:
        result.to_csv(configurations["output_basename"]+".csv")

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"ActiveWearCheck finished in {elapsed_time:.2f} seconds.")