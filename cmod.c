#define XPLM200 1

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "SDK/CHeaders/XPLM/XPLMUtilities.h"
#include "SDK/CHeaders/XPLM/XPLMDefs.h"
#include "SDK/CHeaders/XPLM/XPLMDataAccess.h"
#include "SDK/CHeaders/XPLM/XPLMProcessing.h"

static float gameLoopCallback(float inElapsedSinceLastCall,
				float inElapsedTimeSinceLastFlightLoop, int inCounter,	
				void *inRefcon);
static XPLMCommandRef CmdSTConn, CmdLTConn, CmdFTConn, CmdVSupConn, CmdVSdnConn, CmdLCConn, CmdRCConn, CmdUCConn, CmdDCConn, CmdVDConn, CmdVUConn, CmdVLConn, CmdVRConn, CmdCPConn, CmdMBConn, Cmd2BConn, CmdMCConn, CmdMSConn, CmdEOConn, CmdECConn, CmdAMConn, CmdFSConn, CmdSSConn;
int CmdSTConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdLTConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdFTConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdVSupConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdVSdnConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdLCConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdRCConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdUCConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdDCConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdVDConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdVUConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdVLConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdVRConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdCPConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdMBConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int Cmd2BConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdMCConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdMSConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdEOConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdECConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdAMConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdFSConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
int CmdSSConnCB(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
//int MyCommandHandler(XPLMCommandRef inCommand, XPLMCommandPhase inPhase, void * inRefcon);
static XPLMDataRef acf_desc_ref, acf_icao_ref, speed_brake_ref, landing_lights_ref, geardep_ref, gearhand_ref, flap_h_pos_ref, ap_vvi_ref, ap_hdg_ref, ap_ref, trim_ail_ref, trim_elv_ref, view_ref, sbrake_ref, flap_ref, axis_assign_ref, axis_values_ref, axis_min_ref, axis_max_ref, axis_rev_ref, ev_ip_ref, is_ev_ref, trackv_ref, cowl_ref, mach_ref, ap_state_ref, fse_fly_ref, fse_air_ref, fse_conn_ref, sim_time_ref;
static int cmdhold=0;
static int propbrakes=0;
static int propeng=0;
static int assignments[100];
static float mins[100];
static float maxs[100];
static float proprange, propmin;
static int rev, i;
static int propindex=-1;

struct gotAC {
	char AC[5];
	int has3D;
};

void cmdif3D(char *cmd2D, char *cmd3D);
void CondSet(XPLMDataRef apset_ref, XPLMDataRef trim_ref, float ap_del, float trim_del, int phase);
void holdincrement(XPLMDataRef dataref, float del, int num, XPLMCommandPhase phase);
void increment(XPLMDataRef dataref, float del, int num);

struct gotAC getshortac(XPLMDataRef desc_ref, XPLMDataRef icao_ref);

PLUGIN_API int XPluginStart(char *outName, char *outSig, char *outDesc)
{

	strcpy(outName, "Controller Mods in C");
	strcpy(outSig, "natt.python.cmodc");
	strcpy(outDesc, "Command modifications for using controllers, hacked into C");
	
	acf_desc_ref=XPLMFindDataRef("sim/aircraft/view/acf_descrip"); //string array
	acf_icao_ref=XPLMFindDataRef("sim/aircraft/view/acf_ICAO"); //string array
	speed_brake_ref=XPLMFindDataRef("sim/flightmodel/controls/sbrkrqst"); //float -0.5=armed 0=off 1=max
	landing_lights_ref=XPLMFindDataRef("sim/cockpit/electrical/landing_lights_on"); //int
	geardep_ref=XPLMFindDataRef("sim/aircraft/parts/acf_gear_deploy"); //float array
	gearhand_ref=XPLMFindDataRef("sim/cockpit/switches/gear_handle_status"); //int
	flap_h_pos_ref=XPLMFindDataRef("sim/cockpit2/controls/flap_ratio"); //float handle position 0->1
	ap_vvi_ref=XPLMFindDataRef("sim/cockpit/autopilot/vertical_velocity"); //float fpm
	ap_hdg_ref=XPLMFindDataRef("sim/cockpit/autopilot/heading_mag"); //float degm
	ap_ref=XPLMFindDataRef("sim/cockpit/autopilot/autopilot_mode"); //int 0=off 1=FD 2=ON
	mach_ref=XPLMFindDataRef("sim/cockpit/autopilot/airspeed_is_mach"); //int boolean
	ap_state_ref=XPLMFindDataRef("sim/cockpit/autopilot/autopilot_state"); //int flags
	trim_ail_ref=XPLMFindDataRef("sim/flightmodel/controls/ail_trim"); //float -1=left ... 1=right
	trim_elv_ref=XPLMFindDataRef("sim/flightmodel/controls/elv_trim"); //float -1=down ... 1=up
	view_ref=XPLMFindDataRef("sim/graphics/view/view_type"); //int see docs
	sbrake_ref=XPLMFindDataRef("sim/cockpit2/controls/speedbrake_ratio");
	flap_ref=XPLMFindDataRef("sim/cockpit2/controls/flap_ratio");
	
	axis_assign_ref=XPLMFindDataRef("sim/joystick/joystick_axis_assignments");	// int[100] - prop=7
	axis_values_ref=XPLMFindDataRef("sim/joystick/joystick_axis_values");
	axis_min_ref=XPLMFindDataRef("sim/joystick/joystick_axis_minimum");
	axis_max_ref=XPLMFindDataRef("sim/joystick/joystick_axis_maximum");
	axis_rev_ref=XPLMFindDataRef("sim/joystick/joystick_axis_reverse");
	
	ev_ip_ref=XPLMFindDataRef("sim/network/dataout/external_visual_ip"); //int[20]
	is_ev_ref=XPLMFindDataRef("sim/network/dataout/is_external_visual"); //int
	trackv_ref=XPLMFindDataRef("sim/network/dataout/track_external_visual"); //int[20]
	cowl_ref=XPLMFindDataRef("sim/flightmodel/engine/ENGN_cowl"); //float[8]  0 = closed, 1 = open
	
	fse_conn_ref=XPLMFindDataRef("fse/status/connected"); //int
	fse_fly_ref=XPLMFindDataRef("fse/status/flying"); //int
	fse_air_ref=XPLMFindDataRef("fse/status/airborne"); //int

	sim_time_ref=XPLMFindDataRef("sim/time/sim_speed"); //int
	
	CmdSTConn = XPLMCreateCommand("cmod/toggle/speedbrake","Toggles speed brakes");
	XPLMRegisterCommandHandler(CmdSTConn, CmdSTConnCB, 0, (void *) 0);
	
	CmdLTConn = XPLMCreateCommand("cmod/toggle/landinggearlights","Toggles landing gear and lights");
	XPLMRegisterCommandHandler(CmdLTConn, CmdLTConnCB, 0, (void *) 0);
	
	CmdFTConn = XPLMCreateCommand("cmod/toggle/flaps","Toggles through flaps settings");
	XPLMRegisterCommandHandler(CmdFTConn, CmdFTConnCB, 0, (void *) 0);
	
	CmdVSupConn = XPLMCreateCommand("cmod/custom/vspeed_up","AP vertical speed set +100 fpm");
	XPLMRegisterCommandHandler(CmdVSupConn, CmdVSupConnCB, 0, (void *) 0);
	
	CmdVSdnConn = XPLMCreateCommand("cmod/custom/vspeed_down","AP vertical speed set -100 fpm");
	XPLMRegisterCommandHandler(CmdVSdnConn, CmdVSdnConnCB, 0, (void *) 0);
	
	CmdLCConn = XPLMCreateCommand("cmod/custom/left_cond","If AP: HDG left 1 degree, } else { Aileron trim left");
	XPLMRegisterCommandHandler(CmdLCConn, CmdLCConnCB, 0, (void *) 0);
	
	CmdRCConn = XPLMCreateCommand("cmod/custom/right_cond","If AP: HDG right 1 degree, } else { Aileron trim right");
	XPLMRegisterCommandHandler(CmdRCConn, CmdRCConnCB, 0, (void *) 0);
	
	CmdUCConn = XPLMCreateCommand("cmod/custom/up_cond","If AP: VS +100 fpm, } else { Elevator trim up");
	XPLMRegisterCommandHandler(CmdUCConn, CmdUCConnCB, 0, (void *) 0);
	
	CmdDCConn = XPLMCreateCommand("cmod/custom/down_cond","If AP: VS -100fpm, } else { Elevator trim down");
	XPLMRegisterCommandHandler(CmdDCConn, CmdDCConnCB, 0, (void *) 0);
	
	// CmdRUCConn = XPLMCreateCommand("cmod/custom/right_up_cond","Based on view");
	// XPLMRegisterCommandHandler(CmdRUCConn, CmdRUCConnCB, 0, (void *) 0);
	
	// CmdCConn = XPLMCreateCommand("cmod/custom/right_up_cond","Cockpit view right/up based on airplane");
	// XPLMRegisterCommandHandler(CmdCConn, CmdCConnCB, 0, (void *) 0);
	
	CmdVDConn = XPLMCreateCommand("cmod/custom/view_down_cond","Cockpit view down based on airplane");
	XPLMRegisterCommandHandler(CmdVDConn, CmdVDConnCB, 0, (void *) 0);
	
	CmdVUConn = XPLMCreateCommand("cmod/custom/view_up_cond","Cockpit view up based on airplane");
	XPLMRegisterCommandHandler(CmdVUConn, CmdVUConnCB, 0, (void *) 0);
	
	CmdVLConn = XPLMCreateCommand("cmod/custom/view_left_cond","Cockpit view left based on airplane");
	XPLMRegisterCommandHandler(CmdVLConn, CmdVLConnCB, 0, (void *) 0);
	
	CmdVRConn = XPLMCreateCommand("cmod/custom/view_right_cond","Cockpit view right based on airplane");
	XPLMRegisterCommandHandler(CmdVRConn, CmdVRConnCB, 0, (void *) 0);
	
	CmdCPConn = XPLMCreateCommand("cmod/custom/view_cockpit_cond","Cockpit front view based on airplane");
	XPLMRegisterCommandHandler(CmdCPConn, CmdCPConnCB, 0, (void *) 0);
	
	CmdMBConn = XPLMCreateCommand("cmod/custom/prop_speedbrakes","Use prop axis for speed brakes");
	XPLMRegisterCommandHandler(CmdMBConn, CmdMBConnCB, 0, (void *) 0);
	
	Cmd2BConn = XPLMCreateCommand("cmod/custom/prop_eng2","Use prop axis for eng 2");
	XPLMRegisterCommandHandler(Cmd2BConn, Cmd2BConnCB, 0, (void *) 0);
	
	CmdMCConn = XPLMCreateCommand("cmod/custom/engine_mach_cutoff","AC Conditional - mach hold or cutoff protection");
	XPLMRegisterCommandHandler(CmdMCConn, CmdMCConnCB, 0, (void *) 0);
	
	CmdMSConn = XPLMCreateCommand("cmod/toggle/externvisual","Toggle computer role as master or slave");
	XPLMRegisterCommandHandler(CmdMSConn, CmdMSConnCB, 0, (void *) 0);
	
	CmdECConn = XPLMCreateCommand("cmod/custom/engine_cowl_close","Close engine cowl by small amount");
	XPLMRegisterCommandHandler(CmdECConn, CmdECConnCB, 0, (void *) 0);
	
	CmdEOConn = XPLMCreateCommand("cmod/custom/engine_cowl_open","Open engine cowl by small amount");
	XPLMRegisterCommandHandler(CmdEOConn, CmdEOConnCB, 0, (void *) 0);
	
	CmdAMConn = XPLMCreateCommand("cmod/toggle/airspeed_is_mach","Toggle autopilot airspeed knots/mach");
	XPLMRegisterCommandHandler(CmdAMConn, CmdAMConnCB, 0, (void *) 0);
	
	CmdFSConn = XPLMCreateCommand("cmod/toggle/fseflight","Login/begin/cancel/end FSE flight");
	XPLMRegisterCommandHandler(CmdFSConn, CmdFSConnCB, 0, (void *) 0);

	CmdSSConn = XPLMCreateCommand("cmod/toggle/simtime","Bigger change sim time speed");
	XPLMRegisterCommandHandler(CmdSSConn, CmdSSConnCB, 0, (void *) 0);

	printf("CMOD - plugin loaded\n");	

	return 1;
}

PLUGIN_API void	XPluginStop(void)
{
	XPLMUnregisterCommandHandler(CmdSTConn, CmdSTConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdLTConn, CmdLTConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdFTConn, CmdFTConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdVSupConn, CmdVSupConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdVSdnConn, CmdVSdnConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdLCConn, CmdLCConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdRCConn, CmdRCConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdUCConn, CmdUCConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdDCConn, CmdDCConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdVDConn, CmdVDConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdVUConn, CmdVUConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdVLConn, CmdVLConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdVRConn, CmdVRConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdCPConn, CmdCPConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdMBConn, CmdMBConnCB, 0, 0);
	XPLMUnregisterCommandHandler(Cmd2BConn, Cmd2BConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdMCConn, CmdMCConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdMSConn, CmdMSConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdECConn, CmdECConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdEOConn, CmdEOConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdAMConn, CmdAMConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdFSConn, CmdFSConnCB, 0, 0);
	XPLMUnregisterCommandHandler(CmdSSConn, CmdSSConnCB, 0, 0);
	if (propbrakes==1)
			CmdMBConnCB(NULL, 0, NULL);
}

PLUGIN_API void XPluginDisable(void)
{
}

PLUGIN_API int XPluginEnable(void)
{
	return 1;
}

PLUGIN_API void XPluginReceiveMessage(XPLMPluginID inFromWho,
				long inMessage,	void *inParam)
{
}

int CmdSTConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Toggle speedbrakes
	if (phase==0) { //KeyDown event
		float position;
		position=XPLMGetDataf(speed_brake_ref);
		if (position<1) { //armed, stowed, or not fully deployed
			XPLMSetDataf(speed_brake_ref, 1.0); //Deploy
		} else { //fully deployed
			XPLMSetDataf(speed_brake_ref, -0.5); //Armed
		}
	}
	return 0;
}

int CmdLTConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Toggle landing gear and lights together
	if (phase==0) { //KeyDown event
		int gear, light;
		gear=XPLMGetDatai(gearhand_ref);
		light=XPLMGetDatai(landing_lights_ref);
		//print "CMOD - gear = "+str(gear)+"  light = "+str(light)
		if (gear==0 || light==0) { //Gear handle up->down, may need second go at landing light
			XPLMSetDatai(gearhand_ref, 1);
			XPLMSetDatai(landing_lights_ref, 1);
		} else { //Gear handle down->up
			XPLMSetDatai(landing_lights_ref, 0);
			XPLMSetDatai(gearhand_ref, 0);
		}
	}
	return 0;
}

int CmdFTConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Flaps +1, retract if fully deployed
	if (phase==0) { //KeyDown event
		float handle;
		handle=XPLMGetDataf(flap_h_pos_ref);
		if (handle==1) { //Fully deployed
			XPLMSetDataf(flap_h_pos_ref, 0.0); //Retract full
		} else {
			XPLMCommandRef flap_down_cmd=NULL;
			flap_down_cmd=XPLMFindCommand("sim/flight_controls/flaps_down");
			if (flap_down_cmd) {
				//print "XDMG = Found command, flaps down"
				XPLMCommandOnce(flap_down_cmd);
			}
		// ac=getshortac(acf_desc_ref, acf_icao_ref)
		// handle=XPLMGetDataf(flap_h_pos_ref)
		// if handle==1: //Fully deployed
			// XPLMSetDataf(flap_h_pos_ref, 0.0) //Retract full
		// } else { //Set next detent
			// if ac=="PC12":
				// flaps=(0.3,0.7,1.0) //15 30 40
				// nextflaps(handle, flaps)
			// elif ac=="B738":
				// flaps=(0.125,0.375,0.625,0.875,1.0) //1 5 15 30 40
				// nextflaps(handle, flaps)
			// } else { //Fully deploy
				// XPLMSetDataf(flap_h_pos_ref, 1.0)
		}
	}
	return 0;
}

int CmdVSupConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //AP vertical speed +100 fpm
	if (phase==0) { //KeyDown event
		float vvi;
		vvi=XPLMGetDataf(ap_vvi_ref);
		XPLMSetDataf(ap_vvi_ref, vvi+100);
	}
	return 0;
}

int CmdVSdnConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //AP vertical speed -100 fpm
	if (phase==0) { //KeyDown event
		float vvi;
		vvi=XPLMGetDataf(ap_vvi_ref);
		XPLMSetDataf(ap_vvi_ref, vvi-100);
	}
	return 0;
}

int CmdLCConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Left hdg or aileron trim
	CondSet(ap_hdg_ref, trim_ail_ref, -1, -0.01, phase);
	return 0;
}

int CmdRCConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Right hdg or aileron trim
	CondSet(ap_hdg_ref, trim_ail_ref, 1, 0.01, phase);
	return 0;
}

int CmdDCConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Down vert speed or elev trim
	CondSet(ap_vvi_ref, trim_elv_ref, -100, -0.01, phase);
	return 0;
}

int CmdUCConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Up vert speed or elev trim
	CondSet(ap_vvi_ref, trim_elv_ref, 100, 0.01, phase);
	return 0;
}

int CmdVDConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Cockpit view down based on airplane
	cmdif3D("sim/general/down_fast","sim/view/pan_down_fast");
	return 0;
}
int CmdVUConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Cockpit view up based on airplane
	cmdif3D("sim/general/up_fast","sim/view/pan_up_fast");
	return 0;
}
int CmdVLConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Cockpit view left based on airplane
	cmdif3D("sim/general/left_fast","sim/view/pan_left_fast");
	return 0;
}
int CmdVRConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Cockpit view right based on airplane
	cmdif3D("sim/general/right_fast","sim/view/pan_right_fast");
	return 0;
}

int CmdCPConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Cockpit view based on airplane
	if (phase==0) { //KeyDown event
		cmdif3D("sim/view/forward_with_panel","sim/view/3d_cockpit_cmnd_look");
	}
	return 0;
}

int CmdMSConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Toggle master/slave status
	if (phase==0) { //KeyDown event
		//print "Settings for network:"
		int ips[20], tracks[20];
		int isev=0;
		XPLMGetDatavi(ev_ip_ref, ips, 0, 20);
		XPLMGetDatavi(trackv_ref, tracks, 0, 20);
		isev=XPLMGetDatai(is_ev_ref);
		//print "Is extern visual:"+str(isev)
		for (i=0; i<20; i++) {
			printf("%i (%i) ",ips[i], tracks[i]);
			if (i%5==0)
				printf ("\n");
		}
		// ip=102 if ips[0]==103 else 103
		// ips[0]=ip
		// tracks[0]=0
		// if isev==1:
			// XPLMSetDatai(is_ev_ref,0)
		// } else {
			// XPLMSetDatai(is_ev_ref,1)
		// XPLMSetDatavi(ev_ip_ref, ips, 0, 20)
		// XPLMSetDatavi(trackv_ref, tracks, 0, 20)
	}
	return 0;
}

int CmdMBConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //prop axis for speed brakes
	if (phase==0) {
		if (propbrakes==0) {
			float mins[100], maxs[100];
			int assignments[100], revs[100];
			XPLMGetDatavi(axis_assign_ref, assignments, 0, 100);
			XPLMGetDatavf(axis_min_ref, mins, 0, 100);
			XPLMGetDatavf(axis_max_ref, maxs, 0, 100);
			XPLMGetDatavi(axis_rev_ref, revs, 0, 100);
			for (i=0; i<100; i++) {
				if (assignments[i]==7) { //Guess?
					propindex=i;
					break;
				}
			}
			propindex=13; //At long last
			if (propindex>-1) {
				if (revs[propindex]==1) { //Evidently we DO want the reverse of this axis
					rev=0;
				} else {
					rev=1;
				}
				float propmax;
				propmin=mins[0];
				propmax=maxs[0];
				proprange=propmax-propmin;
				XPLMRegisterFlightLoopCallback(gameLoopCallback, 0.5, NULL);
				XPLMSpeakString("Started propbrake");
				propbrakes=1;
			}
		} else {
			XPLMUnregisterFlightLoopCallback(gameLoopCallback, NULL);
			propbrakes=0;
			XPLMSpeakString("Stopped propbrake");
		}
	}
	return 0;
}

int CmdMCConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Mach/cutoff protect vased on AC
	if (phase==0) {
		char *ac, *cmdref;
		int has3D;
		struct gotAC thisAC;
		XPLMCommandRef got_cmd;
		thisAC=getshortac(acf_desc_ref, acf_icao_ref);
		if (strcmp(thisAC.AC,"CL30")==0) {
			strcpy(cmdref,"cl300/mach_hold");
		} else if (strcmp(thisAC.AC,"PC12")==0) {
			strcpy(cmdref,"pc12/engine/cutoff_protection_toggle");
		} else {
			strcpy(cmdref,"sim/ice/anti_ice_toggle");
		}
		got_cmd=XPLMFindCommand(cmdref);
		if (got_cmd) {
			XPLMDebugString("CMOD - Running switch command");
			XPLMCommandOnce(got_cmd);
		}
	}
	return 0;
}

int CmdECConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //cowl flaps control
	holdincrement(cowl_ref, 0.1, 8, phase);
	return 0;
}

int CmdEOConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //cowl flaps control
	holdincrement(cowl_ref, -0.1, 8, phase);
	return 0;
}

int CmdAMConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //autopilot speed knots/mach
	if (phase==0) {
		int ismach=XPLMGetDatai(mach_ref);
		if (ismach==0) {
			XPLMSetDatai(mach_ref,1);
		} else {
			XPLMSetDatai(mach_ref,0);
		}
	}
	return 0;
}

int CmdFSConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //FSE flight login/begin/cancel/end
	if (phase==0) {
		XPLMCommandRef fse_cmd;
		int loggedin=XPLMGetDatai(fse_conn_ref);
		int flying=XPLMGetDatai(fse_fly_ref);
		int airborne=XPLMGetDatai(fse_air_ref);
		if (loggedin==0) {
			fse_cmd=XPLMFindCommand("fse/server/connect");
		} else if (flying==0) {
			fse_cmd=XPLMFindCommand("fse/flight/start");
		} else if (airborne==1) {
			fse_cmd=XPLMFindCommand("fse/flight/cancelArm");
		} else {
			fse_cmd=XPLMFindCommand("fse/flight/finish");
		}
		if (fse_cmd)
			XPLMCommandOnce(fse_cmd);
	}
	return 0;
}

int CmdSSConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //FSE flight login/begin/cancel/end
	XPLMDebugString("CMOD - Going full potato");
	if (phase==0) {
		int simtime=XPLMGetDatai(sim_time_ref);
		if (simtime<32) {
			XPLMDebugString("CMOD - Going to 32");
			simtime=32;
		} else {
			XPLMDebugString("CMOD - Going to 1");
			simtime=1;
		}
		XPLMSetDatai(sim_time_ref, simtime);
	}
	return 0;
}

void holdincrement(XPLMDataRef dataref, float del, int num, XPLMCommandPhase phase) {
	if (phase==0) {
		increment(dataref, del, num);
	} else if (phase==1) {
		if (cmdhold>10 && cmdhold%3==0) {
			increment(dataref, del, num);
		}
		cmdhold+=1;
	} else if (phase==2)
		cmdhold=0;
}

void increment(XPLMDataRef dataref, float del, int num) {
	if (num>1) {
		float datarray[num];
		int i;
		XPLMGetDatavf(dataref, datarray, 0, num);
		for (i=0; i<num; i++) {
			datarray[i]=datarray[i]+del;
		}
		XPLMSetDatavf(dataref, datarray, 0, num);
	} else {
		float data;
		data=XPLMGetDataf(dataref);
		XPLMSetDataf(dataref, data+del);
	}
}

int Cmd2BConnCB(XPLMCommandRef cmd, XPLMCommandPhase phase, void * refcon) { //Prop axis controls engine 2
	if (phase==0) {
		int assignments[100];
		XPLMGetDatavi(axis_assign_ref, assignments, 0, 100);
		if (propeng==1) {
			for (i=0; i<100; i++) {
				if (assignments[i]==22) { //FIX ME eng2
					assignments[i]=13;
					break;
				}
			}
			propeng=0;
		} else {
			for (i=0; i<100; i++) {
				if (assignments[i]==13) {
					assignments[i]=22; //FIX ME eng2 throttle
					break;
				}
			}
			propeng=1;
		}
		XPLMSetDatavi(axis_assign_ref, assignments, 0, 100);
	}
	return 0;
}

void cmdif3D(char *cmd2D, char *cmd3D) { //Run command depending on 3D cockpit
	char * ac;
	int view, chgview;
	struct gotAC thisAC;
	XPLMCommandRef view_cmd;
	thisAC=getshortac(acf_desc_ref, acf_icao_ref);
	view=XPLMGetDatai(view_ref);
	char *buf;
	size_t sz;
	sz = snprintf(NULL,0,"CMOD - AC %s has3D=%i view=%i\n",thisAC.AC,thisAC.has3D,view);
	buf = (char *)malloc(sz+1);
	snprintf(buf,sz+1,"CMOD - AC %s has3D=%i view=%i\n",thisAC.AC,thisAC.has3D,view);
	if (strcmp("sim/view/forward_with_panel",cmd2D)==0) {
		chgview=1;
	} else {
		chgview=0;
	}
	if (thisAC.has3D==1 && ((view!=1017 && view!=1018) || (chgview==1))) { //view 3D
		view_cmd=XPLMFindCommand(cmd3D);
	} else { //view 2D
		view_cmd=XPLMFindCommand(cmd2D);
	}
	if (view_cmd) {
		XPLMCommandOnce(view_cmd);
	} else {
		printf ("XDMG = Couldn't find one of '%s' or '%s'\n",cmd2D,cmd3D);
	}
}

void CondSet(XPLMDataRef apset_ref, XPLMDataRef trim_ref, float ap_del, float trim_del, int phase) { //Set AP ref+del if AP on, else set trim ref+del
	int ap;
	ap=XPLMGetDatai(ap_ref);
	if (ap==2) {
		holdincrement(apset_ref, ap_del, 1, phase);
	} else if (ap!=2) {
		XPLMCommandRef trim_cmd;
		if (trim_ref==trim_elv_ref) {
			if (trim_del>0) {
				trim_cmd=XPLMFindCommand("sim/flight_controls/pitch_trim_up");
			} else {
				trim_cmd=XPLMFindCommand("sim/flight_controls/pitch_trim_down");
			}
		} else if (trim_ref==trim_ail_ref) {
			if (trim_del>0) {
				trim_cmd=XPLMFindCommand("sim/flight_controls/aileron_trim_right");
			} else {
				trim_cmd=XPLMFindCommand("sim/flight_controls/aileron_trim_left");
			}
		}
		if (trim_cmd) {
			if (phase==0) {
				XPLMCommandBegin(trim_cmd);
			} else if (phase==2) {
				XPLMCommandEnd(trim_cmd);
			}
		}
	}
}

static float gameLoopCallback(float elapsedSinceLastCall, float inElapsedSim, int counter, void *refcon) {
	//Get current conditions
	float vals[100], propaxis, proper;
	XPLMGetDatavf(axis_values_ref, vals, 0, 100);
	propaxis=vals[propindex];
	proper=(propaxis-propmin)/proprange;
	if (rev==1)
		proper=1-proper;
	if (proper<.0001)
		proper=-0.5;
	XPLMSetDataf(sbrake_ref,proper);
	return 0.5;
}

// void nextflaps(float handle, float flaps[10]):
	// i=0
	// while handle<flaps[i]+0.001:
		// i+=1
	// XPLMSetDataf(flap_h_pos_ref, flaps[i])
	
// sim/autopilot/level_change
// sim/autopilot/heading
// sim/autopilot/FMS
// http://www.xsquawkbox.net/xpsdk/mediawiki/sim%252Fcockpit%252Fautopilot%252Fautopilot_state

struct gotAC getshortac(XPLMDataRef desc_ref, XPLMDataRef icao_ref) {
	struct gotAC thisAC;
	char acf_descb[261], acf_icaob[41];
	char buffer[14], ibuffer[5];
	XPLMGetDatab(desc_ref, acf_descb, 0, 260);
	XPLMGetDatab(icao_ref, acf_icaob, 0, 40);
	strncpy(buffer, acf_descb, 13);
	buffer[13]='\0';
	strncpy(ibuffer, acf_icaob, 4);
	ibuffer[5]='\0';
	if (strcmp(buffer, "Boeing 737-80")==0 || strcmp(ibuffer, "B738")==0) {
		strncpy(thisAC.AC,"B738",4);
		thisAC.has3D=1;
	} else if (strcmp(buffer, "Pilatus PC-12")==0 || strcmp(ibuffer, "PC12")==0) {
		strncpy(thisAC.AC,"PC12",4);
		thisAC.has3D=1;
	} else if (strcmp(buffer, "B1900 for X-p")==0 || strcmp(ibuffer, "BE19")==0) {
		strncpy(thisAC.AC,"B190",4);
		thisAC.has3D=1;
	} else if (strcmp(buffer, "Bombardier Ch")==0 || strcmp(ibuffer, "CL30")==0) {
		strncpy(thisAC.AC,"CL30",4);
		thisAC.has3D=1;
	} else if (strcmp(buffer, "C208B Grand C")==0 || strcmp(ibuffer, "C208")==0) {
		strncpy(thisAC.AC,"C208",4);
		thisAC.has3D=1;
	} else if (strcmp(buffer, "C-27J Spartan")==0 || strcmp(ibuffer, "C27J")==0) {
		strncpy(thisAC.AC,"C27J",4);
		thisAC.has3D=1;
	} else if (strcmp(buffer, "Ilushin IL-14")==0 || strcmp(ibuffer, "IL14")==0) {
		strncpy(thisAC.AC,"IL14",4);
		thisAC.has3D=1;
	} else if (strcmp(buffer, "Dassault Falc")==0 || strcmp(ibuffer, "FA7X")==0) { //FIX ME
		strncpy(thisAC.AC,"FA7X",4);
		thisAC.has3D=1;
	} else if (strcmp(buffer, "Antonov An-2")==0 || strcmp(ibuffer, "AN2")==0) { //FIX ME
		strncpy(thisAC.AC,"AN-2",4);
		thisAC.has3D=1;
	} else if (strcmp(buffer, "Beechcraft Ki")==0 || strcmp(ibuffer, "C90B")==0) { //FIX ME
		strncpy(thisAC.AC,"C90B",4);
		thisAC.has3D=1;
	} else if (strcmp(buffer, "Boeing 747-40")==0 || strcmp(ibuffer, "B744")==0) { //FIX ME
		strncpy(thisAC.AC,"B744",4);
		thisAC.has3D=1;
	} else {
		strncpy(acf_descb,thisAC.AC,4);
		thisAC.has3D=0;
		char *buf;
		size_t sz;
		sz = snprintf(NULL,0,"CMOD - not recognizing AC: %s\n",acf_descb);
		buf = (char *)malloc(sz+1);
		snprintf(buf,sz+1,"CMOD - not recognizing AC: %s\n",acf_descb);
		free(buf);
		sz = snprintf(NULL,0,"CMOD - used buffer: %s\n",buffer);
		buf = (char *)malloc(sz+1);
		snprintf(buf,sz+1,"CMOD - used buffer: %s\n",buffer);
	}
	thisAC.AC[4]='\0';
	return thisAC;
}
