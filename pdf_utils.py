import os
import re
from datetime import datetime
from fpdf import FPDF
from config import PROJECT_ROOT

def clean_pdf_string(s):
    if not s:
        return ""
    # Sostituzioni comuni per caratteri accentati in italiano
    replacements = {
        'à': "a'", 'á': "a'",
        'è': "e'", 'é': "e'",
        'ì': "i'", 'í': "i'",
        'ò': "o'", 'ó': "o'",
        'ù': "u'", 'ú': "u'",
        'À': "A'", 'È': "E'",
        'Ì': "I'", 'Ò': "O'",
        'Ù': "U'"
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    # Rimpiazza tutti gli altri caratteri non latin-1 con ?
    return s.encode('latin-1', 'replace').decode('latin-1')

def genera_pdf_distribuzione(lotto_interno, lotto_row, scarichi, filepath):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)
    
    # Header Box (Bordo principale)
    pdf.rect(10, 10, 190, 25)
    
    # Logo aziendale (se presente)
    logo_path = os.path.join(PROJECT_ROOT, "static", "img", "logo.jpg")
    if os.path.exists(logo_path):
        pdf.image(logo_path, 15, 12, 35)
        
    pdf.line(55, 10, 55, 35)
    
    # Titolo
    pdf.set_font("helvetica", "B", 12)
    pdf.set_xy(55, 10)
    pdf.cell(95, 25, "LISTA DI DISTRIBUZIONE LOTTO", border=0, align="C")
    
    pdf.line(150, 10, 150, 35)
    
    # Data di generazione e Pagina
    pdf.set_font("helvetica", size=8)
    pdf.set_xy(150, 10)
    pdf.cell(50, 12.5, f"Data: {datetime.now().strftime('%d-%m-%Y')}", border="B", align="C")
    pdf.set_xy(150, 22.5)
    pdf.cell(50, 12.5, "Pagina: 1 di 1", align="C")
    
    # Meta informazioni sul lotto e la materia prima
    pdf.ln(15)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(190, 8, clean_pdf_string("DETTAGLIO MATERIA PRIMA E LOTTO"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    nome_materia = lotto_row.get('nome_mp') or "N.D."
    codice_materia = lotto_row.get('codice_mp') or "N.D."
    lotto_forn = lotto_row.get('lotto_fornitore') or "N.D."
    forn = lotto_row.get('fornitore') or "N.D."
    scadenza = lotto_row.get('data_scadenza') or "N.D."
    arrivo = lotto_row.get('data_arrivo') or "N.D."
    
    # Formattazione date per visualizzazione
    try:
        scad_display = datetime.strptime(scadenza, '%Y-%m-%d').strftime('%d-%m-%Y')
    except:
        scad_display = scadenza
        
    try:
        arrivo_display = datetime.strptime(arrivo, '%Y-%m-%d').strftime('%d-%m-%Y')
    except:
        arrivo_display = arrivo
        
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(35, 6, "Materia Prima:")
    pdf.set_font("helvetica", size=9)
    pdf.cell(155, 6, clean_pdf_string(f"{nome_materia} (Codice: {codice_materia})"), ln=True)
    
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(35, 6, "Lotto Interno:")
    pdf.set_font("helvetica", size=9)
    pdf.cell(60, 6, clean_pdf_string(lotto_interno))
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(35, 6, "Lotto Fornitore:")
    pdf.set_font("helvetica", size=9)
    pdf.cell(60, 6, clean_pdf_string(lotto_forn), ln=True)
    
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(35, 6, "Fornitore:")
    pdf.set_font("helvetica", size=9)
    pdf.cell(60, 6, clean_pdf_string(forn))
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(35, 6, "Data Arrivo:")
    pdf.set_font("helvetica", size=9)
    pdf.cell(60, 6, clean_pdf_string(arrivo_display), ln=True)
    
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(35, 6, "Data Scadenza:")
    pdf.set_font("helvetica", size=9)
    pdf.cell(60, 6, clean_pdf_string(scad_display))
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(35, 6, "Data Stampa PDF:")
    pdf.set_font("helvetica", size=9)
    pdf.cell(60, 6, datetime.now().strftime('%d-%m-%Y %H:%M:%S'), ln=True)
    
    pdf.ln(6)
    
    # Tabella degli utilizzi (Scarichi)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(190, 8, clean_pdf_string("REGISTRO DEGLI UTILIZZI (SCARICHI)"), ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    try:
        qnt_iniziale = float(lotto_row.get('qnt_arrivata') or 0)
    except (ValueError, TypeError):
        qnt_iniziale = 0.0

    def format_qty(val):
        try:
            val_f = float(val)
            if val_f.is_integer():
                return str(int(val_f))
            return f"{val_f:.2f}".rstrip('0').rstrip('.')
        except:
            return str(val)

    if not scarichi:
        pdf.set_font("helvetica", "I", 10)
        pdf.cell(190, 8, clean_pdf_string("Nessun utilizzo o scarico registrato per questo lotto."), ln=True)
    else:
        # Larghezze colonne: Data (30), Causale (65), Quantità (25), Qtà Rimanente (35), Operatore (35) = 190
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(30, 7, "Data", border=1, align="C")
        pdf.cell(65, 7, "Causale", border=1, align="C")
        pdf.cell(25, 7, clean_pdf_string("Quantita'"), border=1, align="C")
        pdf.cell(35, 7, clean_pdf_string("Q.ta' Rimanente"), border=1, align="C")
        pdf.cell(35, 7, "Operatore", border=1, align="C", ln=True)
        
        pdf.set_font("helvetica", size=8)
        qnt_rimanente = qnt_iniziale
        for row in scarichi:
            try:
                data_disp = datetime.strptime(row['data'], '%Y-%m-%d').strftime('%d-%m-%Y')
            except:
                data_disp = row['data'] or "-"
                
            try:
                q_scarico = float(row['quantita'] or 0)
            except:
                q_scarico = 0.0
                
            qnt_rimanente -= q_scarico
            
            pdf.cell(30, 6, clean_pdf_string(data_disp), border=1, align="C")
            pdf.cell(65, 6, clean_pdf_string(row['causale']), border=1)
            pdf.cell(25, 6, clean_pdf_string(format_qty(q_scarico)), border=1, align="C")
            pdf.cell(35, 6, clean_pdf_string(format_qty(qnt_rimanente)), border=1, align="C")
            pdf.cell(35, 6, clean_pdf_string(row['operatore']), border=1, ln=True)
            
    # Salvataggio del PDF
    pdf.output(filepath)

def genera_pdf_richiesta_analisi(lotti, filepath):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=True, margin=10)
    
    # Bordo esterno principale dell'intestazione
    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.3)
    
    # Top-left cell: Logo
    pdf.rect(10, 10, 55, 22)
    logo_path = os.path.join(PROJECT_ROOT, "static", "img", "logo.jpg")
    if os.path.exists(logo_path):
        pdf.image(logo_path, 15, 12.5, 45)
    else:
        pdf.set_font("helvetica", "B", 18)
        pdf.set_text_color(79, 70, 229)
        pdf.set_xy(10, 10)
        pdf.cell(55, 22, "CURIUM", align="C")
        pdf.set_text_color(0, 0, 0)
        
    # Top-right cell: Title
    pdf.rect(65, 10, 135, 22)
    pdf.set_xy(65, 10)
    pdf.set_font("helvetica", size=9)
    pdf.cell(135, 7, "  Titolo:", align="L")
    
    pdf.set_font("helvetica", "B", 13)
    pdf.set_xy(65, 17)
    pdf.cell(135, 10, "RICHIESTA D'ANALISI", align="C")
    
    # Row 2 (SOP section below logo and title):
    pdf.rect(10, 32, 55, 12)
    pdf.set_xy(10, 32)
    pdf.set_font("helvetica", size=8)
    pdf.cell(55, 5, " SOP DI RIFERIMENTO:", ln=True)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_x(10)
    pdf.cell(55, 6, " UDN-PRD-001")
    
    # Column 2 (Revisione): width 40, height 12
    pdf.rect(65, 32, 40, 12)
    pdf.set_xy(65, 32)
    pdf.set_font("helvetica", size=9)
    pdf.cell(40, 12, "Revisione: 11", align="C")
    
    # Column 3 (Pagina): width 95, height 12
    pdf.rect(105, 32, 95, 12)
    pdf.set_xy(105, 32)
    pdf.set_font("helvetica", size=9)
    pdf.cell(95, 12, "Pagina: 1 di 1", align="C")
    
    # --- TESTO INTRODUTTIVO ---
    pdf.set_xy(10, 52)
    pdf.set_font("helvetica", "B", 10.5)
    testo_intro = "Si richiede l'esecuzione dei controlli sui seguenti materiali posti in stato di QUARANTENA"
    pdf.cell(190, 8, clean_pdf_string(testo_intro), align="C")
    
    pdf.ln(12)
    
    # --- TABELLA DATI ---
    widths = [45, 25, 30, 30, 20, 20, 20]
    headers = ["Materiale", "N. lotto interno", "Nome fornitore", "N. lotto fornitore", "Data di arrivo", "Quantita", "Data al QC"]
    
    # Scrittura intestazione tabella
    pdf.set_font("helvetica", "B", 9)
    pdf.set_fill_color(240, 240, 240)
    for w, h_text in zip(widths, headers):
        pdf.cell(w, 10, clean_pdf_string(h_text), border=1, align="C", fill=True)
    pdf.ln()
    
    pdf.set_font("helvetica", size=8.5)
    today_fmt = datetime.now().strftime('%d/%m/%Y')
    for lot in lotti:
        data_arr = lot.get('data_arrivo') or ""
        try:
            dt = datetime.strptime(data_arr, '%Y-%m-%d')
            data_arr_fmt = dt.strftime('%d/%m/%Y')
        except:
            data_arr_fmt = data_arr
            
        qnt_val = lot.get('qnt_arrivata') or ""
        um = lot.get('unita_misura') or ""
        qnt_str = f"{qnt_val} {um}".strip()
        
        materia_nome = lot.get('nome_mp') or ""
        if len(materia_nome) > 26:
            materia_nome = materia_nome[:23] + "..."
            
        forn_nome = lot.get('fornitore') or ""
        if len(forn_nome) > 17:
            forn_nome = forn_nome[:14] + "..."
            
        lotto_forn_val = lot.get('lotto_fornitore') or ""
        if len(lotto_forn_val) > 18:
            lotto_forn_val = lotto_forn_val[:15] + "..."
        
        # Scrittura dei campi
        pdf.cell(45, 8, clean_pdf_string(materia_nome), border=1)
        pdf.cell(25, 8, clean_pdf_string(lot.get('lotto_interno') or ""), border=1, align="C")
        pdf.cell(30, 8, clean_pdf_string(forn_nome), border=1)
        pdf.cell(30, 8, clean_pdf_string(lotto_forn_val), border=1, align="C")
        pdf.cell(20, 8, clean_pdf_string(data_arr_fmt), border=1, align="C")
        pdf.cell(20, 8, clean_pdf_string(qnt_str), border=1, align="C")
        pdf.cell(20, 8, clean_pdf_string(today_fmt), border=1, align="C")
        pdf.ln()
        
    pdf.output(filepath)

def genera_pdf_picking(batch, data_scarico, operatore, items, filepath):
    try:
        dt_display = datetime.strptime(data_scarico, '%Y-%m-%d').strftime('%d-%m-%Y')
    except:
        dt_display = data_scarico
        
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=10)

    # Header Box (Main Border)
    pdf.rect(10, 10, 190, 30)
    
    # Left Section (Logo + SOP)
    pdf.line(60, 10, 60, 40)
    logo_path = os.path.join(PROJECT_ROOT, "static", "img", "logo.jpg")
    if os.path.exists(logo_path):
        pdf.image(logo_path, 15, 12, 40)
    
    pdf.line(10, 30, 60, 30)
    pdf.set_font("helvetica", size=7)
    pdf.set_xy(10, 30)
    pdf.multi_cell(50, 5, f"SOP di riferimento: \nxxx", align="C")
    
    # Middle Section (Allegato + Title)
    pdf.line(150, 10, 150, 40)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_xy(60, 10)
    pdf.cell(90, 15, "ALLEGATO N° 6", border="B", align="C")
    pdf.set_xy(60, 25)
    pdf.cell(90, 15, "PICKING LIST", align="C")
    
    # Right Section (Revision + Page)
    pdf.set_font("helvetica", size=8)
    pdf.set_xy(150, 10)
    pdf.cell(50, 15, "Revisione: 11", border="B", align="L", new_x="RIGHT", new_y="TOP")
    pdf.set_xy(150, 25)
    pdf.cell(50, 15, "Pagina: 1 di 1", align="L")

    # Meta Data
    pdf.set_font("helvetica", size=10)
    pdf.ln(15)
    pdf.set_x(130)
    pdf.cell(40, 8, "Batch Production Nr.:", border=1)
    pdf.cell(30, 8, batch, border=1, new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(130)
    pdf.cell(40, 8, "Date:", border=1)
    pdf.cell(30, 8, dt_display, border=1, new_x="LMARGIN", new_y="NEXT")

    # Table
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(10, 8, "Num", border=1, align="C")
    pdf.cell(25, 8, "Codice", border=1, align="C")
    pdf.cell(85, 8, "Articolo", border=1, align="C")
    pdf.cell(20, 8, "Quantita", border=1, align="C")
    pdf.cell(30, 8, "Lotto n.", border=1, align="C")
    pdf.cell(20, 8, "Data scad.", border=1, align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("helvetica", size=8)
    for item in items:
        try:
            scad_display = datetime.strptime(item['data_scad'], '%Y-%m-%d').strftime('%d-%m-%Y')
        except:
            scad_display = item['data_scad']

        pdf.cell(10, 7, str(item['num']), border=1, align="C")
        pdf.cell(25, 7, str(item['codice']), border=1, align="C")
        pdf.cell(85, 7, str(item['articolo']), border=1)
        pdf.cell(20, 7, str(item['quantita']), border=1, align="C")
        pdf.cell(30, 7, str(item['lotto_n']), border=1, align="C")
        pdf.cell(20, 7, scad_display, border=1, align="C", new_x="LMARGIN", new_y="NEXT")

    # Footer
    pdf.ln(10)
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(0, 5, "Note:", new_x="LMARGIN", new_y="NEXT")
    pdf.rect(10, pdf.get_y(), 190, 20)
    pdf.ln(22)

    pdf.cell(63, 5, "Operatore", border=1)
    pdf.cell(63, 5, "Data", border=1)
    pdf.cell(64, 5, "Firma", border=1, new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(63, 10, operatore, border=1)
    pdf.cell(63, 10, dt_display, border=1)
    pdf.cell(64, 10, "", border=1, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    pdf.set_font("helvetica", size=8)
    pdf.cell(95, 8, "Copia n°: ________", new_x="RIGHT", new_y="TOP")
    pdf.cell(95, 8, "Sigla QA su ORIGINALE: ________________", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.output(filepath)
