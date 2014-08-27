from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMDisplay import *
from XPLMGraphics import *
from XPLMDefs import *
from math import *

class PythonInterface:

	def interp(self, y2, y1, x2, x1, xi):
		print "Interp "+str(y2)+", "+str(y1)+", "+str(x2)+", "+str(x1)+", "+str(xi)
		result=(y2-y1)/(x2-x1)*(xi-x1)+x1
		return result

	def getDA(self, P, T):
		density_alt=self.T_SL/self.gamma_l*(1-((P/self.P_SL)/(T/self.T_SL))**(self.gamma_u*self.R/(self.g*self.M-self.gamma_u*self.R)))
		return density_alt
	
	def getDA_approx(self, P, T):
		density_alt=145442.16*(1-(17.326*P/(459.67+T))**0.235)
		return density_alt
	
	def getdelISA(self, alt, T):
		T_ISA=15-self.gamma_u*alt
		delISA=T-273.15-T_ISA
		return delISA
	
	def getCC(self, DA, wgt, alt, delISA):
		bestCC="N/A"
		return bestCC
		
	def getOptFL(self, wgt, AC):
		optFL="N/A"
		if AC=="B738":
			wts=(120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175, 180)
			alts=(39700, 38800, 38000, 37200, 36500, 35700, 35000, 34300, 33700, 33000, 32400, 31700, 31100)
			wt_i=wgt/5000-24
			wt_il=int(floor(wt_i))
			wt_ih=int(ceil(wt_i))
			bc=self.interp(alts[wt_ih], alts[wt_il], wts[wt_ih], wts[wt_il], wt_i)
			FLalt=str(round(bc,-2))
			optFL="FL"+FLalt[0:3]
		return optFL
	
	def getMaxFL(self, wgt, delISA, AC):
		maxFL="N/A"
		if AC=="B738":
			GW=(120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175, 180)
			alts=((41000, 41000, 40500, 39800, 39100, 38500, 37800, 37200, 36600, 36000, 35300, 34600, 33800), # +10C, below
			(40900, 40200, 39500, 38800, 38200, 37500, 36900, 36200, 35600, 34900, 34000, 33100, 32100), # +15C
			(39700, 39000, 38300, 37600, 37000, 36200, 35500, 34700, 33800, 32800, 31500, 30300, 29100)) # +20C
			temps=(10, 15, 20)
			wt_i=wgt/5000-24
			dI_i=delISA/5-2
			if dI_i < 0:
				dI_i=0
			elif dI_i > 2:
				dI_i=2
			wt_il=int(floor(wt_i))
			wt_ih=int(ceil(wt_i))
			dI_il=int(floor(dI_i))
			dI_ih=int(ceil(dI_i))
			
			ma_l=self.interp(alts[dI_ih][wt_il], alts[dI_il][wt_il], temps[dI_ih], temps[dI_il], delISA)
			ma_h=self.interp(alts[dI_ih][wt_ih], alts[dI_il][wt_ih], temps[dI_ih], temps[dI_il], delISA)
			ma=self.interp(ma_h, ma_l, GW[wt_ih], GW[wt_il], wgt/1000)
			
			FLalt=str(round(ma,-2))
			maxFL="FL"+FLalt[0:3]
			
		return maxFL
	
	def getCruise(self, DA, wgt, alt, delISA, AC):
		bestCruise="N/A"
		if AC=="B738":
			if DA>42000:
				bestCruise="Descend"
			elif DA<24000:
				bestCruise="280 kts"
			else: # Use LR cruise table
				machs=((.601,.61,.619,.627,.636,.643,.652,.661,.671,.683,.695,.706,.718,.729),	# FL250
				(.683,.647,.658,.690,.684,.698,.711,.725,.738,.749,.757,.764,.769,.773),		# FL290
				(.690,.706,.723,.738,.751,.760,.768,.773,.777,.781,.785,.788,.791,.794),		# FL330
				(.726,.742,.754,.764,.771,.776,.780,.784,.788,.792,.794,.795,.795,0),			# FL350
				(.756,.766,.773,.778,.783,.787,.791,.794,.765,.794,0,0,0,0),					# FL370
				(.774,.780,.785,.789,.793,.795,.795,0,0,0,0,0,0,0),								# FL390
				(.786,.791,.794,.795,0,0,0,0,0,0,0,0,0,0))										# FL410
				GW=(110,115,120,125,130,135,140,145,150,155,160,165,170,175)
				alts=(25,29,33,35,37,39,41)
				if DA<33000:
					wt_i=wgt/5000-22
					fl_i=alt/4000-6.25
				else: #33000 to ceiling
					wt_i=wgt/5000-22
					fl_i=alt/2000-14.5
				fl_il=int(floor(fl_i))
				fl_ih=int(ceil(fl_i))
				wt_il=int(floor(wt_i))
				wt_ih=int(ceil(wt_i))
				
				bc_l=self.interp(machs[fl_ih][wt_il], machs[fl_il][wt_il], alts[fl_ih], alts[fl_il], DA/1000)
				bc_h=self.interp(machs[fl_ih][wt_ih], machs[fl_il][wt_ih], alts[fl_ih], alts[fl_il], DA/1000)
				bc=self.interp(bc_h, bc_l, GW[wt_ih], GW[wt_il], wgt/1000)
				
				bestCruise=str(round(bc,2))
		elif AC=="PC12":
			bestCruise="A billion"
		return bestCruise
	
	def getMaxCruise(self, DA, wgt, alt, delISA):
		maxCruise="N/A"
		return maxCruise
	
	def getMaxTRQ(self, DA, delISA):
		maxTRQ="N/A"
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
		self.msg5=""
		self.msg6=""
		self.winPosX=20
		self.winPosY=800
		self.WINDOW_WIDTH=230
		self.WINDOW_HEIGHT=120
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
			XPLMGetDatab(self.acf_desc_ref, self.acf_desc, 0, 500)
			print self.acf_desc
			XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 1, 0)
		else:
			self.acf_desc=[]
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
		XPLMDrawString(color, left+5, top-80, self.msg5, 0, xplmFont_Basic)
		XPLMDrawString(color, left+5, top-95, self.msg6, 0, xplmFont_Basic)

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
		if str(self.acf_desc)=="['Boeing 737-800 xversion 482']":
			AC="B738"
		else:
			AC=str(self.acf_desc)
		self.msg6=AC
		DenAlt=self.getDA(P,T) #feet
		DenAltApprox=self.getDA_approx(P,T) #ft
		delISA=self.getdelISA(alt, T)
		maxTRQ=self.getMaxTRQ(DenAlt, delISA)
		cruiseclb=self.getCC(DenAlt, wgt, alt, delISA)
		cruise=self.getCruise(DenAlt, wgt, alt, delISA, AC)
		maxcruise=self.getMaxCruise(DenAlt, wgt, alt, delISA)
		optFL=self.getOptFL(wgt, AC)
		maxFL=self.getMaxFL(wgt, delISA, AC)

		self.msg1="DA: "+str(round(DenAlt))+" Approx: "+str(round(DenAltApprox))
		self.msg2="T: "+str(round(T))+" dISA: "+str(round(delISA))
		self.msg3="TRQ: "+maxTRQ+" CC: "+cruiseclb
		self.msg4="Crs: "+maxcruise+" LR: "+cruise
		self.msg5="opt FL: "+optFL+" max FL: "+maxFL
		self.createEventWindow()

		return 1
