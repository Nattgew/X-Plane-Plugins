from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMDisplay import *
from XPLMGraphics import *
from XPLMDefs import *

class PythonInterface:

	def getDA(self, P, T):
		density_alt=self.T_SL/self.gamma_l*(1-((P/self.P_SL)/(T/self.T_SL))**(self.gamma_u*self.R/(self.g*self.M-self.gamma_u*self.R)))
		return density_alt
	
	def getDA_approx(self, P, T):
		density_alt=145442.16*(1-(17.326*P/(459.67+T))**0.235)
		return density_alt
	
	def getdelISA(self, alt, T):
		T_ISA=15-self.gamma_u*alt
		delISA=T-T_ISA
		return delISA
	
	def getCC(self, DA, wgt, alt, delISA):
		
		return bestCC
	
	def getCruise(self, DA, wgt, alt, delISA):
		
		return bestCruise
	
	def getMaxCruise(self, DA, wgt, alt, delISA):
		
		return maxCruise
	
	def getMaxTRQ(self, DA, delISA):
		
		return maxTRQ

	def XPluginStart(self):
		self.Name="Long Range Cruise Calculator"
		self.Sig= "natt.python.cruise"
		self.Desc="Calculates the current best climb/cruise info based on POH"
		self.VERSION="1.0"
		
		self.P_SL=29.92126 # standard sea level atmospheric pressure 1013.25 hPa ISA or 29.92126 inHg US
		self.T_SL=288.15 # ISA standard sea level air temperature in K
		self.gamma_l=0.0019812 # lapse rate K/ft
		self.gamma_u=0.0065 # lapse rate K/m
		self.R=8.31432 # gas constant J/mol K
		self.g=9.80665 # gravity m/s^2
		self.M=0.0289644 # molar mass of dry air kg/mol
		self.kglb=2.20462262
		self.mft=3.2808399
		self.mkt=1.94384
		
		self.ITT_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_ITT_c")
		self.TRQ_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_TRQ")
		self.num_eng_ref=XPLMFindDataRef("sim/aircraft/engine/acf_num_engines")
		self.alt_ref=XPLMFindDataRef("sim/flightmodel/position/elevation")
		self.baro_ref=XPLMFindDataRef("sim/weather/barometer_current_inhg")
		self.temp_ref=XPLMFindDataRef("sim/weather/temperature_ambient_c")
		self.wgt_ref=XPLMFindDataRef("sim/flightmodel/weight/m_total")
		self.acf_desc_ref=XPLMFindDataRef("sim/aircraft/view/acf_descrip")
		
		self.started=0
		self.gWindow=0
		self.msg1=""
		self.msg2=""
		self.msg3=""
		self.msg4=""
		self.winPosX=20
		self.winPosY=800
		self.WINDOW_WIDTH=230
		self.WINDOW_HEIGHT=90
		self.windowCloseRequest=0
		self.num_eng=0
		self.acf_desc=[]

		self.gameLoopCB=self.gameLoopCallback
		self.DrawWindowCB=self.DrawWindowCallback
		self.KeyCB=self.KeyCallback
		self.MouseClickCB=self.MouseClickCallback

		self.MyHotKeyCB=self.MyHotKeyCallback
		self.gHotKey=XPLMRegisterHotKey(self, XPLM_VK_C, xplm_DownFlag+xplm_ShiftFlag+xplm_ControlFlag, "Shows best cruise info", self.MyHotKeyCB, 0)
		# self.MyHotKeyCB2=self.MyHotKeyCallback2
		# self.gHotKey2=XPLMRegisterHotKey(self, XPLM_VK_M, xplm_DownFlag+xplm_ShiftFlag+xplm_ControlFlag, "Sets mixture below FSE damage threshold", self.MyHotKeyCB2, 0)
		
		return self.Name, self.Sig, self.Desc

	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def MyHotKeyCallback(self, inRefcon):
		if self.started == 0:
			self.started=1
			self.num_eng=XPLMGetDatai(self.num_eng_ref)
			XPLMGetDatab(self.acf_desc_ref, acf_desc, 0, 500)
			XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 1, 0)
		else:
			self.started=0
			XPLMUnregisterFlightLoopCallback(self, self.gameLoopCB, 0)
			self.closeEventWindow()

	# def MyHotKeyCallback2(self, inRefcon):
		# self.MixTape(0.949)

	def DrawWindowCallback(self, inWindowID, inRefcon):
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
		#XPLMUnregisterHotKey(self, self.gHotKey2)
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
		if self.gWindow == 0:
			self.gWindow=XPLMCreateWindow(self, self.winPosX, self.winPosY, self.winPosX + self.WINDOW_WIDTH, self.winPosY - self.WINDOW_HEIGHT, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)
	
	def closeEventWindow(self):
		if self.gWindow==1:
			XPLMDestroyWindow(self, self.gWindow)
			self.gWindow = 0
	
	def gameLoopCallback(self, inElapsedSinceLastCall, elapsedSim, counter, refcon):
		TRQ=[]
		ITT=[]
		XPLMGetDatavf(self.TRQ_ref, TRQ, 0, self.num_eng)
		XPLMGetDatavf(self.ITT_ref, ITT, 0, self.num_eng)
		P=XPLMGetDataf(self.baro_ref) #inHg
		T=XPLMGetDataf(self.temp_ref)+273.15 #deg K
		alt=XPLMGetDataf(self.alt_ref)*self.mft #m
		wgt=XPLMGetDataf(self.wgt_ref)*self.kglb #kg
		DenAlt=self.getDA(P,T) #feet
		DenAltApprox=self.getDA_approx(P,T) #ft
		delISA=self.getdelISA(alt, T)
		maxTRQ=self.getMaxTRQ(DenAlt, delISA)
		cruiseclb=self.getCC(DenAlt, wgt, alt, delISA)
		cruise=self.getCruise(DenAlt, wgt, alt, delISA)
		maxcruise=self.getMaxCruise(DenAlt, wgt, alt, delISA)
		
		self.msg1="DA: "+str(round(DenAlt))+" Approx: "+str(round(DenAltApprox))
		self.msg2="T: "+str(round(T))" dISA: "+str(round(delISA))
		self.msg3="TRQ: "+str(round(maxTRQ,1))+" CC: "+str(round(cruiseclb))
		self.msg4="Crs: "+str(round(maxcruise))+" LR: "+str(round(cruise))
		self.createEventWindow()

		return 1
