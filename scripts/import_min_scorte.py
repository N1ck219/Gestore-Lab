import pandas as pd
import sqlite3
import os

file_path = r'database\Materie Prime.xlsm'
db_path = r'database\database.db'

def import_min_scorte():
    if not os.path.exists(file_path):
        print(f"Errore: Il file {file_path} non esiste.")
        return

    try:
        print("Lettura foglio 'Magazzino'...")
        # Leggiamo con header alla riga 1 (quella che contiene 'Codice', 'Materiale', 'Min')
        df = pd.read_excel(file_path, sheet_name='Magazzino', engine='openpyxl', header=1)
        
        # Pulizia dati: prendiamo solo Codice e Min
        if 'Codice' not in df.columns or 'Min' not in df.columns:
            print("Errore: Colonne 'Codice' o 'Min' non trovate nel foglio Magazzino.")
            return

        data = df[['Codice', 'Min']].dropna(subset=['Codice'])
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        count = 0
        print("Aggiornamento scorte minime nel database...")
        
        for _, row in data.iterrows():
            codice = str(row['Codice']).strip()
            # Puliamo il codice se ha .0 (tipico dei numeri letti da Excel)
            if codice.endswith('.0'):
                codice = codice[:-2]
                
            scorta_min = 0
            try:
                scorta_min = float(row['Min'])
            except:
                scorta_min = 0
                
            # Aggiorniamo la tabella Elenco_MP
            cursor.execute('''
                UPDATE Elenco_MP 
                SET scorta_minima = ? 
                WHERE codice = ?
            ''', (scorta_min, codice))
            
            if cursor.rowcount > 0:
                count += 1
        
        conn.commit()
        conn.close()
        print(f"Aggiornamento completato! Aggiornate {count} materie prime.")

    except Exception as e:
        print(f"Errore durante l'importazione: {e}")

if __name__ == "__main__":
    import_min_scorte()
