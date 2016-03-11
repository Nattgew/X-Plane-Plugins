from XPLMMenus import *
from XPWidgetDefs import *
from XPWidgets import *
from XPStandardWidgets import *
from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMDisplay import *
from XPLMGraphics import *
from XPLMUtilities import *
from XPLMDefs import *
#import os

class PythonInterface:

	def XPluginStart(self):
		self.Name="TOD Alert 0.1"
		self.Sig= "natt.python.todalert"
		self.Desc="Alert or pause when reaching TOD distance"
		self.VERSION="0.1"
		
		self.gps_dist_ref=XPLMFindDataRef("sim/cockpit/radios/gps_dme_dist_m")
		self.alt_ref=XPLMFindDataRef("sim/flightmodel/position/elevation")
		
		self.pause_cmd=XPLMFindCommand("sim/operation/pause_toggle")
		
		self.mft=3.2808399 # m to ft
		self.alertdist=0 #Distance from destination to take action
		self.armed=0 #Whether alarm is armed
		self.pause=1 #Whether sim is paused
		self.sound=0 #Whether sound is played (in work)
		self.alarm=0 #Whether alarm is currently triggered
		self.msg1=""
		winPosX=20
		winPosY=500
		win_w=250
		win_h=45

		self.DrawWindowCB=self.DrawWindowCallback
		self.KeyCB=self.KeyCallback
		self.MouseClickCB=self.MouseClickCallback
		self.gWindow=XPLMCreateWindow(self, winPosX, winPosY, winPosX + win_w, winPosY - win_h, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)
		
		self.gameLoopCB=self.gameLoopCallback
		XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 1, 0)
		
		self.CmdSHConn = XPLMCreateCommand("todalert/armed","Toggles whether alarm is armed")
		self.CmdSHConnCB  = self.CmdSHConnCallback
		XPLMRegisterCommandHandler(self, self.CmdSHConn,  self.CmdSHConnCB, 0, 0)
		
		self.MenuItem1 = 0			#Flag if main window has already been created
		Item = XPLMAppendMenuItem(XPLMFindPluginsMenu(), "TOD Alert", 0, 1)
		self.SMenuHandlerCB = self.SMenuHandler
		self.Id = XPLMCreateMenu(self, "TOD Alert" , XPLMFindPluginsMenu(), Item, self.SMenuHandlerCB,	0)
		XPLMAppendMenuItem(self.Id, "Settings", 1, 1)
		
		#Create the Main Window Widget
		self.CreateSWidget(221, 640, 210, 135)
		self.MenuItem1 = 1
		XPHideWidget(self.SWidget)
		
		return self.Name, self.Sig, self.Desc

	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def CmdSHConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "TODALERT = CMD set altimeter"
		return 0

	def DrawWindowCallback(self, inWindowID, inRefcon):
		if self.alarm > 0:
			lLeft=[];	lTop=[];	lRight=[];	lBottom=[]
			XPLMGetWindowGeometry(inWindowID, lLeft, lTop, lRight, lBottom)
			left=int(lLeft[0]); top=int(lTop[0]); right=int(lRight[0]); bottom=int(lBottom[0])
			XPLMDrawTranslucentDarkBox(left,top,right,bottom)
			color=1.0, 1.0, 1.0
			gResult=XPLMDrawString(color, left+5, top-20, self.msg1, 0, xplmFont_Basic)

	def XPluginStop(self):
		XPLMUnregisterCommandHandler(self, self.CmdSHConn, self.CmdSHConnCB, 0, 0)
		XPLMUnregisterFlightLoopCallback(self, self.gameLoopCB, 0);
		XPLMDestroyWindow(self, self.gWindow)
		
		if (self.MenuItem1 == 1):
			XPDestroyWidget(self, self.SWidget, 1)
			self.MenuItem1 = 0
		XPLMDestroyMenu(self, self.Id)
		pass

	def XPluginEnable(self):
		return 1

	def XPluginDisable(self):
		pass

	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass
	
	#############################################################
	## GUI Creation Handler
	def CreateSWidget(self, x, y, w, h):

		self.globalX=x
		self.globalY=y
		x2 = x + w
		y2 = y - h
		
		Title = "TOD Alert v"+str(self.VERSION)

		# Create the Main Widget window
		self.SWidget = XPCreateWidget(x, y, x2, y2, 1, Title, 1, 0, xpWidgetClass_MainWindow)

		# Add Close Box decorations to the Main Widget
		XPSetWidgetProperty(self.SWidget, xpProperty_MainWindowHasCloseBoxes, 1)

		# TOD caption
		TODcaption = XPCreateWidget(x+20, y-30, x+50, y-50,1, "TOD (nmi)", 0, self.SWidget,xpWidgetClass_Caption)

		# TOD field
		self.TODedit = XPCreateWidget(x+130, y-30, x+185, y-50,1, _TAINI, 0, self.SWidget,xpWidgetClass_TextField)
		XPSetWidgetProperty(self.TODedit, xpProperty_TextFieldType, xpTextEntryField)
		XPSetWidgetProperty(self.TODedit, xpProperty_Enabled, 1)

		# Arm caption
		ArmCaption = XPCreateWidget(x+20, y-50, x+50, y-70,1, "Armed", 0, self.SWidget,xpWidgetClass_Caption)

		# Arm option
		self.ArmOpt = XPCreateWidget(x+140, y-50, x+210, y-70,1, "", 0, self.SWidget,xpWidgetClass_Button)
		XPSetWidgetProperty(self.ArmOpt, xpProperty_ButtonType, xpRadioButton)
		XPSetWidgetProperty(self.ArmOpt, xpProperty_ButtonBehavior, xpButtonBehaviorCheckBox)
		XPSetWidgetProperty(self.ArmOpt, xpProperty_ButtonState, 0)
		#XPSetWidgetProperty(self.ArmOpt, xpProperty_ButtonState, int(_ErrINI))
		
		# Pause caption
		PauseCaption = XPCreateWidget(x+20, y-70, x+50, y-90,1, "Pause sim", 0, self.SWidget,xpWidgetClass_Caption)

		# Pause option
		self.PauseOpt = XPCreateWidget(x+140, y-70, x+210, y-90,1, "", 0, self.SWidget,xpWidgetClass_Button)
		XPSetWidgetProperty(self.PauseOpt, xpProperty_ButtonType, xpRadioButton)
		XPSetWidgetProperty(self.PauseOpt, xpProperty_ButtonBehavior, xpButtonBehaviorCheckBox)
		XPSetWidgetProperty(self.PauseOpt, xpProperty_ButtonState, 1)
		#XPSetWidgetProperty(self.PauseOpt, xpProperty_ButtonState, int(_HgINI))

		# Sound caption
		SoundCaption = XPCreateWidget(x+20, y-90, x+50, y-110,1, "Play sound", 0, self.SWidget,xpWidgetClass_Caption)

		# Pause option
		self.SoundOpt = XPCreateWidget(x+140, y-90, x+210, y-110,1, "", 0, self.SWidget,xpWidgetClass_Button)
		XPSetWidgetProperty(self.SoundOpt, xpProperty_ButtonType, xpRadioButton)
		XPSetWidgetProperty(self.SoundOpt, xpProperty_ButtonBehavior, xpButtonBehaviorCheckBox)
		XPSetWidgetProperty(self.SoundOpt, xpProperty_ButtonState, 0)
		#XPSetWidgetProperty(self.SoundOpt, xpProperty_ButtonState, int(_HgINI))
		
		# Save button
		self.SaveButton = XPCreateWidget(x+70, y-120, x+150, y-140,1, "Save", 0, self.SWidget,xpWidgetClass_Button)
		XPSetWidgetProperty(self.SaveButton, xpProperty_ButtonType, xpPushButton)
		
		# Register our widget handler
		self.SHandlerCB = self.SHandler
		XPAddWidgetCallback(self, self.SWidget, self.SHandlerCB)

	def SHandler(self, inMessage, inWidget,    inParam1, inParam2):
		if (inMessage == xpMessage_CloseButtonPushed):
			print "TODALERT | Client window closed"
			if (self.MenuItem1 == 1):
				XPHideWidget(self.SWidget)
				return 1

		if (inMessage == xpMsg_PushButtonPressed):
			if (inParam1 == self.SaveButton):
				print "TODALERT | Saving settings"
				TOD = []
				XPGetWidgetDescriptor(self.TODedit, TOD, 256)
				armbox=XPGetWidgetProperty(self.ArmOpt, xpProperty_ButtonState, None)
				pausebox=XPGetWidgetProperty(self.PauseOpt, xpProperty_ButtonState, None)
				#soundbox=XPGetWidgetProperty(self.SoundOpt, xpProperty_ButtonState, None)
				self.alertdist=int(TOD[0])
				self.armed=int(armbox)
				self.pause=int(pausebox)
				#self.sound=int(soundbox)
				XPHideWidget(self.SWidget)
				return 1

		if (inMessage == xpMsg_Shown):
			XPSetWidgetDescriptor(self.TODedit, self.alertdist)
			XPSetWidgetProperty(self.ArmOpt, xpProperty_ButtonState, int(self.armed))
			XPSetWidgetProperty(self.PauseOpt, xpProperty_ButtonState, int(self.pause))
			XPSetWidgetProperty(self.SoundOpt, xpProperty_ButtonState, int(self.sound))
			return 1
				
		return 0

		def SMenuHandler(self, inMenuRef, inItemRef):
		# If menu selected create our widget dialog
		if (inItemRef == 1):
			if (self.MenuItem1 == 0):
				self.CreateSWidget(221, 640, 210, 135)
				self.MenuItem1 = 1
			else:
				if(not XPIsWidgetVisible(self.SWidget)):
					XPShowWidget(self.SWidget)

	def gameLoopCallback(self, inElapsedSinceLastCall, elapsedSim, counter, refcon):
		
		dist=XPLMGetDataf(self.gps_dist_ref)
		if self.armed==1 and dist<self.alertdist:
			self.alarm=1
			self.msg1="Currently "+str(int(round(dist)))+" nmi from dest!"
			if self.pause==1:
				self.msg1+=" Sim paused!"
				XPLMCommandOnce(self.pause_cmd)
		else:
			self.alarm=0
		
		return 15
