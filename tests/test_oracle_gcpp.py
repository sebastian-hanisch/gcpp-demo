"""Unabhängiges Orakel für das verallgemeinerte Chinesische Postbotenproblem.

Orakel: ganzzahliges lineares Programm (scipy.optimize.milp) über die Durchlaufzahlen x_e >= r_e je Straße
mit der Eulerbedingung "Grad gerade" (Σ_{e∋v} x_e = 2·y_v, y_v ganzzahlig). Es kommt ohne kürzeste Wege und
ohne Matching aus, ist also ein anderer Rechenweg als die Demo (Paarung ungerader Knoten). Der Zusammenhang
folgt, weil jede Straße mindestens einmal befahren wird und das Straßennetz zusammenhängend ist.

Geprüft werden außerdem die Touren selbst: geschlossener Kantenzug auf existierenden Straßen, jede Straße
mindestens r_e-mal, Länge der Tour = Gesamtdistanz."""

import numpy as np
import pytest

pytest.importorskip("scipy")
from scipy.optimize import Bounds, LinearConstraint, milp  # noqa: E402

from gcpp_scenario import baue_strassennetz  # noqa: E402
from gcpp_solver import loese  # noqa: E402

EXAKT = "Exakt (Minimum-Weight Matching)"
GIERIG = "Gierige Paarung"
META = "Metaheuristik (Simulated Annealing)"

# (Kreuzungen, Straßen je Kreuzung, Hauptstraßen-Anteil, Seed): kleine bis mittlere Netze, dünn bis dicht
INSTANZEN = [(n, k, h, s) for s, (n, k, h) in enumerate(
    [(8, 2, 0.0), (8, 3, 0.5), (10, 2, 0.2), (12, 3, 0.1), (12, 4, 0.5), (15, 2, 0.0), (15, 5, 0.3), (18, 3, 0.2),
     (20, 6, 0.5), (24, 3, 0.2), (24, 2, 0.35), (30, 4, 0.0), (30, 3, 0.5), (36, 5, 0.25), (40, 3, 0.35), (40, 2, 0.1)]
)]


def milp_optimum(netz) -> float:
    kanten, n = netz.kanten, len(netz.knoten)
    m = len(kanten)
    laengen = np.array([netz.laenge(k) for k in kanten])
    zielfunktion = np.concatenate([laengen, np.zeros(n)])
    a = np.zeros((n, m + n))
    for j, k in enumerate(kanten):
        a[k.knoten1, j] += 1
        a[k.knoten2, j] += 1
    for v in range(n):
        a[v, m + v] = -2  # Grad = 2 * y_v  <=>  Grad gerade
    untere = np.concatenate([[k.pflichtbesuche for k in kanten], np.zeros(n)])
    obere = np.concatenate([[k.pflichtbesuche + 2 for k in kanten], np.full(n, 40)])
    r = milp(zielfunktion, constraints=LinearConstraint(a, 0, 0), integrality=np.ones(m + n), bounds=Bounds(untere, obere))
    assert r.status == 0
    return float(r.fun)


def _pruefe_tour(netz, tour):
    kanten = {frozenset({k.knoten1, k.knoten2}): k for k in netz.kanten}
    assert tour.kreis, "leere Tour"
    for (_, v1), (u2, _) in zip(tour.kreis, tour.kreis[1:]):
        assert v1 == u2
    assert tour.kreis[-1][1] == tour.kreis[0][0]
    zaehler, laenge = {}, 0.0
    for u, v in tour.kreis:
        schluessel = frozenset({u, v})
        assert schluessel in kanten, f"Straße {u}-{v} existiert nicht"
        zaehler[schluessel] = zaehler.get(schluessel, 0) + 1
        laenge += netz.laenge(kanten[schluessel])
    for schluessel, k in kanten.items():
        assert zaehler.get(schluessel, 0) >= k.pflichtbesuche
    assert laenge == pytest.approx(tour.gesamtdistanz, abs=1e-7)


@pytest.mark.parametrize("n,k,haupt,seed", INSTANZEN)
def test_touren_gegen_milp_orakel(n, k, haupt, seed):
    netz = baue_strassennetz(n, k, haupt, seed)
    optimum = milp_optimum(netz)
    touren = {m: loese(netz, m, seed) for m in (EXAKT, GIERIG, META)}
    for tour in touren.values():
        _pruefe_tour(netz, tour)
    assert touren[EXAKT].gesamtdistanz == pytest.approx(optimum, abs=1e-6)
    assert touren[GIERIG].gesamtdistanz >= optimum - 1e-6
    assert touren[META].gesamtdistanz >= optimum - 1e-6
