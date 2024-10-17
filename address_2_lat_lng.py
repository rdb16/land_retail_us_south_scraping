import requests
import os
from dotenv import load_dotenv


def get_lat_lng_from_address(add):
    load_dotenv()
    api_key = os.getenv("GEOCODING_API_KEY")

    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={add}&key={api_key}"
    response = requests.get(url)
    data = response.json()

    if data["status"] == "OK":
        result = data["results"][0]
        lat = result["geometry"]["location"]["lat"]
        lng = result["geometry"]["location"]["lng"]
        return lat, lng
    else:
        print(f"Error: {data['status']}")
        return "N/A", "N/A"


if __name__ == "__main__":
    address = input("Enter address: ")
    lat, lng = get_lat_lng_from_address(address)
    print("Latitude: ", lat)
    print("Longitude: ", lng)
