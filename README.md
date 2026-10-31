# Pfälzerwald Relief

Ein 3D-Reliefmodell des Pfälzerwalds im Browser, ausgeschnitten an der Grenze des Naturraums. Die Schnittkanten zeigen den Gesteinsaufbau bis 600 m unter dem Meeresspiegel.

**Live:** https://cdapproach.github.io/pfaelzerwald/

- Gelände aus dem 1-m-Laserscan-Modell von Rheinland-Pfalz, auf bis zu 7,8 m vereinfacht und je nach Zoomstufe nachgeladen
- Zuschaltbares Luftbild (DOP20), aus der Nähe mit etwa 2 m pro Pixel
- Gesteinsschichten vom Grundgebirge bis zum Oberen Buntsandstein und Bodenprofile (Podsol, Braunerde), mit Infos zu Material, Eigenschaften und Entstehung
- Zwölf Burgen mit Geschichte, dazu Gipfel und Orte
- Schnitt durch das Modell, Sonnenstand, Überhöhung, Geologie-Ansicht
- Navigation wie in Google Earth: Ziehen verschiebt, rechte Maustaste oder Umschalt + Ziehen dreht und neigt, Scrollen zoomt zum Mauszeiger

## Lokal starten

Die Seite lädt ihre Daten per `fetch`, deshalb braucht sie einen kleinen Webserver:

```bash
python3 -m http.server 8000
```

Danach http://localhost:8000 öffnen. three.js und die Schriften kommen von CDNs, der Rest liegt im Repo.

## Aufbau

| Pfad | Inhalt |
|---|---|
| `index.html` | die ganze Anwendung (three.js 0.160, eigene Shader) |
| `meta.json` | Projektion und Grenzpolygon in lokalen Kilometern |
| `terrain/` | Höhenkacheln als Quadtree, Ebenen 0–4, plus `overview.webp` und `tiles.json` |
| `sat/` | Luftbildkacheln: `0`–`3` je Kachel, `4` je 2×2 Kacheln der feinsten Ebene, `5` die 2-m-Bilder |
| `tools/` | Python-Skripte, mit denen alle Daten neu erzeugt werden können |

Die Schichtgrenzen sind ein vereinfachtes geologisches Modell (sanft nach Westen geneigt, um Albersweiler aufgewölbt, nach Norden ansteigend). Es zeigt das Prinzip, nicht jede Verwerfung.

## Daten neu erzeugen

Benötigt Python 3 mit `numpy`, `scipy`, `matplotlib` und `Pillow` (mit WebP). Im Projektordner ausführen:

```bash
python3 tools/build_boundary.py
```

```bash
python3 tools/build_terrain.py
```

```bash
python3 tools/build_aerial.py
```

## Quellen und Lizenzen

- **Gelände:** Digitales Geländemodell Gitterweite 1 m, ©GeoBasis-DE / LVermGeoRP 2025, [dl-de/by-2-0](https://www.govdata.de/dl-de/by-2-0), aufbereitet über [Mapterhorn](https://mapterhorn.com) [Daten bearbeitet: auf 7,8–125 m vereinfacht]
- **Luftbild:** DOP20, ©GeoBasis-DE / LVermGeoRP 2026, [dl-de/by-2-0](https://www.govdata.de/dl-de/by-2-0), http://www.lvermgeo.rlp.de [Daten bearbeitet: verkleinert auf 2–125 m pro Pixel]
- **Naturraumgrenze, Burg- und Gipfelpositionen:** © [OpenStreetMap-Mitwirkende](https://www.openstreetmap.org/copyright), ODbL
- **Burgdaten und geologische Übersicht:** nach Wikipedia-Artikeln zum Pfälzerwald und zu den einzelnen Burgen
