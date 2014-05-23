#include <math.h>
#include <time.h>
#include <XPLMDataAccess.h>
#include <XPLMMenus.h>
#include <XPWidgets.h>
#include <XPLMProcessing.h>
#include <XPStandardWidgets.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <curl/curl.h>

#define MAX_ENG 8

float kglb = 2.20462262; // conversion constants
float mft = 3.2808399;
float mkt = 1.94384;
float maxC = 0, maxD = 0, maxI = 0, maxG = 0; // flight max values
int OUT = 0, OFF = 0, ON = 0, IN = 0; // flight phase
int Counter = 1; // loop counter
int state = 1; // flight state (clb, desc, lvl)
int ival = 1; // minutes between live reports
int msg = 1; // ACARS message index
char msgc = 'A'; // ACARS message index

time_t OUT_time, OFF_time, ON_time, IN_time; // flight phase times
float Lrate, C_then, BF, FF, ZFW, TOW, LW, OUT_f, OFF_f, ON_f, IN_f, FOB_prev, OUTalt, INalt, IN_net_s; //
int capt_yaeger, capt_smith, delorean, gWidget, num_eng, sWidget;

char pirepurl[64], acarsurl[64], fdurl[64], Ppass[64], fltno[9], tailnum[41], blocktime[6], flighttime[6], Dep[5], Arr[5], OUTlat[12], OUTlon[12], INlat[12], INlon[12], DT[17], Altn[5], Alt[6], Route[256], Type[5], Plan[4], cargo[7], pax[4];
static char DATA1v1[] = "XACARS|1.1", DATA1v2[] = "XACARS|2.0";
// default settings
char pirepurl_def[] = "http://www.swavirtual.com/wn/xacars/pirep.php";
char acarsurl_def[] = "http://www.swavirtual.com/wn/xacars/liveacars.php";
char fdurl_def[] = "http://www.swavirtual.com/wn/xacars/flightdata.php";
//char pirepurl_def[] = "http://www.xacars.net/acars/pirep.php";
//char acarsurl_def[] = "http://www.xacars.net/acars/liveacars.php";
//char fdurl_def[] = "http://www.xacars.net/acars/flightdata.php";
char Ppass_def[] = "pass";
char uname[] = "uname";
char PID[] = "pid";
//char Ppass_def[] = "xactestingpass";
//char uname[] = "xactesting";
//char PID[] = "XAC1001";

static XPLMDataRef eng_run_ref, wt_tot_ref, wt_f_tot_ref, vvi_ref, ias_ref, gs_ref, lat_ref, lon_ref, alt_ref, pbrake_ref, geardep_ref, f_axil_ref, f_side_ref, f_norm_ref, net_ref, tailnum_ref, num_eng_ref, sim_speed_ref, grd_speed_ref, t_le_ref, t_amb_ref, wndk_ref, wndh_ref, en2_ref, en1_ref, hdgt_ref, hdgm_ref, dist_trav_ref;

static XPWidgetID OXWidget, OXWindow, SettingsWidget, SettingsWindow;
static XPWidgetID ACARSInfoButton, SettingsButton, SendButton, StartButton;
static XPWidgetID FltNoText, DepText, ArrText, AltnText, RtText, PaxText, PlanText, TypeText, CargoText, FLText;
static XPWidgetID FltNoCap, DepCap, ArrCap, AltnCap, RtCap, PaxCap, PlanCap, TypeCap, CargoCap, FLCap;
static XPWidgetID DTCap, DTdisp, ZFWCap, ZFWdisp, BTCap, BTdisp, FTCap, FTdisp, TOWCap, TOWdisp, BFCap, BFdisp, FFCap, FFdisp, LWCap, LWdisp;
static XPWidgetID OUTCap, OUTlatdisp, OUTlondisp, OUTaltdisp, INCap, INlatdisp, INlondisp, INaltdisp, MAXCap, maxCdisp, maxslash, maxDdisp, maxICap, maxIdisp, maxGCap, maxGdisp;
static XPWidgetID PIREPCap, PIREPText, ACARSCap, ACARSText, FDCap, FDText, PIDCap, PIDText, PassCap, PassText, SettingsSaveButton;

void myMenuHandler(void *, void *);
void CreateOXWidget(int x1, int y1, int w, int h);
void CreateSettingsWidget(int x1, int y1, int w, int h);
int OXHandler(XPWidgetMessage inMessage, XPWidgetID inWidget, long inParam1, long inParam2);
int SettingsHandler(XPWidgetMessage inMessage, XPWidgetID inWidget, long inParam1, long inParam2);
static float MyFlightLoopCallback(
float inElapsedSinceLastCall,
float inElapsedTimeSinceLastFlightLoop,
int inCounter,
void * inRefcon);

//http://coding.debuntu.org/c-implementing-str_replace-replace-all-occurrences-substring
char * str_replace ( const char *string, const char *substr, const char *replacement ){
  char *tok = NULL;
  char *newstr = NULL;
  char *oldstr = NULL;
  char *head = NULL;

  /* if either substr or replacement is NULL, duplicate string a let caller handle it */
  if ( substr == NULL || replacement == NULL ) return strdup (string);
  newstr = strdup (string);
  head = newstr;
  while ( (tok = strstr ( head, substr ))){
	oldstr = newstr;
	newstr = malloc ( strlen ( oldstr ) - strlen ( substr ) + strlen ( replacement ) + 1 );
	/*failed to alloc mem, free old string and return NULL */
	if ( newstr == NULL ){
	  free (oldstr);
	  return NULL;
	}
	memcpy ( newstr, oldstr, tok - oldstr );
	memcpy ( newstr + (tok - oldstr), replacement, strlen ( replacement ) );
	memcpy ( newstr + (tok - oldstr) + strlen( replacement ), tok + strlen ( substr ), strlen ( oldstr ) - strlen ( substr ) - ( tok - oldstr ) );
	memset ( newstr + strlen ( oldstr ) - strlen ( substr ) + strlen ( replacement ) , 0, 1 );
	/* move back head right after the last replacement */
	head = newstr + (tok - oldstr) + strlen( replacement );
	free (oldstr);
  }
  return newstr;
}

const char * stohhmm(int totalSeconds) {
    int seconds = totalSeconds % 60;
    int minutes = (totalSeconds / 60) % 60;
    int hours = totalSeconds / 3600;
	if ( seconds > 30 )
		minutes++;

	char * hhmmstring = malloc(6);
	snprintf(hhmmstring, sizeof hhmmstring, "%02d:%02d", hours, minutes);

    return hhmmstring;
}

const char * degdm(double decdegrees, int latlon) {
	char * hemi;
	if ( latlon == 0 ) {
		if ( decdegrees > 0 ) {
			hemi = "N";
		} else {
			hemi = "S";
			decdegrees = fabs(decdegrees);
		}
	} else {
		if ( decdegrees > 0 ) {
			hemi = "E";
		} else {
			hemi = "W";
			decdegrees = fabs(decdegrees);
		}
	}
	int degrees = (int)decdegrees;
	double decpart = decdegrees - degrees;
	double minutes = decpart * 60;

	char * locstring = malloc(snprintf(NULL, 0, "%s%u %.4f", hemi, degrees, minutes) + 1);
	sprintf(locstring, "%s%u %.4f", hemi, degrees, minutes);

	return locstring;
}

/*Curl callback*/
size_t static write_callback_func(void *buffer, size_t size, size_t nmemb, void *userp) {
    char **response_ptr = (char**)userp;
    /* assuming the response is a string */
    *response_ptr = strndup(buffer, (size_t)(size *nmemb));
}

PLUGIN_API int XPluginStart(
	char * outName,
	char * outSig,
	char * outDesc)
{
	XPLMMenuID myMenu;
	int mySubMenuItem;

	printf("OXACARS - Starting plugin...\n");
	strcpy(outName, "OXACARS");
	strcpy(outSig, "xplanesdk.crap.oxacars");
	strcpy(outDesc, "XACARS plugin that isn't dumb.");

	mySubMenuItem = XPLMAppendMenuItem(
		XPLMFindPluginsMenu(), /* Put in plugins menu */
		"OXACARS", /* Item Title */
		NULL, /* Item Ref */
		1); /* Force English */
	myMenu = XPLMCreateMenu(
		"OXACARS",
		XPLMFindPluginsMenu(),
		mySubMenuItem, /* Menu Item to attach to. */
		myMenuHandler, /* The handler */
		NULL); /* Handler Ref */
	XPLMAppendMenuItem(
		myMenu,
		"Open OXACARS",
		(void *) +1,
		1);

	gWidget = 0;
	sWidget = 0;
// Use default settings
	strcpy(pirepurl, pirepurl_def);
	strcpy(acarsurl, acarsurl_def);
	strcpy(fdurl, fdurl_def);
	strcpy(Ppass, Ppass_def);

	dist_trav_ref = XPLMFindDataRef("sim/flightmodel/controls/dist"); // float 660+ yes meters Distance Traveled
	eng_run_ref = XPLMFindDataRef("sim/flightmodel/engine/ENGN_running"); // int[8] boolean
	en2_ref = XPLMFindDataRef("sim/flightmodel/engine/ENGN_N2_"); // float[8] 750+ yes percent N2 speed as percent of max (per engine)
	en1_ref = XPLMFindDataRef("sim/flightmodel/engine/ENGN_N1_"); // float[8] 660+ yes percent N1 speed as percent of max (per engine)
	wt_tot_ref = XPLMFindDataRef("sim/flightmodel/weight/m_total"); // float kgs
	wt_f_tot_ref = XPLMFindDataRef("sim/flightmodel/weight/m_fuel_total"); // float kgs
	//sim/aircraft/weight/acf_m_fuel_tot float 660+ yes lbs Weight of total fuel - appears to be in lbs.
	hdgt_ref = XPLMFindDataRef("sim/flightmodel/position/psi"); // float 660+ yes degrees The true heading of the aircraft in degrees from the Z axis
	hdgm_ref = XPLMFindDataRef("sim/flightmodel/position/magpsi"); // float 660+ no degrees The magnetic heading of the aircraft.
	vvi_ref = XPLMFindDataRef("sim/flightmodel/position/vh_ind_fpm"); // float 740+ yes fpm VVI (vertical velocity in feet per second)
	ias_ref = XPLMFindDataRef("sim/flightmodel/position/indicated_airspeed"); // float 660+ yes kias Air speed indicated - this takes into account air density and wind direction
	gs_ref = XPLMFindDataRef("sim/flightmodel/position/groundspeed"); // float meters/sec
	lat_ref = XPLMFindDataRef("sim/flightmodel/position/latitude"); // double degrees
	lon_ref = XPLMFindDataRef("sim/flightmodel/position/longitude"); // double degrees
	alt_ref = XPLMFindDataRef("sim/flightmodel/position/elevation"); // double meters
	pbrake_ref = XPLMFindDataRef("sim/flightmodel/controls/parkbrake"); //float 0-1
	geardep_ref = XPLMFindDataRef("sim/aircraft/parts/acf_gear_deploy"); // float[10] 660+ yes ??? landing gear deployment, 0.0->1.0
	f_axil_ref = XPLMFindDataRef("sim/flightmodel/forces/faxil_gear"); // float 660+ no Newtons Gear/ground forces - downward
	f_side_ref = XPLMFindDataRef("sim/flightmodel/forces/fside_gear"); // float 660+ no Newtons Gear/ground forces - downward
	f_norm_ref = XPLMFindDataRef("sim/flightmodel/forces/fnrml_gear"); // float 660+ no Newtons Gear/ground forces - downward
	net_ref = XPLMFindDataRef("sim/network/misc/network_time_sec"); // float
	wndh_ref = XPLMFindDataRef("sim/weather/wind_direction_degt"); // float 660+ no [0-359) The effective direction of the wind at the plane's location.
	wndk_ref = XPLMFindDataRef("sim/weather/wind_speed_kt"); // float 660+ no kts >= 0 The effective speed of the wind at the plane's location.
	t_amb_ref = XPLMFindDataRef("sim/weather/temperature_ambient_c"); // float 660+ no degrees C The air temperature outside the aircraft (at altitude).
	t_le_ref = XPLMFindDataRef("sim/weather/temperature_le_c"); // float 660+ no degrees C The air temperature at the leading edge of the wings in degrees C.
	tailnum_ref = XPLMFindDataRef("sim/aircraft/view/acf_tailnum"); // byte[40] 660+ yes string Tail number
	num_eng_ref = XPLMFindDataRef("sim/aircraft/engine/acf_num_engines"); // int 660+ yes
	sim_speed_ref = XPLMFindDataRef("sim/time/sim_speed"); // int 860+ yes ratio This is the multiplier for real-time...1 = realtme, 2 = 2x, 0 = paused, etc.
	grd_speed_ref = XPLMFindDataRef("sim/time/ground_speed"); // int 860+ yes ratio This is the multiplier on ground speed, for faster travel via double-distance

	return 1;
}

PLUGIN_API void XPluginStop(void)
{
	/* Unregister the callback */
	XPLMUnregisterFlightLoopCallback(MyFlightLoopCallback, NULL);
	if (gWidget == 1) {
		XPDestroyWidget(OXWidget, 1);
		gWidget = 0;
	}
if (sWidget == 1) {
XPDestroyWidget(SettingsWidget, 1);
sWidget = 0;
}
}

PLUGIN_API void XPluginDisable(void)
{
	XPLMUnregisterFlightLoopCallback(MyFlightLoopCallback, NULL);
}

PLUGIN_API int XPluginEnable(void)
{
	return 1;
}

PLUGIN_API void XPluginReceiveMessage(XPLMPluginID inFrom, long inMsg, void * inParam)
{
}

void myMenuHandler(void * inMenuRef, void * inItemRef)
{
	switch ( (int) inItemRef)
	{
		case 1: if (gWidget == 0)
			{
				CreateOXWidget(50, 712, 974, 662); //left, top, right, bottom.
				gWidget = 1;
			}
			else
			{
				if(!XPIsWidgetVisible(OXWidget))
					XPShowWidget(OXWidget);
			}
			break;
	}
}

//http://www.xsquawkbox.net/xpsdk/mediawiki/Create_Instructions_Widget
void CreateSettingsWidget(int x, int y, int w, int h)
{
	int Index;

	int x2 = x + w;
	int y2 = y - h;

	// Create the Main Widget window.
	SettingsWidget = XPCreateWidget(x, y, x2, y2,
	1, // Visible
	"OXACARS Settings", // desc
	1, // root
	NULL, // no container
	xpWidgetClass_MainWindow);

	// Add Close Box to the Main Widget
	XPSetWidgetProperty(SettingsWidget, xpProperty_MainWindowHasCloseBoxes, 1);

	// Add widgets and stuff
	PIREPCap = XPCreateWidget(x+20, y-40, x+170, y-60,
	1, "PIREP URL", 0, SettingsWidget,
	xpWidgetClass_Caption);

	PIREPText = XPCreateWidget(x+190, y-40, x+500, y-60,
		1, "", 0, SettingsWidget,
		xpWidgetClass_TextField);
		XPSetWidgetProperty(PIREPText, xpProperty_TextFieldType, xpTextEntryField);

	ACARSCap = XPCreateWidget(x+20, y-80, x+170, y-100,
	1, "Live ACARS URL", 0, SettingsWidget,
	xpWidgetClass_Caption);

	ACARSText = XPCreateWidget(x+190, y-80, x+500, y-100,
	1, "", 0, SettingsWidget,
	xpWidgetClass_TextField);
		XPSetWidgetProperty(ACARSText, xpProperty_TextFieldType, xpTextEntryField);

	FDCap = XPCreateWidget(x+20, y-120, x+170, y-140,
	1, "Flight Data URL", 0, SettingsWidget,
	xpWidgetClass_Caption);

	FDText = XPCreateWidget(x+190, y-120, x+500, y-140,
	1, "", 0, SettingsWidget,
	xpWidgetClass_TextField);
		XPSetWidgetProperty(FDText, xpProperty_TextFieldType, xpTextEntryField);

	PIDCap = XPCreateWidget(x+20, y-160, x+60, y-180,
	1, "PID", 0, SettingsWidget,
	xpWidgetClass_Caption);

	PIDText = XPCreateWidget(x+70, y-160, x+120, y-180,
	1, "", 0, SettingsWidget,
	xpWidgetClass_TextField);
	XPSetWidgetProperty(PIDText, xpProperty_TextFieldType, xpTextEntryField);

	PassCap = XPCreateWidget(x+150, y-160, x+190, y-180,
	1, "Pass", 0, SettingsWidget,
	xpWidgetClass_Caption);

	PassText = XPCreateWidget(x+200, y-160, x+300, y-180,
	1, "", 0, SettingsWidget,
	xpWidgetClass_TextField);
	XPSetWidgetProperty(PassText, xpProperty_TextFieldType, xpTextEntryField);
	XPSetWidgetProperty(PassText, xpProperty_PasswordMode, 1);

	SettingsSaveButton = XPCreateWidget(x+20, y-180, x+140, y-200,
	1, "Save", 0, OXWidget,
	xpWidgetClass_Button);
	XPSetWidgetProperty(SettingsSaveButton, xpProperty_ButtonType, xpPushButton);

	XPSetWidgetDescriptor( PIREPText, pirepurl);
	XPSetWidgetDescriptor( ACARSText, acarsurl);
	XPSetWidgetDescriptor( FDText, fdurl);
	XPSetWidgetDescriptor( PIDText, PID);

	// Register our widget handler
	XPAddWidgetCallback(SettingsWidget, SettingsHandler);
}

void CreateOXWidget(int x, int y, int w, int h)
{
int Index;

int x2 = x + w;
int y2 = y - h;

// Create the Main Widget window.
	OXWidget = XPCreateWidget(x, y, x2, y2,
		1, // Visible
		"OXACARS", // desc
		1, // root
		NULL, // no container
		xpWidgetClass_MainWindow);

// Add Close Box to the Main Widget
	XPSetWidgetProperty(OXWidget, xpProperty_MainWindowHasCloseBoxes, 1);

// Add widgets and stuff
	FltNoCap = XPCreateWidget(x+20, y-40, x+80, y-60,
		1, "Flight No.", 0, OXWidget,
		xpWidgetClass_Caption);

	FltNoText = XPCreateWidget(x+100, y-40, x+180, y-60,
		1, "", 0, OXWidget,
		xpWidgetClass_TextField);
	XPSetWidgetProperty(FltNoText, xpProperty_TextFieldType, xpTextEntryField);

	ACARSInfoButton = XPCreateWidget(x+200, y-40, x+300, y-60,
		1, "ACARS Info", 0, OXWidget,
		xpWidgetClass_Button);
	XPSetWidgetProperty(ACARSInfoButton, xpProperty_ButtonType, xpPushButton);

	SettingsButton = XPCreateWidget(x+320, y-40, x+420, y-60,
		1, "Settings", 0, OXWidget,
		xpWidgetClass_Button);
	XPSetWidgetProperty(SettingsButton, xpProperty_ButtonType, xpPushButton);

	DepCap = XPCreateWidget(x+20, y-80, x+50, y-100,
		1, "Dep", 0, OXWidget,
		xpWidgetClass_Caption);

	DepText = XPCreateWidget(x+60, y-80, x+120, y-100,
		1, "", 0, OXWidget,
		xpWidgetClass_TextField);
	XPSetWidgetProperty(DepText, xpProperty_TextFieldType, xpTextEntryField);

	ArrCap = XPCreateWidget(x+150, y-80, x+180, y-100,
		1, "Arr", 0, OXWidget,
		xpWidgetClass_Caption);

	ArrText = XPCreateWidget(x+180, y-80, x+240, y-100,
		1, "", 0, OXWidget,
		xpWidgetClass_TextField);
	XPSetWidgetProperty(ArrText, xpProperty_TextFieldType, xpTextEntryField);

	AltnCap = XPCreateWidget(x+300, y-80, x+330, y-100,
		1, "Altn", 0, OXWidget,
		xpWidgetClass_Caption);

	AltnText = XPCreateWidget(x+340, y-80, x+400, y-100,
		1, "", 0, OXWidget,
		xpWidgetClass_TextField);
	XPSetWidgetProperty(AltnText, xpProperty_TextFieldType, xpTextEntryField);

	RtCap = XPCreateWidget(x+20, y-120, x+60, y-140,
		1, "Route", 0, OXWidget,
		xpWidgetClass_Caption);

	RtText = XPCreateWidget(x+70, y-120, x+430, y-140,
		1, "", 0, OXWidget,
		xpWidgetClass_TextField);
	XPSetWidgetProperty(RtText, xpProperty_TextFieldType, xpTextEntryField);

	PaxCap = XPCreateWidget(x+20, y-160, x+60, y-180,
		1, "Pax", 0, OXWidget,
		xpWidgetClass_Caption);

	PaxText = XPCreateWidget(x+70, y-160, x+120, y-180,
		1, "", 0, OXWidget,
		xpWidgetClass_TextField);
	XPSetWidgetProperty(PaxText, xpProperty_TextFieldType, xpTextEntryField);

	PlanCap = XPCreateWidget(x+150, y-160, x+180, y-180,
		1, "Plan", 0, OXWidget,
		xpWidgetClass_Caption);

	PlanText = XPCreateWidget(x+190, y-160, x+240, y-180,
		1, "", 0, OXWidget,
		xpWidgetClass_TextField);
	XPSetWidgetProperty(PlanText, xpProperty_TextFieldType, xpTextEntryField);

	TypeCap = XPCreateWidget(x+280, y-160, x+310, y-180,
		1, "Type", 0, OXWidget,
		xpWidgetClass_Caption);

	TypeText = XPCreateWidget(x+320, y-160, x+370, y-180,
		1, "", 0, OXWidget,
		xpWidgetClass_TextField);
	XPSetWidgetProperty(TypeText, xpProperty_TextFieldType, xpTextEntryField);

	CargoCap = XPCreateWidget(x+20, y-200, x+60, y-220,
		1, "Cargo", 0, OXWidget,
		xpWidgetClass_Caption);

	CargoText = XPCreateWidget(x+70, y-200, x+120, y-220,
		1, "", 0, OXWidget,
		xpWidgetClass_TextField);
	XPSetWidgetProperty(CargoText, xpProperty_TextFieldType, xpTextEntryField);

	FLCap = XPCreateWidget(x+150, y-200, x+180, y-220,
		1, "Alt", 0, OXWidget,
		xpWidgetClass_Caption);

	FLText = XPCreateWidget(x+190, y-200, x+260, y-220,
		1, "", 0, OXWidget,
		xpWidgetClass_TextField);
	XPSetWidgetProperty(FLText, xpProperty_TextFieldType, xpTextEntryField);

	StartButton = XPCreateWidget(x+280, y-200, x+320, y-220,
		1, "Start", 0, OXWidget,
		xpWidgetClass_Button);
	XPSetWidgetProperty(StartButton, xpProperty_ButtonType, xpPushButton);

	DTCap = XPCreateWidget(x+20, y-240, x+40, y-260,
		1, "DT", 0, OXWidget,
		xpWidgetClass_Caption);

	DTdisp = XPCreateWidget(x+50, y-240, x+220, y-260,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	ZFWCap = XPCreateWidget(x+250, y-240, x+280, y-260,
		1, "ZFW", 0, OXWidget,
		xpWidgetClass_Caption);

	ZFWdisp = XPCreateWidget(x+300, y-240, x+400, y-260,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	BTCap = XPCreateWidget(x+20, y-280, x+40, y-300,
		1, "BT", 0, OXWidget,
		xpWidgetClass_Caption);

	BTdisp = XPCreateWidget(x+50, y-280, x+100, y-300,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	FTCap = XPCreateWidget(x+130, y-280, x+150, y-300,
		1, "FT", 0, OXWidget,
		xpWidgetClass_Caption);

	FTdisp = XPCreateWidget(x+160, y-280, x+210, y-300,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	TOWCap = XPCreateWidget(x+250, y-280, x+280, y-300,
		1, "TOW", 0, OXWidget,
		xpWidgetClass_Caption);

	TOWdisp = XPCreateWidget(x+300, y-280, x+400, y-300,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	BFCap = XPCreateWidget(x+20, y-320, x+40, y-340,
		1, "BF", 0, OXWidget,
		xpWidgetClass_Caption);

	BFdisp = XPCreateWidget(x+50, y-320, x+100, y-340,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	FFCap = XPCreateWidget(x+130, y-320, x+150, y-340,
		1, "FF", 0, OXWidget,
		xpWidgetClass_Caption);

	FFdisp = XPCreateWidget(x+160, y-320, x+210, y-340,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	LWCap = XPCreateWidget(x+250, y-320, x+280, y-340,
		1, "LW", 0, OXWidget,
		xpWidgetClass_Caption);

	LWdisp = XPCreateWidget(x+300, y-320, x+400, y-340,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	OUTCap = XPCreateWidget(x+20, y-360, x+50, y-380,
		1, "OUT", 0, OXWidget,
		xpWidgetClass_Caption);

	OUTlatdisp = XPCreateWidget(x+70, y-360, x+150, y-380,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	OUTlondisp = XPCreateWidget(x+180, y-360, x+260, y-380,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	OUTaltdisp = XPCreateWidget(x+290, y-360, x+350, y-380,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	INCap = XPCreateWidget(x+20, y-400, x+50, y-420,
		1, "IN", 0, OXWidget,
		xpWidgetClass_Caption);

	INlatdisp = XPCreateWidget(x+70, y-400, x+150, y-420,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	INlondisp = XPCreateWidget(x+180, y-400, x+260, y-420,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	INaltdisp = XPCreateWidget(x+290, y-400, x+350, y-420,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	MAXCap = XPCreateWidget(x+20, y-440, x+80, y-460,
		1, "MAX C/D", 0, OXWidget,
		xpWidgetClass_Caption);

	maxCdisp = XPCreateWidget(x+110, y-440, x+140, y-460,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	maxslash = XPCreateWidget(x+150, y-440, x+160, y-460,
		1, "/", 0, OXWidget,
		xpWidgetClass_Caption);

	maxDdisp = XPCreateWidget(x+160, y-440, x+190, y-460,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	maxICap = XPCreateWidget(x+220, y-440, x+250, y-460,
		1, "IAS", 0, OXWidget,
		xpWidgetClass_Caption);

	maxIdisp = XPCreateWidget(x+260, y-440, x+290, y-460,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	maxGCap = XPCreateWidget(x+310, y-440, x+330, y-460,
		1, "GS", 0, OXWidget,
		xpWidgetClass_Caption);

	maxGdisp = XPCreateWidget(x+340, y-440, x+370, y-460,
		1, "", 0, OXWidget,
		xpWidgetClass_Caption);

	SendButton = XPCreateWidget(x+20, y-480, x+140, y-500,
		1, "Send", 0, OXWidget,
		xpWidgetClass_Button);
	XPSetWidgetProperty(SendButton, xpProperty_ButtonType, xpPushButton);

// Register our widget handler
	XPAddWidgetCallback(OXWidget, OXHandler);
}

// This is our widget handler.
int SettingsHandler(XPWidgetMessage inMessage, XPWidgetID inWidget, long inParam1, long inParam2)
{
	if (inMessage == xpMessage_CloseButtonPushed)
	{
		if (sWidget == 1)
		{
			XPHideWidget(SettingsWidget);
			}
				return 1;
			}

			// Test for a button pressed
			if (inMessage == xpMsg_PushButtonPressed) {
				if (inParam1 == (long)SettingsSaveButton) {
					printf("OXACARS - Saving settings...\n");
					XPGetWidgetDescriptor( PIREPText, pirepurl, 63);
					XPGetWidgetDescriptor( ACARSText, acarsurl, 63);
					XPGetWidgetDescriptor( FDText, fdurl, 63);
					XPGetWidgetDescriptor( PIDText, PID, 7);
					}
				}
}

int OXHandler(XPWidgetMessage inMessage, XPWidgetID inWidget, long inParam1, long inParam2)
{
	if (inMessage == xpMessage_CloseButtonPushed)
	{
		if (gWidget == 1)
		{
			XPHideWidget(OXWidget);
		}
		return 1;
	}

	// Test for a button pressed
	if (inMessage == xpMsg_PushButtonPressed)
	{
		if (inParam1 == (long)ACARSInfoButton)
		{
			// ?DATA1=XACARS|1.1&DATA2=XAC1001
			// ?DATA1=XACARS|2.0&DATA2=pid&DATA3=flightplan&DATA4=pid&DATA5=password
			char Altn[5], Alt[6], Route[256], ACType[5], Plan[4], cargo[7], pax[4];
			char *response = NULL;

			printf("OXACARS - Assembling query URL...\n");
			//char * durl = malloc(snprintf(NULL, 0, "%s?DATA1=%s&DATA2=%s", fdurl, DATA1v1, PID) + 1);
			//sprintf(durl, "%s?DATA1=%s&DATA2=%s", fdurl, DATA1v1, PID);

			char * durl = malloc(snprintf(NULL, 0, "DATA1=%s&DATA2=%s&DATA3=flightplan&DATA4=%s&DATA5=%s", DATA1v2, PID, PID, Ppass) + 1);
			sprintf(durl, "DATA1=%s&DATA2=%s&DATA3=flightplan&DATA4=%s&DATA5=%s", DATA1v2, PID, PID, Ppass);

			printf("OXACARS - Will attempt to get %s\n", durl);
			//http://stackoverflow.com/questions/2577654/curl-put-output-into-variable
			CURL *curl;
			CURLcode res;
			curl = curl_easy_init();
			if(curl) {
				curl_easy_setopt(curl, CURLOPT_URL, fdurl);
				curl_easy_setopt(curl, CURLOPT_POSTFIELDS, durl);
				curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback_func);
				curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
				res = curl_easy_perform(curl);
				if(res != CURLE_OK)
				  fprintf(stderr, "curl_easy_perform() failed: %s\n",
					curl_easy_strerror(res));
				curl_easy_cleanup(curl);
			}

			//http://stackoverflow.com/questions/12789883/parallel-to-phps-explode-in-c-split-char-into-char-using-delimiter But I don't wanna explode...
			printf("OXACARS - Now attempting to parse response...\n");
			char ** fd = NULL;
			char * p = strtok (response, "\n");
			int n_spaces = 0, i;

			while (p) {
				fd = realloc (fd, sizeof (char*) * ++n_spaces);
				if (fd == NULL)
					exit (-1); //mem allocation fail
				fd[n_spaces-1] = p;
				p = strtok (NULL, "\n");
			}
			//realloc for last NULL
			fd = realloc (fd, sizeof (char*) * (n_spaces+1));
			fd[n_spaces] = 0;

			strcpy(Dep,fd[1]);
			strcpy(Arr, fd[2]);
			strcpy(Altn, fd[3]);
			//strcpy(Alt, fd[9]); //or not
			strcpy(Route, fd[4]);
			strcpy(ACType, fd[8]);
			strcpy(Plan, fd[7]);
			strcpy(cargo, fd[6]);
			strcpy(pax, fd[5]);

			/*printf("OXACARS - Dep: %s Arr: %s Altn: %s\n", Dep, Arr, Altn);
			printf("OXACARS - Route: %s\n", Route);
			printf("OXACARS - Alt: %s Plan: %s Type: %s\n", Alt, Plan, ACType);
			printf("OXACARS - Pax: %s Cargo: %s\n", pax, cargo);*/

			XPSetWidgetDescriptor( DepText, Dep);
			XPSetWidgetDescriptor( ArrText, Arr);
			XPSetWidgetDescriptor( AltnText, Altn);
			XPSetWidgetDescriptor( RtText, Route);
			XPSetWidgetDescriptor( PlanText, Plan);
			XPSetWidgetDescriptor( TypeText, ACType);
			XPSetWidgetDescriptor( CargoText, cargo);
			XPSetWidgetDescriptor( PaxText, pax);

		}
		if (inParam1 == (long)SettingsButton)
		{
			// open settings stuff
			printf("OXACARS - You pressed the Settings button...\n");
			if (sWidget == 0) {
				CreateSettingsWidget(100, 712, 600, 662); //left, top, right, bottom.
				sWidget = 1;
			} else {
				if(!XPIsWidgetVisible(SettingsWidget))
				XPShowWidget(SettingsWidget);
			}
		}
		if (inParam1 == (long)StartButton) {
			printf("OXACARS - Starting OXACARS monitoring...\n");
			int eng_run[8], i;
			if ( XPLMGetDataf(pbrake_ref) < 1 ) {
				printf("OXACARS - GODDAMN PARKING BRAKE IS SET\n");
				return 0;
			}
			num_eng = XPLMGetDatai( num_eng_ref );
			printf("OXACARS - Found %d engines...\n", num_eng);
			XPLMGetDatavi( eng_run_ref, eng_run, 0, num_eng );
			for ( i = 0; i < num_eng; i++ ) {
				if ( eng_run[i] == 1 ) {
					printf("OXACARS - SHUT OFF THE GODDAMN ENGINES\n");
					return 0;
				}
			}

			char BEGlat[12], BEGlon[12], tailnumbuf[41];
			char * RouteStr = NULL;
			double BEG_lat, BEG_lon, BEG_alt;
			float BEG_f, FW, Elev, hdgm, hdgt, wndh, wndk;
			char *buf = 0;
			void *temp = 0;

			printf("OXACARS - Gathering flight info...\n");
			XPLMGetDatab( tailnum_ref, tailnum, 0, 40 );
			/* XPLMGetDatab( tailnum_ref, tailnumbuf, 0, 40 );
			printf("OXACARS - Tail number is %d long\n",strlen(tailnumbuf));
			temp = realloc(tailnum, strlen(tailnumbuf) + 1);
			if (temp) tailnum = temp;
			strcpy( tailnum, tailnumbuf );*/

			XPGetWidgetDescriptor( PaxText, pax, 3);
			XPGetWidgetDescriptor( FltNoText, fltno, 8);
			XPGetWidgetDescriptor( TypeText, Type, 4);
			XPGetWidgetDescriptor( FLText, Alt, 5);
			XPGetWidgetDescriptor( PlanText, Plan, 3);
			XPGetWidgetDescriptor( DepText, Dep, 4);
			XPGetWidgetDescriptor( ArrText, Arr, 4);
			XPGetWidgetDescriptor( AltnText, Altn, 4);
			XPGetWidgetDescriptor( CargoText, cargo, 6);
			XPGetWidgetDescriptor( RtText, Route, 255);

			RouteStr = str_replace( Route, " ", "~" );

			hdgm = XPLMGetDataf(hdgm_ref);
			wndh = XPLMGetDataf(wndh_ref);
			wndk = XPLMGetDataf(wndk_ref);
			BEG_lat = XPLMGetDatad(lat_ref); // N/Sxx xx.xxxx
			BEG_lon = XPLMGetDatad(lon_ref); //http://data.x-plane.com/designers.html#Hint_LatLonFormat
			BEG_alt = XPLMGetDatad(alt_ref);
			BEG_f = XPLMGetDataf(wt_f_tot_ref);
			strcpy(BEGlat, degdm(BEG_lat, 0));
			strcpy(BEGlon, degdm(BEG_lon, 1));

			FW = BEG_f * kglb;
			Elev = BEG_alt * mft;
			//DATA1=XACARS|2.0&DATA2=BEGINFLIGHT&DATA3=pid||pid|73W||KMDW~PEKUE~OBENE~MONNY~IANNA~FSD~J16~BIL~J136~MLP~GLASR9~KSEA|N34 34.2313 E69 11.6551|5866||||107|180|15414|0|IFR|0|password|&DATA4=

			char * surl = malloc(snprintf(NULL, 0, "DATA1=%s&DATA2=BEGINFLIGHT&DATA3=%s||%s|%s||%s~%s~%s|%s %s|%.0f||||%.0f|%.0f|%.0f%.0f|0|%s|0|%s|&DATA4=", DATA1v2, uname, fltno, Type, Dep, RouteStr, Arr, BEGlat, BEGlon, Elev, FW, hdgm, wndh, wndk, Plan, Ppass) + 1);
			sprintf(surl, "DATA1=%s&DATA2=BEGINFLIGHT&DATA3=%s||%s|%s||%s~%s~%s|%s %s|%.0f||||%.0f|%.0f|%.0f%.0f|0|%s|0|%s|&DATA4=", DATA1v2, uname, fltno, Type, Dep, RouteStr, Arr, BEGlat, BEGlon, Elev, FW, hdgm, wndh, wndk, Plan, Ppass);

			printf("OXACARS - Will send url %s\n", surl);
			/*CURL *curl;
			CURLcode res;
			curl = curl_easy_init();
			if(curl) {
				curl_easy_setopt(curl, CURLOPT_URL, acarsurl);
				curl_easy_setopt(curl, CURLOPT_POSTFIELDS, surl);
				res = curl_easy_perform(curl);
				if(res != CURLE_OK)
				  fprintf(stderr, "curl_easy_perform() failed: %s\n",
					curl_easy_strerror(res));
				curl_easy_cleanup(curl);
			}*/

			XPSetWidgetProperty( PaxText, xpProperty_TextFieldType, xpTextTranslucent);
			XPSetWidgetProperty( FltNoText, xpProperty_TextFieldType, xpTextTranslucent);
			XPSetWidgetProperty( TypeText, xpProperty_TextFieldType, xpTextTranslucent);
			XPSetWidgetProperty( FLText, xpProperty_TextFieldType, xpTextTranslucent);
			XPSetWidgetProperty( PlanText, xpProperty_TextFieldType, xpTextTranslucent);
			XPSetWidgetProperty( DepText, xpProperty_TextFieldType, xpTextTranslucent);
			XPSetWidgetProperty( ArrText, xpProperty_TextFieldType, xpTextTranslucent);
			XPSetWidgetProperty( AltnText, xpProperty_TextFieldType, xpTextTranslucent);
			XPSetWidgetProperty( CargoText, xpProperty_TextFieldType, xpTextTranslucent);
			XPSetWidgetProperty( RtText, xpProperty_TextFieldType, xpTextTranslucent);

			XPLMRegisterFlightLoopCallback(
				MyFlightLoopCallback,
				1.0,
				NULL);
			printf("OXACARS - Registered loop callback, startup complete\n");
		}
		if (inParam1 == (long)SendButton)
		{
			XPLMUnregisterFlightLoopCallback(MyFlightLoopCallback, NULL);
			char online[8];

			/*printf("OXACARS - Defining flight variables...\n");
			time_t OUT_time = 1394204887;
			time_t IN_time = 1394214827;
			time_t OFF_time = 1394204987;
			time_t ON_time = 1394214887;
			float OUT_f = 10000.0;
			float OFF_f = 9500.0;
			float OFF_w = 150000.0;
			float ON_f = 2200.0;
			float ON_w = 142700.0;
			float IN_f = 2100.0;
			double OUT_lat = 45.43210; // N/Sxx xx.xxxx N/E > 0, S/W < 0
			double OUT_lon = -95.43210; // E/Wxx xx.xxxx
			double OUT_alt = 135.0;
			double IN_lat = 44.43210;
			double IN_lon = -90.43210;
			double IN_alt = 583.1;
			float maxC = 4000.0;
			float maxD = 3000.0;
			float maxI = 288.0;
			float maxG = 100.0; */

			//http://www.xacars.net/index.php?Client-Server-Protocol
			printf("Online seconds: %f\n",IN_net_s);
			// if ( IN_net_s > (IN_time - OUT_time) ) { // or...?
			// strcpy(online, "VATSIM");
			// } else {
			strcpy(online, "OFFLINE");
			// }

			/* XPGetWidgetDescriptor( TypeText, Type, 4);
			XPGetWidgetDescriptor( FLText, Alt, 5);
			XPGetWidgetDescriptor( PlanText, Plan, 3);
			XPGetWidgetDescriptor( AltnText, Altn, 4);
			XPGetWidgetDescriptor( PaxText, pax, 3);
			XPGetWidgetDescriptor( CargoText, cargo, 6); */

			printf("OXACARS - This is a lot of information...\n");
			char * DATA2 = malloc(snprintf(NULL, 0, "%s~%s~%s~%s~%s~%s~%s~%s~%s~%s~%s~%s~%.0f~%.0f~%s~%s~%s~%lu~%lu~%lu~%lu~%.0f~%.0f~%.0f~%s~%s~%.0f~%s~%s~%.0f~%.0f~%.0f~%.0f~%.0f", PID, Ppass, fltno, Type, Alt, Plan, Dep, Arr, Altn, DT, blocktime, flighttime, BF, FF, pax, cargo, online, OUT_time, OFF_time, ON_time, IN_time, ZFW, TOW, LW, OUTlat, OUTlon, OUTalt, INlat, INlon, INalt, maxC, -maxD, maxI, maxG) + 1);
			sprintf(DATA2, "%s~%s~%s~%s~%s~%s~%s~%s~%s~%s~%s~%s~%.0f~%.0f~%s~%s~%s~%lu~%lu~%lu~%lu~%.0f~%.0f~%.0f~%s~%s~%.0f~%s~%s~%.0f~%.0f~%.0f~%.0f~%.0f", PID, Ppass, fltno, Type, Alt, Plan, Dep, Arr, Altn, DT, blocktime, flighttime, BF, FF, pax, cargo, online, OUT_time, OFF_time, ON_time, IN_time, ZFW, TOW, LW, OUTlat, OUTlon, OUTalt, INlat, INlon, INalt, maxC, -maxD, maxI, maxG);

			char * purl = malloc(snprintf(NULL, 0, "DATA1=%s&DATA2=%s", DATA1v1, DATA2) + 1);
			sprintf(purl, "DATA1=%s&DATA2=%s", DATA1v1, DATA2);

			printf("OXACARS - Will send url %s\n", purl);
			/*CURL *curl;
			CURLcode res;
			curl = curl_easy_init();
			if(curl) {
				curl_easy_setopt(curl, CURLOPT_URL, pirepurl);
				(curl, CURLOPT_POSTFIELDS, purl);
				res = curl_easy_perform(curl);
				if(res != CURLE_OK)
				  fprintf(stderr, "curl_easy_perform() failed: %s\n",
					curl_easy_strerror(res));
				curl_easy_cleanup(curl);
			}*/
		}
	}
}

//http://www.xsquawkbox.net/xpsdk/mediawiki/TimedProcessing
float MyFlightLoopCallback(
    float inElapsedSinceLastCall,
    float inElapsedTimeSinceLastFlightLoop,
    int inCounter,
    void * inRefcon)
{
	int iter, schg = 0, i, gear_state, hot = 0, cstate, newstate;
	float IAS = XPLMGetDataf(ias_ref), geardep[10], C_now = XPLMGetDataf(vvi_ref);
	double Alt = XPLMGetDatad(alt_ref) * mft;
	char *buf = 0;

if( OFF==1 && ON == 0 ) {
	// Track max values
	float I_now = XPLMGetDataf(ias_ref);
	float G_now = XPLMGetDataf(gs_ref) * mkt;
	if ( C_now > maxC ) {
		maxC = C_now;
		void *temp = realloc(buf, snprintf(NULL, 0, "%.0f", maxC) + 1);
		if (temp) buf = temp;
		sprintf(buf, "%.0f", maxC);
		XPSetWidgetDescriptor( maxCdisp, buf );
	} else if ( C_now < maxD ) {
		maxD = C_now;
		void *temp = realloc(buf, snprintf(NULL, 0, "%.0f", maxD) + 1);
		if (temp) buf = temp;
		sprintf(buf, "%.0f", maxD);
		XPSetWidgetDescriptor( maxDdisp, buf );
	}
	if ( I_now > maxI ) {
		maxI = I_now;
		void *temp = realloc(buf, snprintf(NULL, 0, "%.0f", maxI) + 1);
		if (temp) buf = temp;
		sprintf(buf, "%.0f", maxI);
		XPSetWidgetDescriptor( maxIdisp, buf );
	}
	if ( G_now > maxG ) {
		maxG = G_now;
		void *temp = realloc(buf, snprintf(NULL, 0, "%.0f", maxG) + 1);
		if (temp) buf = temp;
		sprintf(buf, "%.0f", maxG);
		XPSetWidgetDescriptor( maxGdisp, buf );
	}
}

//CLB = 0 LVL = 1 DES = 2

	iter = Counter % ( 60 * ival);
	if ( iter == 0 ) {
		if ( C_now > 500 )
			cstate = 0;
		else if ( C_now < -500 )
			cstate = 2;
		else
			cstate = 1;
		if ( cstate != state )
			newstate = 1;
		else
			newstate = 0;
		schg = 10;
	// printf("Clb: %.0f cstate: %d state: %d newstate: %d",C_now,cstate,state,newstate);
	}

	if ( XPLMGetDatai(sim_speed_ref) > 1 || XPLMGetDatai(grd_speed_ref) > 1 ) // looks like we've got a time traveller here, welcome to the future
		delorean = 1;

	if ( Alt < 10000 && IAS > 270 ) // the FAA will hear about this!
		capt_yaeger = 1;

	// Track flight state

	/*XPLMGetDatai(); //int
	XPLMGetDatavi(); //int array
	XPLMGetDataf(); //flt
	XPLMGetDatavf(); //flt array
	XPLMGetDatad(); //dbl*/

	//f_axil = XPLMGetDataf(f_axil_ref);
	//f_side = XPLMGetDataf(f_side_ref);

	if ( OUT == 0 || ON == 1 && IN == 0 ) {
		int eng_run[8];
		XPLMGetDatavi( eng_run_ref, eng_run, 0, MAX_ENG );
		for ( i = 0; i < num_eng; i++ ) {
			if ( eng_run[i] == 1 )
				hot = 1;
		}
	}

if ( OUT == 1 && OFF == 0 || OFF == 1 && ON == 0 ) {
	XPLMGetDatavf( geardep_ref, geardep, 0, 10);
	gear_state = 1;
	for ( i = 0; i < 10; i++ ) {
		if ( geardep[i] == 0 ) {
			gear_state = 0;
		}
	}
}

	if ( OUT == 0 && hot == 1 ) {
// printf("OXACARS - Detected OUT state...\n");
		OUT = 1;
		schg = 1;
	} else if ( OFF == 0 && OUT == 1 && gear_state == 0 ) {
// printf("OXACARS - Detected OFF state...\n");
		OFF = 1;
		schg = 2;
	} else if ( ON == 0 && OFF == 1 && XPLMGetDataf(f_norm_ref) != 0 && gear_state == 1 ) {
// printf("OXACARS - Detected ON state...\n");
		ON = 1;
		schg = 3;
		Lrate = C_then;
	} else if ( ON == 1 && IN == 0 && hot == 0 && XPLMGetDataf(pbrake_ref) == 1) {
// printf("OXACARS - Detected IN state...\n");
		IN = 1;
		schg = 4;
	}
