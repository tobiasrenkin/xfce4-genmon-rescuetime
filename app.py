#!/usr/bin/env python3

import requests
from datetime import datetime, timedelta
import time
import pprint
import json
import re
import sys, os

### basic definitions
sdir = os.getenv("HOME")+"/.config/xfce4-genmon-rescuetime"
adir = "/".join(sys.path[0].split("/")[:])

now = datetime.now()
today = datetime.today().strftime('%Y-%m-%d')
tomorrow = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')

########################################################################

def quit(text="NA"):
	print("<txtclick>python3 {0}/chart.py</txtclick><txt><span weight='bold'><span fgcolor={1}>{2}</span></span></txt>".format(
		adir, cfg["colors"]["text"], text))
	sys.exit()

def askkey():
	import tkinter as tk
	from tkinter import simpledialog as sd
	tkinput = tk.Tk()
	tkinput.withdraw()
	key = sd.askstring("Input", "Enter Rescuetime API key")
	tkinput.destroy()
	return key

def api_request(key, interval, start, end):
	rspec = {"format": "json", "by": "interval", "rk": "productivity", "key": key,
		"interval": interval,
		"rb": start,
		"re": end
	}
	rstr = "https://www.rescuetime.com/anapi/data" + "?" + "&".join([k+"="+rspec[k] for k in rspec.keys()])
	try:
		apianswer = requests.get(rstr).text
	except:
		raise URLError

	rawdata = json.loads(apianswer)
	# rawdata[rows] format: datetime, minutes, ....., productivity level.
	# reformat to [%Y-m-dT%H:%M:%S, productivity, minutes]; Add interval (hours, minutes, etc.) and time stamp
	data = {"interval": interval, "timestamp": time.time(), "rows": []}
	for r in rawdata["rows"]:
		data["rows"].append({"prod": r[-1], "min": r[1]/60, "time": r[0]})
	
	return data


########################################################################

# load settings, else use default
with open(adir+"/defaultcfg", "r") as f:
		cfg = json.loads(f.read())

try:
	with open(sdir+"/settings", "r") as f:
		usercfg = json.loads(f.read())
except:
	usercfg = {}

for key in cfg:
	if key in usercfg:
		if isinstance(cfg[key],dict):
			for subkey in cfg[key]:
				if subkey in usercfg[key]:
					cfg[key][subkey] = usercfg[key][subkey]
		else:
			cfg[key] = usercfg[key]

if cfg.get("key", "") == "":
	cfg["key"] = askkey()

########################################################################

# if outside of app hours, quit now
if now.hour<cfg["app"]["start_hour"] or now.hour>=cfg["app"]["end_hour"]:
	quit("Free")

# refresh data from last Y days every once in a while
refresh = False
try:
	with open(sdir+"/yearlystats", "r") as f:
		data_stats = json.loads(f.read())
	lastrefresh = datetime.fromtimestamp(data_stats["timestamp"])
except (KeyError, IOError):
	refresh = True
if (now - lastrefresh).days > cfg["stats"]["refreshperiod_d"]:
	refresh = True

if refresh:
	rb = (datetime.today() - timedelta(days=cfg["stats"]["statperiod_d"])).strftime('%Y-%m-%d')
	try:
		data_stats = api_request(cfg["key"], "hour", rb, today)
		with open(sdir+"/yearlystats", "w") as f:
			f.write(json.dumps(data_stats))
	except URLError:
		pass

########################################################################

# get todays data
try:
	data = api_request(cfg["key"], "minute", today, tomorrow)["rows"]
except URLError:
	quit("404")

# calc pulse: % productive time over _period_ minutes
period = cfg["app"]["pulse_period_m"]
cutoff = now - timedelta(minutes=period)

totaltime_day = sum([d["min"] for d in data])
prodtime_day = sum([d["min"] for d in data if d["prod"]>0])
prodtime_period = sum([d["min"] for d in data if d["prod"]>0 and datetime.strptime(d["time"], "%Y-%m-%dT%H:%M:%S")>cutoff])
prodtime_hours = [sum([d["min"] for d in data if d["prod"]>0 and datetime.strptime(d["time"], "%Y-%m-%dT%H:%M:%S").hour==t]) for t in range(24)]

pulse_period = round(prodtime_period / period * 100)
pulse_day = round(prodtime_day / totaltime_day * 100) if totaltime_day > 0 else 0

with open(sdir+"/cache", "w") as f:
	f.write(json.dumps(prodtime_hours))

# format output
if pulse_period==0:
	periodcolor="grey"
elif pulse_period<cfg["goals"][now.hour]/2:
	periodcolor=cfg["colors"]["bad"]
elif pulse_period<cfg["goals"][now.hour]:
	periodcolor=cfg["colors"]["medium"]
else:
	periodcolor=cfg["colors"]["success"]

if pulse_day==0:
	daycolor="grey"
elif pulse_day<33:
	daycolor=cfg["colors"]["bad"]
elif pulse_day<66:
	daycolor=cfg["colors"]["medium"]
else:
	daycolor=cfg["colors"]["success"]

tooltip = "<tool>Share productive time over last {0} minutes / day</tool>".format(period)
txtclick = "<txtclick>python3 {0}/chart.py</txtclick>".format(adir)
icon = ""
txt = "<txt><span weight='bold'><span fgcolor='{2}'>{0}</span>/<span fgcolor='{3}'>{1}</span></span></txt>".format(
	pulse_period, pulse_day, periodcolor, daycolor)

print(tooltip+txtclick+icon+txt)