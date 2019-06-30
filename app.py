from flask import Flask, request, jsonify, render_template, make_response
from forms import SearchForm
import connections
import database


app = Flask(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = True


@app.route("/app/search", methods=["GET", "POST"])
def search_app():
    form = SearchForm(csrf_enabled=False)
    if form.validate_on_submit():  # form is being submitted
        source = request.form.get("source")  # get data
        destination = request.form.get("destination")
        departure_date = request.form.get("departure_date")
        carrier = "Eurolines"
        journeys = connections.find_connections(
            source, destination, departure_date, carrier
        )
        template = render_template(
            "search_results.html", journeys=journeys, carrier=carrier
        )
        return make_response(template)
    else:
        return render_template("search.html", form=form)


@app.route("/search", methods=["GET"])
def search():
    source = request.args.get("source")
    destination = request.args.get("destination")
    departure_date = request.args.get("date_from")
    arrival_date = request.args.get("date_to")
    carrier = request.args.get("carrier")
    if arrival_date is None:
        results = connections.find_connections(
            source, destination, departure_date, carrier
        )
    else:
        results = connections.find_connections_between_dates(
            source, destination, departure_date, arrival_date, carrier
        )
    return jsonify(results)


@app.route("/combinations", methods=["GET"])
def combinations():
    source = request.args.get("source")
    destination = request.args.get("destination")
    date = request.args.get("date")
    return jsonify(database.find_combinations(source, destination, date))


@app.route("/locations-search", methods=["GET"])
def locations_search():
    term = request.args.get("term", "").lower()
    destinations = connections.find_cities_and_stops(term)
    return jsonify([x for x in destinations if term in x.lower()])


if __name__ == "__main__":
    app.run(debug=True)
