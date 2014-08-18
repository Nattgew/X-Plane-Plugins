from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMDisplay import *
from XPLMGraphics import *
from XPLMDefs import *

class PythonInterface:

	def XPluginStart(self):
		self.Name="XFSE Damage Info"
		self.Sig= "natt.python.damaged"
		self.Desc="Shows damage info FSE would calculate"
		self.VERSION="1.0"
		
		self.OAT_ref=XPLMFindDataRef("sim/weather/temperature_ambient_c")
		self.RPM_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_N2_")
		self.CHT_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_CHT_c")
		self.mix_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_mixt")
		self.flightTime_ref=XPLMFindDataRef("sim/time/total_flight_time_sec")
		self.num_eng_ref=XPLMFindDataRef("sim/aircraft/engine/acf_num_engines")
		self.alt_ref=XPLMFindDataRef("sim/flightmodel/position/y_agl")
		
		self.gWindow=0
		self.msg1=""
		self.msg2=""
		self.msg3=""
		self.remainingShowTime=0
		self.showTime=1
		self.winPosX=20
		self.winPosY=600
		self.WINDOW_WIDTH=130
		self.WINDOW_HEIGHT=80
		self.windowCloseRequest=0
		self.defaultcht=-100 #absurd... right? ... right?
		self.num_eng=0
		self.runtime=0
		self.chtDamage=0
		self.mixtureDamage=0

		self.DrawWindowCB=self.DrawWindowCallback
		self.KeyCB=self.KeyCallback
		self.MouseClickCB=self.MouseClickCallback
		#self.WindowId=XPLMCreateWindow(self, 50, 600, 300, 400, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)

		self.MyHotKeyCB=self.MyHotKeyCallback
		self.gHotKey=XPLMRegisterHotKey(self, XPLM_VK_D, xplm_DownFlag+xplm_ShiftFlag+xplm_ControlFlag, "Shows FSE damage info", self.MyHotKeyCB, 0)
		
		return self.Name, self.Sig, self.Desc

	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def MyHotKeyCallback(self, inRefcon):
		if self.started == 0 :
			self.num_eng=XPLMGetDatai(self.num_eng_ref)
			self.gameLoopCB=self.gameLoopCallback
			XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 0.05, 0)
		else:
			print "Already started"

	def DrawWindowCallback(self, inWindowID, inRefcon):
		if self.remainingShowTime > 0:
			lLeft=[];	lTop=[]; lRight=[];	lBottom=[]
			XPLMGetWindowGeometry(inWindowID, lLeft, lTop, lRight, lBottom)
			left=int(lLeft[0]); top=int(lTop[0]); right=int(lRight[0]); bottom=int(lBottom[0])
			XPLMDrawTranslucentDarkBox(left,top,right,bottom)
			color=1.0, 1.0, 1.0
			XPLMDrawString(color, left+5, top-20, self.msg1, 0, xplmFont_Basic)
			XPLMDrawString(color, left+5, top-35, self.msg2, 0, xplmFont_Basic)
			XPLMDrawString(color, left+5, top-50, self.msg3, 0, xplmFont_Basic)
		
			#gl stuff removed

	def XPluginStop(self):
		XPLMUnregisterHotKey(self, self.gHotKey)
		XPLMUnregisterFlightLoopCallback(self, self.gameLoopCB, 0)
		self.closeEventWindow()
		pass

	def XPluginEnable(self):
		return 1

	def XPluginDisable(self):
		pass

	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass

	def createEventWindow(self):
		self.remainingShowTime=self.showTime
		#self.remainingUpdateTime=1.0
		if self.gWindow == 0:
			self.gWindow=XPLMCreateWindow(self, self.winPosX, self.winPosY, self.winPosX + self.WINDOW_WIDTH, self.winPosY - self.WINDOW_HEIGHT, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)
	
	def closeEventWindow(self):
		if self.gWindow==1:
			XPLMDestroyWindow(self, self.gWindow)
			self.gWindow = 0
		self.remainingShowTime = 0.0

	def gameLoopCallback(self, inElapsedSinceLastCall, elapsedSim, counter, refcon):

		if (XPLMGetDataf(self.flightTime_ref) > 3.0):
			if self.defaultcht== -100:
				self.defaultcht=XPLMGetDataf(OAT_ref)
			rpms=XPLMGetDatavf(self.RPM_ref, _currentRPM, 0, self.numberOfEngines)
			if rpms[0] > 0:
				self.runtime+=1
			#Let's do some damage
			cht=XPLMGetDatavf(self.CHT_ref)
			if self.defaultcht>0:
				_diff=abs(cht[0]-self.defaultcht)
				if _diff>0:
					#COOL THE ENGINES
					self.chtDamage+=_diff
			self.defaultcht=cht[0]
			mix=XPLMGetDatavf(self.mix_ref)*100
			if (mix[0] > 95 and XPLMGetDataf(self.alt_ref) > 1000):
				#SMOKIN'
				self.mixtureDamage += 1

			self.msg1="Runtime: "+str(self.runtime)
			self.msg2="CHT dmg: "+str(self.chtDamage)
			self.msg3="mix dmg: "+str(self.mixtureDamage)
			self.createEventWindow()

		return 1
