import pandas as pd
import requests
import os

url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

API_KEY = "YOUR_API_KEY"
LIMIT = 10000
offset = 0
all_records = []

while True:
    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": LIMIT,
        "offset": offset
    }

    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json().get("records", [])

    if not data:
        break

    all_records.extend(data)
    offset += LIMIT

print(f"Fetched records: {len(all_records)}")

new_df = pd.DataFrame(all_records)
new_df.columns = new_df.columns.str.strip().str.lower()
new_df["arrival_date"] = pd.to_datetime(new_df["arrival_date"], errors="coerce")

DATA_FILE = "data/market_data_master.csv"
os.makedirs("data", exist_ok=True)

if os.path.exists(DATA_FILE):
    old_df = pd.read_csv(DATA_FILE)
    df = pd.concat([old_df, new_df], ignore_index=True)
else:
    df = new_df

df.drop_duplicates(
    subset=["state", "district", "market", "commodity", "variety", "arrival_date"],
    keep="last",
    inplace=True
)

df.to_csv(DATA_FILE, index=False)

print("Final rows:", len(df))
