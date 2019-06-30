import click
import connections
from pprint import pprint


@click.command()
@click.option("--source", default="Bratislava Airport")
@click.option("--destination", default="Vienna Airport")
@click.option("--departure_date", default="2019-07-09")
@click.option("--carrier", default="Eurolines")
def cli_find_connections(source, destination, departure_date, carrier):
    pprint(connections.find_connections(source, destination, departure_date, carrier))


if __name__ == "__main__":
    cli_find_connections()
