## ActiWearCheck

<strong>evaluate days of valid wear for Fitbit activity trackers</strong>.

This repository contains:
- a software (<a href="actiwearcheck/actiwearcheck.py"><strong>actiwearcheck.py</strong></a>) to process HR or accelerometer minute data obtained from Fitbit devices and evaluate days of valid wear.
- sample data for 6 subjects, as extracted from Fitabase.

### run actiwearcheck

```python3 actiwearcheck.py [-d path_to_data] [-o path_to_output] [-c path_to_config]```

- <strong>path_to_data</strong>: path to the fitbit data folder, e.g. <a href="https://github.com/OchaUni-Physical-Activity-Measurement/ActiWearCheck/tree/main/samples">.ActiWearCheck/samples/</a>. If not provided, defaults to the current directory.
- <strong>path_to_output</strong>: path where the results will be saved. If not provided, defaults to the current directory.
- <strong>path_to_config</strong>: path to the configuration file for the analysis, provided in the yaml format. If not provided, defaults to <a href="https://github.com/OchaUni-Physical-Activity-Measurement/ActiWearCheck/blob/main/actiwearcheck/conf/default_conf.yaml">conf/default_conf.yaml</a>. See that file for an exaustive list of options. <strong>The default configuration works with Fitabase export files</strong>.

### methods of evaluation

The current configuration file accepts 3 different methods for evaluation of valid wear. The criteria are as follows:
- <strong>"hr_continue"</strong>: a minimum number of minutes with heart rate data is required. The suggested default configuration is looking for days with at least 600 minutes of hear rate data.
- <strong>"calories_continue"</strong>: a minimum number of minutes with energy expenditure data above the resting metabolic rest is required. The suggested default configuration is looking for days with at least 600 minutes above the resting metabolic rate.
- <strong>"calories_hourly"</strong>: a minimum of hours containing at least a given number of minutes with energy expenditure above the resting metabolic rate. The suggested default configuration is looking for days with at least 10 hours that contain at least 1 minute above the resting metabolic rate.

### main options

- <strong>"steps"</strong>: a minimum number of steps ("steps_param") is required to consider a day as valid.
- <strong>"minute_day"</strong>: the ratio of minute data (steps and calories) resampled to day and daily data obtained from daily summarize files should be over a given decimal between 0 and 1 ("minute_day_param") to consider a day as valid.
- <strong>"waking"</strong>: only minutes between 5:00 and 22:59 are considered for the evaluation.
- <strong>"synch_check"</strong>: evaluate the validity of data based on the interval between two synchronization dates. Interval criteria, which depend on device specifications, can be found in <a ref="https://github.com/OchaUni-Physical-Activity-Measurement/ActiWearCheck/blob/main/actiwearcheck/devices/20241015_devices.yaml">./ActiWearCheck/actiwearcheck/devices/20241015_devices.yaml</a>.

#### full documentation (help)
```
method: 'hr_continue' (default), 'calories_continue', 'calories_hourly', 'steps_day', 'steps_hourly', 'all'
Evaluate valid wear days.
'hr_continue': from the number of minutes with HR data found in daily data files. HR data files are used.
'calories_continue': from the number of minutes with EE above REE. Minute data files are used.
'calories_hourly': from the number of hours with a least a selected number of minutes with EE above REE minute. Minute data files are used.
'steps_day': from the number of steps recorded during the day. Steps files are used.
'steps_hourly': from the number of hours with enough steps during the day. Minute steps data files are used.

hr_continue: int between 0 and 1440. (default = 600)
number of minutes to be used as evaluation criteria for the 'hr_continue' method.

calories_continue: int between 0 and 1440. (default = 600)
number of minutes to be used as evaluation criteria for the 'calories_continue' method.

calories_hourly: [int between 1 and 24, int between 1 and 60] (default = [10, 1])
number of hours and minute-per-hour to be used as evaluation criteria for the 'calories_hourly' method.

steps_day: int equal or higher than 0 (default = 1)
number of steps to be used as evaluation criteria for the 'steps_day' method.

steps_hourly: [int between 1 and 24, int between 1 and 60] (default = [10, 1])
number of hours and steps-per-hour to be used as evaluation criteria for the 'steps_hourly' method.

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
```
