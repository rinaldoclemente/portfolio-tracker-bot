import yfinance as yf
import requests
from datetime import datetime
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PORTFOLIO = {
    "IE00B6R52259": ("ISAC.MI", "MSCI ACWI"),
    "IE00B579F325": ("SGLD.MI", "Gold"),
    "IE00BKM4GZ66": ("EIMI.MI", "Emerging Markets"),
    "IE000U58J0M1": ("Q8Y0.DE", "Clean Energy"),
    "IE00BF4RFH31": ("IUSN.MI", "Small Cap"),
    "IE00B4NCWG09": ("SSLN.MI", "Silver"),
    "IE00B3WJKG14": ("QDVE.MI", "Tech"),
    "IE00BH4GR342": ("SPY2.DE", "Real Estate")
}


def get_data(ticker):
    return yf.download(ticker, period="1y", interval="1d", progress=False)


def calc_perf(data):
    close = data["Close"]
    latest = close.iloc[-1]

    daily = (latest - close.iloc[-2]) / close.iloc[-2] if len(close) > 1 else 0
    weekly = (latest - close.iloc[-6]) / close.iloc[-6] if len(close) > 6 else 0
    monthly = (latest - close.iloc[-22]) / close.iloc[-22] if len(close) > 22 else 0
    yearly = (latest - close.iloc[0]) / close.iloc[0]

    return latest, daily, weekly, monthly, yearly


def emoji(v):
    return "🟢" if v > 0 else "🔴" if v < 0 else "⚪"


def format_msg(results):
    today = datetime.now().strftime("%d/%m/%Y")

    msg = f"📊 Portfolio Update ({today})\n\n"

    for isin, (name, price, d, w, m, y) in results.items():
        msg += f"{name}\n"
        msg += f"{isin}\n"
        msg += f"Prezzo: {price:.2f}\n"
        msg += f"{emoji(d)} Giorno: {d:+.2%}\n"
        msg += f"{emoji(w)} Settimana: {w:+.2%}\n"
        msg += f"{emoji(m)} Mese: {m:+.2%}\n"
        msg += f"{emoji(y)} Anno: {y:+.2%}\n\n"

    return msg


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })


def run():
    results = {}

    for isin, (ticker, name) in PORTFOLIO.items():
        try:
            data = get_data(ticker)
            price, d, w, m, y = calc_perf(data)
            results[isin] = (name, price, d, w, m, y)
        except:
            results[isin] = (name, 0, 0, 0, 0, 0)

    msg = format_msg(results)
    send_telegram(msg)


if __name__ == "__main__":
    run()
