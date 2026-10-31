"""Geländekacheln (terrain/) aus Mapterhorn-Höhendaten erzeugen.

Aufruf (im Projektordner, nach build_boundary.py):  python3 tools/build_terrain.py
Braucht numpy, scipy, matplotlib und Pillow mit WebP. Dauert gut 20 Minuten.

Aufbau: Quadtree über ein 64 x 64 km großes Quadrat um den Ursprung. Ebene L hat 2^L x 2^L
Kacheln mit je 513 Stützpunkten von Kante zu Kante plus 1 Randpixel (515 x 515 px).
Ebene 4 hat 7,8 m Punktabstand. Höhe kodiert als h = (R*256 + G) / 50 - 100 (Meter).
Es werden nur Kacheln gespeichert, die das Grenzpolygon berühren.
"""
import glob, json, math, os, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter, binary_dilation
from matplotlib.path import Path

ROOT, N, LMAX, Z = 64.0, 512, 4, 13
CACHE = 'tools/cache/mapterhorn'
meta = json.load(open('meta.json'))
LON0, LAT0, K, C = meta['lon0'], meta['lat0'], meta['kmPerDeg'], meta['cosLat']

# --- Mapterhorn-Kacheln (Zoom 13, 512 px, Terrarium-Kodierung) laden
def tile_xy(lon, lat):
    n = 2 ** Z
    return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
x0, y0 = tile_xy(LON0 - 32.5 / (K * C), LAT0 + 32.5 / K)
x1, y1 = tile_xy(LON0 + 32.5 / (K * C), LAT0 - 32.5 / K)
os.makedirs(CACHE, exist_ok=True)
def fetch(xy):
    x, y = xy; p = f'{CACHE}/{x}_{y}.webp'
    if not os.path.exists(p):
        req = urllib.request.Request(f'https://tiles.mapterhorn.com/{Z}/{x}/{y}.webp', headers={'User-Agent': 'pfaelzerwald-relief'})
        open(p, 'wb').write(urllib.request.urlopen(req, timeout=60).read())
with ThreadPoolExecutor(6) as ex:
    list(ex.map(fetch, [(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]))

TS = 512
mosaic = np.zeros(((y1 - y0 + 1) * TS, (x1 - x0 + 1) * TS), np.float32)
for f in glob.glob(f'{CACHE}/*.webp'):
    tx, ty = map(int, os.path.basename(f)[:-5].split('_'))
    if not (x0 <= tx <= x1 and y0 <= ty <= y1): continue
    a = np.asarray(Image.open(f).convert('RGB')).astype(np.float32)
    mosaic[(ty - y0) * TS:(ty - y0 + 1) * TS, (tx - x0) * TS:(tx - x0 + 1) * TS] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
mosaic = gaussian_filter(mosaic, 0.6)

# --- auf das lokale Gitter der feinsten Ebene umrechnen
d4 = ROOT / (N * 2 ** LMAX)
n4 = N * 2 ** LMAX + 3
coord = -ROOT / 2 + (np.arange(n4) - 1) * d4
G = np.zeros((n4, n4), np.float32)
for r0 in range(0, n4, 512):
    X, Zc = np.meshgrid(coord, coord[r0:r0 + 512])
    lon = LON0 + X / (K * C); lat = LAT0 - Zc / K
    px = ((lon + 180) / 360 * 2 ** Z - x0) * TS - 0.5
    py = ((1 - np.arcsinh(np.tan(np.radians(lat))) / math.pi) / 2 * 2 ** Z - y0) * TS - 0.5
    G[r0:r0 + 512] = map_coordinates(mosaic, [py, px], order=1, mode='nearest')
del mosaic

# --- welche Kacheln berühren das Polygon?
cg = 1025; cc = -ROOT / 2 + np.arange(cg) * ROOT / (cg - 1)
CX, CZ = np.meshgrid(cc, cc)
inside = Path(np.array(meta['boundary'])).contains_points(np.c_[CX.ravel(), CZ.ravel()]).reshape(cg, cg)
inside = binary_dilation(inside, iterations=3)

def encode(h):
    v = np.clip(np.round((h + 100) * 50), 0, 65535).astype(np.uint32)
    im = np.zeros(h.shape + (3,), np.uint8); im[..., 0] = v >> 8; im[..., 1] = v & 255
    return Image.fromarray(im, 'RGB')

tiles = {}
GL = G
for L in range(LMAX, -1, -1):
    if L < LMAX:  # glätten und jeden zweiten Stützpunkt nehmen
        GL = np.pad(gaussian_filter(GL, 0.85)[1:-1, 1:-1][::2, ::2], 1, mode='edge')
    nt = 2 ** L; keys = []
    for j in range(nt):
        for i in range(nt):
            c0, c1 = int(i * (cg - 1) / nt), int((i + 1) * (cg - 1) / nt)
            r0, r1 = int(j * (cg - 1) / nt), int((j + 1) * (cg - 1) / nt)
            if not inside[r0:r1 + 1, c0:c1 + 1].any(): continue
            out = f'terrain/{L}/{i}_{j}.webp'; os.makedirs(os.path.dirname(out), exist_ok=True)
            encode(GL[j * N:j * N + N + 3, i * N:i * N + N + 3]).save(out, lossless=True, quality=100, method=6)
            keys.append(f'{i}_{j}')
    tiles[L] = keys
    if L == 1:  # Übersicht (62,5 m) für Schatten und Umgebungsverdeckung
        encode(GL).save('terrain/overview.webp', lossless=True, quality=100, method=6)
    print('Ebene', L, len(keys), 'Kacheln')
json.dump({'root': ROOT, 'n': N, 'lmax': LMAX, 'enc': 'h=(R*256+G)/50-100', 'tiles': tiles}, open('terrain/tiles.json', 'w'))
