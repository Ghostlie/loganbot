import json
import os

user_path = "users/"
default_data = {"nick": "", "id": ""}

def read(user_id):

	path = user_path+user_id
	data = default_data
	if os.path.exists(path):
		try:data = json.load(open(path))
		except: pass
	data["id"] = user_id
	return data
		
def write(user_id, data):
	path = user_path+user_id
	temp_path = path+"_temp"
	with open(temp_path, "w") as f:
		f.write(json.dumps(data))
	if os.path.exists(temp_path):
		try: os.rename(temp_path, path)
		except: pass
