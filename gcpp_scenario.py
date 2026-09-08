"""Synthetisches Straßennetz für die Winterdienst-Demo: zufällig gestreute
Kreuzungen, verbunden mit ihren k nächsten Nachbarn (dasselbe Prinzip wie
das Straßennetz in vrp_demo) - realistischer und variabler als ein
starres Raster, insbesondere weil Luftlinien- und Netzwerkdistanz hier
öfter auseinanderfallen (Umwege um nicht direkt verbundene Kreuzungen)."""

import networkx as nx
import numpy as np

from gcpp_model import Kante, Knoten, Netzwerk

GEBIETSGROESSE_KM = 6.0


def baue_strassennetz(n_kreuzungen: int, k_nachbarn: int, anteil_hauptstrassen: float, seed: int) -> Netzwerk:
    rng = np.random.default_rng(seed)
    punkte = rng.uniform(0.3, GEBIETSGROESSE_KM - 0.3, size=(n_kreuzungen, 2))

    g = nx.Graph()
    for i, (x, y) in enumerate(punkte):
        g.add_node(i, pos=(float(x), float(y)))

    k = max(2, min(k_nachbarn, n_kreuzungen - 1))
    for i in range(n_kreuzungen):
        abstaende = np.linalg.norm(punkte - punkte[i], axis=1)
        naechste = np.argsort(abstaende)[1 : k + 1]
        for j in naechste:
            j = int(j)
            if not g.has_edge(i, j):
                g.add_edge(i, j, weight=float(abstaende[j]))

    # Zusammenhang sicherstellen (kNN-Graphen können in seltene, getrennte
    # Teilnetze zerfallen) - verbinde jeweils die beiden nächstgelegenen
    # Kreuzungen zwischen den Komponenten, bis alles zusammenhängt.
    while not nx.is_connected(g):
        komponenten = list(nx.connected_components(g))
        komp_a, komp_b = komponenten[0], komponenten[1]
        bester = None
        for a in komp_a:
            diffs = np.linalg.norm(punkte[list(komp_b)] - punkte[a], axis=1)
            idx = int(np.argmin(diffs))
            b = list(komp_b)[idx]
            dist = float(diffs[idx])
            if bester is None or dist < bester[0]:
                bester = (dist, a, b)
        g.add_edge(bester[1], bester[2], weight=bester[0])

    # Hauptstraßen (Priorität, 2x Räumdienst pro Schicht): die längsten
    # Verbindungen - realistisch, weil Hauptverkehrsadern in einem zufällig
    # gestreuten Straßennetz meist die weiter voneinander entfernten
    # Kreuzungen/Stadtteile verbinden, während kurze Kanten eher
    # Wohnstraßen innerhalb eines Blocks sind.
    alle_kanten = list(g.edges(data=True))
    nach_laenge = sorted(alle_kanten, key=lambda e: -e[2]["weight"])
    n_haupt = round(anteil_hauptstrassen * len(alle_kanten))
    haupt_menge = {(min(a, b), max(a, b)) for a, b, _ in nach_laenge[:n_haupt]}

    knoten = [Knoten(i, float(x), float(y)) for i, (x, y) in enumerate(punkte)]
    kanten = []
    for idx, (a, b, _) in enumerate(alle_kanten):
        pflicht = 2 if (min(a, b), max(a, b)) in haupt_menge else 1
        kanten.append(Kante(idx, a, b, pflichtbesuche=pflicht))

    return Netzwerk("Straßennetz", knoten, kanten)
