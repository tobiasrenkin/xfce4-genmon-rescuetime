#!/usr/bin/env python3
import json, collections

def update(d, u):
	for k, v in u.items():
		if isinstance(v, collections.abc.Mapping):
			d[k] = update(d.get(k, {}), v)
		else:
			d[k] = v
	return d

def gencfg(default, user):
	with open(default, "r") as f:
		cfg = json.loads(f.read())
	try:
		with open(user, "r") as f:
			usercfg = json.loads(f.read())
	except:
		usercfg = {}
	cfg = update(cfg, usercfg)
	return cfg

def api_request(key, interval, start, end):
	rspec = {"format": "json", "by": "interval", "rk": "productivity", "key": key, "interval": interval, "rb": start, "re": end}
	rstr = "https://www.rescuetime.com/anapi/data" + "?" + "&".join([k+"="+rspec[k] for k in rspec.keys()])
	try:
		apianswer = requests.get(rstr).text
	except:
		raise URLError
	rawdata = json.loads(apianswer)

	# rawdata[rows] format: datetime, minutes, ....., productivity level.
	# reformat to [%Y-m-dT%H:%M:%S, productivity, minutes]; Add interval (hours, minutes, etc.) and time stamp
	data = {"interval": interval, "timestamp": time.time()}
	data["rows"] = [{"prod": r[-1], "min": r[1]/60, "time": r[0]} for r in rawdata["rows"]]
		
	return data
