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
        return None

# Process each weather station
for site_name, url in bom_urls.items():
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Extract the latest observation (assuming the last item is the most recent)
        latest_obs = data["observations"]["data"][-1]

        # Convert the timestamp from "aifstime_utc"
        formatted_date = convert_timestamp(latest_obs["aifstime_utc"])

        # Create GeoJSON feature
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [latest_obs["lon"], latest_obs["lat"]]
            },
            "properties": {
                "station": site_name,
                "timestamp": formatted_date,  # Now in "YYYY-MM-DD HH:MM:SS" format
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

        print(f"✅ Data added for {site_name}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data for {site_name}: {e}")

# Save the final GeoJSON to file
with open("bom_weather.geojson", "w", encoding="utf-8") as f:
    json.dump(geojson, f, indent=4)

print("✅ GeoJSON file updated successfully!")
