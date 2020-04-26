#!/usr/bin/env python3
from tkinter import font
from tkinter import *
import datetime
import json
import sys, os
import subprocess
import re

sdir = os.getenv("HOME")+"/.config/xfce4-genmon-rescuetime"
adir = "/".join(sys.path[0].split("/")[:])

# load settings
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

# load produvtivity data
with open(sdir+"/cache", "r") as f:
	rawdata_today = json.loads(f.read())
with open(sdir+"/yearlystats", "r") as f:
	rawdata_stats = json.loads(f.read())

now = datetime.datetime.now()
total_today = sum(rawdata_today)
data_today = [rawdata_today[d]/60*100 if d<now.hour else rawdata_today[d]/(now.minute+1)*100 for d in range(len(rawdata_today))]

# calculate mean productivity for each hour in stats
data_stats = [[] for i in range(24)]
N = 0
for r in rawdata_stats["rows"]:
	time = datetime.datetime.strptime(r[0], "%Y-%m-%dT%H:%M:%S")
	if r[1]>0 and time.weekday()<=4:
		#print(time, r[-1])
		data_stats[time.hour].append(r[-1])
#print(data_stats)
data_mean = [sum(data_stats[h])/len(data_stats[h])/60*100 if len(data_stats[h])>0 else 0 for h in range(24)]

# window settings
margin = 5

# graph settings
left_offset = 35
right_offset = 0
max_bar_height = 200
bottom_offset = 25
top_offset = 35

# bar settings
bar_width = 20
bar_gap = 10

# window settings
c_height = max_bar_height + bottom_offset + top_offset
c_width = (bar_width + bar_gap) * max((now.hour-cfg["app"]["start_hour"]+1),6) + left_offset + right_offset

# define coordinate zeros and units
x_zero = left_offset
y_zero = top_offset+max_bar_height
x_unit = bar_width + bar_gap
y_unit = max_bar_height/100

def xc(x):
	return x_zero+x_unit*x
def yc(y):
	return y_zero-y_unit*y

# quit if focus is lost
def on_focus_out(event):
	window.quit()

# get desired window location
xrandr_str = subprocess.run(['xrandr | grep primary'], stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8')
xrandr_geo = xrandr_str.split(" ")[3]
m = re.match("([0-9]+)x([0-9]+)\\+([0-9]+)\\+([0-9]+)", xrandr_geo)
scr_width = int(m[1])
scr_height = int(m[2])
scr_offset_left= int(m[3])
scr_offset_top= int(m[4])
w_pos_x = (scr_width+scr_offset_left)*0.95-c_width
w_pos_y = (scr_height+scr_offset_top)*0.95-c_height

window = Tk()
window.bind("<FocusOut>", on_focus_out)
window.title("")
window.geometry("+%d+%d" % (w_pos_x, w_pos_y))

bold_font = font.Font(size=9, weight="bold")
normal_font = font.Font(size=9)

c = Canvas(window, width=c_width, height=c_height, bg=cfg["colors"]["bg"])
c.pack()

# draw y-axis and grid
hours_str = str(round(total_today // 60)) + "h "
min_str = str(round(total_today % 60)) + "min"
total_str = "Productive time today: "
if hours_str!="0h ":
	total_str += hours_str
total_str += min_str
c.create_text(margin, margin, anchor="nw", text=total_str, fill=cfg["colors"]["text"])

for y in range(0,101,20):
	pos = top_offset + (max_bar_height - (y/100 * max_bar_height))
	c.create_text(margin, pos, anchor="w", text=str(y), font=normal_font, fill=cfg["colors"]["text"])
	c.create_line(xc(0), yc(y), c_width-right_offset, yc(y), dash=(5, 1), fill=cfg["colors"]["text"])

# draw bars and x-axis
for t, y in enumerate(data_today):
	if t >= cfg["app"]["start_hour"] and  t <= now.hour:
		x = t - cfg["app"]["start_hour"]
		# coordinates of each bar
		x0 = xc(x)
		x1 = xc(x) + bar_width
		y0 = yc(y) 
		y1 = yc(0)
		#top_offset + max_bar_height
		# Draw the bar
		if y==0:
			color = "grey"
		elif y<cfg["goals"][t]/2:
			color = cfg["colors"]["bad"]
		elif y<cfg["goals"][t]:
			color = cfg["colors"]["medium"]
		else:
			color = cfg["colors"]["success"]
		
		# bar and label
		c.create_rectangle(x0, y0, x1, y1, fill=color, outline=color)
		c.create_text(xc(x)+bar_width/2, yc(0)+margin, anchor="n", text=str(t), font=normal_font, fill=cfg["colors"]["text"])
		
		# goal and avg.
		if cfg["goals"][t]>0:
			c.create_rectangle(x0-2, yc(cfg["goals"][t])-2, x1+2, yc(cfg["goals"][t])+2, fill=cfg["colors"]["goal"])
		if data_mean[t]>0:
			c.create_rectangle(x0-2, yc(data_mean[t])-2, x1+2, yc(data_mean[t])+2, fill=cfg["colors"]["avg"])
		

#g_plot_line(c, range(now.hour-8), data_mean[plot_start:now.hour+1])

# draw goals

window.mainloop()