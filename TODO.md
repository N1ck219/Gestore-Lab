# 📝 Roadmap Sviluppo Futuro: Sistema di Backup & Miglioramenti Pratici 🧪

Questa TODO list traccia i passaggi pianificati per migliorare **Gestore-Lab** in modo incrementale. L'obiettivo è dotare l'applicazione di un sistema di sicurezza solido, di interfacce semplici e di un codice pulito e facile da mantenere nel tempo, mantenendo le funzionalità enterprise complesse come idee facoltative ("in forse") alla fine.

---

## 🛠️ Fase 1: Creazione Automatica dei Backup (Sicurezza Locale)

L'obiettivo è garantire la creazione automatica di copie storiche del database ad ogni avvio dell'applicazione.

*   [x] **Integrazione in `Avvia_Programma.bat`**
    *   [x] Creare in automatico la cartella `database/backups/` se mancante.
    *   [x] Estrarre la data e l'ora corrente del sistema tramite script Batch.
    *   [x] Copiare il file attivo `database.db` rinominandolo in `database_backup_YYYYMMDD_HHMMSS.db`.
*   [x] **Algoritmo di Rotazione Automatico (Risparmio Spazio)**
    *   [x] Scrivere uno script in Python (avviato in background o all'interno di `app.py`) che controlla la cartella dei backup.
    *   [x] Mantenere in automatico solo le ultime **30 copie storiche** più recenti ed eliminare quelle più vecchie per non occupare spazio inutile.
*   [ ] **Sincronizzazione Cloud Facoltativa**
    *   [ ] Consentire la configurazione di un percorso di backup esterno (es. cartella di sincronizzazione attiva di OneDrive, Dropbox o Google Drive) per il backup automatico off-site.

---

## 🖥️ Fase 2: Pannello Impostazioni & Ripristino Web "a Caldo" (Flask UI)

L'obiettivo è consentire agli operatori del laboratorio di gestire ed effettuare ripristini storici direttamente dal browser in totale autonomia.

*   [x] **Struttura Backend in `app.py`**
    *   [x] Creare la rotta `@app.route('/settings')` per la gestione dell'applicazione.
    *   [x] Creare una funzione per scansionare e listare dinamicamente tutti i file `.db` presenti in `database/backups/` ordinati dal più recente.
*   [x] **Ripristino Sicuro "a Caldo" (SQLite Online Backup API)**
    *   [x] Implementare il ripristino tramite la funzione nativa di SQLite `sorgente.backup(destinazione)`.
    *   [x] Gestire ed evitare errori di blocco (*Database file is locked*) chiudendo temporaneamente eventuali cursori attivi.
*   [x] **Barriere di Sicurezza & Prevenzione Errori**
    *   [x] **Backup Preventivo Immediato:** All'istante prima di sovrascrivere il database con il vecchio backup, creare una copia speciale `database_emergenza_pre_ripristino.db`.
    *   [x] **Interfaccia di Doppia Conferma (Modal):** Schermata di blocco che richiede all'utente di confermare l'azione digitando manualmente la parola *"RIPRISTINA"* per sbloccare il pulsante d'invio.
*   [x] **Interfaccia Grafica (Settings UI)**
    *   [x] Creare il file `templates/settings.html` integrato con il tema scuro premium.
    *   [x] Visualizzare la tabella con i backup disponibili (Data, Ora, Dimensione in KB, pulsante "Ripristina" in rosso e pulsante "Scarica" in azzurro).
    *   [x] Aggiungere un pulsante per forzare la creazione manuale istantanea di un backup.

---

## 🚨 Fase 3: Salvagente di Emergenza & Robustezza (Manutenzione)

L'obiettivo è proteggere il sistema da crash bloccanti ed impostare solide basi per facilitare la manutenzione e la portabilità del codice.

*   [x] **Script Batch di Ripristino Esterno**
    *   [x] Creare un file `Ripristina_Database.bat` nella cartella principale del progetto.
    *   [x] In caso di corruzione grave in cui il server Flask non si avvia, lo script deve consentire all'utente di selezionare e ripristinare l'ultimo backup funzionante direttamente dal terminale Windows.
*   [x] **Separazione delle Configurazioni (File `.env`)**
    *   [x] Spostare tutte le configurazioni cablate (porte, percorsi database, cartelle PDF, chiavi segrete) in un file `.env` esterno per massimizzare la portabilità tra computer.
*   [x] **Registro Log Centralizzato (`app.log`)**
    *   [x] Implementare il modulo `logging` nativo di Python per registrare automaticamente errori, avvii e azioni critiche (como i ripristini dei backup) in un file di log locale (`database/app.log`).
*   [ ] **Scomposizione Modulare di `app.py`**
    *   [ ] Suddividere il file monolitico `app.py` (>1000 righe) in moduli riutilizzabili e più corti (es. `db_utils.py` per le connessioni, `pdf_utils.py` per la logica di stampa, e Blueprint di Flask per dividere le rotte).

---

## 🚀 Fase 4: Funzionalità Avanzate & Tracciabilità (GMP/GLP Ready)

L'obiettivo è elevare il livello di qualità, tracciabilità e conformità regolatoria del software per contesti industriali/clinici.

*   [ ] **Blocco di Sicurezza "QC Gate" (Controllo Qualità)**
    *   [ ] Nella pagina di **Scarico Automatico (Picking List)**, impedire la selezione di lotti che non abbiano lo stato `appr = 'OK'` (Approvato QC).
    *   [ ] Visualizzare un badge rosso bloccante in corrispondenza dei lotti in stato di quarantena o non ancora approvati.
*   [x] **Avvisi e Notifiche di Scadenza (Early Warning Dashboard)**
    *   [x] Mostrare avvisi di tipo *Warning* sulla Dashboard per i lotti attivi che **scadranno entro i prossimi 15-30 giorni**.
    *   [x] Visualizzare alert bloccanti per eventuali lotti scaduti ancora disponibili a magazzino.
    *   [x] Evidenziare in arancione i prodotti che si trovano sotto la soglia di **Scorta Minima**.
*   [ ] **Integrazione con Lettori Barcode / QR Code**
    *   [ ] Aggiungere un input globale o tasto di ricerca rapida con focus automatico per scansionare etichette.
    *   [ ] Permettere l'identificazione istantanea del lotto scansionato per compilare i campi del prelievo senza digitazione.
*   [x] **Registro Modifiche ed Audit Trail (Data Integrity)**
    *   [x] Creare la tabella `Audit_Trail` nel database (`id`, `data_ora`, `operatore`, `azione`, `tabella_interessata`, `vecchio_valore`, `nuovo_valore`).
    *   [x] Salvare in automatico ogni modifica o eliminazione di lotti/prodotti effettuata dagli operatori per garantire la conformità con i requisiti regolatori sulla tracciabilità dei dati.
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
*   [ ] **Modalità ad Alto Contrasto (Light/Dark Switch)**
    *   [ ] Aggiungere un interruttore per alternare il tema scuro premium con un tema chiaro ad alta visibilità, facilitando la lettura del magazzino sotto cappe o in stanze molto illuminate.
*   [ ] **Micro-animazioni per Feedback Visivo**
    *   [ ] Inserire transizioni CSS fluide per hover e focus su bottoni, righe delle tabelle e input, dando una sensazione di reattività immediata.

---

## 🔮 Fase 6: Idee di Espansione Futura (Opzionali / In Forse)

L'obiettivo è tracciare idee enterprise ad alto valore aggiunto, utili qualora l'applicazione debba crescere in futuro verso un contesto commerciale, multi-utente o rigidamente conforme alle normative farmaceutiche.

*   [ ] **Validazione Rigida dei Dati all'Ingresso**
    *   [ ] Integrare controlli formali sui moduli (es. WTForms) per verificare che le quantità, date e nomi inseriti siano conformi e puliti prima di salvare nel database SQLite, evitando dati incongruenti.
*   [ ] **Introduzione Graduale di un ORM (SQLAlchemy)**
    *   [ ] Transizione da query SQL dirette espresse in stringhe di testo a un ORM come SQLAlchemy per gestire in modo sicuro e pulito le relazioni tra prodotti, lotti e prelievi.
*   [ ] **Genealogia del Lotto ("Padre-Figlio" Traceability)**
    *   [ ] Collegare i lotti delle materie prime utilizzate (padri) al lotto di prodotto finito generato dalla sintesi (figlio) per tracciare a ritroso ogni ingrediente partendo dalla dose somministrata al paziente.
*   [ ] **Controllo Accessi & Segregazione dei Ruoli (FDA 21 CFR Part 11)**
    *   [ ] Implementare un sistema di Login con ruoli distinti (Operatore, Controllo Qualità, QA/Amministratore) per garantire che chi produce non possa approvare i propri materiali.
*   [ ] **Generazione e Stampa di Etichette Fisiche con Barcode**
    *   [ ] Creare una funzione per connettere stampanti termiche (Zebra, Dymo, Brother) e generare etichette adesive con codici a barre/QR dei lotti interni da applicare sui flaconi fisici.
*   [ ] **Importazione dei Report di Sintesi (Drag & Drop)**
    *   [ ] Permettere il trascinamento dei file di log/report generati dai sintetizzatori di laboratorio (IBA, Trasis, ecc.) per estrarre e registrare in automatico le quantità scaricate.
*   [ ] **Gestione Fisica dei Controcampioni (Retained Samples Archive)**
    *   [ ] Mappare la posizione fisica dei campioni di riserva nei frigoriferi ed impostare scadenze e allarmi per lo smaltimento programmato (es. 1 anno dopo la scadenza del lotto).
