import os
import sys
from math import *
from urllib import urlopen
import urllib2
from httplib import *
from xml.dom import minidom
from XPLMDisplay import *
from XPLMGraphics import *
from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMMenus import *
from XPWidgets import *
from XPStandardWidgets import *

#include <time.h>

class PythonInterface:

	def XPluginStart(self):
		self.Name="OXACARS 1.0"
		self.Sig= "natt.python.oxacars"
		self.Desc="XACARS plugin for the masses"
		self.VERSION="1.0"
		
		Item = XPLMAppendMenuItem(XPLMFindPluginsMenu(), "OXACARS", 0, 1)
		self.MenuHandlerCB = self.MenuHandler
		self.Id = XPLMCreateMenu(self, "OXACARS" , XPLMFindPluginsMenu(), Item, self.MenuHandlerCB,	0)
		XPLMAppendMenuItem(self.Id, "Open OXACARS", 1, 1)
		
		self.DrawWindowCB = self.DrawWindowCallback
		self.KeyCB = self.KeyCallback
		self.MouseClickCB = self.MouseClickCallback
		self.WindowId = XPLMCreateWindow(self, 50, 600, 300, 400, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)

		self.gWidget = 0
		self.sWidget = 0
		
		self.dist_trav_ref = XPLMFindDataRef("sim/flightmodel/controls/dist")  # float 660+ yes meters Distance Traveled
		self.eng_run_ref = XPLMFindDataRef("sim/flightmodel/engine/ENGN_running")  # int[8] boolean
		self.en2_ref = XPLMFindDataRef("sim/flightmodel/engine/ENGN_N2_")  # float[8] 750+ yes percent N2 speed as percent of max (per engine)
		self.en1_ref = XPLMFindDataRef("sim/flightmodel/engine/ENGN_N1_")  # float[8] 660+ yes percent N1 speed as percent of max (per engine)
		self.wt_tot_ref = XPLMFindDataRef("sim/flightmodel/weight/m_total")  # float kgs
		self.wt_f_tot_ref = XPLMFindDataRef("sim/flightmodel/weight/m_fuel_total")  # float kgs
		#sim/aircraft/weight/acf_m_fuel_tot float 660+ yes lbs Weight of total fuel - appears to be in lbs.
		self.hdgt_ref = XPLMFindDataRef("sim/flightmodel/position/psi")  # float 660+ yes degrees The true heading of the aircraft in degrees from the Z axis
		self.hdgm_ref = XPLMFindDataRef("sim/flightmodel/position/magpsi")  # float 660+ no degrees The magnetic heading of the aircraft.
		self.vvi_ref = XPLMFindDataRef("sim/flightmodel/position/vh_ind_fpm")  # float 740+ yes fpm VVI (vertical velocity in feet per second)
		self.ias_ref = XPLMFindDataRef("sim/flightmodel/position/indicated_airspeed")  # float 660+ yes kias Air speed indicated - this takes into account air density and wind direction
		self.gs_ref = XPLMFindDataRef("sim/flightmodel/position/groundspeed")  # float meters/sec
		self.lat_ref = XPLMFindDataRef("sim/flightmodel/position/latitude")  # double degrees
		self.lon_ref = XPLMFindDataRef("sim/flightmodel/position/longitude")  # double degrees
		self.alt_ref = XPLMFindDataRef("sim/flightmodel/position/elevation")  # double meters
		self.pbrake_ref = XPLMFindDataRef("sim/flightmodel/controls/parkbrake")  #float 0-1
		self.geardep_ref = XPLMFindDataRef("sim/aircraft/parts/acf_gear_deploy")  # float[10] 660+ yes ??? landing gear deployment, 0.0->1.0
		self.f_axil_ref = XPLMFindDataRef("sim/flightmodel/forces/faxil_gear")  # float 660+ no Newtons Gear/ground forces - downward
		self.f_side_ref = XPLMFindDataRef("sim/flightmodel/forces/fside_gear")  # float 660+ no Newtons Gear/ground forces - downward
		self.f_norm_ref = XPLMFindDataRef("sim/flightmodel/forces/fnrml_gear")  # float 660+ no Newtons Gear/ground forces - downward
		self.net_ref = XPLMFindDataRef("sim/network/misc/network_time_sec")  # float
		self.wndh_ref = XPLMFindDataRef("sim/weather/wind_direction_degt")  # float 660+ no [0-359) The effective direction of the wind at the plane's location.
		self.wndk_ref = XPLMFindDataRef("sim/weather/wind_speed_kt")  # float 660+ no kts >= 0 The effective speed of the wind at the plane's location.
		self.t_amb_ref = XPLMFindDataRef("sim/weather/temperature_ambient_c")  # float 660+ no degrees C The air temperature outside the aircraft (at altitude).
		self.t_le_ref = XPLMFindDataRef("sim/weather/temperature_le_c")  # float 660+ no degrees C The air temperature at the leading edge of the wings in degrees C.
		self.tailnum_ref = XPLMFindDataRef("sim/aircraft/view/acf_tailnum")  # byte[40] 660+ yes string Tail number
		self.num_eng_ref = XPLMFindDataRef("sim/aircraft/engine/acf_num_engines")  # 660+ yes
		self.sim_speed_ref = XPLMFindDataRef("sim/time/sim_speed")  # 860+ yes ratio This is the multiplier for real-time...1 = realtme, 2 = 2x, 0 = paused, etc.
		self.grd_speed_ref = XPLMFindDataRef("sim/time/ground_speed")  # 860+ yes ratio This is the multiplier on ground speed, for faster travel via double-distance
	
		return self.Name, self.Sig, self.Desc
	
	def XPluginStop(self):

		# Unregister the callback
		XPLMUnregisterFlightLoopCallback(self, self.MyFlightLoopCallback, 0)
		if gWidget == 1:
			XPDestroyWidget(self, self.OXWidget, 1)
			gWidget = 0
		if sWidget == 1:
			XPDestroyWidget(self, self.SettingsWidget, 1)
			sWidget = 0

		pass

	def XPluginEnable(self):
		return 1


	def XPluginDisable(self):
		pass


	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass

	def MenuHandler(self, inMenuRef, inItemRef):
		# If menu selected create our widget dialog
		if (inItemRef == 1):
			if (self.MenuItem1 == 0):
				self.CreateWidget(221, 640, 480, 490)
				self.MenuItem1 = 1
			else:
				if(not XPIsWidgetVisible(self.Widget)):
					XPShowWidget(self.Widget)

	def OXpost(self, query):
		stuff = urlopen('http:#www.fseconomy.net:81/fsagentx?md5sum='+query).read()
		stuff = stuff.replace('&',' and ')
		dom = minidom.parseString(stuff)
		return dom
		
	def isAllEngineStopped(self):
		_allenginestopped = True
		try:
			for ienga in range(self.NumberOfEngines):
				if self.ACEngine[ienga].isEngRun() > 0:
					_allenginestopped = False
		except Exception:
			_allenginestopped = True

		return _allenginestopped

	def chkBrk(self,h,b):
		if h == 1:
			return True
		if h == 0 and b < float(1.0):
			return True
		
		return False

	def CreateWidget(self, x, y, w, h):
		Index

		x2 = x + w
		y2 = y - h

		# Create the Main Widget window.
			self.OXWidget = XPCreateWidget(x, y, x2, y2,
				1, # Visible
				"OXACARS", # desc
				1, # root
				0, # no container
				xpWidgetClass_MainWindow)

		# Add Close Box to the Main Widget
			XPSetWidgetProperty(self, self.OXWidget, xpProperty_MainWindowHasCloseBoxes, 1)

		# Add widgets and stuff
			FltNoCap = XPCreateWidget(x+20, y-40, x+80, y-60,
				1, "Flight No.", 0, self.OXWidget,
				xpWidgetClass_Caption)

			self.FltNoText = XPCreateWidget(x+100, y-40, x+180, y-60,
				1, "", 0, self.OXWidget,
				xpWidgetClass_TextField)
			XPSetWidgetProperty(self, FltNoText, xpProperty_TextFieldType, xpTextEntryField)

			ACARSInfoButton = XPCreateWidget(x+200, y-40, x+300, y-60,
				1, "ACARS Info", 0, self.OXWidget,
				xpWidgetClass_Button)
			XPSetWidgetProperty(self, ACARSInfoButton, xpProperty_ButtonType, xpPushButton)

			SettingsButton = XPCreateWidget(x+320, y-40, x+420, y-60,
				1, "Settings", 0, self.OXWidget,
				xpWidgetClass_Button)
			XPSetWidgetProperty(self, SettingsButton, xpProperty_ButtonType, xpPushButton)

			DepCap = XPCreateWidget(x+20, y-80, x+50, y-100,
				1, "Dep", 0, self.OXWidget,
				xpWidgetClass_Caption)

			self.DepText = XPCreateWidget(x+60, y-80, x+120, y-100,
				1, "", 0, self.OXWidget,
				xpWidgetClass_TextField)
			XPSetWidgetProperty(self, DepText, xpProperty_TextFieldType, xpTextEntryField)

			ArrCap = XPCreateWidget(x+150, y-80, x+180, y-100,
				1, "Arr", 0, self.OXWidget,
				xpWidgetClass_Caption)

			self.ArrText = XPCreateWidget(x+180, y-80, x+240, y-100,
				1, "", 0, self.OXWidget,
				xpWidgetClass_TextField)
			XPSetWidgetProperty(self, ArrText, xpProperty_TextFieldType, xpTextEntryField)

			AltnCap = XPCreateWidget(x+300, y-80, x+330, y-100,
				1, "Altn", 0, self.OXWidget,
				xpWidgetClass_Caption)

			self.AltnText = XPCreateWidget(x+340, y-80, x+400, y-100,
				1, "", 0, self.OXWidget,
				xpWidgetClass_TextField)
			XPSetWidgetProperty(self, AltnText, xpProperty_TextFieldType, xpTextEntryField)

			RtCap = XPCreateWidget(x+20, y-120, x+60, y-140,
				1, "Route", 0, self.OXWidget,
				xpWidgetClass_Caption)

			self.RtText = XPCreateWidget(x+70, y-120, x+430, y-140,
				1, "", 0, self.OXWidget,
				xpWidgetClass_TextField)
			XPSetWidgetProperty(self, RtText, xpProperty_TextFieldType, xpTextEntryField)

			PaxCap = XPCreateWidget(x+20, y-160, x+60, y-180,
				1, "Pax", 0, self.OXWidget,
				xpWidgetClass_Caption)

			self.PaxText = XPCreateWidget(x+70, y-160, x+120, y-180,
				1, "", 0, self.OXWidget,
				xpWidgetClass_TextField)
			XPSetWidgetProperty(self, PaxText, xpProperty_TextFieldType, xpTextEntryField)

			PlanCap = XPCreateWidget(x+150, y-160, x+180, y-180,
				1, "Plan", 0, self.OXWidget,
				xpWidgetClass_Caption)

			self.PlanText = XPCreateWidget(x+190, y-160, x+240, y-180,
				1, "", 0, self.OXWidget,
				xpWidgetClass_TextField)
			XPSetWidgetProperty(self, PlanText, xpProperty_TextFieldType, xpTextEntryField)

			TypeCap = XPCreateWidget(x+280, y-160, x+310, y-180,
				1, "Type", 0, self.OXWidget,
				xpWidgetClass_Caption)

			self.TypeText = XPCreateWidget(x+320, y-160, x+370, y-180,
				1, "", 0, self.OXWidget,
				xpWidgetClass_TextField)
			XPSetWidgetProperty(self, TypeText, xpProperty_TextFieldType, xpTextEntryField)

			CargoCap = XPCreateWidget(x+20, y-200, x+60, y-220,
				1, "Cargo", 0, self.OXWidget,
				xpWidgetClass_Caption)

			self.CargoText = XPCreateWidget(x+70, y-200, x+120, y-220,
				1, "", 0, self.OXWidget,
				xpWidgetClass_TextField)
			XPSetWidgetProperty(self, CargoText, xpProperty_TextFieldType, xpTextEntryField)

			FLCap = XPCreateWidget(x+150, y-200, x+180, y-220,
				1, "Alt", 0, self.OXWidget,
				xpWidgetClass_Caption)

			self.FLText = XPCreateWidget(x+190, y-200, x+260, y-220,
				1, "", 0, self.OXWidget,
				xpWidgetClass_TextField)
			XPSetWidgetProperty(self, FLText, xpProperty_TextFieldType, xpTextEntryField)

			StartButton = XPCreateWidget(x+280, y-200, x+320, y-220,
				1, "Start", 0, self.OXWidget,
				xpWidgetClass_Button)
			XPSetWidgetProperty(self, StartButton, xpProperty_ButtonType, xpPushButton)

			DTCap = XPCreateWidget(x+20, y-240, x+40, y-260,
				1, "DT", 0, self.OXWidget,
				xpWidgetClass_Caption)

			DTdisp = XPCreateWidget(x+50, y-240, x+220, y-260,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			ZFWCap = XPCreateWidget(x+250, y-240, x+280, y-260,
				1, "ZFW", 0, self.OXWidget,
				xpWidgetClass_Caption)

			ZFWdisp = XPCreateWidget(x+300, y-240, x+400, y-260,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			BTCap = XPCreateWidget(x+20, y-280, x+40, y-300,
				1, "BT", 0, self.OXWidget,
				xpWidgetClass_Caption)

			BTdisp = XPCreateWidget(x+50, y-280, x+100, y-300,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			FTCap = XPCreateWidget(x+130, y-280, x+150, y-300,
				1, "FT", 0, self.OXWidget,
				xpWidgetClass_Caption)

			FTdisp = XPCreateWidget(x+160, y-280, x+210, y-300,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			TOWCap = XPCreateWidget(x+250, y-280, x+280, y-300,
				1, "TOW", 0, self.OXWidget,
				xpWidgetClass_Caption)

			TOWdisp = XPCreateWidget(x+300, y-280, x+400, y-300,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			BFCap = XPCreateWidget(x+20, y-320, x+40, y-340,
				1, "BF", 0, self.OXWidget,
				xpWidgetClass_Caption)

			BFdisp = XPCreateWidget(x+50, y-320, x+100, y-340,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			FFCap = XPCreateWidget(x+130, y-320, x+150, y-340,
				1, "FF", 0, self.OXWidget,
				xpWidgetClass_Caption)

			FFdisp = XPCreateWidget(x+160, y-320, x+210, y-340,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			LWCap = XPCreateWidget(x+250, y-320, x+280, y-340,
				1, "LW", 0, self.OXWidget,
				xpWidgetClass_Caption)

			LWdisp = XPCreateWidget(x+300, y-320, x+400, y-340,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			OUTCap = XPCreateWidget(x+20, y-360, x+50, y-380,
				1, "OUT", 0, self.OXWidget,
				xpWidgetClass_Caption)

			OUTlatdisp = XPCreateWidget(x+70, y-360, x+150, y-380,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			OUTlondisp = XPCreateWidget(x+180, y-360, x+260, y-380,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			OUTaltdisp = XPCreateWidget(x+290, y-360, x+350, y-380,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			INCap = XPCreateWidget(x+20, y-400, x+50, y-420,
				1, "IN", 0, self.OXWidget,
				xpWidgetClass_Caption)

			INlatdisp = XPCreateWidget(x+70, y-400, x+150, y-420,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			INlondisp = XPCreateWidget(x+180, y-400, x+260, y-420,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			INaltdisp = XPCreateWidget(x+290, y-400, x+350, y-420,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			MAXCap = XPCreateWidget(x+20, y-440, x+80, y-460,
				1, "MAX C/D", 0, self.OXWidget,
				xpWidgetClass_Caption)

			maxCdisp = XPCreateWidget(x+110, y-440, x+140, y-460,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			maxslash = XPCreateWidget(x+150, y-440, x+160, y-460,
				1, "/", 0, self.OXWidget,
				xpWidgetClass_Caption)

			maxDdisp = XPCreateWidget(x+160, y-440, x+190, y-460,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			maxICap = XPCreateWidget(x+220, y-440, x+250, y-460,
				1, "IAS", 0, self.OXWidget,
				xpWidgetClass_Caption)

			maxIdisp = XPCreateWidget(x+260, y-440, x+290, y-460,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			maxGCap = XPCreateWidget(x+310, y-440, x+330, y-460,
				1, "GS", 0, self.OXWidget,
				xpWidgetClass_Caption)

			maxGdisp = XPCreateWidget(x+340, y-440, x+370, y-460,
				1, "", 0, self.OXWidget,
				xpWidgetClass_Caption)

			SendButton = XPCreateWidget(x+20, y-480, x+140, y-500,
				1, "Send", 0, self.OXWidget,
				xpWidgetClass_Button)
			XPSetWidgetProperty(self, SendButton, xpProperty_ButtonType, xpPushButton)

		# Register our widget handler
			XPAddWidgetCallback(self.OXWidget, self.OXHandler)

	def OXHandler(self, inMessage, inWidget,    inParam1, inParam2):
		if (inMessage == xpMessage_CloseButtonPushed):
			print "Client window closed"
			if (self.gWidget == 1):
				XPHideWidget(self.OXWidget)
				return 1

		# Test for a button pressed
		if (inMessage == xpMsg_PushButtonPressed):
			if (inParam1 == (long)ACARSInfoButton):
				# ?DATA1=XACARS|1.1&DATA2=XAC1001
				# ?DATA1=XACARS|2.0&DATA2=pid&DATA3=flightplan&DATA4=pid&DATA5=password
				char Altn[5], Alt[6], Route[256], ACType[5], Plan[4], cargo[7], pax[4]

				print "OXACARS - Assembling query URL..."
				#char * durl = malloc(snprintf(NULL, 0, "%s?DATA1=%s&DATA2=%s", fdurl, DATA1v1, PID) + 1)
				#sprintf(durl, "%s?DATA1=%s&DATA2=%s", fdurl, DATA1v1, PID)

				char * durl = malloc(snprintf(NULL, 0, "DATA1=%s&DATA2=%s&DATA3=flightplan&DATA4=%s&DATA5=%s", DATA1v2, PID, PID, Ppass) + 1)
				sprintf(durl, "DATA1=%s&DATA2=%s&DATA3=flightplan&DATA4=%s&DATA5=%s", DATA1v2, PID, PID, Ppass)

				print "OXACARS - Will attempt to get " + durl
				# http://stackoverflow.com/questions/2577654/curl-put-output-into-variable
				CURL *curl
				CURLcode res
				curl = curl_easy_init()
				if(curl) :
					curl_easy_setopt(curl, CURLOPT_URL, fdurl)
					curl_easy_setopt(curl, CURLOPT_POSTFIELDS, durl)
					curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback_func)
					curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response)
					res = curl_easy_perform(curl)
					if(res != CURLE_OK)
					  fprintf(stderr, "curl_easy_perform() failed: %s\n",
						curl_easy_strerror(res))
					curl_easy_cleanup(curl)
				}

				#http://stackoverflow.com/questions/12789883/parallel-to-phps-explode-in-c-split-char-into-char-using-delimiter But I don't wanna explode...
				print "OXACARS - Now attempting to parse response..."
				char ** fd = NULL
				char * p = strtok (response, "\n")
				int n_spaces = 0, i

				while (p) :
					fd = realloc (fd, sizeof (char*) * ++n_spaces)
					if (fd == NULL):
						exit (-1) #mem allocation fail
					fd[n_spaces-1] = p
					p = strtok (NULL, "\n")

					#realloc for last NULL
				fd = realloc (fd, sizeof (char*) * (n_spaces+1))
				fd[n_spaces] = 0

				strcpy(Dep,fd[1])
				strcpy(Arr, fd[2])
				strcpy(Altn, fd[3])
				#strcpy(Alt, fd[9]) #or not
				strcpy(Route, fd[4])
				strcpy(ACType, fd[8])
				strcpy(Plan, fd[7])
				strcpy(cargo, fd[6])
				strcpy(pax, fd[5])

				# print "OXACARS - Dep: %s Arr: %s Altn: %s\n", Dep, Arr, Altn)
				# print "OXACARS - Route: %s\n", Route)
				# print "OXACARS - Alt: %s Plan: %s Type: %s\n", Alt, Plan, ACType)
				# print "OXACARS - Pax: %s Cargo: %s\n", pax, cargo)

				XPSetWidgetDescriptor(self, self.DepText, Dep)
				XPSetWidgetDescriptor(self, self.ArrText, Arr)
				XPSetWidgetDescriptor(self, self.AltnText, Altn)
				XPSetWidgetDescriptor(self, self.RtText, Route)
				XPSetWidgetDescriptor(self, self.PlanText, Plan)
				XPSetWidgetDescriptor(self, self.TypeText, ACType)
				XPSetWidgetDescriptor(self, self.CargoText, cargo)
				XPSetWidgetDescriptor(self, self.PaxText, pax)

			if (inParam1 == (long)SettingsButton):
				# open settings stuff
				print "OXACARS - You pressed the Settings button..."
				if (sWidget == 0) :
					self.CreateSettingsWidget(100, 712, 600, 662) #left, top, right, bottom.
					sWidget = 1
				else :
					if(!XPIsWidgetVisible(SettingsWidget)):
						XPShowWidget(SettingsWidget)
			if (inParam1 == (long)StartButton) :
				print "OXACARS - Starting OXACARS monitoring..."
				if ( XPLMGetDataf(self.pbrake_ref) < 1 ) :
					print "OXACARS - PARKING BRAKE IS SET"
					return 0
				num_eng = XPLMGetDatai( self.num_eng_ref )
				print "OXACARS - Found " + num_eng + "engines..."
				XPLMGetDatavi(self, self.eng_run_ref, eng_run, 0, num_eng )
				for ( i = 0; i < num_eng; i++ ) :
					if ( eng_run[i] == 1 ) :
						print "OXACARS - SHUT OFF THE ENGINES"
						return 0

				char BEGlat[12], BEGlon[12], tailnumbuf[41]
				char * RouteStr = NULL
				double BEG_lat, BEG_lon, BEG_alt
				float BEG_f, FW, Elev, hdgm, hdgt, wndh, wndk
				char *buf = 0
				void *temp = 0

				print "OXACARS - Gathering flight info..."
				XPLMGetDatab( tailnum_ref, tailnum, 0, 40 )
				# XPLMGetDatab( tailnum_ref, tailnumbuf, 0, 40 )
				# print "OXACARS - Tail number is %d long\n",strlen(tailnumbuf))
				# temp = realloc(tailnum, strlen(tailnumbuf) + 1)
				# if (temp) tailnum = temp
				# strcpy( tailnum, tailnumbuf )

				XPGetWidgetDescriptor(self, self.PaxText, pax, 3)
				XPGetWidgetDescriptor(self, self.FltNoText, fltno, 8)
				XPGetWidgetDescriptor(self, self.TypeText, Type, 4)
				XPGetWidgetDescriptor(self, self.FLText, Alt, 5)
				XPGetWidgetDescriptor(self, self.PlanText, Plan, 3)
				XPGetWidgetDescriptor(self, self.DepText, Dep, 4)
				XPGetWidgetDescriptor(self, self.ArrText, Arr, 4)
				XPGetWidgetDescriptor(self, self.AltnText, Altn, 4)
				XPGetWidgetDescriptor(self, self.CargoText, cargo, 6)
				XPGetWidgetDescriptor(self, self.RtText, Route, 255)

				RouteStr = str_replace( Route, " ", "~" )

				hdgm = XPLMGetDataf(self.hdgm_ref)
				wndh = XPLMGetDataf(self.wndh_ref)
				wndk = XPLMGetDataf(self.wndk_ref)
				self.BEG_lat = XPLMGetDatad(self.lat_ref) # N/Sxx xx.xxxx
				self.BEG_lon = XPLMGetDatad(self.lon_ref) #http://data.x-plane.com/designers.html#Hint_LatLonFormat
				self.BEG_alt = XPLMGetDatad(self.alt_ref)
				self.BEG_f = XPLMGetDataf(self.wt_f_tot_ref)
				strcpy(self.BEGlat, degdm(BEG_lat, 0))
				strcpy(self.BEGlon, degdm(BEG_lon, 1))

				FW = self.BEG_f * kglb
				Elev = self.BEG_alt * mft
				#DATA1=XACARS|2.0&DATA2=BEGINFLIGHT&DATA3=pid||pid|73W||KMDW~PEKUE~OBENE~MONNY~IANNA~FSD~J16~BIL~J136~MLP~GLASR9~KSEA|N34 34.2313 E69 11.6551|5866||||107|180|15414|0|IFR|0|password|&DATA4=

				char * surl = malloc(snprintf(NULL, 0, "DATA1=%s&DATA2=BEGINFLIGHT&DATA3=%s||%s|%s||%s~%s~%s|%s %s|%.0f||||%.0f|%.0f|%.0f%.0f|0|%s|0|%s|&DATA4=", DATA1v2, uname, fltno, Type, Dep, RouteStr, Arr, BEGlat, BEGlon, Elev, FW, hdgm, wndh, wndk, Plan, Ppass) + 1)
				sprintf(surl, "DATA1=%s&DATA2=BEGINFLIGHT&DATA3=%s||%s|%s||%s~%s~%s|%s %s|%.0f||||%.0f|%.0f|%.0f%.0f|0|%s|0|%s|&DATA4=", DATA1v2, uname, fltno, Type, Dep, RouteStr, Arr, BEGlat, BEGlon, Elev, FW, hdgm, wndh, wndk, Plan, Ppass)

				print "OXACARS - Will send url " + surl
				# CURL *curl
				# CURLcode res
				# curl = curl_easy_init()
				# if(curl) :
					# curl_easy_setopt(curl, CURLOPT_URL, acarsurl)
					# curl_easy_setopt(curl, CURLOPT_POSTFIELDS, surl)
					# res = curl_easy_perform(curl)
					# if(res != CURLE_OK)
					  # fprintf(stderr, "curl_easy_perform() failed: %s\n",
						# curl_easy_strerror(res))
					# curl_easy_cleanup(curl)
				# }

				XPSetWidgetProperty(self, self.PaxText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self, self.FltNoText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self, self.TypeText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self, self.FLText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self, self.PlanText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self, self.DepText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self, self.ArrText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self, self.AltnText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self, self.CargoText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self, self.RtText, xpProperty_TextFieldType, xpTextTranslucent)

				XPLMRegisterFlightLoopCallback(self,
					MyFlightLoopCallback,
					1.0,
					0)
				print "OXACARS - Registered loop callback, startup complete"

			if (inParam1 == (long)SendButton):
				XPLMUnregisterFlightLoopCallback(self, self.MyFlightLoopCallback, 0)
				char online[8]

				# print "OXACARS - Defining flight variables..."
				# time_t OUT_time = 1394204887
				# time_t IN_time = 1394214827
				# time_t OFF_time = 1394204987
				# time_t ON_time = 1394214887
				# float OUT_f = 10000.0
				# float OFF_f = 9500.0
				# float OFF_w = 150000.0
				# float ON_f = 2200.0
				# float ON_w = 142700.0
				# float IN_f = 2100.0
				# double OUT_lat = 45.43210 # N/Sxx xx.xxxx N/E > 0, S/W < 0
				# double OUT_lon = -95.43210 # E/Wxx xx.xxxx
				# double OUT_alt = 135.0
				# double IN_lat = 44.43210
				# double IN_lon = -90.43210
				# double IN_alt = 583.1
				# float maxC = 4000.0
				# float maxD = 3000.0
				# float maxI = 288.0
				# float maxG = 100.0

				#http://www.xacars.net/index.php?Client-Server-Protocol
				print "Online seconds: " + self.IN_net_s
				# if ( IN_net_s > (IN_time - OUT_time) ) : # or...?
				# strcpy(online, "VATSIM")
				# } else :
				online = "OFFLINE"
				# }

				# XPGetWidgetDescriptor( TypeText, Type, 4)
				# XPGetWidgetDescriptor( FLText, Alt, 5)
				# XPGetWidgetDescriptor( PlanText, Plan, 3)
				# XPGetWidgetDescriptor( AltnText, Altn, 4)
				# XPGetWidgetDescriptor( PaxText, pax, 3)
				# XPGetWidgetDescriptor( CargoText, cargo, 6)

				print "OXACARS - This is a lot of information..."
				char * DATA2 = malloc(snprintf(NULL, 0, "%s~%s~%s~%s~%s~%s~%s~%s~%s~%s~%s~%s~%.0f~%.0f~%s~%s~%s~%lu~%lu~%lu~%lu~%.0f~%.0f~%.0f~%s~%s~%.0f~%s~%s~%.0f~%.0f~%.0f~%.0f~%.0f", PID, Ppass, fltno, Type, Alt, Plan, Dep, Arr, Altn, DT, blocktime, flighttime, BF, FF, pax, cargo, online, OUT_time, OFF_time, ON_time, IN_time, ZFW, TOW, LW, OUTlat, OUTlon, OUTalt, INlat, INlon, INalt, maxC, -maxD, maxI, maxG) + 1)
				sprintf(DATA2, "%s~%s~%s~%s~%s~%s~%s~%s~%s~%s~%s~%s~%.0f~%.0f~%s~%s~%s~%lu~%lu~%lu~%lu~%.0f~%.0f~%.0f~%s~%s~%.0f~%s~%s~%.0f~%.0f~%.0f~%.0f~%.0f", PID, Ppass, fltno, Type, Alt, Plan, Dep, Arr, Altn, DT, blocktime, flighttime, BF, FF, pax, cargo, online, OUT_time, OFF_time, ON_time, IN_time, ZFW, TOW, LW, OUTlat, OUTlon, OUTalt, INlat, INlon, INalt, maxC, -maxD, maxI, maxG)

				char * purl = malloc(snprintf(NULL, 0, "DATA1=%s&DATA2=%s", DATA1v1, DATA2) + 1)
				sprintf(purl, "DATA1=%s&DATA2=%s", DATA1v1, DATA2)

				print "OXACARS - Will send url %s\n", purl)
				# CURL *curl
				# CURLcode res
				# curl = curl_easy_init()
				# if(curl) :
					# curl_easy_setopt(curl, CURLOPT_URL, pirepurl)
					# (curl, CURLOPT_POSTFIELDS, purl)
					# res = curl_easy_perform(curl)
					# if(res != CURLE_OK)
					  # fprintf(stderr, "curl_easy_perform() failed: %s\n",
						# curl_easy_strerror(res))
					# curl_easy_cleanup(curl)
				# }
