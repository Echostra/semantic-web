import sys
import csv
import json
import re
from rdflib import Graph, Namespace, Literal, RDF, RDFS, XSD


def make_iri(ex, prefix, name):
    safe_name = name.replace(' ', '_')
    return ex[f"{prefix}/{safe_name}"]


def main():
    if len(sys.argv) != 4:
        print("Використання: python build_graph.py flights.csv params.json graph.ttl")
        sys.exit(1)

    flights_csv = sys.argv[1]
    params_json = sys.argv[2]
    output_ttl = sys.argv[3]

    with open(params_json, 'r', encoding='utf-8') as f:
        params = json.load(f)
    budget_threshold = params.get("budget_threshold_eur", 0)
    long_flight_min = params.get("long_flight_min", 0)

    flights = []
    seen_ids = set()
    country_departures = {}

    with open(flights_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_id = row.get('flight_id', '').strip()
            if not raw_id:
                continue

            f_id = raw_id.upper()

            if f_id in seen_ids:
                continue
            seen_ids.add(f_id)

            from_city = row.get('from_city', '').strip().title()
            to_city = row.get('to_city', '').strip().title()
            from_country = row.get('from_country', '').strip().title()
            to_country = row.get('to_country', '').strip().title()
            airline = row.get('airline', '').strip()
            note = row.get('note', '').strip()

            raw_date = row.get('dep_date', '').strip()
            if '.' in raw_date:
                parts = raw_date.split('.')
                if len(parts) == 3:
                    dep_date = f"{parts[2]}-{parts[1]}-{parts[0]}"  # YYYY-MM-DD
                else:
                    dep_date = raw_date
            else:
                dep_date = raw_date

            duration = int(row.get('duration_min', 0))
            price_str = row.get('price_eur', '').strip()
            price = float(price_str) if price_str and price_str.lower() != 'nan' else None
            country_departures[from_country] = country_departures.get(from_country, 0) + 1

            flights.append({
                'id': f_id,
                'from_city': from_city, 'to_city': to_city,
                'from_country': from_country, 'to_country': to_country,
                'airline': airline, 'date': dep_date,
                'duration': duration, 'price': price, 'note': note
            })

    busy_countries = {c for c, count in country_departures.items() if count >= 2}

    g = Graph()
    EX = Namespace("http://example.org/mkr/")
    g.bind("ex", EX)

    g.add((EX.BudgetFlight, RDFS.subClassOf, EX.Flight))
    g.add((EX.LongFlight, RDFS.subClassOf, EX.Flight))

    properties_schema = [
        (EX.operatedBy, EX.Flight, EX.Airline),
        (EX.departsFrom, EX.Flight, EX.City),
        (EX.arrivesAt, EX.Flight, EX.City),
        (EX.locatedIn, EX.City, EX.Country),
        (EX.departureDate, EX.Flight, XSD.date),
        (EX.durationMin, EX.Flight, XSD.integer),
        (EX.priceEur, EX.Flight, XSD.decimal),
        (EX.fromBusyCountry, EX.Flight, XSD.boolean),
        (EX.hasDelayMinutes, EX.Flight, XSD.integer),
        (EX.reportedBy, RDF.Statement, EX.Source)
    ]
    for prop, dom, rng in properties_schema:
        g.add((prop, RDFS.domain, dom))
        g.add((prop, RDFS.range, rng))

    for f in flights:
        f_node = EX[f"flight/{f['id']}"]

        is_budget = False
        is_long = False
        if f['price'] is not None and f['price'] <= budget_threshold:
            is_budget = True
            g.add((f_node, RDF.type, EX.BudgetFlight))
        if f['duration'] >= long_flight_min:
            is_long = True
            g.add((f_node, RDF.type, EX.LongFlight))

        if not is_budget and not is_long:
            g.add((f_node, RDF.type, EX.Flight))

        airline_node = make_iri(EX, "airline", f['airline'])
        g.add((f_node, EX.operatedBy, airline_node))
        g.add((airline_node, RDF.type, EX.Airline))
        g.add((airline_node, RDFS.label, Literal(f['airline'], lang="en")))

        from_city_node = make_iri(EX, "city", f['from_city'])
        from_country_node = make_iri(EX, "country", f['from_country'])
        g.add((f_node, EX.departsFrom, from_city_node))
        g.add((from_city_node, RDF.type, EX.City))
        g.add((from_city_node, RDFS.label, Literal(f['from_city'], lang="en")))
        g.add((from_city_node, EX.locatedIn, from_country_node))
        g.add((from_country_node, RDF.type, EX.Country))
        g.add((from_country_node, RDFS.label, Literal(f['from_country'], lang="en")))

        to_city_node = make_iri(EX, "city", f['to_city'])
        to_country_node = make_iri(EX, "country", f['to_country'])
        g.add((f_node, EX.arrivesAt, to_city_node))
        g.add((to_city_node, RDF.type, EX.City))
        g.add((to_city_node, RDFS.label, Literal(f['to_city'], lang="en")))
        g.add((to_city_node, EX.locatedIn, to_country_node))
        g.add((to_country_node, RDF.type, EX.Country))
        g.add((to_country_node, RDFS.label, Literal(f['to_country'], lang="en")))

        g.add((f_node, EX.departureDate, Literal(f['date'], datatype=XSD.date)))
        g.add((f_node, EX.durationMin, Literal(f['duration'], datatype=XSD.integer)))
        if f['price'] is not None:
            g.add((f_node, EX.priceEur, Literal(f['price'], datatype=XSD.decimal)))

        if f['from_country'] in busy_countries:
            g.add((f_node, EX.fromBusyCountry, Literal("true", datatype=XSD.boolean)))

        if f['note']:
            match = re.search(r"delay=(\d+);by=([\w\d_]+)", f['note'])
            if match:
                delay = int(match.group(1))
                source = match.group(2)

                stmt_node = EX[f"stmt/{f['id']}-delay"]
                g.add((stmt_node, RDF.type, RDF.Statement))
                g.add((stmt_node, RDF.subject, f_node))
                g.add((stmt_node, RDF.predicate, EX.hasDelayMinutes))
                g.add((stmt_node, RDF.object, Literal(delay, datatype=XSD.integer)))

                source_node = EX[f"source/{source}"]
                g.add((stmt_node, EX.reportedBy, source_node))

    g.serialize(destination=output_ttl, format="turtle")
    print(f"Граф збережено у {output_ttl}. Трійки: {len(g)}")


if __name__ == "__main__":
    main()