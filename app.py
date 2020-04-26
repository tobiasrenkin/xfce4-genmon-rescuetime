#!/usr/bin/env python3

import requests
import datetime, time
import pprint
import json
import re
import sys, os

### basic definitions
sdir = os.getenv("HOME")+"/.config/xfce4-genmon-rescuetime"
adir = "/".join(sys.path[0].split("/")[:])
now = datetime.datetime.now()
today = datetime.datetime.today().strftime('%Y-%m-%d')
tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

########################################################################

def quitwithna(text="NA"):
	print("<txtclick>python3 "+adir+"/chart.py</txtclick><txt><span weight='bold'><span fgcolor="+cfg["colors"]["text"]+">"+text+"</span></span></txt>")
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
	# get basic json data
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
	
	# reformat to [%Y-m-dT%H:%M:%S, productivity, minutes]; Add interval (hours, minutes, etc.) and time stamp
	data = {}
	data["interval"] = interval
	data["timestamp"] = time.time()
	data["rows"] = []
	for r in rawdata["rows"]:
		data["rows"].append([r[0], r[-1], r[1]/60])
	return data


########################################################################

# load settings, else use default
with open(adir+"/defaultcfg", "r") as f:
		defaultcfg = json.loads(f.read())

if os.path.exists(sdir+"/settings"):
	with open(sdir+"/settings", "r") as f:
		cfg = json.loads(f.read())
else:
	cfg = defaultcfg
		
if "key" not in cfg:
	cfg["key"] = askkey()
elif "key" == "":
	cfg["key"] = askkey()

cfg["app"].setdefault("start_hour", defaultcfg["app"]["start_hour"])
cfg["app"].setdefault("end_hour", defaultcfg["app"]["end_hour"])
cfg["app"].setdefault("pulse_period_m", defaultcfg["app"]["pulse_period_m"])
cfg["stats"].setdefault("refreshperiod_d", defaultcfg["stats"]["refreshperiod_d"])
cfg["stats"].setdefault("statperiod_d", defaultcfg["stats"]["statperiod_d"])
cfg["colors"].setdefault("bad", defaultcfg["colors"]["bad"])
cfg["colors"].setdefault("medium", defaultcfg["colors"]["medium"])
cfg["colors"].setdefault("success", defaultcfg["colors"]["success"])
cfg["colors"].setdefault("avg", defaultcfg["colors"]["avg"])
cfg["colors"].setdefault("goal", defaultcfg["colors"]["goal"])
cfg["colors"].setdefault("text", defaultcfg["colors"]["text"])
cfg["colors"].setdefault("bg", defaultcfg["colors"]["bg"])
cfg.setdefault("goals", defaultcfg["goals"])

########################################################################

# if outside of app hours, quit now
if now.hour<cfg["app"]["start_hour"] or now.hour>=cfg["app"]["end_hour"]:
	quitwithna("FREE")

# download data from last Y days every once in a while

refresh = False
try:
	with open(sdir+"/yearlystats", "r") as f:
		data_stats = json.loads(f.read())
	lastrefresh = datetime.datetime.fromtimestamp(data_stats["timestamp"])
	if (now - lastrefresh).days > cfg["stats"]["refreshperiod_d"]:
		refresh = True
except (KeyError, IOError):
	refresh = True

if refresh:
	rb = (datetime.datetime.today() - datetime.timedelta(days=cfg["stats"]["statperiod_d"])).strftime('%Y-%m-%d')
	try:
		data_stats = api_request(cfg["key"], "hour", rb, today)
		with open(sdir+"/yearlystats", "w") as f:
			f.write(json.dumps(data_stats))
	except URLError:
		pass

########################################################################

# get todays data
try:
	data_today = api_request(cfg["key"], "minute", today, tomorrow)
except URLError:
	quitwithna("404")

# calc pulse: % productive time over _period_ minutes

period = cfg["app"]["pulse_period_m"]
cutoff = now - datetime.timedelta(minutes=period)

prodtime_period = 0
prodtime_day = 0
totaltime_day = 0
prodtime_hours = [0]*24

for r in data_today["rows"]:
	time = datetime.datetime.strptime(r[0], "%Y-%m-%dT%H:%M:%S")
	totaltime_day += r[-1]
	if r[1] > 0:
		prodtime_day += r[-1]
		prodtime_hours[time.hour] += r[-1]
		if time > cutoff:
			prodtime_period += r[-1]

with open(sdir+"/cache", "w") as f:
	f.write(json.dumps(prodtime_hours))

pulse_period = round(prodtime_period / period * 100)
if totaltime_day > 0:
	pulse_day = round(prodtime_day / totaltime_day * 100)
else:
	pulse_day = 0

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
txtclick = "<txtclick>python3 "+adir+"/chart.py</txtclick>"
icon = ""
txt = "<txt><span weight='bold'><span fgcolor='{2}'>{0}</span>/<span fgcolor='{3}'>{1}</span></span></txt>".format(pulse_period, pulse_day, periodcolor, daycolor)

print(tooltip+txtclick+icon+txt)