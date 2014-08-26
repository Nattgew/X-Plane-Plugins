#import os
#import sys
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
from XPWidgetDefs import *
from XPWidgets import *

#include <time.h>

class PythonInterface:

	def stohhmm(self, totalSeconds):
		seconds=totalSeconds % 60
		minutes=(totalSeconds / 60) % 60
		hours=floor(totalSeconds / 3600)
		if seconds > 30:
			minutes+=1
		hhmmstring='%02d:%02d' % (hours, minutes)
		
		return hhmmstring

	def degdm(self, decdegrees, latlon):
		if latlon==0:
			if decdegrees > 0:
				hemi="N"
			else:
				hemi="S"
				decdegrees=fabs(decdegrees)
		elif decdegrees > 0:
			hemi="E"
		else:
			hemi="W"
			decdegrees=fabs(decdegrees)
		degrees=floor(decdegrees)
		decpart=decdegrees - degrees
		minutes=decpart * 60

		locstring=hemi + degrees + " " + str(round(minutes,4))

		return locstring

	def XPluginStart(self):
		self.Name="OXACARS 1.0"
		self.Sig= "natt.python.oxacars"
		self.Desc="XACARS plugin for the 64-bit Linux"
		self.VERSION="1.0"
		
		Item=XPLMAppendMenuItem(XPLMFindPluginsMenu(), "OXACARS py", 0, 1)
		self.MenuHandlerCB=self.MenuHandler
		self.Id=XPLMCreateMenu(self, "OXACARS py" , XPLMFindPluginsMenu(), Item, self.MenuHandlerCB,	0)
		XPLMAppendMenuItem(self.Id, "Open OXACARS", 1, 1)
		
		#self.DrawWindowCB=self.DrawWindowCallback
		#self.KeyCB=self.KeyCallback
		#self.MouseClickCB=self.MouseClickCallback
		self.MyFlightLoopCB=self.MyFlightLoopCallback
		#self.WindowId=XPLMCreateWindow(self, 50, 600, 300, 400, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)

		self.kglb=2.20462262 # conversion constants
		self.mft=3.2808399
		self.mkt=1.94384

		#self.Dep=""
		#self.Arr=""
		#self.Altn=""
		#self.Alt="" #or not
		#self.Route=""
		#self.ACType=""
		#self.Plan=""
		#self.cargo=""
		#self.pax=""
		#self.fltno=""
		#self.Type=""
		#self.Alt=""
		#self.DT=""
		#self.blocktime=""
		#self.flighttime=""
		#self.BF=""
		#self.FF=""
		self.online="OFFLINE"
		#self.OUT_time=""
		#self.OFF_time=""
		#self.ON_time=""
		#self.IN_time=""
		#self.ZFW=""
		#self.TOW=""
		#self.LW=""
		#self.OUTlat=""
		#self.OUTlon=""
		#self.OUTalt=""
		#self.INlat=""
		#self.INlon=""
		#self.INalt=""
		self.maxC=0
		self.maxD=0
		self.maxI=0
		self.maxG=0
		self.tailnum=[]
		self.OUT=0
		self.OFF=0
		self.ON=0
		self.IN=0
		self.delorean=0
		self.capt_yaeger=0
		self.capt_smith=0
		self.MAX_ENG=8
		self.num_eng=0
		self.msgc="A"
		self.msg=1
		self.Counter=1  # loop counter
		self.state=1  # flight state (clb, desc, lvl)
		self.ival=1  # minutes between live reports
		
		self.gWidget=0
		self.sWidget=0
		self.MenuItem1=0
		DATA1v1="XACARS|1.1"
		DATA1v2="XACARS|2.0"
		# default settings
		self.testvalues=1
		default=1
		if default==1:
			pirepurl_def="http://www.xacars.net/acars/pirep.php"
			acarsurl_def="http://www.xacars.net/acars/liveacars.php"
			fdurl_def="http://www.xacars.net/acars/flightdata.php"
			Ppass_def="xactestingpass"
			uname="xactesting"
			PID="XAC1001"
		else:
			pirepurl_def="http://www.swavirtual.com/wn/xacars/pirep.php"
			acarsurl_def="http://www.swavirtual.com/wn/xacars/liveacars.php"
			fdurl_def="http://www.swavirtual.com/wn/xacars/flightdata.php"
			Ppass_def="pass"
			uname="uname"
			PID="pid"
			
		self.pirepurl=pirepurl_def
		self.acarsurl=acarsurl_def
		self.fdurl=fdurl_def
		self.Ppass=Ppass_def
		
		self.dist_trav_ref=XPLMFindDataRef("sim/flightmodel/controls/dist")  # float 660+ yes meters Distance Traveled
		self.eng_run_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_running")  # int[8] boolean
		self.en2_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_N2_")  # float[8] 750+ yes percent N2 speed as percent of max (per engine)
		self.en1_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_N1_")  # float[8] 660+ yes percent N1 speed as percent of max (per engine)
		self.wt_tot_ref=XPLMFindDataRef("sim/flightmodel/weight/m_total")  # float kgs
		self.wt_f_tot_ref=XPLMFindDataRef("sim/flightmodel/weight/m_fuel_total")  # float kgs
		#sim/aircraft/weight/acf_m_fuel_tot float 660+ yes lbs Weight of total fuel - appears to be in lbs.
		self.hdgt_ref=XPLMFindDataRef("sim/flightmodel/position/psi")  # float 660+ yes degrees The true heading of the aircraft in degrees from the Z axis
		self.hdgm_ref=XPLMFindDataRef("sim/flightmodel/position/magpsi")  # float 660+ no degrees The magnetic heading of the aircraft.
		self.vvi_ref=XPLMFindDataRef("sim/flightmodel/position/vh_ind_fpm")  # float 740+ yes fpm VVI (vertical velocity in feet per second)
		self.ias_ref=XPLMFindDataRef("sim/flightmodel/position/indicated_airspeed")  # float 660+ yes kias Air speed indicated - this takes into account air density and wind direction
		self.gs_ref=XPLMFindDataRef("sim/flightmodel/position/groundspeed")  # float meters/sec
		self.lat_ref=XPLMFindDataRef("sim/flightmodel/position/latitude")  # double degrees
		self.lon_ref=XPLMFindDataRef("sim/flightmodel/position/longitude")  # double degrees
		self.alt_ref=XPLMFindDataRef("sim/flightmodel/position/elevation")  # double meters
		self.pbrake_ref=XPLMFindDataRef("sim/flightmodel/controls/parkbrake")  #float 0-1
		self.geardep_ref=XPLMFindDataRef("sim/aircraft/parts/acf_gear_deploy")  # float[10] 660+ yes ??? landing gear deployment, 0.0->1.0
		self.f_axil_ref=XPLMFindDataRef("sim/flightmodel/forces/faxil_gear")  # float 660+ no Newtons Gear/ground forces - downward
		self.f_side_ref=XPLMFindDataRef("sim/flightmodel/forces/fside_gear")  # float 660+ no Newtons Gear/ground forces - downward
		self.f_norm_ref=XPLMFindDataRef("sim/flightmodel/forces/fnrml_gear")  # float 660+ no Newtons Gear/ground forces - downward
		self.wndh_ref=XPLMFindDataRef("sim/weather/wind_direction_degt")  # float 660+ no [0-359) The effective direction of the wind at the plane's location.
		self.wndk_ref=XPLMFindDataRef("sim/weather/wind_speed_kt")  # float 660+ no kts >= 0 The effective speed of the wind at the plane's location.
		self.t_amb_ref=XPLMFindDataRef("sim/weather/temperature_ambient_c")  # float 660+ no degrees C The air temperature outside the aircraft (at altitude).
		self.t_le_ref=XPLMFindDataRef("sim/weather/temperature_le_c")  # float 660+ no degrees C The air temperature at the leading edge of the wings in degrees C.
		self.tailnum_ref=XPLMFindDataRef("sim/aircraft/view/acf_tailnum")  # byte[40] 660+ yes string Tail number
		self.num_eng_ref=XPLMFindDataRef("sim/aircraft/engine/acf_num_engines")  # 660+ yes
		self.sim_speed_ref=XPLMFindDataRef("sim/time/sim_speed")  # 860+ yes ratio This is the multiplier for real-time...1=realtme, 2=2x, 0=paused, etc.
		self.grd_speed_ref=XPLMFindDataRef("sim/time/ground_speed")  # 860+ yes ratio This is the multiplier on ground speed, for faster travel via double-distance
	
		return self.Name, self.Sig, self.Desc
	
	def XPluginStop(self):
		# Unregister the callback
		XPLMUnregisterFlightLoopCallback(self, self.MyFlightLoopCallback, 0)
		if self.gWidget==1:
			XPDestroyWidget(self, self.OXWidget, 1)
			self.gWidget=0
		if self.sWidget==1:
			XPDestroyWidget(self, self.SettingsWidget, 1)
			self.sWidget=0
		pass

	def XPluginEnable(self):
		return 1

	def XPluginDisable(self):
		pass

	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass

	def MenuHandler(self, inMenuRef, inItemRef):
		# If menu selected create our widget dialog
		if inItemRef==1:
			print "OX Menu item selected"
			if self.MenuItem1==0:
				print "OX Creating widget"
				self.CreateWidget(221, 640, 480,525)
				self.MenuItem1=1
			else:
				if not XPIsWidgetVisible(self.Widget):
					print "OX Showing widget"
					XPShowWidget(self.Widget)

	def isAllEngineStopped(self):
		eng_run=[]
		off=0
		XPLMGetDatavi( self.eng_run_ref, eng_run, 0, self.MAX_ENG)
		try:
			for i in range(self.num_eng):
				if eng_run[i]==1:
					off=0
		except Exception:
			off=1
			
		return off

	def chkBrk(self):
		parked=0
		try:
			if XPLMGetDataf(self.pbrake_ref) < float(1.0):
				parked=1
		except Exception:
			parked=0
		
		return parked
	
	def XACARSpost(self, url, query):
		stuff=urlopen(url+query).read()
		stuff=stuff.replace('&',' and ')
		dom=minidom.parseString(stuff)
		return dom

	def CreateWidget(self, x, y, w, h):
		
		x2=x + w
		y2=y - h

	# Create the Main Widget window.
		self.OXWidget=XPCreateWidget(x, y, x2, y2,
			1, # Visible
			"OXACARS py", # desc
			1, # root
			0, # no container
			xpWidgetClass_MainWindow)

	# Add Close Box to the Main Widget
		XPSetWidgetProperty(self.OXWidget, xpProperty_MainWindowHasCloseBoxes, 1)

	# Add widgets and stuff
		FltNoCap=XPCreateWidget(x+20, y-40, x+80, y-60, 1, "Flight No.", 0, self.OXWidget, xpWidgetClass_Caption)

		self.FltNoText=XPCreateWidget(x+100, y-40, x+180, y-60, 1, "", 0, self.OXWidget, xpWidgetClass_TextField)
		XPSetWidgetProperty(self.FltNoText, xpProperty_TextFieldType, xpTextEntryField)

		self.ACARSInfoButton=XPCreateWidget(x+200, y-40, x+300, y-60, 1, "ACARS Info", 0, self.OXWidget, xpWidgetClass_Button)
		XPSetWidgetProperty(self.ACARSInfoButton, xpProperty_ButtonType, xpPushButton)

		self.SettingsButton=XPCreateWidget(x+320, y-40, x+420, y-60, 1, "Settings", 0, self.OXWidget, xpWidgetClass_Button)
		XPSetWidgetProperty(self.SettingsButton, xpProperty_ButtonType, xpPushButton)

		DepCap=XPCreateWidget(x+20, y-80, x+50, y-100, 1, "Dep", 0, self.OXWidget, xpWidgetClass_Caption)

		self.DepText=XPCreateWidget(x+60, y-80, x+120, y-100, 1, "", 0, self.OXWidget, xpWidgetClass_TextField)
		XPSetWidgetProperty(self.DepText, xpProperty_TextFieldType, xpTextEntryField)

		ArrCap=XPCreateWidget(x+150, y-80, x+180, y-100, 1, "Arr", 0, self.OXWidget, xpWidgetClass_Caption)

		self.ArrText=XPCreateWidget(x+180, y-80, x+240, y-100, 1, "", 0, self.OXWidget, xpWidgetClass_TextField)
		XPSetWidgetProperty(self.ArrText, xpProperty_TextFieldType, xpTextEntryField)

		AltnCap=XPCreateWidget(x+300, y-80, x+330, y-100, 1, "Altn", 0, self.OXWidget, xpWidgetClass_Caption)

		self.AltnText=XPCreateWidget(x+340, y-80, x+400, y-100, 1, "", 0, self.OXWidget, xpWidgetClass_TextField)
		XPSetWidgetProperty(self.AltnText, xpProperty_TextFieldType, xpTextEntryField)

		RtCap=XPCreateWidget(x+20, y-120, x+60, y-140, 1, "Route", 0, self.OXWidget, xpWidgetClass_Caption)

		self.RtText=XPCreateWidget(x+70, y-120, x+430, y-140, 1, "", 0, self.OXWidget, xpWidgetClass_TextField)
		XPSetWidgetProperty(self.RtText, xpProperty_TextFieldType, xpTextEntryField)

		PaxCap=XPCreateWidget(x+20, y-160, x+60, y-180, 1, "Pax", 0, self.OXWidget, xpWidgetClass_Caption)

		self.PaxText=XPCreateWidget(x+70, y-160, x+120, y-180, 1, "", 0, self.OXWidget, xpWidgetClass_TextField)
		XPSetWidgetProperty(self.PaxText, xpProperty_TextFieldType, xpTextEntryField)

		PlanCap=XPCreateWidget(x+150, y-160, x+180, y-180, 1, "Plan", 0, self.OXWidget, xpWidgetClass_Caption)

		self.PlanText=XPCreateWidget(x+190, y-160, x+240, y-180, 1, "", 0, self.OXWidget, xpWidgetClass_TextField)
		XPSetWidgetProperty(self.PlanText, xpProperty_TextFieldType, xpTextEntryField)

		TypeCap=XPCreateWidget(x+280, y-160, x+310, y-180, 1, "Type", 0, self.OXWidget, xpWidgetClass_Caption)

		self.TypeText=XPCreateWidget(x+320, y-160, x+370, y-180, 1, "", 0, self.OXWidget, xpWidgetClass_TextField)
		XPSetWidgetProperty(self.TypeText, xpProperty_TextFieldType, xpTextEntryField)

		CargoCap=XPCreateWidget(x+20, y-200, x+60, y-220, 1, "Cargo", 0, self.OXWidget, xpWidgetClass_Caption)

		self.CargoText=XPCreateWidget(x+70, y-200, x+120, y-220, 1, "", 0, self.OXWidget, xpWidgetClass_TextField)
		XPSetWidgetProperty(self.CargoText, xpProperty_TextFieldType, xpTextEntryField)

		FLCap=XPCreateWidget(x+150, y-200, x+180, y-220, 1, "Alt", 0, self.OXWidget, xpWidgetClass_Caption)

		self.FLText=XPCreateWidget(x+190, y-200, x+260, y-220, 1, "", 0, self.OXWidget, xpWidgetClass_TextField)
		XPSetWidgetProperty(self.FLText, xpProperty_TextFieldType, xpTextEntryField)

		self.StartButton=XPCreateWidget(x+280, y-200, x+320, y-220, 1, "Start", 0, self.OXWidget, xpWidgetClass_Button)
		XPSetWidgetProperty(self.StartButton, xpProperty_ButtonType, xpPushButton)

		DTCap=XPCreateWidget(x+20, y-240, x+40, y-260, 1, "DT", 0, self.OXWidget, xpWidgetClass_Caption)

		self.DTdisp=XPCreateWidget(x+50, y-240, x+220, y-260, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		ZFWCap=XPCreateWidget(x+250, y-240, x+280, y-260, 1, "ZFW", 0, self.OXWidget, xpWidgetClass_Caption)

		self.ZFWdisp=XPCreateWidget(x+300, y-240, x+400, y-260, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		BTCap=XPCreateWidget(x+20, y-280, x+40, y-300, 1, "BT", 0, self.OXWidget, xpWidgetClass_Caption)

		self.BTdisp=XPCreateWidget(x+50, y-280, x+100, y-300, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		FTCap=XPCreateWidget(x+130, y-280, x+150, y-300, 1, "FT", 0, self.OXWidget, xpWidgetClass_Caption)

		self.FTdisp=XPCreateWidget(x+160, y-280, x+210, y-300, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		TOWCap=XPCreateWidget(x+250, y-280, x+280, y-300, 1, "TOW", 0, self.OXWidget, xpWidgetClass_Caption)

		self.TOWdisp=XPCreateWidget(x+300, y-280, x+400, y-300, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		BFCap=XPCreateWidget(x+20, y-320, x+40, y-340, 1, "BF", 0, self.OXWidget, xpWidgetClass_Caption)

		self.BFdisp=XPCreateWidget(x+50, y-320, x+100, y-340, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		FFCap=XPCreateWidget(x+130, y-320, x+150, y-340, 1, "FF", 0, self.OXWidget, xpWidgetClass_Caption)

		self.FFdisp=XPCreateWidget(x+160, y-320, x+210, y-340, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		LWCap=XPCreateWidget(x+250, y-320, x+280, y-340, 1, "LW", 0, self.OXWidget, xpWidgetClass_Caption)

		self.LWdisp=XPCreateWidget(x+300, y-320, x+400, y-340, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		OUTCap=XPCreateWidget(x+20, y-360, x+50, y-380, 1, "OUT", 0, self.OXWidget, xpWidgetClass_Caption)

		self.OUTlatdisp=XPCreateWidget(x+70, y-360, x+150, y-380, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		self.OUTlondisp=XPCreateWidget(x+180, y-360, x+260, y-380, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		self.OUTaltdisp=XPCreateWidget(x+290, y-360, x+350, y-380, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		INCap=XPCreateWidget(x+20, y-400, x+50, y-420, 1, "IN", 0, self.OXWidget, xpWidgetClass_Caption)

		self.INlatdisp=XPCreateWidget(x+70, y-400, x+150, y-420, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		self.INlondisp=XPCreateWidget(x+180, y-400, x+260, y-420, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		self.INaltdisp=XPCreateWidget(x+290, y-400, x+350, y-420, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		MAXCap=XPCreateWidget(x+20, y-440, x+80, y-460, 1, "MAX C/D", 0, self.OXWidget, xpWidgetClass_Caption)

		self.maxCdisp=XPCreateWidget(x+110, y-440, x+140, y-460, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		maxslash=XPCreateWidget(x+150, y-440, x+160, y-460, 1, "/", 0, self.OXWidget, xpWidgetClass_Caption)

		self.maxDdisp=XPCreateWidget(x+160, y-440, x+190, y-460, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		maxICap=XPCreateWidget(x+220, y-440, x+250, y-460, 1, "IAS", 0, self.OXWidget, xpWidgetClass_Caption)

		self.maxIdisp=XPCreateWidget(x+260, y-440, x+290, y-460, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		maxGCap=XPCreateWidget(x+310, y-440, x+330, y-460, 1, "GS", 0, self.OXWidget, xpWidgetClass_Caption)

		self.maxGdisp=XPCreateWidget(x+340, y-440, x+370, y-460, 1, "", 0, self.OXWidget, xpWidgetClass_Caption)

		self.SendButton=XPCreateWidget(x+20, y-480, x+140, y-500, 1, "Send", 0, self.OXWidget, xpWidgetClass_Button)
		XPSetWidgetProperty(self.SendButton, xpProperty_ButtonType, xpPushButton)

	# Register our widget handler
		print "OX Widget created"
		self.OXHandlerCB=self.OXHandler
		XPAddWidgetCallback(self, self.OXWidget, self.OXHandlerCB)


	def OXHandler(self, inMessage, inWidget,    inParam1, inParam2):
		if inMessage==xpMessage_CloseButtonPushed:
			print "Client window closed"
			if self.gWidget==1:
				XPHideWidget(self.OXWidget)
				return 1

		# Test for a button pressed
		if inMessage==xpMsg_PushButtonPressed:
			if inParam1==self.ACARSInfoButton:
				# ?DATA1=XACARS|1.1&DATA2=XAC1001
				# ?DATA1=XACARS|2.0&DATA2=pid&DATA3=flightplan&DATA4=pid&DATA5=password

				print "OXACARS - Assembling query URL..."
				#char * durl=malloc(snprintf(NULL, 0, "%s?DATA1=%s&DATA2=%s", fdurl, DATA1v1, PID) + 1)
				#sprintf(durl, "%s?DATA1=%s&DATA2=%s", fdurl, DATA1v1, PID)

				durl="DATA1="+DATA1v2+"&DATA2="+PID+"&DATA3=flightplan&DATA4="+PID+"&DATA5="+Ppass

				print "OXACARS - Will attempt to get " + durl
				
				getInfo=self.XACARSpost(self.fdurl,durl)

				#But I don't wanna explode...
				print "OXACARS - Now attempting to parse response..."

				p=getInfo.split('\n')
				n_spaces=0
				
				fd=[]
				fd[n_spaces-1]=p

				self.Dep=fd[1]
				self.Arr= fd[2]
				self.Altn= fd[3]
				#self.Alt= fd[9] #or not
				self.Route= fd[4]
				self.ACType= fd[8]
				self.Plan= fd[7]
				self.cargo= fd[6]
				self.pax= fd[5]

				# print "OXACARS - Dep: %s Arr: %s Altn: %s\n", Dep, Arr, Altn)
				#print "OXACARS - Route: %s\n", Route)
				#print "OXACARS - Alt: %s Plan: %s Type: %s\n", Alt, Plan, ACType)
				#print "OXACARS - Pax: %s Cargo: %s\n", pax, cargo)

				XPSetWidgetDescriptor(self, self.DepText, self.Dep)
				XPSetWidgetDescriptor(self, self.ArrText, self.Arr)
				XPSetWidgetDescriptor(self, self.AltnText, self.Altn)
				XPSetWidgetDescriptor(self, self.RtText, self.Route)
				XPSetWidgetDescriptor(self, self.PlanText, self.Plan)
				XPSetWidgetDescriptor(self, self.TypeText, self.ACType)
				XPSetWidgetDescriptor(self, self.CargoText, self.cargo)
				XPSetWidgetDescriptor(self, self.PaxText, self.pax)

			if inParam1==self.SettingsButton:
				# open settings stuff
				print "OXACARS - You pressed the Settings button..."
				if sWidget==0:
					self.CreateSettingsWidget(100, 712, 600, 662) #left, top, right, bottom.
					sWidget=1
				else :
					if not XPIsWidgetVisible(self.SettingsWidget):
						XPShowWidget(self.SettingsWidget)
			if inParam1==self.StartButton:
				print "OXACARS - Starting OXACARS monitoring..."
				if self.chkBrk()==1:
					print "OXACARS - PARKING BRAKE IS SET"
					return 0
				self.num_eng=XPLMGetDatai( self.num_eng_ref)
				print "OXACARS - Found " + self.num_eng + "engines..."
				if self.isAllEngineStopped()==0:
					print "OXACARS - SHUT OFF ENGINES"
					return 0

				print "OXACARS - Gathering flight info..."
				XPLMGetDatab( self.tailnum_ref, self.tailnum, 0, 40)

				XPGetWidgetDescriptor(self.PaxText, self.pax, 3)
				XPGetWidgetDescriptor(self.FltNoText, self.fltno, 8)
				XPGetWidgetDescriptor(self.TypeText, self.Type, 4)
				XPGetWidgetDescriptor(self.FLText, self.Alt, 5)
				XPGetWidgetDescriptor(self.PlanText, self.Plan, 3)
				XPGetWidgetDescriptor(self.DepText, self.Dep, 4)
				XPGetWidgetDescriptor(self.ArrText, self.Arr, 4)
				XPGetWidgetDescriptor(self.AltnText, self.Altn, 4)
				XPGetWidgetDescriptor(self.CargoText, self.cargo, 6)
				XPGetWidgetDescriptor(self.RtText, self.Route, 255)

				hdgm=XPLMGetDataf(self.hdgm_ref)
				wndh=XPLMGetDataf(self.wndh_ref)
				wndk=XPLMGetDataf(self.wndk_ref)
				BEG_lat=XPLMGetDatad(self.lat_ref) # N/Sxx xx.xxxx
				BEG_lon=XPLMGetDatad(self.lon_ref) #http://data.x-plane.com/designers.html#Hint_LatLonFormat
				BEG_alt=XPLMGetDatad(self.alt_ref)
				BEG_f=XPLMGetDataf(self.wt_f_tot_ref)
				BEGlat=self.degdm(BEG_lat, 0)
				BEGlon=self.degdm(BEG_lon, 1)
				
				FW=BEG_f * self.kglb
				Elev=BEG_alt * self.mft
				
				self.FOB_prev=FW
				#DATA1=XACARS|2.0&DATA2=BEGINFLIGHT&DATA3=pid||pid|73W||KMDW~PEKUE~OBENE~MONNY~IANNA~FSD~J16~BIL~J136~MLP~GLASR9~KSEA|N34 34.2313 E69 11.6551|5866||||107|180|15414|0|IFR|0|password|&DATA4=
				#surl="DATA1="+self.DATA1v2+"&DATA2=BEGINFLIGHT&DATA3="+self.uname+"||"+self.fltno+"|"+self.Type+"||"+self.Dep+"~"+self.Route.replace(" ", "~")+"~"+self.Arr+"|"+BEGlat+" "+BEGlon+"|"+str(round(Elev))+"||||"+str(round(FW))+"|"+str(round(hdgm))+"|"+str(round(wndh))+str(round(wndk))+"|0|"+self.Plan+"|0|"+self.Ppass+"|&DATA4="
				surl='DATA1=%s&DATA2=BEGINFLIGHT&DATA3=%s||%s|%s||%s~%s~%s|%s %s|%.0f||||%.0f|%.0f|%.0f%.0f|0|%s|0|%s|&DATA4=' % (self.DATA1v2, self.uname, self.fltno, self.Type, self.Dep, self.Route.replace(" ", "~"), self.Arr, BEGlat, BEGlon, Elev, FW, hdgm, wndh, wndk, self.Plan, self.Ppass)
				
				print "OXACARS - Will send url " + surl
				
				getInfo=self.XACARSpost(self.acarsurl,surl)

				XPSetWidgetProperty(self.PaxText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self.FltNoText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self.TypeText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self.FLText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self.PlanText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self.DepText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self.ArrText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self.AltnText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self.CargoText, xpProperty_TextFieldType, xpTextTranslucent)
				XPSetWidgetProperty(self.RtText, xpProperty_TextFieldType, xpTextTranslucent)

				XPLMRegisterFlightLoopCallback(self, self.MyFlightLoopCB, 1.0, 0)
				print "OXACARS - Registered loop callback, startup complete"

			if inParam1==self.SendButton:
				XPLMUnregisterFlightLoopCallback(self, self.MyFlightLoopCB, 0)

				if self.testvalues==1:
					print "OXACARS - Defining flight variables..."
					self.OUT_time=1394204887
					self.IN_time=1394214827
					self.OFF_time=1394204987
					self.ON_time=1394214887
					self.OUT_f=10000.0
					self.OFF_f=9500.0
					self.OFF_w=150000.0
					self.ON_f=2200.0
					self.ON_w=142700.0
					self.IN_f=2100.0
					self.OUT_lat=45.43210 # N/Sxx xx.xxxx N/E > 0, S/W < 0
					self.OUT_lon=-95.43210 # E/Wxx xx.xxxx
					self.OUT_alt=135.0
					self.IN_lat=44.43210
					self.IN_lon=-90.43210
					self.IN_alt=583.1
					self.maxC=4000.0
					self.maxD=3000.0
					self.maxI=288.0
					self.maxG=100.0

				#http://www.xacars.net/index.php?Client-Server-Protocol
				#print "Online seconds: " + self.IN_net_s
				# if ( IN_net_s > (IN_time - OUT_time)): # or...?
				# strcpy(online, "VATSIM")
				# else :
				online="OFFLINE"

				print "OXACARS - This is a lot of information..."
				#DATA2=self.PID+"~"+self.Ppass+"~"+self.fltno+"~"+self.Type+"~"+self.Alt+"~"+self.Plan+"~"+self.Dep+"~"+self.Arr+"~"+self.Altn+"~"+self.DT+"~"+self.blocktime+"~"+self.flighttime+"~"+str(round(self.BF))+"~"+str(round(self.FF))+"~"+self.pax+"~"+self.cargo+"~"+self.online+"~"+str(self.OUT_time)+"~"+str(self.OFF_time)+"~"+str(self.ON_time)+"~"+str(self.IN_time)+"~"+str(round(self.ZFW))+"~"+str(round(self.TOW))+"~"+str(round(self.LW))+"~"+self.OUTlat+"~"+self.OUTlon+"~"+str(round(self.OUTalt))+"~"+self.INlat+"~"+self.INlon"~"+str(round(self.INalt))+"~"+str(round(self.maxC))+"~"+str(round(-self.maxD))+"~"+str(round(self.maxI))+"~"+str(round(self.maxG))
				DATA2='%s~%s~%s~%s~%s~%s~%s~%s~%s~%s~%s~%s~%.0f~%.0f~%s~%s~%s~%lu~%lu~%lu~%lu~%.0f~%.0f~%.0f~%s~%s~%.0f~%s~%s~%.0f~%.0f~%.0f~%.0f~%.0f' % (self.PID, self.Ppass, self.fltno, self.Type, self.Alt, self.Plan, self.Dep, self.Arr, self.Altn, self.DT, self.blocktime, self.flighttime, self.BF, self.FF, self.pax, self.cargo, self.online, self.OUT_time, self.OFF_time, self.ON_time, self.IN_time, self.ZFW, self.TOW, self.LW, self.OUTlat, self.OUTlon, self.OUTalt, self.INlat, self.INlon, self.INalt, self.maxC, -self.maxD, self.maxI, self.maxG)

				purl="DATA1="+DATA1v1+"&DATA2="+DATA2

				print "OXACARS - Will send url "+ purl

				sendInfo=self.XACARSpost(self.pirepurl,purl)

	def MyFlightLoopCallback(self,):
		schg=0
		cold=0
		gear_state=1
		IAS=XPLMGetDataf(self.ias_ref)
		C_now=XPLMGetDataf(self.vvi_ref)
		Alt=XPLMGetDatad(self.alt_ref) * self.mft

		if ( self.OFF==1 and self.ON==0):
			# Track max values
			I_now=XPLMGetDataf(self.ias_ref)
			G_now=XPLMGetDataf(self.gs_ref) * mkt
			if C_now > self.maxC:
				self.maxC=C_now
				XPSetWidgetDescriptor(self.maxCdisp, str(round(maxC)))
			elif C_now < self.maxD:
				self.maxD=C_now;
				XPSetWidgetDescriptor(self.maxDdisp, str(round(maxD)))
			if I_now > self.maxI:
				self.maxI=I_now
				XPSetWidgetDescriptor(self.maxIdisp, str(round(maxI)))
			if G_now > self.maxG:
				self.maxG=G_now
				XPSetWidgetDescriptor(self.maxGdisp, str(round(maxG)))

		iter=self.Counter % ( 60 * self.ival);
		cstate=1
		if iter==0:
			if C_now > 500:
				cstate=0
			elif C_now < -500:
				cstate=2
			else:
				cstate=1
			if cstate != self.state:
				newstate=1
			else:
				newstate=0
			if IN==0:
				schg=10
			#print "Clb: "+str(round(C_now))+" cstate: "+str(cstate)+" state: "+str(state)+" newstate: "+str(newstate)
		
		if ( XPLMGetDatai(self.sim_speed_ref) > 1 or XPLMGetDatai(self.grd_speed_ref) > 1): # looks like we've got a time traveller here, welcome to the future
			self.delorean=1

		if ( Alt < 10000 and IAS > 270): # the FAA will hear about this!
			self.capt_yaeger=1
		
		if ( self.OUT==0 or self.ON==1 and self.IN==0):
			cold=self.isAllEngineStopped()

		if ( self.OUT==1 and self.OFF==0 or self.OFF==1 and self.ON==0):
			geardep=[]
			XPLMGetDatavf( self.geardep_ref, geardep, 0, 10)
			gear_state=0
			for i in range(10):
				if geardep[i]==1:
					gear_state=1
		
		if ( self.OUT==0 and cold==0):
			# print "OXACARS - Detected OUT state..."
			self.OUT=1
			schg=1
		elif ( self.OFF==0 and self.OUT==1 and gear_state==0):
			# print "OXACARS - Detected OFF state..."
			self.OFF=1
			schg=2
		elif ( self.ON==0 and self.OFF==1 and XPLMGetDataf(self.f_norm_ref) != 0 and gear_state==1):
			# print "OXACARS - Detected ON state..."
			self.ON=1
			schg=3
			Lrate=C_then
		elif ( ON==1 and IN==0 and cold==1 and self.chkBrk()==1):
			# print "OXACARS - Detected IN state..."
			self.IN=1
			schg=4

		if schg > 0:
			print "OXACARS - Assembling message..."
			hdgm=XPLMGetDataf(self.hdgm_ref)
			hdgt=XPLMGetDataf(self.hdgt_ref)
			wndh=XPLMGetDataf(self.wndh_ref)
			wndk=XPLMGetDataf(self.wndk_ref)
			OAT=XPLMGetDataf(self.t_amb_ref)
			TAT=XPLMGetDataf(self.t_le_ref)
			FOB=XPLMGetDataf(self.wt_f_tot_ref) * self.kglb
			dist=0
			dist_down=0
			dist_togo=0 # this would be too hard
			n1=[]
			n2=[]
			
			print "States: OUT="+str(self.OUT)+", OFF="+str(self.OFF)+", ON="+str(self.ON)+", IN="+str(IN)
			# print "Gear: Dep: "+str(gear_state)+" F_norm: "+XPLMGetDataf(f_norm_ref)

			if FOB > self.FOB_prev:
				self.capt_smith=1 # hooked up with a tanker, did you?
			
			tstamp=gmtime()
			zdate=strftime("%m/%d/%Y", tstamp)
			ztime=strftime("%H:%MZ", tstamp)

			if self.msg==100:# roll ACARS message index
				self.msgc=chr(ord(self.msgc) + 1)
				self.msg=1
				
			msgstr='M%02d%c' % (self.msg, self.msgc)
			#head="["+zdate+" "+ztime+"]\nACARS Mode: 2 Aircraft Reg: ."+self.tailnum[0]+"\nMsg Label: PR Block ID: 01 Msg No: "+msgstr+"\nFlight ID: "+self.fltno+"\nMessage:\n"
			head='[%s %s]\nACARS Mode: 2 Aircraft Reg: .%s\nMsg Label: PR Block ID: 01 Msg No: M%02d%c\nFlight ID: %s\nMessage:\n' % (zdate, ztime, self.tailnum[0], self.msg, self.msgc, self.fltno)

			#com="/HDG "+str(round(hdgm))+"\n/HDT "+str(round(hdgt))+"\n/IAS "+str(round(IAS))+"\n/WND "+str(round(wndh))+str(round(wndk))+" /OAT "+str(round(OAT))+" /TAT "+str(round(TAT))+"\n"
			com='/HDG %.0f\n/HDT %.0f\n/IAS %.0f\n/WND %.0f%.0f /OAT %.0f /TAT %.0f\n' % (hdgm, hdgt, IAS, wndh, wndk, OAT, TAT)

			lat=XPLMGetDatad(self.lat_ref)
			lon=XPLMGetDatad(self.lon_ref)
			dlat=self.degdm(lat, 0)
			dlon=self.degdm(lon, 1)
			
			POS='POS %s %s\n' % (dlat,dlon)

			if schg==1: # OUT
				TAW=XPLMGetDataf(self.wt_tot_ref) * self.kglb
				self.OUT_f=FOB
				self.ZFW=TAW - self.OUT_f
				self.OUT_time=tstamp
				self.OUTlat=dlat
				self.OUTlon=dlon
				self.OUTalt=Alt
				XPSetWidgetDescriptor(self.ZFWdisp, str(round(self.ZFW)))
				XPSetWidgetDescriptor(self.OUTlatdisp, self.OUTlat)
				XPSetWidgetDescriptor(self.OUTlondisp, self.OUTlon)
				XPSetWidgetDescriptor(self.OUTaltdisp, str(round(OUTalt)))
				print "OXACARS - Building OUT report..."
				#messg="OUT "+ztime+" /ZFW "+str(round(self.ZFW))+" /FOB "+str(round(self.OUT_f))+" /TAW "+str(round(TAW))+"\n/AP "+self.Dep+"\n/"+POS+"/ALT "+str(round(self.OUTalt))+"\n"+com
				messg='OUT %s /ZFW %.0f /FOB %.0f /TAW %.0f\n/AP %s\n/%s/ALT %.0f\n%s' % (ztime, self.ZFW, self.OUT_f, TAW, self.Dep, POS, self.OUTalt, com)
			elif schg==2: # OFF
				self.OFF_f=FOB
				self.TOW=XPLMGetDataf(self.wt_tot_ref) * self.kglb
				XPLMGetDatavf( self.en1_ref, n1, 0, self.num_eng)
				XPLMGetDatavf( self.en2_ref, n2, 0, self.num_eng)
				self.OFF_time=tstamp
				XPSetWidgetDescriptor(self.TOWdisp, str(round(self.TOW)))
				print "OXACARS - Building OFF report..."
				#messg="OFF "+ztime+" /FOB "+str(round(self.OFF_f))+" /TOW "+str(round(self.TOW))+"\n/"+POS+"/ALT "+str(round(Alt))+"\n"+com
				messg='OFF %s /FOB %.0f /TOW %.0f\n/%s/ALT %.0f\n%s' % (ztime, self.OFF_f, self.TOW, POS, Alt, com);
				for i in range(self.num_eng):
					#messg=messg+"/E"+str(i+1)+"N1 "+str(round(n1[i]))+" /E"+str(i+1)+"N2 "+str(round(n2[i]))+" "
					messg='%s/E%dN1 %.0f /E%dN2 %.0f ' % (messg, i+1, n1[i], i+1, n2[i]);
				messg='%s\n\n' % (messg)
			elif schg==3: # ON
				XPLMGetDatavf(self.en1_ref, n1, 0, self.num_eng)
				XPLMGetDatavf(self.en2_ref, n2, 0, self.num_eng)
				self.ON_f=FOB
				self.LW=XPLMGetDataf(self.wt_tot_ref) * self.kglb
				self.ON_time=tstamp
				self.FF=(self.OFF_f - self.ON_f)
				XPSetWidgetDescriptor(self.LWdisp, str(round(self.LW)))
				XPSetWidgetDescriptor(self.FFdisp, str(round(self.FF)))
				print "OXACARS - Building ON report..."
				#messg="ON "+ztime+" /FOB "+str(round(self.ON_f))+" /LAW "+str(round(self.LW))+"\n/AP "+self.Arr+"\n/"+POS+"/ALT "+str(round(Alt))+"\n"+com
				messg='ON %s /FOB %.0f /LAW %.0f\n/AP %s\n/%s/ALT %.0f\n%s' % (ztime, self.ON_f, self.LW, self.Arr, POS, Alt, com)
				for i in range(self.num_eng):
					messg='%s/E%dN1 %.0f /E%dN2 %.0f ' % (messg, i+1, n1[i], i+1, n2[i]);
			elif schg==4: # IN
				#WTF what happened to the IN report?
				self.IN_f=FOB
				self.BF=(self.OUT_f - self.IN_f)
				self.IN_time=tstamp
				self.blocktime=self.stohhmm(self.IN_time - self.OUT_time) # (hh:mm)
				self.flighttime=self.stohhmm(self.ON_time - self.OFF_time) # (hh:mm)
				self.DT=strftime("%d.%m.%Y %H:%M", self.OUT_time) # (dd.mm.yyyy hh:mm)
				XPSetWidgetDescriptor(self.BTdisp, self.blocktime)
				XPSetWidgetDescriptor(self.FTdisp, self.flighttime)
				XPSetWidgetDescriptor(self.DTdisp, self.DT)
				self.INlat=dlat
				self.INlon=dlon
				self.INalt=Alt
				self.IN_net_s=XPLMGetDataf(self.net_ref)
				dist=XPLMGetDataf(self.dist_trav_ref) * self.mft / 6076
				XPSetWidgetDescriptor(self.BFdisp, str(round(self.BF)))
				XPSetWidgetDescriptor(self.INlatdisp, self.INlat)
				XPSetWidgetDescriptor(self.INlondisp, self.INlon)
				XPSetWidgetDescriptor(self.INaltdisp, str(round(self.INalt)))
				print "OXACARS - Building IN report..."
				#messg="BLOCK TIME "+self.blocktime+" /FUEL "+str(round(self.BF))+"\nFLIGHT TIME "+self.flighttime+" /FUEL "+str(round(self.FF))+"\nFLIGHT DISTANCE "+str(round(dist))+"\n"
				messg='BLOCK TIME %s /FUEL %.0f\nFLIGHT TIME %s /FUEL %.0f\nFLIGHT DISTANCE %.0f\n' % (self.blocktime, self.BF, self.flighttime, self.FF, dist)
			elif schg==10: # CHG CLB=0 LVL=1 DES=2
				if newstate==1:
					if cstate==0:
						act=' CHG CLIMB\n'
					elif cstate==1:
						act=' LEVEL\n'
					elif cstate==2:
						act=' CHG DESC\n'
					else:
						act='\n'
				else:
					act='\n'
					print "OXACARS - Building routine report..."
					#messg=POS+"/ALT "+str(round(Alt))+act+com+"/FOB "+str(round(FOB))+"\n/DST "+str(round(dist_down))+" - "+str(round(dist_togo))+"\n"
					messg='%s/ALT %.0f%s%s/FOB %.0f\n/DST %.0f - %.0f\n' % (POS, Alt, act, com, FOB, dist_down, dist_togo)
			else:
				messg="/I hate this airline YOLO"
			#print "OXACARS - Assembling message URL..."
			murl="DATA1="+DATA1v2+"&DATA2=MESSAGE&DATA3="+str(tstamp)+"&DATA4="+head+messg
			print "OXACARS - Will attempt to visit "+murl

			sendMsg=self.XACARSpost(self.acarsurl,murl)

			self.msg+=1
			self.FOB_prev=FOB # this is rocket science
			self.state=cstate # when you learn something, you need to remember it
			self.Counter=0 # no need to report sooner than interval

		self.C_then=C_now # in case we land before next loop
		self.Counter+=1 # increment loop counter

		# Return 1.0 to indicate that we want to be called again in 1 second.
		return 1.0
