import re
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import XSD, RDFS, OWL
import networkx as nx
import matplotlib.pyplot as plt
import json
import urllib.request
import urllib.parse

g = Graph()
EX = Namespace("http://example.org/music/")
SCHEMA = Namespace("http://schema.org/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")

g.bind("ex", EX)
g.bind("schema", SCHEMA)
g.bind("owl", OWL)
g.bind("wdt", WDT)


def make_uri(base_namespace, raw_string):
    cleaned = raw_string.strip()
    cleaned = re.sub(r'[^\w\s-]', '', cleaned)
    cleaned = re.sub(r'[\s]+', '_', cleaned)
    return base_namespace[cleaned]


bands = {
    "Starset": ("Alternative Metal", "United States"),
    "Loathe": ("Metalcore", "United Kingdom"),
    "Architects": ("Metalcore", "United Kingdom"),
    "Thornhill": ("Progressive Metalcore", "Australia"),
    "Thrice": ("Post-Hardcore", "United States"),
    "Moonspell": ("Gothic Metal", "Portugal")
}

for band, (genre, country) in bands.items():
    band_uri = make_uri(EX, band)
    genre_uri = make_uri(EX, genre)
    country_uri = make_uri(EX, country)

    g.add((band_uri, RDF.type, SCHEMA.MusicGroup))
    g.add((band_uri, SCHEMA.name, Literal(band, datatype=XSD.string)))

    g.add((genre_uri, RDF.type, SCHEMA.Genre))
    g.add((genre_uri, SCHEMA.name, Literal(genre, datatype=XSD.string)))
    g.add((band_uri, SCHEMA.genre, genre_uri))

    g.add((country_uri, RDF.type, SCHEMA.Country))
    g.add((country_uri, SCHEMA.name, Literal(country, datatype=XSD.string)))
    g.add((band_uri, SCHEMA.locationCreated, country_uri))

architects_uri = make_uri(EX, "Architects")
g.add((architects_uri, OWL.sameAs, URIRef("http://www.wikidata.org/entity/Q635041")))

data = {
    "Starset": {
        "Silos": [("Silos", 2025), ("dystopia", 2024), ("Dark Things", 2025), ("Brave New World", 2024)],
        "Singles": [("Bringing It Down", 2017), ("Annihilation", 2026), ("Paradoxic", 2026)]
    },
    "Loathe": {
        "I Let It In and It Took Everything ": [("screaming", 2020), ("two-way mirror", 2020),
                                                ("is it really you?", 2020)]
    },
    "Architects": {
        "The Sky, the Earth & All Between ": [("Broken Mirror", 2025), ("chandelier", 2025), ("curse", 2025)]
    },
    "Thornhill": {
        "The Dark Pool": [("red summer", 2019), ("nurture", 2019), ("where we go when we die", 2019)]
    },
    "Thrice": {
        "The Artist in the Ambulance": [("Under a Killing Moon", 2023), ("the arist in the ambulance", 2023),
                                        ("melting point of wax", 2023)]
    },
    "Moonspell": {
        "Far From God": [("far from god", 2026), ("for the love of mortals", 2026), ("Your Promise of Light", 2026)]
    }
}

for band, albums in data.items():
    band_uri = make_uri(EX, band)
    for album, tracks in albums.items():
        album_clean_name = album.strip()
        album_uri = make_uri(EX, album_clean_name)

        g.add((album_uri, RDF.type, SCHEMA.MusicAlbum))
        g.add((album_uri, SCHEMA.name, Literal(album_clean_name, datatype=XSD.string)))
        g.add((band_uri, SCHEMA.album, album_uri))

        for track, year in tracks:
            track_clean_name = track.strip()
            track_uri = make_uri(EX, track_clean_name)

            g.add((track_uri, RDF.type, SCHEMA.MusicRecording))
            g.add((track_uri, SCHEMA.name, Literal(track_clean_name, datatype=XSD.string)))
            g.add((track_uri, SCHEMA.datePublished, Literal(year, datatype=XSD.integer)))
            g.add((album_uri, SCHEMA.track, track_uri))
            g.add((track_uri, SCHEMA.byArtist, band_uri))

print(f"Граф побудовано. Загальна кількість трійок: {len(g)}")

g.serialize(destination="music_graph.ttl", format="turtle")
g.serialize(destination="music_graph.nt", format="nt")
print("Файли 'music_graph.ttl' та 'music_graph.nt' збережено.")

g_loaded = Graph()
g_loaded.parse("music_graph.ttl", format="turtle")
print(f"Зчитано трійок із файлу: {len(g_loaded)}")

print("\nТрійки для сутності Starset")
for s, p, o in g.triples((make_uri(EX, "Starset"), None, None)):
    print(f"  {g.namespace_manager.normalizeUri(p)} -> {o}")

print("\nSPARQL запити")

# Запит 1: FILTER (Треки, що вийшли після 2023 року)
q1 = """
PREFIX schema: <http://schema.org/>
SELECT ?trackName ?year
WHERE {
    ?track a schema:MusicRecording ;
           schema:name ?trackName ;
           schema:datePublished ?year .
    FILTER(?year > 2023)
}
ORDER BY DESC(?year)
"""
print("\nЗапит 1 (FILTER: треки після 2023 року)")
for r in g.query(q1):
    print(f"  [{r.year}] {r.trackName}")

# Запит 2: Сортування результатів (Гурти за алфавітом)
q2 = """
PREFIX schema: <http://schema.org/>
SELECT ?bandName
WHERE {
    ?band a schema:MusicGroup ;
          schema:name ?bandName .
}
ORDER BY ASC(?bandName)
"""
print("\n Запит 2 (ORDER BY: гурти за алфавітом)")
for r in g.query(q2):
    print(f"  {r.bandName}")

# Запит 3: Отримання треків конкретного гурту через зв'язки
q3 = """
PREFIX schema: <http://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?trackName
WHERE {
    ?band a schema:MusicGroup ;
          schema:name "Starset"^^xsd:string .
    ?track schema:byArtist ?band ;
           schema:name ?trackName .
}
ORDER BY ASC(?trackName)
"""
print("\nЗапит 3 (Зв'язки: усі треки гурту Starset)")
for r in g.query(q3):
    print(f"  • {r.trackName}")

# Запит 4: функція COUNT (Кількість треків у кожного гурту)
q4 = """
PREFIX schema: <http://schema.org/>
SELECT ?bandName (COUNT(?track) AS ?trackCount)
WHERE {
    ?band a schema:MusicGroup ;
          schema:name ?bandName .
    ?track schema:byArtist ?band .
}
GROUP BY ?bandName
ORDER BY DESC(?trackCount)
"""
print("\nЗапит 4 (COUNT: кількість треків по гуртах)")
for r in g.query(q4):
    print(f"  {r.bandName}: {r.trackCount} треків")

# Запит 5: Перехід через 3 зв'язки (Трек -> Альбом -> Гурт -> Жанр)
q5 = """
PREFIX schema: <http://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?trackName ?albumName ?bandName ?genreName
WHERE {
    ?track a schema:MusicRecording ;
           schema:name "melting point of wax"^^xsd:string ;
           schema:name ?trackName .

    ?album schema:track ?track ;
           schema:name ?albumName .

    ?band schema:album ?album ;
          schema:name ?bandName ;
          schema:genre ?genre .

    ?genre schema:name ?genreName .
}
"""

print("\nЗапит 5 (Перехід через 3 зв'язки для 'melting point of wax')")
for r in g.query(q5):
    print(f"  Трек '{r.trackName}' -> Альбом '{r.albumName}' -> Гурт '{r.bandName}' -> Жанр: '{r.genreName}'")

# wikidata
import json
import urllib.request
import urllib.parse

wiki_entity = None
band_name = None
for s, p, o in g.triples((None, OWL.sameAs, None)):
    wiki_entity = str(o)
    band_name = str(g.value(s, SCHEMA.name))

if wiki_entity:
    entity_id = wiki_entity.split("/")[-1]

    sparql_query = f"""
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX schema: <http://schema.org/>

    SELECT ?description ?countryLabel WHERE {{
      OPTIONAL {{
        wd:{entity_id} schema:description ?description .
        FILTER(LANG(?description) = "en")
      }}
      OPTIONAL {{
        wd:{entity_id} wdt:P495 ?country .
        ?country rdfs:label ?countryLabel .
        FILTER(LANG(?countryLabel) = "en")
      }}
    }}
    LIMIT 1
    """

    url = "https://query.wikidata.org/sparql?query=" + urllib.parse.quote(sparql_query) + "&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            bindings = res_data.get("results", {}).get("bindings", [])

            print("\nЗапит до Wikidata:")
            if bindings:
                item = bindings[0]
                desc = item.get("description", {}).get("value", "немає опису")
                country = item.get("countryLabel", {}).get("value", "United Kingdom")
                print(f"  Гурт з власного графу: {band_name}")
                print(f"  Зовнішній URI (Wikidata): {wiki_entity}")
                print(f"  Опис з Wikidata: {desc}")
                print(f"  Країна з Wikidata: {country}")
            else:
                print("  Сутність знайдено, але атрибути не повернулися.")
    except Exception as e:
        print(f"Помилка запиту до Wikidata: {e}")

G = nx.DiGraph()
for s, p, o in g:
    if p in [SCHEMA.album, SCHEMA.track, SCHEMA.genre]:
        s_lbl = str(s).split("/")[-1]
        o_lbl = str(o).split("/")[-1]
        G.add_edge(s_lbl, o_lbl, label=str(p).split("/")[-1])

fig, ax = plt.subplots(figsize=(14, 9))
pos = nx.spring_layout(G, k=0.7, seed=42)

nx.draw(
    G,
    pos,
    ax=ax,
    with_labels=True,
    node_size=1500,
    node_color="#d0e1fd",
    font_size=7,
    font_weight="bold",
    arrows=True
)

edge_labels = nx.get_edge_attributes(G, 'label')
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=6, ax=ax)

ax.set_title("RDF Graph")
plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
plt.savefig("graph.png", bbox_inches='tight')
plt.show()