# Vanilla tag -> Kaiserredux tags that should inherit its formable eligibility.
# Only tags whose meaning differs between the two mods, or that need extra
# Kaiserredux successor states, are listed; everything else maps to itself
# when Kaiserredux has the tag, or to the same-capital Kaiserredux tag otherwise.
OVERRIDES = {
    # same code, different country in Kaiserredux
    'BAH': [],                       # Bahamas  (KRX BAH = Bahia)
    'BAN': ['BHC', 'INR'],           # Bangladesh (KRX BAN = Banat)
    'BAS': ['CAF'],                  # British Antillean Federation (KRX BAS = Euskadi)
    'BUK': ['UZB'],                  # Bukhara (KRX BUK = Bukovina)
    'CAR': ['CEA'],                  # Central African Republic (KRX CAR = Carlist Spain)
    'COR': [],                       # Corsica (KRX COR = Constitutional American Republic)
    'FSA': ['YEM'],                  # Federation of South Arabia (KRX FSA = Free States of America)
    'KAS': [],                       # Kashmir (KRX KAS = Kasai)
    'MAD': ['MAG'],                  # Madagascar (KRX MAD = Kingdom of India)
    'MAL': ['MLY'],                  # Malaysia (KRX MAL = Mali)
    'NGR': ['NER'],                  # Niger (KRX NGR = Nigeria)
    'SAM': [],                       # Samoa (KRX SAM = Sapmi)
    'SIC': ['SZC'],                  # Sichuan (KRX SIC = Two Sicilies)
    'SLO': ['SVK'],                  # Slovakia (KRX SLO = Slovene State)
    'SSI': [],                       # Siak (KRX SSI = Pacific communities)
    'TAN': [],                       # Tannu Tuva (KRX TAN = Kumul)
    'FAR': [],
    'KUW': [],                       # Kuwait (shares a capital state with KRX Assyria)
    # vanilla-only tags with a Kaiserredux counterpart under another code
    'MLI': ['MAL'], 'NGA': ['NGR'], 'SMI': ['SAM'], 'SLV': ['SLO'], 'KUM': ['TAN'], 'TTS': ['SIC'],
    'NAV': ['BAS'], 'SND': ['SQI'], 'SPM': ['SRI', 'SRD'], 'TOS': ['TUS'], 'LBV': ['VNC'],
    'YUG': ['SER'], 'SCO': ['SCT'], 'WLS': ['WAL'], 'NIR': ['ULS'], 'PUE': ['PRI'], 'SRL': ['CEY'],
    'SKK': ['SKM'], 'MAC': ['MCD'], 'CRI': ['CRM'], 'DON': ['DKB'], 'KAL': ['KLY'], 'TAT': ['TTR'],
    'BSK': ['BKN'], 'BYA': ['BRY'], 'AZR': ['AZE'], 'BLR': ['WHR'], 'ISR': ['PAL'], 'CHA': ['WAD'],
    'VOL': ['BFA'], 'GNB': ['CVG'], 'RCG': ['TKE', 'KOG'], 'UAE': ['TRU'], 'CPS': ['LAO'], 'BRN': ['SAR'],
    'HAN': ['NGF'], 'RHI': ['WGR'], 'PRE': ['DDR', 'EPR'], 'GDC': ['GXC', 'PRC'], 'HBC': ['QIE'],
    'NOA': ['MTR'], 'FIJ': [], 'SNG': [], 'BAR': ['BRT'],
    'KAZ': ['ALO'], 'RUT': ['CPU'], 'TRA': ['TRS'], 'IMO': ['OMA'], 'GAM': ['SEN'], 'HRZ': ['BOS'],
    'ADU': ['ADL'], 'CBV': ['CVG'], 'WPG': ['PNG'], 'KOL': ['PRF'],
    # vanilla great powers split into several Kaiserredux successor states
    'SOV': ['RUS', 'WRA', 'RVA', 'RRF', 'SIB'],
    'RAJ': ['DEH', 'PGI', 'BHC', 'PRF', 'MAD', 'INR'],
    'ENG': ['ENG', 'GBR', 'GBP'],
    'FRA': ['FRA', 'NFA', 'FRP'],
    'GER': ['GER', 'GRU'],
    'ITA': ['ITA', 'SRI', 'SRD', 'PAP'],
    'SPR': ['SPR', 'CAR', 'CNT'],
    'SPA': ['CAR', 'CNT'],
    'USA': ['USA', 'CSA', 'TEX', 'CAL', 'NEE', 'COR', 'FSA'],
    'CSA': ['CSA', 'TEX', 'CAL', 'COR', 'FSA'],
    'CHI': ['CHI', 'QIE', 'LEP', 'LEC', 'SQI', 'SZC', 'HNN', 'ANQ', 'FNG'],
    'PRC': ['LEP', 'LEC'],
    'MAN': ['MAN', 'FNG'],
    'BRA': ['BRA', 'SPO', 'GOY', 'AMA', 'GRP', 'PIR', 'BAH'],
    'MEX': ['MEX', 'YUC', 'RJM'],
    'INS': ['INS', 'DEI'],
    'BEL': ['BEL', 'FLN', 'WLL'],
    'LAT': ['LAT', 'BAT'],
    'GRE': ['GRE', 'GRR'],
}
