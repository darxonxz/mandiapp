# ---------- robust GitHub-fetch + local-sync (replace previous load logic) ----------
import os, time, hashlib, requests
from datetime import datetime, timezone
import pandas as pd
import streamlit as st

GITHUB_OWNER = "darxonxz"          # <-- set your owner/org
GITHUB_REPO  = "mandiapp"          # <-- set your repo name exactly
GITHUB_PATH  = "data/market_data_master.csv"
RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/{GITHUB_PATH}"
FILE_PATH = os.path.join("data", "market_data_master.csv")
os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)

def sha256_bytes(b: bytes):
    import hashlib
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def download_raw_if_changed(raw_url, local_path, timeout=30):
    """Download raw_url and write to local_path only if content differs.
       Returns tuple (downloaded:bool, reason:str)."""
    try:
        r = requests.get(raw_url, timeout=timeout)
    except Exception as e:
        return False, f"download failed: {e}"

    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"

    remote_bytes = r.content
    remote_hash = sha256_bytes(remote_bytes)

    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        with open(local_path, "rb") as f:
            local_bytes = f.read()
        local_hash = sha256_bytes(local_bytes)
        if local_hash == remote_hash:
            return False, "no-change"
    # write new file
    with open(local_path, "wb") as f:
        f.write(remote_bytes)
    return True, "updated"

# Try to download and update local copy if it changed
downloaded, reason = download_raw_if_changed(RAW_URL, FILE_PATH)
st.write(f"GitHub raw fetch: {RAW_URL}")
st.write(f"Download result: {downloaded} ({reason})")

# Show local file mtime and size for debugging
if os.path.exists(FILE_PATH):
    mtime = datetime.fromtimestamp(os.path.getmtime(FILE_PATH), tz=timezone.utc)
    st.caption(f"Local CSV path: {FILE_PATH}  |  size: {os.path.getsize(FILE_PATH)} bytes  |  mtime (UTC): {mtime}")
else:
    st.caption(f"Local CSV not found at {FILE_PATH}")

# Final load into dataframe (use pandas, fallback to raw URL if local not present)
try:
    if os.path.exists(FILE_PATH) and os.path.getsize(FILE_PATH) > 0:
        df = pd.read_csv(FILE_PATH)
    else:
        # fallback to reading raw url directly (cache-busted)
        df = pd.read_csv(RAW_URL + f"?v={int(time.time())}")
except Exception as e:
    st.error(f"Failed to load CSV: {e}")
    df = pd.DataFrame()  # empty df to keep app alive

# normalize column names now (you already do this later)
df.columns = df.columns.str.strip().str.lower()
# ensure arrival_date column exists and is parsed
if "arrival_date" in df.columns:
    df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")
else:
    st.warning("arrival_date column missing in CSV")
