"""Plotly-Visualisierungen: Netzwerkplot mit Pflicht-/Leerfahrten-Kennzeichnung,
Konvergenz- und Methodenvergleich.

Zwei Layer pro Kantengruppe: eine dünne, sichtbare Linie (Farbe/Breite
transportieren Information) und eine unsichtbare "Hitbox" aus dicht entlang
jeder Kante VERTEILTEN PUNKTEN (nicht: einer breiten Linie!), die den
Hover-Tooltip trägt. Plotly hovert bei Linien-Traces nach Distanz zum
NÄCHSTEN DATENPUNKT, nicht interpoliert entlang der Strecke dazwischen -
eine Kante hat aber nur 2 Punkte (die Endpunkte), sodass die Mitte einer
längeren Kante selbst mit einer breiten Linie nie in Hover-Reichweite eines
Punktes lag (live vom Nutzer bestätigt: Tooltips erschienen praktisch nie).
Viele Zwischenpunkte pro Kante lösen das, weil Marker-Hover verlässlich
punktbasiert funktioniert. Gleichartige Kanten werden pro Kategorie zu
EINER sichtbaren Trace zusammengefasst (None-getrennte Segmente) statt
einer Trace pro Kante - bei 100+ Kreuzungen sonst hunderte Einzel-Traces."""

from collections import Counter

import numpy as np
import plotly.graph_objects as go

from gcpp_model import Netzwerk
from gcpp_solver import Tour

FARBE_PFLICHT_EINFACH = "#95a5a6"
FARBE_PFLICHT_MEHRFACH = "#2980b9"
FARBE_LEERFAHRT = "#e67e22"
HITBOX_PUNKTE_JE_KANTE = 8
HITBOX_MARKERGROESSE = 14


def _groessen_skalierung(n_knoten: int) -> tuple[float, float]:
    """(Knotengröße, Basis-Linienbreite) - skaliert mit der Netzwerkgröße,
    damit auch Netze mit 100+ Kreuzungen noch lesbar bleiben."""
    knoten_groesse = max(4.0, min(11.0, 800.0 / max(n_knoten, 1)))
    linien_basis = max(0.8, min(2.2, 45.0 / max(n_knoten, 1)))
    return knoten_groesse, linien_basis


def _segmente(kanten, netzwerk: Netzwerk):
    """Baut None-getrennte x/y-Arrays für eine Gruppe von Kanten - damit
    lässt sich eine ganze Kategorie in EINER sichtbaren Scatter-Trace zeichnen."""
    xs, ys = [], []
    for k in kanten:
        k1, k2 = netzwerk.knoten[k.knoten1], netzwerk.knoten[k.knoten2]
        xs += [k1.x, k2.x, None]
        ys += [k1.y, k2.y, None]
    return xs, ys


def _hitbox_trace(kanten, netzwerk: Netzwerk, text_fn) -> go.Scatter:
    """Unsichtbare Marker-Punkte dicht entlang jeder Kante verteilt - siehe
    Moduldocstring, warum das (statt einer breiten Linie) nötig ist."""
    xs, ys, texte = [], [], []
    t_werte = np.linspace(0.0, 1.0, HITBOX_PUNKTE_JE_KANTE)
    for k in kanten:
        k1, k2 = netzwerk.knoten[k.knoten1], netzwerk.knoten[k.knoten2]
        text = text_fn(k)
        for t in t_werte:
            xs.append(k1.x + t * (k2.x - k1.x))
            ys.append(k1.y + t * (k2.y - k1.y))
            texte.append(text)
    return go.Scatter(
        x=xs, y=ys, mode="markers", marker=dict(size=HITBOX_MARKERGROESSE, color="rgba(0,0,0,0)"),
        hoverinfo="text", hovertext=texte, showlegend=False,
    )


def _knoten_grade(netzwerk: Netzwerk) -> dict[int, int]:
    grade = {k.id: 0 for k in netzwerk.knoten}
    for kante in netzwerk.kanten:
        grade[kante.knoten1] += 1
        grade[kante.knoten2] += 1
    return grade


def _hinzufuegen_knoten_trace(fig: go.Figure, netzwerk: Netzwerk, knoten_groesse: float) -> None:
    grade = _knoten_grade(netzwerk)
    fig.add_trace(
        go.Scatter(
            x=[k.x for k in netzwerk.knoten], y=[k.y for k in netzwerk.knoten], mode="markers",
            marker=dict(size=knoten_groesse, color="#2c3e50", line=dict(width=1, color="white")),
            hoverinfo="text",
            text=[f"Kreuzung {k.id} ({grade[k.id]} Straßen)" for k in netzwerk.knoten],
            showlegend=False,
        )
    )


def _traversierungen(tour: Tour) -> Counter:
    zaehler = Counter()
    for u, v in tour.kreis:
        zaehler[frozenset({u, v})] += 1
    return zaehler


def tour_figure(netzwerk: Netzwerk, tour: Tour, titel: str) -> go.Figure:
    fig = go.Figure()
    traversiert = _traversierungen(tour)
    knoten_groesse, linien_basis = _groessen_skalierung(len(netzwerk.knoten))

    gruppen: dict[str, list] = {"einfach": [], "mehrfach": [], "leerfahrt": []}
    for k in netzwerk.kanten:
        gesamt = traversiert.get(frozenset({k.knoten1, k.knoten2}), 0)
        extra = max(0, gesamt - k.pflichtbesuche)
        if extra > 0:
            gruppen["leerfahrt"].append((k, gesamt, extra))
        elif k.pflichtbesuche > 1:
            gruppen["mehrfach"].append((k, gesamt, extra))
        else:
            gruppen["einfach"].append((k, gesamt, extra))

    kategorien = [
        ("einfach", FARBE_PFLICHT_EINFACH, linien_basis),
        ("mehrfach", FARBE_PFLICHT_MEHRFACH, linien_basis * 1.6),
        ("leerfahrt", FARBE_LEERFAHRT, linien_basis * 1.8),
    ]
    text_lookup = {}
    for key, farbe, breite in kategorien:
        eintraege = gruppen[key]
        if not eintraege:
            continue
        xs, ys = _segmente([e[0] for e in eintraege], netzwerk)
        fig.add_trace(
            go.Scatter(x=xs, y=ys, mode="lines", line=dict(width=breite, color=farbe), hoverinfo="skip", showlegend=False)
        )
        for kante, gesamt, extra in eintraege:
            text_lookup[kante.id] = f"Straße {kante.id}: Pflicht {kante.pflichtbesuche}x, befahren {gesamt}x" + (f" (+{extra} Leerfahrt)" if extra else "")

    fig.add_trace(_hitbox_trace(netzwerk.kanten, netzwerk, lambda k: text_lookup[k.id]))
    _hinzufuegen_knoten_trace(fig, netzwerk, knoten_groesse)

    # Legenden-Dummy-Traces (echte Kanten haben showlegend=False, damit die Legende nicht mit 100+ Einträgen zumüllt).
    for name, farbe in [
        ("Wohnstraße (1x räumen)", FARBE_PFLICHT_EINFACH), ("Hauptstraße (2x räumen)", FARBE_PFLICHT_MEHRFACH),
        ("Leerfahrt (Parität)", FARBE_LEERFAHRT),
    ]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(width=4, color=farbe), name=name, hoverinfo="skip"))

    fig.update_layout(
        title=titel, xaxis=dict(scaleanchor="y", scaleratio=1, showgrid=False, zeroline=False, title="km"),
        yaxis=dict(showgrid=False, zeroline=False, title="km"), height=560,
        legend=dict(orientation="h", yanchor="top", y=-0.12, x=0.5, xanchor="center"),
        margin=dict(l=20, r=20, t=50, b=70), hovermode="closest",
    )
    return fig


def netzwerk_figure(netzwerk: Netzwerk, titel: str) -> go.Figure:
    fig = go.Figure()
    knoten_groesse, linien_basis = _groessen_skalierung(len(netzwerk.knoten))

    einfach = [k for k in netzwerk.kanten if k.pflichtbesuche == 1]
    mehrfach = [k for k in netzwerk.kanten if k.pflichtbesuche > 1]
    for gruppe, farbe, breite in [(einfach, FARBE_PFLICHT_EINFACH, linien_basis), (mehrfach, FARBE_PFLICHT_MEHRFACH, linien_basis * 1.6)]:
        if not gruppe:
            continue
        xs, ys = _segmente(gruppe, netzwerk)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(width=breite, color=farbe), hoverinfo="skip", showlegend=False))

    fig.add_trace(_hitbox_trace(netzwerk.kanten, netzwerk, lambda k: f"Straße {k.id}: {k.pflichtbesuche}x Pflichträumung"))
    _hinzufuegen_knoten_trace(fig, netzwerk, knoten_groesse)

    fig.update_layout(
        title=titel, xaxis=dict(scaleanchor="y", scaleratio=1, showgrid=False, zeroline=False, title="km"),
        yaxis=dict(showgrid=False, zeroline=False, title="km"), height=420,
        margin=dict(l=20, r=20, t=50, b=20), hovermode="closest",
    )
    return fig


def konvergenz_figure(verlauf: list[float]) -> go.Figure:
    fig = go.Figure(go.Scatter(x=list(range(1, len(verlauf) + 1)), y=verlauf, mode="lines"))
    fig.update_layout(
        title="Konvergenz der Metaheuristik: beste Leerfahrten-Distanz je Iteration",
        xaxis_title="Iteration", yaxis_title="Leerfahrten [km]", height=340,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def vergleich_balken_figure(touren: dict[str, Tour]) -> go.Figure:
    labels = list(touren.keys())
    leer = [touren[l].leerfahrten for l in labels]
    fig = go.Figure(go.Bar(x=labels, y=leer, marker_color="#e67e22", text=[f"{v:.1f} km" for v in leer], textposition="outside"))
    fig.update_layout(title="Leerfahrten-Distanz je Methode", yaxis_title="Leerfahrten [km]", height=360, margin=dict(l=20, r=20, t=50, b=20))
    return fig
