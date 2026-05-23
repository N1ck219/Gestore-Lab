# 🧪 Gestore-Lab — Gestione Magazzino & Tracciabilità Materie Prime

Benvenuto in **Gestore-Lab**, un'applicazione web locale sviluppata in **Python + Flask + SQLite**. Questo software è specificamente progettato per soddisfare i rigorosi requisiti di **tracciabilità, gestione del magazzino e controllo qualità (QC)** tipici di un laboratorio chimico o radiofarmaceutico (GMP compliant).

L'applicazione si distingue per un'interfaccia estremamente raffinata con **Premium Dark Theme** ad alto contrasto, ideale per l'utilizzo quotidiano su schermi di laboratorio e camera calda, offrendo al contempo micro-animazioni fluide e strumenti di produttività all'avanguardia.

---

## 🚀 1. Come Avviare il Server e Collegarsi

L'avvio dell'applicazione su sistemi Windows è completamente automatizzato ed è progettato per funzionare in modalità *zero-configuration* per l'utente finale.

### Avvio Rapido (Windows)
1. Fai doppio clic sul file **`Avvia_Programma.bat`** o **`Avvia_Programma.vbs`** situato nella cartella principale del progetto.
2. Lo script eseguirà autonomamente le seguenti azioni:
   - Verifica la presenza di Python nel sistema (in caso contrario, scarica e installa in modalità silenziosa la versione **Python 3.11**).
   - Inizializza l'ambiente virtuale (`.venv`) isolando le dipendenze.
   - Installa e aggiorna tutti i requisiti indicati in `requirements.txt`.
   - Avvia il server Flask e apre automaticamente il browser web predefinito.

### Avvio Manuale (Riga di comando / PowerShell)
Se preferisci gestire manualmente l'ambiente:
```powershell
# 1. Entra nella cartella del progetto ed attiva l'ambiente virtuale
.venv\Scripts\Activate.ps1

# 2. Avvia il server web
python app.py
```

### Come Collegarsi
Al momento dell'avvio, il server Flask rileva l'indirizzo all'interno della rete locale (LAN). È possibile connettersi da qualsiasi dispositivo (PC, Tablet, Smartphone) collegato alla stessa rete:
* **Connessione Locale:** [http://127.0.0.1:5000](http://127.0.0.1:5000) o [http://localhost:5000](http://localhost:5000)
* **Connessione in Rete LAN:** `http://[IP_LOCALE_DEL_PC]:5000` (es. `http://192.168.1.120:5000`)

---

## 📁 2. Struttura del Progetto

Il progetto segue un'architettura modulare, separando la logica di routing (backend), i dati fisici (database), le utilità di stampa/PDF e l'interfaccia web (static/templates).

```text
Gestore-Lab/
├── database/                   # Contenitore dei dati di persistenza
│   ├── database.db             # Database SQLite principale (tabelle relazionali centrali)
│   ├── backups/                # Copie di sicurezza temporizzate del database (.db, .json, .csv)
│   └── app.log                 # File di log a rotazione di sistema (RotatingFileHandler)
│
├── lista_distribuzione/        # PDF di Lista Distribuzione generati dal sistema
├── picking list/               # PDF di Picking List (prelievi di produzione) generati
├── richiesta_analisi/          # PDF di Richiesta Analisi inviati al Controllo Qualità
│
├── routes/                     # Moduli di routing dell'applicazione Flask (Backend separato)
│   ├── __init__.py             # Inizializzatore e registro centrale dei blueprint
│   ├── main.py                 # Dashboard principale e home views
│   ├── products.py             # CRUD e anagrafica delle Materie Prime
│   ├── lotti.py                # Gestione del ciclo di vita dei lotti interni e QC
│   ├── etichette.py            # Generazione, stampa e ristampa delle etichette fisiche
│   ├── scarichi.py             # Logiche di scarico manuale, prelievi FIFO ed automatici
│   ├── search.py               # Algoritmo Spotlight Search universale
│   ├── settings.py             # Pannello di amministrazione, backup e registro Audit Trail
│   └── stats.py                # Statistiche di consumo e grafici analitici
│
├── static/                     # Asset statici erogati dal server web
│   └── css/
│       └── style.css           # CSS personalizzato contenente il design system Premium Dark
│
├── templates/                  # File HTML di interfaccia (Jinja2 Templates)
│   ├── base.html               # Struttura madre (Dark Style, Navbar, Menu Impostazioni)
│   ├── index.html              # Dashboard e Spotlight Universal Search
│   ├── list.html               # Registro e anagrafica Materie Prime
│   ├── add_product.html        # Form per l'inserimento di una Nuova Materia Prima
│   ├── lotti_list.html         # Gestione e modifica in-line dei lotti registrati
│   ├── add_lotto.html          # Form per la registrazione di un lotto in ingresso
│   ├── magazzino.html          # Riepilogo giacenze aggregate e alert scorte minime
│   ├── nuova_etichetta.html    # Anteprima e stampa etichette (Bianche e Verdi 95x60mm)
│   ├── storico_etichetta.html  # Registro storico etichette e ristampa rapida
│   ├── scarico_manuale.html    # Prelievi manuali ed automatici (FIFO, Run in Bianco)
│   ├── storico_scarichi.html   # Storico cronologico dei movimenti di magazzino
│   ├── audit_trail.html        # Registro inalterabile delle attività (tracciabilità GMP)
│   ├── statistiche.html        # Grafici analitici dei consumi e report scorte
│   └── settings.html           # Strumenti di manutenzione, backup e restore database
│
├── scripts/                    # Script amministrativi di utilità
│   └── inizializza_sistema.py  # Script per pulizia totale e simulazione dell'inizio del software
│
├── app.py                      # Punto d'ingresso principale dell'applicazione Flask
├── requirements.txt            # Dipendenze Python necessarie
├── Avvia_Programma.bat         # Script Batch per l'automazione dell'avvio su Windows
└── README.md                   # Questo manuale d'uso completo
```

---

## 🖥️ 3. Documentazione Dettagliata delle Pagine

Di seguito viene analizzata singolarmente ogni schermata dell'applicazione, descrivendone accuratamente **l'aspetto visivo** (cosa si vede) e **tutte le funzioni operative** incluse.

---

### 🏠 Dashboard Principale (`index.html`)

> [!NOTE]
> Rappresenta la home page dell'applicazione e funge da centro di smistamento operativo per tutte le aree gestionali.

*   **Cosa si vede:**
    *   Una testata elegante con il titolo del laboratorio ed un design scuro e pulito.
    *   **Spotlight Universal Search:** Una barra di ricerca monolitica in stile Spotlight (Apple macOS) situata in alto al centro. Mostra l'icona di una lente d'ingrandimento e un campo di input che cattura l'attenzione visiva.
    *   **Griglia di Navigazione Principale:** Una griglia responsive con 4 schede giganti dal forte impatto cromatico e icone fluttuanti:
        *   **Stato Magazzino (Azzurro Neon):** Monitoraggio globale e alert giacenze.
        *   **Anagrafica Materie Prime (Indaco):** Configurazione e scheda dei prodotti.
        *   **Gestione Lotti (Viola Regale):** Registrazione degli arrivi, Controllo Qualità e stampa etichette.
        *   **Scarichi e Movimenti (Arancione Caldo):** Prelievi e storico dei consumi.
    *   Una barra di stato superiore (Navbar) con link rapidi di navigazione ed un menu a tendina per le **Impostazioni Amministrative** (icona a ingranaggio) che fluttua al di sopra del layout.
*   **Funzioni operative:**
    *   **Spotlight Universal Search (AJAX):** Consente di cercare in tempo reale digitando caratteri. L'algoritmo interroga simultaneamente codici prodotto, nomi materia prima e lotti interni. Cliccando su un risultato del dropdown, l'utente viene reindirizzato all'istante sul record cercato o nella pagina corrispondente.
    *   **Navigazione Rapida:** Clic sulle macro-sezioni colorate per accedere alle rispettive aree del software.

---

### 📊 Stato Magazzino & Giacenze (`magazzino.html`)

> [!TIP]
> Questa pagina offre una panoramica istantanea delle scorte fisiche aggregate del laboratorio, aggregando tutti i lotti attivi.

*   **Cosa si vede:**
    *   Un riepilogo in tempo reale dello stato delle giacenze aggregate.
    *   Le materie prime sono raggruppate in **sezioni visive separate in base alla Categoria di Magazzino** (es. *Kit*, *Filtri*, *Reagenti*, *Consumabili*).
    *   Una tabella dettagliata con colonne: Codice, Nome Materia Prima, Categoria, Giacenza Totale aggregata (somma dei lotti in uso), Unità di Misura (pz o g), Stato Scorte, e la Scadenza Imminente.
    *   **Alert Scorte Minime:** Se la giacenza di un prodotto scende sotto la soglia impostata, la cella dello stato si illumina in rosso acceso mostrando la dicitura **"Scorta Minima Superata!"**.
    *   **Alert Scadenza Imminente:** Mostra la data di scadenza più vicina tra i lotti attivi per quel reagente, evidenziandola se è imminente.
*   **Funzioni operative:**
    *   **Aggregazione in Tempo Reale:** Calcola automaticamente le somme delle giacenze dei soli lotti attivi e non esauriti.
    *   **Filtro Istantaneo:** Campo di testo per filtrare rapidamente i materiali visualizzati per nome o codice.
    *   **Monitoraggio Qualità:** Individuazione tempestiva del lotto prioritario da consumare.

---

### 📋 Anagrafica Materie Prime (`list.html`)

> [!NOTE]
> È il catalogo centrale del software, dove vengono censiti i prodotti gestiti nel magazzino.

*   **Cosa si vede:**
    *   L'elenco in forma tabellare di tutti i reagenti e dispositivi registrati nell'anagrafica del laboratorio.
    *   Colonne: Codice, Nome Materia Prima, Nome per Etichette, Unità di Misura, Destinazione d'Uso, Fornitore Standard, Controcampione Richiesto (SI/NO), Distribuzione Richiesta (SI/NO), Scorta Minima e Ordine Magazzino.
    *   **Pulsante Modifica:** Situato all'estrema destra di ogni riga.
    *   In alto, il pulsante **"Nuova Materia Prima"** per procedere a un nuovo inserimento.
*   **Funzioni operative:**
    *   **Modifica In-Line tramite Modal:** Facendo clic su "Modifica", si apre un modal precompilato che consente di cambiare le proprietà anagrafiche del materiale (es. aggiornare il nome per le etichette, modificare la scorta minima o cambiare l'uso).
    *   Il salvataggio aggiorna istantaneamente il database SQLite, rinfresca la tabella tramite Flask e genera un log dell'operazione nell'Audit Trail GMP.

---

### ➕ Nuova Materia Prima (`add_product.html`)

*   **Cosa si vede:**
    *   Un pannello centrale di inserimento con campi di input moderni ed eleganti dal design scuro.
    *   Campi richiesti: Codice MP (univoco), Nome Prodotto, Nome File, Unità di Misura (g o pz), Nome per Etichette (nome compatto stampato), Uso/Destinazione, Codice Fornitore, Controcampione, Distribuzione, Scorta Minima e Categoria Magazzino.
*   **Funzioni operative:**
    *   **Registrazione Prodotto:** Aggiunge una nuova materia prima nell'anagrafica.
    *   **Validazione lato client/server:** Controlla l'univocità del codice primario impedendo duplicazioni e verifica che i campi obbligatori siano compilati, mostrando avvisi flash dinamici.

---

### 📦 Gestione Lotti (`lotti_list.html`)

> [!IMPORTANT]
> Schermata operativa cruciale che gestisce la qualità dei singoli lotti di reagenti in magazzino.

*   **Cosa si vede:**
    *   **Filtri di Stato in alto:** Pulsanti per alternare la visualizzazione tra **Lotti Attivi (in uso)**, **Lotti Esauriti (chiusi)** o **Tutti i Lotti**.
    *   Tabella principale con colonne: Lotto Interno, Codice MP, Nome MP, Fornitore, Lotto Fornitore, Data Arrivo, Data Scadenza, Giacenza, Stato Approvazione (Appr.) e Stato Etichetta (Etich.).
    *   **Indicatori di Stampa Etichette:** Due pallini (dot) colorati con etichette 'B' (Etichetta Bianca) e 'V' (Etichetta Verde) indicano visivamente se le etichette fisiche sono già state stampate.
    *   Pulsante **"Modifica"** (icona a matita) e collegamento per la generazione di etichette per ogni riga.
*   **Funzioni operative:**
    *   **Filtro Dinamico:** Consente di escludere i lotti esauriti per evitare confusione visiva.
    *   **Gestione Qualità e QC (Modal di Modifica):** Consente di aggiornare tutti i parametri di conformità del lotto:
        - *Data consegna al QC*
        - *Data approvazione* (l'inserimento imposta automaticamente lo stato di approvazione `appr` su `'OK'`)
        - *Giacenza residua*
        - *Stato Appr.* (`OK` o `-`)
        - *Stato Etich.* (`OK` o `-`)
        - *Controcampione (CC)*, *Reparto*, *Stato Chiuso* (se impostato su "SÌ", il lotto viene archiviato).
    *   **Inalterabilità Audit Trail:** Ogni modifica a un lotto (ad es. cambio di giacenza o approvazione) confronta i vecchi valori con i nuovi e ne esegue il log rigido in `Audit_Trail`.

---

### 📦 Nuovo Lotto (`add_lotto.html`)

*   **Cosa si vede:**
    *   Un form guidato ed elegante per inserire un lotto in arrivo.
    *   **Ricerca Assistita Materia Prima:** Un campo di input dotato di dropdown a discesa che permette di selezionare rapidamente la materia prima anagrafica digitandone il nome o il codice.
    *   Campi: Lotto Interno, Data Arrivo, Lotto Fornitore, Fornitore (con autocompletamento intelligente dei fornitori qualificati in anagrafica), Data Scadenza, Quantità Arrivata e Pezzi per confezione.
*   **Funzioni operative:**
    *   **Associazione Anagrafica:** Collega il lotto in arrivo alla corretta materia prima nel database.
    *   **Validazione Date:** Blocca la sottomissione del form se la data di scadenza è precedente alla data di arrivo.
    *   **Stato Iniziale QC:** Crea il lotto con stato di approvazione ed etichetta inizializzati come non approvati (`'-'`), in attesa del controllo QC.

---

### 🏷️ Nuova Etichetta (`nuova_etichetta.html`)

> [!IMPORTANT]
> Questa pagina gestisce la generazione e la stampa fisica delle etichette adesive (layout rigido 95mm x 60mm) da applicare sui reagenti.

*   **Cosa si vede:**
    *   Una tabella superiore per selezionare il lotto desiderato, dotata di indicatori di stampa (Bianca e Verde).
    *   **Pannello di Anteprima Live Doppia:** Visualizza in tempo reale:
        1.  **Etichetta Bianca (Standard):** Contiene Codice Prodotto, Nome MP, Lotto Interno, Data Arrivo, Lotto Fornitore, Quantità, Operatore, e un Barcode dinamico.
        2.  **Etichetta Verde (Approvato):** Sfondo verde brillante con scritta "APPROVATO", Codice, Nome MP, Lotto Interno, Fornitore, Lotto Fornitore, Data Scadenza, Data Approvazione, e l'Operatore QC autorizzato.
*   **Funzioni operative:**
    *   **Vincoli Rigidi GMP per l'Etichetta Verde:** Il pulsante di stampa dell'etichetta verde è abilitato unicamente se:
        - L'etichetta bianca è stata stampata.
        - La data di consegna al QC è configurata.
        - Lo stato di approvazione (`appr`) del lotto è impostato su `'OK'`.
    *   **Registrazione Storico Etichette:** Cliccando su "Stampa", l'evento viene salvato nel database in `Storico_Etichette`. Se viene stampata un'etichetta verde, lo stato `etich` del lotto viene automaticamente aggiornato su `'OK'`.
    *   **Stampa Ottimizzata:** Utilizza regole CSS `@media print` per adattare la griglia di stampa su fogli adesivi A4 (griglie standard 2x4 o 3x8) eliminando le intestazioni del browser.

---

### 🗂️ Storico Etichette (`storico_etichetta.html`)

*   **Cosa si vede:**
    *   Tabella riepilogativa cronologica delle etichette stampate in laboratorio.
    *   Colonne: Data/Ora Stampa, Lotto Interno, Codice e Nome MP, Data Arrivo, Quantità, Tipo Stampa (Bianco/Verde) e Operatore.
*   **Funzioni operative:**
    *   **Filtri e Ricerca:** Ricerca rapida per lotto o tipo etichetta.
    *   **Ristampa Rapida:** Consente agli operatori di ristampare un'etichetta deteriorata con un solo clic bypassando i passaggi del QC originale.

---

### 📉 Gestione Scarichi & Prelievi (`scarico_manuale.html`)

> [!IMPORTANT]
> È il cuore funzionale del magazzino, diviso in due aree operative fondamentali per gestire le uscite dei reagenti.

*   **Cosa si vede:**
    *   **Area di Sinistra - Scarico Manuale:**
        *   Un form pulito per registrare singoli prelievi manuali (es. per controcampionamento, analisi o scarto).
        *   Campi: Data scarico, Materiale (dropdown dinamico), Lotto Interno (mostra solo i lotti attivi con giacenza reale del materiale selezionato), Quantità da scaricare, Causale e Operatore.
    *   **Area di Destra - Scarico Automatizzato (Picking List):**
        *   Un menu per selezionare il profilo di una ricetta di produzione standard (es. *Picking FDG (Synthera)*, *Trasis*, *FBB*, *FCH*, *PYL*, *DOTA*, ecc.).
        *   Il checkbox **"Run in bianco"** per abilitare l'uso di reagenti non ancora approvati nei test di prova.
        *   Una **tabella dinamica** che si popola all'istante quando si sceglie una ricetta, visualizzando tutti i componenti previsti, proponendo il **lotto interno ideale applicando la logica FIFO** e controllando la sicurezza.
*   **Funzioni operative:**
    *   **Scarico Manuale:** Sottrae la quantità indicata dal database. Blocca l'operazione se la quantità richiesta è superiore alla giacenza reale.
    *   **Algoritmo FIFO:** Seleziona automaticamente il lotto approvato con data di scadenza più imminente per ottimizzare la rotazione del magazzino.
    *   **Generazione Picking List in PDF:** Crea ed esporta istantaneamente una Picking List ufficiale in formato PDF (salvata in `picking list/`), aprendola nel browser.
    *   **Bypass "Run in Bianco":** Se attivo, preimposta l'Acqua arricchita 18O (codice `'424'`) con l'eventuale lotto non ancora approvato dal QC, consentendo l'avvio della sintesi di prova.
    *   **Blocco Sicurezza (Etichetta Verde):** Impedisce tassativamente lo scarico se uno o più lotti proposti per la produzione non sono stati approvati dal QC (stato `etich` non su `OK` e nessun record "VERDE" stampato), a meno che non si tratti del bypass per il Run in bianco.
    *   **Blocco Sicurezza (Lotto Scaduto):** **Controllo rigido di scadenza**. Lo scarico automatizzato viene interrotto con errore bloccante se anche uno solo dei lotti selezionati risulta scaduto alla data dello scarico (`data_scadenza < data_scarico`).

---

### 📜 Storico Scarichi (`storico_scarichi.html`)

*   **Cosa si vede:**
    *   Il registro cronologico completo di tutti i movimenti in uscita effettuati in magazzino.
    *   Tabella con colonne: Data scarico, Codice MP, Nome MP, Lotto Interno, Quantità, Causale, Operatore e il **Lotto Prodotto finale** associato.
*   **Funzioni operative:**
    *   **Filtri e Ricerca:** Consente di filtrare per testo, operatore o data.
    *   **Tracciabilità del Prodotto Finito:** Correlazione diretta ed inalterabile tra le materie prime consumate ed il lotto di radiofarmaco sintetizzato.

---

### 🛡️ Registro Audit Trail (`audit_trail.html`)

> [!CAUTION]
> Questa pagina fornisce la tracciabilità delle attività richieste dalle severe linee guida di qualità GMP (Annex 11).

*   **Cosa si vede:**
    *   Una griglia tabellare rigida non modificabile contenente l'elenco cronologico di tutte le modifiche apportate nel sistema.
    *   Colonne: ID, Data/Ora, Operatore, Azione, Tabella Interessata, Vecchio Valore e Nuovo Valore.
    *   I valori sono formattati in JSON strutturato e facilmente leggibile per visualizzare esattamente i singoli campi modificati (es. giacenza da 10 a 5, o stato approvazione da '-' a 'OK').
*   **Funzioni operative:**
    *   **Filtri di consultazione:** Ricerca per operatore, azione o tabella.
    *   **Sola Lettura:** Non esiste alcuna interfaccia utente o funzione per eliminare, alterare o azzerare i record dell'Audit Trail dal frontend, garantendo l'integrità assoluta del log di sistema.

---

### 📈 Statistiche & Analisi (`statistiche.html`)

*   **Cosa si vede:**
    *   Una dashboard analitica con metriche chiave e grafici interattivi.
    *   Metriche: Numero totale di materie prime, lotti attivi, scarichi eseguiti nell'ultimo mese e alert di scorte minime attivi.
    *   Grafici: Consumo mensile dei prodotti e andamento temporale degli scarichi.
*   **Funzioni operative:**
    *   Analisi predittiva sui reagenti in esaurimento in base alle medie storiche.
    *   Generazione visiva e consultazione di reportistica dettagliata dei consumi.

---

### ⚙️ Impostazioni & Utilità (`settings.html`)

*   **Cosa si vede:**
    *   Un pannello amministrativo strutturato in sezioni chiare:
        *   **Backup Database:** Opzioni per scaricare o salvare sul server backup di sicurezza in formato `.db`, o esportare le tabelle in `CSV` o `JSON`.
        *   **Ripristino Database:** Sezione con input file per caricare un backup `.db` esterno.
        *   **Svuotamento Temporanei:** Strumento per ripulire le cartelle PDF dai vecchi documenti generati per liberare spazio su disco.
*   **Funzioni operative:**
    *   **Esportazione Dati:** Genera ed esporta all'istante copie conformi del database.
    *   **Ripristino Database:** Esegue l'importazione di un file SQLite con validazione preliminare della firma del database per evitarne la corruzione.
    *   **Pulizia File Temporanei:** Svuota in sicurezza le cartelle `lista_distribuzione`, `picking list` e `richiesta_analisi`.
