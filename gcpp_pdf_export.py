"""Erzeugt einen Rundtour-Bericht als downloadbares PDF (in-memory).

Umlaute sind unproblematisch (Latin-1, von der FPDF-Kernschrift Helvetica
unterstützt) - vermieden werden nur echte Sonderzeichen wie Halbgeviertstriche
(–), die die Kernschrift nicht darstellen kann.
"""

import time
from collections import Counter

from gcpp_model import Netzwerk
from gcpp_solver import Tour


def generate_tour_report_pdf(netzwerk: Netzwerk, tour: Tour) -> bytes:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    zaehler = Counter()
    for u, v in tour.kreis:
        zaehler[frozenset({u, v})] += 1

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Winterdienst-Tourenplan (Demo)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Erstellt: {time.strftime('%d.%m.%Y %H:%M')} Uhr", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Zusammenfassung", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Gebiet: {netzwerk.name}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Methode: {tour.methode}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Pflichtdistanz: {tour.pflichtdistanz:.1f} km", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Leerfahrten: {tour.leerfahrten:.1f} km", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Gesamtdistanz: {tour.gesamtdistanz:.1f} km", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Strassen", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    headers = ["Strasse", "Pflichtbesuche", "Tatsaechlich befahren", "Leerfahrt"]
    widths = [25, 45, 55, 40]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(235, 235, 235)
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.ln(7)

    pdf.set_font("Helvetica", "", 9)
    for k in netzwerk.kanten:
        gesamt = zaehler.get(frozenset({k.knoten1, k.knoten2}), 0)
        extra = max(0, gesamt - k.pflichtbesuche)
        row = [str(k.id), str(k.pflichtbesuche), str(gesamt), "Ja" if extra else "Nein"]
        for val, w in zip(row, widths):
            pdf.cell(w, 6, val, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.ln(6)

    return bytes(pdf.output())
