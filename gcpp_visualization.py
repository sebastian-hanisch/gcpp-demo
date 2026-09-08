"""Plotly-Visualisierungen: Netzwerkplot mit Pflicht-/Leerfahrten-Kennzeichnung,
Konvergenz- und Methodenvergleich.

Zwei Layer pro Kantengruppe: eine dünne, sichtbare Linie (Farbe/Breite
transportieren Information) und eine breite, unsichtbare "Hitbox"-Linie
direkt darüber, die den Hover-Tooltip trägt - eine dünne 2px-Linie ist ein
winziges Trefferziel für die Maus, die breite Hitbox macht das Hovern
zuverlässig, ohne die Optik zu verändern. Gleichartige Kanten werden pro
Kategorie zu EINER Trace zusammengefasst (None-getrennte Segmente) statt
einer Trace pro Kante - bei 100+ Kreuzungen sonst hunderte Einzel-Traces."""

from collections import Counter

import plotly.graph_objects as go

from gcpp_model import Netzwerk
from gcpp_solver import Tour

FARBE_PFLICHT_EINFACH = "#95a5a6"
FARBE_PFLICHT_MEHRFACH = "#2980b9"
FARBE_LEERFAHRT = "#e67e22"
HITBOX_BREITE = 16


def _groessen_skalierung(n_knoten: int) -> tuple[float, float]:
    """(Knotengröße, Basis-Linienbreite) - skaliert mit der Netzwerkgröße,
    damit auch Netze mit 100+ Kreuzungen noch lesbar bleiben."""
    knoten_groesse = max(4.0, min(11.0, 800.0 / max(n_knoten, 1)))
    linien_basis = max(0.8, min(2.2, 45.0 / max(n_knoten, 1)))
    return knoten_groesse, linien_basis


def _segmente(kanten, netzwerk: Netzwerk, text_fn=None):
    """Baut None-getrennte x/y(/hovertext)-Arrays für eine Gruppe von Kanten -
    damit lässt sich eine ganze Kategorie in EINER Scatter-Trace zeichnen."""
    xs, ys, texte = [], [], []
    for k in kanten:
        k1, k2 = netzwerk.knoten[k.knoten1], netzwerk.knoten[k.knoten2]
        xs += [k1.x, k2.x, None]
        ys += [k1.y, k2.y, None]
        if text_fn is not None:
            t = text_fn(k)
            texte += [t, t, None]
    return (xs, ys, texte) if text_fn is not None else (xs, ys)


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
    hitbox_x, hitbox_y, hitbox_text = [], [], []
    for key, farbe, breite in kategorien:
        eintraege = gruppen[key]
        if not eintraege:
            continue
        xs, ys = _segmente([e[0] for e in eintraege], netzwerk)
        fig.add_trace(
            go.Scatter(x=xs, y=ys, mode="lines", line=dict(width=breite, color=farbe), hoverinfo="skip", showlegend=False)
        )
        for kante, gesamt, extra in eintraege:
            k1, k2 = netzwerk.knoten[kante.knoten1], netzwerk.knoten[kante.knoten2]
            text = f"Straße {kante.id}: Pflicht {kante.pflichtbesuche}x, befahren {gesamt}x" + (f" (+{extra} Leerfahrt)" if extra else "")
            hitbox_x += [k1.x, k2.x, None]
            hitbox_y += [k1.y, k2.y, None]
            hitbox_text += [text, text, None]

    fig.add_trace(
        go.Scatter(
            x=hitbox_x, y=hitbox_y, mode="lines", line=dict(width=HITBOX_BREITE, color="rgba(0,0,0,0)"),
            hoverinfo="text", hovertext=hitbox_text, showlegend=False,
        )
    )
    _hinzufuegen_knoten_trace(fig, netzwerk, knoten_groesse)

    # Legenden-Dummy-Traces (echte Kanten haben showlegend=False, damit die Legende nicht mit 100+ Einträgen zumüllt).
    for name, farbe in [
        ("Wohnstraße (1x räumen)", FARBE_PFLICHT_EINFACH), ("Hauptstraße (2x räumen)", FARBE_PFLICHT_MEHRFACH),
        ("Leerfahrt (Parität)", FARBE_LEERFAHRT),
    ]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(width=4, color=farbe), name=name, hoverinfo="skip"))

    fig.update_layout(
        title=titel, xaxis=dict(scaleanchor="y", scaleratio=1, showgrid=False, zeroline=False, title="km"),
        yaxis=dict(showgrid=False, zeroline=False, title="km"), height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=20, r=20, t=50, b=20), hovermode="closest", hoverdistance=30,
    )
    return fig


def _traversierungen(tour: Tour) -> Counter:
    zaehler = Counter()
    for u, v in tour.kreis:
        zaehler[frozenset({u, v})] += 1
    return zaehler


def netzwerk_figure(netzwerk: Netzwerk, titel: str) -> go.Figure:
    fig = go.Figure()
    knoten_groesse, linien_basis = _groessen_skalierung(len(netzwerk.knoten))

    einfach = [k for k in netzwerk.kanten if k.pflichtbesuche == 1]
    mehrfach = [k for k in netzwerk.kanten if k.pflichtbesuche > 1]
    hitbox_x, hitbox_y, hitbox_text = [], [], []
    for gruppe, farbe, breite in [(einfach, FARBE_PFLICHT_EINFACH, linien_basis), (mehrfach, FARBE_PFLICHT_MEHRFACH, linien_basis * 1.6)]:
        if not gruppe:
            continue
        xs, ys = _segmente(gruppe, netzwerk)
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(width=breite, color=farbe), hoverinfo="skip", showlegend=False))
        for k in gruppe:
            k1, k2 = netzwerk.knoten[k.knoten1], netzwerk.knoten[k.knoten2]
            text = f"Straße {k.id}: {k.pflichtbesuche}x Pflichträumung"
            hitbox_x += [k1.x, k2.x, None]
            hitbox_y += [k1.y, k2.y, None]
            hitbox_text += [text, text, None]

    fig.add_trace(
        go.Scatter(
            x=hitbox_x, y=hitbox_y, mode="lines", line=dict(width=HITBOX_BREITE, color="rgba(0,0,0,0)"),
            hoverinfo="text", hovertext=hitbox_text, showlegend=False,
        )
    )
    _hinzufuegen_knoten_trace(fig, netzwerk, knoten_groesse)

    fig.update_layout(
        title=titel, xaxis=dict(scaleanchor="y", scaleratio=1, showgrid=False, zeroline=False, title="km"),
        yaxis=dict(showgrid=False, zeroline=False, title="km"), height=420,
        margin=dict(l=20, r=20, t=50, b=20), hovermode="closest", hoverdistance=30,
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
