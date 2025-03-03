import requests
import json
from datetime import datetime

# Dictionary of BoM station URLs (using HTTP)
bom_urls = {
    "Canungra": "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.94418.json",
    "Amberley": "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.94568.json",
    "Greenbank": "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.94419.json",
    "Tin Can Bay": "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.94420.json",
    "Brisbane": "http://www.bom.gov.au/fwo/IDQ60801/IDQ60801.94576.json"
}

# Headers to avoid 403 errors (using a realistic User-Agent and a Referer)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "http://www.bom.gov.au/"
}

# Initialize GeoJSON structure
geojson = {
    "type": "FeatureCollection",
    "features": []
}

# Function to convert a 14-digit timestamp (YYYYMMDDHHMMSS) to "YYYY-MM-DD HH:MM:SS" and ISO 8601
def convert_timestamp(raw_timestamp):
    """
    Returns a tuple: (human_readable_string, iso_datetime_string)
    Example: ("2025-02-28 05:00:00", "2025-02-28T05:00:00Z")
    """
    try:
        dt = datetime.strptime(str(raw_timestamp)[:14], "%Y%m%d%H%M%S")
        human_readable = dt.strftime("%Y-%m-%d %H:%M:%S")
        # Append 'Z' to indicate UTC; ArcGIS often treats that as a Date/Time field
        iso_8601 = dt.isoformat() + "Z"
        return human_readable, iso_8601
    except ValueError:
        print(f"DEBUG: Failed to convert timestamp '{raw_timestamp}'")
        return None, None

print("DEBUG: Starting BoM JSON fetch & GeoJSON creation...")

# Process each station
for site_name, url in bom_urls.items():
    print(f"\nDEBUG: Processing site '{site_name}' with URL: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        print(f"DEBUG: HTTP status code for {site_name} → {response.status_code}")

        # Check if response body is empty
        if not response.text.strip():
            print(f"WARNING: Empty response received for {site_name}. Skipping.")
            continue

        try:
            data = response.json()
        except json.JSONDecodeError as jde:
            print(f"❌ JSON decode error for {site_name}: {jde}")
            snippet = response.text[:500] + ("... [truncated]" if len(response.text) > 500 else "")
            print(f"DEBUG: Response text for {site_name}: {snippet}")
            continue

        # Check JSON structure
        if "observations" not in data or "data" not in data["observations"]:
            print(f"WARNING: 'observations.data' missing in JSON for {site_name}. Skipping.")
            continue

        obs_list = data["observations"]["data"]
        print(f"DEBUG: {site_name} has {len(obs_list)} observations")

        if not obs_list:
            print(f"WARNING: No observations found for {site_name}. Skipping.")
            continue

        # Use the last observation as the latest
        latest_obs = obs_list[-1]
        print(f"DEBUG: Latest observation for {site_name}: {latest_obs}")

        # Convert the timestamp from "aifstime_utc"
        raw_ts = latest_obs.get("aifstime_utc")
        human_date, iso_date = convert_timestamp(raw_ts)
        print(f"DEBUG: Raw timestamp: {raw_ts} → human: {human_date}, iso: {iso_date}")

        # If conversion failed, skip
        if human_date is None or iso_date is None:
            print(f"❌ Could not parse timestamp for {site_name}, skipping.")
            continue

        # Get coordinates
        lat = latest_obs.get("lat")
        lon = latest_obs.get("lon")
        print(f"DEBUG: Coordinates for {site_name}: lat={lat}, lon={lon}")

        # Create GeoJSON feature
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "station": site_name,
                "timestamp": human_date,    # human-readable
                "timestamp_date": iso_date, # ISO 8601 (ArcGIS-friendly)
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
    except Exception as ex:
        print(f"❌ Unexpected error for {site_name}: {ex}")

print(f"\nDEBUG: Finished processing all sites. Total features = {len(geojson['features'])}")

# Save the final GeoJSON to file
output_file = "bom_weather.geojson"
try:
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=4)
    print(f"✅ GeoJSON file saved to '{output_file}'")
except Exception as ex:
    print(f"❌ Error writing GeoJSON file: {ex}")
