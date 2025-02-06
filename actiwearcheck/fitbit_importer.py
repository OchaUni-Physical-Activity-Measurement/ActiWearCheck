#!/usr/bin/env python3

import fitbit
import json
from functools import partial
import os
import numpy as np
import pandas as pd
from glob import glob
import datetime


def get_token(filename):
	res = {'access_token': None, 'refresh_token': None}
	if filename is not None and os.path.isfile(filename):
		with open(filename, "r") as f:
			res = json.load(f)
	return res

def update_token(filename, token):
	with open(filename, "w") as f:
		json.dump(token,f)

def get_client_params(args):
	res = {}
	if args.id_file is not None:
		with open(filename, "r") as f:
			res = json.load(f)
	if args.id is not None:
		res["CLIENT_ID"] = args.id
	if args.secret is not None:
		res["CLIENT_SECRET"] = args.secret

	return res

def get_syncs(name):
	files = glob(name+"_syncEvents_*.csv")
	df = None
	columns = ["DateTime", "SyncDateUTC", "Provider", "DeviceName"]
	if len(files) == 0:
		df = pd.DataFrame(columns=columns)
	else:
		df = pd.read_csv(files[-1])
	return df

def check_sync(df, response):
	last_sync = datetime.datetime.fromisoformat(response['lastSyncTime']).strftime("%m/%d/%Y %I:%M:%S %p")
	return df["SyncDateUTC"].str.contains(last_sync).any()

def update_syncs(name, df, response, keep=False):
	new_val = [[datetime.datetime.now().strftime("%m/%d/%Y %I:%M:%S %p"),datetime.datetime.fromisoformat(response['lastSyncTime']).strftime("%m/%d/%Y %I:%M:%S %p"),"fitbit",response['deviceVersion']]]
	df_final = pd.concat([df, pd.DataFrame(new_val,columns=df.columns)]).reset_index(drop=True)
	from_date = datetime.datetime.strptime(df_final.iloc[0,1],"%m/%d/%Y %I:%M:%S %p").strftime("%Y%m%d")
	to_date = datetime.datetime.strptime(df_final.iloc[-1,1],"%m/%d/%Y %I:%M:%S %p").strftime("%Y%m%d")
	previous_date = to_date
	if len(df_final) > 1:
		previous_date = datetime.datetime.strptime(df_final.iloc[-2,1],"%m/%d/%Y %I:%M:%S %p").strftime("%Y%m%d")
		if to_date == previous_date:
			# we are syncing twice the same day, remove the previous sync today
			df_final.drop([len(df_final)-2], axis=0, inplace=True)
	df_final.to_csv(f"{name}_syncEvents_{from_date}_{to_date}.csv", index=False)
	if not keep and (previous_date != to_date):
		os.remove(f"{name}_syncEvents_{from_date}_{previous_date}.csv")
	return df_final

def get_date_range(name, activity):
	files = glob(f"{name}_{activity}_*.csv")
	if len(files) == 0:
		return None
	filename = files[-1][:-4]
	return "_".join(filename.split("_")[-2:])


# username is the base name for files.
# activity is the file we want
# filename_date_range is the date range used in the filename we want to open. Useful when multiple files co-exist. None means we take the last file (according to the file system)
def get_daily_activity(username, activity, filename_date_range=None):
	if filename_date_range is None:
		filename_date_range = get_date_range(username, activity)
		if filename_date_range is None: 
			#Not an update and no data
			return pd.DataFrame(columns=[_eq_day_name[activity], _eq_activity_list[activity]])
	df = pd.read_csv(f"{username}_{activity}_{filename_date_range}.csv")
	return df


def parse_daily_calories(res):
	lines = []
	columns = ["ActivityDay", "Calories"]
	entries = res['activities-heart']
	for entry in entries:
		lines.append([datetime.datetime.strptime(entry['dateTime'],"%Y-%m-%d").strftime("%m/%d/%Y"),np.sum([value['caloriesOut'] if 'caloriesOut' in value else 0 for value in entry['value']['heartRateZones']])])
	df = pd.DataFrame(lines, columns=columns)
	return df

def parse_steps(res):
	lines = []
	columns = ["ActivityDay", "StepTotal"]
	entries = res['activities-tracker-steps']
	for entry in entries:
		lines.append([datetime.datetime.strptime(entry['dateTime'],"%Y-%m-%d").strftime("%m/%d/%Y"), entry['value']])
	df = pd.DataFrame(lines, columns=columns)
	return df

def parse_weartime(res):
	lines = []
	columns = ["Day", "TotalMinutesWearTime"]
	entries = res['activities-heart']
	for entry in entries: 
		lines.append([datetime.datetime.strptime(entry['dateTime'],"%Y-%m-%d").strftime("%m/%d/%Y"),np.sum([value['minutes'] if 'minutes' in value else 0 for value in entry['value']['heartRateZones']])])
	df = pd.DataFrame(lines, columns=columns)
	return df

def parse_minute_wear(res):
	lines = []
	columns = ["Day", "TotalMinutesWearTime"]
	entries = res['activities-heart']
	for entry in entries: 
		lines.append([datetime.datetime.strptime(entry['dateTime'],"%Y-%m-%d").strftime("%m/%d/%Y"),np.sum([value['minutes'] if 'minutes' in value else 0 for value in entry['value']['heartRateZones']])])
	df = pd.DataFrame(lines, columns=columns)
	return df

def parse_intraday(res, date, value_name):
	lines = []
	columns = ["ActivityMinute", value_name]
	entries = res['dataset']
	for entry in entries:
		day_minute = date.strftime("%m/%d/%Y")+" "+datetime.datetime.strptime(entry['time'],"%H:%M:%S").strftime("%I:%M:%S %p")
		
		lines.append([day_minute, entry['value']])
	df = pd.DataFrame(lines, columns=columns)
	return df

def parse_daily_activity(res, activity):
	return _eq_parse_list[activity](res)

def update_daily_activity(name, activity, response, filename_date_range=None, keep=False):
	df = get_daily_activity(name,activity)
	df2 = parse_daily_activity(response, activity)
	print(df2)
	previous_range = None
	if filename_date_range is None:
		filename_date_range = get_date_range(name, activity)
		if filename_date_range is None: 
			#get it from response
			from_date = datetime.datetime.strptime(df2[_eq_day_name[activity]].iloc[0],"%m/%d/%Y").strftime("%Y%m%d")
		else:# update the second part
			previous_range = filename_date_range
			from_date = filename_date_range.split("_")[0]
		to_date = datetime.datetime.strptime(df2[_eq_day_name[activity]].iloc[-1],"%m/%d/%Y").strftime("%Y%m%d")
		filename_date_range = f"{from_date}_{to_date}"
			
	if len(df) >0:
		if df[_eq_day_name[activity]].iloc[-1] == df2[_eq_day_name[activity]].iloc[0]:
			#overlap in data
			#We keep the highest value
			if float(df2[_eq_activity_list[activity]].iloc[0]) > float(df[_eq_activity_list[activity]].iloc[-1]):
				df.drop(df.index[-1], inplace=True)
			else:
				#df2 is either the same or lost data
				df2.drop(df2.index[0], inplace=True)
		df_final = pd.concat([df,df2])
	else:
		df_final = df2
	df_final.to_csv(f"{name}_{activity}_{filename_date_range}.csv", index=False)
	if (not keep) and (previous_range is not None) and (previous_range != filename_date_range):
		os.remove(f"{name}_{activity}_{previous_range}.csv")

def get_last_entry_minute(name, activity):

	files = glob(f"{name}_{activity}_*.csv")
	if len(files) == 0:
		return None
	df = pd.read_csv(files[-1])
	return df

def update_intraday_activity(name, activity, max_days=7, keep=False):
	date = datetime.datetime.now() - datetime.timedelta(days=max_days) # take the last max_days days
	from_date = date
	end_date = datetime.datetime.now()
	all_df = []
	prev_df = get_last_entry_minute(name, activity)
	overlap_check = None
	if prev_df is not None:
		all_df = [prev_df]
		from_date = datetime.datetime.strptime(prev_df.iloc[0]["ActivityMinute"], "%m/%d/%Y %I:%M:%S %p")
		date = datetime.datetime.strptime(prev_df.iloc[-1]["ActivityMinute"], "%m/%d/%Y %I:%M:%S %p")
		overlap_check = datetime.datetime.strptime(prev_df.iloc[-1]["ActivityMinute"], "%m/%d/%Y %I:%M:%S %p")
	while date <= end_date:
		res = authed_client.intraday_time_series(_eq_entry_list[activity], base_date=date.strftime("%Y-%m-%d"))
		res_df = parse_intraday(res[_eq_intraday_entry[activity]],date, _eq_intraday_list[activity])
		# check overlap
		if overlap_check is not None:
			if datetime.datetime.strptime(res_df.iloc[0]["ActivityMinute"], "%m/%d/%Y %I:%M:%S %p") <= overlap_check:
				# There's overlap
				# First, find the relevant entries
				location = prev_df.index[prev_df["ActivityMinute"] == res_df.iloc[0]["ActivityMinute"]]
				res_index_range = res_df.index[[overlap_check>=datetime.datetime.strptime(val, "%m/%d/%Y %I:%M:%S %p") for val in res_df["ActivityMinute"]]]
				# Then take the max
				best_values = np.maximum(pd.to_numeric(prev_df.loc[location[0]:][_eq_intraday_list[activity]]).to_numpy(),pd.to_numeric(res_df.loc[res_index_range][_eq_intraday_list[activity]]).to_numpy())
				prev_df.loc[location[0]:,_eq_intraday_list[activity]] = best_values
				# Delete duplicated entries
				res_df.drop(res_index_range, inplace=True)

		all_df.append(res_df)
		date += datetime.timedelta(days=1)
	final_df = pd.concat(all_df)
	final_df.to_csv(f"{name}_{activity}_"+from_date.strftime("%Y%m%d")+"_"+end_date.strftime("%Y%m%d")+".csv",index=False)
	if not keep and overlap_check is not None and overlap_check.strftime("%Y%m%d") != end_date.strftime("%Y%m%d"):
		os.remove("{name}_{activity}_"+from_date.strftime("%Y%m%d")+"_"+overlap_check.strftime("%Y%m%d")+".csv")

_eq_activity_list = {"dailyCalories": "Calories", "dailySteps": "StepTotal", "fitbitWearTimeViaHR": "TotalMinutesWearTime"}
_eq_intraday_entry = {"minuteCaloriesNarrow": 'activities-calories-intraday', "minuteStepsNarrow": 'activities-steps-intraday'}
_eq_intraday_list = {"minuteCaloriesNarrow": "Calories", "minuteStepsNarrow": "Steps"}
_eq_parse_list = {"dailyCalories": parse_daily_calories, "dailySteps": parse_steps, "fitbitWearTimeViaHR": parse_weartime}
_eq_entry_list = {"dailyCalories": 'activities/heart', "dailySteps": 'activities/tracker/steps', "fitbitWearTimeViaHR": 'activities/heart', "minuteCaloriesNarrow": 'activities/calories', "minuteStepsNarrow": 'activities/steps'}
_eq_day_name = {"dailyCalories": "ActivityDay", "dailySteps": "ActivityDay", "fitbitWearTimeViaHR": "Day"}



if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('-t', '--token', type=str, default="name1_token.txt", help = "Path to authentication token")
	parser.add_argument('-i', '--id', type=str, default=None, help = "App client id")
	parser.add_argument('-s', '--secret', type=str, default=None, help= "App client secret")
	parser.add_argument('--id_file', type=str, default=None, help="Path to the file containing the client id and client secret. Overridden by command line data (-i and -s)")
	parser.add_argument('--url', type=str, default=None, help="Redirection url used by your app")
	parser.add_argument('-o', '--output', type=str, default="name1", help="Pattern for saving the data files")
	parser.add_argument('--keep', action='store_true', help="Keep previous files after updates")
	parser.add_argument('--max_days', type=int, default=7, help="Maximum number of days to look back for intraday data")
	args = parser.parse_args()
	token_dict = get_token(args.token) # either obtained beforehand, or using the gather_keys_oauth2.py script from python-fitbit
	refresh_cb = partial(update_token, args.token)
	client_params = get_client_params(args)

	#TODO:get from and to from the data, make a file using the pattern and saving it
	authed_client = fitbit.Fitbit(client_params["CLIENT_ID"], client_params["CLIENT_SECRET"], access_token=token_dict['access_token'],\
	   								refresh_token=token_dict['refresh_token'], refresh_cb=refresh_cb, redirect_uri=args.url)
		
	res= authed_client.get_devices()
	#authed_client.time_series('activities/heart', period="max")

	df = get_syncs(args.output)
	if not check_sync(df, res[0]): #TODO what about the case with multiple devices?
		df = update_syncs(args.output, df, res[0], keep=args.keep)
		if len(df) == 1 and len(get_daily_activity(args.output, "dailyCalories"))==0: # First time syncing data; if partial files, nothing we can do
			base_date = "today"
			period = "max"
			end_date = None
		else:
			base_date = datetime.datetime.strptime(df.iloc[-1,1],"%m/%d/%Y %I:%M:%S %p").strftime("%Y-%m-%d")
			end_date = datetime.datetime.now().strftime("%Y-%m-%d")
			period = None
		for activity in _eq_activity_list:
			print(activity)
			print(base_date, end_date)
			update_daily_activity(args.output, activity, authed_client.time_series(_eq_entry_list[activity], base_date= base_date, end_date=end_date, period=period), keep=args.keep)
			print("=================================")
		for activity in _eq_intraday_list:
			print(activity)
			update_intraday_activity(args.output,activity,max_days=args.max_days, keep=args.keep)
			print("=================================")
	else:
		print("sync is up to date")
