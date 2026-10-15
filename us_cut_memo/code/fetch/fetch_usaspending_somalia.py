import requests, json, sys, pandas as pd
out=[]
for codes in [["02","03","04","05"],["A","B","C","D"]]:
  for p in range(1,40):
    r=requests.post("https://api.usaspending.gov/api/v2/search/spending_by_award/",json={"filters":{"place_of_performance_locations":[{"country":"SOM"}],"award_type_codes":codes,"time_period":[{"start_date":"2021-10-01","end_date":"2025-09-30"}]},"fields":["Award ID","Recipient Name","Award Amount","Total Outlays","Awarding Agency","Start Date","End Date","Description"],"limit":100,"page":p,"sort":"Award Amount","order":"desc"},timeout=60).json()
    out+=r["results"]
    if not r["page_metadata"]["hasNext"]: break
d=pd.DataFrame(out); d.to_csv(sys.argv[1],index=False); print(len(d))
