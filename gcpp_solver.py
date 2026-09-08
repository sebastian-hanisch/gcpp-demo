"""Drei Lösungsverfahren für dasselbe Problem: jede Kante des Netzwerks
muss `pflichtbesuche`-mal befahren werden, gesucht ist die kürzeste
geschlossene Rundtour.

Alle drei folgen demselben Grundgerüst (Edmonds & Johnson 1973): das
"Pflicht-Multigraph" (jede Kante so oft dupliziert wie gefordert) hat i. A.
Knoten mit ungeradem Grad - eine Rundtour, die jede Kante genau einmal
nutzt, existiert nur in einem Graphen, in dem JEDER Knoten geraden Grad hat
(Satz von Euler). Also müssen Knotenpaare mit ungeradem Grad über
zusätzliche (doppelt gefahrene) kürzeste Wege verbunden werden, bis alle
Grade gerade sind ("Parität reparieren") - danach liefert ein Eulerkreis
(Hierholzer, hier `networkx.eulerian_circuit`) die Rundtour. Die drei
Verfahren unterscheiden sich NUR darin, WIE die ungeraden Knoten gepaart
werden - das isoliert die eigentliche Kernfrage der Demo: wie stark wirkt
sich optimales vs. naives Paaren auf die Leerfahrten-Distanz aus?

WICHTIG: `networkx.eulerize()` wurde bewusst NICHT verwendet - ein Blick in
den Quellcode zeigt, dass es `nx.shortest_path()` OHNE `weight=` aufruft,
also nach KantenANZAHL (Hops) statt nach echter Distanz paart. Für
Netzwerke mit unterschiedlich langen Kanten (wie hier) wäre das schlicht
falsch. Stattdessen wird hier mit `nx.min_weight_matching()` auf einem
selbst aufgebauten, gewichtsrichtigen Hilfsgraphen gearbeitet.
"""

import random
import time
from dataclasses import dataclass, field
from itertools import combinations

import networkx as nx

from gcpp_model import Netzwerk


@dataclass
class Tour:
    methode: str
    kreis: list[tuple[int, int]]  # Folge von (von, nach) - Kanten der Rundtour
    pflichtdistanz: float  # Summe aller Pflicht-Durchläufe (untere Schranke)
    leerfahrten: float  # zusätzliche (Paritäts-)Distanz über die Pflicht hinaus
    rechenzeit: float

    @property
    def gesamtdistanz(self) -> float:
        return self.pflichtdistanz + self.leerfahrten


def _pflicht_multigraph(netzwerk: Netzwerk) -> nx.MultiGraph:
    g = nx.MultiGraph()
    g.add_nodes_from(range(len(netzwerk.knoten)))
    for k in netzwerk.kanten:
        for _ in range(k.pflichtbesuche):
            g.add_edge(k.knoten1, k.knoten2)
    return g


def _ungerade_knoten(g: nx.MultiGraph) -> list[int]:
    return sorted(n for n, d in g.degree() if d % 2 == 1)


def _kuerzeste_wege_zwischen(basisgraph: nx.Graph, knoten: list[int]) -> dict[tuple[int, int], tuple[float, list[int]]]:
    wege = {}
    for u, v in combinations(knoten, 2):
        dist, pfad = nx.single_source_dijkstra(basisgraph, u, v, weight="weight")
        wege[(u, v)] = (dist, pfad)
        wege[(v, u)] = (dist, list(reversed(pfad)))
    return wege


def _paarung_exakt(knoten: list[int], wege: dict) -> list[tuple[int, int]]:
    hilfsgraph = nx.Graph()
    hilfsgraph.add_nodes_from(knoten)
    for u, v in combinations(knoten, 2):
        hilfsgraph.add_edge(u, v, weight=wege[(u, v)][0])
    matching = nx.min_weight_matching(hilfsgraph)
    return [tuple(paar) for paar in matching]


def _paarung_gierig(knoten: list[int], wege: dict, netzwerk: Netzwerk) -> list[tuple[int, int]]:
    """Nächster-Nachbar-Heuristik nach LUFTLINIE (wie ein Planer, der auf dem
    Lageplan einfach die optisch nächstgelegenen Punkte verbindet, ohne den
    tatsächlichen - ggf. deutlich längeren - Weg entlang der Stäbe
    nachzurechnen): nimm den ersten offenen Knoten, paare ihn mit dem nach
    Luftlinie NÄCHSTGELEGENEN noch offenen Knoten. Die tatsächlichen
    Leerfahrten-Kosten (über `wege`, echte kürzeste Wege im Netzwerk) können
    davon deutlich abweichen, wenn Luftlinien- und Netzwerkdistanz
    auseinanderfallen (z. B. wenn zwei Knoten räumlich nah, aber nur über
    einen Umweg durchs Tragwerk verbunden sind)."""
    def luftlinie(a: int, b: int) -> float:
        ka, kb = netzwerk.knoten[a], netzwerk.knoten[b]
        return ((ka.x - kb.x) ** 2 + (ka.y - kb.y) ** 2) ** 0.5

    offen = list(knoten)
    paare = []
    while offen:
        a = offen.pop(0)
        if not offen:
            break
        b = min(offen, key=lambda kandidat: luftlinie(a, kandidat))
        offen.remove(b)
        paare.append((a, b))
    return paare


def _paarungskosten(paare: list[tuple[int, int]], wege: dict) -> float:
    return sum(wege[paar][0] for paar in paare)


def _paarung_metaheuristik(
    knoten: list[int], wege: dict, netzwerk: Netzwerk, seed: int, iterationen: int | None = None,
) -> tuple[list[tuple[int, int]], list[float]]:
    """Simulated Annealing über den Raum aller perfekten Paarungen: startet
    bei der gierigen Paarung, tauscht zufällig Partner zwischen zwei Paaren.

    Eine einzelne Iteration ist extrem billig (Summe von Dictionary-Lookups,
    kein Solver-Aufruf) - deshalb wird das Budget mit der Anzahl ungerader
    Knoten skaliert (mehr Paare = größerer Suchraum), statt einen festen
    Wert zu verwenden, der bei größeren Straßennetzen zu früh abbricht
    (live beobachtet: bei 40 Knoten fand die Suche mit 300 Iterationen
    NIE eine bessere Paarung als die gierige, mit 10 000 traf sie exakt
    das Optimum - bei weiterhin < 0.02s Rechenzeit)."""
    if iterationen is None:
        iterationen = max(3000, 800 * len(knoten))
    rng = random.Random(seed)
    paare = _paarung_gierig(knoten, wege, netzwerk)
    beste_paare = list(paare)
    beste_kosten = _paarungskosten(paare, wege)
    kosten = beste_kosten
    verlauf = [beste_kosten]

    if len(paare) < 2:
        return beste_paare, verlauf

    for schritt in range(iterationen):
        temperatur = max(1e-6, 1.0 - schritt / iterationen)
        i, j = rng.sample(range(len(paare)), 2)
        (a, b), (c, d) = paare[i], paare[j]
        # Zwei mögliche Rekombinationen der 4 beteiligten Knoten:
        if rng.random() < 0.5:
            neu_i, neu_j = (a, c), (b, d)
        else:
            neu_i, neu_j = (a, d), (b, c)
        delta = (
            wege[neu_i][0] + wege[neu_j][0]
            - wege[(a, b)][0] - wege[(c, d)][0]
        )
        if delta < 0 or rng.random() < pow(2.718281828, -delta / (temperatur * max(beste_kosten, 1e-9))):
            paare[i], paare[j] = neu_i, neu_j
            kosten += delta
            if kosten < beste_kosten - 1e-9:
                beste_kosten = kosten
                beste_paare = list(paare)
        verlauf.append(beste_kosten)
    return beste_paare, verlauf


def _rundtour_aus_paarung(
    netzwerk: Netzwerk, pflicht_mg: nx.MultiGraph, paare: list[tuple[int, int]], wege: dict
) -> Tour:
    """Ergänzt das Pflicht-Multigraph um die (Paritäts-)Wege der Paarung und
    liefert den daraus resultierenden Eulerkreis + dessen Distanz."""
    erweitert = nx.MultiGraph(pflicht_mg)
    laengen = netzwerk.kanten_laengen_lookup()
    leerfahrten = 0.0
    for paar in paare:
        _, pfad = wege[paar]
        for u, v in zip(pfad[:-1], pfad[1:]):
            erweitert.add_edge(u, v)
            leerfahrten += laengen[frozenset({u, v})]

    if not nx.is_eulerian(erweitert):
        raise RuntimeError("Interner Fehler: Paritätsreparatur hat kein Euler-Graph erzeugt.")

    kreis = list(nx.eulerian_circuit(erweitert, source=paare[0][0] if paare else next(iter(erweitert.nodes))))
    pflichtdistanz = netzwerk.gesamtlaenge_pflicht()
    return Tour("", kreis, pflichtdistanz, leerfahrten, 0.0)


def loese(netzwerk: Netzwerk, methode: str, seed: int = 0) -> Tour:
    start = time.perf_counter()
    basisgraph = netzwerk.zu_graph()
    pflicht_mg = _pflicht_multigraph(netzwerk)
    ungerade = _ungerade_knoten(pflicht_mg)

    if not ungerade:
        tour = _rundtour_aus_paarung(netzwerk, pflicht_mg, [], {})
        tour.methode = methode
        tour.rechenzeit = time.perf_counter() - start
        return tour

    wege = _kuerzeste_wege_zwischen(basisgraph, ungerade)
    if methode == "Exakt (Minimum-Weight Matching)":
        paare = _paarung_exakt(ungerade, wege)
    elif methode == "Gierige Paarung":
        paare = _paarung_gierig(ungerade, wege, netzwerk)
    elif methode == "Metaheuristik (Simulated Annealing)":
        paare, _ = _paarung_metaheuristik(ungerade, wege, netzwerk, seed)
    else:
        raise ValueError(f"Unbekannte Methode: {methode}")

    tour = _rundtour_aus_paarung(netzwerk, pflicht_mg, paare, wege)
    tour.methode = methode
    tour.rechenzeit = time.perf_counter() - start
    return tour


def loese_alle(netzwerk: Netzwerk, seed: int = 0) -> dict[str, Tour]:
    return {
        "Gierige Paarung": loese(netzwerk, "Gierige Paarung", seed),
        "Exakt (Minimum-Weight Matching)": loese(netzwerk, "Exakt (Minimum-Weight Matching)", seed),
        "Metaheuristik (Simulated Annealing)": loese(netzwerk, "Metaheuristik (Simulated Annealing)", seed),
    }


def metaheuristik_verlauf(netzwerk: Netzwerk, seed: int = 0) -> list[float]:
    basisgraph = netzwerk.zu_graph()
    pflicht_mg = _pflicht_multigraph(netzwerk)
    ungerade = _ungerade_knoten(pflicht_mg)
    if not ungerade:
        return [0.0]
    wege = _kuerzeste_wege_zwischen(basisgraph, ungerade)
    _, verlauf = _paarung_metaheuristik(ungerade, wege, netzwerk, seed)
    return verlauf
