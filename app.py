#!/usr/bin/env python3

import requests
from datetime import datetime, timedelta
from dateutil.parser import parse
import collections
import time
import pprint
import json
import re
import sys, os

from utils import gencfg

### basic definitions
sdir = os.getenv("HOME")+"/.config/xfce4-genmon-rescuetime"
if not(os.path.exists(sdir)):
	os.mkdir(sdir)
adir = "/".join(sys.path[0].split("/")[:])

now = datetime.now()
today = datetime.today().strftime('%Y-%m-%d')
tomorrow = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')

tooltip = "<tool></tool>"
txtclick = "<txtclick>python3 {0}/chart.py</txtclick>".format(adir)
icon = ""

########################################################################

def stop(text="NA"):
	print(tooltip+txtclick+"<txt><span weight='bold'><span fgcolor={0}>{1}</span></span></txt>".format(
		cfg["colors"]["text"], text))
	sys.exit(0)

def askkey():
	import tkinter as tk
	from tkinter import simpledialog as sd
	tkinput = tk.Tk()
	tkinput.withdraw()
	key = sd.askstring("Input", "Enter Rescuetime API key")
	tkinput.destroy()
	return key

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


########################################################################

# load settings, else use default
cfg = gencfg(adir+"/defaultcfg", sdir+"/settings")

if cfg.get("key", "") == "":
	cfg["key"] = askkey()
	with open(sdir+"/settings", "w") as f:
		f.write(json.dumps(cfg))

########################################################################

# if outside of app hours, quit now
if now.hour < cfg["app"]["start_hour"] or now.hour >= cfg["app"]["end_hour"]:
	stop("Free")

########################################################################

# refresh data used for stats every once in a while

refresh = False
try:
	if (now - datetime.fromtimestamp(os.path.getmtime(sdir+"/yearlystats"))).days > cfg["stats"]["refreshperiod_d"]:
		refresh = True
except OSError:
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

########################################################################

# calc pulse: % productive time over _period_ minutes
timefmt = "%Y-%m-%dT%H:%M:%S"
period = cfg["app"]["pulse_period_m"]
cutoff = now - timedelta(minutes=period)

totaltime_day = sum([d["min"] for d in data])
prodtime_day = sum([d["min"] for d in data if d["prod"] > 0])
prodtime_period = sum([d["min"] for d in data if d["prod"] > 0 and datetime.strptime(d["time"], timefmt) > cutoff])
prodtime_hours = [sum([d["min"] for d in data if d["prod"] > 0 and datetime.strptime(d["time"], timefmt).hour == t]) for t in range(24)]

p_pd = prodtime_period / period * 100
p_day = prodtime_day / totaltime_day * 100 if totaltime_day > 0.0 else 0.0

with open(sdir+"/cache", "w") as f:
	f.write(json.dumps(prodtime_hours))

########################################################################

# format and output

gls = cfg["goals"]
t = now.hour
color_pd = "bad" if p_pd < gls[t]/2 else "medium" if p_pd < gls[t] else "success"
color_day = "bad" if p_day < 33 else "medium" if p_day < 66 else "success"

txt = ("<txt><span weight='bold'><span fgcolor='%s'>%.0f</span>/<span fgcolor='%s'>%.0f</span></span></txt>" 
	% (cfg["colors"][color_pd], p_pd, cfg["colors"][color_day], p_day))

print(tooltip+txtclick+icon+txt)