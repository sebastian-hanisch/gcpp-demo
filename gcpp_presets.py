"""Ein-Klick-Beispielszenarien und Permalink-Logik (dasselbe SETTING_SPECS-
Muster wie in den anderen Demos dieses Workspace, z. B. vrp_presets.py) -
Problemgröße und Netzcharakteristik sind hier frei einstellbar statt über
feste, benannte Szenarien."""

import math
import random
from dataclasses import dataclass
from typing import Callable, Optional

import streamlit as st


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: Callable
    default: object
    lo: Optional[float] = None
    hi: Optional[float] = None


SETTING_SPECS = {
    "n_kreuzungen_slider": SettingSpec("n", int, 20, 8, 50),
    "k_nachbarn_slider": SettingSpec("k", int, 3, 2, 5),
    # Prozent (ganzzahlig, 0-50) statt Anteil (0.0-0.5) - st.slider()s `format`
    # wendet das Format-Muster direkt auf den Rohwert an, "%.0f%%" auf 0.2
    # würde also "0%" anzeigen statt "20%".
    "anteil_hauptstrassen_slider": SettingSpec("haupt", int, 20, 0, 50),
    "seed_input": SettingSpec("seed", int, 0, 0, 2_000_000_000),
}


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def apply_preset(n_kreuzungen, k_nachbarn, anteil_hauptstrassen_prozent, seed):
    st.session_state["n_kreuzungen_slider"] = n_kreuzungen
    st.session_state["k_nachbarn_slider"] = k_nachbarn
    st.session_state["anteil_hauptstrassen_slider"] = anteil_hauptstrassen_prozent
    st.session_state["seed_input"] = seed


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, 2_000_000_000)


def load_permalink_settings():
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
                if isinstance(value, float) and not math.isfinite(value):
                    continue
                if not isinstance(value, str):
                    if spec.lo is not None:
                        value = max(spec.lo, value)
                    if spec.hi is not None:
                        value = min(spec.hi, value)
                st.session_state[state_key] = value
            except (ValueError, TypeError):
                pass
    st.session_state["permalink_loaded"] = True


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def sync_query_params(n_kreuzungen, k_nachbarn, anteil_hauptstrassen_prozent, seed):
    try:
        st.query_params["n"] = str(int(n_kreuzungen))
        st.query_params["k"] = str(int(k_nachbarn))
        st.query_params["haupt"] = str(int(anteil_hauptstrassen_prozent))
        st.query_params["seed"] = str(int(seed))
    except Exception:
        pass
