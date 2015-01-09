X-Plane Plugins
======

Performance Info (PI_perf.py)
======
Calculates performance info based on the POH (or best available info) for certain planes. Data shown:

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

Possible future info:

<ul><li>Max cruise speed</li></ul>

Aircraft currently available:

<ul><li>PC-12</li>
<li>B737-800</li></ul>

In work:

<ul><li>B1900D</li>
<li>CL300</li></ul>

There is also a function for setting the autopilot if a destination is set in the FMS. If on the ground, this function will set climb rate, cruise altitude and initial heading based on the distance and direction of the destination. If in the air, the function will set descent rate and altitude based on the destination airport elevation. Different planes have different values for these.

XFSE Damage (PI_xdmg.py)
======
Shows the damage that the FSE plugin would calculate (good for testing new code). Automatically reduces mixture above 1000 feet to prevent damage, and warns if taking off without a flight started. A function is also in work to automatically run the steps for finishing the flight.

Engine Info (PI_enginfo.py)
======
Shows some info about engine 1 on the aircraft. Helpful for getting info for coding plugins.

Altimeter Helper (PI_altimeterhelper.py)
======
Simple plugin for X-Plane that shows the altimeter setting each time it is changed, automatically switches between local and standard pressure at transition altitude, and has a command to set the correct altimeter.

Auto Throttle (PI_pcat.py)
======
Simple throttle controller that uses a PID feedback loop to keep the specified airspeed. Currently working on tuning gains for the PC-12, other aircraft will be tuned in later.
