import yfinance as yf
import requests
from datetime import datetime, timedelta
import os
import matplotlib.pyplot as plt

# ==============================
# CONFIG
# ==============================

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ==============================
# DATI REALI ATTUALI
# ==============================

PORTFOLIO_VALUES = {
    "ACWI": 23337,
    "GLD": 2257,
    "EEM": 3795,
    "ICLN": 4916,
    "IWM": 2924,
    "SLV": 2853,
    "XLK": 4037,
    "REET": 2355,
    "BTC-USD": 865
}

INVESTITO_TOTALE = 34500
PAC_MENSILE = 750
CAGR = 0.097  # calcolato prima

# ==============================
# NOMI
# ==============================

NAMES = {
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

def get_perf(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1y")
        close = data["Close"].dropna()

        last = float(close.iloc[-2])

        return {
            "d": (last - float(close.iloc[-3])) / float(close.iloc[-3]),
            "w": (last - float(close.iloc[-7])) / float(close.iloc[-7]),
            "m": (last - float(close.iloc[-22])) / float(close.iloc[-22]),
            "y": (last - float(close.iloc[0])) / float(close.iloc[0])
        }
    except:
        return {"d":0,"w":0,"m":0,"y":0}

# ==============================

def build_data():
    results = {}

    for t in PORTFOLIO_VALUES:
        results[t] = get_perf(t)

    return results

# ==============================

def total_value():
    return sum(PORTFOLIO_VALUES.values())

# ==============================

def dynamic_weights():
    total = total_value()
    return {t: PORTFOLIO_VALUES[t] / total for t in PORTFOLIO_VALUES}

# ==============================

def weighted(results, key):
    weights = dynamic_weights()

    return sum(results[t][key] * weights[t] for t in results)

# ==============================

def simulate_future(months):
    value = total_value()

    for _ in range(months):
        value = value * (1 + CAGR/12)
        value += PAC_MENSILE  # PAC su ACWI

    return value

# ==============================

def emoji(v):
    return "🟢" if v > 0 else "🔴" if v < 0 else "⚪"

# ==============================

def best_worst(results):
    daily = {t: results[t]["d"] for t in results}
    return max(daily, key=daily.get), min(daily, key=daily.get)

# ==============================

def create_chart(results):
    names = [NAMES[t] for t in results]
    values = [results[t]["d"]*100 for t in results]

    plt.figure()
    plt.bar(names, values)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("chart.png")
    plt.close()

# ==============================


def format_msg(results):
    val = total_value()
    pnl = val - INVESTITO_TOTALE
    pnl_pct = pnl / INVESTITO_TOTALE

    daily = weighted(results, "d")
    weekly = weighted(results, "w")
    monthly = weighted(results, "m")
    yearly = weighted(results, "y")

    best, worst = best_worst(results)

    fut1 = simulate_future(12)
    fut5 = simulate_future(60)

    date = (datetime.now()-timedelta(days=1)).strftime("%d/%m/%Y")

    msg = f"📊 *Portfolio Update* ({date})\n\n"

    msg += f"💼 {val:,.0f} €\n\n"

    msg += f"📈 {pnl:+,.0f} € ({pnl_pct:+.2%})\n\n"

    # -----------------------------
    # PERFORMANCE PORTAFOGLIO
    # -----------------------------
    msg += "📅 *Performance Portafoglio*\n"
    msg += f"{emoji(daily)} Giorno: {daily:+.2%}\n"
    msg += f"{emoji(weekly)} Settimana: {weekly:+.2%}\n"
    msg += f"{emoji(monthly)} Mese: {monthly:+.2%}\n"
    msg += f"{emoji(yearly)} Anno: {yearly:+.2%}\n\n"

    # -----------------------------
    # TOP / FLOP
    # -----------------------------
    msg += f"🏆 Top: {NAMES[best]} {results[best]['d']:+.2%}\n"
    msg += f"🔻 Worst: {NAMES[worst]} {results[worst]['d']:+.2%}\n\n"

    # -----------------------------
    # PROIEZIONI
    # -----------------------------
    msg += "🔮 *Proiezioni*\n"
    msg += f"12 mesi: {fut1:,.0f} €\n"
    msg += f"5 anni: {fut5:,.0f} €\n\n"

    # -----------------------------
    # DETTAGLIO ASSET + CONTRIBUTO 🔥
    # -----------------------------
    msg += "📦 *Asset*\n\n"

    total_contribution = 0

    for t in results:
        data = results[t]

        value = PORTFOLIO_VALUES[t]
        weight = value / val

        contrib_pct = weight * data["d"]
        contrib_euro = contrib_pct * val

        total_contribution += contrib_euro

        msg += f"*{NAMES[t]}*\n"
        msg += f"{emoji(data['d'])} D: {data['d']:+.2%} → {contrib_euro:+,.0f} €\n"
        msg += f"{emoji(data['w'])} W: {data['w']:+.2%}\n"
        msg += f"{emoji(data['m'])} M: {data['m']:+.2%}\n"
        msg += f"{emoji(data['y'])} Y: {data['y']:+.2%}\n\n"

    # -----------------------------
    # CONTROLLO COERENZA
    # -----------------------------
    msg += f"💰 Totale impatto: {total_contribution:+,.0f} €\n"

    return msg


# ==============================

def send_telegram(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    )

def send_chart():
    with open("chart.png","rb") as img:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
            data={"chat_id": CHAT_ID},
            files={"photo": img}
        )

# ==============================

def run():
    results = build_data()

    create_chart(results)

    msg = format_msg(results)

    print(msg)

    send_telegram(msg)
    send_chart()

# ==============================

if __name__ == "__main__":
    run()
