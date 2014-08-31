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

	def get_index(self, i, length):
		flo=int(floor(i))
		fhi=int(ceil(i))
		exact=0
		if fhi>length-1:
			flo=length-2
			fhi=length-1
		elif flo<0:
			flo=0
			fhi=1
		elif flo==fhi:
			exact=1
		return (fhi, flo, exact)
	
	def interp(self, y2, y1, x2, x1, xi):
		if y2==y1:
			
			result=y1
		else:
			result=(y2-y1)/(x2-x1)*(xi-x1)+y1
		#print "Interp "+str(y2)+", "+str(y1)+", "+str(x2)+", "+str(x1)+", "+str(round(xi))+" = "+str(round(result))
		#print "Interp result: "+str(result)
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

	def getVref(self, flaps, wgt, DA, T, AC):
		Vref="N/A"
		if AC=="PC12": # Flaps 40
			self.vr=1
			exactwt=0
			GW=tuple(range(6400,10001,900))
			vapps=(67.0,72.0,76.0,80.0,84.0)
			
			wgt_i=wgt/900-64/9
			wgt_ih, wgt_il, exactwt = self.get_index(wgt_i, len(GW))
			self.Dstarted=1
			vapp=self.interp(vapps[wgt_ih], vapps[wgt_il], GW[wgt_ih], GW[wgt_il], wgt)
			self.Dstarted=0
			#print 'Vref %.0f %.0f %.0f %.0f %.0f = %.0f' % (vapps[wgt_ih], vapps[wgt_il], GW[wgt_ih], GW[wgt_il], wgt, vapp)
			Vref=str(int(round(vapp)))+" kias"
		elif AC=="B738":
			exactwt=0
			GW=tuple(range(90,181,10))
			vrs=((122.0,129.0,135.0,142.0,148.0,154.0,159.0,164.0,169.0,174),		# flaps 15
				(116.0,123.0,129.0,135.0,141.0,146.0,151.0,156.0,160.0,165),		# flaps 30
				(109.0,116.0,122,128.0,133.0,139.0,144.0,148.0,153.0,157))		# flaps 40

			flap_i=-1
			for i in range(2,5):
				if flaps == self.flaps_B738[i]:
					flap_i=i-2
			if flap_i==-1:
				Vref="LAND CONFIG"
			else:
				wgt_i=wgt/10000-9
				wgt_ih, wgt_il, exactwt = self.get_index(wgt_i, len(GW))
				
				vri=self.interp(vrs[flap_i][wgt_ih], vrs[flap_i][wgt_il], GW[wgt_ih], GW[wgt_il], wgt/1000)
				Vref=str(int(round(vri)))+" kias"
				
		return Vref

	def getV1(self, flaps, wgt, DA, T, AC):
		V1="N/A"
		if AC=="B738":
			exactwt=0
			GW=tuple(range(90,181,10))
			alts=tuple(range(0,8001,2000))
			
			if T < 27 and DA < alts[1] or T < 38 and DA < alts[1] and (-T+38)/5.5 <= DA/1000: # A cyan
				v1s=((107.0,114.0,121.0,127.0,133.0,139.0,145.0,150.0,155.0,160.0),	# flaps 1
					(103.0,109.0,116.0,122.0,128.0,134.0,139.0,144.0,149.0,153.0),	# flaps 5
					(99.0,106.0,112.0,118.0,124.0,130.0,135.0,140.0,145.0,150.0))	# flaps 15
			elif T < 27 and DA < alts[2] or T < 38 and DA < alts[2] and (-T+38)/11 <= DA/1000-3 or T < 43 and DA < (alts[2]+alts[1])/2 and (-T+43)/(5/3) <= DA/1000: #B yellow
				v1s=((108.0,115,122.0,128.0,134.0,140.0,146.0,151.0,156.0,161.0),	# flaps 1
					(104.0,110.0,117.0,123.0,129.0,135.0,140.0,145.0,150.0,154.0),	# flaps 5
					(100.0,107.0,113.0,119.0,125.0,131.0,136.0,141.0,146.0,0))	# flaps 15
			elif T < 27 and DA < alts[3] or T < 38 and DA < alts[3] and (-T+38)/5.5 <= DA/1000-4 or T < 49 and DA < (alts[3]+alts[2])/2 and (-T+49)/2.75 <= DA/1000: #C pink
				v1s=((109.0,116.0,123.0,129.0,135.0,141.0,147.0,152.0,157.0,162.0),	# flaps 1
					(105.0,111.0,118.0,124.0,130.0,136.0,141.0,146.0,151.0,0),	# flaps 5
					(101.0,108.0,114.0,120.0,126.0,132.0,137.0,142.0,0,0))		# flaps 15
			elif T < 60 and DA/1000 < 160/11 and (-T+60)/4.125 <= DA/1000: #D green
				v1s=((110.0,117.0,124.0,130.0,136.0,142.0,148.0,153.0,158.0,0),	# flaps 1
					(106.0,112.0,119.0,125.0,131.0,137.0,142.0,147.0,0,0),		# flaps 5
					(102.0,109.0,115.0,121.0,127.0,133.0,138.0,0,0,0))		# flaps 15
			else: #E blue uh oh
				v1s=((112.0,119.0,126.0,132.0,138.0,144.0,150.0,155.0,0,0),		# flaps 1
					(108.0,114.0,121.0,127.0,133.0,139.0,0,0,0,0),			# flaps 5
					(104.0,111.0,117.0,123.0,129.0,0,0,0,0,0))			# flaps 15
			
			flap_i=-1
			for i in range(3):
				if flaps == self.flaps_B738[i]:
					flap_i=i
			if flap_i==-1:
				V1="T/O CONFIG"
			else:
				wgt_i=wgt/10000-9
				wgt_ih, wgt_il, exactwt = self.get_index(wgt_i, len(GW))
				
				v1f=self.interp(v1s[flap_i][wgt_ih], v1s[flap_i][wgt_il], GW[wgt_ih], GW[wgt_il], wgt/1000)
				V1=str(int(round(v1f)))+" kias"
				
		elif AC=="PC12":
			GW=(6400,7300,8200,9100,10000,10450)
			vrs=((63,67,71,75,79,81),	# flaps 15
				(58,62,66,70,73,75))	# flaps 30
			#vas=((65,70,74,78,82,84), # flaps 15, Accelerate-stop, not used right now
			#(59,63,67,71,74,76)) # flaps 30
			
			flap_i=-1
			for i in range(0,2):
				if round(flaps,1) == self.flaps_PC12[i]:
					flap_i=i
			if flap_i==-1:
				V1="T/O CONFIG"
			else:
				if wgt<10000:
					wgt_i=wgt/900-64/9
				else:
					wgt_i=wgt/450-236/9
				
				wgt_ih, wgt_il, exactwt = self.get_index(wgt_i, len(GW))
				#print 'Interp: %.0f %.0f %.0f %.0f %.0f' % (vrs[flap_i][wgt_ih], vrs[flap_i][wgt_il], GW[wgt_ih], GW[wgt_il], wgt)
				vr=self.interp(vrs[flap_i][wgt_ih], vrs[flap_i][wgt_il], GW[wgt_ih], GW[wgt_il], wgt)
				V1=str(int(round(vr)))+" kias"
			
		return V1
	
	def getCC(self, DA, alt, delISA, AC):
		bestCC="N/A"
		if AC=="PC12":
			exactfl=0
			exactdi=0
			alts=tuple(range(0,30001,5000))
			ias=((160.0,160.0,160.0,160.0,160.0,150.0,125.0),	# -40
				(160.0,160.0,160.0,160.0,160.0,150.0,125.0),	# -30
				(160.0,160.0,160.0,160.0,155.0,142.0,125.0),	# -20
				(160.0,160.0,160.0,160.0,148.0,135.0,120.0),	# -10
				(160.0,160.0,160.0,150.0,140.0,130.0,115.0),	# +0
				(160.0,160.0,155.0,140.0,130.0,120.0,110.0),	# +10
				(160.0,155.0,140.0,130.0,120.0,110.0,110.0),	# +20
				(150.0,140.0,130.0,120.0,110.0,110.0,110.0))	# +30
			dis=(-40.0,-30.0,-20.0,-10.0,0.0,10.0,20.0,30.0)
			
			alt_i=alt/5000
			dis_i=delISA/10+4
			alt_ih, alt_il, exactfl = self.get_index(alt_i, len(alts))
			dis_ih, dis_il, exactdi = self.get_index(dis_i, len(dis))
			if exactfl==1 and exactdi==1:
				cc=ias[dis_il][alt_il]
			elif exactfl==1:
				cc=self.interp(ias[dis_ih][alt_il], ias[dis_il][alt_il], dis[dis_ih], dis[dis_il], delISA)
			elif exactdi==1:
				cc=self.interp(ias[dis_il][alt_ih], ias[dis_il][alt_il], alts[alt_ih], alts[alt_il], alt)
			else:
				cc=self.interp2(ias[dis_ih][alt_il], ias[dis_il][alt_il], ias[dis_ih][alt_ih], ias[dis_il][alt_ih], dis[dis_ih], dis[dis_il], alts[alt_ih], alts[alt_il], delISA, alt)
			
			bestCC=str(int(round(cc)))+" kias"
			
		return bestCC
		
	def getOptFL(self, wgt, AC):
		optFL="N/A"
		if AC=="B738":
			exactwt=0
			wts=tuple(range(120,181,5))
			alts=(39700, 38800, 38000, 37200, 36500, 35700, 35000, 34300, 33700, 33000, 32400, 31700, 31100)
			wt_i=wgt/5000-24
			wt_ih, wt_il, exactwt = self.get_index(wt_i, len(wts))
			if exactwt==1:
				oa=alts[wt_il]
			else:
				oa=self.interp(alts[wt_ih], alts[wt_il], wts[wt_ih], wts[wt_il], wgt/1000)
			
			FLalt=str(round(oa,-2))
			optFL="FL"+FLalt[0:3]
			
		return optFL
	
	def getMaxFL(self, wgt, delISA, AC):
		maxFL="N/A"
		if AC=="B738":
			exactwt=0
			exactdi=0
			GW=tuple(range(120,181,5))
			alts=((41000, 41000, 40500, 39800, 39100, 38500, 37800, 37200, 36600, 36000, 35300, 34600, 33800),	# +10C, below
				(40900, 40200, 39500, 38800, 38200, 37500, 36900, 36200, 35600, 34900, 34000, 33100, 32100),	# +15C
				(39700, 39000, 38300, 37600, 37000, 36200, 35500, 34700, 33800, 32800, 31500, 30300, 29100))	# +20C
			temps=(10,15,20)
			wt_i=wgt/5000-24
			dI_i=delISA/5-2
			if dI_i < 0:
				dI_i=0
			elif dI_i > 2:
				dI_i=2
			wt_ih, wt_il, exactwt = self.get_index(wt_i, len(GW))
			dI_ih, dI_il, exactdi = self.get_index(dI_i, len(temps))
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
					(.683,.647,.658,.690,.684,.698,.711,.725,.738,.749,.757,.764,.769,.773),	# FL290
					(.690,.706,.723,.738,.751,.760,.768,.773,.777,.781,.785,.788,.791,.794),	# FL330
					(.726,.742,.754,.764,.771,.776,.780,.784,.788,.792,.794,.795,.795,0),		# FL350
					(.756,.766,.773,.778,.783,.787,.791,.794,.765,.794,0,0,0,0),				# FL370
					(.774,.780,.785,.789,.793,.795,.795,0,0,0,0,0,0,0),							# FL390
					(.786,.791,.794,.795,0,0,0,0,0,0,0,0,0,0))									# FL410
				GW=tuple(range(110,176,5))
				alts=(25,29,33,35,37,39,41)
				
				if DA<33000:
					wt_i=wgt/5000-22
					fl_i=alt/4000-6.25
				else: #33000 to ceiling
					wt_i=wgt/5000-22
					fl_i=alt/2000-14.5
				fl_ih, fl_il, exactfl = self.get_index(fl_i, len(alts))
				wt_ih, wt_il, exactwt = self.get_index(wt_i, len(GW))
				
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
			alts=tuple(range(0,30001,2000))
			ias=(((218,212,207,202,196,191,185,179,173,167,160,154,147,139,132,123),	# 7000lb	-40C
				(217,212,207,202,196,191,186,180,175,169,163,156,150,143,136,129),		# 8000lb
				(216,211,206,201,196,191,186,181,176,170,164,159,153,147,140,133),		# 9000lb
				(214,210,205,201,196,191,186,181,176,171,166,160,155,149,143,137),		# 10000lb
				(214,209,205,200,196,191,186,181,176,171,166,161,155,150,144,138)),		# 10400lb
				((216,211,205,200,194,189,183,177,171,165,159,152,145,137,130,121),		# 7000lb	-30C
				(215,210,205,200,194,189,184,178,173,167,161,154,148,141,134,126),		# 8000lb
				(214,209,204,199,194,189,184,179,174,168,162,157,151,144,138,131),		# 9000lb
				(212,208,203,199,194,189,184,179,174,169,163,158,152,146,140,134),		# 10000lb
				(212,207,203,198,194,189,184,179,174,169,164,158,153,147,141,135)),		# 10400lb
				((214,209,204,198,193,187,181,175,169,163,157,150,143,135,128,119),		# 7000lb	-20C
				(213,208,203,198,193,187,182,176,171,165,159,152,146,139,132,124),		# 8000lb
				(212,207,202,197,193,188,182,177,172,166,160,155,148,142,135,128),		# 9000lb
				(211,206,201,197,192,187,182,177,172,167,161,156,150,144,138,131),		# 10000lb
				(210,206,201,197,192,187,182,177,172,167,161,156,151,145,139,132)),		# 10400lb
				((212,207,202,197,191,158,179,174,168,162,155,148,141,134,126,117),		# 7000lb	-10C
				(212,206,201,196,191,185,180,175,169,163,157,150,144,137,130,122),		# 8000lb
				(210,205,201,196,191,186,181,175,170,164,158,152,146,140,133,126),		# 9000lb
				(209,204,200,195,190,185,180,175,170,164,159,154,148,142,136,129),		# 10000lb
				(208,204,199,195,190,185,180,175,170,165,159,154,148,142,136,130)),		# 10400lb
				((211,206,200,195,189,184,178,172,166,160,153,146,139,132,124,116),		# 7000lb	+0C
				(210,205,200,194,189,184,178,173,167,131,155,149,142,135,128,120),		# 8000lb
				(209,204,199,194,189,184,179,173,168,162,156,150,144,138,131,124),		# 9000lb
				(207,203,198,193,188,183,178,173,168,162,157,151,146,139,133,126),		# 10000lb
				(207,202,198,193,188,183,178,173,168,163,157,152,147,140,134,127)),		# 10400lb
				((209,204,199,193,188,182,176,170,164,158,151,145,138,130,123,114),		# 7000lb	+10C
				(208,203,198,193,187,182,177,171,165,159,153,147,140,134,126,118),		# 8000lb
				(207,202,197,192,187,182,177,171,166,160,154,148,142,136,129,122),		# 9000lb
				(205,201,196,192,187,181,176,171,166,161,155,150,143,137,131,123),		# 10000lb
				(205,200,196,191,186,181,176,171,166,161,155,150,144,138,132,124)),		# 10400lb
				((208,203,197,192,186,180,175,169,163,156,150,143,136,129,121,112),		# 7000lb	+20C
				(207,202,196,191,186,181,175,170,163,157,151,145,138,132,124,116),		# 8000lb
				(205,200,196,191,186,181,175,170,164,158,153,147,141,134,127,119),		# 9000lb
				(204,199,195,190,185,180,175,169,164,159,153,148,141,135,128,120),		# 10000lb
				(203,199,194,189,184,179,174,169,164,159,154,148,142,136,129,121)),		# 10400lb
				((206,201,196,190,185,179,173,167,161,155,148,142,135,127,119,110),		# 7000lb	+30C
				(205,200,195,190,184,179,174,168,162,156,150,143,137,130,122,114),		# 8000lb
				(204,199,194,189,184,179,173,168,162,157,151,145,139,132,125,116),		# 9000lb
				(202,198,193,188,183,178,173,168,162,157,151,146,140,133,126,117),		# 10000lb
				(202,197,193,188,183,178,173,168,162,157,152,149,140,134,127,118)))		# 10400lb
			dis=tuple(range(-40,31,10))
			
			if wgt>10000:
				wgt_i=wgt/400-22
			else:
				wgt_i=wgt/1000-7
			alt_i=alt/2000
			dis_i=delISA/10+4
			
			wgt_ih, wgt_il, exactwt = self.get_index(wgt_i, len(GW))
			alt_ih, alt_il, exactfl = self.get_index(alt_i, len(alts))
			dis_ih, dis_il, exactdi = self.get_index(dis_i, len(dis))

			#print "al: "+str(round(alt))+" wt: "+str(round(wgt))+" di: "+str(round(delISA))
			#print "index: "+str(alt_il)+" "+str(alt_ih)+" "+str(wgt_il)+" "+str(wgt_ih)+" "+str(dis_il)+" "+str(dis_ih)			

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
			bestCruise=str(int(round(bc)))+" kias"
			
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
		self.Desc="Calculates the current performance info based on POH"
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
		#self.d=chr(0x2103)
		#self.d=u'\xb0'.encode('cp1252')
		self.d=""
			
		self.N1_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_N1_")
		self.EGT_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_EGT_c")
		self.ITT_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_ITT_c")
		self.TRQ_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_TRQ")
		self.eng_type_ref=XPLMFindDataRef("sim/aircraft/prop/acf_en_type")
		self.num_eng_ref=XPLMFindDataRef("sim/aircraft/engine/acf_num_engines")
		self.alt_ref=XPLMFindDataRef("sim/flightmodel/position/elevation")
		self.ias_ref=XPLMFindDataRef("sim/flightmodel/position/indicated_airspeed")
		self.baro_ref=XPLMFindDataRef("sim/weather/barometer_current_inhg")
		self.temp_ref=XPLMFindDataRef("sim/weather/temperature_ambient_c")
		self.wgt_ref=XPLMFindDataRef("sim/flightmodel/weight/m_total")
		self.acf_desc_ref=XPLMFindDataRef("sim/aircraft/view/acf_descrip")
		self.flap_pos_ref=XPLMFindDataRef("sim/flightmodel2/controls/flap_handle_deploy_ratio") # actual position
		self.flap_h_pos_ref=XPLMFindDataRef("sim/cockpit2/controls/flap_ratio") # handle position
		self.geardep_ref=XPLMFindDataRef("sim/aircraft/parts/acf_gear_deploy")
		self.f_norm_ref=XPLMFindDataRef("sim/flightmodel/forces/fnrml_gear")
		self.gear_h_pos_ref=XPLMFindDataRef("sim/cockpit2/controls/gear_handle_down")
		
		self.started=0
		self.Dstarted=0
		self.msg1="Starting..."
		self.msg2=""
		self.msg3=""
		self.msg4=""
		self.msg5=""
		self.msg6=""
		winPosX=20
		winPosY=700
		win_w=270
		win_h=110
		self.num_eng=0
		self.TO_pwr=0
		self.acf_descb=[]
		self.eng_type=[]
		self.flaps_B738=(0.125,0.375,0.625,0.875,1) #1 5 15 30 40
		self.flaps_PC12=(0.3,0.7,1) #15 30 40?

		self.gameLoopCB=self.gameLoopCallback
		self.DrawWindowCB=self.DrawWindowCallback
		self.KeyCB=self.KeyCallback
		self.MouseClickCB=self.MouseClickCallback
		self.gWindow=XPLMCreateWindow(self, winPosX, winPosY, winPosX + win_w, winPosY - win_h, 1, self.DrawWindowCB, self.KeyCB, self.MouseClickCB, 0)

		self.CmdSHConn = XPLMCreateCommand("fsei/flight/perfinfo","Shows or hides performance info")
		self.CmdSHConnCB  = self.CmdSHConnCallback
		XPLMRegisterCommandHandler(self, self.CmdSHConn,  self.CmdSHConnCB, 0, 0)
		
		self.CmdSDConn = XPLMCreateCommand("fsei/flight/descinfo","Shows or hides descent/landing info")
		self.CmdSDConnCB  = self.CmdSDConnCallback
		XPLMRegisterCommandHandler(self, self.CmdSDConn,  self.CmdSDConnCB, 0, 0)
		
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

	def CmdSDConnCallback(self, cmd, phase, refcon):
		if(phase==0): #KeyDown event
			print "XDMG = CMD desc info"
			self.toggleDInfo()
		return 0
	
	def toggleInfo(self):
		if self.started == 0:
			self.num_eng=XPLMGetDatai(self.num_eng_ref)
			XPLMGetDatab(self.acf_desc_ref, self.acf_descb, 0, 500)
			XPLMGetDatavi(self.eng_type_ref, self.eng_type, 0, self.num_eng)
			#print str(self.acf_descb)
			XPLMRegisterFlightLoopCallback(self, self.gameLoopCB, 1, 0)
			self.started=1
		else:
			self.acf_descb=[]
			XPLMDestroyWindow(self, self.gWindow)
			XPLMUnregisterFlightLoopCallback(self, self.gameLoopCB, 0)
			self.started=1
			
	def toggleDInfo(self):
		if self.Dstarted==0:
			self.Dstarted=1
		else:
			self.Dstarted=0

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
		XPLMUnregisterCommandHandler(self, self.CmdSHConn, self.CmdSHConnCB, 0)
		pass

	def XPluginEnable(self):
		return 1

	def XPluginDisable(self):
		pass

	def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
		pass

	def gameLoopCallback(self, inElapsedSinceLastCall, elapsedSim, counter, refcon):
		
		P=XPLMGetDataf(self.baro_ref) #inHg
		T=XPLMGetDataf(self.temp_ref) #deg C
		alt=XPLMGetDataf(self.alt_ref)*self.mft #m -> ft
		wgt=XPLMGetDataf(self.wgt_ref)*self.kglb #kg -> lb
		acf_desc=str(self.acf_descb)
		if self.eng_type[0]==2 or self.eng_type[0]==8: #Turboprop
			TRQ=[]
			XPLMGetDatavf(self.TRQ_ref, TRQ, 0, self.num_eng)
			pwr=str(round(TRQ[0],1))+" Nm"
		elif self.eng_type[0]==4 or self.eng_type[0]==5: #Jet
			N1=[]
			XPLMGetDatavf(self.N1_ref, N1, 0, self.num_eng)
			pwr=str(round(N1[0],1))+"% N1"
		else:
			pwr="N/A"
		#print "B737 part "+acf_desc[0:27]
		if acf_desc[0:27]=="['Boeing 737-800 xversion 4":
			AC="B738"
		elif acf_desc=="['Pilatus PC-12']":
			AC="PC12"
			torque_psi=0.0088168441*TRQ[0]-0.0091189588
			pwr=str(round(torque_psi,1))+" psi"
			if torque_psi>37:
				self.TO_pwr+=inElapsedSinceLastCall
				TO_pwr_remain=300-self.TO_pwr
				TPR_m=int(TO_pwr_remain/60)
				TPR_s=int(TO_pwr_remain%60)
				TO_str=str(TPR_m)+":"+str(TPR_s)+" TO pwr remain"
			else:
				self.TO_pwr=0
				TO_str=""
		else:
			AC=acf_desc
		kias=XPLMGetDataf(self.ias_ref)
		speed=str(int(round(kias)))+" kias"
		DenAlt=self.getDA(P,T) #ft
		#DenAltApprox=self.getDA_approx(P,T) #ft
		delISA=self.getdelISA(alt, T)
		maxPwr=self.getMaxPwr(DenAlt, delISA, AC)
		cruiseclb=self.getCC(DenAlt, alt, delISA, AC)
		cruise=self.getCruise(DenAlt, wgt, alt, delISA, AC)
		maxcruise=self.getMaxCruise(DenAlt, wgt, alt, delISA, AC)
		optFL=self.getOptFL(wgt, AC)
		maxFL=self.getMaxFL(wgt, delISA, AC)
		
		gears=[]
		XPLMGetDatavf(self.geardep_ref, gears, 0, 10)
		#print "Gear "+str(gears[0])
		if gears[0]==1:
			gear_state=1
		else:
			gear_state=0
		Vref="N/A"
		V1="N/A"
		if gear_state==1:
			#print "XDMG = Gear down"
			flaps=XPLMGetDataf(self.flap_h_pos_ref)
			if XPLMGetDataf(self.f_norm_ref) != 0:
				#print "XDMG = On ground"
				V1=self.getV1(flaps, wgt, DenAlt, T, AC)
			else:
				#print "XDMG = In air"
				Vref=self.getVref(flaps, wgt, DenAlt, T, AC)
						
		dIstr=str(int(round(delISA)))+" "+self.d+"C"
		if delISA>0:
			dIstr="+"+dIstr
			
		self.msg1=AC+"  DA: "+str(int(round(DenAlt)))+" ft  GW: "+str(int(round(wgt)))+" lb"
		self.msg2="T: "+str(int(round(T)))+" "+self.d+"C  ISA +/-: "+dIstr+"  "+TO_str
		self.msg3="Pwr: "+maxPwr+"  CC: "+cruiseclb+"  Thr: "+pwr
		self.msg4="Crs: "+maxcruise+"  LR: "+cruise+"  AS: "+speed
		self.msg5="FL: "+maxFL+"  FL: "+optFL#+" Flaps: "+str(flaps)
		self.msg6="V1: "+V1+"  Vref: "+Vref

		return 10
