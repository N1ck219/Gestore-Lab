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
    *   [x] Creare the file `templates/settings.html` integrato con il tema scuro premium.
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
*   [x] **Scomposizione Modulare di `app.py`**
    *   [x] Suddividere il file monolitico `app.py` (>1000 righe) in moduli riutilizzabili e più corti (es. `db_utils.py` per le connessioni, `pdf_utils.py` per la logica di stampa, e Route Registry per dividere le rotte).

---

## 🚀 Fase 4: Funzionalità Avanzate & Tracciabilità (GMP/GLP Ready)

L'obiettivo è elevare il livello di qualità, tracciabilità e conformità regolatoria del software per contesti industriali/clinici.

*   [x] **Avvisi e Notifiche di Scadenza (Early Warning Dashboard)**
    *   [x] Mostrare avvisi di tipo *Warning* sulla Dashboard per i lotti attivi che **scadranno entro i primi 15-30 giorni**.
    *   [x] Visualizzare alert bloccanti per eventuali lotti scaduti ancora disponibili a magazzino.
    *   [x] Evidenziare in arancione i prodotti che si trovano sotto la soglia di **Scorta Minima**.
*   [x] **Registro Modifiche ed Audit Trail (Data Integrity)**
    *   [x] Creare la tabella `Audit_Trail` nel database (`id`, `data_ora`, `operatore`, `azione`, `tabella_interessata`, `vecchio_valore`, `nuovo_valore`).
    *   [x] Salvare in automatico ogni modifica o eliminazione di lotti/prodotti effettuata dagli operatori per garantire la conformità con i requisiti regolatori sulla tracciabilità dei dati.
*   [x] **Statistiche di Consumo & Data Visualization**
    *   [x] Integrare la libreria *Chart.js* per visualizzare grafici ad area/linee.
    *   [x] Mostrare il trend dei consumi mensili delle materie prime chiave (es. O-18 acqua, cassette di sintesi).
    *   [x] Monitorare il numero di cicli di sintesi eseguiti e i lotti prodotti.

---

## 🎨 Fase 5: Semplificazione dell'Interfaccia & Esperienza Utente (UX/UI)

L'obiettivo è rendere l'utilizzo dell'applicazione immediato, riducendo lo sforzo cognitivo e i passaggi ripetitivi.


*   [x] **Ricerca Intelligente Universale (Spotlight Search)**
    *   [x] Inserire una barra di ricerca centrale nella Home Page in grado di scansionare simultaneamente codici prodotto, nomi di materie prime e numeri di lotto interni.
    *   [x] Mostrare un menu a tendina istantaneo con i risultati e link diretti alle schede o ai form di modifica.
*   [x] **Guida alle Sigle di Laboratorio (Tooltips Esplicativi)**
    *   [x] Inserire micro-icone informative `🛈` accanto a sigle o campi complessi nei form (`CC`, `CA`, `Appr`, `Pz x Cf`).
    *   [x] Mostrare spiegazioni chiare al passaggio del mouse (*hover*) per facilitare l'inserimento dei dati ed eliminare dubbi operativi per i nuovi utenti.
*   [x] **Modalità ad Alto Contrasto (Light/Dark Switch)**
    *   [x] Aggiungere un interruttore per alternare il tema scuro premium con un tema chiaro ad alta visibilità, facilitando la lettura del magazzino sotto cappe o in stanze molto illuminate.
*   [x] **Ottimizzazioni dell'Interfaccia (Richieste Visive)**
    *   [x] Intestazione sticky sempre in vista nell'elenco delle materie prime (`list.html`).
    *   [x] Sfondo inset più scuro per i campi Controcampione e Distribuzione in inserimento materia prima (`add_product.html`).
    *   [x] Grigio chiaro, delicato e tratteggiato per badge `-` e `QC` non valorizzati nel Registro Lotti (`lotti_list.html`).
    *   [x] Sostituito il grigio piatto con gradienti ciano/indaco ad alta tecnologia per i filtri e dettagli nel Registro Scarichi (`storico_scarichi.html`).
    *   [x] Dimensionamento dinamico auto-adattivo basato su `scrollHeight` delle schede dettagli nel Registro Scarichi per evitare tagli di scritte e scroll bar.

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

---

## 🌟 Fase 7: Miglioramenti di Usabilità & Semplicità (UX/UI Pratica)

L'obiettivo è rendere l'interfaccia estremamente fluida, rapida e a prova di errore per gli operatori durante la routine quotidiana di laboratorio, senza aggiungere complessità infrastrutturali (come database, account o stampanti speciali).

*   [x] **Scorciatoie da Tastiera & Focus Automatico (Navigazione Rapida)**
    *   [x] **Focus all'Avvio:** Posizionare automaticamente il focus del cursore nella barra Spotlight Search all'apertura della Home Page, consentendo la digitazione immediata.
    *   [x] **Shortcut di Attivazione:** Abilitare la scorciatoia globale premendo il tasto `/` (slash) o la combinazione `Ctrl + K` per mettere a fuoco la barra di ricerca da qualsiasi punto della pagina.
    *   [x] **Pulizia Rapida & Chiusura:** Permettere di svuotare la barra e chiudere il menu a tendina premendo il tasto `Esc`.
    *   [x] **Navigazione con Frecce:** Consentire di scorrere i risultati di ricerca usando le frecce direzionali `↑` / `↓` e premere `Invio` per aprire la scheda selezionata senza usare il mouse.
*   [ ] **Scarico Rapido Contestuale dalle Tabelle (Workflow Integrato)**
    *   [ ] **Pulsanti Contestuali:** Inserire un'icona o pulsante di scarico rapido (es. `📉`) direttamente in corrispondenza di ciascun lotto attivo nelle tabelle del *Registro Lotti* e dello *Stato Magazzino*.
    *   [ ] **Redirect Precompilato:** Facendo clic sul pulsante, reindirizzare l'utente al form di *Scarico Manuale* con i campi `Materia Prima` e `Lotto` precompilati in modo del tutto automatico.
*   [x] **Compilazione Intelligente & Assistita nei Form (Prevenzione Errori)**
    *   [x] **Auto-compilazione Date:** Nei form di inserimento del lotto (`add_lotto.html`), impostare di default nel campo "Data Arrivo" la data corrente di oggi.
    *   [x] **Feedback Dinamico Giacenza:** Nel form di *Scarico Manuale*, calcolare in tempo reale tramite JS e mostrare all'operatore la giacenza residua stimata del lotto *mentre* digita la quantità (es. *"Rimangono 2.50 L su 5.00 L"* in verde, o segnalazione d'errore in rosso se si supera la giacenza).
    *   [x] **Maiuscolo Automatico (Uppercase Auto-formatting):** Nei form di inserimento lotto e nuova materia prima, forzare automaticamente in maiuscolo i caratteri digitati nei campi sensibili (es. Codici MP, Lotto Interno, Lotto Fornitore).
*   [ ] **Filtri di Visualizzazione Rapida nelle Tabelle (Pulizia Visiva)**
    *   [ ] **Toggle Lotti Attivi:** Nel *Registro Lotti*, inserire un interruttore rapido (es. pulsante o checkbox) per mostrare/nascondere con un clic i lotti esauriti o chiusi (`chiuso = 'SI'`), pulendo la visualizzazione.
    *   [ ] **Toggle Stato Allarmi:** Nello *Stato Magazzino*, inserire filtri veloci per mostrare solo le materie prime sotto la scorta minima o con lotti in scadenza.
