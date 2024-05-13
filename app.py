from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import requests
import os
from waitress import serve


app = Flask(__name__)
CORS(app, origins=["http://localhost:3333", "https://chat.openai.com"])


api_key = os.environ.get("GOOGLE_API_KEY")


def get_place_address(place_id):
    url = (
        f"https://maps.googleapis.com/maps/api/place/details/json"
        f"?place_id={place_id}"
        f"&fields=formatted_address"
        f"&key={api_key}"
    )
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        address = data.get("result", {}).get("formatted_address", "")
        return address
    else:
        return None


def get_lat_lng_from_address(address):
    params = {
        "address": address,
    }
    url = (
        f"https://maps.googleapis.com/maps/api/geocode/json"
        f"?address={params['address']}"
        f"&key={api_key}"
    )
    response = requests.get(url)

    response = requests.get(url)

    if response.status_code == 200:
        location = (
            response.json()
            .get("results", [])[0]
            .get("geometry", {})
            .get("location", {})
        )
        return f"{location.get('lat')},{location.get('lng')}"
    else:
        return "37.795980, -122.416920"


def get_reviews(place_id, name, address):
    params = {
        "place_id": place_id,
    }
    url = (
        f"https://maps.googleapis.com/maps/api/place/details/json"
        f"?place_id={params['place_id']}"
        f"&key={api_key}"
    )
    response = requests.get(url)
    if response.status_code == 200:
        reviewObj = {
            "name": name,
            "reviews": response.json().get("result", {}).get("reviews", [])[:3],
            "address": address,
        }
        return reviewObj
    else:
        return {}


@app.route("/get_place_details/<address>/<int:radius>/<type>", methods=["GET"])
def proccessPlaces(address, radius, type):
    location = get_lat_lng_from_address(address)

    if not location:
        return {"error": "Unable to get coordinates for the specified address"}, 400

    params = {"key": api_key, "location": location, "radius": radius, "type": type}

    url = (
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={params['location']}"
        f"&radius={params['radius']}"
        f"&type={params['type']}"
        f"&key={api_key}"
        f"&opennow=true"
    )
    response = requests.get(url)

    if response.status_code == 200:
        possibleNearbyPlaces = response.json().get("results", [])[:10]

        all_reviews = []
        for index, place in enumerate(possibleNearbyPlaces):
            name = place.get("name", "")
            address = get_place_address(place["place_id"])
            reviews = get_reviews(place["place_id"], name, address)
            all_reviews.append(reviews)
        return all_reviews
    else:
        return []


@app.route("/.well-known/ai-plugin.json")
def serve_ai_plugin():
    return send_from_directory(".", "ai-plugin.json", mimetype="application/json")


@app.route("/.well-known/openapi.yaml")
def serve_openapi_yaml():
    return send_from_directory(".", "openapi.yaml", mimetype="text/yaml")

@app.route("/logo")
def serve_logo():
    return send_from_directory(".", "perfect.png", mimetype="image/png")

if __name__ == "__main__":
    serve(app, host="localhost", port=3333)
