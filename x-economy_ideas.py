from XPLMMenus import *
from XPLMNavigation import *
from XPWidgetDefs import *
from XPWidgets import *
from XPStandardWidgets import *
from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMUtilities import *
from XPLMPlanes import *
from httplib import *
from xml.dom import minidom
from re import *
from math import *
import urllib2
import hashlib
import os
import sys
from urllib import urlopen
from XPLMDisplay import *
from XPLMGraphics import *

##########################################################################################################################
## the engine class
class engine:
	def __init__(self,cht,runtime,chtDamage,mixDamage,engineNumber):
		self.defaultcht=cht
		self.runtime=runtime
		self.chtDamage=chtDamage
		self.engineNumber=engineNumber
		self.mixtureDamage=mixDamage
		self.numberOfEngines=XPLMGetDatai(XPLMFindDataRef("sim/aircraft/engine/acf_num_engines"))
		print "[XFSE|dbg] Engine created #"+str(engineNumber)

	def clearEng(self):
		print "[XFSE|dbg] Clearing engine"
		self.runtime=0
		self.chtDamage=0
		self.mixtureDamage=0

	def engineType(self):
		_engineType=[]
		XPLMGetDatavi(XPLMFindDataRef("sim/aircraft/prop/acf_prop_type"), _engineType, 0, self.numberOfEngines)
		return _engineType[self.engineNumber]

	def currentRPM(self):
		_currentRPM=[]
		XPLMGetDatavf(XPLMFindDataRef("sim/flightmodel/engine/ENGN_N2_"), _currentRPM, 0, self.numberOfEngines)
		return _currentRPM[self.engineNumber]

	def currentCHT(self):
		_currentCHT=[]
		XPLMGetDatavf(XPLMFindDataRef("sim/flightmodel/engine/ENGN_CHT_c"), _currentCHT, 0, self.numberOfEngines)
		return _currentCHT[self.engineNumber]

	def currentMIX(self):
		_currentMIX=[]
		XPLMGetDatavf(XPLMFindDataRef("sim/flightmodel/engine/ENGN_mixt"), _currentMIX, 0, self.numberOfEngines)
		return _currentMIX[self.engineNumber]*100

	def planeALT(self):
		_planeALT=XPLMGetDataf(XPLMFindDataRef("sim/flightmodel/position/y_agl"))
		return _planeALT*float(3.33)

	def feed(self,sec,rpm,mix,cht,altitude):
		if rpm>0:
			self.runtime+=sec
		if self.defaultcht>0:
			_diff=abs(cht-self.defaultcht)/float(sec)
			if _diff>0:
				self.chtDamage+=_diff
		self.defaultcht=cht
		if (mix > 95 and altitude > 1000):
			self.mixtureDamage += sec

	def getData(self,flightTime):
		return "&mixture"+str(self.engineNumber+1)+"="+str(self.mixtureDamage)+"&heat"+str(self.engineNumber+1)+"="+str(self.chtDamage)+"&time"+str(self.engineNumber+1)+"="+str(self.runtime)

	def isEngRun(self):
		_engrun = []
		XPLMGetDatavi(XPLMFindDataRef("sim/flightmodel/engine/ENGN_running"), _engrun, 0, self.numberOfEngines)
		return _engrun[self.engineNumber]
		
##########################################################################################################################
## the main plugin interface class
class PythonInterface:
	def XPluginStart(self):
		self.Name = "X-Economy"
		self.Sig =  "ksgy.Python.XFSEconomy"
		self.Desc = "X-Economy - plugin for FSEconomy (www.fseconomy.net)"
		self.VERSION="1.8.1"
		self.MenuItem1 = 0			#Flag if main window has already been created
		self.MenuItem2 = 0			#Flag if alias window has already been created
		self.cancelCmdFlag = 0		#Flag if "cancelArm" Command has been called

		self.flightTimer = 0		#X-Plane's one second Ticker
		self.flightTimerLast = 0	#last value of flightTimer to recognize a "flightTimer"-Reset

		self.XPVer = 10				#X-Plane Version
		
		self.connected = 0			#Flag if logged on to the FSE server
		self.flying = 0				#Flag if a Flight was started
		self.airborne = 0			#Flag if Plane/Heli took off the airfield
		self.flightStart = 0		#Time when the Flight was started
		self.flightTime = 0			#Time that we are flying
		self.Arrived = 0			#Flag that we have arrived and need to transmit the data now
		self.Transmitting = 0		#Counter for Transmit-Retries
		self.leaseStart = 0			#Maximum lease time allowed to this rent
		self.leaseTime = 0			#Actual lease time (time left)
		self.EndFlightCaption=""
		self.LeaseCaption = 0
		self.CurrentAircraft=""		#Name of the current aircraft
		
		self.endFlightTime = 60		#Seconds to pass to end   a flight
		self.endPlaneAlt = 5		#Maximum height  to end   a flight
		self.endPlaneSpd = 1		#Maximum speed   to end   a flight
		self.startPlaneAlt = 20		#Minimum height  to start a flight
		self.startPlaneSpd = 15		#Minimum speed   to start a flight
		self.startPlaneRpm = 10		#Minimum RPM     to start a flight
		self.startBrakeMax = 0.3	#Maximum Brake   to start a flight (mainly Carenado feature workaround)
		
		self.FuelTanks=[]
		self.stPayload=0
		self.stEq=0
		self.gsCheat=0
		self.globalX=0
		self.globalY=0
		self.checkfuel=0
		self.errortext=(["","","",""])
		self.errorcolor=""
		self.errormessage = 10		#Timeout that the GlassWindow-Messages will be shown
		self.ACEngine=[]
		Item = XPLMAppendMenuItem(XPLMFindPluginsMenu(), "X-Economy", 0, 1)
		self.XFSEMenuHandlerCB = self.XFSEMenuHandler
		self.Id = XPLMCreateMenu(self, "X-Economy" , XPLMFindPluginsMenu(), Item, self.XFSEMenuHandlerCB,	0)
		XPLMAppendMenuItem(self.Id, "Open X-Economy", 1, 1)
		XPLMAppendMenuItem(self.Id, "-", 3, 1)
		XPLMAppendMenuItem(self.Id, "Set aircraft alias", 2, 1)
		self.checkACStateCB = self.checkACState
		XPLMRegisterFlightLoopCallback(self, self.checkACStateCB, 1.0, 0)

		self.DrawWindowCB = self.DrawWindowCallback
		self.KeyCB = self.KeyCallback
		self.MouseClickCB = self.MouseClickCallback
		self.WindowId = XPLMCreateWindow(self, 50, 600, 300, 400, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)

		#register CustomDataRef
		self.tempCB0      = self.CallbackDatarefConnected
		self.drConnected  = XPLMRegisterDataAccessor(self, "fse/status/connected",  xplmType_Int, 0, self.tempCB0, None, None, None, None, None, None, None, None, None, None, None, 0, 0)
		self.tempCB1      = self.CallbackDatarefFlying
		self.drFlying     = XPLMRegisterDataAccessor(self, "fse/status/flying",     xplmType_Int, 0, self.tempCB1, None, None, None, None, None, None, None, None, None, None, None, 0, 0)
		self.tempCB4      = self.CallbackDatarefAirborne
		self.drAirborne   = XPLMRegisterDataAccessor(self, "fse/status/airborne",   xplmType_Int, 0, self.tempCB4, None, None, None, None, None, None, None, None, None, None, None, 0, 0)
		self.tempCB2      = self.CallbackDatarefLeasetime
		self.drLeasetime  = XPLMRegisterDataAccessor(self, "fse/status/leasetime",  xplmType_Int, 0, self.tempCB2, None, None, None, None, None, None, None, None, None, None, None, 0, 0)
		self.tempCB3      = self.CallbackDatarefFlighttime
		self.drFlighttime = XPLMRegisterDataAccessor(self, "fse/status/flighttime", xplmType_Int, 0, self.tempCB3, None, None, None, None, None, None, None, None, None, None, None, 0, 0)

		#register Custom commands
		self.CmdServerConn  = XPLMCreateCommand("fse/server/connect",      "Login to FSE Server")
		self.CmdWindowShow  = XPLMCreateCommand("fse/window/show",         "show FSE window")
		self.CmdWindowHide  = XPLMCreateCommand("fse/window/hide",         "hide FSE window")
		self.CmdWindowTogl  = XPLMCreateCommand("fse/window/toggle",       "toggle FSE window")
		self.CmdFlightStart = XPLMCreateCommand("fse/flight/start",        "Start flight")
		self.CmdFlightCArm  = XPLMCreateCommand("fse/flight/cancelArm",    "Cancel flight")
		self.CmdFlightCCon  = XPLMCreateCommand("fse/flight/cancelConfirm","Cancel flight confirm")
		
		self.CmdServerConnCB  = self.CmdServerConnCallback
		self.CmdWindowShowCB  = self.CmdWindowShowCallback
		self.CmdWindowHideCB  = self.CmdWindowHideCallback
		self.CmdWindowToglCB  = self.CmdWindowToglCallback
		self.CmdFlightStartCB = self.CmdFlightStartCallback
		self.CmdFlightCArmCB  = self.CmdFlightCArmCallback
		self.CmdFlightCConCB  = self.CmdFlightCConCallback
		
		XPLMRegisterCommandHandler(self, self.CmdServerConn,  self.CmdServerConnCB, 0, 0)
		XPLMRegisterCommandHandler(self, self.CmdWindowShow,  self.CmdWindowShowCB, 0, 0)
		XPLMRegisterCommandHandler(self, self.CmdWindowHide,  self.CmdWindowHideCB, 0, 0)
		XPLMRegisterCommandHandler(self, self.CmdWindowTogl,  self.CmdWindowToglCB, 0, 0)
		XPLMRegisterCommandHandler(self, self.CmdFlightStart, self.CmdFlightStartCB,0, 0)
		XPLMRegisterCommandHandler(self, self.CmdFlightCArm,  self.CmdFlightCArmCB, 0, 0)
		XPLMRegisterCommandHandler(self, self.CmdFlightCCon,  self.CmdFlightCConCB, 0, 0)

		#Create the Main Window Widget
		self.CreateXFSEWidget(221, 640, 480, 490)
		self.MenuItem1 = 1
		XPHideWidget(self.XFSEWidget)
		
		#
		return self.Name, self.Sig, self.Desc

	def XPluginStop(self):
		if (self.MenuItem1 == 1):
			XPDestroyWidget(self, self.XFSEWidget, 1)
			self.MenuItem1 = 0
		if (self.MenuItem2 == 1):
			XPDestroyWidget(self, self.CreateACAliasWidget, 1)
			self.MenuItem2 = 0

		XPLMDestroyMenu(self, self.Id)
		XPLMUnregisterFlightLoopCallback(self, self.checkACStateCB, 0)
		XPLMDestroyWindow(self, self.WindowId)

		XPLMUnregisterDataAccessor(self, self.drConnected)
		XPLMUnregisterDataAccessor(self, self.drFlying)
		XPLMUnregisterDataAccessor(self, self.drAirborne)
		XPLMUnregisterDataAccessor(self, self.drLeasetime)
		XPLMUnregisterDataAccessor(self, self.drFlighttime)

		XPLMUnregisterCommandHandler(self, self.CmdServerConn,  self.CmdServerConnCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdWindowShow,  self.CmdWindowShowCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdWindowHide,  self.CmdWindowHideCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdWindowTogl,  self.CmdWindowToglCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdFlightStart, self.CmdFlightStartCB,0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdFlightCArm,  self.CmdFlightCArmCB, 0, 0)
		XPLMUnregisterCommandHandler(self, self.CmdFlightCCon,  self.CmdFlightCConCB, 0, 0)
		
		pass

	def XPluginEnable(self):
		return 1

	def XPluginDisable(self):
		pass

	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass

	#############################################################
	## Callback handler for reading custom datarefs
	def CallbackDatarefConnected(self, inval):
		return self.connected
	def CallbackDatarefFlying(self, inval):
		return self.flying
	def CallbackDatarefAirborne(self, inval):
		return self.airborne
	def CallbackDatarefLeasetime(self, inval):
		return self.leaseTime
	def CallbackDatarefFlighttime(self, inval):
		return self.flightTime
		
	#############################################################
	## Callback handler for custom commands
	def CmdServerConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "[XFSE|Nfo] CMD server connect"
			self.login()
		return 0
			
	def CmdWindowShowCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "[XFSE|Nfo] CMD window show"
			XPShowWidget(self.XFSEWidget)
		return 0
			
	def CmdWindowHideCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "[XFSE|Nfo] CMD window hide"
			XPHideWidget(self.XFSEWidget)
		return 0
			
	def CmdWindowToglCallback(self, cmd, phase, refcon):
		if(phase==0):
			print "[XFSE|Nfo] CMD window toggle"
			if(not XPIsWidgetVisible(self.XFSEWidget)):
				XPShowWidget(self.XFSEWidget)
			else:
				XPHideWidget(self.XFSEWidget)
		return 0

	def CmdFlightStartCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "[XFSE|Nfo] CMD flight start"
			self.startFly()
		return 0

	def CmdFlightCArmCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "[XFSE|Nfo] CMD flight cancel arm"
			self.cancelCmdFlag = 1
		return 0
			
	def CmdFlightCConCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			if(self.cancelCmdFlag == 1):
				print "[XFSE|Nfo] CMD flight cancel confirm"
				self.cancelFlight("Flight cancelled","")
			else:
				print "[XFSE|Nfo] CMD flight cancel confirm is locked!"
		return 0
		
	#############################################################
	## Callback for System/plugin calls
	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def DrawWindowCallback(self, inWindowID, inRefcon):
		if(self.errortext[0] != "" and self.errormessage > 0):
			lLeft = [];	lTop = []; lRight = [];	lBottom = []
			XPLMGetWindowGeometry(inWindowID, lLeft, lTop, lRight, lBottom)
			left = int(lLeft[0]); top = int(lTop[0]); right = int(lRight[0]); bottom = int(lBottom[0])

			#window height depending of number of strings to show
			_yOffs=275
			if(self.errortext[3] == ""):
				_yOffs=290
				if(self.errortext[2] == ""):
					_yOffs=305
					if(self.errortext[1] == ""):
						_yOffs=315
					
			#window width depending of length of strings
			_xOffs=0 #130
			for _str in self.errortext:
				_px=XPLMMeasureString(xplmFont_Basic, _str, len(_str))+20
				if(_px>_xOffs):
					_xOffs=_px
			
			XPLMDrawTranslucentDarkBox(left,top+150,right+_xOffs-250,bottom+_yOffs)
			XPLMDrawTranslucentDarkBox(left,top+150,right+_xOffs-250,bottom+_yOffs) #draw two of them to add more contrast

			brt = 0.2
			color = 1.0, 1.0, 1.0
			if(self.errorcolor=="green"):
				color = brt, 1.0, brt
			if(self.errorcolor=="red"):
				color = 1.0, brt, brt
			if(self.errorcolor=="yellow"):
				color = 1.0, 1.0, brt

			XPLMDrawString(color, left+10, top+132, self.errortext[0], 0, xplmFont_Basic)
			XPLMDrawString(color, left+10, top+117, self.errortext[1], 0, xplmFont_Basic)
			XPLMDrawString(color, left+10, top+102, self.errortext[2], 0, xplmFont_Basic)
			XPLMDrawString(color, left+10, top+ 87, self.errortext[3], 0, xplmFont_Basic)

	#############################################################
	## GUI Creation Handler
	def CreateXFSEWidget(self, x, y, w, h):
		#read ini file
		try:
			_INIfile=open(os.path.join('Resources','plugins','PythonScripts','x-economy.ini'), 'r')
			_userINI=_INIfile.readline()
			_userINI=_userINI.replace('\n','')
			_passINI=_INIfile.readline()
			_INIfile.close()
			print "[XFSE|dbg] Init successfully completed"

		except IOError, (errno, strerror):
			_userINI=""
			_passINI=""

		self.globalX=x
		self.globalY=y
		x2 = x + w
		y2 = y - h
		
		#check X-Plane Version

		# Solution 2
		#XPlane9Date = "Jun  1 2011 23:51:55" # X-Plane 9.70
		CompileDate = []
		XPLMGetDatab(XPLMFindDataRef("sim/version/sim_build_string"), CompileDate, 0, 30)
		if " 2011 " in str(CompileDate):
			self.XPVer=9
		else:
			self.XPVer=10
		
		# Solution 2
		#if not XPLMFindDataRef("sim/operation/failures/rel_batter0"):
		#	self.XPVer=9
		#else:
		#	self.XPVer=10
		
		#Buffer = "X-Economy v"+str(self.VERSION)+" for X-Plane "+str(self.XPVer)+" ("+str(CompileDate)+")"
		Buffer = "X-Economy v"+str(self.VERSION)+" for X-Plane "+str(self.XPVer)

		# Create the Main Widget window
		self.XFSEWidget = XPCreateWidget(x, y, x2, y2, 1, Buffer, 1,	0, xpWidgetClass_MainWindow)

		# Add Close Box decorations to the Main Widget
		XPSetWidgetProperty(self.XFSEWidget, xpProperty_MainWindowHasCloseBoxes, 1)

		# Create the Sub Widget1 window
		# Added by Egor 'SanDmaN' Pastukhov 22.03.2010 - littile correction of window geometry (height)
		XFSEWindow1 = XPCreateWidget(x+10, y-30, x2-10, y2+400,
					     1,		# Visible
					     "",		# desc
					     0,		# root
					     self.XFSEWidget,
					     xpWidgetClass_SubWindow)

		# Set the style to sub window (Top Button Box)
		XPSetWidgetProperty(XFSEWindow1, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)

		# Create the Sub Widget2 window (Lower Box)
		XFSEWindow2 = XPCreateWidget(x+10, y-100, x2-10, y2+10,
					     1,		# Visible
					     "",		# desc
					     0,		# root
					     self.XFSEWidget,
					     xpWidgetClass_SubWindow)

		# Set the style to sub window (Assignments Box)
		XPSetWidgetProperty(XFSEWindow2, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)

		XFSEWindow3 = XPCreateWidget(x+15, y-130, x2-15, y2+150,
					     1,		# Visible
					     "",		# desc
					     0,		# root
					     self.XFSEWidget,
					     xpWidgetClass_SubWindow)

		# Set the style to sub window
		XPSetWidgetProperty(XFSEWindow2, xpProperty_SubWindowType, xpSubWindowStyle_SubWindow)

		# Login user caption
		LoginUserCaption = XPCreateWidget(x+20, y-40, x+50, y-60,1, "Username:", 0, self.XFSEWidget,xpWidgetClass_Caption)

		# Login user field
		self.LoginUserEdit = XPCreateWidget(x+80, y-40, x+160, y-60,1, _userINI, 0, self.XFSEWidget,xpWidgetClass_TextField)
		XPSetWidgetProperty(self.LoginUserEdit, xpProperty_TextFieldType, xpTextEntryField)
		XPSetWidgetProperty(self.LoginUserEdit, xpProperty_Enabled, 1)

		# Login pass caption
		LoginPassCaption = XPCreateWidget(x+20, y-60, x+50, y-80,1, "Password:", 0, self.XFSEWidget,xpWidgetClass_Caption)

		# Login user field
		self.LoginPassEdit = XPCreateWidget(x+80, y-60, x+160, y-80,1, _passINI, 0, self.XFSEWidget,xpWidgetClass_TextField)
		XPSetWidgetProperty(self.LoginPassEdit, xpProperty_TextFieldType, xpTextEntryField)
		XPSetWidgetProperty(self.LoginPassEdit, xpProperty_Enabled, 1)
		XPSetWidgetProperty(self.LoginPassEdit, xpProperty_PasswordMode, 1)

		# Login button
		self.LoginButton = XPCreateWidget(x+180, y-40, x+260, y-60,1, "Log in", 0, self.XFSEWidget,xpWidgetClass_Button)
		XPSetWidgetProperty(self.LoginButton, xpProperty_ButtonType, xpPushButton)

		# Server response text
		self.ServerResponseCaption = XPCreateWidget(x+180, y-60, x+260, y-80,1, "Not logged in", 0, self.XFSEWidget,xpWidgetClass_Caption)

		# Assignments text
		self.AssignmentListCaption = XPCreateWidget(x+20, y-105, x+50, y-125,1, "Assignment info:", 0, self.XFSEWidget,xpWidgetClass_Caption)

		# Error text
		self.ErrorCaption=[]
		self.ErrorCaption.append(XPCreateWidget(x+20, y-410, x+50, y-430,1, "", 0, self.XFSEWidget,xpWidgetClass_Caption))
		# Error2 text
		self.ErrorCaption.append(XPCreateWidget(x+20, y-425, x+50, y-445,1, "", 0, self.XFSEWidget,xpWidgetClass_Caption))
		# Error3 text
		self.ErrorCaption.append(XPCreateWidget(x+20, y-440, x+50, y-460,1, "", 0, self.XFSEWidget,xpWidgetClass_Caption))
		# Error4 text
		self.ErrorCaption.append(XPCreateWidget(x+20, y-455, x+50, y-475,1, "", 0, self.XFSEWidget,xpWidgetClass_Caption))

		# From/To/Cargo
		self.FromCaption=[]
		self.ToCaption=[]
		self.CargoCaption=[]

		# AC reg
		self.ACRegCaption = XPCreateWidget(x+20, y-340, x+50, y-360,1, "", 0, self.XFSEWidget,xpWidgetClass_Caption)

		# Lease expires
		self.LeaseCaption = XPCreateWidget(x+20, y-360, x+50, y-380,1, "", 0, self.XFSEWidget,xpWidgetClass_Caption)

		# Current flight time
		self.EndFlightCaption = XPCreateWidget(x+20, y-330, x+50, y-450,1, "", 0, self.XFSEWidget,xpWidgetClass_Caption)
		
		# Start fly button
		self.StartFlyButton = XPCreateWidget(x+360, y-40, x+450, y-60,
						     1, "Start flying", 0, self.XFSEWidget,
						     xpWidgetClass_Button)
		XPSetWidgetProperty(self.StartFlyButton, xpProperty_ButtonType, xpPushButton)
		XPSetWidgetProperty(self.StartFlyButton, xpProperty_Enabled, 0)

		# cancel fly button
		self.CancelFlyButton = XPCreateWidget(x+360, y-60, x+450, y-80,
						      1, "Cancel flight", 0, self.XFSEWidget,
						      xpWidgetClass_Button)
		XPSetWidgetProperty(self.CancelFlyButton, xpProperty_ButtonType, xpPushButton)
		XPSetWidgetProperty(self.CancelFlyButton, xpProperty_Enabled, 0)

		# Register our widget handler
		self.XFSEHandlerCB = self.XFSEHandler
		XPAddWidgetCallback(self, self.XFSEWidget, self.XFSEHandlerCB)

		#update button
		self.UpdateButton = XPCreateWidget(x+270, y-40, x+350, y-60,1, "Update", 0, self.XFSEWidget,xpWidgetClass_Button)
		XPSetWidgetProperty(self.UpdateButton, xpProperty_ButtonType, xpPushButton)
		XPSetWidgetProperty(self.UpdateButton, xpProperty_Enabled, 0)

	#############################################################
	## GUI (BTN) Message Handler
	def XFSEHandler(self, inMessage, inWidget,    inParam1, inParam2):
		if (inMessage == xpMessage_CloseButtonPushed):
			print "[XFSE|dbg] Client window closed"
			if (self.MenuItem1 == 1):
				XPHideWidget(self.XFSEWidget)
				return 1

		if (inMessage == xpMsg_PushButtonPressed):
			if (inParam1 == self.LoginButton):
				print "[XFSE|Nfo] BTN Login"
				return self.login()
			elif (inParam1 == self.StartFlyButton):
				print "[XFSE|Nfo] BTN Start flying"
				return self.startFly()
			elif (inParam1 == self.CancelFlyButton):
				print "[XFSE|Nfo] BTN canel flight"
				self.cancelFlight("Flight cancelled","")
			elif (inParam1 == self.UpdateButton):
				self.doUpdate()
			else:
				print "[XFSE|ERR] UNKNOWN GUI button pressed"
				
		return 0

	#############################################################
	## Custom Plane Description functions
	# Added by SanDmaN
	def ReadACAliasFromFile(self):
		raw_PlanePath = XPLMGetNthAircraftModel(0)
		planePath = os.path.dirname(raw_PlanePath[1])
		aliasFile = os.path.join(planePath, 'xfse_alias.txt')

		if (os.path.exists(aliasFile) and os.path.isfile(aliasFile)):
			fd = open(aliasFile, 'r')
			alias = fd.readline()
			fd.close()
			alias = alias.replace('\r','')
			alias = alias.replace('\n','')
			return alias
		return ""

	def WriteACAliasToFile(self, alias):
		raw_PlanePath = XPLMGetNthAircraftModel(0)
		planePath = os.path.dirname(raw_PlanePath[1])
		aliasFile = os.path.join(planePath, 'xfse_alias.txt')
		fd = open(aliasFile, 'wb')
		alias = fd.write(alias)
		fd.close()

	def ACAliasWidget_cb(self, inMessage, inWidget, inParam1, inParam2):
		if (inMessage == xpMessage_CloseButtonPushed):
				XPHideWidget(self.ACAliasWidget)
				return 1

		if (inMessage == xpMsg_PushButtonPressed):
			if (inParam1 == self.SetACAliasButton):
				ac_alias = []
				XPGetWidgetDescriptor(self.ACAliasEdit, ac_alias, 256)
				self.WriteACAliasToFile(ac_alias[0])
				XPHideWidget(self.ACAliasWidget)
				return 1

		if (inMessage == xpMsg_Shown):
			ac_alias = self.ReadACAliasFromFile()
			XPSetWidgetDescriptor(self.ACAliasEdit, ac_alias)
			return 1

		return 0

	def CreateACAliasWidget(self, x, y, w ,h):
		x2 = x + w
		y2 = y - h

		self.ACAliasWidget = XPCreateWidget(x, y, x2, y2, 1, "Enter custom alias", 1, 0, xpWidgetClass_MainWindow)
		XPSetWidgetProperty(self.ACAliasWidget, xpProperty_MainWindowHasCloseBoxes, 1)

		HintCaption = XPCreateWidget(x+7, y-17, x+248, y-37, 1, "Leave input field blank to use alias from .acf file", 0, self.ACAliasWidget, xpWidgetClass_Caption)

		# Alias field
		ac_alias = self.ReadACAliasFromFile()
		self.ACAliasEdit = XPCreateWidget(x+7, y-40, x+265, y-60, 1, ac_alias, 0, self.ACAliasWidget, xpWidgetClass_TextField)
		XPSetWidgetProperty(self.ACAliasEdit, xpProperty_TextFieldType, xpTextEntryField)
		XPSetWidgetProperty(self.ACAliasEdit, xpProperty_Enabled, 1)

		# SET button
		self.SetACAliasButton = XPCreateWidget(x+96, y-62, x+176, y-82, 1, "Set", 0, self.ACAliasWidget, xpWidgetClass_Button)
		XPSetWidgetProperty(self.SetACAliasButton, xpProperty_ButtonType, xpPushButton)

		# callback
		self.ACAliasWidgetCB = self.ACAliasWidget_cb
		XPAddWidgetCallback(self, self.ACAliasWidget, self.ACAliasWidgetCB)

	#############################################################
	## Menu Handler
	def XFSEMenuHandler(self, inMenuRef, inItemRef):
		# If menu selected create our widget dialog
		if (inItemRef == 1):
			if (self.MenuItem1 == 0):
				self.CreateXFSEWidget(221, 640, 480, 490)
				self.MenuItem1 = 1
			else:
				if(not XPIsWidgetVisible(self.XFSEWidget)):
					XPShowWidget(self.XFSEWidget)
		elif (inItemRef == 2):
			if (self.MenuItem2 == 0):
				self.CreateACAliasWidget(128, 480, 272, 87)
				self.MenuItem2 = 1
			else:
				if (not XPIsWidgetVisible(self.ACAliasWidget)):
					XPShowWidget(self.ACAliasWidget)

	#############################################################
	## FSEconomy Server Communication
	def XFSEpost(self, query):
		f1 = open(os.path.join('Resources','plugins','PythonScripts','PI_xfse.py'), 'rb')
		filemd5sum = hashlib.md5(f1.read()).hexdigest()
		f1.close()

		URL = 'http://www.fseconomy.net:81/fsagentx?md5sum='+filemd5sum+'&'+query;
		#print "[XFSE|dbg] Calling URL: "+URL
		stuff = urlopen(URL).read()
		stuff = stuff.replace('&',' and ')
		#print "[XFSE|dbg] Server retd: "+stuff
		dom = minidom.parseString(stuff)
		return dom

	#############################################################
	## Helper funcs
	def setInfoMessage(self, msg1,msg2,msg3,msg4, color):
		self.errortext[0] = msg1
		self.errortext[1] = msg2
		self.errortext[2] = msg3
		self.errortext[3] = msg4
		self.errorcolor = color
		self.errormessage = 10
		XPSetWidgetDescriptor(self.ErrorCaption[0], self.errortext[0])
		XPSetWidgetDescriptor(self.ErrorCaption[1], self.errortext[1])
		XPSetWidgetDescriptor(self.ErrorCaption[2], self.errortext[2])
		XPSetWidgetDescriptor(self.ErrorCaption[3], self.errortext[3])

	#############################################################
	## Plane related Helper funcs
	def isAllEngineStopped(self):
		_allenginestopped = True
		try:
			for ienga in range(self.NumberOfEngines):
				if self.ACEngine[ienga].isEngRun() > 0:
					_allenginestopped = False
		except Exception:
			_allenginestopped = True

		return _allenginestopped

	def setPlanePayload(self,payload):
		XPLMSetDataf(XPLMFindDataRef("sim/flightmodel/weight/m_fixed"), float(payload))
	
	def setPlaneEW(self,EW):
		XPLMSetDataf(XPLMFindDataRef("sim/aircraft/weight/acf_m_empty"), float(EW))

	def getPlaneEW(self,AC):
		self.stockEW=XPLMGetDataf(XPLMFindDataRef("sim/aircraft/weight/acf_m_empty"))
		EWlist=(("Airbus A320",42220),
				("Airbus A321",48038),
				("Boeing 247D",4055),
				("Boeing 727-100/200",45400),
				("Boeing 737-800",41145),
				("Piper J-3 Cub",308),
				("Cessna 152 Aerobat",517),
				("Luscombe 8A",340),
				("Robinson R22",376),
				("Aeronca Champion",325),
				("Piper PA-18 Super Cub",476),
				("American Champion Scout",597),
				("Globe Swift",500),
				("Aviat A-1 Husky",652),
				("Piper PA-38 Tomahawk",512),
				("Diamond DA20 Katana",519),
				("Aircreation 582SL",168),
				("Bell 47G-2",788),
				("Stinson L-5B Sentinel",702),
				("Van's RV-7/7A",495),
				("ERCO Ercoupe 415-C",339),
				("Zepplin NT",60),
				("Waco Classic YMF",1136),
				("DeHavilland DH-82 Tiger Moth",512),
				("North American T-28 Trojan",2914),
				("Bucker Jungmann 131",390),
				("Boeing Stearman",878),
				("Fairchild PT19/26 Cornell",822),
				("Lancair Legacy",635),
				("Cessna 162 Skycatcher",382),
				("Liberty XL2",533),
				("BAC Jet Provost T5",2222),
				("DeHavilland DHC-1 Chipmunk",537),
				("PZL Wilga",890),
				("Cessna 172 Skyhawk",748),
				("North American P-51D Mustang",3263),
				("DeHavilland DH80A Puss Moth",575),
				("Curtiss Robertson Robin J-1",699),
				("North American T-6G Texan",2384),
				("Auster J/1 Autocrat",470),
				("Eurocopter Colibri EC 120",455),
				("Piper PA-22 Super Pacer",528),
				("Piper PA-12 Super Cruiser RTW",476),
				("Stinson 108",599),
				("Zenair CH 801",522),
				("SIAI-Marchetti SF260",796),
				("Robinson R44",635),
				("Piper PA-28 Archer",727),
				("Piper PA-28 Cherokee 180",555),
				("Piper PA-20 Pacer",455),
				("Yakovlev Yak-12A",1026),
				("Piper PA-28 Warrior",700),
				("Beech T-34 Mentor",1018),
				("Piper PA-22 Tri-Pacer",528),
				("Zlin Z-43",830),
				("Robin/Apex DR221",480),
				("Yakovlev Yak-18T",1217),
				("Stinson Reliant",1114),
				("Cessna 182 Skylane",821),
				("Tecnam P92 Echo",284),
				("Cessna 177 Cardinal",745),
				("Socata TB-10 Tobago",730),
				("Cessna 177RG Cardinal",800),
				("Cessna L-19/O-1 Birddog",682),
				("Bell 206B",799),
				("Bell 206L RTW N3911Z",799),
				("Piper PA-24 Comanche",859),
				("Rans S-7 Courier",306),
				("Piper PA-28 Arrow",756),
				("Let L 410 UVP-T",3964),
				("Grumman Tiger",588),
				("Commander 112",695),
				("Diamond DA-42 Twin Star",1263),
				("Socata TB21GT Trinidad",800),
				("Piaggio P-149D",1167),
				("SIAI-Marchetti SM.1019A",690),
				("New Standard D25A",932),
				("Piper PA-28 Dakota",776),
				("Hughes/McDonnell Douglas MD500E",675),
				("Diamond DA40D DiamondStar",735),
				("Republic Seabee",993),
				("Cirrus SR20",938),
				("Piper PA-30 Twin Comanche",1124),
				("Beech Debonair",791),
				("Piper PA-23 Apache",1004),
				("Commander 115",976),
				("Bellanca 260",794),
				("Maule M-7",681),
				("Rockwell Commander 114",855),
				("Meyers 200D",900),
				("Robin DR400",638),
				("Cessna T-50 Bobcat",1841),
				("Cirrus SR22 G2",1023),
				("Messerschmitt Bf 108 B",863),
				("Bell 205A-1/UH-1C",2497),
				("Cessna 195",929),
				("Beechcraft Duchess 76",1116),
				("Piper PA-44 Seminole",1183),
				("Fairchild 24R",762),
				("Found Bush Hawk",895),
				("Eurocopter AS-350 Ecureuil",1171),
				("Dornier Do-27 A4",1052),
				("Dornier Do-27 B1",1070),
				("Beriev BE-103",1680),
				("Grumman G-44 Widgeon",1447),
				("Helio Super Courier H-295/U-10b",943),
				("Ford Tri-Motor",3000),
				("Columbia 400",1136),
				("Bell 407",1178),
				("Lake Renegade",839),
				("Lockheed Vega",1166),
				("Cessna 337 Skymaster",1204),
				("Mooney M20 Juliet",744),
				("Spartan 7W Executive",1242),
				("Cessna 185 Skywagon",727),
				("Antonov An-14",2600),
				("Boeing 221A Monomail",2067),
				("Cessna 206 Stationair",883),
				("Cessna 310",1642),
				("Agusta A109",1930),
				("DeHavilland DHC-2 Beaver",1293),
				("Eurocopter BK117",1500),
				("Junkers W33 EW Flight",612),
				("Junkers W33/34",612),
				("Ryan L-17 Navion",831),
				("DeHavilland DH 89 Dragon Rapide",1330),
				("Mooney M20 Bravo",993),
				("Bell 430",2354),
				("Bell 430 RTW N430Q",2354),
				("Beechcraft Bonanza A36",1148),
				("Cessna 210 Centurion",1023),
				("Piper PA-32 Cherokee Six/ Saratoga",950),
				("Beechcraft Bonanza F33",1000),
				("Beechcraft Bonanza V35",1000),
				("Piaggio 166 Albatross",2700),
				("Howard DGA-15",1236),
				("Gippsland GA8 Airvan",862),
				("Beechcraft 17",1113),
				("Piper PA-32 Saratoga TC",991),
				("Piper PA-23 Aztec",1483),
				("Aero Vodochody L-39",4980),
				("Morane-Saulnier MS-760",4939),
				("Beechcraft Duke B60",2007),
				("Lancair Legacy IV-P",1105),
				("Piper PA-34 Seneca",1417),
				("Piper PA-60 Aerostar",2111),
				("Bell UH-1H Huey",2358),
				("Beechcraft Baron 58",1774),
				("Beechcraft Baron 58 - tip tanks (Dreamfleet)",1774),
				("Piper PA-31T1 Cheyenne I/IA",2318),
				("DeHavilland DHC-2 Turbo Beaver",1268),
				("Sikorsky S-55",2381),
				("Cessna 207 Stationair 8",951),
				("Antonov AN-2",3330),
				("Piper PA-31T Cheyenne II",2257),
				("Bell 412",3156),
				("Piper PA-31 Navajo",1927),
				("Bell 212",2516),
				("Douglas A-26",10168),
				("North American B-25",9610),
				("Britten-Norman BN-2B Islander",1925),
				("Aero Design AC500C",1746),
				("Supermarine Walrus MK 1",2220),
				("Noorduyn Norseman",2052),
				("Aero Design AC680S",2005),
				("Piper PA-46 Meridian",1533),
				("Beechcraft Twin Bonanza 50",1778),
				("Pilatus PC-6 Porter",1250),
				("Cessna 340A",1780),
				("Eurocopter EC-135",1455),
				("Aero Design AC690",2810),
				("Beagle B 206 Basset",1979),
				("Sikorsky S-76",2695),
				("Pacific Aerospace 750XL",1393),
				("Cessna Mustang",3960),
				("Socata TBM 700",1823),
				("Quest Kodiak",1522),
				("Beechcraft Royal Turbine Duke B60",2109),
				("Beechcraft 18",2576),
				("Grumman G21 Goose",2800),
				("Aermacchi - Lockheed AL-60",1068),
				("DeHavilland DHC-3 Otter",2110),
				("DeHavilland DH104 Dove",2563),
				("Junkers Ju-52",6590),
				("Cessna 421 Golden Eagle",2443),
				("Grumman S2/C1",7560),
				("Piper PA-31T2 Cheyenne IIXL",2489),
				("Lockheed L10A Electra",2927),
				("Lockheed L10E Amelia Special",2927),
				("Socata TBM 850",2081),
				("Grumman Turbo Goose",3175),
				("Beech Queen Air 80S",2173),
				("Embraer Phenom 100",3235),
				("Cessna 414A Chancellor",1984),
				("Cessna 404 Titan",2192),
				("Australia GAF N22 Nomad",2925),
				("Beechcraft Queen Air",2449),
				("Mitsubishi MU-2B",3470),
				("Cessna Citation CJ1",2930),
				("Eclipse 500",1537),
				("Kazan Helicopter Plant Mi-17-1V-GA",7070),
				("Douglas DC-2",5604),
				("Douglas DC-2 (FSX)",5604),
				("DeHavilland DHC-3-T Turbo Otter",1710),
				("Beechcraft 1900C Freighter",4045),
				("Westland Seaking",6202),
				("Britten Norman BN-2A Mk3-3 Trislander",2485),
				("Consolidated PBY5 Catalina",9384),
				("Cessna 208 Caravan",2075),
				("Sikorsky S-43",5783),
				("Cessna 441 Conquest II",2592),
				("Raytheon Premier1",3634),
				("Piaggio 180 Avanti",3400),
				("Beechcraft King Air C90",3005),
				("Cessna Citation II",3220),
				("Lear 45",5318),
				("Shorts Skyvan",3341),
				("Pilatus PC-12",2605),
				("DeHavilland DHC-6 300 Twin Otter (Aerosoft Extended)",3265),
				("DeHavilland DHC-6 Twin Otter",3265),
				("Howard Aero 500",10886),
				("Antonov An-28",4123),
				("Beechcraft King Air 200",3675),
				("Piper PA-42-1000 Cheyenne 400",3563),
				("Raytheon Beechjet / Hawker",4717),
				("Beechcraft King Air 350",4123),
				("Bombardier Challenger 300",10773),
				("Let L 410 UVP-E",3964),
				("Beechcraft King Air 300",4009),
				("North American T-39 Sabreliner",7527),
				("LearJet LJ25D",3637),
				("Douglas DC-3",7325),
				("Bombardier CL-415",10546),
				("Beechcraft 1900C",4422),
				("Cessna Citation X",9797),
				("Grumman HU-16B Albatross",10227),
				("Beechcraft 1900D",4815),
				("DeHavilland DHC-4 Caribou",8293),
				("Embraer 110",3515),
				("BAe Jetstream 32",4360),
				("Fairchild Metro III",4164),
				("Dornier 228",3258),
				("Dassault Falcon 7X",15059),
				("Embraer Legacy 600",16000),
				("Fairchild C123",12519),
				("Douglas C117D",8600),
				("Ilyushin Il-14",12500),
				("Boeing Vertol CH-47 Chinook",10150),
				("Curtis C46",13710),
				("Bombardier Lear 60",6641),
				("BAe Jetstream 41",6415),
				("SAAB Scandia 90",9960),
				("Basler BT-67",7144),
				("Yakovlev Yak-40",9400),
				("Embraer 120",7100),
				("Boeing B-17G",16391),
				("Shorts SD3-60",6758),
				("DeHavilland Dash 8 100/200",10400),
				("Antonov An-26 Curl",13400),
				("Saab 340B",8620),
				("DeHavilland DHC-5 Buffalo",11436),
				("Martin 404",14786),
				("Convair 340/440",13828),
				("CASA CN235",9800),
				("Airspeed AS-57 Ambassador ",16062),
				("Antonov An-24",13800),
				("Hawker Siddeley HS-748",11570),
				("Fairchild C119",16145),
				("DeHavilland Dash 7",12568),
				("Alenia C-27J Spartan",14620),
				("Alenia C-27J Spartan (IRIS)",14620),
				("Convair 580",14772),
				("Douglas DC-6",28727),
				("Antonov An-32",16800),
				("Fokker F27-500 Friendship",12243),
				("DeHavilland Dash 8 Q300",11791),
				("Lockheed C-130 (Capt Sim)",34300),
				("Lockheed C-130 (Generic)",34350),
				("ATR 72-500",12950),
				("Vickers Viscount",16718),
				("Lockheed Constellation",41306),
				("Embraer ERJ-135LR",11499),
				("Boeing 377",38083),
				("Embraer ERJ-145LR",12399),
				("Douglas DC-4",18583),
				("Tupolev Tu-124",22493),
				("Bombardier CRJ-200ER",9298),
				("Douglas DC-6B",28727),
				("Douglas DC-7B",26376),
				("Lockheed P-3C (L-188)",30344),
				("Ilyushin Il-18D",35000),
				("Bombardier Dash-8 Q400",17185),
				("Douglas DC-7C",33005),
				("Bristol Britannia 300",42469),
				("Bombardier CRJ700-ER",19731),
				("BAe 146-100 (Avro RJ70)",23300))
		for i in range(length(EWlist)):
			if EWlist[i][0]==AC:
				XPLMSetDataf(wgt_EW_ref,EWlist[i][1])
				break

	#############################################################
	## Instruments functions
	def setInstrGPS(self,failmode):
		self.setInstrGPS_Vx(failmode)
		#if self.XPVer == 9:
		#	self.setInstrGPS_V9(failmode)
		#else:
		#	self.setInstrGPS_V10(failmode)

	def setInstrAP(self,failmode):
		if self.XPVer == 9:
			self.setInstrAP_V9(failmode)
		else:
			self.setInstrAP_V10(failmode)

	def setInstrIFR(self,failmode):
		if self.XPVer == 9:
			self.setInstrIFR_V9(failmode)
		else:
			self.setInstrIFR_V10(failmode)

	def enableAllInstruments(self):
		self.setInstrGPS(0) 	#remove failure modes
		self.setInstrAP(0) 		#remove failure modes
		self.setInstrIFR(0) 	#remove failure modes

	#############################################################
	## Instruments V10/V9
	def setInstrGPS_Vx(self,failmode):
		if(failmode!=0):
			_source="sim/cockpit2/radios/actuators/HSI_source_select_pilot"
			if(XPLMGetDatai(XPLMFindDataRef(_source))==2):
				XPLMSetDatai(XPLMFindDataRef(_source),0)
			_source="sim/cockpit2/radios/actuators/HSI_source_select_copilot"
			if(XPLMGetDatai(XPLMFindDataRef(_source))==2):
				XPLMSetDatai(XPLMFindDataRef(_source),0)
			_source="sim/cockpit2/radios/actuators/RMI_source_select_pilot"
			if(XPLMGetDatai(XPLMFindDataRef(_source))==2):
				XPLMSetDatai(XPLMFindDataRef(_source),0)
			_source="sim/cockpit2/radios/actuators/RMI_source_select_copilot"
			if(XPLMGetDatai(XPLMFindDataRef(_source))==2):
				XPLMSetDatai(XPLMFindDataRef(_source),0)
		#XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gps"),int(failmode))
		#XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gps2"),int(failmode))
		#XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g430_gps1"),int(failmode))
		#XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g430_gps2"),int(failmode))

	#############################################################
	## Instruments V10
	def setInstrAP_V10(self,failmode):
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_auto_servos"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_otto"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_servo_ailn"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_servo_elev"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_servo_rudd"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_servo_thro"),int(failmode))

	def setInstrIFR_V10(self,failmode):
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gps"),6)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gps2"),6) #wenn Config AP,GPS wird das hier trotzdem ausgemacht !? Kazan!

		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gls"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_dme"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_adf1"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_adf2"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_nav1"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_nav2"),int(failmode))

#	def enableAllInstruments_V10(self,failmode):
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gps"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gps2"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g430_gps1"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g430_gps2"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_auto_servos"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_otto"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_servo_ailn"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_servo_elev"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_servo_rudd"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_servo_thro"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gls"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_dme"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_adf1"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_adf2"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_nav1"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_nav2"),0)

	#############################################################
	## Instruments V9
#	def setInstrGPS_V9(self,failmode):
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gps"),int(failmode))
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gps1"),int(failmode))
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gps2"),int(failmode))

	def setInstrAP_V9(self,failmode):
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_otto"),int(failmode))

	def setInstrIFR_V9(self,failmode):
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gs1"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gs2"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_navrad1"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_navrad2"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gls"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_dme"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_adf1"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_adf2"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_nav1"),int(failmode))
		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_nav2"),int(failmode))

#	def enableAllInstruments_V9(self):
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gps"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gps1"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gps2"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_otto"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gs1"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_gs2"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_navrad1"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_g_navrad2"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_gls"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_dme"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_adf1"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_adf2"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_nav1"),0)
#		XPLMSetDatai(XPLMFindDataRef("sim/operation/failures/rel_nav2"),0) 
		
	#############################################################
	## airborne/flight supervising function
	def checkACState(self, elapsedMe, elapsedSim, counter, refcon):
		if(self.errormessage>0):
			self.errormessage = self.errormessage - 1
		
		_groundcompression=XPLMGetDatai(XPLMFindDataRef("sim/time/ground_speed"))
		XPLMSetDatai(XPLMFindDataRef("sim/time/ground_speed"),1)

		# flightTimer and check
		self.flightTimer=XPLMGetDataf(XPLMFindDataRef("sim/time/total_flight_time_sec"))

		if self.flying==1:
			
			elapsed=self.flightTimer-self.flightTimerLast
			
			if _groundcompression>1:
				self.gsCheat+=1

			if self.gsCheat>10:
				self.cancelFlight("Excessive time compression used. Your flight has been cancelled")

			if self.ACEngine[0].engineType() == 3 or self.ACEngine[0].engineType() == 5:
				isHeli = 1
			else:
				isHeli = 0
					  
			if(isHeli == 0):
				isBrake=XPLMGetDataf(XPLMFindDataRef("sim/flightmodel/controls/parkbrake"))
			else:
				isBrake=float(XPLMGetDatai(XPLMFindDataRef("sim/cockpit2/switches/rotor_brake")))
				
			airspeed=XPLMGetDataf(XPLMFindDataRef("sim/flightmodel/position/groundspeed"))

			#fuel change check
			_fueltotal=XPLMGetDataf(XPLMFindDataRef("sim/flightmodel/weight/m_fuel_total"))

			# converting values to integer for comparison.  values after decimal were unrelaiable for this purpose.
			if((int(_fueltotal) * 0.95) > int(self.checkfuel)):
				self.cancelFlight("Airborn refueling not allowed. Flight cancelled","")

			self.checkfuel=XPLMGetDataf(XPLMFindDataRef("sim/flightmodel/weight/m_fuel_total"))

			# flightTimer check
			if(self.flightTimer < self.flightTimerLast):
				self.cancelFlight("Aircraft changed or repositioned. Your flight has been cancelled","")
			self.flightTimerLast=self.flightTimer

			# flightTime calc
			self.flightTime=int( self.flightTimer - self.flightStart )
			
			# lease time calc
			if self.leaseTime>0: 
				self.leaseTime=int(self.leaseStart-self.flightTime)

			# times output
			if self.LeaseCaption:
				_outtxt=""
				
				_currhours=self.flightTime/3600
				_currmins=(self.flightTime-_currhours*3600)/60
				_outtxt+="Current flight time: "+str(_currhours)+" hours "+str(_currmins)+" mins"
				
				_leasehours=self.leaseTime/3600
				_leasemins=(self.leaseTime-_leasehours*3600)/60
				_outtxt+=" - Lease time left: "+str(_leasehours)+" hours "+str(_leasemins)+" mins"
				
				XPSetWidgetDescriptor(self.LeaseCaption, _outtxt)

			# Status
			if self.EndFlightCaption:
				if(self.airborne==0):
					_outtxt = "To go airborne:"
					if(self.ACEngine[0].currentRPM()<float(self.startPlaneRpm)):
						_outtxt += " RPM>"+str(self.startPlaneRpm)+"/min"

					if(self.ACEngine[0].planeALT()<self.startPlaneAlt):
						_outtxt += " ALT>"+str(self.startPlaneAlt)+"ft"

					if(airspeed<self.startPlaneSpd):
						_outtxt += " SPD>"+str(self.startPlaneSpd)+"kts"

					if(isHeli == 0):
						_brk="PrkBrk"
					else:
						_brk="RotBrk"
					if(isBrake>self.startBrakeMax):
						_outtxt += " "+_brk+"<="+str(int(self.startBrakeMax*100))+"%"
					if(isBrake>self.startBrakeMax and isBrake<1.0):
						_outtxt += " ("+_brk+"="+str(int(isBrake*100))+"%)"
				
				else:
					_outtxt = "To end flight:"
					
					if(self.flightTime<self.endFlightTime):
						_outtxt += " FltTim>"+str(self.endFlightTime)+"s"

					if(self.ACEngine[0].planeALT()>self.endPlaneAlt):
						_outtxt += " ALT<"+str(self.endPlaneAlt)+"ft"

					if(airspeed>self.endPlaneSpd):
						_outtxt += " SPD<"+str(self.endPlaneSpd)+"kts"

					for ienga in range(self.NumberOfEngines):
						if self.ACEngine[ienga].isEngRun() > 0:
							_outtxt += " Eng"+str(ienga+1)

					if(isHeli == 0):
						_brk="PrkBrk"
					else:
						_brk="RotBrk"
					if(isBrake!=1.0):
						_outtxt += " "+_brk+"=100%"
					if(isBrake>0 and isBrake<1.0):
						_outtxt += " ("+_brk+"="+str(int(isBrake*100))+"%)"

				XPSetWidgetDescriptor(self.EndFlightCaption, _outtxt)
				
			# go airborne
			if(isBrake<=self.startBrakeMax and self.ACEngine[0].currentRPM()>float(self.startPlaneRpm) and airspeed>float(self.startPlaneSpd) and self.ACEngine[0].planeALT()>self.startPlaneAlt):
				self.airborne = 1
				self.Transmitting = 0
				# engine feed only when flying: pre-heat recommended on ground
				for iengfeed in range(self.NumberOfEngines):
					#sec,rpm,mix,cht,altitude):
					self.ACEngine[iengfeed].feed(elapsed,self.ACEngine[iengfeed].currentRPM(),self.ACEngine[iengfeed].currentMIX(),self.ACEngine[iengfeed].currentCHT(),self.ACEngine[iengfeed].planeALT())

			# arrive
			else:
				if(self.airborne == 1):
					if(self.flightTime>self.endFlightTime and self.isAllEngineStopped() and self.ACEngine[0].planeALT()<self.endPlaneAlt):
						if(isBrake==1.0 and airspeed<float(self.endPlaneSpd)):
							print "[XFSE|Nfo] Aircraft (Plane or Heli) arrived"
							self.arrive()

			#Instruments
			if(self.stEq=="0"):
				self.setInstrAP(6)
				self.setInstrGPS(6)
				self.setInstrIFR(6)

			if(self.stEq=="1"):
				self.setInstrAP(6)
				self.setInstrGPS(6)

			if(self.stEq=="2"):
				self.setInstrAP(6)
				self.setInstrIFR(6)

			if(self.stEq=="4"):
				self.setInstrGPS(6)
				self.setInstrIFR(6)

			if(self.stEq=="3"):
				self.setInstrAP(6)

			if(self.stEq=="5"):
				self.setInstrGPS(6)

			if(self.stEq=="6"):
				self.setInstrIFR(6)

			self.setPlanePayload(self.stPayload)

			
		if(self.flying==1 and self.airborne==1 and self.Transmitting>1):
			return float(150) # unanswered call of the website lasts 2:15, call again in 150 seconds for repeating transmission
		else:
			return float(1) # call again in one second

	#############################################################
	## airborne/flight supervising function
	def startFly(self):
		if(self.flying==1):
			print "[XFSE|WRN] Start flight function is disabled"
		else:
			print "[XFSE|dbg] Start flight function"
			_INIFileW=open(os.path.join('Resources','plugins','PythonScripts','x-economy.ini'), 'w')
			_INIFileW.write(self.userstr+'\n'+self.passstr)
			_INIFileW.close()
			
			self.cancelCmdFlag = 0
			
			# Added by Egor 'SanDmaN' Pastukhov - 22.03.2010
			self.CurrentAircraft = self.ReadACAliasFromFile()
			
			if (self.CurrentAircraft == ""):
				ByteVals = []
				XPLMGetDatab(XPLMFindDataRef("sim/aircraft/view/acf_descrip"), ByteVals, 0, 500)
				self.CurrentAircraft = ByteVals[0].replace(' ','%20')

			print "[XFSE|Nfo] Current AC: " + self.CurrentAircraft

			#clear prev a/c's engines
			self.ACEngine = []

			# set up engines
			self.NumberOfEngines=int(XPLMGetDatai(XPLMFindDataRef("sim/aircraft/engine/acf_num_engines")))
			print "[XFSE|Nfo] Number of engines: " + str(self.NumberOfEngines)
			_OAT=XPLMGetDataf(XPLMFindDataRef("sim/weather/temperature_ambient_c"))

			for _iengApp in range(self.NumberOfEngines):
				self.ACEngine.append(engine(_OAT,0,0,0,_iengApp))

			#destroy captions
			for idestroy in range(len(self.FromCaption)):
				XPDestroyWidget(self,self.FromCaption[idestroy],1)
				XPDestroyWidget(self,self.ToCaption[idestroy],1)
				XPDestroyWidget(self,self.CargoCaption[idestroy],1)

			self.FromCaption=[]
			self.ToCaption=[]
			self.CargoCaption=[]

			#if self.CurrentAircraft=="":
			#	self.setInfoMessage("Unknown aircraft: "+str(ByteVals[0])+". If you're sure this is an FSE compatible aircraft,",
			#						"please edit aircraft description in Plane Maker, eg.: King Air B200. If you're not sure,",
			#						"or it's a new plane to FSE, please email to templates@fseconomy.com including the plane specs",
			#						"",
			#						"yellow")
			#else:
			PlaneLatdr = XPLMFindDataRef("sim/flightmodel/position/latitude")
			PlaneLondr = XPLMFindDataRef("sim/flightmodel/position/longitude")
			Lat = XPLMGetDataf(PlaneLatdr)
			Lon = XPLMGetDataf(PlaneLondr)

			startFlight=self.XFSEpost("user="+self.userstr+"&pass="+self.passstr+"&action=startFlight&lat="+str(Lat)+"&lon="+str(Lon)+"&aircraft="+self.CurrentAircraft.replace(' ','%20'))
			
			if startFlight.getElementsByTagName('response')[0].firstChild.nodeName=="error":
				_err=startFlight.getElementsByTagName('error')[0].firstChild.data
				_find=_err.find("is not compatible with your rented")
				#break the "is not campatible" warning down into three lines with additional information
				if _find>0:
					self.setInfoMessage("Your flight has not been started: Aircraft alias does not match!",
										"FSE=["+_err[_find+35:]+"] X-Plane=["+_err[:_find-1]+"]",
										"Pick an aircraft alias from the FSE website 'Home->Aircraft models .. Request aliases'",
										"and enter it to 'Plugins->X-Economy->Set Aircraft alias' ... or ask the forum for help!",
										"red")
				else:
					self.setInfoMessage("Your flight has not been started:",
										startFlight.getElementsByTagName('error')[0].firstChild.data,
										"",
										"",
										"red")
				
				
			else: # no error ... let's start the flight!

				stFrom="-"
				stTo="-"
				stCargo="-"
				_aMax=14 #+1 = toal 15
				
				_assignments=len(startFlight.getElementsByTagName('assignment'))
				for iAssignment in range(_assignments):
					if iAssignment<_aMax: 			# Assignments 1 - 14
						self.addAssignment(iAssignment,str(startFlight.getElementsByTagName('from')[iAssignment].firstChild.data),str(startFlight.getElementsByTagName('to')[iAssignment].firstChild.data),str(startFlight.getElementsByTagName('cargo')[iAssignment].firstChild.data))
					if iAssignment==_aMax:
						if _assignments == _aMax+1: 	# Assignments 15 is the last one
							self.addAssignment(iAssignment,str(startFlight.getElementsByTagName('from')[iAssignment].firstChild.data),str(startFlight.getElementsByTagName('to')[iAssignment].firstChild.data),str(startFlight.getElementsByTagName('cargo')[iAssignment].firstChild.data))
						else: 						# at least 2 more won't fit in the list
							self.addAssignment(iAssignment,"[...]","[...]",str((_assignments-_aMax))+ " additional assignments")

				Accounting=startFlight.getElementsByTagName('accounting')[0].firstChild.data

				self.stEq=startFlight.getElementsByTagName('equipment')[0].firstChild.data

				if(self.stEq=="0"):
					stEquipment=" (VFR)"
				if(self.stEq=="1"):
					stEquipment=" (IFR)"
				if(self.stEq=="2"):
					stEquipment=" (GPS)"
				if(self.stEq=="4"):
					stEquipment=" (AP)"
				if(self.stEq=="3"):
					stEquipment=" (IFR, GPS)"
				if(self.stEq=="5"):
					stEquipment=" (AP, IFR)"
				if(self.stEq=="6"):
					stEquipment=" (AP, GPS)"
				if(self.stEq=="7"):
					stEquipment=" (IFR, AP, GPS)"

				stACReg=startFlight.getElementsByTagName('registration')[0].firstChild.data
				stLE=startFlight.getElementsByTagName('leaseExpires')[0].firstChild.data
				XPSetWidgetDescriptor(self.ACRegCaption, "Aircraft registration: "+str(stACReg)+str(stEquipment))
		
				self.leaseTime = 0
				self.leaseTime=int(stLE)
				self.leaseStart=int(stLE)
				#XPSetWidgetDescriptor(self.LeaseCaption, "Lease time: "+str(int(stLE)/3600)+" hours")

				# set weight and fuel
				newEW=self.getPlaneEW(self.CurrentAircraft)
				self.setPlaneEW(newEW)
				self.stPayload=startFlight.getElementsByTagName('payloadWeight')[0].firstChild.data
				stFuel=startFlight.getElementsByTagName('fuel')[0].firstChild.data
				self.setPlanePayload(self.stPayload)
				astFuel=stFuel.split(' ')

				self.FuelTanks=[]
				totalFuel=float(0)
				for iFuel in range(len(astFuel)-1):
					totalFuel+=float(astFuel[iFuel])
					if float(astFuel[iFuel])>float(0):
						self.FuelTanks.append(1)
					else:
						self.FuelTanks.append(0)
						
				num_tanks = 9 	#XPLMGetDatai(XPLMFindDataRef("sim/aircraft/overflow/acf_num_tanks")) # thx sandy barbour :)
								#num_tanks can be set to "max", all not used tanks will have a value of 0 as multiplier
								
				currentFuel = totalFuel*float(2.68735)

				_fuelPerTanks = []
				_currentRatio = []
				XPLMGetDatavf(XPLMFindDataRef("sim/aircraft/overflow/acf_tank_rat"),_currentRatio,0,num_tanks)
				for _it in range(num_tanks):
					_fuelPerTanks.append(currentFuel*_currentRatio[_it])								

				XPLMSetDatavf(XPLMFindDataRef("sim/flightmodel/weight/m_fuel"),_fuelPerTanks,0,num_tanks)

				self.checkfuel=XPLMGetDataf(XPLMFindDataRef("sim/flightmodel/weight/m_fuel_total"))

				_fuelTotalGal=int((XPLMGetDataf(XPLMFindDataRef("sim/flightmodel/weight/m_fuel_total")) * 0.3721)+0.5)
				
				XPSetWidgetProperty(self.StartFlyButton, xpProperty_Enabled, 0)
				XPSetWidgetProperty(self.CancelFlyButton, xpProperty_Enabled, 1)

				self.Arrived=0
				self.flightStart = int( XPLMGetDataf(XPLMFindDataRef("sim/time/total_flight_time_sec")) )
				self.flightTimerLast=self.flightTimer #sync timer diffs
				self.flightTime = 0
				self.flying=1 # start flight query
				self.airborne=0
				self.gsCheat = 0

				XPSetWidgetDescriptor(self.ServerResponseCaption, "")
				
				self.setInfoMessage("Your flight has been started:",
									str(_fuelTotalGal)+" gallons of fuel onboard.",
									str(_assignments)+" assignments loaded.",
									"Enjoy your flight!",
									"green")
									
				for iengclear in range(self.NumberOfEngines):
					self.ACEngine[iengclear].clearEng()

			return 1

	#############################################################
	## arrival function
	def arrive(self):
		print "[XFSE|dbg] Arrive()"
		if self.Arrived==0:
			if self.leaseTime>0:

				print "[XFSE|Nfo] Flight has arrived"

				#XPSetWidgetDescriptor(self.LeaseCaption, "")
				XPSetWidgetDescriptor(self.EndFlightCaption, "Flight has ended ...")
				
				self.Transmitting=self.Transmitting+1
				XPSetWidgetDescriptor(self.ServerResponseCaption, "Transmitting (Try "+str(self.Transmitting)+") ...")
				if (self.Transmitting==2): #open the window to let the user know that 1st try failed
					XPShowWidget(self.XFSEWidget)
				
				_PlaneLatdr = XPLMFindDataRef("sim/flightmodel/position/latitude")
				_PlaneLondr = XPLMFindDataRef("sim/flightmodel/position/longitude")
				_lat = XPLMGetDataf(_PlaneLatdr)
				_lon = XPLMGetDataf(_PlaneLondr)

				_totalfuel = 0

				num_tanks = 9 	#XPLMGetDatai(XPLMFindDataRef("sim/aircraft/overflow/acf_num_tanks")) # thx sandy barbour :)
								#num_tanks can be set to "max", all not used tanks will have a value of 0 as multiplier
				_fueltanksQTY = []
				XPLMGetDatavf(XPLMFindDataRef("sim/flightmodel/weight/m_fuel"),_fueltanksQTY,0,num_tanks)
				for _iTotFuel in range(num_tanks):
					_totalfuel = _totalfuel + _fueltanksQTY[_iTotFuel]/float(2.68735)

				print "[XFSE|Nfo] Fuel at arrival: "+str(_totalfuel)
				
				_iFuel=0
				_actfueltanks=float(0)
				for _iFuel in range(len(self.FuelTanks)):
					if self.FuelTanks[_iFuel]==1:
						_actfueltanks=_actfueltanks+1
				_iFuel=0
				_fuelarray=[]
				_eachfuel=_totalfuel/float(_actfueltanks) # thx no2 jck :)
				for _iFuel in range(len(self.FuelTanks)):
					if self.FuelTanks[_iFuel]==0:
						_fuelarray.append(0)
					else:
						_fuelarray.append(_eachfuel)

				_c=_fuelarray[0]
				_lm=_fuelarray[1]
				_la=_fuelarray[2]
				_let=_fuelarray[3]
				_rm=_fuelarray[4]
				_ra=_fuelarray[5]
				_rt=_fuelarray[6]
				_c2=_fuelarray[7]
				_c3=_fuelarray[8]
				_x1=_fuelarray[9]
				_x2=_fuelarray[10]

				_engineStr=""
				for _ieng in range(self.NumberOfEngines):
					_engineStr=_engineStr+str(self.ACEngine[_ieng].getData(self.flightTime))
					
				print "[XFSE|Nfo] Engine conditions: "+_engineStr

				print "[XFSE|Nfo] Sending flight to the server ..."
				
				_finishflight=self.XFSEpost("user="+self.userstr+"&pass="+self.passstr+"&action=arrive&rentalTime="+str(self.flightTime)+"&lat="+str(_lat)+"&lon="+str(_lon)+"&c="+str(_c)+"&lm="+str(_lm)+"&la="+str(_la)+"&let="+str(_let)+"&rm="+str(_rm)+"&ra="+str(_ra)+"&rt="+str(_rt)+"&c2="+str(_c2)+"&c3="+str(_c3)+"&x1="+str(_x1)+"&x2="+str(_x2)+_engineStr)

				if len(_finishflight.getElementsByTagName('result'))>0:

					_err=_finishflight.getElementsByTagName('result')[0].firstChild.data
					print "[XFSE|Nfo] Server returned: "+_err

					#replace pipe by space
					_err=_err.replace('|', ' ')
					
					#split string into an array
					_errA=_err.split(' ')
					#append the spaces again
					for ierr in range(len(_errA)-1):
						_errA[ierr]=_errA[ierr]+" "

					#concat string up to a length of 80 chars max again
					ierr=0
					while ierr<len(_errA)-1:
						if(len(_errA[ierr])+len(_errA[ierr+1])<=80):
							_errA[ierr]=_errA[ierr]+_errA.pop(ierr+1) #append _errA[ierr+1] and delete it
						else:
							ierr=ierr+1

					#trim all strings
					for ierr in range(len(_errA)):
						_errA[ierr]=_errA[ierr].strip();
							
					#fill up the error text array to have at least 4 lines
					linesAdd=4-len(_errA)
					for ierr in range(linesAdd):
						_errA.append("")

					if(_errA[0].find("Your flight is logged and the results can be found at the website")==0):
						self.errorcolor="green"
						# fill err4 with more useful information
						_currhours=self.flightTime/3600
						_currmins=(self.flightTime-_currhours*3600)/60
						_fuelTotalGal=int((XPLMGetDataf(XPLMFindDataRef("sim/flightmodel/weight/m_fuel_total")) * 0.3721)+0.5)

						_currhourstot=str(_currhours)
						if(_currhours<10):
							_currhourstot="0"+_currhourstot

						_currminstot=str(_currmins)
						if(_currmins<10):
							_currminstot="0"+_currminstot
						
						self.setInfoMessage(_errA[0],
											_errA[1],
											_errA[2],
											"Total Flight time "+_currhourstot+":"+_currminstot+". Still "+str(_fuelTotalGal)+" gallons of fuel onboard.",
											"green")
					else:
						self.setInfoMessage(_errA[0],
											_errA[1],
											_errA[2],
											_errA[3],
											"red")
						
					XPSetWidgetProperty(self.StartFlyButton, xpProperty_Enabled, 1)
					XPSetWidgetProperty(self.CancelFlyButton, xpProperty_Enabled, 0)
					self.flying=0
					self.airborne=0
					self.Arrived=1

					print "[XFSE|dbg] Flight time reset. All instruments enabled"
					self.flightStart=0
					self.flightTime=0
					self.enableAllInstruments()
					self.stPayload=0
					self.setPlanePayload(self.stPayload)
					self.setPlaneEW(self.stockEW)

					XPSetWidgetDescriptor(self.ServerResponseCaption, "Transmitting (Try "+str(self.Transmitting)+") ... OK")
				else:
					print "[XFSE|WRN] Flight logging NOT complete. Check your internet connection to the FSE-Server and try again."
					
			else:
				print "[XFSE|Nfo] Lease time has ended, cancelling flight"
				self.cancelFlight("Lease time has ended. Your flight has been cancelled. Sorry, you will have to re-fly this trip","")
				
	#############################################################
	## Flight cancel function
	def cancelFlight(self,message,message2):
		if(self.flying==0):
			print "[XFSE|WRN] Cancel flight function (BTN) is disabled"
		else:
			print "[XFSE|dbg] Cancel flight function"
			self.flying=0
			self.airborne=0

			cancelflight=self.XFSEpost("user="+self.userstr+"&pass="+self.passstr+"&action=cancel")
			if (cancelflight.getElementsByTagName('response')[0].firstChild.nodeName=="ok"):
				XPSetWidgetProperty(self.StartFlyButton, xpProperty_Enabled, 1)
				XPSetWidgetProperty(self.CancelFlyButton, xpProperty_Enabled, 0)
				self.setInfoMessage(message,
									message2,
									"",
									"",
									"red")
				
			print "[XFSE|dbg] Cancel flight1: [" + message + "][" + message2 + "]"
			XPSetWidgetDescriptor(self.LeaseCaption, "")
			XPSetWidgetDescriptor(self.EndFlightCaption, "")
			self.enableAllInstruments()
			self.stPayload=0
			self.setPlanePayload(self.stPayload)
			self.setPlaneEW(self.stockEW)

	#############################################################
	## login function
	def login(self):
		if(self.connected==1):
			print "[XFSE|WRN] login function (BTN) is disabled"
		else:
			Buffer = []
			XPGetWidgetDescriptor(self.LoginUserEdit,Buffer,256)
			XPGetWidgetDescriptor(self.LoginPassEdit,Buffer,256)
			self.userstr=Buffer[0]
			self.passstr=Buffer[1]
			logincheck=self.XFSEpost("user="+self.userstr+"&pass="+self.passstr+"&action=accountCheck")
			print "[XFSE|Nfo] Logincheck"

			if (logincheck.getElementsByTagName('response')[0].firstChild.nodeName=="ok"):
				print "[XFSE|Nfo] Login successful"
				XPSetWidgetDescriptor(self.ServerResponseCaption, "Logged in!")
				self.connected=1
				XPSetWidgetProperty(self.LoginButton, xpProperty_Enabled, 0)
				XPSetWidgetProperty(self.StartFlyButton, xpProperty_Enabled, 1)
				self.setInfoMessage("Logged in!",
									"",
									"",
									"",
									"green")
			else:
				print "[XFSE|Nfo] Login was not successful"
				if(logincheck.getElementsByTagName('response')[0].firstChild.nodeName=="error"):
					print "[XFSE|Nfo] Invalid script"
					XPSetWidgetDescriptor(self.ServerResponseCaption, "Error!")
					self.setInfoMessage(logincheck.getElementsByTagName('error')[0].firstChild.data,
										"",
										"",
										"",
										"red")
				else:
					if(logincheck.getElementsByTagName('response')[0].firstChild.nodeName=="notok"):
						print "[XFSE|Nfo] New version avail"
						XPSetWidgetDescriptor(self.ServerResponseCaption, "Update available!")
						XPSetWidgetProperty(self.UpdateButton, xpProperty_Enabled, 1)
						self.setInfoMessage("!!! New version is available: v"+str(logincheck.getElementsByTagName('notok')[0].firstChild.data),
											"",
											"",
											"",
											"red")
					else:
						print "[XFSE|Nfo] Invalid account"
						XPSetWidgetDescriptor(self.ServerResponseCaption, "Invalid account!")
						self.setInfoMessage("Invalid account!",
											"",
											"",
											"",
											"red")
		return 1

	#############################################################
	## update function
	def doUpdate(self):
		_newClient = urlopen('http://www.fseconomy.net/download/client/xfse/PI_xfse.py').read()
		_oldClient=open(os.path.join('Resources','plugins','PythonScripts','PI_xfse.py'), 'w')
		_oldClient.write(_newClient)
		_oldClient.close()
		self.setInfoMessage("Your client is updated, please restart X-Plane,"
							"or reload plugins via Plugins / Python Interface / Control Panel"
							"",
							"",
							"yellow")
		self.errormessage = 100
		
	#############################################################
	## Start Flight Assignment Helper function
	def addAssignment(self,aIndex,aFrom,aTo,aCargo):
		print "[XFSE|Nfo] Adding assignment #" + str(aIndex) +", From: "+ str(aFrom) +", To: "+ str(aTo) +", Cargo: "+ str(aCargo)
		_baseY1=(aIndex+1)*18+120
		_baseY2=(aIndex+1)*28+120
		oLeft=[]
		oTop=[]
		oRight=[]
		oBottom=[]
		XPGetWidgetGeometry(self.XFSEWidget,oLeft,oTop,oRight,oBottom)
		y=oTop[0]
		x=oLeft[0]
		_offset=10
		self.FromCaption.append(XPCreateWidget(x+20, 	y-_baseY1+_offset*aIndex, x+50, 	y-_baseY2+_offset*aIndex,1, "From: -", 0, self.XFSEWidget,xpWidgetClass_Caption))
		self.ToCaption.append(XPCreateWidget(x+140, 	y-_baseY1+_offset*aIndex, x+170, 	y-_baseY2+_offset*aIndex,1, "To: -", 0, self.XFSEWidget,xpWidgetClass_Caption))
		self.CargoCaption.append(XPCreateWidget(x+210, 	y-_baseY1+_offset*aIndex, x+240,	y-_baseY2+_offset*aIndex,1, "Cargo: -", 0, self.XFSEWidget,xpWidgetClass_Caption))
		XPSetWidgetDescriptor(self.FromCaption[aIndex], str(aFrom))
		XPSetWidgetDescriptor(self.ToCaption[aIndex], str(aTo))
		XPSetWidgetDescriptor(self.CargoCaption[aIndex], str(aCargo))

	#The End
