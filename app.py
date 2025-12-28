#!/usr/bin/env python
# coding: utf-8

# In[1]:

import requests
import pandas as pd
import streamlit as st
import requests
import plotly.express as px
import warnings

# ----------------- 1. Load_data -----------------
import os
import time
# put near top of app.py (replace your current file-read logic)
import os, time, requests
from datetime import datetime, timezone

FILE_PATH = os.path.join("data", "market_data_master.csv")
GITHUB_OWNER = "darxonxz"   # <<<< set this
GITHUB_REPO = "mandiapp"              # <<<< set this
GITHUB_PATH = "data/market_data_master.csv"

def get_github_latest_commit_date(owner, repo, path):
    """Return datetime (UTC) of latest commit that touched `path`, or None."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"path": path, "per_page": 1}
    try:
        r = requests.get(api_url, params=params, timeout=20)
        r.raise_for_status()
        commits = r.json()
        if commits:
            date_str = commits[0]['commit']['committer']['date']  # ISO 8601
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception as e:
        print("GitHub commit check failed:", e)
    return None

def download_raw_github(owner, repo, path, dest):
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{path}"
    try:
        r = requests.get(raw_url, timeout=30)
        r.raise_for_status()
        open(dest, "wb").write(r.content)
        return True
    except Exception as e:
        print("Failed to download raw file:", e)
        return False

# ensure data dir exists
os.makedirs(os.path.dirname(FILE_PATH), exist_ok=True)

# check local mtime
local_mtime = None
if os.path.exists(FILE_PATH) and os.path.getsize(FILE_PATH) > 0:
    local_mtime = datetime.fromtimestamp(os.path.getmtime(FILE_PATH), tz=timezone.utc)

# check remote commit
remote_commit_dt = get_github_latest_commit_date(GITHUB_OWNER, GITHUB_REPO, GITHUB_PATH)

# if remote is newer (or local missing), download
if remote_commit_dt and (local_mtime is None or remote_commit_dt > local_mtime):
    print("Remote CSV newer -> downloading from GitHub")
    ok = download_raw_github(GITHUB_OWNER, GITHUB_REPO, GITHUB_PATH, FILE_PATH)
    if ok:
        # update file timestamp to reflect remote commit (optional)
        os.utime(FILE_PATH, (time.time(), remote_commit_dt.timestamp()))

# final read (fall back to local if download failed)
import pandas as pd
if os.path.exists(FILE_PATH) and os.path.getsize(FILE_PATH) > 0:
    df = pd.read_csv(FILE_PATH)
else:
    # as a fallback try one-time raw fetch with cache-buster
    raw = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main/{GITHUB_PATH}?v={int(time.time())}"
    df = pd.read_csv(raw)

# In[4]:

df["arrival_date"] = pd.to_datetime(df["arrival_date"], errors="coerce")

df["year"] = df["arrival_date"].dt.year
df["month"] = df["arrival_date"].dt.month   # optional but useful

state = df.groupby('state').sum('modal_price')

# ----------------- 2. Sidebar Filters -----------------
st.set_page_config(page_title="Indian Mandi Price Dashboard", layout="wide", initial_sidebar_state = 'expanded')

st.sidebar.header("Filters")

states = st.sidebar.multiselect("Select States", df['state'].unique(), default=df['state'].unique())
districts = st.sidebar.multiselect("Select Districts", df['district'].unique(), default=df['district'].unique())
commodities = st.sidebar.multiselect("Select Commodities", df['commodity'].unique(), default=df['commodity'].unique())
varieties = st.sidebar.multiselect("Select Varieties", df['variety'].unique(), default=df['variety'].unique())
grades = st.sidebar.multiselect("Select Grades", df['grade'].unique(), default=df['grade'].unique())
year = st.sidebar.multiselect("Year", sorted(df["year"].dropna().unique()), default=sorted(df["year"].dropna().unique()))
filtered_df = df[
    (df['state'].isin(states)) &
    (df['district'].isin(districts)) &
    (df['commodity'].isin(commodities)) &
    (df['variety'].isin(varieties)) &
    (df['grade'].isin(grades)) &
    (df["year"].isin(year))
].sort_values(by = ["state", "commodity", "arrival_date"], ascending = [True, True, True])

# ----------------- 3. Dashboard Title -----------------
st.title("📊 Indian APMC Market Prices Dashboard")
st.markdown("Interactive dashboard with all metrics, aggregations, and visualizations.")

# ----------------- 4. Display Filtered Table -----------------
st.subheader("Filtered Market Data in ₹")
st.dataframe(filtered_df)

# ----------------- 5. Price Metrics -----------------
st.subheader("Price Metrics / Calculations in ₹")

metrics_df = pd.DataFrame({
    "Metric": ["Min Price", "Max Price", "Modal Price Mean", "Modal Price Median",
               "Modal Price Std Dev", "Number of Records", "Price Range (Max-Min)"],
    "Value": [
        filtered_df['min_price'].min(),
        filtered_df['max_price'].max(),
        round(filtered_df['modal_price'].mean(),2),
        round(filtered_df['modal_price'].median(),2),
        round(filtered_df['modal_price'].std(),2),
        filtered_df.shape[0],
        filtered_df['max_price'].max() - filtered_df['min_price'].min()
    ]
})

st.table(metrics_df)

# -----------------------------
# KPI Metrics
# -----------------------------

st.subheader("📌 Key Metrics in ₹")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Records", len(filtered_df))
col2.metric("Avg Min Price", round(filtered_df["min_price"].mean(), 2))
col3.metric("Avg Max Price", round(filtered_df["max_price"].mean(), 2))
col4.metric("Avg Modal Price", round(filtered_df["modal_price"].mean(), 2))

# -----------------------------
# YEAR-WISE REPORT
# -----------------------------

st.subheader("📅 Year-wise Price Report ₹")

yearly_report = (
    filtered_df
    .groupby("year")[["min_price", "max_price", "modal_price"]]
    .mean()
    .reset_index()
)

fig_year = px.line(
    yearly_report,
    x="year",
    y=["min_price", "max_price", "modal_price"],
    markers=True,
    labels={
        "value": "Average Price",
        "year": "Year",
        "variable": "Price Type"
    },
    title="Year-wise Average Price Trend ₹"
)

st.plotly_chart(fig_year, use_container_width=True)

# ----------------- 6. Aggregations -----------------
st.subheader("Aggregated Data by State & Commodity ₹")
agg_df = filtered_df.groupby(['state','commodity']).agg(
    Min_Price=('min_price','min'),
    Max_Price=('max_price','max'),
    Avg_Modal=('modal_price','mean'),
    Count=('modal_price','count')
).reset_index()
st.dataframe(agg_df)

# ----------------- 7. Visualizations -----------------
st.subheader("Visualizations")

# 7a: Commodity-wise Modal Prices Bar Chart

fig1 = px.bar(filtered_df, x="modal_price", y="commodity", color="state", text="modal_price",
              labels={"modal_price":"Modal Price", "commodity":"Commodity", "state":"State"},
              title="Commodity-wise Modal Prices by State")

fig1.update_layout(xaxis_title="modal_price", yaxis_title="commodity")
st.plotly_chart(fig1)

# 7b: State-wise Average Modal Price Line Chart
state_avg = filtered_df.groupby("state")["modal_price"].mean().reset_index()
fig2 = px.line(state_avg, x="state", y="modal_price", markers=True,
               labels={"modal_price":"Average Modal Price", "state":"State"},
               title="State-wise Average Modal Price")
st.plotly_chart(fig2)

# 7c: Box Plot for Price Distribution
st.subheader("Price Distribution by Commodity ₹")
fig3 = px.box(filtered_df, x="modal_price", y="commodity", color="state",
              labels={"modal_price":"Modal Price", "commodity":"Commodity", "state":"State"},
              title="Price Distribution by Commodity")
st.plotly_chart(fig3)

# 7d: Scatter Plot Min vs Max Prices
st.subheader("Min vs Max Prices Scatter Plot ₹")
fig4 = px.scatter(filtered_df, x="min_price", y="max_price", color="commodity", size="modal_price",
                  hover_data=["state","district","market"], labels={"min_price":"Min Price","max_price":"Max Price"},
                  title="Scatter of Min vs Max Prices by Commodity")
st.plotly_chart(fig4)

# 7e: Heat_Map of Commodities Proportion
st.subheader("🔥 Commodity vs State Heatmap (Record Count)")

heatmap_df = (
    filtered_df
    .groupby(["state", "commodity"])
    .size()
    .reset_index(name="count")
)

fig = px.density_heatmap(
    heatmap_df,
    x="commodity",
    y="state",
    z="count",
    color_continuous_scale="Turbo",
    title="Commodity Distribution Across States"
)

st.plotly_chart(fig, use_container_width=True)










