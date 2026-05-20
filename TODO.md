# 📝 Roadmap Sviluppo Futuro: Sistema di Backup & Ripristino 🧪

Questa TODO list traccia i passaggi pianificati per implementare un sistema di sicurezza dei dati a doppia barriera (locale/cloud) e un'interfaccia di ripristino self-service all'interno di **Gestore-Lab**.

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
