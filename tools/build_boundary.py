"""Grenze des Naturraums Pfälzerwald aus OpenStreetMap holen und als meta.json speichern.

Aufruf (im Projektordner):  python3 tools/build_boundary.py
Ergebnis: meta.json mit Projektionsparametern und dem Grenzpolygon in lokalen Kilometern
(x nach Osten, z nach Süden, Ursprung bei 7,84° O / 49,31° N).
"""
import json, math, urllib.parse, urllib.request

RELATION = 14218399            # OSM-Relation "Pfälzerwald" (natural=mountain_range)
LON0, LAT0, KM_PER_DEG = 7.84, 49.31, 111.195
COS = math.cos(math.radians(LAT0))

query = f'[out:json][timeout:120];relation({RELATION});out geom;'
req = urllib.request.Request('https://overpass-api.de/api/interpreter',
                             data=urllib.parse.urlencode({'data': query}).encode(),
                             headers={'User-Agent': 'pfaelzerwald-relief'})
rel = json.load(urllib.request.urlopen(req, timeout=180))['elements'][0]

# Wege der Relation zu einem geschlossenen Ring zusammensetzen
segs = [[(p['lon'], p['lat']) for p in m['geometry']] for m in rel['members'] if m['type'] == 'way' and m['role'] == 'outer']
ring = segs.pop(0)
while ring[0] != ring[-1]:
    for i, s in enumerate(segs):
        if s[0] == ring[-1]: ring += s[1:]; break
        if s[-1] == ring[-1]: ring += s[::-1][1:]; break
    else:
        raise SystemExit('Ring lässt sich nicht schließen')
    segs.pop(i)

boundary = [[round((lon - LON0) * KM_PER_DEG * COS, 4), round(-(lat - LAT0) * KM_PER_DEG, 4)] for lon, lat in ring]
json.dump({'lon0': LON0, 'lat0': LAT0, 'kmPerDeg': KM_PER_DEG, 'cosLat': COS, 'boundary': boundary},
          open('meta.json', 'w'))
print('meta.json:', len(boundary), 'Punkte')
