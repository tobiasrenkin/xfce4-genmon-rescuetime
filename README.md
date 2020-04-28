# About

This script provides a Rescuetime applet in xfce4 panels using the generic monitor applet. The applet displays current and daily productivity in the panel. On click, it provides some additional statistics about daily productivity.

![Screenshot](/screenshot.png)

# Setup

1. Install xfce4-genmon-plugin
2. Add generic monitor instance to your panel
3. Clone repository, make sure app.py and chart.py are executable
4. Create Rescuetime API key here: https://www.rescuetime.com/anapi/manage
5. Point generic monitor instance to app.py
6. Enter API key when prompted

# Configuration

The configuration is stored in json format in ~/.config/settings.
