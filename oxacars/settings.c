FILE *fr;

fr = fopen ("login.txt", "rt");

if( fr == NULL) perror("Error opening settings file.\n");

fscanf(fr, "%s %s %s %s %s", &PID, &Ppass, &pirepurl, &acarsurl, &fdurl);

fclose(fr);


Example file:

PID
pass
http://www.swavirtual.com/wn/xacars/pirep.php
http://www.swavirtual.com/wn/xacars/liveacars.php
http://www.swavirtual.com/wn/xacars/flightdata.php

//xactesting
//xactestingpass
//http://www.xacars.net/acars/pirep.php
//http://www.xacars.net/acars/liveacars.php
//http://www.xacars.net/acars/flightdata.php
