import pandas as pd
import requests
import os
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    warnings.warn("This is hidden")

url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070" # mandi api

params = {
    "api-key": "579b464db66ec23bdd000001683b398a0bdd40066aefc6ace98749c7",
    "format": "json",
    "limit": 10000
}

response = requests.get(url, params)

# Check status
print(response.status_code)

# Convert JSON → Python object
data = response.json()

# first 5 records
new_df = pd.DataFrame(data["records"]).reset_index()
# normalize column names
new_df.columns = new_df.columns.str.strip().str.lower()

new_df.head(2)
new_df["arrival_date"] = pd.to_datetime(new_df["arrival_date"], errors="coerce")

# In[2]:


new_df.tail(2)


DATA_FILE = "data/market_data_master.csv"
os.makedirs("data", exist_ok=True)

# In[3]:

# load old data
if os.path.exists(DATA_FILE):
    old_df = pd.read_csv(DATA_FILE)
    final_df = pd.concat([old_df, new_df], ignore_index=True)
    
else:
    final_df = new_df

final_df.drop_duplicates(
    subset=[
        "state",
        "district",
        "market",
        "commodity",
        "variety",
        "arrival_date"
    ],
    keep="last",
    inplace=True
)

final_df.to_csv(DATA_FILE, index=False)


