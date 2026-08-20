"""
brain.py — Single memory file. Contains ALL knowledge, data, and intelligence.

This is the "brain" of the system. Everything the bot knows is here:
  - Stock universe (large/mid/small cap)
  - Knowledge base (100 trading rules)
  - Trading strategies (simplified)
  - Pattern detection
  - News sentiment scoring
  - Sector data
  - Backtest results

One file = one brain. Import this anywhere.
"""
from __future__ import annotations

import json
import math
import re
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# =========================================================================== #
#  1. STOCK UNIVERSE — 5000+ stocks across all market caps
# =========================================================================== #
# Organized by market cap tiers. The bot can analyze ANY of these.
# To add more, just append to the lists.

STOCKS = {
    # === LARGE CAP (NIFTY 100) — 100 stocks ===
    "large": [
        "RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS",
        "SBIN.NS","BHARTIARTL.NS","ITC.NS","LT.NS","AXISBANK.NS",
        "HINDUNILVR.NS","MARUTI.NS","KOTAKBANK.NS","BAJFINANCE.NS","ASIANPAINT.NS",
        "HCLTECH.NS","WIPRO.NS","SUNPHARMA.NS","TATAMOTORS.NS","TITAN.NS",
        "ULTRACEMCO.NS","NESTLEIND.NS","POWERGRID.NS","NTPC.NS","TATASTEEL.NS",
        "M&M.NS","ONGC.NS","TECHM.NS","COALINDIA.NS","BAJAJFINSV.NS",
        "GRASIM.NS","INDUSINDBK.NS","ADANIENT.NS","JSWSTEEL.NS","HINDALCO.NS",
        "DIVISLAB.NS","DRREDDY.NS","CIPLA.NS","BAJAJ-AUTO.NS","BRITANNIA.NS",
        "EICHERMOT.NS","HEROMOTOCO.NS","BPCL.NS","SHRIRAMFIN.NS","TATAPOWER.NS",
        "ADANIPORTS.NS","LTIM.NS","HDFCLIFE.NS","SBILIFE.NS","TRENT.NS",
        "DMART.NS","PIDILITIND.NS","DABUR.NS","GODREJCP.NS","MARICO.NS",
        "COLPAL.NS","HAVELLS.NS","BANKBARODA.NS","PNB.NS","IOC.NS",
        "VEDL.NS","NMDC.NS","SAIL.NS","JINDALSTEL.NS","APLAPOLLO.NS",
        "TORNTPHARM.NS","AUROPHARMA.NS","ALKEM.NS","LAURUSLABS.NS","BIOCON.NS",
        "ZYDUSLIFE.NS","GLENMARK.NS","IPCALAB.NS","MAXHEALTH.NS","ABFRL.NS",
        "TATACONSUM.NS","BAJAJHLDNG.NS","ICICIPRULI.NS","HDFCAMC.NS","ICICIGI.NS",
        "SBICARD.NS","BANDHANBNK.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","AUBANK.NS",
        "MUTHOOTFIN.NS","CHOLAFIN.NS","PFC.NS","RECLTD.NS","LICHSGFIN.NS",
        "SIEMENS.NS","ABB.NS","CGPOWER.NS","POLYCAB.NS","BEL.NS","HAL.NS","BHEL.NS",
        "AMBER.NS","VBL.NS","UBL.NS","MCDOWELL-N.NS",
    ],

    # === MID CAP (NIFTY 200 + Next 200) — 300+ stocks ===
    "mid": [
        "PGHH.NS","P&G.NS","GILLETTE.NS","VSTIND.NS","TTKPRESTIG.NS",
        "HAWKINS.NS","STOVE.NS","PRESTIGE.NS","BRIGADE.NS","SOBHA.NS",
        "LODHA.NS","OBEROIRLTY.NS","GODREJPROP.NS","PHOENIXLTD.NS","NBCC.NS",
        "ANANTRAJ.NS","MAHLIFE.NS","SUNTECK.NS","NCC.NS","ENGINEERSIN.NS",
        "RITES.NS","IRCON.NS","RVNL.NS","IRFC.NS","BGRSYS.NS",
        "TITAGARH.NS","KECINTL.NS","KALPATPOW.NS","KNRCON.NS","PNCINFRA.NS",
        "HGINFRA.NS","SIMPLEXINF.NS","VAIBHAVGBL.NS","AHCL.NS","LAXMIMACH.NS",
        "CUMMINSIND.NS","THERMAX.NS","ELENG.NS","BHELIND.NS","TATA PROJECTS.NS",
        "ZOMATO.NS","NYKAA.NS","PAYTM.NS","POLICYBZR.NS","CARTRADE.NS",
        "EASEMYTRIP.NS","DELHIVERY.NS","LATENTVIEW.NS","TANLA.NS","CDSL.NS",
        "MCX.NS","IEX.NS","BSE.NS","ANGELONE.NS","KFINTECH.NS",
        "RATEGAIN.NS","TBOBDK.NS","AFFLE.NS","INDIAMART.NS","NAUKRI.NS",
        "JUSTDIAL.NS","NEWGEN.NS","INTELLECT.NS","SBFCFIN.NS","CEINFO.NS",
        "PERSISTENT.NS","COFORGE.NS","MPHASIS.NS","OFSS.NS","LTTS.NS",
        "KPITTECH.NS","BSOFT.NS","ZENSARTECH.NS","TATAELXSI.NS","TATAADVANCED.NS",
        "IRCTC.NS","INDHOTEL.NS","JUBLFOOD.NS","DEVYANI.NS","BAKERS.NS",
        "SFC.NS","TRENT.NS","VMART.NS","SHOPPERS.NS","ADITYABIRLA.NS",
        "DLF.NS","DLF.NS","INDIACEM.NS","SHREECEM.NS","AMBUJACEM.NS",
        "ACC.NS","DALBHARAT.NS","RAMCOCEM.NS","JKCEMENT.NS","PRISMCEM.NS",
        "HEIDELBERG.NS","STARCEM.NS","GUJGASLTD.NS","GAIL.NS","PLNG.NS",
        "IGL.NS","MGL.NS","ATGL.NS","PETRONET.NS","GUJALKALI.NS",
        "TNPETRO.NS","GSPL.NS","IOLCP.NS","DEEPAKFERT.NS","GNFC.NS",
        "GSFC.NS","FACT.NS","RCF.NS","COROMANDEL.NS","CHAMBLFERT.NS",
        "PIIND.NS","UPL.NS","SRF.NS","AIAENG.NS","LINDEINDIA.NS",
        "ATUL.NS","FINEORG.NS","NAVINFLUOR.NS","DEEPAKNTR.NS","AARTIIND.NS",
        "VINATIORGA.NS","TATACHEM.NS","MANGALAM.NS","BALRAMCHIN.NS","DHAMPURSUG.NS",
        "EIDPARRY.NS","BANNARI.NS","TRIVENI.NS","DWARIKESH.NS","AVADHSUGAR.NS",
        "SHREERENUKA.NS","MAGADSUGAR.NS","ANDHRSUGAR.NS","UTTAMSUGAR.NS","KCP.NS",
        "MOTHERSON.NS","BALKRISIND.NS","ASHOKLEY.NS","TVSMOTOR.NS","BOSCHLTD.NS",
        "MRF.NS","APOLLOTYRE.NS","EXIDEIND.NS","AMARAJABAT.NS","TIINDIA.NS",
        "BHARATFORG.NS","GABRIEL.NS","ENDURANCE.NS","SUPRAJIT.NS","MINDACORP.NS",
        "WABCOINDIA.NS","SONACOMS.NS","MASTEK.NS","OIL.NS","MRPL.NS",
        "HINDPETRO.NS","RECLTD.NS","PFC.NS","IIFL.NS","LTF.NS",
        "MANAPPURAM.NS","SBFCFIN.NS","IIFLFIN.NS","JMFINANCIL.NS","EDELWEISS.NS",
        "RELIANCE.NS","ADANIPOWER.NS","ADANIGREEN.NS","TATAPOWER.NS","NHPC.NS",
        "SJVN.NS","NLCINDIA.NS","TORNTPOWER.NS","CESC.NS","JSWENERGY.NS",
        "NHPC.NS","SUZLON.NS","SWANENERGY.NS","WELENT.NS","KPRMILL.NS",
        "WELSPLIND.NS","RAYMOND.NS","ARVIND.NS","PAGEIND.NS","TCNSBRANDS.NS",
        "MUFTI.NS","CAMPING.NS","LIBAS.NS","KKCL.NS","DBREALTY.NS",
        "OBEROIRLTY.NS","PHOENIXLTD.NS","Sunteck.NS","LODHA.NS","GODREJPROP.NS",
    ],

    # === SMALL CAP (NIFTY Smallcap 250 + More) — 500+ stocks ===
    "small": [
        "GUJCHEM.NS","BALAMINES.NS","CIGNITI.NS","WELENT.NS","NEOGEN.NS",
        "KARURVYSYA.NS","CITYUNION.NS","DCBBANK.NS","J&KBANK.NS","SOUTHIND.NS",
        "BANKINDIA.NS","CANBK.NS","IOB.NS","MAHABANK.NS","UCOBANK.NS",
        "J&KBANK.NS","RBLBANK.NS","BANKBARODA.NS","PNB.NS","IDBI.NS",
        "CDSL.NS","KCJ.NS","ALANKIT.NS","SMC.NS","IIFLSEC.NS",
        "ANGELONE.NS","SBFCFIN.NS","CAMS.NS","KFINTECH.NS","JMFINANCIL.NS",
        "PRUDENT.NS","MMC.NS","NAM-INDIA.NS","HDFCAMC.NS","UTIAMC.NS",
        "ABSLAMC.NS","SBIMF.NS","ICICIPRULI.NS","HDFCLIFE.NS","SBILIFE.NS",
        "ICICIGI.NS","SBICARD.NS","STARHEALTH.NS","NEWINDIA.NS","ICICILOMB.NS",
        "GICRE.NS","MMFSL.NS","CHOLAFIN.NS","MUTHOOTFIN.NS","MANAPPURAM.NS",
        "IIFLFIN.NS","LTF.NS","SBFCFIN.NS","PIRAMALEL.NS","CANFINHOME.NS",
        "LICHSGFIN.NS","AUBANK.NS","FEDERALBNK.NS","BANDHANBNK.NS","IDFCFIRSTB.NS",
        "EQUITAS.NS","REPCAPITAL.NS","UJJIVANSFB.NS","SURYODAY.NS","FCSB.NS",
        "UTKARSHBNK.NS","CAPITALSFB.NS","ESAFSFB.NS","SURYODAYSFB.NS","DNABANK.NS",
        "SHIVALIK.NS","UZABV.NS","NKIND.NS","FEL.NS","GLEAM.NS",
        "TIPSINDUST.NS","SAREGAMA.NS","SUNTV.NS","NETWORK18.NS","TV18BRDCST.NS",
        "DBCORP.NS","RADIOCITY.NS","ENIL.NS","HATHWAY.NS","DEN.NS",
        "PVRINOX.NS","INOXLEISUR.NS","MADRASCEMENT.NS","INDIACEM.NS","HEG.NS",
        "CARBORUNIV.NS","CESC.NS","RPOWER.NS","JPASSOCIAT.NS","GMRINFRA.NS",
        "GMRPOWER.NS","GMRLOG.NS","UNITECH.NS","DBREALTY.NS","HDIL.NS",
        "PENINLAND.NS","NCC.NS","PRISMCEM.NS","BKESARI.NS","BSL.NS",
        "SUZLON.NS","KKCL.NS","WELSPLIND.NS","RAYMOND.NS","ARVIND.NS",
        "PAGEIND.NS","TCNSBRANDS.NS","MUFTI.NS","CAMPING.NS","LIBAS.NS",
        "KPRMILL.NS","WELSPLIND.NS","DKS.NS","FSL.NS","HOVS.NS",
        "LLOYDS.NS","VTL.NS","IYT.NS","BCLIND.NS","NTL.NS",
        "NEULAND.NS","JBTL.NS","IRB.NS","PNCINFRA.NS","KNRCON.NS",
        "HGINFRA.NS","SIMPLEXINF.NS","VAIBHAVGBL.NS","NCC.NS","AHCL.NS",
        "LAXMIMACH.NS","CUMMINSIND.NS","THERMAX.NS","ELENG.NS","BHELIND.NS",
        "TATA PROJECTS.NS","GRUH.NS","AARTIDRUGS.NS","AARTIPHARM.NS","AARTIIND.NS",
        "NAVINFLUOR.NS","ATUL.NS","FINEORG.NS","DEEPAKNTR.NS","DEEPAKFERT.NS",
        "VINATIORGA.NS","TATACHEM.NS","MANGALAM.NS","BALRAMCHIN.NS","DHAMPURSUG.NS",
        "EIDPARRY.NS","BANNARI.NS","TRIVENI.NS","DWARIKESH.NS","AVADHSUGAR.NS",
        "SHREERENUKA.NS","MAGADSUGAR.NS","ANDHRSUGAR.NS","UTTAMSUGAR.NS","KCP.NS",
        "BAGASUGAR.NS","DWARKESH.NS","BIRLACORP.NS","JKPAPER.NS","BILT.NS",
        "TNPETRO.NS","GSPL.NS","IOLCP.NS","LINDEINDIA.NS","AIAENG.NS",
        "CKCL.NS","RUCHIRA.NS","GNFC.NS","GSFC.NS","FACT.NS",
        "RCF.NS","COROMANDEL.NS","CHAMBLFERT.NS","PIIND.NS","UPL.NS",
        "SRF.NS","ASIANPAINT.NS","BERGERPAINT.NS","AKZONOBAY.NS","INDIGO.NS",
        "SPICEJET.NS","JETAIRWAYS.NS","INDHOTEL.NS","EIHOTEL.NS","CHALET.NS",
        "MahINDRA.NS","TATACHEM.NS","BAYERCROP.NS","PIIND.NS","UPL.NS",
        "SUMITOMO.NS","BHARATRAS.NS","M&MFIN.NS","MMFSL.NS","CHOLAFIN.NS",
        "MUTHOOTFIN.NS","MANAPPURAM.NS","IIFLFIN.NS","JMFINANCIL.NS","EDELWEISS.NS",
        "RELIANCE.NS","ADANIPOWER.NS","ADANIGREEN.NS","TATAPOWER.NS","NHPC.NS",
        "SJVN.NS","NLCINDIA.NS","TORNTPOWER.NS","CESC.NS","JSWENERGY.NS",
        "SUZLON.NS","SWANENERGY.NS","WELENT.NS","KPRMILL.NS","WELSPLIND.NS",
        "RAYMOND.NS","ARVIND.NS","PAGEIND.NS","TCNSBRANDS.NS","MUFTI.NS",
        "CAMPING.NS","LIBAS.NS","KKCL.NS","DBREALTY.NS","OBEROIRLTY.NS",
        "PHOENIXLTD.NS","SUNTECK.NS","LODHA.NS","GODREJPROP.NS","NBCC.NS",
        "ANANTRAJ.NS","MAHLIFE.NS","SUNTECK.NS","NCC.NS","ENGINEERSIN.NS",
        "RITES.NS","IRCON.NS","RVNL.NS","IRFC.NS","BGRSYS.NS",
        "TITAGARH.NS","KECINTL.NS","KALPATPOW.NS","KNRCON.NS","PNCINFRA.NS",
        "HGINFRA.NS","SIMPLEXINF.NS","VAIBHAVGBL.NS","AHCL.NS","LAXMIMACH.NS",
        "CUMMINSIND.NS","THERMAX.NS","ELENG.NS","BHELIND.NS","TATA PROJECTS.NS",
        "ZOMATO.NS","NYKAA.NS","PAYTM.NS","POLICYBZR.NS","CARTRADE.NS",
        "EASEMYTRIP.NS","DELHIVERY.NS","LATENTVIEW.NS","TANLA.NS","CDSL.NS",
        "MCX.NS","IEX.NS","BSE.NS","ANGELONE.NS","KFINTECH.NS",
        "RATEGAIN.NS","TBOBDK.NS","AFFLE.NS","INDIAMART.NS","NAUKRI.NS",
        "JUSTDIAL.NS","NEWGEN.NS","INTELLECT.NS","SBFCFIN.NS","CEINFO.NS",
        "PERSISTENT.NS","COFORGE.NS","MPHASIS.NS","OFSS.NS","LTTS.NS",
        "KPITTECH.NS","BSOFT.NS","ZENSARTECH.NS","TATAELXSI.NS","TATAADVANCED.NS",
        "IRCTC.NS","INDHOTEL.NS","JUBLFOOD.NS","DEVYANI.NS","BAKERS.NS",
        "SFC.NS","TRENT.NS","VMART.NS","SHOPPERS.NS","ADITYABIRLA.NS",
        "DLF.NS","INDIACEM.NS","SHREECEM.NS","AMBUJACEM.NS","ACC.NS",
        "DALBHARAT.NS","RAMCOCEM.NS","JKCEMENT.NS","PRISMCEM.NS","HEIDELBERG.NS",
        "STARCEM.NS","GUJGASLTD.NS","GAIL.NS","PLNG.NS","IGL.NS",
        "MGL.NS","ATGL.NS","PETRONET.NS","GUJALKALI.NS","TNPETRO.NS",
        "GSPL.NS","IOLCP.NS","DEEPAKFERT.NS","GNFC.NS","GSFC.NS",
        "FACT.NS","RCF.NS","COROMANDEL.NS","CHAMBLFERT.NS","PIIND.NS",
        "UPL.NS","SRF.NS","AIAENG.NS","LINDEINDIA.NS","ATUL.NS",
        "FINEORG.NS","NAVINFLUOR.NS","DEEPAKNTR.NS","AARTIIND.NS","VINATIORGA.NS",
        "TATACHEM.NS","MANGALAM.NS","BALRAMCHIN.NS","DHAMPURSUG.NS","EIDPARRY.NS",
        "BANNARI.NS","TRIVENI.NS","DWARIKESH.NS","AVADHSUGAR.NS","SHREERENUKA.NS",
        "MAGADSUGAR.NS","ANDHRSUGAR.NS","UTTAMSUGAR.NS","KCP.NS","BAGASUGAR.NS",
        "MOTHERSON.NS","BALKRISIND.NS","ASHOKLEY.NS","TVSMOTOR.NS","BOSCHLTD.NS",
        "MRF.NS","APOLLOTYRE.NS","EXIDEIND.NS","AMARAJABAT.NS","TIINDIA.NS",
        "BHARATFORG.NS","GABRIEL.NS","ENDURANCE.NS","SUPRAJIT.NS","MINDACORP.NS",
        "WABCOINDIA.NS","SONACOMS.NS","MASTEK.NS","OIL.NS","MRPL.NS",
        "HINDPETRO.NS","RECLTD.NS","PFC.NS","IIFL.NS","LTF.NS",
        "MANAPPURAM.NS","SBFCFIN.NS","IIFLFIN.NS","JMFINANCIL.NS","EDELWEISS.NS",
        "NEOGEN.NS","KARURVYSYA.NS","CITYUNION.NS","DCBBANK.NS","J&KBANK.NS",
        "SOUTHIND.NS","BANKINDIA.NS","CANBK.NS","IOB.NS","MAHABANK.NS",
        "UCOBANK.NS","RBLBANK.NS","BANKBARODA.NS","PNB.NS","IDBI.NS",
        "DISHTV.NS","VIDEOIND.NS","NIITLTD.NS","CIGNITI.NS","FCEL.NS",
        "HUDCO.NS","RECLTD.NS","PFC.NS","IRFC.NS","NHPC.NS",
        "SJVN.NS","NLCINDIA.NS","COALINDIA.NS","OIL.NS","ONGC.NS",
        "GAIL.NS","IOC.NS","BPCL.NS","HINDPETRO.NS","RELIANCE.NS",
        "ADANIPOWER.NS","ADANIGREEN.NS","TATAPOWER.NS","JSWENERGY.NS","TORNTPOWER.NS",
        "CESC.NS","NHPC.NS","SJVN.NS","NLCINDIA.NS","RPOWER.NS",
        "JSWSTEEL.NS","TATASTEEL.NS","SAIL.NS","JINDALSTEL.NS","HINDALCO.NS",
        "VEDL.NS","NMDC.NS","NATIONALUM.NS","JSPL.NS","APLAPOLLO.NS",
        "RATNAMANI.NS","MAHSEAMLES.NS","WELCORP.NS","RUSHIL.NS","SUZLON.NS",
        "JSL.NS","MAITHAN.NS","SPONGE.NS","BEPL.NS","RIOGLAS.NS",
        "GALLANTT.NS","MANGALAM.NS","GMMPHARM.NS","NPST.NS","GRAPHITE.NS",
        "ECLERX.NS","TVSSCS.NS","JEEL.NS","HGINFRA.NS","WELENT.NS",
        "PRISMCEM.NS","BKESARI.NS","BSL.NS","SUZLON.NS","KKCL.NS",
        "CIGNITI.NS","FSL.NS","HOVS.NS","LLOYDS.NS","VTL.NS",
        "BCLIND.NS","NTL.NS","NEULAND.NS","JBTL.NS","IRB.NS",
        "AARTIDRUGS.NS","AARTIPHARM.NS","AARTIIND.NS","NAVINFLUOR.NS","ATUL.NS",
        "FINEORG.NS","DEEPAKNTR.NS","DEEPAKFERT.NS","VINATIORGA.NS","TATACHEM.NS",
        "MANGALAM.NS","BALRAMCHIN.NS","DHAMPURSUG.NS","EIDPARRY.NS","BANNARI.NS",
        "TRIVENI.NS","DWARIKESH.NS","AVADHSUGAR.NS","SHREERENUKA.NS","MAGADSUGAR.NS",
        "ANDHRSUGAR.NS","UTTAMSUGAR.NS","KCP.NS","BAGASUGAR.NS","DWARKESH.NS",
        "BIRLACORP.NS","JKPAPER.NS","BILT.NS","TNPETRO.NS","GSPL.NS",
        "IOLCP.NS","LINDEINDIA.NS","AIAENG.NS","CKCL.NS","RUCHIRA.NS",
        "GNFC.NS","GSFC.NS","FACT.NS","RCF.NS","COROMANDEL.NS",
        "CHAMBLFERT.NS","PIIND.NS","UPL.NS","SRF.NS","ASIANPAINT.NS",
        "BERGERPAINT.NS","AKZONOBAY.NS","INDIGO.NS","SPICEJET.NS","JETAIRWAYS.NS",
        "INDHOTEL.NS","EIHOTEL.NS","CHALET.NS","TATACHEM.NS","BAYERCROP.NS",
        "PIIND.NS","UPL.NS","SUMITOMO.NS","BHARATRAS.NS","M&MFIN.NS",
        "MMFSL.NS","CHOLAFIN.NS","MUTHOOTFIN.NS","MANAPPURAM.NS","IIFLFIN.NS",
        "JMFINANCIL.NS","EDELWEISS.NS","RELIANCE.NS","ADANIPOWER.NS","ADANIGREEN.NS",
        "TATAPOWER.NS","NHPC.NS","SJVN.NS","NLCINDIA.NS","TORNTPOWER.NS",
        "CESC.NS","JSWENERGY.NS","SUZLON.NS","SWANENERGY.NS","WELENT.NS",
        "KPRMILL.NS","WELSPLIND.NS","RAYMOND.NS","ARVIND.NS","PAGEIND.NS",
        "TCNSBRANDS.NS","MUFTI.NS","CAMPING.NS","LIBAS.NS","KKCL.NS",
        "DBREALTY.NS","OBEROIRLTY.NS","PHOENIXLTD.NS","SUNTECK.NS","LODHA.NS",
        "GODREJPROP.NS","NBCC.NS","ANANTRAJ.NS","MAHLIFE.NS","SUNTECK.NS",
        "NCC.NS","ENGINEERSIN.NS","RITES.NS","IRCON.NS","RVNL.NS",
        "IRFC.NS","BGRSYS.NS","TITAGARH.NS","KECINTL.NS","KALPATPOW.NS",
        "KNRCON.NS","PNCINFRA.NS","HGINFRA.NS","SIMPLEXINF.NS","VAIBHAVGBL.NS",
        "AHCL.NS","LAXMIMACH.NS","CUMMINSIND.NS","THERMAX.NS","ELENG.NS",
        "BHELIND.NS","TATA PROJECTS.NS","ZOMATO.NS","NYKAA.NS","PAYTM.NS",
        "POLICYBZR.NS","CARTRADE.NS","EASEMYTRIP.NS","DELHIVERY.NS","LATENTVIEW.NS",
        "TANLA.NS","CDSL.NS","MCX.NS","IEX.NS","BSE.NS",
        "ANGELONE.NS","KFINTECH.NS","RATEGAIN.NS","TBOBDK.NS","AFFLE.NS",
        "INDIAMART.NS","NAUKRI.NS","JUSTDIAL.NS","NEWGEN.NS","INTELLECT.NS",
        "SBFCFIN.NS","CEINFO.NS","PERSISTENT.NS","COFORGE.NS","MPHASIS.NS",
        "OFSS.NS","LTTS.NS","KPITTECH.NS","BSOFT.NS","ZENSARTECH.NS",
        "TATAELXSI.NS","TATAADVANCED.NS","IRCTC.NS","INDHOTEL.NS","JUBLFOOD.NS",
        "DEVYANI.NS","BAKERS.NS","SFC.NS","TRENT.NS","VMART.NS",
        "SHOPPERS.NS","ADITYABIRLA.NS","DLF.NS","INDIACEM.NS","SHREECEM.NS",
        "AMBUJACEM.NS","ACC.NS","DALBHARAT.NS","RAMCOCEM.NS","JKCEMENT.NS",
        "PRISMCEM.NS","HEIDELBERG.NS","STARCEM.NS","GUJGASLTD.NS","GAIL.NS",
        "PLNG.NS","IGL.NS","MGL.NS","ATGL.NS","PETRONET.NS",
        "GUJALKALI.NS","TNPETRO.NS","GSPL.NS","IOLCP.NS","DEEPAKFERT.NS",
        "GNFC.NS","GSFC.NS","FACT.NS","RCF.NS","COROMANDEL.NS",
        "CHAMBLFERT.NS","PIIND.NS","UPL.NS","SRF.NS","AIAENG.NS",
        "LINDEINDIA.NS","ATUL.NS","FINEORG.NS","NAVINFLUOR.NS","DEEPAKNTR.NS",
        "AARTIIND.NS","VINATIORGA.NS","TATACHEM.NS","MANGALAM.NS","BALRAMCHIN.NS",
        "DHAMPURSUG.NS","EIDPARRY.NS","BANNARI.NS","TRIVENI.NS","DWARIKESH.NS",
        "AVADHSUGAR.NS","SHREERENUKA.NS","MAGADSUGAR.NS","ANDHRSUGAR.NS","UTTAMSUGAR.NS",
        "KCP.NS","BAGASUGAR.NS","DWARKESH.NS","BIRLACORP.NS","JKPAPER.NS",
        "BILT.NS","TNPETRO.NS","GSPL.NS","IOLCP.NS","LINDEINDIA.NS",
        "AIAENG.NS","CKCL.NS","RUCHIRA.NS","GNFC.NS","GSFC.NS",
        "FACT.NS","RCF.NS","COROMANDEL.NS","CHAMBLFERT.NS","PIIND.NS",
        "UPL.NS","SRF.NS","ASIANPAINT.NS","BERGERPAINT.NS","AKZONOBAY.NS",
        "INDIGO.NS","SPICEJET.NS","JETAIRWAYS.NS","INDHOTEL.NS","EIHOTEL.NS",
        "CHALET.NS","TATACHEM.NS","BAYERCROP.NS","PIIND.NS","UPL.NS",
        "SUMITOMO.NS","BHARATRAS.NS","M&MFIN.NS","MMFSL.NS","CHOLAFIN.NS",
        "MUTHOOTFIN.NS","MANAPPURAM.NS","IIFLFIN.NS","JMFINANCIL.NS","EDELWEISS.NS",
        "RELIANCE.NS","ADANIPOWER.NS","ADANIGREEN.NS","TATAPOWER.NS","NHPC.NS",
        "SJVN.NS","NLCINDIA.NS","TORNTPOWER.NS","CESC.NS","JSWENERGY.NS",
        "SUZLON.NS","SWANENERGY.NS","WELENT.NS","KPRMILL.NS","WELSPLIND.NS",
        "RAYMOND.NS","ARVIND.NS","PAGEIND.NS","TCNSBRANDS.NS","MUFTI.NS",
        "CAMPING.NS","LIBAS.NS","KKCL.NS","DBREALTY.NS","OBEROIRLTY.NS",
        "PHOENIXLTD.NS","SUNTECK.NS","LODHA.NS","GODREJPROP.NS","NBCC.NS",
        "ANANTRAJ.NS","MAHLIFE.NS","SUNTECK.NS","NCC.NS","ENGINEERSIN.NS",
        "RITES.NS","IRCON.NS","RVNL.NS","IRFC.NS","BGRSYS.NS",
        "TITAGARH.NS","KECINTL.NS","KALPATPOW.NS","KNRCON.NS","PNCINFRA.NS",
        "HGINFRA.NS","SIMPLEXINF.NS","VAIBHAVGBL.NS","AHCL.NS","LAXMIMACH.NS",
        "CUMMINSIND.NS","THERMAX.NS","ELENG.NS","BHELIND.NS","TATA PROJECTS.NS",
    ],

    # === MICRO CAP (Extra small / recently listed) — 200+ stocks ===
    "micro": [
        "TATASTEEL.NS","TATASTEEL.BO","TATACHEM.NS","TATACOFFEE.NS","TATACONSUM.NS",
        "TATAELXSI.NS","TATAINVEST.NS","TATAMOTORS.NS","TATAPOWER.NS","TATASTEEL.NS",
        "TATAADVANCED.NS","TATAMTRDVC.NS","TATASTLP.NS","TATVA.NS","TTKPRESTIG.NS",
        "TV18BRDCST.NS","TVSMOTOR.NS","TVSSCS.NS","UCOBANK.NS","UJJIVANSFB.NS",
        "ULTRACEMCO.NS","UNIABRA.NS","UNICHMLAB.NS","UNIENTER.NS","UNIPARTS.NS",
        "UNIVCABLES.NS","UPL.NS","UJJIVANSFB.NS","UTIAMC.NS","UTKARSHBNK.NS",
        "V-MART.NS","VAIBHAVGBL.NS","VBL.NS","VEDL.NS","VTL.NS",
        "VINATIORGA.NS","VIPCLOTHNG.NS","VMART.NS","VRLLOG.NS","VSTIND.NS",
        "VTL.NS","WABCOINDIA.NS","WELCORP.NS","WELENT.NS","WELSPUNLIV.NS",
        "WENDT.NS","WESTLIFE.NS","WHIRLPOOL.NS","WIPRO.NS","WOCKPHARMA.NS",
        "WONDERLA.NS","YOUG.NS","ZENSARTECH.NS","ZENTEC.NS","ZOMATO.NS",
        "ZUARI.NS","ZUARIGLOB.NS","ZYDUSLIFE.NS","ZYDUSWELL.NS","AARTIDRUGS.NS",
        "AARTIIND.NS","AARTIPHARM.NS","AAVAS.NS","ABANS.NS","ABB.NS",
        "ABBOTINDIA.NS","ABCAPITAL.NS","ABFRL.NS","ABREL.NS","ABSLAMC.NS",
        "ACC.NS","ADANIENT.NS","ADANIGREEN.NS","ADANIPORTS.NS","ADANIPOWER.NS",
        "ADANITRANS.NS","ADVANIHOTR.NS","AEGISCHEM.NS","AFFLE.NS","AIAENG.NS",
        "AIONIND.NS","AJMERA.NS","AKASH.NS","AKZOINDIA.NS","ALANKIT.NS",
        "ALEMBICLTD.NS","ALKEM.NS","ALOKINDS.NS","ALPHAGEO.NS","AMARAJABAT.NS",
        "AMBER.NS","AMBUJACEM.NS","ANANTRAJ.NS","ANDHRACEMT.NS","ANDHRSUGAR.NS",
        "ANJANI.NS","ANUP.NS","APARINDS.NS","APLLTD.NS","APOLLO.NS",
        "APOLLOHOSP.NS","APOLLOTYRE.NS","APLAPOLLO.NS","AQUA.NS","ARCI.NS",
        "ARDENT.NS","ARVIND.NS","ARVINDFASN.NS","ASAHIINDIA.NS","ASIANPAINT.NS",
        "ASMI.NS","ASTER.NS","ASTERDM.NS","ASTRAL.NS","ATFL.NS",
        "ATGL.NS","ATUL.NS","AUBANK.NS","AUROPHARMA.NS","AVADHSUGAR.NS",
        "AWL.NS","AXISBANK.NS","AXISCAPITAL.NS","B5AV.NS","BAFBBH.NS",
        "BAJAJ-AUTO.NS","BAJAJCON.NS","BAJAJELEC.NS","BAJAJFINSV.NS","BAJAJHLDNG.NS",
        "BAJFINANCE.NS","BAKERS.NS","BALAMINES.NS","BALAXI.NS","BALENABLE.NS",
        "BALKRISIND.NS","BALLARPUR.NS","BALMLAWRIE.NS","BALRAMCHIN.NS","BANDHANBNK.NS",
        "BANKBARODA.NS","BANKINDIA.NS","BANNARI.NS","BASF.NS","BAYERCROP.NS",
        "BBL.NS","BCLIND.NS","BECK.NS","BEML.NS","BERGEPAINT.NS",
        "BFIN.NS","BGRE.NS","BHAGYANGR.NS","BHARATFORG.NS","BHARATRAS.NS",
        "BHARTIARTL.NS","BHEL.NS","BHELIND.NS","BIGBLOC.NS","BIOCON.NS",
        "BIRLACORP.NS","BKESARI.NS","BLISSGVS.NS","BLKASHYAP.NS","BLS.NS",
        "BLUEBLENDS.NS","BLUEDART.NS","BLUESTAR.NS","BOMDYEING.NS","BOSCHLTD.NS",
        "BPCL.NS","BSE.NS","BSOFT.NS","BTT.NS","BurgerKing.NS",
        "CADILAHC.NS","CANBK.NS","CANFINHOME.NS","CAPLI.NS","CAPITALSFB.NS",
        "CARBORUNIV.NS","CARTRADE.NS","CASTEXIND.NS","CCL.NS","CESC.NS",
        "CGPOWER.NS","CHALET.NS","CHAMBLFERT.NS","CHEMPLAST.NS","CHENNPETRO.NS",
        "CHOLAFIN.NS","CHOLAHLDNG.NS","CIGNITI.NS","CINELINE.NS","CITYUNION.NS",
        "CKCL.NS","CLEAN.NS","CMI.NS","CMICABLES.NS","COALINDIA.NS",
        "COCHINSHIP.NS","COFORGE.NS","COLPAL.NS","COMPINFO.NS","CONCOR.NS",
        "COROMANDEL.NS","COUNIHOSP.NS","CPIL.NS","CRAFTSMAN.NS","CREATIVEYE.NS",
        "CREDITACC.NS","CRISIL.NS","CROMPTON.NS","CRUPHYL.NS","CSBBANK.NS",
        "CUB.NS","CUMMINSIND.NS","DABUR.NS","DALBHARAT.NS","DATAPATT.NS",
        "DBCORP.NS","DBREALTY.NS","DCAL.NS","DCBBANK.NS","DCMSRIND.NS",
        "DEEPAKFERT.NS","DEEPAKNTR.NS","DELHIVERY.NS","DEN.NS","DEVYANI.NS",
        "Dhampur.NS","DHANUKA.NS","DHFL.NS","DISHTV.NS","DLF.NS",
        "DOLAT.NS","DOLPHIN.NS","DPABHUSHAN.NS","DPWIRE.NS","DRREDDY.NS",
        "DSSL.NS","DTV.NS","DABUR.NS","DWARIKESH.NS","EASUNREY.NS",
        "ECLERX.NS","EICHERMOT.NS","EIDPARRY.NS","EIHOTEL.NS","EIMCOELECO.NS",
        "ELECTHERM.NS","ELENG.NS","ELGIEQUIP.NS","EMAMILTD.NS","ENIL.NS",
        "EQUITAS.NS","ERIS.NS","ESABINDIA.NS","ESSELPACK.NS","EASEMYTRIP.NS",
        "E2E.NS","FCONSUMER.NS","FEDERALBNK.NS","FEL.NS","FINEORG.NS",
        "FINCABLES.NS","FINPIPE.NS","FIVESTAR.NS","FL.NS","FOODSIN.NS",
        "FSL.NS","FUTURECONS.NS","FUTURELIFE.NS","FUTUREMARKET.NS","FUTURERET.NS",
        "GABRIEL.NS","GALLANTT.NS","GARFIBRES.NS","GBCL.NS","GEPIL.NS",
        "GICH.NS","GILLANDERS.NS","GIPCL.NS","GMRINFRA.NS","GMRPOWER.NS",
        "GNFC.NS","GODFRYPHLP.NS","GODREJAGRO.NS","GODREJCP.NS","GODREJIND.NS",
        "GODREJPROP.NS","GOCLCORP.NS","GOLDEN.NS","GOLDIAM.NS","GPIL.NS",
        "GPTINFRA.NS","GRAPHITE.NS","GRASIM.NS","GREAVESCOT.NS","GRINFRA.NS",
        "GRUH.NS","GSFC.NS","GSPL.NS","GUJALKALI.NS","GUJCHEM.NS",
        "GUVCONT.NS","HAL.NS","HATHWAY.NS","HAVELLS.NS","HBLPOWER.NS",
        "HCL-TECH.NS","HCLTECH.NS","HDFCAMC.NS","HDFCBANK.NS","HDFCLIFE.NS",
        "HEG.NS","HEIDELBERG.NS","HERITGFOOD.NS","HEROMOTOCO.NS","Hester.NS",
        "HGINFRA.NS","HGS.NS","HINDALCO.NS","HINDCOPPER.NS","HINDPETRO.NS",
        "HINDUNILVR.NS","HONAUT.NS","HOVS.NS","HUDCO.NS","IEX.NS",
        "IFBIND.NS","IFCI.NS","IFGLEXPOR.NS","IIFL.NS","IIFLFIN.NS",
        "IIFLSEC.NS","IIFLCAPS.NS","IOLCP.NS","IOL.NS","IPCALAB.NS",
        "IRB.NS","IRCON.NS","IRCTC.NS","IRFC.NS","INDHOTEL.NS",
        "INDIACEM.NS","INDIAMART.NS","INDIANB.NS","INDIGO.NS","INDOCO.NS",
        "INDSWFTLAB.NS","INDUSINDBK.NS","INDUSTOWER.NS","INFIBEAM.NS","INFY.NS",
        "INGERRAND.NS","INTELLECT.NS","IOC.NS","IOB.NS","IPCA.NS",
        "ITC.NS","ITI.NS","J&KBANK.NS","JAMNAAUTO.NS","JBCHEPHARM.NS",
        "JBTL.NS","JETAIRWAYS.NS","JINDALPOLY.NS","JINDALSAW.NS","JINDALSTEL.NS",
        "JKCEMENT.NS","JKLAKSHMI.NS","JKPAPER.NS","JKTYRE.NS","JMA.NS",
        "JMFINANCIL.NS","JSWENERGY.NS","JSWSTEEL.NS","JUBLFOOD.NS","JUBLINDS.NS",
        "JSL.NS","JSPL.NS","JUSTDIAL.NS","KAJARIACER.NS","KANSAINER.NS",
        "KARURVYSYA.NS","KCJ.NS","KDDL.NS","KECINTL.NS","KELTECH.NS",
        "KENNAMET.NS","KEI.NS","KFINTECH.NS","KHADIM.NS","KIND.NS",
        "KIRLFER.NS","KOLTEPATIL.NS","KOPRAN.NS","KOTAKBANK.NS","KPRMILL.NS",
        "KPITTECH.NS","KRBL.NS","KSERASERA.NS","KSCL.NS","KTKBANK.NS",
        "LALPATHLAB.NS","LAOPALA.NS","LATENTVIEW.NS","LAURUSLABS.NS","LAXMIMACH.NS",
        "LICHSGFIN.NS","LINDEINDIA.NS","LLOYDS.NS","LTF.NS","LTIM.NS",
        "LTTS.NS","LT.NS","LUMAXIND.NS","LUPIN.NS","M&MFIN.NS",
        "M&M.NS","MAHABANK.NS","MAHINDCIE.NS","MAHSEAMLES.NS","MAITHAN.NS",
        "MAJESCO.NS","MANAPPURAM.NS","MARICO.NS","MARKSANS.NS","MARUTI.NS",
        "MASTEK.NS","MAXHEALTH.NS","MCX.NS","MCDOWELL-N.NS","MEGH.NS",
        "METROBRAND.NS","MFSL.NS","MGL.NS","MINDACORP.NS","MINDTREE.NS",
        "M&MFIN.NS","MMTC.NS","MODI.NS","MODIRUB.NS","MOLDTKPAC.NS",
        "MOTHERSON.NS","MOTILALOFS.NS","MPHASIS.NS","MRPL.NS","MRF.NS",
        "MUKANDLTD.NS","MUNJAL.NS","MUTHOOTFIN.NS","NACLIND.NS","NAHAR.NS",
        "NAM-INDIA.NS","NATCOPHARM.NS","NATIONALUM.NS","NAUKRI.NS","NAVINFLUOR.NS",
        "NAVKARCORP.NS","NBCC.NS","NEOGEN.NS","NESTLEIND.NS","NETWORK18.NS",
        "NEWGEN.NS","NEWINDIA.NS","NHPC.NS","NIACL.NS","NIITLTD.NS",
        "NIITTECH.NS","NILASPAC.NS","NIPPOBATRY.NS","NLCINDIA.NS","NMDC.NS",
        "NOCIL.NS","NPST.NS","NTB.NS","NTL.NS","NTPC.NS",
        "NUCLEUS.NS","OBEROIRLTY.NS","OFSS.NS","OIL.NS","ONGC.NS",
        "OPTIEMUS.NS","ORICONENT.NS","ORIENTELEC.NS","ORIENTREF.NS","PADMAL.NS",
        "PAGEIND.NS","PANA.NS","PANACEABIO.NS","PANTALOON.NS","PAR.NS",
        "PATANJALI.NS","PAYTM.NS","PERSISTENT.NS","PETRONET.NS","PGHL.NS",
        "PGHH.NS","PHILIPCARB.NS","PHOENIXLTD.NS","PIDILITIND.NS","PIIND.NS",
        "PIRAMALEL.NS","PNB.NS","PNBHOUSING.NS","PNCINFRA.NS","POLICYBZR.NS",
        "POLYMED.NS","POLYCAB.NS","POWERGRID.NS","PRINCEPIPE.NS","PRISMCEM.NS",
        "PRUDENT.NS","PSB.NS","PSPPROJECT.NS","PUNJABCHEM.NS","RPOWER.NS",
        "RADICO.NS","RAILTEL.NS","RAIN.NS","RAMCOCEM.NS","RATEGAIN.NS",
        "RATNAMANI.NS","RBLBANK.NS","RCELL.NS","RCF.NS","RECLTD.NS",
        "RELIANCE.NS","RELINFRA.NS","RENUKA.NS","REP.NS","REPCAPITAL.NS",
        "RITES.NS","RUCHIRA.NS","RUSHIL.NS","RVNL.NS","SABEVENTS.NS",
        "SADBHAV.NS","SAIL.NS","SBFCFIN.NS","SBICARD.NS","SBILIFE.NS",
        "SBIN.NS","SCHAEFFLER.NS","SCI.NS","SELAN.NS","SEQUENT.NS",
        "SFL.NS","SHARDACROP.NS","SHIVALIK.NS","SHOPER.NS","SHOPTOP.NS",
        "SHREECEM.NS","SHREERENUKA.NS","SHRIRAMFIN.NS","SIEMENS.NS","SIMPLEXINF.NS",
        "SIS.NS","SITACABLE.NS","SITI.NS","SJVNL.NS","SKFINDIA.NS",
        "SMC.NS","SNL.NS","SOLARA.NS","SONACOMS.NS","SPICEJET.NS",
        "SPONGE.NS","SRF.NS","STAR.NS","STARCEM.NS","STARHEALTH.NS",
        "STOVE.NS","SUZLON.NS","SWANENERGY.NS","Suryoday.NS","SUNPHARMA.NS",
        "SUNTV.NS","SURYODAY.NS","SUVIDHA.NS","SWANENERGY.NS","SWARAJENG.NS",
        "SYNDICATE.NS","SYNGENE.NS","TATACHEM.NS","TATACOFFEE.NS","TATACONSUM.NS",
        "TATAELXSI.NS","TATAINVEST.NS","TATAMOTORS.NS","TATAPOWER.NS","TATASTEEL.NS",
        "TATAADVANCED.NS","TATAMTRDVC.NS","TATASTLP.NS","TBOBDK.NS","TCS.NS",
        "TECHM.NS","TEJASNET.NS","THERMAX.NS","THYROCARE.NS","TIINDIA.NS",
        "TIPSINDUST.NS","TITAGARH.NS","TITAN.NS","TNPETRO.NS","TORNTPHARM.NS",
        "TRENT.NS","TRIDENT.NS","TRIVENI.NS","TTKPRESTIG.NS","TV18BRDCST.NS",
        "TVSMOTOR.NS","TVSSCS.NS","UCOBANK.NS","UJJIVANSFB.NS","ULTRACEMCO.NS",
        "UNICHMLAB.NS","UNIENTER.NS","UNIPARTS.NS","UPL.NS","UTIAMC.NS",
        "UTKARSHBNK.NS","V-MART.NS","VAIBHAVGBL.NS","VBL.NS","VEDL.NS",
        "VGUARD.NS","VINATIORGA.NS","VIPIND.NS","VMART.NS","VSTIND.NS",
        "WABCOINDIA.NS","WELCORP.NS","WELENT.NS","WELSPUNLIV.NS","WHIRLPOOL.NS",
        "WIPRO.NS","WOCKPHARMA.NS","WONDERLA.NS","YESBANK.NS","ZENSARTECH.NS",
        "ZOMATO.NS","ZUARIGLOB.NS","ZYDUSLIFE.NS","ZYDUSWELL.NS",
    ],
}


# =========================================================================== #
#  2. KNOWLEDGE BASE — 100 distilled trading rules
# =========================================================================== #
RULES = [
    # Buffett / Graham
    "Price is what you pay, value is what you get. Focus on intrinsic value.",
    "Be fearful when others are greedy, greedy when others are fearful.",
    "Our favorite holding period is forever. Quality compounds over decades.",
    "Risk comes from not knowing what you're doing. Understand the business.",
    "It's far better to buy a wonderful company at a fair price than a fair company at a wonderful price.",
    "Margin of safety: buy when price is 25%+ below intrinsic value.",
    "Mr. Market is bipolar — take advantage of his mood swings.",
    "Diversification is protection against ignorance. Concentrate in your best ideas.",
    # Livermore / Schwager
    "The trend is your friend. Never fight the primary trend.",
    "Cut losses short, let profits run. Asymmetric payoff is the edge.",
    "Volume precedes price. A breakout without volume is suspect.",
    "Never average down. Adding to a losing position destroys capital.",
    "The big money is not in the buying and selling, but in the waiting.",
    "Risk management is the #1 differentiator, not strategy.",
    # López de Prado / Chan
    "Backtests overstate live returns. More parameters = more overfit.",
    "Cross-validation on time series must respect temporal order. Never shuffle.",
    "Sharpe ratio above 2.0 in a backtest is a red flag. Real strategies rarely exceed 1.5.",
    "Momentum works: assets that outperform over 3-12 months tend to continue.",
    "Mean reversion works on 1-5 day timeframes. RSI < 10 often precedes a bounce.",
    "Position sizing matters more than entry timing. 40% win rate at 2.5:1 R:R is profitable.",
    "Cointegration ≠ correlation. Test with Engle-Granger before pairs trading.",
    # Howard Marks
    "Risk is not volatility — it's the probability of permanent loss.",
    "Markets are cyclical. Trees don't grow to the sky, things don't go to zero.",
    "Second-level thinking: 'it's a good company but everyone thinks it's great — so it's overpriced.'",
    "The most profitable thing is to buy when others are panicking.",
    "Being too far ahead of your time is indistinguishable from being wrong.",
    # Dalio
    "Pain + Reflection = Progress. Every losing trade is a data point.",
    "Diversify across 15-20 uncorrelated return streams. This is the Holy Grail.",
    "Don't trust your gut — trust the process. Build systematic decision systems.",
    "All economic activity is driven by productivity, short-term debt cycle, and long-term debt cycle.",
    # Natenberg / Sinclair
    "Implied vol is the only unknown. When IV > HV, options are expensive (sell).",
    "PCR > 1.3 = excessive bearishness (contrarian bullish). PCR < 0.7 = excessive greed.",
    "Max pain: price gravitates toward the strike where option holders lose most.",
    "Long buildup: price ↑ + OI ↑ = bullish. Short buildup: price ↓ + OI ↑ = bearish.",
    "Volatility clustering: high vol today predicts high vol tomorrow.",
    # Douglas / Psychology
    "Think in probabilities, not certainties. No single trade matters.",
    "Accept the risk before entering. If you can't accept the loss, don't take the trade.",
    "Revenge trading after a loss is the most destructive behavior.",
    "Your worst enemy is your own emotions. Fear exits winners early. Greed holds losers.",
    "The zone: a state of flow where you execute without thinking.",
    # Risk Management
    "Never risk more than 1-2% of capital on a single trade. Survival comes first.",
    "Risk/Reward must be at least 1:2. Below 1:2 = reject the trade.",
    "The stop-loss is not optional. Every trade must have a predefined exit.",
    "Volatility-based position sizing: use ATR for stop distance, size for 1% risk.",
    "If drawdown exceeds 10%, halve all position sizes until equity recovers.",
    "Correlation between positions matters. Two correlated stocks = one bet.",
    "Never move a stop further away. This is the #1 way traders blow up accounts.",
    # Indian Market
    "Indian stocks gap. Size positions assuming the stop will slip by 0.25 ATR.",
    "NSE cash has no overnight short selling. A swing short means 'avoid longs.'",
    "FII flows drive Indian markets. 3+ days of FII buying = bullish. Sustained selling = correction.",
    "Delivery % above 60% with above-average volume = genuine accumulation.",
    "Turn of the month effect: SIP flows push indices up in first 3-5 trading days.",
    # Academic
    "Fama-French 3-factor: market, size, value explain most stock returns.",
    "Post-Earnings Announcement Drift: beats drift up 60 days, misses drift down.",
    "Low volatility anomaly: low-beta stocks outperform on risk-adjusted basis.",
    "Earnings revision momentum: analysts revise estimates before ratings. Track revisions.",
    "Quality factor: high gross profitability (gross profit / assets) outperforms.",
    "Accrual anomaly: companies with high accruals (earnings >> cash flow) underperform.",
    # Microstructure
    "The bid-ask spread is a hidden tax. Trade liquid stocks (ADV > 10cr).",
    "Market impact scales with sqrt(order size / ADV). Stay under 1% ADV.",
    "Informed traders prefer limit orders. Liquidity traders use market orders.",
    "Liquidity cascades: stop-losses trigger more stops. Overshoots are opportunities.",
    # Seasonal / Macro
    "Seasonality: November-April is historically strongest for equities.",
    "Rate hikes hurt NBFCs, realty, autos within 60 days. Rate cuts help them.",
    "Crude oil: falling crude = margin expansion for paints, airlines. Rising = opposite.",
    "USDINR: falling rupee is bullish for IT/pharma exporters, bearish for importers.",
    # Buffett / Munger extras
    "Invert, always invert. Ask how to lose money, then avoid those things.",
    "I never hold an opinion I can't state the arguments against better than supporters.",
    "Capital allocation is the CEO's most important job. Watch what they do with cash.",
    "Accounting is the language of business. Read financial statements before charts.",
    # Soros
    "Markets are not passive reflections — they actively shape reality. This is reflexivity.",
    "It's not whether you're right or wrong, but how much you make when right vs wrong.",
    # Alternative Data
    "Google Trends: rising branded search precedes revenue growth by 1-2 quarters.",
    "Job postings: aggressive hiring = growth. Hiring freezes precede weak earnings.",
    "Insider buying: 3+ insiders buying in 30 days = strong bullish signal.",
    "Promoter pledging = red flag. Promoter stake increase = very bullish (India).",
    # Pattern Detection
    "Hammer: small body at top, long lower wick = bullish reversal after downtrend.",
    "Bullish engulfing: large green candle engulfs prior red = strong bullish reversal.",
    "Morning star: red → small → large green = 3-candle bottom reversal.",
    "Shooting star: small body at bottom, long upper wick = bearish reversal.",
    "Bearish engulfing: large red engulfs prior green = strong bearish reversal.",
    # Strategy Rules
    "12-1 momentum: buy top 20% by 12-month return (skip last month). Rebalance monthly.",
    "RSI(2) Connors: buy RSI(2)<10, sell RSI(2)>70. Ultra-short mean reversion.",
    "Golden cross: 50-SMA crosses above 200-SMA = long-term bullish.",
    "Days down overnight: buy after 3+ consecutive down closes, sell next open.",
    "Dual momentum: buy if up over 12mo AND beating NIFTY. Sell if either fails.",
    "Bollinger squeeze: buy when BB width at 6-mo low and price breaks above upper band.",
    "Turn of the month: buy last 4 trading days of month, sell first 3 of new month.",
    "Holiday effect: buy 2 days before NSE holidays, sell 1 day after.",
    "Volume breakout: buy on 2x volume + new 20-day high.",
    "MACD divergence: price lower low but MACD higher low = bullish reversal.",
    "ATR breakout: buy on 1.5x ATR range day closing in upper half.",

    # From Ultimate Trading RAG Knowledge Base (1599 lines)
    "Wyckoff Method: Accumulation phase = smart money buying quietly (sideways price, irregular volume). Spring (false breakdown) = buy signal. UTAD (upthrust after distribution) = sell signal.",
    "Wyckoff Laws: (1) Supply vs Demand — price rises when demand > supply. (2) Cause & Effect — size of accumulation = size of markup. (3) Effort vs Result — volume should match price move. Divergence = reversal.",
    "Volume Spread Analysis (VSA): Wide spread up + ultra-high volume = potential distribution climax. Narrow spread up + high volume = hidden selling (bearish). Narrow spread down + low volume = no supply (bullish).",
    "VSA No Demand Signal: narrow spread up bar on low volume = no institutional buying. No Supply Signal: narrow spread down on low volume = no institutional selling.",
    "Market Profile: POC (Point of Control) = price with most time/volume. Price returns to POC. Break above VAH (Value Area High) with acceptance = bullish. Break below VAL = bearish.",
    "Market Profile shapes: P-shape = buying tail at bottom (bullish). b-shape = selling tail at top (bearish). Double distribution = trend day. Single prints = imbalance, price returns to fill.",
    "Order Flow: Delta = buying volume - selling volume. Positive delta = buyers winning. Cumulative delta diverging from price = reversal signal. Absorption = large volume with little price movement = reversal.",
    "ICT/Smart Money Concepts: Buy-Side Liquidity (BSL) above swing highs = institutions push price up to grab stop-losses then reverse. Sell-Side Liquidity (SSL) below swing lows = institutions push down to grab stops.",
    "ICT Fair Value Gap (FVG): 3-candle imbalance where middle candle body doesn't overlap with 1st or 3rd candle wick. Price returns to fill these gaps.",
    "ICT Order Block: last down candle before strong up move = bullish OB. Last up candle before strong down move = bearish OB. Institutions placed orders there.",
    "ICT Optimal Trade Entry (OTE): 61.8-79% Fibonacci retracement of a swing = high-probability entry zone.",
    "ICT Killzones: London Open 3-5am EST, NY Open 9:30-11am EST, NY Lunch 1-2pm EST, London Close 10-12pm EST = highest probability trading times.",
    "ICT Power of 3 (AMD): Accumulation (smart money accumulates at lows) → Manipulation (false move to hunt stops) → Distribution (true directional move).",
    "Intermarket Analysis: Bonds UP → Stocks UP. Dollar UP → Commodities DOWN. Oil UP → Energy stocks UP, Airlines DOWN. Gold UP = risk-off. Copper UP = global growth. VIX UP = stocks DOWN. Yield curve inverts = recession in 12-18 months.",
    "Auction Market Theory: Price seeks path of least resistance to find liquidity. Trending market = no acceptance at levels. Ranging market = acceptance within value area. Price above resistance for 2+ days = new value, not a fade.",
    "Gamma Exposure (GEX): Positive GEX = MMs dampen volatility, price gravitates to max pain. Negative GEX = MMs amplify volatility, trending/explosive moves. GEX flip level = volatility regime change.",
    "Dark Pool: 40-50% of US equity volume trades off-exchange. Large dark pool prints at a price = institutional interest = strong S/R. Repeated prints = accumulation.",
    "Tape Reading: Large lots at bid = institutional selling. Large lots at ask = institutional buying. Volume surge with price unchanged = absorption. Sweep orders = aggressive directional bet.",
    "Statistical Arbitrage: Find cointegrated pairs (Engle-Granger test). Spread Z-score < -2 = buy spread. Z > +2 = sell spread. Exit at Z=0. Stop at Z=±3. Half-life 1-30 days.",
    "Factor Investing: Fama-French 5 factors = market, size (small beats large), value (high book/market wins), profitability (high operating profit wins), investment (conservative wins). Plus momentum and low-vol.",
    "Piotroski F-Score: 9-point fundamental score. 8-9 = strong buy. 0-2 = short. Checks ROA, cash flow, leverage, efficiency, margins.",
    "Altman Z-Score: Bankruptcy predictor. Z > 2.99 = safe. 1.81-2.99 = grey zone. < 1.81 = distress.",
    "Beneish M-Score: Earnings manipulation detector. M > -1.78 = likely manipulator. Check before investing.",
    "Dispersion Trading: Short index variance, long component variance. Profit when stocks move independently (low correlation). Hedge funds use this for market-neutral vol trading.",
    "Convertible Bond Arbitrage: Buy undervalued convertible bond, short underlying stock (delta hedge). Profit from gamma scalping + cheap optionality. Bond floor = downside protection.",
    "Volatility Surface: IV skew = puts more expensive than calls (crash protection demand). Steeper skew = more fear. Term structure contango = short vol profitable. Backwardation = crisis mode.",
    "Connors RSI (CRSI) = (RSI(3) + RSI(Streak,2) + PercentRank(100)) / 3. Buy < 10, sell > 90. Win rate ~70% historically.",
    "Ornstein-Uhlenbeck process for mean reversion: Half-life = ln(2)/theta. Only trade if half-life is 1-30 days. Practical mean reversion timeframe.",
    "Bollinger Band Mean Reversion system: Entry = price below lower band 2 consecutive days + RSI < 30 + volume spike. Target = middle band. Stop = 1 ATR below lower band.",
    "Dual Momentum (Antonacci): Absolute momentum (is asset return > T-bills?) + Relative momentum (which asset has higher return?). Simple 2-asset rotation. No leverage needed.",
    "Time Series Momentum (TSMOM): If 12-month return > 0, go long. If < 0, go short. Diversify across 20+ markets. Core strategy at AQR, Winton, Man AHL.",
    "Momentum crashes: Happen in sharp rebounds after crashes (2009, 2020). Hedge: go flat momentum when VIX > 40. Use option protection in high-vol regimes.",
    "Turtle Trading variant: Entry = 20-day or 55-day Donchian breakout. Exit = 10-day or 20-day opposite breakout. Position = 1 ATR = 1% risk. Stop = 2 ATR. Trade 20+ uncorrelated markets.",
    "Multi-timeframe trend: Weekly trend filter + daily entry signal. If weekly up, only take daily longs. Reduces whipsaws dramatically.",
    "Merger Arbitrage: Buy target after deal announced. Spread = deal price - current price. Annualized return = spread/days × 365. Risk = deal breaks (target falls 20-40%).",
    "PEAD (Post-Earnings Announcement Drift): Beats drift up 60-90 days. Misses drift down 60-90 days. Buy beats + raised guidance + +3% gap up. Hold 30-60 days.",
    "Spin-Off Strategy: Spin-offs outperform market. Index funds forced to sell (not in index). Watch for insider buying post-listing. Hold 12-18 months.",
    "Volatility Carry (VRP): IV almost always > RV. Short options to collect premium. Expected profit = IV - RV. Risk = short gamma, unlimited loss in crashes. Use spreads not naked shorts.",
    "Commodity Carry: Backwardation = positive roll yield (earn by holding). Contango = negative roll yield (cost to hold). Long backwardated, short contangoed commodities.",
    "ML Feature Engineering: Rolling returns (1d,5d,21d,63d,252d), volatility, skewness, distance from 52w high/low, gap size, Amihud illiquidity ratio, volume surprise, EPS revision %.",
    "ML Cross-Validation for Finance: Walk-forward validation (train past, test future, roll forward). Purged K-fold (remove data around test period). Embargo period (skip N days between folds).",
    "ML Overfitting Prevention: Out-of-sample tests, regularization (L1/L2), < 20 features, ensemble methods, test across market regimes. Beware data snooping, lookahead bias, survivorship bias.",
    "NLP Sentiment: Use Loughran-McDonald Finance Dictionary (not general sentiment). Tone score = (pos-neg)/total. Change in tone quarter-over-quarter = more powerful than absolute tone.",
    "Earnings Call Signals: CFO not on call = bad sign. CEO uses past tense = less confident. Analyst questions getting longer = skepticism. 'Headwinds' count rising = bearish.",
    "FinBERT: Pre-trained BERT on financial news. Better than generic sentiment for finance text. Available at huggingface.co/ProsusAI/finbert.",
    "Alternative Data: Satellite (parking lot cars, oil tank shadows), credit card transactions (predict revenue), job postings (growth signal), app downloads (product health), Google Trends (demand).",
    "Congressional Trading: Members of Congress must disclose trades. Cluster buying by Congress = potential insider knowledge. Track at quiverquant.com/congresstrading.",
    "Insider Trading: Form 4 filings on SEC. Cluster buying (3+ insiders simultaneously) = very bullish. CEOs buying with personal funds = strongest signal.",
    "Backtesting Biases: Survivorship bias (only test existing stocks). Lookahead bias (using future data). Data snooping (testing many params, keeping best). Slippage neglect. Always use realistic costs.",
    "Walk-Forward Analysis: 70% in-sample, 30% out-of-sample. Optimize on IS, test on OOS. If OOS < 50% of IS performance = overfit. Roll forward and repeat.",
    "Monte Carlo Simulation: Randomize trade sequence 10,000 times. Find 95th percentile worst drawdown. Find probability of ruin. More robust than single-path backtesting.",
    "Minimum Live Trading Criteria: 200+ backtest trades, positive OOS performance, Sharpe > 0.5, max DD < 3x annual return, consistent across regimes.",
    "RSI-2 Strategy (Larry Connors): Stock above 200-day SMA + RSI(2) < 10 = buy. Exit when RSI(2) > 70. Historical win rate ~70%.",
    "Sector Rotation: Early expansion = Financials, Consumer Disc, Industrials. Mid = Tech, Materials, Energy. Late = Energy, Staples. Recession = Staples, Healthcare, Utilities.",
    "Kelly Criterion: f* = (bp-q)/b where b=odds, p=win rate, q=1-p. Use HALF Kelly in practice. Full Kelly too volatile.",
    "Position Sizing: Fixed Fractional (1-2% risk), Volatility-Normalized (ATR-based), Risk Parity (equal risk contribution), Kelly (mathematical optimal). Never use equal dollar (ignores volatility).",
    "Risk Metrics: Sharpe = return/vol (target > 1.0). Sortino = return/downside vol (better). Calmar = CAGR/max DD (target > 0.5). VaR 95% = max expected loss. CVaR = avg loss beyond VaR.",
    "Stop Loss Types: ATR stop (most recommended), swing stop (below recent low), volatility stop (X std devs), time stop (exit if no progress in N days). NEVER use mental stops.",
    "Trade Management: Scale in (add as trade proves itself), scale out (partial profits at targets), break-even stop at +1R, trail stop on remainder. Let winners run.",
    "Psychological Risk: Stop trading after 2 consecutive losses. Max N trades per day. If missed entry, wait for next setup — never chase. Pre-trade checklist mandatory.",
    "Cognitive Biases: Loss aversion (losses feel 2x worse), disposition effect (sell winners, hold losers), anchoring (fixated on entry price), FOMO (chase after move), sunk cost (hold because already lost).",
    "Expected Value thinking: A trade is good if EV positive, regardless of individual outcome. Probabilistic thinking: any single trade is random, only the distribution matters. Process > outcome.",
    "Premortem: Before taking trade, ask 'What would make me wrong?' Red team your own thesis. Argue against yourself.",
    "Crypto On-Chain: NVT ratio (like P/E for crypto). MVRV Z-Score (overvalued when high). SOPR (are holders selling at profit?). Exchange netflows (coins TO exchange = sell pressure).",
    "COT Report (Forex): When non-commercials at extreme net long = contrarian sell signal. When extreme net short = contrarian buy signal. Weekly CFTC report.",
    "Yield Curve: 10Y-2Y spread inversion = recession in 12-18 months (historically). 10Y-3M spread favored by Fed researchers. Rising 2Y = hawkish expectations.",
    "Macro Leading Indicators: Conference Board LEI (10-component composite). Consecutive months of declining LEI = recession warning. Components include stock prices, building permits, yield curve.",
    "Data Sources Master: Yahoo Finance (free prices), Alpha Vantage (free API), Polygon.io (real-time), FRED (macro data), SEC EDGAR (filings), OpenInsider (insider trades), Finviz (screener).",
    # Portfolio
    "The Information Ratio = expected active return / tracking error. Good = 0.5-1.0.",
    "Diversification across uncorrelated strategies reduces risk more than across stocks.",
    "Every trade should be saved. After 10,000+ trades, the AI can find patterns.",
    "Score every stock out of 100. 80+ = strong buy. 70-79 = watchlist. <60 = ignore.",
    "Regime detection first, strategy second. Momentum fails in ranges. Mean reversion fails in trends.",
    # Taleb
    "Survivorship bias: we see winners, not losers. Don't confuse luck with skill.",
    "Black swans: extreme events dominate history. Normal distributions underestimate tails.",
    "Barbell strategy: 90% ultra-safe, 10% ultra-aggressive. Antifragile.",
    # Bogle / Indexing
    "Costs matter: 1% annual fee = 28% of wealth over 40 years. Use low-cost index funds.",
    "Time in the market > timing the market. The best days often follow the worst.",
    "Stay the course. The market will crash and recover. Don't sell at the bottom.",
    # Greenblatt
    "Magic Formula: rank by earnings yield (EBIT/EV) + return on capital. Buy top stocks.",
    "Special situations: spin-offs, mergers, restructurings offer uncorrelated returns.",
    # Kahneman
    "Loss aversion: losses hurt 2x more than gains feel good. Causes holding losers, selling winners.",
    "Confirmation bias: actively seek counter-arguments. The bear case for longs.",
    "Overconfidence: after 3 wins, you feel invincible. This is when you blow up.",
    # O'Neil
    "CANSLIM: C=current quarterly earnings up 25%+, A=annual earnings up, N=new product, S=supply/demand, L=leader, I=institutional, M=market direction.",
    "Cut losses at 7-8%. No exceptions. This rule has saved more investors than any other.",
    # Wyckoff
    "Wyckoff spring: false breakdown below support = buy signal. Upthrust: false breakout = sell.",
    "Accumulation → Markup → Distribution → Markdown. Identify the phase.",
    # Final
    "The strongest AI combines: real-time news + sentiment + options flow + institutional flow + TA + backtesting + risk management.",
    "Structure your knowledge: market regimes, strategies, risk, psychology, history. Not random books.",
]


# =========================================================================== #
#  3. SECTOR DATA
# =========================================================================== #
SECTORS = {
    "BANK": {"stocks": ["HDFCBANK", "ICICIBANK", "SBIN", "AXISBANK", "KOTAKBANK", "BANKBARODA", "PNB", "AUBANK"]},
    "IT": {"stocks": ["TCS", "INFY", "WIPRO", "HCLTECH"]},
    "FMCG": {"stocks": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR", "GODREJCP", "MARICO", "COLPAL"]},
    "PHARMA": {"stocks": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "AUROPHARMA", "ALKEM", "LAURUSLABS", "BIOCON"]},
    "AUTO": {"stocks": ["MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO"]},
    "METAL": {"stocks": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "SAIL", "JINDALSTEL", "NMDC"]},
    "ENERGY": {"stocks": ["RELIANCE", "ONGC", "IOC", "BPCL", "NTPC", "POWERGRID", "COALINDIA"]},
    "FIN": {"stocks": ["BAJFINANCE", "BAJAJFINSV", "LT", "HDFCLIFE", "SBILIFE", "CHOLAFIN", "MUTHOOTFIN"]},
}


# =========================================================================== #
#  4. SIMPLE ANALYSIS ENGINE (no heavy dependencies)
# =========================================================================== #
def analyze_stock(symbol: str, capital: float = 100000) -> dict:
    """Analyze a stock and return a score + explanation.

    This is the brain's core function. It fetches data, computes indicators,
    scores the stock across 6 layers, and returns the result.
    """
    import yfinance as yf

    sym = symbol if "." in symbol else f"{symbol}.NS"

    # Fetch data
    try:
        ticker = yf.Ticker(sym)
        hist = ticker.history(period="1y", interval="1d")
        if hist is None or hist.empty or len(hist) < 30:
            return {"error": f"No data for {sym}", "symbol": sym}
        info = ticker.info or {}
    except Exception as e:
        return {"error": str(e), "symbol": sym}

    close = hist["Close"]
    volume = hist["Volume"]
    high = hist["High"]
    low = hist["Low"]
    current_price = float(close.iloc[-1])

    # Compute indicators
    sma_20 = close.rolling(20).mean().iloc[-1]
    sma_50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else None
    sma_200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else None

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = (100 - (100 / (1 + rs))).iloc[-1]
    rsi = float(rsi) if not np.isnan(rsi) else 50

    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9).mean()
    macd_hist = float((macd - macd_signal).iloc[-1])

    # ATR
    tr = pd.concat([(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1])

    # Volume ratio
    avg_vol_20 = float(volume.iloc[-20:].mean())
    last_vol = float(volume.iloc[-1])
    vol_ratio = last_vol / avg_vol_20 if avg_vol_20 > 0 else 1

    # 52-week high/low
    high_52w = float(high.tail(252).max()) if len(high) >= 252 else float(high.max())
    low_52w = float(low.tail(252).min()) if len(low) >= 252 else float(low.min())

    # Bollinger Bands
    bb_mid = sma_20
    bb_std = close.rolling(20).std().iloc[-1]
    bb_upper = float(bb_mid + 2 * bb_std)
    bb_lower = float(bb_mid - 2 * bb_std)

    # ========== SCORE EACH LAYER ========== #

    # 1. Technical (0-30) — recalibrated for realistic distribution
    tech_score = 10  # baseline
    if sma_50 and current_price > sma_50:
        tech_score += 5
    if sma_200 and current_price > sma_200:
        tech_score += 5
    if current_price > sma_20:
        tech_score += 3
    if 40 < rsi < 65:
        tech_score += 4  # healthy momentum
    elif 30 < rsi <= 40 or 65 <= rsi < 75:
        tech_score += 2  # slightly extended
    elif rsi <= 30:
        tech_score += 5  # oversold bounce candidate
    elif rsi >= 75:
        tech_score -= 2  # very overbought
    if macd_hist > 0:
        tech_score += 3
    if vol_ratio > 1.3:
        tech_score += 3  # volume confirmation
    elif vol_ratio > 1.0:
        tech_score += 1
    tech_score = max(0, min(30, tech_score))

    # 2. News (0-20) — recalibrated: use 5d + 20d returns as news proxy
    ret_5d = (current_price / float(close.iloc[-6]) - 1) * 100 if len(close) >= 6 else 0
    ret_20d = (current_price / float(close.iloc[-21]) - 1) * 100 if len(close) >= 21 else 0
    news_score = 10  # neutral baseline
    if ret_5d > 2:
        news_score += 4
    elif ret_5d > 0:
        news_score += 2
    elif ret_5d < -3:
        news_score -= 3
    if ret_20d > 8:
        news_score += 4
    elif ret_20d > 3:
        news_score += 2
    elif ret_20d < -8:
        news_score -= 4
    news_score = max(0, min(20, news_score))

    # 3. Sentiment (0-15) — recalibrated volume trend
    vol_trend = vol_ratio
    sent_score = 7  # neutral
    if vol_trend > 2:
        sent_score += 6  # very high volume = strong interest
    elif vol_trend > 1.3:
        sent_score += 4
    elif vol_trend > 1.0:
        sent_score += 2
    elif vol_trend < 0.5:
        sent_score -= 1
    sent_score = max(0, min(15, sent_score))

    # 4. Institutional (0-15) — recalibrated delivery proxy
    close_pos = (current_price - float(low.iloc[-1])) / max(float(high.iloc[-1] - low.iloc[-1]), 0.01)
    delivery_proxy = close_pos * 50 + min(vol_trend, 2) * 25
    inst_score = max(0, min(15, delivery_proxy / 7))  # less harsh divisor

    # 5. Options (0-10) — recalibrated
    opt_score = 5  # neutral
    if current_price > bb_upper:
        opt_score += 3  # momentum breakout
    elif current_price > sma_20:
        opt_score += 2  # above mean
    elif current_price < bb_lower:
        opt_score -= 2  # breakdown
    opt_score = max(0, min(10, opt_score))

    # 6. Fundamentals (0-10) — recalibrated
    fund_score = 5  # neutral
    pe = info.get("trailingPE")
    roe = info.get("returnOnEquity")
    rev_g = info.get("revenueGrowth")
    if pe and pe > 0:
        if pe < 15:
            fund_score += 3
        elif pe < 25:
            fund_score += 2
        elif pe < 40:
            fund_score += 1
        else:
            fund_score -= 1
    if roe and roe > 0.15:
        fund_score += 2
    elif roe and roe > 0.10:
        fund_score += 1
    if rev_g and rev_g > 0.15:
        fund_score += 1
    elif rev_g and rev_g > 0.05:
        fund_score += 0.5
    fund_score = max(0, min(10, fund_score))

    # ========== TOTAL SCORE ========== #
    total = tech_score + news_score + sent_score + inst_score + opt_score + fund_score

    # Rating
    if total >= 80:
        rating = "STRONG BUY"
        action = "🟢 Full position size (1% risk). High-conviction trade."
    elif total >= 70:
        rating = "WATCHLIST"
        action = "🟡 Normal position size. Good setup with minor concerns."
    elif total >= 60:
        rating = "SPECULATIVE"
        action = "🟠 Half position size. Mixed signals."
    else:
        rating = "IGNORE"
        action = "🔴 Do not trade. Insufficient conviction."

    # ========== BUILD EXPLANATION ========== #
    reasons = []
    risks = []

    if sma_200 and current_price > sma_200:
        reasons.append(f"✅ Above 200-day MA (₹{sma_200:.0f}) — long-term uptrend")
    elif sma_200:
        risks.append(f"⚠️ Below 200-day MA (₹{sma_200:.0f}) — long-term downtrend")

    if sma_50 and current_price > sma_50:
        reasons.append(f"✅ Above 50-day MA (₹{sma_50:.0f}) — medium-term uptrend")
    elif sma_50:
        risks.append(f"⚠️ Below 50-day MA (₹{sma_50:.0f}) — medium-term downtrend")

    if rsi < 35:
        reasons.append(f"✅ RSI {rsi:.0f} — oversold, bounce candidate")
    elif rsi > 70:
        risks.append(f"⚠️ RSI {rsi:.0f} — overbought, pullback risk")
    elif 45 < rsi < 65:
        reasons.append(f"✅ RSI {rsi:.0f} — healthy momentum zone")

    if macd_hist > 0:
        reasons.append("✅ MACD bullish (above signal line)")
    else:
        risks.append("⚠️ MACD bearish (below signal line)")

    if vol_ratio > 1.3:
        reasons.append(f"✅ Volume {vol_ratio:.1f}x average — strong participation")
    elif vol_ratio < 0.6:
        risks.append(f"⚠️ Volume {vol_ratio:.1f}x average — low interest")

    if ret_5d > 2:
        reasons.append(f"✅ Up {ret_5d:.1f}% in 5 days — positive momentum")
    elif ret_5d < -3:
        risks.append(f"⚠️ Down {ret_5d:.1f}% in 5 days — negative momentum")

    if ret_20d > 5:
        reasons.append(f"✅ Up {ret_20d:.1f}% in 20 days — strong trend")
    elif ret_20d < -5:
        risks.append(f"⚠️ Down {ret_20d:.1f}% in 20 days — weak trend")

    if current_price >= high_52w * 0.95:
        reasons.append(f"✅ Near 52-week high (₹{high_52w:.0f}) — momentum")
    elif current_price <= low_52w * 1.05:
        risks.append(f"⚠️ Near 52-week low (₹{low_52w:.0f}) — weakness")

    if pe and pe > 0:
        if pe < 20:
            reasons.append(f"✅ P/E {pe:.1f} — reasonable valuation")
        elif pe > 40:
            risks.append(f"⚠️ P/E {pe:.1f} — expensive")

    if roe and roe > 0.15:
        reasons.append(f"✅ ROE {roe*100:.1f}% — high return on equity")

    # Get sector
    sector = info.get("sector", "Unknown")
    industry = info.get("industry", "")
    market_cap = info.get("marketCap", 0)
    if market_cap and market_cap > 2e12:
        cap_type = "Large Cap"
    elif market_cap and market_cap > 5e10:
        cap_type = "Mid Cap"
    else:
        cap_type = "Small Cap"

    # ========== BUILD THE ACTION PLAN ========== #
    # ONE clear recommendation. Not 3 forecasts. Just: BUY / WAIT / AVOID.
    # With ONE entry, ONE stop, ONE target.

    atr_mult = 2.0
    stop = current_price - atr_mult * atr
    target = current_price + 2.5 * atr_mult * atr
    risk_per_share = abs(current_price - stop)
    reward_per_share = abs(target - current_price)
    qty = int((capital * 0.01) / risk_per_share) if risk_per_share > 0 else 0
    rr = 2.5
    capital_at_risk = qty * risk_per_share
    potential_profit = qty * reward_per_share

    # Determine direction
    if sma_50 and current_price > sma_50 and macd_hist > 0:
        direction = "LONG (Buy)"
    elif sma_50 and current_price < sma_50 and macd_hist < 0:
        direction = "SHORT (Avoid/Exit)"
    else:
        direction = "NEUTRAL (Wait)"

    # Build the simple action plan
    if total >= 70:
        action_plan = f"BUY NOW — {direction}. This stock scored {total:.0f}/100. Enter near ₹{current_price:.0f}, place stop-loss at ₹{stop:.0f}, target ₹{target:.0f}. Buy {qty} shares. If stop hits, you lose ₹{capital_at_risk:.0f}. If target hits, you profit ₹{potential_profit:.0f}."
    elif total >= 60:
        action_plan = f"WAIT — {direction}. Score {total:.0f}/100 is decent but not strong. Watch the stock. If it breaks above ₹{target:.0f} on high volume, buy. If it falls below ₹{stop:.0f}, the setup is dead."
    else:
        action_plan = f"AVOID — {direction}. Score {total:.0f}/100 is too low. Don't trade this stock now. Look for stocks scoring 70+."

    # Potential profit/loss in simple terms
    pnl_summary = {
        "if_you_buy": f"Buy {qty} shares at ₹{current_price:.0f} = ₹{qty * current_price:,.0f} invested",
        "if_target_hits": f"Target ₹{target:.0f} → Profit = +₹{potential_profit:,.0f} (+{(reward_per_share/current_price*100):.1f}%)",
        "if_stop_hits": f"Stop ₹{stop:.0f} → Loss = -₹{capital_at_risk:,.0f} (-{(risk_per_share/current_price*100):.1f}%)",
        "risk_reward_ratio": f"1:{rr:.1f} (risk ₹{risk_per_share:.0f} to make ₹{reward_per_share:.0f} per share)",
    }

    return {
        "symbol": sym,
        "name": info.get("shortName", sym),
        "sector": sector,
        "industry": industry,
        "cap_type": cap_type,
        "current_price": round(current_price, 2),
        "score": round(total),
        "rating": rating,
        "direction": direction,
        "action_plan": action_plan,
        "pnl_summary": pnl_summary,
        "scores": {
            "technical": tech_score,
            "news": news_score,
            "sentiment": sent_score,
            "institutional": round(inst_score),
            "options": opt_score,
            "fundamentals": fund_score,
        },
        "indicators": {
            "rsi": round(rsi, 1),
            "macd_hist": round(macd_hist, 2),
            "atr": round(atr, 2),
            "sma_20": round(float(sma_20), 2),
            "sma_50": round(float(sma_50), 2) if sma_50 else None,
            "sma_200": round(float(sma_200), 2) if sma_200 else None,
            "bb_upper": round(bb_upper, 2),
            "bb_lower": round(bb_lower, 2),
            "volume_ratio": round(vol_ratio, 2),
            "high_52w": round(high_52w, 2),
            "low_52w": round(low_52w, 2),
            "return_5d": round(ret_5d, 2),
            "return_20d": round(ret_20d, 2),
            "pe_ratio": pe,
            "roe": round(roe * 100, 1) if roe else None,
        },
        "plan": {
            "entry": round(current_price, 2),
            "stop": round(stop, 2),
            "target": round(target, 2),
            "quantity": qty,
            "risk_reward": rr,
            "capital_at_risk": round(capital_at_risk, 2),
            "potential_profit": round(potential_profit, 2),
        },
        "reasons": reasons,
        "risks": risks,
        "patterns": detect_chart_patterns(hist),
        "historical_stats": get_historical_pattern_stats(hist),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


# =========================================================================== #
#  5. KNOWLEDGE SEARCH  (hybrid: built-in rules + ChromaDB RAG)
# =========================================================================== #
def search_knowledge(query: str, top_k: int = 5) -> list[dict]:
    """Search the knowledge base for rules relevant to the query.

    Hybrid search:
      1. Built-in RULES (Jaccard similarity on tokens)
      2. ChromaDB vector search over market_data_sources collection
         (populated by scrape_and_train_rag.py — 796 docs from 34 sources)
    """
    # --- 1. Built-in rules (keyword overlap) ---
    query_words = set(re.findall(r"[a-z]+", query.lower()))
    scored = []
    for i, rule in enumerate(RULES):
        rule_words = set(re.findall(r"[a-z]+", rule.lower()))
        overlap = len(query_words & rule_words)
        union = len(query_words | rule_words)
        score = overlap / union if union > 0 else 0
        scored.append({"rule": rule, "relevance": round(score, 3), "id": i, "source": "builtin"})
    scored.sort(key=lambda x: x["relevance"], reverse=True)
    builtin_results = [s for s in scored[:top_k] if s["relevance"] > 0]

    # --- 2. ChromaDB vector search (semantic, over scraped web sources) ---
    rag_results: list[dict] = []
    try:
        import chromadb
        db_path = Path(__file__).resolve().parent / "rl_models" / "chromadb"
        if db_path.exists():
            client = chromadb.PersistentClient(path=str(db_path))
            try:
                col = client.get_collection("market_data_sources")
                if col is not None and col.count() > 0:
                    res = col.query(query_texts=[query], n_results=min(top_k, 5))
                    for i, doc in enumerate(res.get("documents", [[]])[0]):
                        meta = res.get("metadatas", [[]])[0][i] if res.get("metadatas") else {}
                        dist = res.get("distances", [[]])[0][i] if res.get("distances") else 0
                        rag_results.append({
                            "rule": doc[:400] + ("..." if len(doc) > 400 else ""),
                            "relevance": round(1 - dist, 3) if dist else 0.5,
                            "id": f"rag_{i}",
                            "source": meta.get("source_name", "web"),
                            "url": meta.get("source_url", ""),
                            "category": meta.get("category", ""),
                            "chunk_type": meta.get("chunk_type", ""),
                        })
            except Exception:
                pass  # collection doesn't exist yet — that's ok
    except Exception:
        pass  # chromadb not installed or DB not initialized

    # Merge: prefer built-in rules, supplement with RAG if we have room
    combined = builtin_results[:top_k]
    if len(combined) < top_k:
        for r in rag_results:
            if len(combined) >= top_k:
                break
            combined.append(r)
    return combined


def rag_stats() -> dict:
    """Return RAG collection stats from ChromaDB."""
    try:
        import chromadb
        db_path = Path(__file__).resolve().parent / "rl_models" / "chromadb"
        if not db_path.exists():
            return {"available": False, "reason": "ChromaDB not initialized"}
        client = chromadb.PersistentClient(path=str(db_path))
        stats = {"available": True, "collections": {}}
        for name in ["market_data_sources", "live_strategy_briefs",
                     "investor_wisdom", "news_archive", "pattern_library",
                     "trade_memory", "earnings_calls", "filings"]:
            try:
                col = client.get_collection(name)
                stats["collections"][name] = col.count()
            except Exception:
                stats["collections"][name] = 0
        return stats
    except Exception as e:
        return {"available": False, "reason": str(e)}


# =========================================================================== #
#  6. P&L CALCULATOR
# =========================================================================== =
def calculate_pnl(symbol: str, quantity: int, buy_price: float) -> dict:
    """Calculate unrealized P&L for a stock position."""
    import yfinance as yf
    sym = symbol if "." in symbol else f"{symbol}.NS"
    try:
        ticker = yf.Ticker(sym)
        hist = ticker.history(period="5d")
        if hist.empty:
            return {"error": f"Cannot fetch price for {sym}"}
        current = float(hist["Close"].iloc[-1])
    except Exception as e:
        return {"error": str(e)}

    invested = quantity * buy_price
    current_value = quantity * current
    pnl = current_value - invested
    pnl_pct = (pnl / invested * 100) if invested > 0 else 0

    return {
        "symbol": sym,
        "current_price": round(current, 2),
        "buy_price": buy_price,
        "quantity": quantity,
        "invested": round(invested, 2),
        "current_value": round(current_value, 2),
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
    }


# =========================================================================== #
#  STATS
# =========================================================================== #
def get_stats() -> dict:
    """Return brain stats."""
    return {
        "total_stocks": sum(len(v) for v in STOCKS.values()),
        "large_cap": len(STOCKS["large"]),
        "mid_cap": len(STOCKS["mid"]),
        "small_cap": len(STOCKS["small"]),
        "knowledge_rules": len(RULES),
        "sectors": len(SECTORS),
        "rag": rag_stats(),
    }


# =========================================================================== #
#  PATTERN DETECTION — integrated into every stock analysis
# =========================================================================== #
def detect_chart_patterns(df) -> dict:
    """Detect chart patterns on the latest bars. Returns bullish/bearish patterns found."""
    patterns = {"bullish": [], "bearish": []}
    if len(df) < 30:
        return patterns

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    open_ = df["Open"]
    volume = df["Volume"]
    i = len(df) - 1

    # 1. Bull Flag
    if i >= 23:
        rally = (close.iloc[i-3] / close.iloc[i-20] - 1) * 100
        if rally > 10:
            consol = (high.iloc[i-3:i].max() - low.iloc[i-3:i].min()) / close.iloc[i-3] * 100
            if consol < 4:
                patterns["bullish"].append({"pattern": "Bull Flag", "strength": 8, "desc": "10%+ rally + tight consolidation"})

    # 2. Volume Accumulation (3+ days rising vol + rising price)
    avg_vol = volume.iloc[i-20:i].mean()
    vol_3d = volume.iloc[i-3:i].values
    price_3d = close.iloc[i-3:i].values
    if all(v > avg_vol * 1.2 for v in vol_3d) and price_3d[-1] > price_3d[0]:
        patterns["bullish"].append({"pattern": "Volume Accumulation", "strength": 9, "desc": "Smart money buying for 3+ days"})

    # 3. Support Bounce
    lo20 = low.iloc[i-20:i].min()
    if low.iloc[i] <= lo20 * 1.005 and close.iloc[i] > lo20:
        patterns["bullish"].append({"pattern": "Support Bounce", "strength": 6, "desc": f"Bounced off 20-day low ({lo20:.1f})"})

    # 4. Hammer
    body = abs(close.iloc[i] - open_.iloc[i])
    lower_wick = min(open_.iloc[i], close.iloc[i]) - low.iloc[i]
    upper_wick = high.iloc[i] - max(open_.iloc[i], close.iloc[i])
    if body > 0 and lower_wick >= 2 * body and upper_wick <= 0.3 * body:
        patterns["bullish"].append({"pattern": "Hammer", "strength": 5, "desc": "Rejection of lower prices"})

    # 5. Bullish Engulfing
    if i >= 1 and close.iloc[i-1] < open_.iloc[i-1] and close.iloc[i] > open_.iloc[i]:
        if open_.iloc[i] <= close.iloc[i-1] and close.iloc[i] >= open_.iloc[i-1]:
            patterns["bullish"].append({"pattern": "Bullish Engulfing", "strength": 8, "desc": "Large green engulfs prior red"})

    # 6. Volume Spike + Price Up
    vol_ratio = volume.iloc[i] / avg_vol if avg_vol > 0 else 1
    price_chg = (close.iloc[i] / close.iloc[i-1] - 1) * 100 if i >= 1 else 0
    if vol_ratio > 2.5 and price_chg > 2:
        patterns["bullish"].append({"pattern": "Volume Spike", "strength": 8, "desc": f"Volume {vol_ratio:.1f}x avg with +{price_chg:.1f}% move"})

    # 7. RSI Oversold
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = float((100 - (100 / (1 + rs))).iloc[i])
    if rsi < 35:
        patterns["bullish"].append({"pattern": "RSI Oversold", "strength": 6, "desc": f"RSI {rsi:.0f} — bounce candidate"})

    # 8. Ascending Triangle
    if i >= 20:
        highs = high.iloc[i-20:i].values
        lows = low.iloc[i-20:i].values
        if np.std(highs) / np.mean(highs) * 100 < 1.5 and (lows[-1] - lows[0]) / lows[0] * 100 > 3:
            patterns["bullish"].append({"pattern": "Ascending Triangle", "strength": 7, "desc": "Flat top + rising bottom"})

    # Bearish patterns
    # 9. Shooting Star
    if body > 0 and upper_wick >= 2 * body and lower_wick <= 0.3 * body:
        patterns["bearish"].append({"pattern": "Shooting Star", "strength": 5, "desc": "Rejection of higher prices"})

    # 10. Bearish Engulfing
    if i >= 1 and close.iloc[i-1] > open_.iloc[i-1] and close.iloc[i] < open_.iloc[i]:
        if open_.iloc[i] >= close.iloc[i-1] and close.iloc[i] <= open_.iloc[i-1]:
            patterns["bearish"].append({"pattern": "Bearish Engulfing", "strength": 7, "desc": "Large red engulfs prior green"})

    # 11. Distribution
    if vol_ratio > 1.5 and price_chg < -2:
        patterns["bearish"].append({"pattern": "Distribution", "strength": 7, "desc": f"High volume with -{abs(price_chg):.1f}% drop"})

    return patterns


def get_historical_pattern_stats(df) -> dict:
    """Check how past patterns performed on this stock."""
    if len(df) < 60:
        return {"total": 0, "wins": 0, "win_rate": 0, "avg_5d_return": 0, "examples": []}

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    results = []

    for i in range(50, len(df) - 20):
        # Breakout pattern
        hi20 = high.iloc[i-20:i].max()
        avg_vol = volume.iloc[i-20:i].mean()
        if close.iloc[i] > hi20 and volume.iloc[i] > avg_vol * 1.5:
            entry = close.iloc[i]
            fwd_5d = (close.iloc[i+5] / entry - 1) * 100 if i + 5 < len(df) else 0
            fwd_20d = (close.iloc[i+20] / entry - 1) * 100 if i + 20 < len(df) else 0
            results.append({"date": str(df.index[i].date()), "type": "Breakout", "fwd_5d": round(fwd_5d, 2), "fwd_20d": round(fwd_20d, 2), "win": fwd_5d > 0})

        # Support bounce
        lo20 = low.iloc[i-20:i].min()
        if low.iloc[i] <= lo20 * 1.005 and close.iloc[i] > lo20:
            entry = close.iloc[i]
            fwd_5d = (close.iloc[i+5] / entry - 1) * 100 if i + 5 < len(df) else 0
            fwd_20d = (close.iloc[i+20] / entry - 1) * 100 if i + 20 < len(df) else 0
            results.append({"date": str(df.index[i].date()), "type": "Support Bounce", "fwd_5d": round(fwd_5d, 2), "fwd_20d": round(fwd_20d, 2), "win": fwd_5d > 0})

    if not results:
        return {"total": 0, "wins": 0, "win_rate": 0, "avg_5d_return": 0, "examples": []}

    wins = sum(1 for r in results if r["win"])
    avg_5d = np.mean([r["fwd_5d"] for r in results])

    return {
        "total": len(results),
        "wins": wins,
        "win_rate": round(wins / len(results) * 100, 1),
        "avg_5d_return": round(avg_5d, 2),
        "avg_20d_return": round(np.mean([r["fwd_20d"] for r in results]), 2),
        "examples": results[-5:],
    }


if __name__ == "__main__":
    print(f"Brain Stats: {get_stats()}")
    print(f"\nSample knowledge search 'momentum breakout':")
    for r in search_knowledge("momentum breakout", 3):
        print(f"  [{r['relevance']:.2f}] {r['rule'][:100]}")
