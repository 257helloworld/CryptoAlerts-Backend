import json
import datetime as dt
import requests


def getCurrencies():
    try:
        f = open("data/data.json", "r+")
        data = json.load(f)
        f.close()
        cachedTime = dt.datetime.fromtimestamp(data["timestamp"])
        currentTime = dt.datetime.now()
        differenceInSeconds = abs(cachedTime - currentTime).total_seconds()
        
        
        # 86400 seconds = 1 day.
        if((differenceInSeconds / 86400) <= 0.5):
            print("Cached")
            return data["data"]
        
        url = f""
        f = open("data/data.json", "wt+")
        f.seek(0)

        # Todo: Just change data source to API
        newData = {"timestamp": currentTime.timestamp(), "data": {"ABC": "PQR", "XYZ": "LMN"}}
        f.write(json.dumps(newData, indent = 4))
        f.seek(0)
        data = json.load(f)
        print("Server")
        return data["data"]

        
    except Exception as e:
        print("Error in getting currencies", e)
    finally:
        f.close()
        
    

    

getCurrencies()