# 📝 Roadmap Sviluppo Futuro: Sistema di Backup & Miglioramenti Pratici 🧪

Questa TODO list traccia i passaggi pianificati per migliorare **Gestore-Lab** in modo incrementale. Abbiamo spostato le funzionalità complesse di livello industriale in fondo ("in forse"), concentrandoci su soluzioni **estremamente semplici, pratiche e ad alto impatto** per l'utilizzo quotidiano e la manutenibilità offline del laboratorio.

---

## 🚀 Funzionalità Già Implementate (Portabilità Totale)
*   [x] **Portabilità Dinamica dei Percorsi** (Risolto!)
    *   [x] Rimosso il percorso assoluto fisso `D:\python\Gestore-Lab` per il salvataggio dei PDF delle Picking List; ora `app.py` utilizza un percorso relativo alla cartella del server.
    *   [x] Rimosso il percorso assoluto fisso `c:\Users\Nicola\Desktop\Gestore-Lab` nel file `Avvia_Programma.bat`; ora rileva automaticamente la cartella corrente tramite `%~dp0`. Il programma può essere spostato in qualsiasi unità o cartella senza rompersi!

---

## 🛠️ Fase 1: Creazione Automatica dei Backup (Sicurezza Locale)

L'obiettivo è garantire la creazione automatica di copie storiche del database ad ogni avvio dell'applicazione per prevenire perdite accidentali.

*   [ ] **Integrazione in `Avvia_Programma.bat`**
    *   [ ] Creare in automatico la cartella `database/backups/` se mancante.
    *   [ ] Estrarre la data e l'ora corrente del sistema tramite script Batch.
    *   [ ] Copiare il file attivo `database.db` rinominandolo in `database_backup_YYYYMMDD_HHMMSS.db`.
*   [ ] **Algoritmo di Rotazione Automatico (Risparmio Spazio)**
    *   [ ] Scrivere uno script leggero in Python (chiamato all'avvio in `app.py`) che scansiona `database/backups/`.
    *   [ ] Mantenere in automatico solo le ultime **30 copie storiche** più recenti ed eliminare quelle più vecchie per non occupare spazio sul disco.

---

## 🖥️ Fase 2: Pannello Impostazioni & Ripristino Web "a Caldo" (Flask UI)

Consentire agli operatori del laboratorio di controllare lo stato dei backup ed effettuare ripristini storici direttamente dal browser in totale autonomia.

*   [ ] **Struttura Backend in `app.py`**
    *   [ ] Creare la rotta `@app.route('/settings')` per la gestione dell'applicazione.
    *   [ ] Creare una funzione per scansionare e listare dinamicamente tutti i file `.db` presenti in `database/backups/` ordinati dal più recente.
*   [ ] **Ripristino Sicuro "a Caldo" (SQLite Online Backup API)**
    *   [ ] Implementare il ripristino tramite la funzione nativa di SQLite `sorgente.backup(destinazione)`.
    *   [ ] Gestire ed evitare errori di blocco (*Database file is locked*) chiudendo temporaneamente eventuali cursori attivi prima dello swap.
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
    *   [ ] In caso di corruzione grave in cui il server Flask non si avvia, lo script deve consentire all'utente di selezionare e ripristinare l'ultimo backup funzionante direttamente dal terminale Windows tramite comandi standard.

---

## 📈 Fase 4: Idee "Semplicissime" ad Alto Impatto (Operatività & Manutenibilità)

Miglioramenti a bassissimo costo di sviluppo che "svoltano" la gestione quotidiana, garantendo la pulizia dei dati e la robustezza del sistema offline.

*   [ ] **Prevenzione Corruzione su OneDrive ("Safe Temp Run" via Batch)**
    *   *Idea:* Evitare la corruzione dovuta alla sincronizzazione in tempo reale di OneDrive mentre SQLite è aperto e attivo.
    *   *Azione:* Modificare `Avvia_Programma.bat` per copiare il database attivo in una cartella locale temporanea (es. `%temp%\GestoreLab_Active`), far puntare Flask a quel file locale per tutta la durata del lavoro, e ricopiarlo nella cartella principale (sincronizzata con OneDrive) solo al momento della chiusura del server.
*   [ ] **Evidenziazione Visiva Automatica "Sotto Scorta"**
    *   *Idea:* Sapere subito cosa sta finendo senza dover fare calcoli a mente o navigare in menu complessi.
    *   *Azione:* Nella tabella **Stato Magazzino**, se la giacenza totale di un articolo scende al di sotto del valore `scorta_minima` impostato, colorare il badge in arancione o mostrare un'icona di alert ⚠️ per segnalare l'imminente necessità di ordine.
*   [ ] **Esportazione Rapida Excel / CSV (Zero Dipendenze)**
    *   *Idea:* Consentire all'operatore di estrarre i dati in formato compatibile con Excel per statistiche, stampe o inventari veloci.
    *   *Azione:* Inserire un pulsante *"Esporta in CSV"* nelle pagine **Stato Magazzino** e **Storico Scarichi**. Generare il download al volo tramite la libreria standard Python `csv` (con separatore `;`), apribile direttamente in Excel in un clic.
*   [ ] **Dropdown per Unità di Misura (Pulizia dei Dati)**
    *   *Idea:* Evitare che inserimenti diversi della stessa unità (es. `g`, `grammi`, `G`, `gr`) inquinino le statistiche.
    *   *Azione:* Nel form di aggiunta prodotto, trasformare il campo di testo libero in un menu a tendina con opzioni predefinite (`g`, `ml`, `Pz`, `Kit`) e una voce "Altro" che abilita la scrittura manuale.
*   [ ] **Filtro Rapido per Nascondere Lotti Esauriti**
    *   *Idea:* Con il passare dei mesi, il registro dei lotti accumulerà decine di lotti con giacenza a `0.0`.
    *   *Azione:* Aggiungere un semplice interruttore/checkbox in alto nella pagina lotti *"Nascondi lotti esauriti"*. Tramite poche righe di JavaScript client-side, nasconderà all'istante le righe con giacenza pari a zero, mantenendo la tabella compatta e leggibile.
*   [ ] **Proposta di Scadenza Predefinita (Shelf-Life Suggerita)**
    *   *Idea:* Alcuni materiali hanno scadenze fisse rispetto alla data di arrivo (es. piastre TSA 3 mesi, cassette 1 anno).
    *   *Azione:* Quando l'operatore inserisce la data di arrivo nel modulo lotto, mostrare un piccolo suggerimento o calcolo automatico per velocizzare l'inserimento, lasciando comunque il campo modificabile liberamente.
*   [ ] **Duplicazione Rapida delle Materie Prime ("Clona")**
    *   *Idea:* Velocizzare l'inserimento di prodotti simili.
    *   *Azione:* Aggiungere un tasto "Clona" nel registro prodotti per pre-compilare il form con i dati di un prodotto esistente, lasciando da cambiare solo il codice interno.

---

## 🎨 Fase 5: Esperienza Utente & UI Semplificata (UX)

*   [ ] **Dashboard Consolidata (Alert in Home)**
    *   [ ] Mostrare piccoli contatori direttamente sopra le card della Home Page (es. *"⚠️ 2 prodotti sotto scorta"* nella card Magazzino, *"🔴 3 lotti scaduti"* nella card Lotti) per una panoramica immediata.
*   [ ] **Suggerimenti di Autocompilazione Fornitore**
    *   [ ] Quando si inserisce un nuovo lotto, mostrare un menu a tendina o un autocompletamento per il campo "Fornitore" basato sui fornitori già memorizzati, per evitare errori di battitura (es. `Merck`, `merck-sigma`, `Merck srl`).
*   [ ] **Guida Rapida alle Sigle di Laboratorio (Tooltips)**
    *   [ ] Inserire una micro-icona informativa `🛈` accanto ai campi complessi nei form (`CC`, `CA`, `Appr`, `Pz x Cf`). Mostrare una spiegazione chiara al passaggio del mouse (*hover*) per facilitare l'inserimento per i nuovi operatori.

---

## 🔮 Fase 6: Estensioni Complesse & Integrazioni Regolatorie (IN FORSE / DA VALUTARE)

*Queste funzionalità rappresentano estensioni avanzate di livello industriale/GMP, tipicamente non presenti nei fogli Excel. Sono tenute in considerazione come possibili sviluppi futuri da valutare solo se le necessità del laboratorio dovessero scalare significativamente.*

*   [ ] **Genealogia del Lotto**
    *   *Descrizione:* Collegamento automatico tracciabile tra le materie prime esatte consumate e il lotto di radiofarmaco finale prodotto.
*   [ ] **Controllo Accessi basato su Ruoli (Compliance FDA 21 CFR Part 11)**
    *   *Descrizione:* Sistema di autenticazione con credenziali separate per Operatori, Controllo Qualità (QA/QC) e Amministratori, con firma elettronica.
*   [ ] **Integrazione Stampante Termica (Barcode / QR Code)**
    *   *Descrizione:* Stampa di etichette adesive fisiche con QR code per tracciare i lotti interni ed eseguire carichi/scarichi tramite lettore ottico.
*   [ ] **Importazione File di Report di Sintesi (IBA / Trasis)**
    *   *Descrizione:* Funzionalità di Drag & Drop dei report generati dai sintetizzatori per calcolare e scaricare i consumi dei reagenti in automatico.
*   [ ] **Modulo Gestione Controcampioni Avanzato**
    *   *Descrizione:* Tracciamento del posizionamento fisico del controcampione (es. Frigo A, Cassetto 3) e promemoria di smaltimento calcolato a 1 anno dalla scadenza.
