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
