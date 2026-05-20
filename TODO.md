# 📝 Roadmap Sviluppo Futuro: Sistema di Backup & Ripristino 🧪

Questa TODO list traccia i passaggi pianificati per implementare un sistema di sicurezza dei dati a doppia barriera (locale/cloud), un'interfaccia di ripristino self-service e una serie di funzionalità avanzate per la tracciabilità professionale in conformità con gli standard di laboratorio (GMP/GLP) in **Gestore-Lab**.

---

## 🛠️ Fase 1: Creazione Automatica dei Backup (Sicurezza & Sincronizzazione)

L'obiettivo è garantire la creazione automatica di copie storiche del database ad ogni avvio dell'applicazione.

*   [ ] **Integrazione in `Avvia_Programma.bat`**
    *   [ ] Creare in automatico la cartella `database/backups/` se mancante.
    *   [ ] Estrarre la data e l'ora corrente del sistema tramite script Batch.
    *   [ ] Copiare il file attivo `database.db` rinominandolo in `database_backup_YYYYMMDD_HHMMSS.db`.
*   [ ] **Algoritmo di Rotazione Automatico (Risparmio Spazio)**
    *   [ ] Scrivere uno script in Python (avviato in background o all'interno di `app.py`) che controlla la cartella dei backup.
    *   [ ] Mantenere in automatico solo le ultime **30 copie storiche** più recenti ed eliminare quelle più vecchie.
*   [ ] **Sincronizzazione Cloud Facoltativa**
    *   [ ] Consentire la configurazione di un percorso di backup esterno (es. cartella di sincronizzazione attiva di OneDrive, Dropbox o Google Drive) per il backup automatico off-site.

---

## 🖥️ Fase 2: Pannello Impostazioni & Ripristino Web "a Caldo" (Flask UI)

L'obiettivo è consentire agli operatori del laboratorio di gestire ed effettuare ripristini storici direttamente dal browser in totale autonomia.

*   [ ] **Struttura Backend in `app.py`**
    *   [ ] Creare la rotta `@app.route('/settings')` per la gestione dell'applicazione.
    *   [ ] Creare una funzione per scansionare e listare dinamicamente tutti i file `.db` presenti in `database/backups/` ordinati dal più recente.
*   [ ] **Ripristino Sicuro "a Caldo" (SQLite Online Backup API)**
    *   [ ] Implementare il ripristino tramite la funzione nativa di SQLite `sorgente.backup(destinazione)`.
    *   [ ] Gestire ed evitare errori di blocco (*Database file is locked*) chiudendo temporaneamente eventuali cursori attivi.
*   [ ] **Barriere di Sicurezza & Prevenzione Errori**
    *   [ ] **Backup Preventivo Immediato:** All'istante prima di sovrascrivere il database con il vecchio backup, creare una copia speciale `database_emergenza_pre_ripristino.db`.
    *   [ ] **Interfaccia di Doppia Conferma (Modal):** Schermata di blocco che richiede all'utente di confermare l'azione digitando manualmente la parola *"RIPRISTINA"* per sbloccare il pulsante d'invio.
*   [ ] **Interfaccia Grafica (Settings UI)**
    *   [ ] Creare il file `templates/settings.html` integrato con il tema scuro premium.
    *   [ ] Visualizzare la tabella con i backup disponibili (Data, Ora, Dimensione in KB, pulsante "Ripristina" in rosso e pulsante "Scarica" in azzurro).
    *   [ ] Aggiungere un pulsante per forzare la creazione manuale istantanea di un backup.

---

## 🚨 Fase 3: Salvagente di Emergenza (Offline)

*   [ ] **Script Batch di Ripristino Esterno**
    *   [ ] Creare un file `Ripristina_Database.bat` nella cartella principale del progetto.
    *   [ ] In caso di corruzione grave in cui il server Flask non si avvia, lo script deve consentire all'utente di selezionare e ripristinare l'ultimo backup funzionante direttamente dal terminale Windows.

---

## 🚀 Fase 4: Funzionalità Avanzate & Tracciabilità Professionale (GMP/GLP Ready)

L'obiettivo è elevare il livello di qualità, tracciabilità e conformità regolatoria del software per contesti industriali/clinici.

*   [ ] **Blocco di Sicurezza "QC Gate" (Controllo Qualità)**
    *   [ ] Nella pagina di **Scarico Automatico (Picking List)**, impedire la selezione di lotti che non abbiano lo stato `appr = 'OK'` (Approvato QC).
    *   [ ] Visualizzare un badge rosso bloccante in corrispondenza dei lotti in stato di quarantena o non ancora approvati.
*   [ ] **Avvisi e Notifiche di Scadenza (Early Warning Dashboard)**
    *   [ ] Mostrare avvisi di tipo *Warning* sulla Dashboard per i lotti attivi che **scadranno entro i prossimi 15-30 giorni**.
    *   [ ] Visualizzare alert bloccanti per eventuali lotti scaduti ancora disponibili a magazzino.
    *   [ ] Evidenziare in arancione i prodotti che si trovano sotto la soglia di **Scorta Minima**.
*   [ ] **Integrazione con Lettori Barcode / QR Code**
    *   [ ] Aggiungere un input globale o tasto di ricerca rapida con focus automatico per scansionare etichette.
    *   [ ] Permettere l'identificazione istantanea del lotto scansionato per compilare i campi del prelievo senza digitazione.
*   [ ] **Registro Modifiche ed Audit Trail (Data Integrity)**
    *   [ ] Creare la tabella `Audit_Trail` nel database (`id`, `data_ora`, `operatore`, `azione`, `tabella_interessata`, `vecchio_valore`, `nuovo_valore`).
    *   [ ] Salvare in automatico ogni modifica o eliminazione di lotti/prodotti effettuata dagli operatori per garantire la conformità con i requisiti regolatori sulla tracciabilità dei dati.
*   [ ] **Statistiche di Consumo & Data Visualization**
    *   [ ] Integrare la libreria *Chart.js* per visualizzare grafici ad area/linee.
    *   [ ] Mostrare il trend dei consumi mensili delle materie prime chiave (es. O-18 acqua, cassette di sintesi).
    *   [ ] Monitorare il numero di cicli di sintesi eseguiti e i lotti prodotti.
*   [ ] **Ottimizzazione Interfaccia Touch & Tablet (Cleanroom Friendly)**
    *   [ ] Ottimizzare il layout CSS per schermi tablet da 10 pollici (pulsanti e righe delle tabelle più grandi per facilitare l'uso con guanti in laboratorio).
    *   [ ] Rendere la compilazione della picking list di produzione interamente spuntabile a schermo tramite pulsanti touch veloci.

---

## 🎨 Fase 5: Semplificazione dell'Interfaccia & Esperienza Utente (UX/UI)

L'obiettivo è rendere l'utilizzo dell'applicazione immediato, riducendo lo sforzo cognitivo e i passaggi ripetitivi.

*   [ ] **Dashboard Consolidata (Micro-Dati in Home)**
    *   [ ] Integrare contatori e alert in piccolo direttamente dentro le card della Home Page (es. *"2 prodotti sotto scorta"* nella card Magazzino, *"3 lotti da approvare"* nella card Lotti) per evitare di dover navigare nelle singole pagine.
*   [ ] **Ricerca Intelligente Universale (Spotlight Search)**
    *   [ ] Inserire una barra di ricerca centrale nella Home Page in grado di scansionare simultaneamente codici prodotto, nomi di materie prime e numeri di lotto interni.
    *   [ ] Mostrare un menu a tendina istantaneo con i risultati e link diretti alle schede o ai form di modifica.
*   [ ] **Azioni Rapide ad Un Clic (Quick Actions)**
    *   [ ] Aggiungere pulsanti di scelta rapida direttamente nelle tabelle (es. un tasto verde `✔️ Approva QC` nel Registro Lotti che imposta all'istante l'approvazione con la data odierna, senza costringere ad aprire il modulo di modifica completo).
*   [ ] **Guida alle Sigle di Laboratorio (Tooltips Esplicativi)**
    *   [ ] Inserire micro-icone informative `🛈` accanto a sigle o campi complessi nei form (`CC`, `CA`, `Appr`, `Pz x Cf`).
    *   [ ] Mostrare spiegazioni chiare al passaggio del mouse (*hover*) per facilitare l'inserimento dei dati ed eliminare dubbi operativi per i nuovi utenti.
