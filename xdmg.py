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
		self.VERSION="1.1"
		
		self.OAT_ref=XPLMFindDataRef("sim/weather/temperature_ambient_c")
		self.RPM_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_N2_")
		self.CHT_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_CHT_c")
		self.mix_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_mixt")
		self.flightTime_ref=XPLMFindDataRef("sim/time/total_flight_time_sec")
		self.num_eng_ref=XPLMFindDataRef("sim/aircraft/engine/acf_num_engines")
		self.alt_ref=XPLMFindDataRef("sim/flightmodel/position/y_agl")
		self.prop_type_ref=XPLMFindDataRef("sim/aircraft/prop/acf_prop_type")
		self.acf_fuel_ref=XPLMFindDataRef("sim/aircraft/weight/acf_m_fuel_tot") #flt
		self.m_fuel_ref=XPLMFindDataRef("sim/flightmodel/weight/m_fuel_total") #flt
		self.eng_type_ref=XPLMFindDataRef("sim/aircraft/prop/acf_en_type") #int[8]
		
		self.started=0
		self.gWindow=0
		self.msg1=""
		self.msg2=""
		self.msg3=""
		self.msg4=""
		self.remainingShowTime=0
		self.showTime=1
		self.winPosX=20
		self.winPosY=300
		self.WINDOW_WIDTH=230
		self.WINDOW_HEIGHT=90
		self.windowCloseRequest=0
		self.num_eng=0
		self.runtime=0
		self.chtDamage=0
		self.mixtureDamage=0
		self.prop_type=[]
		self.eng_type=[]

		self.DrawWindowCB=self.DrawWindowCallback
		self.KeyCB=self.KeyCallback
		self.MouseClickCB=self.MouseClickCallback
		#self.WindowId=XPLMCreateWindow(self, 50, 600, 300, 400, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)

		self.MyHotKeyCB=self.MyHotKeyCallback
		self.gHotKey=XPLMRegisterHotKey(self, XPLM_VK_D, xplm_DownFlag+xplm_ShiftFlag+xplm_ControlFlag, "Shows FSE damage info", self.MyHotKeyCB, 0)
		self.MyHotKeyCB2=self.MyHotKeyCallback2
		self.gHotKey2=XPLMRegisterHotKey(self, XPLM_VK_M, xplm_DownFlag+xplm_ShiftFlag+xplm_ControlFlag, "Sets mixture below FSE threshold", self.MyHotKeyCB2, 0)
		
		return self.Name, self.Sig, self.Desc

	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def MyHotKeyCallback(self, inRefcon):
		if self.started == 0 :
			self.started=1
			self.num_eng=XPLMGetDatai(self.num_eng_ref)
			XPLMGetDatavi(self.prop_type_ref, self.prop_type, 0, self.num_eng)
			XPLMGetDatavi(self.eng_type_ref, self.eng_type, 0, self.num_eng)
			self.defaultcht=XPLMGetDataf(self.OAT_ref)
			self.gameLoopCB=self.gameLoopCallback
			XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 1, 0)
		else:
			self.started=0
			XPLMUnregisterFlightLoopCallback(self, self.gameLoopCB, 0)
			self.closeEventWindow()
			self.prop_type=[]
			self.eng_type=[]
			self.runtime=0
			self.chtDamage=0
			self.mixtureDamage=0

	def MyHotKeyCallback2(self, inRefcon):
		h=0.949
		XPLMSetDatavf(self.mix_ref, [h, h, h, h, h, h, h, h], 0, self.num_eng)

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
			XPLMDrawString(color, left+5, top-65, self.msg4, 0, xplmFont_Basic)

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
			rpms=[]
			XPLMGetDatavf(self.RPM_ref, rpms, 0, self.num_eng)
			if rpms[0] > 0:
				self.runtime+=1
			#Let's do some damage
			chts=[]
			XPLMGetDatavf(self.CHT_ref, chts, 0, self.num_eng)
			if self.defaultcht>0:
				_diff=abs(chts[0]-self.defaultcht)
				if _diff>0:
					#COOL THE ENGINES
					self.chtDamage+=_diff
			self.defaultcht=chts[0]
			mixes=[]
			XPLMGetDatavf(self.mix_ref, mixes, 0, self.num_eng)
			mixes*=100
			if (mixes[0] > 0.95 and XPLMGetDataf(self.alt_ref) > 1000):
				#SMOKIN'
				self.mixtureDamage += 1
			m_fuel=XPLMGetDataf(self.m_fuel_ref)
			a_fuel=XPLMGetDataf(self.acf_fuel_ref)
			self.msg1="Run: "+str(self.runtime)+" Type: "+str(self.prop_type[0])
			self.msg2="CHT: "+str(round(chts[0],2))+" dmg: "+str(round(self.chtDamage,2))
			self.msg3="Mix: "+str(round(mixes[0],2))+" dmg: "+str(round(self.mixtureDamage,2))
			self.msg4="En: "+str(self.eng_type[0])+" F_m: "+str(round(m_fuel))+" F_a: "+str(round(a_fuel))
			self.createEventWindow()

		return 1
