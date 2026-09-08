import pytest

from gcpp_model import Kante, Knoten, Netzwerk, UnzusammenhaengendesNetzwerk, pruefe_zusammenhang


def test_laenge_ist_euklidischer_abstand():
    knoten = [Knoten(0, 0.0, 0.0), Knoten(1, 3.0, 4.0)]
    kanten = [Kante(0, 0, 1)]
    netz = Netzwerk("Test", knoten, kanten)
    assert netz.laenge(kanten[0]) == pytest.approx(5.0)


def test_pflichtbesuche_muss_mindestens_eins_sein():
    knoten = [Knoten(0, 0.0, 0.0), Knoten(1, 1.0, 0.0)]
    with pytest.raises(ValueError):
        Netzwerk("Test", knoten, [Kante(0, 0, 1, pflichtbesuche=0)])


def test_unbekannter_knoten_wird_erkannt():
    knoten = [Knoten(0, 0.0, 0.0)]
    with pytest.raises(ValueError):
        Netzwerk("Test", knoten, [Kante(0, 0, 5)])


def test_unzusammenhaengendes_netzwerk_wird_erkannt():
    knoten = [Knoten(0, 0.0, 0.0), Knoten(1, 1.0, 0.0), Knoten(2, 5.0, 5.0), Knoten(3, 6.0, 5.0)]
    kanten = [Kante(0, 0, 1), Kante(1, 2, 3)]
    netz = Netzwerk("Test", knoten, kanten)
    with pytest.raises(UnzusammenhaengendesNetzwerk):
        pruefe_zusammenhang(netz)


def test_zu_graph_nimmt_kuerzere_kante_bei_parallelen_kanten():
    knoten = [Knoten(0, 0.0, 0.0), Knoten(1, 1.0, 0.0)]
    kanten = [Kante(0, 0, 1)]
    netz = Netzwerk("Test", knoten, kanten)
    g = netz.zu_graph()
    assert g[0][1]["weight"] == pytest.approx(1.0)
