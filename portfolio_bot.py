import yfinance as yf
import requests
from datetime import datetime
import os
import matplotlib.pyplot as plt

# ==============================
# CONFIG
# ==============================

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ==============================
# DATI REALI TUOI
# ==============================

VALORE_TOTALE = 47339
INVESTITO_TOTALE = 34500
ANNI = 3.4

# ==============================
# PORTFOLIO
# ==============================

PORTFOLIO = {
    "ACWI": "MSCI ACWI",
    "GLD": "Gold",
    "EEM": "Emerging Markets",
    "ICLN": "Clean Energy",
    "IWM": "Small Cap",
    "SLV": "Silver",
    "XLK": "Tech",
    "REET": "Real Estate",
    "BTC-USD": "Bitcoin"
}

# ==============================
# FUNZIONI
# ==============================

def get_change(ticker):
    try:
        data = yf.Ticker(ticker).history(period="2d")
        close = data["Close"].dropna()

        today = float(close.iloc[-1])
        prev = float(close.iloc[-2])

        return (today - prev) / prev
    except:
        return 0


def calc_cagr():
    return (VALORE_TOTALE / INVESTITO_TOTALE) ** (1 / ANNI) - 1


def emoji(v):
    if v > 0:
        return "🟢"
    elif v < 0:
        return "🔴"
    return "⚪"


def build_data():
    changes = {}

    for ticker in PORTFOLIO:
        change = get_change(ticker)
        changes[ticker] = change

    return changes


def calc_daily_total(changes):
    avg = sum(changes.values()) / len(changes)
    euro = VALORE_TOTALE * avg
    return avg, euro


def best_worst(changes):
    best = max(changes, key=changes.get)
    worst = min(changes, key=changes.get)

    return best, worst


def create_chart(changes):
    names = [PORTFOLIO[t] for t in changes]
    values = [v * 100 for v in changes.values()]

    plt.figure()
    plt.bar(names, values)
    plt.xticks(rotation=45)
    plt.ylabel("Performance %")
    plt.title("Daily Performance ETF")

    plt.tight_layout()
    plt.savefig("chart.png")
    plt.close()


def format_msg(changes):
    today = datetime.now().strftime("%d/%m/%Y")

    pnl = VALORE_TOTALE - INVESTITO_TOTALE
    pnl_pct = pnl / INVESTITO_TOTALE
    cagr = calc_cagr()

    daily_pct, daily_euro = calc_daily_total(changes)

    best, worst = best_worst(changes)

    msg = f"📊 *Portfolio Update* ({today})\n\n"

    msg += f"💼 *Valore totale*\n{VALORE_TOTALE:,.0f} €\n\n"

    msg += f"📈 *Performance totale*\n"
    msg += f"{emoji(pnl)} {pnl:+,.0f} € ({pnl_pct:+.2%})\n\n"

    msg += f"📉 *CAGR*\n{cagr:+.2%}\n\n"

    msg += f"📅 *Oggi*\n"
    msg += f"{emoji(daily_pct)} {daily_euro:+,.0f} € ({daily_pct:+.2%})\n\n"

    msg += f"🏆 *Top / Flop*\n"
    msg += f"🟢 {PORTFOLIO[best]} ({changes[best]:+.2%})\n"
    msg += f"🔴 {PORTFOLIO[worst]} ({changes[worst]:+.2%})\n\n"

    if daily_pct < -0.02:
        msg += "🚨 *ALERT*: perdita giornaliera oltre -2%\n\n"

    msg += "📦 *Dettaglio Asset*\n"

    for t, name in PORTFOLIO.items():
        val = changes[t]
        msg += f"{emoji(val)} {name}: {val:+.2%}\n"

    return msg


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    })


def send_chart():
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

    with open("chart.png", "rb") as img:
        requests.post(url, data={"chat_id": CHAT_ID}, files={"photo": img})


def run():
    changes = build_data()

    create_chart(changes)

    msg = format_msg(changes)

    print(msg)

    send_telegram(msg)
    send_chart()


# ==============================
# RUN
# ==============================

if __name__ == "__main__":
    run()
