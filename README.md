# ActiWearCheck (Fitbit valid wear estimation software)   
**Input: PA and HR data from  Fitbit (.csv per subject in ~/samples)**  
**Output: filters for each day (.csv per subject in ~/results)**  
**Script: ActiWearCheck.ipynb**  

Three different methods to estimate days with valid wear from Fitbit minute data.
Please consult the [log] at the beggining of the notebook to get information about the features and progress.  

**Warning: the name of columns, file names, key and path may change over software's versions**

*Step by step description:*
- gather all the physical activity data from fitbit trackers as .csv files in the same folder (see exemples of file structure in ["~/samples"](https://github.com/OchaUni-Physical-Activity-Measurement/ActiWearCheck/tree/main/samples) for examples)
- apply the script provided ([**ActiWearCheck.ipynb**](https://github.com/OchaUni-Physical-Activity-Measurement/ActiWearCheck/blob/main/ActiWearCheck.ipynb)), which:
    - imports all the .csv files as dataframes in Python.
    - applies different filters for each days:
        - removes days with a =<1 step record, which indicates that the device was not worn during the 24-hour period or that the battery was discharged.
        - removes days with a discrepancy b >=10% between the daily EE estimates provided by the original Fitbit application and the EE estimates computed by resampling the minute-per-minute EE data, which indicates that the minute-per-minute data record was corrupted possibly due to memory or sync issues.
    - calculates, for each day, the minute with the minimum calories value. This defines the resting metabolic rate (RMR).
    - defines each minute in each day as above or beyound RMR.
    - application of different methods:
        - Method 1 = days with valid wear required a minimum of c = 600 minutes above the estimated RMR.
        - Method 2 = days with valid wear required a minimum of d = 10 hours containing at least e = 1 minute above the RMR.
        - Method 3 = days with valid wear required a minimum of f = X steps *(not used in the manuscript presenting the software)*.
        - Method HR = days with valid wear required a minimum of g = 600 minutes with HR data.
    - you can also restrain the of-interest period during the day (ex: from 5am to 11pm) applying h = waking hours *(not used in the manuscript presenting the software)*.
     - you obtain one .csv file per individual, whith Steps and Calories PA data and several filters bool columns for each day (see exemples of files structure in  ["~/results"](https://github.com/OchaUni-Physical-Activity-Measurement/ActiWearCheck/tree/main/results))

Note: a, b, c ,d, e, f,g and h values can me modified in the script.  

___
We provide the analysis code, data and results for the application of this software on data obtained during the [drePAnon clinical trial (UMIN000042826)](https://center6.umin.ac.jp/cgi-open-bin/ctr_e/ctr_view.cgi?recptno=R000048880) research project in the ["~/analysis" folder](https://github.com/OchaUni-Physical-Activity-Measurement/ActiWearCheck/tree/main/analysis).
