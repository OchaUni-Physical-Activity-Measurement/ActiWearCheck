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
    print("Checking correct function call and configuration file...")
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
            print("error, HR data files not found")
            return False
    if "calories_continue" in method or "calories_hourly" in method:
        if len(paths["calories_minutes"]) == 0:
            print("error, EE data files not found")
            return False
        if configurations["calories_continue"] > 1440:
            print("error, a day contains 1440 minutes only")
            return False
    if configurations["steps"]:
        if len(paths["steps_day"]) == 0:
            print("error, step data files not found")
            # TODO: add the fallback on minute files (with a warning)
            return False
     
    # checking configuration for "minute_day and minute_day_param"
    if not configurations["minute_day"]:
        print("warining, not checking data alignment")
    else:
        alignment_arg = configurations["minute_day_param"]
        if alignment_arg > 1:
            print("error, 'minute_day_param' should be a float between 0 and 1")
            return False
        if alignment_arg < 0:
            print("error, 'minute_day_param' should be a float between 0 and 1")
            return False
        if "calories_continue" not in method and "calories_hourly" not in method:
            print("warning, data alignment check currently only supported for calories data, calory and step files will be used.")
            
        if len(paths["calories_day"]) != len(paths["calories_minutes"]):
            print("error, the number of dailyCalories and minuteCalories files are different")
            return False
        if len(paths["steps_day"]) != len(paths["steps_minutes"]):
            print("error, the number of dailySteps and minuteSteps files are different")
            return False
        if len(paths["steps_day"]) != len(paths["calories_day"]):
            print("error, the number of steps and calories files are different")
            return False
    
    return True




def get_files(data_path,configurations,default_format="fitabase", debug=False):
    """
    Imports file, as extracted from the specified API (default: Fitabase).
    Arguments:
    - data_path: where data are located
    - condigurations: the configuration.yaml file to apply

    Returns:
    - paths = dictionary of data
    """
    print("Importing data...")
    if "data_format" in configurations:
        data_format = configurations["data_format"]
    else:
        data_format = default_format

    suffixes = {}
    paths = {}
    suf = configurations[f"{data_format}_suffixes"]
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

def synch_check(files, configurations, default_max_days=5, default_format="fitabase", debug=False):
    all_Synch_data = {}
    if "data_format" in configurations:
        data_format = configurations["data_format"]
    else:
        data_format = default_format
    print("Starting synchronisation check...")
    for file in files["synch"]:
        if debug:
            print(file)
        id_ = os.path.basename(file)
        id_=id_.split("_")[0]
        series=configurations[f"{data_format}_series"]["synch"]
        synch_data = pd.read_csv(file).set_index("DateTime")
        synch_data.index = pd.to_datetime(synch_data.index,format="%m/%d/%Y %I:%M:%S %p")
        synch_data[series] = pd.to_datetime(synch_data[series],format="%m/%d/%Y %I:%M:%S %p")
        device_name = synch_data[configurations[f"{data_format}_series"]["device_name"]].to_numpy()[0].lower()
        # Sort by time
        synch_data = synch_data.sort_values(by=series)
        # Calculate differences between consecutive sync times
        synch_data['time_diff'] = synch_data[series].diff().dt.days
        synch_data['time_diff'] = synch_data['time_diff'].fillna(0) # Change Nan for 0 so that idxmax can be processed
        # Group data daywise and return the line where the time difference is maximum
        synch_data = synch_data.groupby(synch_data.index.date).apply(lambda x: x.loc[x['time_diff'].idxmax()])
        # Reset the index to be a datetime
        synch_data.index = pd.to_datetime(synch_data.index)                     
        # Check if the time difference exceeds max_days
        if device_name in configurations["devices"]:
            max_days = float(configurations["devices"][device_name]["memory"])
        else:
            max_days = default_max_days
            print(f"warning, unknown device {device_name}, defaulting to {max_days} days")
            print(configurations["devices"])
        # Compute the data_loss_risk in a vectorized manner
        synch_data['data_loss_risk'] = synch_data['time_diff'] > max_days
        #synch_data['data_loss_risk'] = synch_data['time_diff'] > 5 
        all_Synch_data[id_] = synch_data       
    
    return all_Synch_data

####################
# MAIN CHECK
####################
def ActiWearCheck(data_path,configurations, default_format="fitabase", debug=False):
    """
    data_path : None or string
    if None, take the files in the current directory.
    if string, take the files in the indicated path.

    configuration:
    a dict containing the following entries:
    
        method: 'hr_continue' (default), 'calories_continue', 'calories_hourly','all'
        evaluate valid wear days,
        if 'hr_continue', from the number of minutes with HR data found in daily data files. HR data files are used.
        if 'calories_continue', from the number of minutes with EE above REE. Minute data files are used.
        if 'calories_hourly', from the number of hours with a least a selected number of minutes with EE above REE minute. Minute data files are used.

        hr_continue: int between 0 and 1440. (default = 600)
        number of minutes to be used as evaluation criteria for the 'hr_continue' method.

        calories_continue: int between 0 and 1440. (default = 600)
        number of minutes to be used as evaluation criteria for the 'calories_continue' method.

        calories_hourly: [int between 1 and 24, int between 1 and 60] (default = [10, 1])
        number of hours and minute-per-hour to be used as evaluation criteria for the 'calories_hourly' method.

        steps: boolean (default = True)
        an option to evaluate valid wear based on the daily number of steps.

        steps_param: int equal or higher than 0 (default = 1)
        number of steps to be used as evaluation criteria when steps = True.

        minute_day: boolean (default = True)
        An option to evaluate valid wear based on the ratio of minute data (steps and calories) resampled to day and daily data obtained from daily summarize files.

        minute day_param: float between 0.0 and 1.0 (default = 0.9)
        ratio of difference between "per day" data, and "per minute" data resampled by day, to be used as evaluation criteria when  = True.

        synch_check: boolean (default = False)
        an option to evaluate the validity of data based on the interval between two synchronization dates.
        the interval criteria depends on the device specifications (currently supported for the following devices: alta, alta hr and inspire 2).

        waking: boolean (default = False)
        if True, conduct the valid wear evaluation between 5:00 and 22:59 only.
        cannot currenlty be used for method = 'hr_continue'

        fitabase_suffixes:
        string to be found in fitabase file names for hr, minute calories, daily calories, minutes steps, daily steps and synch data.

        fitabase_series:
        name of time series of interest for hr, calories, minute steps and daily steps data.

        drop_na: boolean (default = True)
        if True, remove days with no data.

        subjectwise_output: boolean (default = True)
        if True, results are saved in one file per subject.

        output_basename: string (default = 'actiwear')
        name of the output csv file.

        debug: boolean (default = False)  
        prints all steps and information to debug.

    """
    print("Starting ActiWearCheck...")

    if "data_format" in configurations:
        data_format = configurations["data_format"]
    else:
        data_format = default_format

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
            series= configurations[f"{data_format}_series"]["hr"]
            data=pd.read_csv(file).set_index("Day")
            data.index = pd.to_datetime(data.index)
            data["ID"] = id_
            data=data[["ID",series]]
            data['HR-worn'] = data[series] >= configurations["hr_continue"]
            if id_ in data_out:
                data.drop(columns=["ID"], inplace=True) # We already know it
                data_out[id_].append(data)
            else:
                data_out[id_] = [data]
            if debug:
                print("One file finished")


    
    # QUESTION: alignment should probably be done separately?
    if "calories_continue" in configurations["method"] or "calories_hourly" in configurations["method"] or configurations["minute_day"]:
        align_count = 0
        for file in files["calories_minutes"]:
            if debug:
                print(file)
            id_ = os.path.basename(file)
            id_=id_.split("_")[0]
            series=configurations[f"{data_format}_series"]["calories"]
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
                data['Cal-worn(per-hour)'] = data['hourAboveRMR'] >= configurations["calories_hourly"][0]  
            
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
                    print("Alignment data")
                    print(pd.concat([data_step,data_align],axis=1))
                # Perform the comparison after alignment
                data_align['diff'] = (data_align[series+" resampled (from min files)"].astype('float') / data_align[series+" from day files"].astype('float')) >= configurations["minute_day_param"]
                data_step['diff'] = (data_step[configurations[f"{data_format}_series"]["steps"]].astype("float") / data_step[configurations[f"{data_format}_series"]["steps_day"]].astype("float")) >= configurations["minute_day_param"]
                data["day/min_calory_alignment"] = data_align['diff']
                data["day/min_step_alignment"] = data_step["diff"]
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
                print("One file finished")

        if configurations["steps"]:
            for file in files["steps_day"]:
                if debug:
                    print(file)
                data = pd.read_csv(file).set_index("ActivityDay")
                data.index = pd.to_datetime(data.index)

                id_ = os.path.basename(file)
                id_=id_.split("_")[0]
                series=configurations[f"{data_format}_series"]["steps_day"]
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
                    print("One file finished")

    if configurations["synch_check"]:
        synchs = synch_check(files, configurations)
        for _id in synchs:
            if _id in data_out:
                data_out[_id].append(synchs[_id])
            else:
                data_out[_id] = [synchs[_id]]

    # get device name if available
    device_names = {}
    for file in files["synch"]:
        if debug:
            print("Reading device name from", file)
        id_ = os.path.basename(file)
        id_=id_.split("_")[0]
        device_name= configurations[f"{data_format}_series"]["device_name"]
        data=pd.read_csv(file)[device_name][0]
        device_names[id_] = data


    # Finished reading the files
    if debug:
        for indiv in data_out:
            print(data_out[indiv])

    # check that all data are consistent
    if len(set([len(data_out[_id]) for _id in data_out])) != 1:
        print("warning, inconsistent number of data types across individuals")
        print([(_id, len(data_out[_id])) for _id in data_out])

    print("Saving data...")
    id_list = sorted(data_out.keys())
    frames = []
    for _id in id_list:
        f = pd.concat(data_out[_id], axis=1)
        if _id in device_names:
            f[configurations[f"{data_format}_series"]["device_name"]] = device_names[_id]
        if configurations["drop_na"]:
            f.dropna(inplace=True)
        frames.append(f)

        if configurations["subjectwise_output"]:
            f.to_csv(configurations["output_basename"]+str(_id)+".csv")
    # print("...Done")
    return pd.concat(frames)

def read_configurations(config_path, default_format="fitabase"):
    """
    (...)
    """
    print("Reading configuration file...")
    with open(config_path, 'r') as yml:
        config = yaml.safe_load(yml)
    if "method" in config and (config["method"] == "all" or "all" in config["method"]):
        config["method"] = config["all_methods"]
    if not "data_format" in config:
        config["data_format"] = default_format
    return config

if __name__ == "__main__":
    start_time = time.time()

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dataFilepath', type=str, default=None, help = "Path to data files")
    parser.add_argument('-o', '--outputpath', type=str, default="./", help = "Output directory")
    parser.add_argument('-c', '--configFilename', type=str, default='conf/default_conf.yaml', help = "Path to configuration file")
    parser.add_argument('--devicesFilename', type=str, default='devices/20241015_devices.yaml', help = "Path to devices definitions")
    parser.add_argument('--dataFormat', type=str, default=None, help = "Selects the file format of the data. If set, will override the configuration settings. \
        If no format is selected at all, will default to fitabase.")
    args = parser.parse_args()

    configurations = read_configurations(args.configFilename)
    devices = read_configurations(args.devicesFilename)
    configurations["output_basename"] = os.path.join(args.outputpath, configurations["output_basename"])
    configurations["devices"] = devices
    if args.dataFormat is not None:
        configurations["data_format"] = args.dataFormat
    result = ActiWearCheck(args.dataFilepath,configurations, debug=configurations["debug"])

    if not configurations["subjectwise_output"]:
        result.to_csv(configurations["output_basename"]+".csv")

    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"ActiveWearCheck finished in {elapsed_time:.2f} seconds.")