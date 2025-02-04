#!/usr/bin/env python3

import fitbit
import json
from functools import partial
import os

def get_token(filename):
	res = {'access_token': None, 'refresh_token': None}
	if filename is not None and os.path.isfile(filename):
		with open(filename, "r") as f:
			res = json.load(f)
	return res

def update_token(filename, token):
	with open(filename, "w") as f:
		f.write(token)

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

if __name__ == "__main__":
	import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--token', type=str, default="name1_token.txt", help = "Path to authentication token.")
    parser.add_argument('-i', '--id', type=str, default=None, help = "App client id")
    parser.add_argument('-s', '--secrect', type=str, default=None, help= "App client secret")
    parser.add_argument('--id_file', type=str, default=None, help="Path to the file containing the client id and client secret. Overridden by command line data (-i and -s)")
    parser.add_argument('--url', type=str, default=None, help="Redirection url used by your app")
    parser.add_argument('-o', '--output', type=str, default="name1_FROM_TO", help="Pattern for saving the data files")
    args = parser.parse_args()
    token_dict = get_token(args.token) # either obtained beforehand, or using the gather_keys_oauth2.py script from python-fitbit
    refresh_cb = partial(update_token, args.token)
    client_params = get_client_params(args)
    authed_client = fitbit.Fitbit(client_params["CLIENT_ID"], client_params["CLIENT_SECRET"], access_token=token_dict['access_token'],\
       								refresh_token=token_dict['refresh_token'], refresh_cb=refresh_cb, redirect_uri=args.url)
    
    print(authed_client.time_series('activities/heart', period="max"))
    #TODO:get from and to from the data, make a file using the pattern and saving it


