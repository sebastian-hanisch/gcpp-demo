import pytest

from gcpp_model import pruefe_zusammenhang
from gcpp_scenario import baue_strassennetz

GROESSEN = [8, 16, 30, 50]
DICHTEN = [2, 3, 5]


@pytest.mark.parametrize("n", GROESSEN)
@pytest.mark.parametrize("k", DICHTEN)
def test_strassennetz_ist_immer_zusammenhaengend(n, k):
    """kNN-Graphen können in seltenen Fällen in getrennte Komponenten
    zerfallen - der Generator muss das reparieren, sonst gibt es keine
    gültige Rundtour."""
    for seed in range(5):
        netz = baue_strassennetz(n, k, 0.2, seed)
        pruefe_zusammenhang(netz)  # darf nicht werfen


@pytest.mark.parametrize("n", GROESSEN)
def test_strassennetz_hat_erwartete_knotenzahl(n):
    netz = baue_strassennetz(n, 3, 0.2, seed=0)
    assert len(netz.knoten) == n


def test_anteil_hauptstrassen_wird_ungefaehr_getroffen():
    netz = baue_strassennetz(40, 3, 0.25, seed=0)
    n_haupt = sum(1 for k in netz.kanten if k.pflichtbesuche == 2)
    anteil = n_haupt / len(netz.kanten)
    assert anteil == pytest.approx(0.25, abs=0.03)


def test_anteil_null_ergibt_keine_hauptstrassen():
    netz = baue_strassennetz(30, 3, 0.0, seed=0)
    assert all(k.pflichtbesuche == 1 for k in netz.kanten)


def test_hauptstrassen_sind_die_laengsten_kanten():
    """Kernannahme des Generators: Hauptstraßen werden aus den LÄNGSTEN
    Kandidaten-Kanten gewählt (verbindende Achsen), nicht zufällig."""
    netz = baue_strassennetz(30, 3, 0.2, seed=0)
    laengen_haupt = [netz.laenge(k) for k in netz.kanten if k.pflichtbesuche == 2]
    laengen_normal = [netz.laenge(k) for k in netz.kanten if k.pflichtbesuche == 1]
    assert min(laengen_haupt) >= max(laengen_normal) - 1e-9


def test_gleicher_seed_erzeugt_dasselbe_netz():
    netz1 = baue_strassennetz(20, 3, 0.2, seed=42)
    netz2 = baue_strassennetz(20, 3, 0.2, seed=42)
    assert [(k.x, k.y) for k in netz1.knoten] == [(k.x, k.y) for k in netz2.knoten]
    assert {(k.knoten1, k.knoten2) for k in netz1.kanten} == {(k.knoten1, k.knoten2) for k in netz2.kanten}


def test_verschiedene_seeds_erzeugen_verschiedene_netze():
    netz1 = baue_strassennetz(20, 3, 0.2, seed=1)
    netz2 = baue_strassennetz(20, 3, 0.2, seed=2)
    assert [(k.x, k.y) for k in netz1.knoten] != [(k.x, k.y) for k in netz2.knoten]
