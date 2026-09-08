"""Strukturtests für die Hover-Hitbox-Konstruktion: eine dünne (2-4px)
sichtbare Linie ist ein winziges Trefferziel für die Maus - die Fixes hier
stellen sicher, dass jede Kante trotzdem über eine breite, unsichtbare
Hilfslinie zuverlässig anhoverbar bleibt (siehe gcpp_visualization.py
Moduldocstring)."""

from gcpp_model import Kante, Knoten, Netzwerk
from gcpp_solver import loese
from gcpp_visualization import HITBOX_BREITE, netzwerk_figure, tour_figure


def _kleines_netz() -> Netzwerk:
    knoten = [Knoten(0, 0.0, 0.0), Knoten(1, 4.0, 0.0), Knoten(2, 2.0, 3.0), Knoten(3, 6.0, 3.0)]
    kanten = [Kante(0, 0, 1), Kante(1, 1, 2, pflichtbesuche=2), Kante(2, 2, 0), Kante(3, 1, 3)]
    return Netzwerk("Test", knoten, kanten)


def _hitbox_trace(fig):
    kandidaten = [t for t in fig.data if t.mode == "lines" and t.hoverinfo == "text"]
    assert len(kandidaten) == 1, "es sollte genau eine Hitbox-Trace für alle Kanten geben"
    return kandidaten[0]


def test_tour_figure_hat_breite_hitbox_fuer_jede_kante():
    netz = _kleines_netz()
    tour = loese(netz, "Exakt (Minimum-Weight Matching)")
    fig = tour_figure(netz, tour, "Test")
    hitbox = _hitbox_trace(fig)
    assert hitbox.line.width == HITBOX_BREITE
    # 3 Punkte (x1, x2, None) je Kante
    assert len(hitbox.x) == 3 * len(netz.kanten)
    assert all(text is None or "Straße" in text for text in hitbox.hovertext)


def test_netzwerk_figure_hat_breite_hitbox_fuer_jede_kante():
    netz = _kleines_netz()
    fig = netzwerk_figure(netz, "Test")
    hitbox = _hitbox_trace(fig)
    assert hitbox.line.width == HITBOX_BREITE
    assert len(hitbox.x) == 3 * len(netz.kanten)


def test_sichtbare_linien_traces_haben_hover_deaktiviert():
    """Die sichtbaren, dünnen Linien dürfen KEIN eigenes Hover haben - sonst
    würde Plotly zufällig mal die dünne, mal die breite Trace für den
    Tooltip wählen, je nachdem welche näher an der Maus liegt."""
    netz = _kleines_netz()
    tour = loese(netz, "Exakt (Minimum-Weight Matching)")
    fig = tour_figure(netz, tour, "Test")
    linien_traces = [t for t in fig.data if t.mode == "lines" and t.line.width != HITBOX_BREITE]
    assert linien_traces
    assert all(t.hoverinfo == "skip" for t in linien_traces)


def test_knoten_trace_zeigt_grad_im_tooltip():
    netz = _kleines_netz()
    tour = loese(netz, "Exakt (Minimum-Weight Matching)")
    fig = tour_figure(netz, tour, "Test")
    knoten_trace = next(t for t in fig.data if t.mode == "markers")
    # Knoten 1 hat 3 Kanten (zu 0, 2, 3)
    assert any("Kreuzung 1 (3 Straßen)" in text for text in knoten_trace.text)
