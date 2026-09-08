"""Plotly-Visualisierungen: Netzwerkplot mit Pflicht-/Leerfahrten-Kennzeichnung,
Konvergenz- und Methodenvergleich."""

from collections import Counter

import plotly.graph_objects as go

from gcpp_model import Netzwerk
from gcpp_solver import Tour

FARBE_PFLICHT_EINFACH = "#7f8c8d"
FARBE_PFLICHT_MEHRFACH = "#2c3e50"
FARBE_LEERFAHRT = "#e67e22"


def _traversierungen(tour: Tour) -> Counter:
    zaehler = Counter()
    for u, v in tour.kreis:
        zaehler[frozenset({u, v})] += 1
    return zaehler


def tour_figure(netzwerk: Netzwerk, tour: Tour, titel: str) -> go.Figure:
    fig = go.Figure()
    traversiert = _traversierungen(tour)

    for k in netzwerk.kanten:
        k1, k2 = netzwerk.knoten[k.knoten1], netzwerk.knoten[k.knoten2]
        gesamt = traversiert.get(frozenset({k.knoten1, k.knoten2}), 0)
        extra = max(0, gesamt - k.pflichtbesuche)
        farbe = FARBE_LEERFAHRT if extra > 0 else (FARBE_PFLICHT_MEHRFACH if k.pflichtbesuche > 1 else FARBE_PFLICHT_EINFACH)
        breite = 2.0 + 3.0 * gesamt
        fig.add_trace(
            go.Scatter(
                x=[k1.x, k2.x], y=[k1.y, k2.y], mode="lines",
                line=dict(width=breite, color=farbe), hoverinfo="text",
                text=f"Straße {k.id}: Pflicht {k.pflichtbesuche}x, befahren {gesamt}x" + (f" (+{extra} Leerfahrt)" if extra else ""),
                showlegend=False,
            )
        )

    fig.add_trace(
        go.Scatter(
            x=[k.x for k in netzwerk.knoten], y=[k.y for k in netzwerk.knoten], mode="markers",
            marker=dict(size=10, color="#333333"), hoverinfo="skip", showlegend=False,
        )
    )
    # Legenden-Dummy-Traces (echte Kanten haben showlegend=False, damit die Legende nicht mit 20+ Einträgen zumüllt).
    for name, farbe in [
        ("Wohnstraße (1x räumen)", FARBE_PFLICHT_EINFACH), ("Hauptstraße (2x räumen)", FARBE_PFLICHT_MEHRFACH),
        ("Leerfahrt (Parität)", FARBE_LEERFAHRT),
    ]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(width=4, color=farbe), name=name))

    fig.update_layout(
        title=titel, xaxis=dict(scaleanchor="y", scaleratio=1, showgrid=False, zeroline=False, title="km"),
        yaxis=dict(showgrid=False, zeroline=False, title="km"), height=460,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def netzwerk_figure(netzwerk: Netzwerk, titel: str) -> go.Figure:
    fig = go.Figure()
    for k in netzwerk.kanten:
        k1, k2 = netzwerk.knoten[k.knoten1], netzwerk.knoten[k.knoten2]
        farbe = FARBE_PFLICHT_MEHRFACH if k.pflichtbesuche > 1 else FARBE_PFLICHT_EINFACH
        fig.add_trace(
            go.Scatter(
                x=[k1.x, k2.x], y=[k1.y, k2.y], mode="lines",
                line=dict(width=2.5 + 2.5 * (k.pflichtbesuche - 1), color=farbe), hoverinfo="text",
                text=f"Straße {k.id}: {k.pflichtbesuche}x Pflichträumung", showlegend=False,
            )
        )
    fig.add_trace(
        go.Scatter(
            x=[k.x for k in netzwerk.knoten], y=[k.y for k in netzwerk.knoten], mode="markers",
            marker=dict(size=10, color="#333333"), hoverinfo="skip", showlegend=False,
        )
    )
    fig.update_layout(
        title=titel, xaxis=dict(scaleanchor="y", scaleratio=1, showgrid=False, zeroline=False, title="km"),
        yaxis=dict(showgrid=False, zeroline=False, title="km"), height=380,
        margin=dict(l=20, r=20, t=50, b=20),
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
