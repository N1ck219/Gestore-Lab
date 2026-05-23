import unittest
import sqlite3
import os
import json
from app import app
from db_utils import get_db_connection

class TestGreenLabelConstraint(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()
        
        # Insert a mock material and mock lots for testing
        self.cursor.execute("INSERT OR IGNORE INTO Elenco_MP (codice, nome_mp) VALUES ('TEST99', 'Materiale Test')")
        
        # Lotto 1: Approved with green label (etich = 'OK')
        self.cursor.execute("""
            INSERT OR REPLACE INTO Lotti_Interni 
            (lotto_interno, codice_mp, data_arrivo, lotto_fornitore, fornitore, data_scadenza, qnt_arrivata, pz_x_cf, giacenza, appr, etich)
            VALUES ('L-TEST99-OK', 'TEST99', '2026-05-01', 'F99', 'Fornitore Test', '2027-05-01', '10.0', '1', '10.0', 'OK', 'OK')
        """)
        
        # Lotto 2: Not approved with green label (etich = '-')
        self.cursor.execute("""
            INSERT OR REPLACE INTO Lotti_Interni 
            (lotto_interno, codice_mp, data_arrivo, lotto_fornitore, fornitore, data_scadenza, qnt_arrivata, pz_x_cf, giacenza, appr, etich)
            VALUES ('L-TEST99-NO', 'TEST99', '2026-05-01', 'F99', 'Fornitore Test', '2027-05-01', '10.0', '1', '10.0', 'OK', '-')
        """)
        
        # Lotto 3: Expired, but approved with green label (etich = 'OK')
        self.cursor.execute("""
            INSERT OR REPLACE INTO Lotti_Interni 
            (lotto_interno, codice_mp, data_arrivo, lotto_fornitore, fornitore, data_scadenza, qnt_arrivata, pz_x_cf, giacenza, appr, etich)
            VALUES ('L-TEST99-EXPIRED', 'TEST99', '2026-05-01', 'F99', 'Fornitore Test', '2026-05-10', '10.0', '1', '10.0', 'OK', 'OK')
        """)
        
        # Inserimento mock per Acqua 18O (codice '424')
        self.cursor.execute("INSERT OR IGNORE INTO Elenco_MP (codice, nome_mp) VALUES ('424', 'Acqua arricchita [18O]H2O')")
        self.cursor.execute("""
            INSERT OR REPLACE INTO Lotti_Interni 
            (lotto_interno, codice_mp, data_arrivo, lotto_fornitore, fornitore, data_scadenza, qnt_arrivata, pz_x_cf, giacenza, appr, etich)
            VALUES ('L-424-NO', '424', '2026-05-01', 'F424', 'Fornitore Water', '2027-05-01', '10.0', '1', '10.0', 'OK', '-')
        """)
        
        self.conn.commit()

    def tearDown(self):
        # Clean up database
        self.cursor.execute("DELETE FROM Lotti_Interni WHERE lotto_interno IN ('L-TEST99-OK', 'L-TEST99-NO', 'L-424-NO', 'L-TEST99-EXPIRED')")
        self.cursor.execute("DELETE FROM Elenco_MP WHERE codice IN ('TEST99', '424')")
        self.conn.commit()
        self.conn.close()

    def test_discharge_approved_lot_succeeds(self):
        # Prepare request data
        payload = {
            'lotto_prod': 'PROD99',
            'operatore': 'TestOperatore',
            'data': '2026-05-23',
            'items': [
                {
                    'codice_mp': 'TEST99',
                    'lotto_interno': 'L-TEST99-OK',
                    'quantita': 2.0
                }
            ]
        }
        
        response = self.client.post('/scarico_fdg', 
                                    data=json.dumps(payload), 
                                    content_type='application/json')
        
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn("successo", data['message'])
        
        # Clean up discharge record created
        self.cursor.execute("DELETE FROM Scarichi WHERE lotto_interno = 'L-TEST99-OK'")
        self.conn.commit()

    def test_discharge_unapproved_lot_fails(self):
        # Prepare request data
        payload = {
            'lotto_prod': 'PROD99',
            'operatore': 'TestOperatore',
            'data': '2026-05-23',
            'items': [
                {
                    'codice_mp': 'TEST99',
                    'lotto_interno': 'L-TEST99-NO',
                    'quantita': 2.0
                }
            ]
        }
        
        response = self.client.post('/scarico_fdg', 
                                    data=json.dumps(payload), 
                                    content_type='application/json')
        
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
        self.assertIn("non è ancora stato approvato con l'etichetta verde", data['message'])

    def test_discharge_unapproved_water_18O_fails_without_run_in_bianco(self):
        payload = {
            'lotto_prod': 'PROD99',
            'operatore': 'TestOperatore',
            'data': '2026-05-23',
            'items': [
                {
                    'codice_mp': '424',
                    'lotto_interno': 'L-424-NO',
                    'quantita': 2.0
                }
            ],
            'run_in_bianco': False
        }
        
        response = self.client.post('/scarico_fdg', 
                                    data=json.dumps(payload), 
                                    content_type='application/json')
        
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
        self.assertIn("non è ancora stato approvato con l'etichetta verde", data['message'])

    def test_discharge_unapproved_water_18O_succeeds_with_run_in_bianco(self):
        payload = {
            'lotto_prod': 'PROD99',
            'operatore': 'TestOperatore',
            'data': '2026-05-23',
            'items': [
                {
                    'codice_mp': '424',
                    'lotto_interno': 'L-424-NO',
                    'quantita': 2.0
                }
            ],
            'run_in_bianco': True
        }
        
        response = self.client.post('/scarico_fdg', 
                                    data=json.dumps(payload), 
                                    content_type='application/json')
        
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn("successo", data['message'])
        
        # Clean up discharge record created
        self.cursor.execute("DELETE FROM Scarichi WHERE lotto_interno = 'L-424-NO'")
        self.conn.commit()

    def test_discharge_expired_lot_fails(self):
        # Prepare request data
        payload = {
            'lotto_prod': 'PROD99',
            'operatore': 'TestOperatore',
            'data': '2026-05-23',
            'items': [
                {
                    'codice_mp': 'TEST99',
                    'lotto_interno': 'L-TEST99-EXPIRED',
                    'quantita': 2.0
                }
            ]
        }
        
        response = self.client.post('/scarico_fdg', 
                                    data=json.dumps(payload), 
                                    content_type='application/json')
        
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
        self.assertIn("è scaduto il 10-05-2026", data['message'])

if __name__ == '__main__':
    unittest.main()
