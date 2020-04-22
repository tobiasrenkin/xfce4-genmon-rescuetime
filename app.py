#!/usr/bin/env python3

import requests
import datetime
import pprint
import json
import re
import sys, os

sdir = os.getenv("HOME")+"/.config/xfce4-genmon-rescuetime"
adir = "/".join(sys.path[0].split("/")[:])

# check if key is set up
def askkey():
	import tkinter as tk
	from tkinter import simpledialog as sd
	tkinput = tk.Tk()
	tkinput.withdraw()
	key = sd.askstring("Input", "Enter Rescuetime API key")
	tkinput.destroy()
	return key

if not(os.path.exists(sdir)):
	os.mkdir(sdir)
try:
    with open(sdir+"/settings") as f:
    	settings = json.loads(f.read())
    	key = settings["key"]
except (IOError, KeyError):
	key = askkey()
	with open(sdir+"/settings", "w") as f:
			f.write(json.dumps({"key":key}))

# prep api call
today = datetime.datetime.today().strftime('%Y-%m-%d')
tomorrow = (datetime.datetime.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

rspec = {
	"key": key,
	"format": "json",
	"by": "interval",
	"interval": "minute",
	"rb": today,
	"re": tomorrow,
	"rk": "productivity"
}

rstr = "https://www.rescuetime.com/anapi/data" + "?" + "&".join([k+"="+rspec[k] for k in rspec.keys()])
r = requests.get(rstr)
rawdata = json.loads(r.text)

# calc pulse: % productive time over _period_ minutes

now = datetime.datetime.now()
period = 30
cutoff = datetime.datetime.now() - datetime.timedelta(minutes=period)

prodtime_period = 0
prodtime_day = 0
totaltime_day = 0
prodtime_hours = [0]*24
for r in rawdata["rows"]:
	m = re.match("([0-9]+)-([0-9]+)-([0-9]+)T([0-9]+):([0-9]+):[0-9]+", r[0])
	year = int(m[1])
	month = int(m[2])
	day = int(m[3])
	hour = int(m[4])
	minute = int(m[5])
	time = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
	
	totaltime_day += r[1]/60
	if r[-1]>0:
		prodtime_day += r[1]/60
		prodtime_hours[time.hour] += r[1]/60
		if time>cutoff:
			prodtime_period += r[1]/60

with open(sdir+"/cache", "w") as f:
	f.write(json.dumps(prodtime_hours))

pulse_period = round(prodtime_period/period*100)
if totaltime_day>0:
	pulse_day = round(prodtime_day/totaltime_day*100)
else:
	pulse_day = 0

# format output

if pulse_period==0:
	periodcolor="grey"
elif pulse_period<33:
	periodcolor="red"
elif pulse_period<66:
	periodcolor="yellow"
else:
	periodcolor="green"

if pulse_day==0:
	daycolor="grey"
elif pulse_day<33:
	daycolor="red"
elif pulse_day<66:
	daycolor="yellow"
else:
	daycolor="green"


tooltip = "<tool>Share productive time over last {0} minutes / day</tool>".format(period)
txtclick = "<txtclick>python3 "+adir+"/chart.py</txtclick>"
icon = ""
txt = "<txt><span weight='bold'><span fgcolor='{2}'>{0}</span>/<span fgcolor='{3}'>{1}</span></span></txt>".format(pulse_period, pulse_day, periodcolor, daycolor)

print(tooltip+txtclick+icon+txt)