import credentials
import googlemaps
from datetime import datetime

gmaps = googlemaps.Client(credentials.MAPS_API_KEY)

# For getting the lat and lng of work parameters
# geocode_result = gmaps.geocode('UCL Roberts Building London')[0]['geometry']['location']
# dest_lat = geocode_result['lat']
# dest_lng = geocode_result['lng']
# print(f'{latitude}, {longitude}')
dest_lat = 51.5228492
dest_lng = -0.1321774


def distance_from_work(origin):
    now = datetime.now()
    directions_result = gmaps.directions(origin,
                                         f"{dest_lat}, {dest_lng}",
                                         mode="bicycling",
                                         departure_time=now)[0]['legs'][0]

    return directions_result['duration']['value']