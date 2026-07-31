import subprocess
import sys
import pkg_resources
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import time
from datetime import datetime

st.set_page_config(page_title="FX99 Live Alerts", layout="wide")

# --- CONFIG (இங்கே மட்டும் மாற்றவும்) ---
WHATSAPP_NUMBER = "+918098284754"   # உங்க எண்ணை +91 உட்பட எழுதவும்
WHATSAPP_API_KEY = "zJ9HmywRYGtS"   # உங்க API Key-ஐ எழுதவும்

ASSETS = {"US100": "NQ=F", "XAUUSD": "GC=F", "US30": "YM=F", "WTI": "CL=F", "SP500": "ES=F"}

if "alert_history" not in st.session_state:
    st.session_state.alert_history = []

def send_whatsapp(msg):
    url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_NUMBER}&text={msg}&apikey={WHATSAPP_API_KEY}"
    try:
        requests.get(url)
    except:
        pass

def analyze_asset(ticker):
    df = yf.download(ticker, period="1d", interval="5m", progress=False)
    if df.empty:
        return None
    last = df.iloc[-1]
    price = last['Close']
    high20 = df['High'].rolling(20).max().iloc[-2]
    low20 = df['Low'].rolling(20).min().iloc[-2]
    sma15 = df['Close'].rolling(15).mean().iloc[-1]
    sma30 = df['Close'].rolling(30).mean().iloc[-1]
    sweep = price > high20 or price < low20
    mss = price > df['High'].rolling(10).max().iloc[-2] or price < df['Low'].rolling(10).min().iloc[-2]
    cisd = (price > last['Open'] and df['Close'].iloc[-2] > df['Open'].iloc[-2]) or (price < last['Open'] and df['Close'].iloc[-2] < df['Open'].iloc[-2])
    score = 0
    if sma15 > sma30: score += 2
    if sweep: score += 2
    if mss: score += 3
    if cisd: score += 2
    if (df['High']-df['Low']).iloc[-1] > (df['High']-df['Low']).rolling(10).mean().iloc[-1]*1.5: score += 2
    score = min(score, 12)
    entry = round(price, 2) if score >= 10 else None
    sl = round(price - (price*0.005), 2) if score >= 10 else None
    tp = round(price + ((price-sl)*3), 2) if score >= 10 else None
    return {"price": round(price,2), "score": score, "entry": entry, "sl": sl, "tp": tp}

st.title("📲 FX99 LIVE SCANNER")
asset = st.selectbox("Select Asset", list(ASSETS.keys()))
data = analyze_asset(ASSETS[asset])
if data:
    st.metric(asset, f"${data['price']}")
    st.progress(data['score']/12)
    st.write(f"**Score:** {data['score']}/12")
    if data['score'] >= 10:
        st.success(f"✅ READY! Entry: ${data['entry']} | SL: ${data['sl']} | TP: ${data['tp']}")
        if f"alert_{asset}" not in st.session_state:
            send_whatsapp(f"🚀 FX99 ALERT – {asset}\nScore: {data['score']}/12\nEntry: ${data['entry']}\nSL: ${data['sl']}\nTP: ${data['tp']}")
            st.session_state[f"alert_{asset}"] = True
            st.success("✅ Alert sent to WhatsApp!")
    else:
        st.info(f"⏳ Waiting. Score: {data['score']}/12")
time.sleep(15)
st.rerun()