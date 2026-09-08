"""
Winterdienst-Tourenplanung – interaktive Demo
Sebastian Hanisch - Operations Research und Machine Learning

Logistik-Anwendung des (verallgemeinerten) Chinesischen Postbotenproblems
(Route Inspection Problem): ein Räumfahrzeug muss in seinem Bezirk JEDE
Straße mindestens einmal räumen - Hauptverkehrsstraßen sogar zweimal pro
Schicht. Das ist die Verallgemeinerung des Eulerpfad-Klassikers "Haus vom
Nikolaus" (dort: jede Kante genau 1x) auf beliebige Pflicht-Häufigkeiten.

Kernthema dieser Demo: Anders als die meisten Tourenplanungsprobleme in
diesem Portfolio (z. B. vrp_demo) ist DIESES Problem - alle Straßen sind
Pflicht - polynomiell exakt lösbar (Edmonds & Johnson 1973)! Der Trick
steckt allein darin, WIE man die Kreuzungen mit ungerader Straßenanzahl
paart, um das Netzwerk "eulersch" zu machen. Eine naive Paarung nach
Luftlinie (wie ein Disponent, der auf dem Stadtplan einfach optisch nahe
Kreuzungen verbindet) kann dabei deutlich schlechter sein als die
mathematisch optimale Paarung - das zufällig gestreute Straßennetz dieser
Demo (dasselbe Erzeugungsprinzip wie in vrp_demo) macht diesen Unterschied
zuverlässig sichtbar.

Code-Struktur: Modell, Straßennetz-Generator, Solver, PDF-Export und
Visualisierung liegen in den Modulen gcpp_*.py neben dieser Datei.
"""

import pandas as pd
import streamlit as st

from gcpp_pdf_export import generate_tour_report_pdf
from gcpp_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sync_query_params,
)
from gcpp_scenario import baue_strassennetz
from gcpp_solver import loese_alle, metaheuristik_verlauf
from gcpp_visualization import konvergenz_figure, tour_figure, vergleich_balken_figure

METHODEN_REIHENFOLGE = ["Gierige Paarung", "Exakt (Minimum-Weight Matching)", "Metaheuristik (Simulated Annealing)"]
METHODEN_TAB_LABEL = {
    "Gierige Paarung": "📍 Gierige Paarung",
    "Exakt (Minimum-Weight Matching)": "✅ Exakt",
    "Metaheuristik (Simulated Annealing)": "🧬 Metaheuristik",
}


@st.cache_data(show_spinner=False)
def _compute(n_kreuzungen, k_nachbarn, anteil_hauptstrassen_prozent, seed, cache_key):
    netzwerk = baue_strassennetz(n_kreuzungen, k_nachbarn, anteil_hauptstrassen_prozent / 100, seed)
    touren = loese_alle(netzwerk, seed)
    verlauf = metaheuristik_verlauf(netzwerk, seed)
    return netzwerk, touren, verlauf


st.set_page_config(page_title="Winterdienst-Tourenplanung – Sebastian Hanisch", layout="wide")

st.title("🚜 Winterdienst-Tourenplanung")
st.markdown(
    """
Interaktive Demo zur **Tourenplanung für den Winterdienst**: Ein Räumfahrzeug muss in seinem Bezirk
**jede Straße mindestens einmal räumen** - stark befahrene Hauptstraßen sogar zweimal pro Schicht.
Gesucht ist die **kürzeste geschlossene Rundtour**, die das erfüllt (das (verallgemeinerte)
**Chinesische Postbotenproblem** / Route Inspection Problem). Anders als bei den meisten
Tourenplanungsproblemen in diesem Portfolio ist dieses Problem **polynomiell exakt lösbar** - die
eigentliche Frage ist nur, wie man die Kreuzungen mit ungerader Straßenanzahl klug paart. Details im
Expander "Wie funktioniert diese Demo?" unten sowie formal hergeleitet im Expander "📐 Mathematische
Formulierung".
"""
)

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_col1, preset_col2, preset_col3 = st.columns(3)
with preset_col1:
    st.button(
        "🏘️ Kleines Wohnviertel", use_container_width=True,
        on_click=apply_preset, args=(12, 3, 10, 4),
        help="Übersichtliches Netz - der Unterschied zwischen gieriger und exakter Paarung ist hier trotzdem deutlich sichtbar.",
    )
with preset_col2:
    st.button(
        "🏙️ Mittelgroßer Bezirk", use_container_width=True,
        on_click=apply_preset, args=(24, 3, 20, 0),
        help="Realistischere Bezirksgröße mit einem Fünftel Hauptstraßen.",
    )
with preset_col3:
    st.button(
        "🌆 Große Stadt (viele Hauptstraßen)", use_container_width=True,
        on_click=apply_preset, args=(40, 3, 35, 0),
        help="Großer Bezirk mit hohem Hauptstraßenanteil - testet, wie gut die Verfahren mit der Problemgröße skalieren.",
    )

st.caption(
    "🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, "
    "um ein Szenario zu teilen."
)

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_kreuzungen = st.slider(
        "Anzahl Kreuzungen", *bounds("n_kreuzungen_slider"), key="n_kreuzungen_slider",
        help="Problemgröße - wie viele Kreuzungen hat der Winterdienst-Bezirk?",
    )
    k_nachbarn = st.slider(
        "Straßen je Kreuzung (Netzdichte)", *bounds("k_nachbarn_slider"), key="k_nachbarn_slider",
        help="Mit wie vielen der nächstgelegenen Kreuzungen jede Kreuzung verbunden wird - mehr = dichteres Straßennetz.",
    )
    anteil_hauptstrassen_prozent = st.slider(
        "Anteil Hauptstraßen (2x räumen)", *bounds("anteil_hauptstrassen_slider"), step=5,
        key="anteil_hauptstrassen_slider", format="%d%%",
        help="Anteil der (längsten, also meist verbindenden) Straßen, die pro Schicht zweimal geräumt werden müssen.",
    )

    seed_lo, seed_hi = bounds("seed_input")
    seed = st.number_input("Zufalls-Seed (Straßennetz & Metaheuristik)", min_value=seed_lo, max_value=seed_hi, step=1, key="seed_input")
    st.button(
        "🎲 Neuen Bezirk generieren", use_container_width=True, on_click=randomize_seed,
        help="Würfelt einen neuen Zufalls-Seed - erzeugt ein neues Straßennetz UND eine neue Suchtrajektorie für die Metaheuristik.",
    )

sync_query_params(n_kreuzungen, k_nachbarn, anteil_hauptstrassen_prozent, int(seed))

cache_key = (n_kreuzungen, k_nachbarn, anteil_hauptstrassen_prozent, int(seed))
netzwerk, touren, meta_verlauf = _compute(n_kreuzungen, k_nachbarn, anteil_hauptstrassen_prozent, int(seed), cache_key)

exakt = touren["Exakt (Minimum-Weight Matching)"]
gierig = touren["Gierige Paarung"]
meta = touren["Metaheuristik (Simulated Annealing)"]

st.markdown("## 🎯 Ergebnis: Exakte Lösung")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Pflichtdistanz", f"{exakt.pflichtdistanz:.1f} km")
m2.metric("Leerfahrten", f"{exakt.leerfahrten:.1f} km")
m3.metric("Gesamtdistanz", f"{exakt.gesamtdistanz:.1f} km")
m4.metric("Anzahl Straßen", f"{len(netzwerk.kanten)}")

st.plotly_chart(
    tour_figure(netzwerk, exakt, f"Winterdienst-Bezirk ({n_kreuzungen} Kreuzungen) – exakte Rundtour"),
    use_container_width=True, key="tour_main",
)

pdf_bytes = generate_tour_report_pdf(netzwerk, exakt)
st.download_button(
    "📄 Winterdienst-Tourenplan als PDF herunterladen", data=pdf_bytes,
    file_name="winterdienst_tourenplan.pdf", mime="application/pdf", key="primary_pdf_download",
)

st.caption(
    "Berechnet mit dem exakten Minimum-Weight-Matching-Verfahren (Edmonds & Johnson 1973) - "
    "dieses Problem ist eines der wenigen in diesem Portfolio, das sich polynomiell EXAKT lösen "
    "lässt. Details und Methodenvergleich unten."
)

st.markdown("---")
st.subheader("📐 Warum kann \"optische Nähe\" in die Irre führen?")
st.markdown(
    """
Um jede Straße die geforderte Anzahl mal zu räumen, muss man zusätzliche ("Leerfahrten"-)Wege
zwischen den Kreuzungen mit ungerader Straßenanzahl einfügen, bis das Netzwerk überall geraden Grad
hat (Satz von Euler). Die **gierige Paarung** wählt dafür naiv die Kreuzung, die auf dem Stadtplan am
nächsten liegt (Luftlinie) - ohne zu prüfen, wie weit der tatsächliche Weg durchs Straßennetz ist.
Liegen zwei Kreuzungen räumlich nah, sind aber nur über einen Umweg verbunden (z. B. weil kein
direkter Durchgangsweg existiert), kann das teuer werden.
"""
)

if exakt.leerfahrten > 0:
    gap_pct = (gierig.leerfahrten - exakt.leerfahrten) / exakt.leerfahrten * 100
else:
    gap_pct = 0.0 if gierig.leerfahrten == 0 else float("inf")

c1, c2 = st.columns(2)
c1.metric("Gierige Paarung (Leerfahrten)", f"{gierig.leerfahrten:.1f} km")
c2.metric(
    "Exakte Paarung (Leerfahrten)", f"{exakt.leerfahrten:.1f} km",
    delta=f"{-gap_pct:.1f} %" if gap_pct != float("inf") else None, delta_color="inverse",
)
if gap_pct > 5.0:
    st.warning(
        f"⚠️ In diesem Bezirk fährt die gierige Paarung **{gap_pct:.0f}%** mehr Leerfahrten als "
        "nötig - ein Hinweis darauf, dass Luftlinien- und Netzwerkdistanz hier auseinanderfallen."
    )
else:
    st.success(
        f"✅ In diesem Bezirk liegt die gierige Paarung nur **{max(gap_pct, 0):.0f}%** über dem "
        "Optimum - hier stimmen Luftlinien- und Netzwerkdistanz weitgehend überein."
    )

st.markdown("---")

with st.expander("🔧 Wie wir das erreichen – vollständiger Methodenvergleich", expanded=False):
    st.plotly_chart(vergleich_balken_figure(touren), use_container_width=True, key="vergleich_balken")
    tabelle = pd.DataFrame(
        [
            {
                "Methode": name,
                "Leerfahrten (km)": touren[name].leerfahrten,
                "Gesamtdistanz (km)": touren[name].gesamtdistanz,
                "Rechenzeit (s)": touren[name].rechenzeit,
            }
            for name in METHODEN_REIHENFOLGE
        ]
    )
    st.dataframe(tabelle, use_container_width=True, hide_index=True)

    tab_labels = [METHODEN_TAB_LABEL[m] for m in METHODEN_REIHENFOLGE] + ["📊 Konvergenz"]
    tabs = st.tabs(tab_labels)
    beschreibungen = {
        "Gierige Paarung": "Paart ungerade Kreuzungen nach Luftliniendistanz - schnell, aber ohne Rücksicht auf den tatsächlichen Straßen-Umweg.",
        "Exakt (Minimum-Weight Matching)": "Minimum-Weight Perfect Matching (Edmonds & Johnson 1973) auf den echten kürzesten Straßennetz-Wegen zwischen den ungeraden Kreuzungen - beweisbar optimal.",
        "Metaheuristik (Simulated Annealing)": "Lokale Suche über den Raum aller Paarungen, startend bei der gierigen Lösung - trifft bei diesen Problemgrößen praktisch immer dieselbe Paarung wie das exakte Verfahren, aber ohne Optimalitätsgarantie.",
    }
    for tab, name in zip(tabs[:-1], METHODEN_REIHENFOLGE):
        with tab:
            tour = touren[name]
            st.caption(beschreibungen[name])
            tm1, tm2, tm3 = st.columns(3)
            tm1.metric("Leerfahrten", f"{tour.leerfahrten:.1f} km")
            tm2.metric("Gesamtdistanz", f"{tour.gesamtdistanz:.1f} km")
            tm3.metric("Rechenzeit", f"{tour.rechenzeit*1000:.1f} ms")
            st.plotly_chart(
                tour_figure(netzwerk, tour, name), use_container_width=True, key=f"tour_{name}",
            )

    with tabs[-1]:
        st.caption(
            "Beste bisher gefundene Leerfahrten-Distanz je Iteration der Simulated-Annealing-Suche "
            "über den Raum aller Paarungen (Startpunkt: die gierige Paarung)."
        )
        st.plotly_chart(konvergenz_figure(meta_verlauf), use_container_width=True, key="konvergenz")

st.markdown("---")

with st.expander("Wie funktioniert diese Demo?"):
    st.markdown(
        r"""
**Die Problemstellung:** Ein Winterdienst-Fahrzeug muss in seinem Bezirk **jede Straße eine
vorgegebene Anzahl mal räumen** - normale Wohnstraßen 1x pro Schicht, verkehrsreiche Hauptstraßen
2x. Gesucht ist die kürzeste **geschlossene Rundtour**, die das erfüllt. Das ist die
Verallgemeinerung des klassischen Eulerpfad-Rätsels "Haus vom Nikolaus" (dort: jede Kante genau 1x,
lösbar wenn 0 oder 2 Knoten ungeraden Grad haben) auf beliebige Pflicht-Häufigkeiten je Straße - in
der Literatur das **Chinesische Postbotenproblem** (Route Inspection Problem). Dieselbe Modellierung
passt genauso auf Straßenreinigung, Briefzustellung oder Zählerablesung - überall dort, wo ein
Fahrzeug jede Kante eines Netzwerks bedienen muss, statt nur bestimmte Punkte anzufahren (der
Unterschied zum klassischen Fahrzeugrouting in `vrp_demo`).

**Das Straßennetz:** Zufällig gestreute Kreuzungen, jede mit ihren $k$ nächstgelegenen Kreuzungen
verbunden (genau dasselbe Erzeugungsprinzip wie das Hintergrund-Straßennetz in `vrp_demo`) - dadurch
entsteht ein unregelmäßiges, aber realistisches Netz, in dem Luftlinien- und tatsächliche
Netzwerkdistanz zwischen zwei Kreuzungen oft spürbar auseinanderfallen (kein direkter Durchgang
vorhanden). Die längsten Straßen (meist die verbindenden Hauptachsen zwischen entfernten Bereichen)
werden als Hauptstraßen mit doppelter Räumpflicht markiert.

**Warum das (fast) immer lösbar ist - Satz von Euler:** Eine geschlossene Rundtour, die jede Kante
eines (Multi-)Graphen genau einmal nutzt, existiert genau dann, wenn der Graph zusammenhängend ist
und **jeder Knoten geraden Grad hat**. Das "Pflicht-Multigraph" (jede Straße so oft dupliziert wie
gefordert) hat aber i. A. Kreuzungen mit ungeradem Grad. Die Lösung: Kreuzungspaare mit ungeradem
Grad über zusätzliche, doppelt gefahrene kürzeste Wege verbinden ("Leerfahrten"), bis alle Grade
gerade sind - danach liefert ein **Eulerkreis** (Hierholzer-Algorithmus) die eigentliche Rundtour.

**Der eigentliche Clou - dieses Problem ist polynomiell EXAKT lösbar:** Anders als fast jedes
andere Tourenplanungsproblem in diesem Portfolio (z. B. das Fahrzeugrouting in `vrp_demo`,
NP-schwer) lässt sich die BESTE Paarung der ungeraden Kreuzungen in Polynomialzeit finden - über ein
**Minimum-Weight Perfect Matching** (Edmonds & Johnson, 1973) auf einem Hilfsgraphen, dessen
Kantengewichte die echten kürzesten Straßennetz-Wege zwischen den ungeraden Kreuzungen sind. Das ist
einer der wenigen Fälle, in denen "exakt" nicht "langsam" bedeutet.

**Warum die gierige Paarung trotzdem scheitern kann:** Die naive Heuristik paart nach
**Luftliniendistanz** - so, wie ein Disponent auf dem Stadtplan einfach die optisch nächstgelegenen
Kreuzungen verbindet, ohne den tatsächlichen Weg durchs Straßennetz nachzurechnen. Fallen Luftlinien-
und Netzwerkdistanz auseinander, erzwingt das teure Fehlentscheidungen - bei den zufällig gestreuten
Straßennetzen dieser Demo tritt das schon bei kleinen bis mittleren Bezirksgrößen regelmäßig auf.

**Wichtiger Modellierungshinweis:** `networkx` bringt mit `eulerize()` eine fertige Funktion für
genau dieses Problem mit - ein Blick in den Quellcode zeigt aber, dass sie Knoten nach
**Kantenanzahl (Hops)** statt nach echter Distanz paart. Für Straßennetze mit unterschiedlich langen
Straßen (wie hier) wäre das schlicht falsch, weshalb diese Demo einen eigenen, gewichtsrichtigen
Matching-Aufbau verwendet (`gcpp_solver.py`) statt sich auf `eulerize()` zu verlassen.
"""
    )

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
Gegeben ein zusammenhängender, ungerichteter Graph $G=(V,E)$ mit Kantenlängen $\ell_e > 0$ und
Pflicht-Häufigkeiten $r_e \geq 1$ je Kante $e \in E$. Gesucht ist eine geschlossene Rundtour minimaler
Länge, die jede Kante $e$ mindestens $r_e$-mal nutzt.
"""
    )
    st.latex(r"\min \sum_{e \in E} x_e \, \ell_e \qquad \text{s.t.} \quad x_e \geq r_e \;\; \forall e \in E")
    st.markdown(
        r"""
mit der Nebenbedingung, dass der Multigraph, der jede Kante $e$ genau $x_e$-mal enthält,
**zusammenhängend ist und in dem jeder Knoten geraden Grad hat** (Satz von Euler - nur dann
existiert überhaupt eine geschlossene Rundtour, die jede Kante $x_e$-mal nutzt).
"""
    )
    st.markdown(
        r"""
**Lösungsweg (Edmonds & Johnson, 1973):**

1. **Pflicht-Multigraph** $G_r$: jede Kante $e$ wird $r_e$-mal dupliziert.
2. **Ungerade Knoten** $T = \{v \in V : \deg_{G_r}(v) \text{ ungerade}\}$ bestimmen ($|T|$ ist immer
   gerade, Handshake-Lemma).
3. **Kürzeste Wege**: für jedes Paar $(u,v) \in T \times T$ die kürzeste Weglänge $d(u,v)$ in $G$
   berechnen (Dijkstra).
4. **Minimum-Weight Perfect Matching** auf dem vollständigen Graphen über $T$ mit Kantengewichten
   $d(u,v)$ lösen - liefert die kostenminimale Paarung $M^*$.
5. Für jedes Paar in $M^*$ den zugehörigen kürzesten Weg in $G_r$ **noch einmal duplizieren**
   ("Leerfahrten"). Das Ergebnis ist zusammenhängend und hat nur noch gerade Grade (jede Duplikation
   ändert den Grad von genau 2 Knoten um genau 1).
6. **Eulerkreis** (Hierholzer-Algorithmus, hier `networkx.eulerian_circuit`) liefert die konkrete
   Rundtour.

**Optimalität:** Schritt 4 minimiert genau die zusätzliche ("Leerfahrten"-)Distanz - da die
Pflichtdistanz $\sum_e r_e \ell_e$ für JEDE gültige Tour gleich (und damit fix) ist, minimiert die
optimale Paarung automatisch auch die Gesamtdistanz. Da ein Minimum-Weight Perfect Matching in
Polynomialzeit lösbar ist (Blossom-Algorithmus), ist das gesamte Verfahren polynomiell.

**Bezug zum Code:** `gcpp_scenario.py` erzeugt das zufällige Straßennetz (dasselbe kNN-Prinzip wie
`vrp_demo`s Hintergrundnetz), `gcpp_solver.py` implementiert Schritt 1-6 dreimal mit identischem
Gerüst - die drei Methoden unterscheiden sich AUSSCHLIESSLICH in Schritt 4 (`_paarung_exakt` nutzt
`networkx.min_weight_matching`, `_paarung_gierig` paart nächster-Nachbar nach Luftlinie,
`_paarung_metaheuristik` verbessert die gierige Paarung per Simulated Annealing über
Paarungs-Vertauschungen).

**Quelle:** J. Edmonds, E. L. Johnson. *Matching, Euler tours and the Chinese postman.*
Mathematical Programming, Volume 5, Issue 1 (1973), 111-114.
"""
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
