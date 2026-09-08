"""End-to-end Smoke-Test via Streamlits offizielles AppTest-Framework: laedt app.py mit
den Standardeinstellungen und prueft, dass kein Python-Fehler auftritt - insbesondere
`streamlit.errors.StreamlitDuplicateElementId` (mehrere st.plotly_chart-Aufrufe ohne
eindeutiges key= koennen zufaellig identischen Inhalt rendern und kollidieren)."""

import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")


def test_app_loads_without_exception():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=120)
    assert not at.exception, [str(e) for e in at.exception]


def test_preset_buttons_do_not_raise():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=120)
    for button in at.button:
        button.click().run(timeout=120)
        assert not at.exception, [str(e) for e in at.exception]


def test_app_loads_at_slider_extremes():
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=120)
    at.slider(key="n_kreuzungen_slider").set_value(8).run(timeout=120)
    assert not at.exception, [str(e) for e in at.exception]
    at.slider(key="n_kreuzungen_slider").set_value(200).run(timeout=180)
    assert not at.exception, [str(e) for e in at.exception]
    at.slider(key="k_nachbarn_slider").set_value(6).run(timeout=180)
    assert not at.exception, [str(e) for e in at.exception]
    at.slider(key="anteil_hauptstrassen_slider").set_value(0).run(timeout=120)
    assert not at.exception, [str(e) for e in at.exception]
    at.slider(key="anteil_hauptstrassen_slider").set_value(50).run(timeout=120)
    assert not at.exception, [str(e) for e in at.exception]
