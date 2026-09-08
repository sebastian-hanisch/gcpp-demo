import pytest

from gcpp_model import Kante, Knoten, Netzwerk
from gcpp_scenario import baue_strassennetz
from gcpp_solver import (
    _kuerzeste_wege_zwischen,
    _pflicht_multigraph,
    _ungerade_knoten,
    loese,
    loese_alle,
)

# Kleine Instanzen (wenige ungerade Knoten) - hält die Brute-Force-Kreuzprobe schnell.
KLEINE_SZENARIEN = [(8, 2, 0), (8, 3, 1), (10, 2, 2), (10, 3, 3)]


def _alle_perfekten_paarungen(knoten):
    if not knoten:
        yield []
        return
    a = knoten[0]
    rest = knoten[1:]
    for i, b in enumerate(rest):
        uebrig = rest[:i] + rest[i + 1 :]
        for teilpaarung in _alle_perfekten_paarungen(uebrig):
            yield [(a, b)] + teilpaarung


def _brute_force_optimum(netzwerk: Netzwerk) -> float:
    basisgraph = netzwerk.zu_graph()
    mg = _pflicht_multigraph(netzwerk)
    ungerade = _ungerade_knoten(mg)
    if not ungerade:
        return 0.0
    wege = _kuerzeste_wege_zwischen(basisgraph, ungerade)
    return min(
        sum(wege[paar][0] for paar in paarung) for paarung in _alle_perfekten_paarungen(ungerade)
    )


@pytest.mark.parametrize("n,k,seed", KLEINE_SZENARIEN)
def test_exakte_methode_stimmt_mit_brute_force_ueberein(n, k, seed):
    netz = baue_strassennetz(n, k, 0.2, seed)
    exakt = loese(netz, "Exakt (Minimum-Weight Matching)")
    erwartet = _brute_force_optimum(netz)
    assert exakt.leerfahrten == pytest.approx(erwartet, abs=1e-6)


@pytest.mark.parametrize("n,k,seed", KLEINE_SZENARIEN + [(20, 3, 0), (30, 4, 1)])
def test_exakt_ist_nie_schlechter_als_gierig(n, k, seed):
    netz = baue_strassennetz(n, k, 0.2, seed)
    ergebnisse = loese_alle(netz, seed=seed)
    assert ergebnisse["Exakt (Minimum-Weight Matching)"].leerfahrten <= ergebnisse["Gierige Paarung"].leerfahrten + 1e-9


def test_zufaelliges_strassennetz_zeigt_eine_echte_luecke():
    """Kernbehauptung der Demo: bei einem unregelmäßigen, zufällig erzeugten
    Straßennetz ist die gierige (Luftlinien-)Paarung nachweisbar schlechter
    als die exakte - hier bei einem konkret geprüften Seed mit >50% Rückstand
    (per Sweep über mehrere Netzgrößen als zuverlässig auftretend bestätigt,
    siehe project-arc-routing-demo-venv memory)."""
    netz = baue_strassennetz(12, 3, 0.1, seed=4)
    ergebnisse = loese_alle(netz, seed=4)
    gierig = ergebnisse["Gierige Paarung"].leerfahrten
    exakt = ergebnisse["Exakt (Minimum-Weight Matching)"].leerfahrten
    assert gierig > exakt * 1.5


@pytest.mark.parametrize("n,k,seed", KLEINE_SZENARIEN)
def test_tour_befaehrt_jede_kante_mindestens_pflichtbesuche_mal(n, k, seed):
    netz = baue_strassennetz(n, k, 0.2, seed)
    tour = loese(netz, "Exakt (Minimum-Weight Matching)")
    zaehler = {}
    for u, v in tour.kreis:
        key = frozenset({u, v})
        zaehler[key] = zaehler.get(key, 0) + 1
    for kante in netz.kanten:
        key = frozenset({kante.knoten1, kante.knoten2})
        assert zaehler.get(key, 0) >= kante.pflichtbesuche


@pytest.mark.parametrize("n,k,seed", KLEINE_SZENARIEN)
def test_tour_ist_ein_geschlossener_kreis(n, k, seed):
    netz = baue_strassennetz(n, k, 0.2, seed)
    tour = loese(netz, "Exakt (Minimum-Weight Matching)")
    if not tour.kreis:
        return
    for (u1, v1), (u2, v2) in zip(tour.kreis, tour.kreis[1:]):
        assert v1 == u2
    assert tour.kreis[-1][1] == tour.kreis[0][0]


def test_bereits_eulerscher_graph_braucht_keine_leerfahrten():
    knoten = [Knoten(0, 0.0, 0.0), Knoten(1, 3.0, 0.0), Knoten(2, 1.5, 2.6)]
    kanten = [Kante(0, 0, 1), Kante(1, 1, 2), Kante(2, 2, 0)]
    netz = Netzwerk("Dreieck", knoten, kanten)
    for methode in ["Gierige Paarung", "Exakt (Minimum-Weight Matching)", "Metaheuristik (Simulated Annealing)"]:
        tour = loese(netz, methode)
        assert tour.leerfahrten == pytest.approx(0.0)


def test_metaheuristik_erreicht_optimum_bei_kleinen_instanzen():
    netz = baue_strassennetz(12, 3, 0.1, seed=4)
    exakt = loese(netz, "Exakt (Minimum-Weight Matching)").leerfahrten
    beste_meta = min(loese(netz, "Metaheuristik (Simulated Annealing)", seed=s).leerfahrten for s in range(10))
    assert beste_meta == pytest.approx(exakt, abs=1e-6)


def test_metaheuristik_bleibt_bei_grossen_netzen_nah_am_optimum():
    """Regressionstest: mit einem linear statt quadratisch skalierten
    Iterationsbudget blieb die Metaheuristik bei 200 Kreuzungen (~100
    ungerade Knoten) exakt bei der gierigen Lösung stehen (155% über dem
    Optimum) - das Budget muss mit dem Quadrat der ungeraden Knotenzahl
    wachsen, nicht linear (siehe `_paarung_metaheuristik`-Docstring)."""
    netz = baue_strassennetz(200, 3, 0.2, seed=0)
    ergebnisse = loese_alle(netz, seed=0)
    exakt = ergebnisse["Exakt (Minimum-Weight Matching)"].leerfahrten
    meta = ergebnisse["Metaheuristik (Simulated Annealing)"].leerfahrten
    assert meta <= exakt * 1.1
