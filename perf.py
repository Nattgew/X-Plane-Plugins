from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMDisplay import *
from XPLMGraphics import *
from XPLMDefs import *
from math import *
from XPLMUtilities import *

class PythonInterface:

	def CtoF(self, C):
		F=C*1.8+32
		return F

	def check_index(self, hi, lo, length):
		flo=lo
		fhi=hi
		exact=0
		if hi>length:
			flo=length-1
			fhi=length
		elif lo<0:
			flo=0
			fhi=1
		elif lo==hi:
			exact=1
		return (fhi, flo, exact)
	
	def interp(self, y2, y1, x2, x1, xi):
		if y2==y1:
			result=y1
		else:
			result=(y2-y1)/(x2-x1)*(xi-x1)+y1
		#print "Interp "+str(y2)+", "+str(y1)+", "+str(x2)+", "+str(x1)+", "+str(round(xi))+" = "+str(round(result))
		return result
	
	def interp2(self, y1, y2, y3, y4, x1, x2, x3, x4, xi1, xi2):
		res_l=self.interp(y1, y2, x1, x2, xi1)
		res_h=self.interp(y3, y4, x1, x2, xi1)
		result=self.interp(res_h, res_l, x3, x4, xi2)
		return result

	def getDA(self, P, T):
		T+=273.15
		density_alt=self.T_SL/self.gamma_l*(1-((P/self.P_SL)/(T/self.T_SL))**(self.gamma_u*self.R/(self.g*self.M-self.gamma_u*self.R)))
		return density_alt
	
	def getDA_approx(self, P, T):
		T=self.CtoF(T)
		density_alt=145442.16*(1-(17.326*P/(459.67+T))**0.235)
		return density_alt
	
	def getdelISA(self, alt, T):
		T_ISA=15-self.gamma_l*alt
		delISA=T-T_ISA
		return delISA

	def getVref(self, flaps, wt, DA, T, AC):
		Vref="N/A"
		return Vref

	def getV1(self, flaps, wt, DA, T, AC):
		V1="N/A"
		if AC=="B738":
			exactwt=0
			GW=tuple(range(90,181,10))
			flapdet=(1,5,15)
			alts=tuple(range(0,8001,2000))
			flaps1=1
			flaps5=1
			flaps10=1
			
			if T < 27 and DA < alts[1] or T < 38 and DA < alts[1] and (-T+38)/5.5 <= DA/1000: # A cyan
				v1s=((107,114,121,127,133,139,145,150,155,160),	# flaps 1
				(103,109,116,122,128,134,139,144,149,153),		# flaps 5
				(99,106,112,118,124,130,135,140,145,150))		# flaps 15
			elif T < 27 and DA < alts[2] or T < 38 and DA < alts[2] and (-T+38)/11 <= DA/1000-3 or T < 43 and DA < (alts[2]+alts[1])/2 and (-T+43)/(5/3) <= DA/1000: #B yellow
				v1s=((108,115,122,128,134,140,146,151,156,161),	# flaps 1
				(104,110,117,123,129,135,140,145,150,154),		# flaps 5
				(100,107,113,119,125,131,136,141,146,0))		# flaps 15
			elif T < 27 and DA < alts[3] or T < 38 and DA < alts[3] and (-T+38)/5.5 <= DA/1000-4 or T < 49 and DA < (alts[3]+alts[2])/2 and (-T+49)/2.75 <= DA/1000: #C pink
				v1s=((109,116,123,129,135,141,147,152,157,162),	# flaps 1
				(105,111,118,124,130,136,141,146,151,0),		# flaps 5
				(101,108,114,120,126,132,137,142,0,0))			# flaps 15
			elif T < 60 and DA/1000 < 160/11 and (-T+60)/4.125 <= DA/1000: #D green
				v1s=((110,117,124,130,136,142,148,153,158,0),	# flaps 1
				(106,112,119,125,131,137,142,147,0,0),			# flaps 5
				(102,109,115,121,127,133,138,0,0,0))			# flaps 15
			else: #E blue uh oh
				v1s=((112,119,126,132,138,144,150,155,0,0),		# flaps 1
				(108,114,121,127,133,139,0,0,0,0),				# flaps 5
				(104,111,117,123,129,0,0,0,0,0))				# flaps 15
			
			if flaps == flaps1:
				flap_i=0
			elif flaps == flaps5:
				flap_i=1
			elif flaps == flaps15:
				flap_i=2
			else:
				flap_i=-1
				V1="T/O CONFIG"
			if flap_i>-1:
				wgt_i=GW/10000-9
				wgt_il=int(floor(wgt_i))
				wgt_ih=int(ceil(wgt_i))
				wgt_ih, wgt_il, exactwt = self.check_index(wgt_ih, wgt_il, len(GW))
				
				v1f=self.interp(v1s[flap_i][wgt_ih], v1s[flap_i][wgt_il], GW[wgt_ih], GW[wgt_il], wgt/1000)
				V1=str(round(v1f))+" kias"
				
		elif AC=="PC12":
			GW=1
			flaps=1
			alts=1
		return V1
	
	def getCC(self, DA, alt, delISA, AC):
		bestCC="N/A"
		if AC=="PC12":
			exactfl=0
			exactdi=0
			#alts=(0,5000,10000,15000,20000,25000,30000)
			alts=tuple(range(0,30001,5000))
			ias=((160,160,160,160,160,150,125),	# -40
			(160,160,160,160,160,150,125),		# -30
			(160,160,160,160,155,142,125),		# -20
			(160,160,160,160,148,135,120),		# -10
			(160,160,160,150,140,130,115),		# +0
			(160,160,155,140,130,120,110),		# +10
			(160,155,140,130,120,110,110),		# +20
			(150,140,130,120,110,110,110))		# +30
			dis=(-40,-30,-20,-10,0,10,20,30)
			
			alt_i=alt/5000
			alt_il=int(floor(alt_i))
			alt_ih=int(ceil(alt_i))
			dis_i=delISA/10+4
			dis_il=int(floor(dis_i))
			dis_ih=int(ceil(dis_i))
			alt_ih, alt_il, exactfl = self.check_index(alt_ih, alt_il, len(alts))
			dis_ih, dis_il, exactdi = self.check_index(dis_ih, dis_il, len(dis))
			if exactfl==1 and exactdi==1:
				cc=ias[dis_il][alt_il]
			elif exactfl==1:
				cc=self.interp(ias[dis_ih][alt_il], ias[dis_il][alt_il], dis[dis_ih], dis[dis_il], delISA)
			elif exactdi==1:
				cc=self.interp(ias[dis_il][alt_ih], ias[dis_il][alt_il], alts[alt_ih], alts[alt_il], alt)
			else:
				cc=self.interp2(ias[dis_ih][alt_il], ias[dis_il][alt_il], ias[dis_ih][alt_ih], ias[dis_il][alt_ih], dis[dis_ih], dis[dis_il], alts[alt_ih], alts[alt_il], delISA, alt)
			
			bestCC=str(round(cc))+" kias"
			
		return bestCC
		
	def getOptFL(self, wgt, AC):
		optFL="N/A"
		if AC=="B738":
			exactwt=0
			#wts=(120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175, 180)
			wts=tuple(range(120,181,5))
			alts=(39700, 38800, 38000, 37200, 36500, 35700, 35000, 34300, 33700, 33000, 32400, 31700, 31100)
			wt_i=wgt/5000-24
			wt_il=int(floor(wt_i))
			wt_ih=int(ceil(wt_i))
			wt_ih, wt_il, exactwt = self.check_index(wt_ih, wt_il, len(wts))
			if exactwt==1:
				oa=alts[wt_il]
			else:
				oa=self.interp(alts[wt_ih], alts[wt_il], wts[wt_ih], wts[wt_il], wt_i)
				
			FLalt=str(round(oa,-2))
			optFL="FL"+FLalt[0:3]
			
		return optFL
	
	def getMaxFL(self, wgt, delISA, AC):
		maxFL="N/A"
		if AC=="B738":
			exactwt=0
			exactdi=0
			#GW=(120, 125, 130, 135, 140, 145, 150, 155, 160, 165, 170, 175, 180)
			GW=tuple(range(120,181,5))
			alts=((41000, 41000, 40500, 39800, 39100, 38500, 37800, 37200, 36600, 36000, 35300, 34600, 33800), # +10C, below
			(40900, 40200, 39500, 38800, 38200, 37500, 36900, 36200, 35600, 34900, 34000, 33100, 32100), # +15C
			(39700, 39000, 38300, 37600, 37000, 36200, 35500, 34700, 33800, 32800, 31500, 30300, 29100)) # +20C
			temps=(10,15,20)
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
			wt_ih, wt_il, exactwt = self.check_index(wt_ih, wt_il, len(GW))
			dI_ih, dI_il, exactdi = self.check_index(dI_ih, dI_il, len(temps))
			if exactdi==1 and exactwt==1:
				ma=alts[dI_il][wt_il]
			elif exactdi==1:
				ma=self.interp(alts[dI_il][wt_ih], alts[dI_il][wt_il], GW[wt_ih], GW[wt_il], wgt/1000)
			elif exactwt==1:
				ma=self.interp(alts[dI_ih][wt_il], alts[dI_il][wt_il], temps[dI_ih], temps[dI_il], delISA)
			else:
				ma=self.interp2(alts[dI_ih][wt_il], alts[dI_il][wt_il], alts[dI_ih][wt_ih], alts[dI_il][wt_ih], temps[dI_ih], temps[dI_il], GW[wt_ih], GW[wt_il], delISA, wgt/1000)

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
			else: # Use LR cruise table from manual
				exactfl=0
				exactwt=0
				machs=((.601,.61,.619,.627,.636,.643,.652,.661,.671,.683,.695,.706,.718,.729),	# FL250
				(.683,.647,.658,.690,.684,.698,.711,.725,.738,.749,.757,.764,.769,.773),		# FL290
				(.690,.706,.723,.738,.751,.760,.768,.773,.777,.781,.785,.788,.791,.794),		# FL330
				(.726,.742,.754,.764,.771,.776,.780,.784,.788,.792,.794,.795,.795,0),			# FL350
				(.756,.766,.773,.778,.783,.787,.791,.794,.765,.794,0,0,0,0),					# FL370
				(.774,.780,.785,.789,.793,.795,.795,0,0,0,0,0,0,0),								# FL390
				(.786,.791,.794,.795,0,0,0,0,0,0,0,0,0,0))										# FL410
				#GW=(110,115,120,125,130,135,140,145,150,155,160,165,170,175)
				GW=tuple(range(110,176,5))
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
				fl_ih, fl_il, exactfl = self.check_index(fl_ih, fl_il, len(alts))
				wt_ih, wt_il, exactwt = self.check_index(wt_ih, wt_il, len(GW))
				
				if exactfl==1 and exactwt==1:
					bc=machs[fl_il][wt_il]
				elif exactfl==1:
					bc=self.interp(machs[fl_il][wt_ih], machs[fl_il][wt_il], GW[wt_ih], GW[wt_il], wgt/1000)
				elif exactwt==1:
					bc=self.interp(machs[fl_ih][wt_il], machs[fl_il][wt_il], alts[fl_ih], alts[fl_il], DA/1000)
				else:
					bc=self.interp2(machs[fl_ih][wt_il], machs[fl_il][wt_il], machs[fl_ih][wt_ih], machs[fl_il][wt_ih], alts[fl_ih], alts[fl_il], GW[wt_ih], GW[wt_il], DA/1000, wgt/1000)

				bestCruise="M"+str(round(bc,2))
			
		elif AC=="PC12": # PIM Section 5
			exactdi=0
			exactfl=0
			exactwt=0
			GW=(7000,8000,9000,10000,10400)
			#alts=(0,2000,4000,6000,8000,10000,12000,14000,16000,18000,20000,22000,24000,26000,28000,30000)
			alts=tuple(range(0,30001,2000))
			ias=(((218,212,207,202,196,191,185,179,173,167,160,154,147,139,132,123),	# 7000lb	-40C
			(217,212,207,202,196,191,186,180,175,169,163,156,150,143,136,129),			# 8000lb
			(216,211,206,201,196,191,186,181,176,170,164,159,153,147,140,133),			# 9000lb
			(214,210,205,201,196,191,186,181,176,171,166,160,155,149,143,137),			# 10000lb
			(214,209,205,200,196,191,186,181,176,171,166,161,155,150,144,138)),			# 10400lb
			((216,211,205,200,194,189,183,177,171,165,159,152,145,137,130,121),	# 7000lb	-30C
			(215,210,205,200,194,189,184,178,173,167,161,154,148,141,134,126),			# 8000lb
			(214,209,204,199,194,189,184,179,174,168,162,157,151,144,138,131),			# 9000lb
			(212,208,203,199,194,189,184,179,174,169,163,158,152,146,140,134),			# 10000lb
			(212,207,203,198,194,189,184,179,174,169,164,158,153,147,141,135)),			# 10400lb
			((214,209,204,198,193,187,181,175,169,163,157,150,143,135,128,119),	# 7000lb	-20C
			(213,208,203,198,193,187,182,176,171,165,159,152,146,139,132,124),			# 8000lb
			(212,207,202,197,193,188,182,177,172,166,160,155,148,142,135,128),			# 9000lb
			(211,206,201,197,192,187,182,177,172,167,161,156,150,144,138,131),			# 10000lb
			(210,206,201,197,192,187,182,177,172,167,161,156,151,145,139,132)),			# 10400lb
			((212,207,202,197,191,158,179,174,168,162,155,148,141,134,126,117),	# 7000lb	-10C
			(212,206,201,196,191,185,180,175,169,163,157,150,144,137,130,122),			# 8000lb
			(210,205,201,196,191,186,181,175,170,164,158,152,146,140,133,126),			# 9000lb
			(209,204,200,195,190,185,180,175,170,164,159,154,148,142,136,129),			# 10000lb
			(208,204,199,195,190,185,180,175,170,165,159,154,148,142,136,130)),			# 10400lb
			((211,206,200,195,189,184,178,172,166,160,153,146,139,132,124,116),	# 7000lb	+0C
			(210,205,200,194,189,184,178,173,167,131,155,149,142,135,128,120),			# 8000lb
			(209,204,199,194,189,184,179,173,168,162,156,150,144,138,131,124),			# 9000lb
			(207,203,198,193,188,183,178,173,168,162,157,151,146,139,133,126),			# 10000lb
			(207,202,198,193,188,183,178,173,168,163,157,152,147,140,134,127)),			# 10400lb
			((209,204,199,193,188,182,176,170,164,158,151,145,138,130,123,114),	# 7000lb	+10C
			(208,203,198,193,187,182,177,171,165,159,153,147,140,134,126,118),			# 8000lb
			(207,202,197,192,187,182,177,171,166,160,154,148,142,136,129,122),			# 9000lb
			(205,201,196,192,187,181,176,171,166,161,155,150,143,137,131,123),			# 10000lb
			(205,200,196,191,186,181,176,171,166,161,155,150,144,138,132,124)),			# 10400lb
			((208,203,197,192,186,180,175,169,163,156,150,143,136,129,121,112),	# 7000lb	+20C
			(207,202,196,191,186,181,175,170,163,157,151,145,138,132,124,116),			# 8000lb
			(205,200,196,191,186,181,175,170,164,158,153,147,141,134,127,119),			# 9000lb
			(204,199,195,190,185,180,175,169,164,159,153,148,141,135,128,120),			# 10000lb
			(203,199,194,189,184,179,174,169,164,159,154,148,142,136,129,121)),			# 10400lb
			((206,201,196,190,185,179,173,167,161,155,148,142,135,127,119,110),	# 7000lb	+30C
			(205,200,195,190,184,179,174,168,162,156,150,143,137,130,122,114),			# 8000lb
			(204,199,194,189,184,179,173,168,162,157,151,145,139,132,125,116),			# 9000lb
			(202,198,193,188,183,178,173,168,162,157,151,146,140,133,126,117),			# 10000lb
			(202,197,193,188,183,178,173,168,162,157,152,149,140,134,127,118)))			# 10400lb
			#dis=(-40,-30,-20,-10,0,10,20,30)
			dis=tuple(range(-40,31,10))
			
			if wgt>10000:
				wgt_i=wgt/400-22
			else:
				wgt_i=wgt/1000-7
			wgt_il=int(floor(wgt_i))
			wgt_ih=int(ceil(wgt_i))
			alt_i=alt/2000
			alt_il=int(floor(alt_i))
			alt_ih=int(ceil(alt_i))
			dis_i=delISA/10+4
			dis_il=int(floor(dis_i))
			dis_ih=int(ceil(dis_i))
			wgt_ih, wgt_il, exactwt = self.check_index(wgt_ih, wgt_il, len(GW))
			alt_ih, alt_il, exactfl = self.check_index(alt_ih, alt_il, len(alts))
			dis_ih, dis_il, exactdi = self.check_index(dis_ih, dis_il, len(dis))
			
			if exactwt==1 and exactfl==1 and exactdi==1: # Epic win
				bc=ias[dis_il][wgt_il][alt_il]
			elif exactwt==1 and exactfl==1:
				bc=self.interp(ias[dis_ih][wgt_il][alt_il], ias[dis_il][wgt_il][alt_il], dis[dis_ih], dis[dis_il], delISA)
			elif exactwt==1 and exactdi==1:
				bc=self.interp(ias[dis_il][wgt_il][alt_ih], ias[dis_il][wgt_il][alt_il], alts[alt_ih], alts[alt_il], alt)
			elif exactfl==1 and exactdi==1:
				bc=self.interp(ias[dis_il][wgt_ih][alt_il], ias[dis_il][wgt_il][alt_il], GW[wgt_ih], GW[wgt_il], wgt)
			elif exactwt==1:
				bc=self.interp2(ias[dis_ih][wgt_il][alt_il], ias[dis_il][wgt_il][alt_il], ias[dis_ih][wgt_il][alt_ih], ias[dis_il][wgt_il][alt_ih], dis[dis_ih], dis[dis_il], alts[alt_ih], alts[alt_il], delISA, alt)
			elif exactfl==1:
				bc=self.interp2(ias[dis_ih][wgt_il][alt_il], ias[dis_il][wgt_il][alt_il], ias[dis_ih][wgt_ih][alt_il], ias[dis_il][wgt_ih][alt_il], dis[dis_ih], dis[dis_il], GW[wgt_ih], GW[wgt_il], delISA, wgt)
			elif exactdi==1:
				bc=self.interp2(ias[dis_il][wgt_ih][alt_il], ias[dis_il][wgt_il][alt_il], ias[dis_il][wgt_ih][alt_ih], ias[dis_il][wgt_il][alt_ih], GW[wgt_ih], GW[wgt_il], alts[alt_ih], alts[alt_il], wgt, alt)
			else: # Triple interpolation here we come
				bc_l=self.interp2(ias[dis_ih][wgt_il][alt_il], ias[dis_il][wgt_il][alt_il], ias[dis_ih][wgt_il][alt_ih], ias[dis_il][wgt_il][alt_ih], dis[dis_ih], dis[dis_il], alts[alt_ih], alts[alt_il], delISA, alt)
				bc_h=self.interp2(ias[dis_ih][wgt_ih][alt_il], ias[dis_il][wgt_ih][alt_il], ias[dis_ih][wgt_ih][alt_ih], ias[dis_il][wgt_ih][alt_ih], dis[dis_ih], dis[dis_il], alts[alt_ih], alts[alt_il], delISA, alt)
				bc=self.interp(bc_h, bc_l, GW[wgt_ih], GW[wgt_il], wgt)
			bestCruise=str(round(bc))+" kias"
			
		return bestCruise
	
	def getMaxCruise(self, DA, wgt, alt, delISA, AC):
		maxCruise="N/A"
		return maxCruise
	
	def getMaxPwr(self, DA, delISA, AC):
		maxTRQ="N/A"
		return maxTRQ

	def XPluginStart(self):
		self.Name="Performance Calculator"
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
		self.flap_pos_ref=XPLMFindDataRef("sim/flightmodel2/controls/flap_handle_deploy_ratio") # actual position
		self.flap_h_pos_ref=XPLMFindDataRef("sim/cockpit2/controls/flap_ratio") # handle position
		self.geardep_ref=XPLMFindDataRef("sim/aircraft/parts/acf_gear_deploy")
		self.f_norm_ref=XPLMFindDataRef("sim/flightmodel/forces/fnrml_gear")
		
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
		self.num_eng=0
		self.acf_descb=[]

		self.gameLoopCB=self.gameLoopCallback
		self.DrawWindowCB=self.DrawWindowCallback
		self.KeyCB=self.KeyCallback
		self.MouseClickCB=self.MouseClickCallback

		self.CmdSHConn = XPLMCreateCommand("fsei/flight/perfinfo","Shows or hides performance info")
		self.CmdSHConnCB  = self.CmdSHConnCallback
		XPLMRegisterCommandHandler(self, self.CmdSHConn,  self.CmdSHConnCB, 0, 0)
		
		return self.Name, self.Sig, self.Desc

	def MouseClickCallback(self, inWindowID, x, y, inMouse, inRefcon):
		return 0

	def KeyCallback(self, inWindowID, inKey, inFlags, inVirtualKey, inRefcon, losingFocus):
		pass 

	def CmdSHConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "XDMG = CMD perf info"
			self.toggleInfo()
		return 0
		
	def toggleInfo(self):
		if self.started == 0:
			self.started=1
			self.num_eng=XPLMGetDatai(self.num_eng_ref)
			XPLMGetDatab(self.acf_desc_ref, self.acf_descb, 0, 500)
			print str(self.acf_descb)
			XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 10, 0)
		else:
			self.acf_descb=[]
			XPLMUnregisterFlightLoopCallback(self, self.gameLoopCB, 0)
			self.closeEventWindow()

	def DrawWindowCallback(self, inWindowID, inRefcon):
		if self.started==1:
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
		if self.started==1:
			self.toggleInfo()
		XPLMUnegisterCommandHandler(self, self.CmdSHConn, 0)
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
		if self.started==1:
			XPLMDestroyWindow(self, self.gWindow)
			self.gWindow = 0
			self.started=0
	
	def gameLoopCallback(self, inElapsedSinceLastCall, elapsedSim, counter, refcon):
		TRQ=[]
		ITT=[]
		XPLMGetDatavf(self.TRQ_ref, TRQ, 0, self.num_eng)
		XPLMGetDatavf(self.ITT_ref, ITT, 0, self.num_eng)
		P=XPLMGetDataf(self.baro_ref) #inHg
		T=XPLMGetDataf(self.temp_ref) #deg C
		alt=XPLMGetDataf(self.alt_ref)*self.mft #m -> ft
		wgt=XPLMGetDataf(self.wgt_ref)*self.kglb #kg -> lb
		acf_desc=str(self.acf_descb)
		if acf_desc[0:27]=="['Boeing 737-800 xversion":
			AC="B738"
		elif acf_desc=="['Pilatus PC-12']":
			AC="PC12"
		else:
			AC=acf_desc
		DenAlt=self.getDA(P,T) #ft
		#DenAltApprox=self.getDA_approx(P,T) #ft
		delISA=self.getdelISA(alt, T)
		maxPwr=self.getMaxPwr(DenAlt, delISA, AC)
		cruiseclb=self.getCC(DenAlt, alt, delISA, AC)
		cruise=self.getCruise(DenAlt, wgt, alt, delISA, AC)
		maxcruise=self.getMaxCruise(DenAlt, wgt, alt, delISA, AC)
		optFL=self.getOptFL(wgt, AC)
		maxFL=self.getMaxFL(wgt, delISA, AC)
		
		geardep=[]
		XPLMGetDatavf( self.geardep_ref, geardep, 0, 10)
		gear_state=0
		for i in range(10):
			if geardep[i]==1:
				gear_state=1
		Vref="N/A"
		V1="N/A"
		if gear_state==1:
			flaps=XPLMGetDataf(self.flap_h_pos_ref)
			Vref=self.getVref(flaps, wgt, DenAlt, T, AC)
			if XPLMGetDataf(self.f_norm_ref) != 0:
				V1=self.getV1(flaps, wgt, DenAlt, T, AC)
				
		dIstr=str(round(delISA))
		if delISA>0:
			dIstr="+"+dIstr
			
		self.msg1="DA: "+str(round(DenAlt))+"  GW: "+str(round(wgt))+" lb"
		self.msg2="T: "+str(round(T))+"  dISA: "+dIstr
		self.msg3="Pwr: "+maxPwr+"  CC: "+cruiseclb
		self.msg4="Crs: "+maxcruise+"  LR: "+cruise
		self.msg5="FL: "+maxFL+"  FL: "+optFL
		self.msg6=AC+"  V1: "+V1+"  Vref: "+Vref
		self.createEventWindow()

		return 10
