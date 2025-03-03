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

# Function to convert timestamp to ISO 8601 format (YYYY-MM-DD HH:MM:SS)
def convert_timestamp(raw_timestamp):
    try:
        # Convert YYYYMMDDHHMMSSSS to YYYY-MM-DD HH:MM:SS
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

        # Extract the latest observation
        latest_obs = data["observations"]["data"][-1]

        # Convert timestamp
        formatted_date = convert_timestamp(latest_obs["aifstime_utc"])

        # Create GeoJSON feature
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [latest_obs["lon"], latest_obs["lat"]]
            },
            "properties": {
                "site": site_name,
                "timestamp": formatted_date,  # ✅ Now in a proper date format!
                "rainfall_mm": latest_obs.get("rain_trace", None),
                "humidity": latest_obs.get("rel_hum", None),
                "dew_point": latest_obs.get("dewpt", None),
                "air_temp": latest_obs.get("air_temp", None),
                "feels_like_temp": latest_obs.get("apparent_t", None),
                "wind_dir": latest_obs.get("wind_dir", None),
                "wind_speed_kmh": latest_obs.get("wind_spd_kmh", None),
                "wind_gust_kmh": latest_obs.get("wind_gust_kmh", None)
            }
        }

        # Add feature to GeoJSON
        geojson["features"].append(feature)

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching data for {site_name}: {e}")

# Save as GeoJSON
with open("bom_weather.geojson", "w", encoding="utf-8") as f:
    json.dump(geojson, f, indent=4)

print("✅ GeoJSON file updated successfully!")
