from requests_html import HTMLSession
from redis import StrictRedis
import json
import os
import sys
from datetime import datetime, timedelta
from slugify import slugify


session = HTMLSession()

redis_config = {
    "host": os.environ["REDIS_HOST"],
    "password": os.environ["REDIS_PASS"],
    "port": os.environ["REDIS_PORT"],
}

redis = StrictRedis(socket_connect_timeout=3, **redis_config)


def get_city_id(city_name, carrier):
    key = slugify(f"{carrier}_{city_name}", separator="_")
    # check for redis
    city_id = redis.get(key)
    if city_id is not None:
        return city_id
    else:
        city_detail_request = session.get(
            f"https://back.eurolines.eu/euroline_api/origins?q={city_name}"
        ).text
        city_request_json = json.loads(city_detail_request)
        try:
            city_id = city_request_json[0]["stops"][0]["id"]
            redis.set(key, city_id)
            return city_id
        except IndexError:
            sys.stderr.write("City that you provided does not exists")
            return None


def create_connection(json_data):
    data = {}
    data["departure_datetime"] = datetime.strptime(
        json_data["departure"], "%Y-%m-%dT%H:%M:%S"
    ).strftime("%Y-%m-%d %H:%M:%S")
    data["arrival_datetime"] = datetime.strptime(
        json_data["arrival"], "%Y-%m-%dT%H:%M:%S"
    ).strftime("%Y-%m-%d %H:%M:%S")
    data["source"] = json_data["origin"]["name"]
    data["destinations"] = json_data["destination"]["name"]
    data["price"] = json_data["price"]
    data["type"] = "bus"
    data["source_id"] = json_data["origin"]["id"]
    data["destination_id"] = json_data["destination"]["id"]
    data["carrier"] = "Eurolines"

    return data


def get_json_connection_payload(source_id, destination_id, date):
    connections_payload = session.get(
        f"https://back.eurolines.eu/euroline_api/journeys?date={date}&flexibility=0&currency=CURRENCY.EUR"
        f"&passengers=BONUS_SCHEME_GROUP.ADULT,1&promoCode=&direct=false"
        f"&originStop={source_id}&destinationStop={destination_id}"
    )
    return json.loads(connections_payload.text)


def get_connections(source_id, destination_id, date):
    connections_payload = get_json_connection_payload(source_id, destination_id, date)
    connections_data = []
    for json_info in connections_payload:
        connections_data.append(create_connection(json_info))
    return connections_data


def make_key(source, destination, departure_date, carrier):
    return slugify(f"{source}_{destination}_{departure_date}_{carrier}", separator="_")


def find_connections(source, destination, departure_date, carrier):
    # make key
    key = make_key(source, destination, departure_date, carrier)
    # try to find info in redis
    connections = redis.get(key)
    if connections is not None:
        print("Using redis")
        connections = json.loads(connections)
    else:
        # info is not in redis, make requests and put it into redis
        source_id = get_city_id(source, carrier)
        destination_id = get_city_id(destination, carrier)
        if source_id is None or destination_id is None:
            return []
        connections = get_connections(source_id, destination_id, departure_date)
        redis.setex(key, 60 * 60, json.dumps(connections))
    return connections


def find_connections_between_dates(
    source, destination, departure_date, arrival_date, carrier
):
    connections = []
    dates = []

    departure_date = datetime.strptime(departure_date, "%Y-%m-%d")
    arrival_date = datetime.strptime(arrival_date, "%Y-%m-%d")

    delta = arrival_date - departure_date

    for i in range(delta.days + 1):
        actual_date = departure_date + timedelta(days=i)
        dates.append(actual_date)

    # Create redis pipeline
    pipe = redis.pipeline()
    for index, date in enumerate(dates):
        pipe.get(make_key(source, destination, date, carrier))
    # Check and add cached connections and create&add for non-cached for post proccessing
    responses = pipe.execute()
    for response, date in zip(responses, dates):
        if response is not None:
            connections += json.loads(response)
        else:
            connections += find_connections(source, destination, date, carrier)

    return connections


def find_cities_and_stops(search_term):
    key = slugify(search_term, separator="_")
    cities_and_stops = redis.get(key)
    if cities_and_stops is not None:
        return json.loads(cities_and_stops)
    else:
        city_detail_request = session.get(
            f"https://back.eurolines.eu/euroline_api/origins?q={search_term}"
        ).text
        city_request_json = json.loads(city_detail_request)
        try:
            cities_and_stops = []
            for city in city_request_json:
                cities_and_stops.append(city["name"])
                for stop in city["stops"]:
                    cities_and_stops.append(stop["name"])
            redis.set(key, json.dumps(cities_and_stops))
            return cities_and_stops
        except IndexError:
            return []
