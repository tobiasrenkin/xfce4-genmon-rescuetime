# About

This script provides a Rescuetime applet for xfce4 panels. The applet displays your current and daily productivity in the panel. On click, it provides some additional statistics about daily productivity.

![](screenshot.png | width=100)

# Setup

1. Install xfce4-genmon-plugin
2. Add generic monitor instance to your panel
3. Clone repository, make sure app.py and chart.py are executable
4. Create Rescuetime API key here: https://www.rescuetime.com/anapi/manage
5. Point generic monitor instance to ./app.py
6. Enter API key when prompted

# Configuration

The configuration is stored in json format in ~/.config/xfce4-genmon-rescuetime/settings.


__Note:__ The premium version of Rescuetime updates user data every three minutes, while the free version updates only every 30 minutes. As a result, current productivity will not always be up-to-date for users with a free Rescuetime account.
