import psycopg2
import os
from psycopg2.extras import RealDictCursor

pg_config = {
    "host": os.environ["PG_HOST"],
    "database": os.environ["PG_DATABASE"],
    "user": os.environ["PG_USER"],
    "password": os.environ["PG_PASS"],
}

sql_insert = """
    INSERT INTO journeys_<nickname> (source, destination, departure_datetime, arrival_datetime, carrier,
                          vehicle_type, price, currency)
    VALUES (%(source)s,
            %(destination)s,
		    %(departure_datetime)s,
            %(arrival_datetime)s,
            %(carrier)s,
            %(vehicle_type)s,
            %(price)s,
            %(currency)s);
"""

sql_combinations = """
    select  * from (select * from journeys j1 where lower(j1.source) = lower(%(source)s) and j1.departure_datetime::date = %(date)s::timestamp::date) j1
    inner join  journeys j2
    on j1.destination = j2.source	
    where j1.arrival_datetime > j2.departure_datetime
    and lower(j2.destination) = lower(%(destination)s)
"""


def query_journeys():
    sql_select = "SELECT * FROM journeys_<nickname>"
    conn = psycopg2.connect(**pg_config)
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(sql_select)
        results_dict = cursor.fetchall()
        print(results_dict)
        conn.close()
        return results_dict


def insert_journey(
    source,
    destination,
    departure_datetime,
    arrival_datetime,
    carrier,
    vehicle_type,
    price,
    currency,
):
    values = {
        "source": source,
        "destination": destination,
        "departure_datetime": departure_datetime,
        "arrival_datetime": arrival_datetime,
        "carrier": carrier,
        "vehicle_type": vehicle_type,
        "price": price,
        "currency": currency,
    }
    conn = psycopg2.connect(**pg_config)
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(sql_insert, values)  # psycopg2 prepared statement syntax
        conn.commit()  # important, otherwise your data won’t be inserted!
    conn.close()


def find_combinations(source, destination, date):
    values = {"source": source, "destination": destination, "date": date}
    conn = psycopg2.connect(**pg_config)
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(sql_combinations, values)
        results_dict = cursor.fetchall()
        print(results_dict)
        conn.close()
        return results_dict
