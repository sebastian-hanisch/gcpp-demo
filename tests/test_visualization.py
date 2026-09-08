"""Strukturtests für die Hover-Hitbox-Konstruktion: Plotly hovert bei
Linien-Traces nach Distanz zum nächsten DATENPUNKT, nicht interpoliert
entlang der Strecke - eine Kante mit nur 2 Punkten (den Endpunkten) ist
daher in der Mitte praktisch nie in Hover-Reichweite, selbst mit einer
breiten Linie (live vom Nutzer bestätigt: Tooltips erschienen praktisch
nie). Die Hitbox besteht deshalb aus vielen unsichtbaren MARKER-Punkten
dicht entlang jeder Kante, siehe gcpp_visualization.py Moduldocstring."""

from gcpp_model import Kante, Knoten, Netzwerk
from gcpp_solver import loese
from gcpp_visualization import (
    HITBOX_MARKERGROESSE,
    HITBOX_PUNKTE_JE_KANTE,
    netzwerk_figure,
    tour_figure,
)


def _kleines_netz() -> Netzwerk:
    knoten = [Knoten(0, 0.0, 0.0), Knoten(1, 4.0, 0.0), Knoten(2, 2.0, 3.0), Knoten(3, 6.0, 3.0)]
    kanten = [Kante(0, 0, 1), Kante(1, 1, 2, pflichtbesuche=2), Kante(2, 2, 0), Kante(3, 1, 3)]
    return Netzwerk("Test", knoten, kanten)


def _hitbox_trace(fig):
    kandidaten = [t for t in fig.data if t.mode == "markers" and t.hoverinfo == "text" and t.marker.size == HITBOX_MARKERGROESSE]
    assert len(kandidaten) == 1, "es sollte genau eine Hitbox-Trace für alle Kanten geben"
    return kandidaten[0]


def test_tour_figure_hat_dicht_verteilte_hitbox_punkte_je_kante():
    netz = _kleines_netz()
    tour = loese(netz, "Exakt (Minimum-Weight Matching)")
    fig = tour_figure(netz, tour, "Test")
    hitbox = _hitbox_trace(fig)
    # HITBOX_PUNKTE_JE_KANTE Punkte je Kante, KEINE None-Lücken (Marker, keine Linie)
    assert len(hitbox.x) == HITBOX_PUNKTE_JE_KANTE * len(netz.kanten)
    assert all(x is not None for x in hitbox.x)
    assert all("Straße" in text for text in hitbox.hovertext)


def test_hitbox_punkte_liegen_auf_der_kante_zwischen_den_endpunkten():
    """Kernbehauptung des Fixes: es gibt Hitbox-Punkte auch in der MITTE
    einer Kante, nicht nur an den beiden Endpunkten."""
    knoten = [Knoten(0, 0.0, 0.0), Knoten(1, 10.0, 0.0)]
    kanten = [Kante(0, 0, 1)]
    netz = Netzwerk("Test", knoten, kanten)
    tour = loese(netz, "Exakt (Minimum-Weight Matching)")
    fig = tour_figure(netz, tour, "Test")
    hitbox = _hitbox_trace(fig)
    mittelpunkt_vorhanden = any(4.0 < x < 6.0 for x in hitbox.x)
    assert mittelpunkt_vorhanden


def test_netzwerk_figure_hat_dicht_verteilte_hitbox_punkte_je_kante():
    netz = _kleines_netz()
    fig = netzwerk_figure(netz, "Test")
    hitbox = _hitbox_trace(fig)
    assert len(hitbox.x) == HITBOX_PUNKTE_JE_KANTE * len(netz.kanten)


def test_sichtbare_linien_traces_haben_hover_deaktiviert():
    """Die sichtbaren, dünnen Linien dürfen KEIN eigenes Hover haben - sonst
    würde Plotly zufällig mal die Linie, mal die Hitbox für den Tooltip
    wählen, je nachdem welche näher an der Maus liegt."""
    netz = _kleines_netz()
    tour = loese(netz, "Exakt (Minimum-Weight Matching)")
    fig = tour_figure(netz, tour, "Test")
    linien_traces = [t for t in fig.data if t.mode == "lines"]
    assert linien_traces
    assert all(t.hoverinfo == "skip" for t in linien_traces)


def test_knoten_trace_zeigt_grad_im_tooltip():
    netz = _kleines_netz()
    tour = loese(netz, "Exakt (Minimum-Weight Matching)")
    fig = tour_figure(netz, tour, "Test")
    knoten_trace = next(t for t in fig.data if t.mode == "markers" and t.marker.size != HITBOX_MARKERGROESSE)
    # Knoten 1 hat 3 Kanten (zu 0, 2, 3)
    assert any("Kreuzung 1 (3 Straßen)" in text for text in knoten_trace.text)


def test_legende_liegt_unterhalb_des_plots_nicht_ueber_dem_titel():
    """Regressionstest: die Legende überlappte mit dem Titel, als sie knapp
    oberhalb der Zeichenfläche positioniert war (y=1.02) - jetzt unterhalb."""
    netz = _kleines_netz()
    tour = loese(netz, "Exakt (Minimum-Weight Matching)")
    fig = tour_figure(netz, tour, "Test")
    assert fig.layout.legend.y < 0
