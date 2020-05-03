#!/usr/bin/env python3
from utils import gencfg
from tkinter import *
from tkinter.font import nametofont
from datetime import datetime
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
cfg = gencfg(adir+"/defaultcfg", sdir+"/settings")

########################################################################

# todays data
with open(sdir+"/cache", "r") as f:
	prod_time_today = json.loads(f.read())

total = sum(prod_time_today)
percent_by_hour = [minutes/60*100 if h<now.hour else minutes/(now.minute+1)*100 
	for h, minutes in enumerate(prod_time_today)]

# mean by hour
with open(sdir+"/yearlystats", "r") as f:
	data = json.loads(f.read())

timefmt = "%Y-%m-%dT%H:%M:%S"
data_by_hour = [
	[d["min"] for d in data["rows"]
	if datetime.strptime(d["time"], timefmt).hour==t and datetime.strptime(d["time"], timefmt).weekday()<=4 and d["prod"]>0]
	for t in range(24)]
mean_by_hour = [mean(lst)/60*100 if len(lst)>0 else 0 for lst in data_by_hour]

########################################################################

# prepare to draw gui
gui = cfg["chart"]
clr = cfg["colors"]

# calc window size from settings
c_height = gui["max_bar_height"] + gui["bottom_offset"] + gui["top_offset"]
c_width = (gui["bar_width"] + gui["bar_gap"]) * max((now.hour - cfg["app"]["start_hour"] + 1), 7) + gui["left_offset"] + gui["right_offset"]

# define chart coordinate zeros and units from settings
x_zero = gui["left_offset"]
y_zero = gui["top_offset"] + gui["max_bar_height"]
x_unit = gui["bar_width"] + gui["bar_gap"]
y_unit = gui["max_bar_height"] / 100
def xc(x):
	return x_zero + x_unit * x
def yc(y):
	return y_zero - y_unit * y

# ugly hack: get window location based on xrandr primary monitor
xrandr_str = subprocess.run(['xrandr | grep primary'], stdout=subprocess.PIPE, shell=True).stdout.decode('utf-8')
xrandr_geo = xrandr_str.split(" ")[3]
m = re.match("([0-9]+)x([0-9]+)\\+([0-9]+)\\+([0-9]+)", xrandr_geo)
scr_width = int(m[1])
scr_height = int(m[2])
scr_offset_left= int(m[3])
scr_offset_top= int(m[4])
w_pos_x = (scr_width + scr_offset_left) * 0.97 - c_width
w_pos_y = (scr_height + scr_offset_top) * 0.97 - c_height

def on_focus_out(event):
	window.quit()

########################################################################

# draw gui

# make window
window = Tk()

window.bind("<FocusOut>", on_focus_out)
window.title("")
window.geometry("+%d+%d" % (w_pos_x, w_pos_y))

default_font = nametofont("TkDefaultFont")
default_font.configure(size=11, family="Noto Sans Regular")

c = Canvas(window, width=c_width, height=c_height, bg=clr["bg"], highlightthickness=0)
c.pack()

# draw total time text
time_str = "%.0fh %.0fmin" %  (total//60, total%60) if total>60 else "%.0fmin" % total
c.create_text(gui["margin"], gui["margin"], anchor="nw", text="Total productive time: " + time_str, fill=clr["text"])

# draw horizontal grid and y-labels
for y in range(0, 101, 20):
	pos = gui["top_offset"] + (gui["max_bar_height"] - (y / 100 * gui["max_bar_height"]))
	c.create_text(gui["margin"], pos, anchor="w", text=str(y), fill=clr["text"])
	c.create_line(xc(0), yc(y), c_width - gui["right_offset"], yc(y), dash=(5, 1), fill=clr["text"])

# draw bars and x-lables
for t, y in enumerate(percent_by_hour):
	if t >= cfg["app"]["start_hour"] and t <= now.hour:
		x = t - cfg["app"]["start_hour"]
		
		# bar color
		color = "bad" if y < cfg["goals"][t]/2 else "medium" if y < cfg["goals"][t] else "success"
	
		# bar and axis label
		if y>0:
			c.create_rectangle(xc(x), yc(y), xc(x) + gui["bar_width"], yc(0), fill=clr[color])

		c.create_text(xc(x)+gui["bar_width"]/2, yc(0)+gui["margin"], anchor="n", text=str(t), fill=clr["text"])
		
		# goal and avg.
		if cfg["goals"][t]>0:
			c.create_rectangle(xc(x)-2, yc(cfg["goals"][t])-2, xc(x)+gui["bar_width"]+2, yc(cfg["goals"][t])+2, fill=clr["goal"])
		if mean_by_hour[t]>0:
			c.create_rectangle(xc(x)-2, yc(mean_by_hour[t])-2, xc(x)+gui["bar_width"]+2, yc(mean_by_hour[t])+2, fill=clr["avg"])
		
window.mainloop()