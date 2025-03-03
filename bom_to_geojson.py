import requests
import json

# Dictionary of BoM station URLs
bom_urls = {
    "Canungra": "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.94418.json",
    "Amberley": "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.94568.json",
    "Greenbank": "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.94419.json",
    "Tin Can Bay": "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.94420.json",
    "Brisbane": "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.94576.json"
}

# Headers to prevent 403 errors
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Create a GeoJSON structure
geojson = {
    "type": "FeatureCollection",
    "features": []
}

# Loop through all stations and fetch data
for site_name, url in bom_urls.items():
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        # Extract observation data
        for obs in data.get("observations", {}).get("data", []):
            feature = {
                "type": "Feature",
                "properties": {
                    "station": site_name,  # Assign station name
                    "timestamp": obs.get("local_date_time_full"),
                    "rainfall_mm": obs.get("rain_trace", None),
                    "humidity_%": obs.get("rel_hum", None),
                    "dew_point_C": obs.get("dewpt", None),
                    "air_temp_C": obs.get("air_temp", None),
                    "feels_like_C": obs.get("apparent_t", None),
                    "wind_dir": obs.get("wind_dir", None),
                    "wind_speed_kmh": obs.get("wind_spd_kmh", None),
                    "wind_gust_kmh": obs.get("wind_gust_kmh", None),
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [obs.get("lon", 0), obs.get("lat", 0)]  # Defaults to 0 if missing
                }
            }
            geojson["features"].append(feature)

        print(f"✅ Data added for {site_name}")

    else:
        print(f"❌ Error fetching {site_name}: {response.status_code} - {response.reason}")

# Save final GeoJSON
with open("bom_weather.geojson", "w") as f:
    json.dump(geojson, f, indent=4)

print("✅ All station data saved to bom_weather.geojson")
