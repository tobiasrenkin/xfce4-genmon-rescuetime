#!/usr/bin/env python3
from tkinter import *
from tkinter.font import Font, nametofont
from datetime import datetime, timedelta
from statistics import mean
import json
import sys, os
import subprocess
import re

sdir = os.getenv("HOME")+"/.config/xfce4-genmon-rescuetime"
adir = "/".join(sys.path[0].split("/")[:])
now = datetime.now()

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

########################################################################

# load produvtivity data and prepare numbers to plot
with open(sdir+"/cache", "r") as f:
	prod_time_today = json.loads(f.read())
with open(sdir+"/yearlystats", "r") as f:
	rawdata_stats = json.loads(f.read())["rows"]

total_today = sum(prod_time_today)
percent_byhour = [prod_time_today[d]/60*100 if d<now.hour else prod_time_today[d]/(now.minute+1)*100 
	for d in range(len(prod_time_today))]

lists = [[d["min"] for d in rawdata_stats if datetime.strptime(d["time"], "%Y-%m-%dT%H:%M:%S").hour==t and d["prod"]>0] for t in range(24)]
means = [mean(lst) if len(lst)>0 else 0 for lst in lists]

########################################################################

# prepare to draw gui

# window settings
margin = 5

# graph settings
left_offset = 35
right_offset = 0
max_bar_height = 200
bottom_offset = 25
top_offset = 40

# bar settings
bar_width = 20
bar_gap = 10

# calc window size from settings
c_height = max_bar_height + bottom_offset + top_offset
c_width = (bar_width + bar_gap) * max((now.hour-cfg["app"]["start_hour"]+1),7) + left_offset + right_offset

# define coordinate zeros and units from settings
x_zero = left_offset
y_zero = top_offset+max_bar_height
x_unit = bar_width + bar_gap
y_unit = max_bar_height/100

# get window location based on settings
xrandr_str = subprocess.run(['xrandr | grep primary'], stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8')
xrandr_geo = xrandr_str.split(" ")[3]
m = re.match("([0-9]+)x([0-9]+)\\+([0-9]+)\\+([0-9]+)", xrandr_geo)
scr_width = int(m[1])
scr_height = int(m[2])
scr_offset_left= int(m[3])
scr_offset_top= int(m[4])
w_pos_x = (scr_width+scr_offset_left)*0.97-c_width
w_pos_y = (scr_height+scr_offset_top)*0.97-c_height

def xc(x):
	return x_zero+x_unit*x
def yc(y):
	return y_zero-y_unit*y
def on_focus_out(event):
	window.quit()

########################################################################

# draw gui

# start window
window = Tk()

window.bind("<FocusOut>", on_focus_out)
window.title("")
window.geometry("+%d+%d" % (w_pos_x, w_pos_y))

default_font = nametofont("TkDefaultFont")
default_font.configure(size=11, family="Noto Sans Regular")

c = Canvas(window, width=c_width, height=c_height, bg=cfg["colors"]["bg"], highlightthickness=0)
c.pack()

# draw total time text
hours_str = str(round(total_today // 60)) + "h "
min_str = str(round(total_today % 60)) + "min"
total_str = "Total productive time: "
if hours_str!="0h ":
	total_str += hours_str
total_str += min_str
c.create_text(margin, margin, anchor="nw", text=total_str, fill=cfg["colors"]["text"])

# draw y-axis and grid
for y in range(0,101,20):
	pos = top_offset + (max_bar_height - (y/100 * max_bar_height))
	c.create_text(margin, pos, anchor="w", text=str(y), fill=cfg["colors"]["text"])
	c.create_line(xc(0), yc(y), c_width-right_offset, yc(y), dash=(5, 1), fill=cfg["colors"]["text"])

# draw bars and x-axis
for t, y in enumerate(percent_byhour):
	if t >= cfg["app"]["start_hour"] and  t <= now.hour:
		x = t - cfg["app"]["start_hour"]
		
		# bar color
		if y==0:
			color = "grey"
		elif y<cfg["goals"][t]/2:
			color = cfg["colors"]["bad"]
		elif y<cfg["goals"][t]:
			color = cfg["colors"]["medium"]
		else:
			color = cfg["colors"]["success"]
		
		# bar and axis label
		if y>0:
			c.create_rectangle(xc(x), yc(y), xc(x) + bar_width, yc(0), fill=color)
		c.create_text(xc(x)+bar_width/2, yc(0)+margin, anchor="n", text=str(t), fill=cfg["colors"]["text"])
		
		# goal and avg.
		if cfg["goals"][t]>0:
			c.create_rectangle(xc(x)-2, yc(cfg["goals"][t])-2, xc(x)+bar_width+2, yc(cfg["goals"][t])+2, fill=cfg["colors"]["goal"])
		if means[t]>0:
			c.create_rectangle(xc(x)-2, yc(means[t])-2, xc(x)+bar_width+2, yc(means[t])+2, fill=cfg["colors"]["avg"])
		
window.mainloop()