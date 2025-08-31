import requests
import pandas as pd
import plotly.graph_objects as go
import base64
from datetime import datetime
import pytz
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = "jkwfung87"
REPO_NAME = "dotbot-charts"

def fetch_dot_data():
    url = "https://api.coingecko.com/api/v3/coins/polkadot/market_chart"
    params = {"vs_currency": "usd", "days": 2}
    try:
        res = requests.get(url, params=params)
        data = res.json()
        df = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df["timestamp"] = df["timestamp"].dt.tz_convert("Asia/Singapore")
        df["price"] = df["price"].astype(float)
        df["open"] = df["price"].shift(1)
        df["close"] = df["price"]
        df["high"] = df["price"].rolling(2).max()
        df["low"] = df["price"].rolling(2).min()
        df.dropna(inplace=True)
        return df[["timestamp", "open", "high", "low", "close"]]
    except Exception as e:
        print("❌ Error fetching DOT data:", e)
        return pd.DataFrame()

def generate_chart(df, filename="dot_chart.png"):
    df["label_time"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
    fig = go.Figure(data=[go.Candlestick(
        x=df["label_time"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        increasing_line_color="green",
        decreasing_line_color="red"
    )])
    fig.update_layout(
        title="DOT/USDT Candlestick Chart (SGT)",
        xaxis_title="Time (SGT)",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=600,
        xaxis=dict(type="category", tickangle=-45, nticks=10)
    )
    fig.write_image(filename)
    print("✅ Chart saved:", filename)
    return filename

def upload_chart(filename, repo_path="charts/dot_chart.png"):
    with open(filename, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf-8")
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{repo_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    get_res = requests.get(url, headers=headers)
    sha = get_res.json().get("sha") if get_res.status_code == 200 else None
    payload = {
        "message": f"Upload chart {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "content": content,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
    res = requests.put(url, headers=headers, json=payload)
    if res.status_code in [200, 201]:
        print("✅ Chart uploaded to GitHub.")
    else:
        print("❌ Upload failed:", res.json())

df = fetch_dot_data()
if not df.empty:
    filename = generate_chart(df)
    upload_chart(filename)
else:
    print("📉 No data fetched. Chart generation skipped.")
