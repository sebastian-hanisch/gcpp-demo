# 🚜 Winterdienst-Tourenplanung

Interaktive Demo zum (verallgemeinerten) Chinesischen Postbotenproblem: Ein Räumfahrzeug muss in seinem Bezirk jede Straße mindestens einmal räumen — Hauptstraßen sogar zweimal pro Schicht. Gesucht ist die kürzeste geschlossene Rundtour, die das erfüllt.

## Worum geht's?

Logistik-Anwendung des Eulerpfad-Klassikers "Haus vom Nikolaus" (dort: jede Kante genau 1x) auf beliebige Pflicht-Häufigkeiten je Straße — in der Literatur das **Chinesische Postbotenproblem** (Route Inspection Problem). Dieselbe Modellierung passt auf Straßenreinigung, Briefzustellung oder Zählerablesung — überall dort, wo ein Fahrzeug jede Kante eines Netzwerks bedienen muss, statt nur bestimmte Punkte anzufahren (der Unterschied zum klassischen Fahrzeugrouting in `vrp_demo`).

Kernthema der Demo: Anders als die meisten Tourenplanungsprobleme in diesem Portfolio (z. B. `vrp_demo`) ist dieses Problem — alle Straßen sind Pflicht — **polynomiell exakt lösbar** (Edmonds & Johnson 1973). Der Trick steckt allein darin, wie man die Kreuzungen mit ungerader Straßenanzahl paart, um das Netzwerk "eulersch" zu machen. Eine naive Paarung nach Luftlinie kann dabei deutlich schlechter sein als die mathematisch optimale Paarung — bei den zufällig gestreuten Straßennetzen dieser Demo tritt das schon bei kleinen bis mittleren Bezirksgrößen zuverlässig auf.

Schwesterdemo zu [arc-routing-demo](https://github.com/sebastian-hanisch/arc-routing-demo) (dasselbe Lösungsverfahren, aber mit festen, aus der Strukturoptimierungs-Linie übernommenen Netzen statt frei einstellbarer Problemgröße) und Gegenstück zu [vrp_demo](https://github.com/sebastian-hanisch/vrp_demo) im Sinne von Kantenrouting (jede Straße bedienen) vs. Knotenrouting (bestimmte Stopps anfahren).

## Methodik

- **Einstellbare Problemgröße** (wie in `vrp_demo`): Anzahl Kreuzungen, Netzdichte (Straßen je Kreuzung) und Anteil Hauptstraßen sind frei per Slider wählbar, das Straßennetz wird für jeden Zufalls-Seed neu erzeugt — keine festen, benannten Szenarien
- Straßennetz-Generator: zufällig gestreute Kreuzungen, verbunden mit ihren k nächsten Nachbarn (dasselbe Erzeugungsprinzip wie das Hintergrundnetz in `vrp_demo`) — realistischer und variabler als ein starres Raster, insbesondere weil Luftlinien- und Netzwerkdistanz hier öfter auseinanderfallen
- Gemeinsames algorithmisches Gerüst (Edmonds & Johnson 1973) für alle drei Methoden: Pflicht-Multigraph aufbauen, Kreuzungen mit ungerader Straßenanzahl bestimmen, kürzeste Wege dazwischen berechnen, Paarung wählen, Eulerkreis (Hierholzer) extrahieren — die Methoden unterscheiden sich nur in der Paarungsstrategie
- Drei Lösungsverfahren: gierige Paarung nach Luftliniendistanz, exaktes Minimum-Weight Perfect Matching (`networkx.min_weight_matching` auf einem selbst aufgebauten, gewichtsrichtigen Hilfsgraphen — bewusst NICHT `networkx.eulerize()`, das nach Kantenanzahl statt echter Distanz paart), Metaheuristik (Simulated Annealing über den Paarungsraum, Iterationsbudget skaliert mit der Anzahl ungerader Kreuzungen)
- Brute-Force-Kreuzcheck in den Tests: die exakte Methode wird gegen die vollständige Enumeration aller perfekten Paarungen verifiziert
- PDF-Export, Permalink
- Mathematische Herleitung (inkl. Beweis der Optimalität über die Matching-Formulierung) im Expander „Mathematische Formulierung“

## Lokal ausführen

```bash
pip install -r requirements-dev.txt
streamlit run app.py
```

Tests: `pytest tests/ -v`

---

Teil des [Operations-Research-Demo-Portfolios](https://sebastianhanisch.net/demos.html) von [Sebastian Hanisch](https://sebastianhanisch.net) — Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html).
