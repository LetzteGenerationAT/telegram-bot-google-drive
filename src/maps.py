import googlemaps
from datetime import datetime
import requests
import os

# gmaps = googlemaps.Client(key='Add Your Key here')

# # Geocoding an address
# geocode_result = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')

# # Look up an address with reverse geocoding
# reverse_geocode_result = gmaps.reverse_geocode((40.714224, -73.961452))

def get_location(lat:str, lon:str):
    resp = requests.get(f"https://us1.locationiq.com/v1/reverse?key={os.environ['LOCATION_IQ_API_TOKEN']}&lat={lat}&lon={lon}&format=json")
    return f"{resp.json()['address']['city']}_{resp.json()['address']['road']}"