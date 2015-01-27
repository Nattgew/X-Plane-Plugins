X-Plane Plugins
======

Performance Info (PI_perf.py)
======
Calculates performance info based on the POH for certain planes. Data shown:

<ul><li>Descent profile</li>
<li>Top of descent distance from destination (working on this)</li>
<li>Takeoff distance</li>
<li>Landing distance</li>
<li>Landing reference speed</li>
<li>Takeoff rotation speed</li>
<li>Cruise climb speed</li>
<li>Max/Optimum flight level (B738)</li>
<li>Best cruise speed</li>
<li>Max cruise power</li></ul>

The following are shown regardless of aircraft:

<ul><li>Density altitude</li>
<li>Temperature</li>
<li>ISA +/-</li>
<li>Gross weight</li>
<li>Distance to next waypoint</li>
<li>Power setting</li></ul>

Possible future info:

<ul><li>Max cruise speed</li></ul>

Aircraft currently available:

<ul><li>PC-12</li>
<li>B737-800</li></ul>

In work:

<ul><li>B1900D</li>
<li>CL300</li></ul>

There is also an autopilot setting function. When a destination is displayed in the FMS, this function will set cruise altitude and initial heading (if gear down) or descent altitude and heading (if gear up) based on the distance, elevation, and direction of the destination. These values are specifically tuned if the aircraft type is recognized.

Controller Mod (PI_cmod.py)
======
This script sets up various commands that can be assigned to keys/buttons. The main usefulness is for toggles that X-Plane doesn't provide, or commands that have different functions depending on a condition, such as what the current airplane is or whether the autopilot is engaged.

Toggles:

<ul><li>Speed brakes</li>
<li>Landing gear and lights (together)</li>
<li>Flaps (down through all settings, then retracted)</li></ul>

Conditionals:

<ul><li>Aileron trim or heading adjust (depending on AP engaged)</li>
<li>Elevator trim or vertical speed adjust (depending on AP engaged)</li>
<li>Look left/right/up/down (depending on 3D or 2D cockpit)</li>
<li>Front view (depending on 2D or 3D cockpit)</li></ul>

Simple:

<ul><li>AP vertical speed +100 and -100 fpm</li></ul>

XFSE Damage (PI_xdmg.py)
======
Shows the damage that the FSE plugin would calculate. Automatically reduces mixture above 1000 feet to prevent damage, and warns if taking off without a flight started. A function is also in work to automatically run the steps for finishing the flight.

Engine Info (PI_enginfo.py)
======
Shows some info about engine 1 on the aircraft. Helpful for getting info for coding plugins.

Altimeter Helper (PI_altimeterhelper.py)
======
Simple plugin for X-Plane that shows the altimeter setting each time it is changed, automatically switches between local and standard pressure at transition altitude, and has a command to set the correct altimeter.

Auto Throttle (PI_pcat.py)
======
Simple throttle controller that uses a PID feedback loop to keep the specified airspeed. Currently working on tuning gains for the PC-12, other aircraft will be tuned in later.
