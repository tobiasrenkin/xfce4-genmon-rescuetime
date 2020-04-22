#!/usr/bin/env python3
from tkinter import font
from tkinter import *
import datetime
import json
import sys, os

sdir = os.getenv("HOME")+"/.config/xfce4-genmon-rescuetime"

# load produvtivity data
with open(sdir+"/cache", "r") as f:
	rawdata = json.loads(f.read())

now = datetime.datetime.now()
prodtime_hours = rawdata[now.hour-4:now.hour+1]
data = []
for t,d in enumerate(prodtime_hours):
	if t<len(prodtime_hours)-1:
		data.append(d/60*100)
	else:
		data.append(d/now.minute*100)

# draw gui etc.
def on_focus_out(event):
	window.quit()

# window settings
margin = 5

# graph settings
bar_width = 20
bar_gap = 10
left_offset = 30+margin
right_offset = 0+margin
max_bar_height = 200
bottom_offset = 20+margin
top_offset = 30+margin

c_height = max_bar_height + bottom_offset + top_offset
c_width = (bar_width + bar_gap) * len(data) + left_offset + right_offset

window = Tk()
#window.after(3000, lambda: window.destroy())
window.bind("<FocusOut>", on_focus_out)
window.bind("<Leave>", on_focus_out)
window.wm_attributes('-type', 'splash');

pnt_x = window.winfo_pointerx() - window.winfo_rootx()
pnt_y = window.winfo_pointery() - window.winfo_rooty()
w_pos_x = pnt_x-c_width
w_pos_y = pnt_y
window.geometry("+%d+%d" % (w_pos_x, w_pos_y))

c = Canvas(window, width=c_width, height=c_height, bg='whitesmoke')
c.pack()

bold_font = font.Font(size=9, weight="bold")
normal_font = font.Font(size=9)
# draw y-axis and grid
c.create_text(c_width/2, margin, anchor=N, text="Productivity")

for y in range(0,101,20):
	pos = top_offset + (max_bar_height - (y/100 * max_bar_height))
	c.create_text(margin, pos, anchor=W, text=str(y), font=normal_font)
	c.create_line(left_offset, pos, c_width-right_offset, pos, dash=(5, 1))

# draw bars and x-axis
for x, y in enumerate(data):
	# coordinates of each bar
	# left coordinate (from right)
	x0 = left_offset + x*(bar_width+bar_gap)
	# top coordinate (from top)
	y0 = top_offset + (max_bar_height - (y/100 * max_bar_height))
	# right coordinates (from right)
	x1 = x0+bar_width
	# bottom coordinates (from top)
	y1 = top_offset + max_bar_height
	# Draw the bar
	if y==0:
		color="grey"
	elif y<33:
		color="red"
	elif y<66:
		color="yellow"
	else:
		color = "green"

	c.create_rectangle(x0, y0, x1, y1, fill=color)
	# Put the y value above the bar
	# create text
	c.create_text(x0 + bar_width/2, c_height, anchor=S, text=str(round(now.hour-(4-x))), font=normal_font)
window.mainloop()

