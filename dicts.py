#!/usr/bin/python

def getactypedict():
	dict={"B461": "BAe 146-100 (Avro RJ70)",
	"CRJ7": "Bombardier CRJ700-ER",
	"BR30": "Bristol Britannia 300",
	"DC7C": "Douglas DC-7C",
	"DH8D": "Bombardier Dash-8 Q400",
	"IL18": "Ilyushin Il-18D",
	"L188": "Lockheed P-3C (L-188)",
	"DC7B": "Douglas DC-7B",
	"DC6B": "Douglas DC-6B",
	"CRJ2": "Bombardier CRJ-200ER",
	"T124": "Tupolev Tu-124",
	"DC4M": "Douglas DC-4",
	"E145": "Embraer ERJ-145LR",
	"B377": "Boeing 377",
	"E135": "Embraer ERJ-135LR",
	"CONI": "Lockheed Constellation",
	"VISC": "Vickers Viscount",
	"AT75": "ATR 72-500",
	"C130": "Lockheed C-130 (Generic)",
	"C130i": "Lockheed C-130 (Capt Sim)",
	"DH8C": "DeHavilland Dash 8 Q300",
	"F27": "Fokker F27-500 Friendship",
	"AN32": "Antonov An-32",
	"DC6": "Douglas DC-6",
	"CVLT": "Convair 580",
	"C27J": "Alenia C-27J Spartan (IRIS)",
	"C27Ji": "Alenia C-27J Spartan",
	"DHC7": "DeHavilland Dash 7",
	"C119": "Fairchild C119",
	"A748": "Hawker Siddeley HS-748",
	"AT45": "ATR 42-500",
	"AN24": "Antonov An-24",
	"AS57": "Airspeed AS-57 Ambassador",
	"CN35": "CASA CN235",
	"CVLP": "Convair 340/440",
	"M404": "Martin 404",
	"DHC5": "DeHavilland DHC-5 Buffalo",
	"SF34": "Saab 340B",
	"AN26": "Antonov An-26 Curl",
	"DH8A": "DeHavilland Dash 8 100/200",
	"SH36": "Shorts SD3-60",
	"B17G": "Boeing B-17G",
	"E120": "Embraer 120",
	"YK40": "Yakovlev Yak-40",
	"SF90": "SAAB Scandia 90",
	"JS41": "BAe Jetstream 41",
	"LJ60": "Bombardier Lear 60",
	"C46": "Curtis C46",
	"CH47": "Boeing Vertol CH-47 Chinook",
	"IL14": "Ilyushin Il-14",
	"C117": "Douglas C117D",
	"C123": "Fairchild C123",
	"E135i": "Embraer Legacy 600",
	"FA7X": "Dassault Falcon 7X",
	"D228": "Dornier 228",
	"FSW3": "Fairchild Metro III",
	"JS32": "BAe Jetstream 32",
	"E110": "Embraer 110",
	"DHC4": "DeHavilland DHC-4 Caribou",
	"B190D": "Beechcraft 1900D",
	"HU16": "Grumman HU-16B Albatross",
	"C750": "Cessna Citation X",
	"B190C": "Beechcraft 1900C",
	"CL2T": "Bombardier CL-415",
	"DC3": "Douglas DC-3",
	"LJ25": "LearJet LJ25D",
	"SBR1": "North American T-39 Sabreliner",
	"BE30": "Beechcraft King Air 300",
	"L410E": "Let L 410 UVP-E",
	"CL30": "Bombardier Challenger 300",
	"B350": "Beechcraft King Air 350",
	"BE40": "Raytheon Beechjet / Hawker",
	"PA42": "Piper PA-42-1000 Cheyenne 400",
	"BE20": "Beechcraft King Air 200",
	"AN28": "Antonov An-28",
	"L37": "Howard Aero 500",
	"C210": "Cessna 210 Centurion",
	"PA32": "Piper PA-32 Cherokee Six/ Saratoga",
	"BE33": "Beechcraft Bonanza F33",
	"BE35": "Beechcraft Bonanza V35",
	"P166": "Piaggio 166 Albatross",
	"DG15": "Howard DGA-15",
	"ANSN": "Avro Anson MK-1",
	"GA8": "Gippsland GA8 Airvan",
	"BE17": "Beechcraft 17",
	"PA32T": "Piper PA-32 Saratoga TC",
	"PA23": "Piper PA-23 Aztec",
	"L39": "Aero Vodochody L-39",
	"MS76": "Morane-Saulnier MS-760",
	"BE60": "Beechcraft Duke B60",
	"LEG2": "Lancair Legacy IV-P",
	"PA34": "Piper PA-34 Seneca",
	"PA60": "Piper PA-60 Aerostar",
	"UH1": "Bell UH-1H Huey",
	"BE58": "Beechcraft Baron 58",
	"BE58i": "Beechcraft Baron 58 - tip tanks (Dreamfleet)",
	"PAY1": "Piper PA-31T1 Cheyenne I/IA",
	"DHC2": "DeHavilland DHC-2 Turbo Beaver",
	"S55": "Sikorsky S-55",
	"C207": "Cessna 207 Stationair 8",
	"AN2": "Antonov AN-2",
	"PAY2": "Piper PA-31T Cheyenne II",
	"B412": "Bell 412",
	"PA31": "Piper PA-31 Navajo",
	"B212": "Bell 212",
	"A26": "Douglas A-26",
	"B25": "North American B-25",
	"BN2P": "Britten-Norman BN-2B Islander",
	"AC50": "Aero Design AC500C",
	"LJ24": "Learjet 24B",
	"LJ24i": "Learjet 24B - Tip Tanks",
	"WALR": "Supermarine Walrus MK 1",
	"NORS": "Noorduyn Norseman",
	"AC68": "Aero Design AC680S",
	"PA46": "Piper PA-46 Meridian",
	"BE50": "Beechcraft Twin Bonanza 50",
	"PC6": "Pilatus PC-6 Porter",
	"C340": "Cessna 340A",
	"EC35": "Eurocopter EC-135",
	"AC90": "Aero Design AC690",
	"BASS": "Beagle B 206 Basset",
	"S76": "Sikorsky S-76",
	"P750": "Pacific Aerospace 750XL",
	"C510": "Cessna Mustang",
	"TBM7": "Socata TBM 700",
	"KODI": "Quest Kodiak",
	"B60T": "Beechcraft Royal Turbine Duke B60",
	"BE18": "Beechcraft 18",
	"G21": "Grumman G21 Goose",
	"LA60": "Aermacchi - Lockheed AL-60",
	"DHC3": "DeHavilland DHC-3 Otter",
	"DOVE": "DeHavilland DH104 Dove",
	"JU52": "Junkers Ju-52",
	"C421": "Cessna 421 Golden Eagle",
	"S2P": "Grumman S2/C1",
	"PAY2x": "Piper PA-31T2 Cheyenne IIXL",
	"L10A": "Lockheed L10A Electra",
	"L10E": "Lockheed L10E Amelia Special",
	"TBM8": "Socata TBM 850",
	"G21T": "Grumman Turbo Goose",
	"B80S": "Beech Queen Air 80S",
	"E50P": "Embraer Phenom 100",
	"C414": "Cessna 414A Chancellor",
	"C404": "Cessna 404 Titan",
	"NOMA": "Australia GAF N22 Nomad",
	"BE80": "Beechcraft Queen Air",
	"MU2B": "Mitsubishi MU-2B",
	"C25": "Cessna Citation CJ1",
	"EA50": "Eclipse 500",
	"MI8": "Kazan Helicopter Plant Mi-17-1V-GA",
	"DC2": "Douglas DC-2",
	"DC2i": "Douglas DC-2 (FSX)",
	"DH3T": "DeHavilland DHC-3-T Turbo Otter",
	"HERN": "DeHavilland DH114 Heron",
	"B190F": "Beechcraft 1900C Freighter",
	"S61": "Westland Seaking",
	"BN2T": "Britten Norman BN-2A Mk3-3 Trislander",
	"CAT": "Consolidated PBY5 Catalina",
	"C208": "Cessna 208 Caravan",
	"S43": "Sikorsky S-43",
	"C441": "Cessna 441 Conquest II",
	"PRM1": "Raytheon Premier1",
	"P180": "Piaggio 180 Avanti",
	"BE9L": "Beechcraft King Air C90",
	"C550": "Cessna Citation II",
	"LJ45": "Lear 45",
	"SC7": "Shorts Skyvan",
	"PC12": "Pilatus PC-12",
	"DHC6i": "DeHavilland DHC-6 300 Twin Otter (Aerosoft Extended)",
	"DHC6": "DeHavilland DHC-6 Twin Otter"}
	return dict

def getregiondict():
	dict={"Afghanistan": "Middle East",
	"Albania": "Europe",
	"Algeria": "Africa",
	"American Samoa": "Pacific",
	"Angola": "Africa",
	"Anguilla": "Caribbean",
	"Antarctica": "Antarctica",
	"Antigua and Barbuda": "Caribbean",
	"Argentina": "South America",
	"Armenia": "Europe",
	"Aruba": "Caribbean",
	"Ascension Island": "South America",
	"Australia": "Australia",
	"Austria": "Europe",
	"Azerbaijan": "Europe",
	"Bahamas, The": "Caribbean",
	"Bahrain": "Middle East",
	"Bangladesh": "Southeast Asia",
	"Barbados": "Caribbean",
	"Belarus": "Europe",
	"Belgium": "Europe",
	"Belize": "Central America",
	"Benin": "Africa",
	"Bermuda": "Caribbean",
	"Bhutan": "Southeast Asia",
	"Bolivia": "South America",
	"Bosnia and Herzegovina": "Europe",
	"Botswana": "Africa",
	"Brazil": "South America",
	"British Virgin Islands": "Caribbean",
	"Brunei": "Middle East",
	"Bulgaria": "Europe",
	"Burkina Faso": "Africa",
	"Burundi": "Africa",
	"Cambodia": "Southeast Asia",
	"Cameroon": "Africa",
	"Canada": "North America",
	"Cape Verde": "Africa",
	"Cayman Islands": "Caribbean",
	"Central African Republic": "Africa",
	"Chad": "Africa",
	"Chile": "South America",
	"China": "East Asia",
	"Colombia": "South America",
	"Comoros": "Africa",
	"Congo": "Africa",
	"Congo (DRC)": "Africa",
	"Congo DRC": "Africa",
	"Cook Islands": "Pacific",
	"Costa Rica": "Central America",
	"Cote d'Ivoire": "Africa",
	"Croatia": "Europe",
	"Cuba": "Caribbean",
	"Cyprus": "Europe",
	"Czech Republic": "Europe",
	"Denmark": "Europe",
	"Djibouti": "Africa",
	"Dominica": "Caribbean",
	"Dominican Republic": "Caribbean",
	"Ecuador": "South America",
	"Egypt": "Africa",
	"El Salvador": "Central America",
	"Equatorial Guinea": "Africa",
	"Eritrea": "Africa",
	"Estonia": "Europe",
	"Ethiopia": "Africa",
	"Falkland Islands (Islas Malvinas)": "South America",
	"Faroe Islands": "Europe",
	"Fiji Islands": "Pacific",
	"Finland": "Europe",
	"France": "Europe",
	"French Guiana": "South America",
	"French Polynesia": "Pacific",
	"Gabon": "Africa",
	"Gambia, The": "Africa",
	"Gaza Strip": "Middle East",
	"Georgia": "Europe",
	"Germany": "Europe",
	"Ghana": "Africa",
	"Gibraltar": "Europe",
	"Greece": "Europe",
	"Greenland": "North America",
	"Grenada": "Caribbean",
	"Guadeloupe": "Caribbean",
	"Guam": "Pacific",
	"Guatemala": "Central America",
	"Guinea": "Africa",
	"Guinea-Bissau": "Africa",
	"Guyana": "South America",
	"Haiti": "Caribbean",
	"Honduras": "Central America",
	"Hong Kong SAR": "East Asia",
	"Hungary": "Europe",
	"Iceland": "Europe",
	"India": "South Asia",
	"Indonesia": "Southeast Asia",
	"Iran": "Middle East",
	"Iraq": "Middle East",
	"Ireland": "Europe",
	"Israel": "Middle East",
	"Italy": "Europe",
	"Jamaica": "Caribbean",
	"Japan": "East Asia",
	"Jordan": "Middle East",
	"Kazakhstan": "Asia",
	"Kenya": "Africa",
	"Kiribati": "Pacific",
	"Korea": "East Asia",
	"Kuwait": "Middle East",
	"Kyrgyzstan": "Asia",
	"Laos": "Southeast Asia",
	"Latvia": "Europe",
	"Lebanon": "Middle East",
	"Lesotho": "Africa",
	"Liberia": "Africa",
	"Libya": "Africa",
	"Lithuania": "Europe",
	"Luxembourg": "Europe",
	"Macao SAR": "East Asia",
	"Macedonia, Former Yugoslav Republic of": "Europe",
	"Madagascar": "Africa",
	"Malawi": "Africa",
	"Malaysia": "Southeast Asia",
	"Maldives": "Pacific",
	"Mali": "Africa",
	"Malta": "Europe",
	"Marshall Islands": "Pacific",
	"Martinique": "Caribbean",
	"Mauritania": "Africa",
	"Mauritius": "Africa",
	"Mayotte": "Africa",
	"Mexico": "North America",
	"Micronesia": "Southeast Asia",
	"Moldova": "Europe",
	"Mongolia": "East Asia",
	"Morocco": "Africa",
	"Mozambique": "Africa",
	"Myanmar": "Southeast Asia",
	"Namibia": "Africa",
	"Nauru": "Pacific",
	"Nepal": "South Asia",
	"Netherlands Antilles": "Caribbean",
	"Netherlands, The": "Europe",
	"New Caledonia": "Pacific",
	"New Zealand": "Australia",
	"Nicaragua": "Central America",
	"Niger": "Africa",
	"Nigeria": "Africa",
	"Niue": "Pacific",
	"North Korea": "East Asia",
	"Northern Mariana Islands": "Pacific",
	"Norway": "Europe",
	"Oman": "Middle East",
	"Pakistan": "Middle East",
	"Panama": "Central America",
	"Papua New Guinea": "Southeast Asia",
	"Paraguay": "South America",
	"Peru": "South America",
	"Philippines": "Southeast Asia",
	"Poland": "Europe",
	"Portugal": "Europe",
	"Puerto Rico": "Caribbean",
	"Qatar": "Middle East",
	"Reunion": "Africa",
	"Romania": "Europe",
	"Russia": "Asia",
	"Rwanda": "Africa",
	"Samoa": "Pacific",
	"Sao Tome and Principe": "Africa",
	"Saudi Arabia": "Middle East",
	"Senegal": "Africa",
	"Serbia and Montenegro": "Europe",
	"Seychelles": "Africa",
	"Sierra Leone": "Africa",
	"Singapore": "Southeast Asia",
	"Slovakia": "Europe",
	"Slovenia": "Europe",
	"Solomon Islands": "Pacific",
	"Somalia": "Africa",
	"South Africa": "Africa",
	"Spain": "Europe",
	"Sri Lanka": "South Asia",
	"St. Kitts and Nevis": "Caribbean",
	"St. Lucia": "Caribbean",
	"St. Pierre and Miquelon": "Caribbean",
	"St. Vincent and the Grenadines": "Caribbean",
	"Sudan": "Africa",
	"Suriname": "South America",
	"Swaziland": "Africa",
	"Sweden": "Europe",
	"Switzerland": "Europe",
	"Syria": "Middle East",
	"Taiwan": "East Asia",
	"Tajikistan": "Asia",
	"Tanzania": "Africa",
	"Thailand": "Southeast Asia",
	"Timor-Leste": "Southeast Asia",
	"Togo": "Africa",
	"Tonga": "Pacific",
	"Trinidad and Tobago": "Caribbean",
	"Tunisia": "Africa",
	"Turkey": "Middle East",
	"Turkmenistan": "Asia",
	"Turks and Caicos Islands": "Caribbean",
	"Tuvalu": "Pacific",
	"Uganda": "Africa",
	"Ukraine": "Asia",
	"United Arab Emirates": "Middle East",
	"United Kingdom": "Europe",
	"United States": "North America",
	"Uruguay": "South America",
	"Uzbekistan": "Asia",
	"Vanuatu": "Pacific",
	"Venezuela": "South America",
	"Vietnam": "Southeast Asia",
	"Virgin Islands": "Caribbean",
	"Virgin Islands, British": "Caribbean",
	"Wallis and Futuna": "Pacific",
	"Yemen": "Middle East",
	"Zambia": "Africa",
	"Zimbabwe": "Africa"}
	return dict