import json
import os

channel_path = "channels/"
default_data = {"data": None}

def read(channel):
	path = channel_path+channel
	data = default_data
	if os.path.exists(path):
		with open(path) as f:
			try: data = json.load(f)
			except: pass
	return data

def write(channel, data):
	path = channel_path+channel
	temp_path = path+"_temp"
	with open(temp_path, "w") as f:
		f.write(json.dumps(data))
	if os.path.exists(temp_path):
		try: os.rename(temp_path, path)
		except: pass