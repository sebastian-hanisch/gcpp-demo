"""Netzwerk-Modell für das (verallgemeinerte) Chinesische Postbotenproblem
(Route Inspection Problem): jede Kante muss eine vorgegebene Anzahl mal
befahren werden, gesucht ist die kürzeste geschlossene Rundtour, die das
erfüllt.

Nicht jede Kante braucht 1 Durchlauf - eine Kante mit `pflichtbesuche=2`
modelliert z. B. einen sicherheitskritischen Knotenpunkt, der beidseitig
geschweißt/inspiziert werden muss.
"""

from dataclasses import dataclass, field

import networkx as nx


@dataclass(frozen=True)
class Knoten:
    id: int
    x: float
    y: float


@dataclass(frozen=True)
class Kante:
    id: int
    knoten1: int
    knoten2: int
    pflichtbesuche: int = 1


@dataclass(frozen=True)
class Netzwerk:
    name: str
    knoten: list[Knoten]
    kanten: list[Kante]

    def __post_init__(self) -> None:
        n = len(self.knoten)
        for k in self.kanten:
            if not (0 <= k.knoten1 < n and 0 <= k.knoten2 < n):
                raise ValueError(f"Kante {k.id} referenziert unbekannten Knoten")
            if k.pflichtbesuche < 1:
                raise ValueError(f"Kante {k.id}: pflichtbesuche muss >= 1 sein")

    def laenge(self, kante: Kante) -> float:
        k1, k2 = self.knoten[kante.knoten1], self.knoten[kante.knoten2]
        return float(((k2.x - k1.x) ** 2 + (k2.y - k1.y) ** 2) ** 0.5)

    def gesamtlaenge_pflicht(self) -> float:
        """Summe aller Pflicht-Durchläufe (untere Schranke jeder Tour, ohne Leerfahrten)."""
        return sum(self.laenge(k) * k.pflichtbesuche for k in self.kanten)

    def zu_graph(self) -> nx.Graph:
        """Einfacher (nicht dupliziter) Graph - für Kürzeste-Wege-Berechnungen."""
        g = nx.Graph()
        g.add_nodes_from(range(len(self.knoten)))
        for k in self.kanten:
            laenge = self.laenge(k)
            if g.has_edge(k.knoten1, k.knoten2):
                g[k.knoten1][k.knoten2]["weight"] = min(g[k.knoten1][k.knoten2]["weight"], laenge)
            else:
                g.add_edge(k.knoten1, k.knoten2, weight=laenge)
        return g

    def kanten_laengen_lookup(self) -> dict[frozenset, float]:
        return {frozenset({k.knoten1, k.knoten2}): self.laenge(k) for k in self.kanten}


class UnzusammenhaengendesNetzwerk(Exception):
    pass


def pruefe_zusammenhang(netzwerk: Netzwerk) -> None:
    g = netzwerk.zu_graph()
    if len(netzwerk.knoten) > 0 and not nx.is_connected(g):
        raise UnzusammenhaengendesNetzwerk(
            "Netzwerk ist nicht zusammenhängend - eine geschlossene Rundtour über alle Kanten ist unmöglich."
        )
