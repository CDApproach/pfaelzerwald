"""Luftbildkacheln (sat/) vom WMS DOP20 des LVermGeo Rheinland-Pfalz holen.

Aufruf (im Projektordner, nach build_terrain.py):  python3 tools/build_aerial.py

sat/0 … sat/3  ein Bild je Geländekachel, 512 px
sat/4          ein Bild je Kachel der Ebene 3 mit 2048 px; jede Kachel der Ebene 4 nutzt ein Viertel (3,9 m/px)
sat/5          ein Bild je Kachel der Ebene 4 mit 2048 px (2 m/px), wird nur aus der Nähe geladen
"""
import io, json, os, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

WMS = ('https://geo4.service24.rlp.de/wms/rp_dop20.fcgi?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap'
       '&LAYERS=rp_dop20&STYLES=&CRS=EPSG:4326&FORMAT=image/jpeg&BBOX={b}&WIDTH={w}&HEIGHT={w}')
meta = json.load(open('meta.json')); tinfo = json.load(open('terrain/tiles.json'))
LON0, LAT0, K, C = meta['lon0'], meta['lat0'], meta['kmPerDeg'], meta['cosLat']
ROOT, LMAX = tinfo['root'], tinfo['lmax']

def bbox(L, key):
    i, j = map(int, key.split('_')); size = ROOT / 2 ** L
    x0, z0 = -ROOT / 2 + i * size, -ROOT / 2 + j * size
    # WMS 1.3.0 mit EPSG:4326: Achsenreihenfolge Breite, Länge
    return f'{LAT0 - (z0 + size) / K:.7f},{LON0 + x0 / (K * C):.7f},{LAT0 - z0 / K:.7f},{LON0 + (x0 + size) / (K * C):.7f}'

jobs = []
for L, keys in tinfo['tiles'].items():
    L = int(L)
    for k in keys:
        if L < LMAX: jobs.append((f'sat/{L}/{k}.webp', bbox(L, k), 512, 74))
        if L == LMAX - 1: jobs.append((f'sat/{LMAX}/{k}.webp', bbox(L, k), 2048, 72))
        if L == LMAX: jobs.append((f'sat/{LMAX + 1}/{k}.webp', bbox(L, k), 2048, 70))

def run(job):
    out, b, w, q = job
    if os.path.exists(out): return
    os.makedirs(os.path.dirname(out), exist_ok=True)
    for attempt in range(4):
        try:
            req = urllib.request.Request(WMS.format(b=b, w=w), headers={'User-Agent': 'pfaelzerwald-relief'})
            Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=120).read())).convert('RGB').save(out, quality=q, method=5)
            return
        except Exception as e:
            err = e; time.sleep(3 * (attempt + 1))
    print('Fehlgeschlagen:', out, err)

with ThreadPoolExecutor(4) as ex: list(ex.map(run, jobs))
print(len(jobs), 'Luftbilder')
