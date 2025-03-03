import requests
import json
from datetime import datetime

# Dictionary of BoM station URLs
bom_urls = {
    "Canungra": "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.94418.json",
    "Amberley": "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.94568.json",
    "Greenbank": "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.94419.json",
    "Tin Can Bay": "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.94420.json",
    "Brisbane": "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.94576.json"
}

# Initialize GeoJSON structure
geojson = {
    "type": "FeatureCollection",
    "features": []
}

# Function to convert a 14-digit timestamp to "YYYY-MM-DD HH:MM:SS"
def convert_timestamp(raw_timestamp):
    try:
        # raw_timestamp is assumed to be 14 characters long (e.g., "20250303133000")
        dt = datetime.strptime(str(raw_timestamp)[:14], "%Y%m%d%H%M%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        print(f"DEBUG: Failed to convert timestamp '{raw_timestamp}'")
        return None

print("DEBUG: Starting BoM JSON fetch & GeoJSON creation...")

for site_name, url in bom_urls.items():
    print(f"\nDEBUG: Processing site '{site_name}' with URL: {url}")
    try:
        # 1. Fetch data
        response = requests.get(url)
        print(f"DEBUG: HTTP status code for {site_name} → {response.status_code}")

        response.raise_for_status()  # Will throw an exception if status >= 400
        data = response.json()

        # 2. Basic checks on data structure
        if "observations" not in data:
            print(f"WARNING: 'observations' key missing in JSON for {site_name}")
            continue

        if "data" not in data["observations"]:
            print(f"WARNING: 'data' key missing under 'observations' for {site_name}")
            continue

        obs_list = data["observations"]["data"]
        print(f"DEBUG: {site_name} has {len(obs_list)} observations")

        if not obs_list:
            print(f"WARNING: No observations found for {site_name}, skipping...")
            continue

        # 3. Take the last observation as "latest"
        latest_obs = obs_list[-1]
        print(f"DEBUG: Latest observation snippet for {site_name}: {latest_obs}")

        # 4. Convert the timestamp
        raw_ts = latest_obs.get("aifstime_utc")
        formatted_date = convert_timestamp(raw_ts)
        print(f"DEBUG: Original timestamp: {raw_ts} → Converted: {formatted_date}")

        # 5. Extract lat/lon
        lat = latest_obs.get("lat")
        lon = latest_obs.get("lon")
        print(f"DEBUG: Coordinates for {site_name}: lat={lat}, lon={lon}")

        # 6. Create GeoJSON feature
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "station": site_name,
                "timestamp": formatted_date,
                "rainfall_mm": float(latest_obs.get("rain_trace", 0)),
                "humidity_%": latest_obs.get("rel_hum"),
                "dew_point_C": latest_obs.get("dewpt"),
                "air_temp_C": latest_obs.get("air_temp"),
                "feels_like_C": latest_obs.get("apparent_t"),
                "wind_dir": latest_obs.get("wind_dir"),
                "wind_speed_kmh": latest_obs.get("wind_spd_kmh"),
                "wind_gust_kmh": latest_obs.get("wind_gust_kmh")
            }
        }
        geojson["features"].append(feature)

        print(f"✅ Successfully added feature for {site_name}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data for {site_name}: {e}")
    except KeyError as ke:
        print(f"❌ KeyError for {site_name}: Missing key {ke}")
    except Exception as ex:
        print(f"❌ Unexpected error for {site_name}: {ex}")

# 7. After processing all stations, print how many features we have
num_features = len(geojson["features"])
print(f"\nDEBUG: Finished processing all sites. Total features = {num_features}")

# 8. Save the final GeoJSON to file
try:
    with open("bom_weather.geojson", "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=4)
    print("✅ GeoJSON file updated successfully!")
except Exception as ex:
    print(f"❌ Error writing bom_weather.geojson: {ex}")
