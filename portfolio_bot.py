import yfinance as yf
import requests
from datetime import datetime
import os

# ==============================
# CONFIG (GitHub Secrets)
# ==============================

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ==============================
# PORTFOLIO ORIGINALE (EUROPA) ❌ NON AFFIDABILE SU GITHUB
# ==============================
# PORTFOLIO = {
#     "IE00B6R52259": ("SSAC.L", "MSCI ACWI"),
#     "IE00B579F325": ("SGLD.L", "Gold"),
#     "IE00BKM4GZ66": ("EIMI.L", "Emerging Markets"),
#     "IE000U58J0M1": ("INRA.AS", "Clean Energy"),
#     "IE00BF4RFH31": ("WSML.L", "Small Cap"),
#     "IE00B4NCWG09": ("SSLN.L", "Silver"),
#     "IE00B3WJKG14": ("IITU.L", "Tech"),
#     "IE00BH4GR342": ("GLRA.L", "Real Estate")
# }

# ==============================
# PORTFOLIO ATTIVO ✅ (US ETF PROXY - STABILI)
# ==============================

PORTFOLIO = {
    "IE00B6R52259": ("ACWI", "MSCI ACWI"),
    "IE00B579F325": ("GLD", "Gold"),
    "IE00BKM4GZ66": ("EEM", "Emerging Markets"),
    "IE000U58J0M1": ("ICLN", "Clean Energy"),
    "IE00BF4RFH31": ("IWM", "Small Cap"),
    "IE00B4NCWG09": ("SLV", "Silver"),
    "IE00B3WJKG14": ("XLK", "Tech"),
    "IE00BH4GR342": ("REET", "Real Estate")
}

# ==============================
# FUNZIONI
# ==============================

def get_data(ticker):      
    try:
            ticker_obj = yf.Ticker(ticker)
            data = ticker_obj.history(period="1y")
    
            if data is None or data.empty:
                return None
    
            return data
    
        except Exception as e:
            print(f"Errore su {ticker}: {e}")
            return None



def calc_perf(data):
    if data is None or data.empty:
        return 0, 0, 0, 0, 0

    close = data["Close"]

    try:
        latest = float(close.iloc[-1])

        daily = (latest - float(close.iloc[-2])) / float(close.iloc[-2]) if len(close) > 1 else 0
        weekly = (latest - float(close.iloc[-6])) / float(close.iloc[-6]) if len(close) > 6 else 0
        monthly = (latest - float(close.iloc[-22])) / float(close.iloc[-22]) if len(close) > 22 else 0
        yearly = (latest - float(close.iloc[0])) / float(close.iloc[0])

    except:
        return 0, 0, 0, 0, 0

    return latest, daily, weekly, monthly, yearly


def emoji(value):
    if value > 0:
        return "🟢"
    elif value < 0:
        return "🔴"
    return "⚪"


def format_msg(results):
    today = datetime.now().strftime("%d/%m/%Y")

    msg = f"📊 Portfolio Update ({today})\n\n"

    for isin, (name, price, d, w, m, y) in results.items():

        msg += f"📌 {name}\n"
        msg += f"{isin}\n"

        if price == 0:
            msg += "⚠️ Dati non disponibili\n\n"
            continue

        msg += f"💰 Prezzo: {price:.2f}\n"
        msg += f"{emoji(d)} Giorno: {d:+.2%}\n"
        msg += f"{emoji(w)} Settimana: {w:+.2%}\n"
        msg += f"{emoji(m)} Mese: {m:+.2%}\n"
        msg += f"{emoji(y)} Anno: {y:+.2%}\n\n"

    return msg


def send_telegram(msg):
    if not TOKEN or not CHAT_ID:
        print("❌ TOKEN o CHAT_ID mancanti")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg
        })
    except Exception as e:
        print("Errore invio Telegram:", e)


def run():
    results = {}

    for isin, (ticker, name) in PORTFOLIO.items():
        data = get_data(ticker)
        results[isin] = (name, *calc_perf(data))

    msg = format_msg(results)
    send_telegram(msg)


# ==============================
# AVVIO
# ==============================

if __name__ == "__main__":
    run()
