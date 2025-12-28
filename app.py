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
st.set_page_config(
    page_title="Indian Mandi Price Dashboard",
    layout="wide"
)

st.cache_data.clear()


@st.cache_data(ttl=300)  # refresh every 5 minutes
def load_data():
    url = "https://raw.githubusercontent.com/darxonxz/mandiapp/main/data/market_data_master.csv"
    return pd.read_csv(url)

df = load_data()



# ----------------- 2. Sidebar Filters -----------------
st.set_page_config(page_title="Indian Mandi Price Dashboard", layout="wide", initial_sidebar_state = 'expanded')

st.caption(f"Last loaded rows: {len(df)}")
st.caption(f"Latest arrival_date: {df['arrival_date'].max()}")

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

