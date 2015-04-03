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

class PythonInterface:

	def getSign(self, val): #Puts a plus sign in front of positive values
		sign=""
		if val>0:
			sign="+"
		return sign
	
	def getAlt(self, SL, AM): #Determines altitude based on pressure delta
		alt=1000*(SL-AM)
		return alt
	
	def setBaro(self, bar_new): #Set the barometer
		bar_old=XPLMGetDataf(self.baro_set_ref)
		XPLMSetDataf(self.baro_set_ref, bar_new)
		del_baro_set=bar_new-bar_old
		del_baro_str=self.getSign(del_baro_set)+str(round(del_baro_set,2))
		if self.inHg==1:
			baro_str=str(round(bar_new,2))
			del_baro_str=self.getSign(del_baro_set)+str(round(del_baro_set,2))+" inHg"
		else:
			baro_str=str(round(bar_new*self.inhghpa))
			del_baro_str=self.getSign(del_baro_set)+str(round(del_baro_set*self.inhghpa))+" hPa"
		self.msg1="Altimeter  " +baro_str+"  "+del_baro_str
		self.remainingShowTime=self.showTime
		pass
	
	def showBaro(self, bar): #Show the barometer setting
		self.msg1="Altimeter  "+self.getBaroString(bar)
		self.remainingShowTime=self.showTime
		pass
	
	def getBaroString(self, bar): #Get string with setting in inHg or hPa
		if self.inHg==1:
			string=str(round(bar,2))+" inHg"
		else:
			string=str(round(bar*self.inhghpa))+" hPa"
		return string

	def XPluginStart(self):
		self.Name="Altimeter Helper 1.3.1"
		self.Sig= "natt.python.altimeterhelper"
		self.Desc="A plugin that helps with altimeter settings"
		self.VERSION="1.3.1"
		
		self.baro_set_ref=XPLMFindDataRef("sim/cockpit/misc/barometer_setting")
		self.baro_act_ref=XPLMFindDataRef("sim/weather/barometer_sealevel_inhg")
		self.alt_act_ref=XPLMFindDataRef("sim/flightmodel/position/elevation")
		self.alt_ind_ref=XPLMFindDataRef("sim/flightmodel/misc/h_ind")
		self.vvi_ref=XPLMFindDataRef("sim/flightmodel/position/vh_ind_fpm")
		
		self.mft=3.2808399 #m -> ft
		self.inhghpa=33.8638866667 #inHg -> hPa
		self.msg1=""
		self.remainingShowTime=0
		self.showTime=3 #Seconds to show the altimeter setting when changed
		winPosX=20
		winPosY=500
		win_w=200
		win_h=35
		self.stdpress=0 #Whether standard pressure is set
		_TAINI,_ErrINI,_HgINI=self.ReadSFromFile()
		self.trans_alt=18000 #Transition altitude
		self.err=1 #Whether to show altitude error
		self.trans_alt=int(_TAINI)
		self.err=int(_ErrINI)
		self.inHg=int(_HgINI)
		self.tol=[17.009, 0.0058579, -0.000000012525] #Parameters for altimeter tolerance
		self.last_bar=XPLMGetDataf(self.baro_set_ref)

		self.DrawWindowCB=self.DrawWindowCallback
		self.KeyCB=self.KeyCallback
		self.MouseClickCB=self.MouseClickCallback
		self.gWindow=XPLMCreateWindow(self, winPosX, winPosY, winPosX + win_w, winPosY - win_h, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)
		
		self.gameLoopCB=self.gameLoopCallback
		XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 1, 0)
		
		self.CmdSHConn = XPLMCreateCommand("althelp/set_altimeter","Sets altimeter for current position and altitude")
		self.CmdSHConnCB  = self.CmdSHConnCallback
		XPLMRegisterCommandHandler(self, self.CmdSHConn,  self.CmdSHConnCB, 0, 0)
		
		self.MenuItem1 = 0			#Flag if main window has already been created
		Item = XPLMAppendMenuItem(XPLMFindPluginsMenu(), "Altimeter Helper", 0, 1)
		self.SMenuHandlerCB = self.SMenuHandler
		self.Id = XPLMCreateMenu(self, "Altimeter Helper" , XPLMFindPluginsMenu(), Item, self.SMenuHandlerCB,	0)
		XPLMAppendMenuItem(self.Id, "Settings", 1, 1)
		
		#Create the Main Window Widget
		self.CreateSWidget(221, 640, 200, 100)
		self.MenuItem1 = 1
		XPHideWidget(self.SWidget)
		
		return self.Name, self.Sig, self.Desc

	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def CmdSHConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "AltHelper = CMD set altimeter"
			if XPLMGetDataf(self.alt_ind_ref) > self.trans_alt:
				newbaro=29.92
			else:
				newbaro=XPLMGetDataf(self.baro_act_ref)
			if round(newbaro,2)!=round(XPLMGetDataf(self.baro_set_ref),2):
				self.last_bar=newbaro
				self.setBaro(newbaro)
			else:
				self.showBaro(newbaro)
		return 0

	def DrawWindowCallback(self, inWindowID, inRefcon):
		if self.remainingShowTime > 0:
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
		XPLMDestroyWindow(self, self.SWindowId)
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
		_TAINI,_ErrINI,_HgINI=self.ReadSFromFile()

		self.globalX=x
		self.globalY=y
		x2 = x + w
		y2 = y - h
		
		Title = "Altimeter Helper v"+str(self.VERSION)

		# Create the Main Widget window
		self.SWidget = XPCreateWidget(x, y, x2, y2, 1, Title, 1,	0, xpWidgetClass_MainWindow)

		# Add Close Box decorations to the Main Widget
		XPSetWidgetProperty(self.SWidget, xpProperty_MainWindowHasCloseBoxes, 1)

		# TA caption
		TACaption = XPCreateWidget(x+20, y-40, x+50, y-60,1, "Transition altitude:", 0, self.SWidget,xpWidgetClass_Caption)

		# TA field
		self.TAEdit = XPCreateWidget(x+80, y-40, x+160, y-60,1, _TAINI, 0, self.SWidget,xpWidgetClass_TextField)
		XPSetWidgetProperty(self.TAEdit, xpProperty_TextFieldType, xpTextEntryField)
		XPSetWidgetProperty(self.TAEdit, xpProperty_Enabled, 1)

		# Err caption
		ErrCaption = XPCreateWidget(x+20, y-60, x+50, y-80,1, "Altimeter error warning:", 0, self.SWidget,xpWidgetClass_Caption)

		# Error option
		self.ErrOpt = XPCreateWidget(x+80, y-60, x+160, y-80,1, "ErrOpt", 0, self.SWidget,xpWidgetClass_Button)
		XPSetWidgetProperty(self.ErrOpt, xpProperty_ButtonType, xpRadioButton)
		XPSetWidgetProperty(self.ErrOpt, xpProperty_ButtonBehavior, xpButtonBehaviorCheckBox)
		XPSetWidgetProperty(self.ErrOpt, xpProperty_ButtonState, _ErrINI)
		
		# Units caption
		HgCaption = XPCreateWidget(x+20, y-60, x+50, y-80,1, "Display inHg:", 0, self.SWidget,xpWidgetClass_Caption)

		# Units option
		self.HgOpt = XPCreateWidget(x+80, y-80, x+160, y-100,1, "HgOpt", 0, self.SWidget,xpWidgetClass_Button)
		XPSetWidgetProperty(self.HgOpt, xpProperty_ButtonType, xpRadioButton)
		XPSetWidgetProperty(self.HgOpt, xpProperty_ButtonBehavior, xpButtonBehaviorCheckBox)
		XPSetWidgetProperty(self.HgOpt, xpProperty_ButtonState, _HgINI)

		# Save button
		self.SaveButton = XPCreateWidget(x+180, y-40, x+260, y-60,1, "Save", 0, self.SWidget,xpWidgetClass_Button)
		XPSetWidgetProperty(self.SaveButton, xpProperty_ButtonType, xpPushButton)
		
		# Register our widget handler
		self.SHandlerCB = self.SHandler
		XPAddWidgetCallback(self, self.SWidget, self.SHandlerCB)

	def SHandler(self, inMessage, inWidget,    inParam1, inParam2):
		if (inMessage == xpMessage_CloseButtonPushed):
			print "ALTHELP | Client window closed"
			if (self.MenuItem1 == 1):
				XPHideWidget(self.SWidget)
				return 1

		if (inMessage == xpMsg_PushButtonPressed):
			if (inParam1 == self.SaveButton):
				print "ALTHELP | Saving settings"
				TA = []
				XPGetWidgetDescriptor(self.TAEdit, TA, 256)
				Err=XPGetWidgetProperty(self.ErrOpt, xpProperty_ButtonState, None)
				inHg=XPGetWidgetProperty(self.HgOpt, xpProperty_ButtonState, None)
				self.WriteSToFile(TA[0],Err,inHg)
				self.trans_alt=int(TA[0])
				self.err=int(Err)
				self.inHg=int(inHg)
				XPHideWidget(self.SWidget)
				return 1

		if (inMessage == xpMsg_Shown):
			TA, Err, inHg = self.ReadSFromFile()
			XPSetWidgetDescriptor(self.TAEdit, TA)
			XPSetWidgetProperty(self.ErrOpt, xpProperty_ButtonState, Err)
			XPSetWidgetProperty(self.HgOpt, xpProperty_ButtonState, inHg)
			return 1
				
		return 0

	def ReadSFromFile(self):
		SFile = os.path.join('Resources','plugins','PythonScripts','altimeterhelper.ini')
		if (os.path.exists(SFile) and os.path.isfile(SFile)):
			fd = open(SFile, 'r')
			_TAINI=fd.readline()
			_TAINI=_TAINI.replace('\n','')
			_ErrINI=fd.readline()
			_ErrINI=_ErrINI.replace('\n','')
			_HgINI=fd.readline()
			fd.close()
			return _TAINI,_ErrINI,_HgINI
		return "",""

	def WriteSToFile(self, TA, Err, inHg):
		SFile = os.path.join('Resources','plugins','PythonScripts','altimeterhelper.ini')
		fd = open(SFile, 'wb')
		fd.write(TA+'\n'+Err+'\n'+inHg)
		fd.close()

	def SMenuHandler(self, inMenuRef, inItemRef):
		# If menu selected create our widget dialog
		if (inItemRef == 1):
			if (self.MenuItem1 == 0):
				self.CreateSWidget(221, 640, 200, 100)
				self.MenuItem1 = 1
			else:
				if(not XPIsWidgetVisible(self.SWidget)):
					XPShowWidget(self.SWidget)

	def gameLoopCallback(self, inElapsedSinceLastCall, elapsedSim, counter, refcon):
		if 0.0 < self.remainingShowTime:
			self.remainingShowTime -= inElapsedSinceLastCall
		
		alt=XPLMGetDataf(self.alt_ind_ref) #Indicated altitude, ft
		vvi=XPLMGetDataf(self.vvi_ref) #Vertical speed, fpm
		alt_act=XPLMGetDataf(self.alt_act_ref)*self.mft #Real altitude, convert to ft
		bar=XPLMGetDataf(self.baro_set_ref) #Current altimeter setting
		bar_act=XPLMGetDataf(self.baro_act_ref) #Current local sea level pressure
		
		if (vvi >= 500 and alt >= (self.trans_alt-25) or 0 < vvi < 500 and alt > self.trans_alt + 250) and self.stdpress==0: # Climbing through TA
			bar=29.92
			self.stdpress=1
			self.setBaro(bar)
		elif (vvi <= -500 and alt < (self.trans_alt-25) or 0 > vvi > -500 and alt < self.trans_alt - 250) and self.stdpress==1: # Descending through TL
			bar=XPLMGetDataf(self.baro_act_ref)
			self.stdpress=0
			self.setBaro(bar)
		
		alt_err=self.getAlt(bar-bar_act,0)
		alt_err=(alt-alt_act)
		tolerance=self.tol[2]*alt**2+self.tol[1]*alt+self.tol[0] #Determine altimeter error tolerance
		if abs(alt_err)>tolerance and self.stdpress==0 and self.err==1:
			alt_err_str=self.getSign(alt_err)+str(round(alt_err))
			self.msg1="Local QNH "+getBaroString(bar_act)+", "+alt_err_str+" feet!"
			self.remainingShowTime=self.showTime
		
		if round(self.last_bar,2)!=round(bar,2):
			self.showBaro(bar)

		self.last_bar=bar
		
		return 0.1
