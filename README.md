# 🧪 Gestore-Lab — Manuale d'Uso e Documentazione di Magazzino

Benvenuto nel **Gestionale di Laboratorio (Gestore-Lab)**, un'applicazione software sviluppata in **Python + Flask + SQLite** per centralizzare, ottimizzare e semplificare la gestione quotidiana del magazzino e delle attività correlate.

Il sistema offre un controllo completo e intuitivo sulle giacenze in tempo reale, consentendo al personale di monitorare l'intero ciclo di vita dei materiali, dall'ingresso delle materie prime fino al loro scarico. L'applicazione riduce al minimo il rischio di errori manuali e garantisce la **tracciabilità totale (Audit Trail)** di ogni singolo movimento, supportando l'efficienza e gli standard qualitativi (GMP compliant) del laboratorio.

L'interfaccia è nativamente progettata e ottimizzata per la **Modalità Notte (Tema Scuro Premium)**, che garantisce la massima coerenza visiva e il contrasto ideale tra tutti gli elementi grafici su schermi di laboratorio e camera calda.

---

## 🚀 1. Avvio e Accesso al Sistema

Il software non richiede complesse procedure di configurazione manuale. L'avvio su sistemi Windows è completamente automatizzato ed è progettato per funzionare in modalità *zero-configuration*.

### Prima Attivazione e Avvio Rapido
1. Localizzare la cartella principale del software.
2. Eseguire un doppio clic sul file **`Avvia_Programma.vbs`** (in alternativa, è possibile usare `Avvia_Programma.bat`).
3. **Nota per il primo avvio:** Durante la prima esecuzione, il sistema verificherà la presenza dei componenti necessari, scaricando e installando automaticamente gli aggiornamenti mancanti. Questa operazione iniziale potrebbe richiedere alcuni minuti. I successivi avvii saranno quasi istantanei.
4. All'avvio del programma, si aprirà automaticamente una nuova scheda nel browser web predefinito, mostrando la schermata principale del gestionale.

### Accesso al Gestionale
L'applicazione è progettata per funzionare all'interno della rete locale, permettendo la consultazione anche da altri dispositivi (PC, Tablet o Smartphone) connessi alla stessa rete Wi-Fi:

*   **Accesso Locale (sullo stesso PC):** In caso di chiusura accidentale della finestra del browser, è possibile riprendere l'attività aprendo una nuova scheda nel browser e digitando il seguente indirizzo nella barra degli URL:
    [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
*   **Accesso Remoto (da altri dispositivi della stessa rete):** Digitare nella barra degli indirizzi del browser:
    `http://<Indirizzo_IP>:5000/`
    Per identificare l'esatto indirizzo IP del PC principale (il computer su cui è stato avviato il programma tramite il file `.vbs` o `.bat`):
    1. Aprire il terminale dei comandi del PC principale (digitando `cmd` nella barra di ricerca di Windows).
    2. Digitare il comando `ipconfig` e premere Invio.
    3. Individuare la voce **Indirizzo IPv4** (es. `192.168.1.120`). Sostituire questo valore numerico all'interno del link sopra indicato.

---

## 📁 2. Struttura del Progetto

Il progetto segue un'architettura modulare e pulita per separare la persistenza dei dati, la logica di routing, le utilità di stampa/PDF e l'interfaccia web (static/templates):

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

## 🖥️ 3. Struttura della Schermata Principale

L'interfaccia utente è suddivisa in quattro macroaree principali per facilitare una navigazione immediata e intuitiva:
1. **Pulsanti Ausiliari (in alto a destra):** Consentono l'accesso rapido alle statistiche, alle impostazioni avanzate, alle funzioni di backup, allo storico delle operazioni (Audit Trail) e all'interruttore del tema cromatico.
2. **Barra Spotlight (centrale in alto):** Lo strumento di ricerca globale e navigazione rapida basato su codici o nomi.
3. **Schede Operative (Card centrali):** Quattro pulsanti riquadrati che indirizzano alle diverse funzionalità principali del gestionale (Stato Magazzino, Materie Prime, Lotti, Scarichi).
4. **Pannello degli Avvisi (sul lato destro):** Un'area dedicata alla segnalazione visiva delle scorte in esaurimento o dei lotti in scadenza.

---

## 🔍 4. Barra Spotlight: Navigazione Rapida e Ricerca Globale

La barra Spotlight, posizionata centralmente nella parte superiore della schermata principale, è lo strumento principale per la ricerca globale all'interno del gestionale. Consente di rintracciare istantaneamente codici interni, lotti o operazioni di scarico, offrendo al contempo scorciatoie per le principali attività operative.

### Scorciatoie da Tastiera
Per rendere il flusso di lavoro più efficiente e limitare l'uso del mouse, l'interfaccia supporta i seguenti comandi rapidi da tastiera:
*   **Attivazione Automatica:** All'apertura della schermata principale, il cursore si posiziona automaticamente all'interno della barra, pronto per la digitazione.
*   `CTRL + K`: Sposta istantaneamente il cursore all'interno della barra di ricerca da qualsiasi punto della pagina in cui ci si trovi.
*   `Frecce Direzionali (Su/Giù) + Invio`: Permettono di scorrere l'elenco dei risultati suggeriti sotto la barra e di selezionare la voce desiderata.
*   `ESC`: Cancella interamente il testo digitato, azzera i filtri e chiude il pannello dei risultati di ricerca.

### Categorie di Ricerca e Azioni Rapide
La barra analizza in tempo reale i caratteri digitati e suddivide i risultati in tre categorie principali, proponendo azioni rapide per accedere direttamente alle funzioni correlate:

#### A. Materie Prime
Quando si digita il nome o il codice di una materia prima, il sistema offre tre opzioni di navigazione:
*   **Registro:** Reindirizza alla pagina generale del registro delle materie prime, applicando automaticamente un filtro sul prodotto selezionato.
*   **Lotti:** Mostra l'elenco completo di tutti i lotti (attivi e storici) associati specificamente a quella materia prima.
*   **Scarica:** Indirizza direttamente alla pagina di Scarico Manuale, precompilando il modulo con l'anagrafica del prodotto selezionato per accelerare la procedura.

#### B. Lotti di Magazzino
Cercando un codice lotto specifico, l'operatore può accedere rapidamente a:
*   **Vedi lotto:** Apre la scheda informativa dettagliata del singolo lotto nel registro, mostrandone lo stato di conformità, i quantitativi residui e le scadenze.
*   **Etichetta:** Porta alla sezione di generazione e stampa delle etichette, con i dati del lotto già inseriti.
*   **Scarica:** Avvia la procedura di Scarico Manuale impostando automaticamente il lotto in questione come oggetto del prelievo.

---

## 📦 5. Documentazione Dettagliata delle Schede Operative (Card)

### 📊 A. Stato Magazzino
La scheda Stato Magazzino offre una panoramica centralizzata e in tempo reale di tutte le materie prime e i materiali censiti nel laboratorio. La schermata è strutturata su due livelli di lettura: una vista generale aggregata e una vista di dettaglio dedicata ai singoli lotti.

#### 1. Schermata Principale (Vista Aggregata)
All'apertura della sezione viene mostrato l'elenco completo dei materiali. Per ciascuna voce, il sistema calcola e mostra automaticamente i seguenti indicatori:
*   **Giacenza Totale:** Rappresenta la disponibilità complessiva del materiale in magazzino, calcolata sommando le quantità residue di tutti i relativi lotti attivi.
*   **Data di Scadenza:** Al fine di garantire la sicurezza e l'integrità delle analisi, il sistema individua e mostra la scadenza più ravvicinata tra tutti i lotti disponibili per quel materiale.
*   **Scorta Minima e Sistema di Allerta:** Indica la soglia numerica minima di sicurezza stabilita per quel prodotto. Qualora la giacenza totale dovesse scendere al di sotto di questo valore, il sistema genererà automaticamente un messaggio visivo di avviso sia in questa schermata sia nel pannello degli avvisi della home, segnalando la necessità di un riordino.

#### 2. Dettaglio Prodotto (Vista Lotti)
Selezionando una riga corrispondente a un materiale, l'interfaccia si espande mostrando la scomposizione analitica di tutti i lotti fisicamente presenti in magazzino. In questa schermata sono presenti elementi interattivi e indicatori specifici:
*   **Stato "In Uso":** Questo indicatore contrassegna il lotto che il software suggerirà o preleverà prioritariamente durante le operazioni. Il sistema applica automaticamente la **logica FEFO (First Expired, First Out)**, impostando come *"In Uso"* il lotto con la data di scadenza più vicina.
*   **Ultimo Utilizzo (Campo Interattivo):** Cliccando su questa voce, si accede a una finestra informativa che mostra i dettagli relativi all'ultima movimentazione registrata per quel lotto (es. data, ora e operatore).
*   **Giacenza del Lotto (Campo Interattivo):** Cliccando sul valore numerico della giacenza del singolo lotto, l'utente viene reindirizzato direttamente al Registro Scarichi. In questa pagina è possibile tracciare lo storico dei prelievi e verificare con precisione in quali sessioni di lavoro o analisi è stato impiegato quel lotto specifico.

---

### 📋 B. Materie Prime
Questa sezione descrive la gestione anagrafica dei materiali del laboratorio. Attraverso questo modulo è possibile censire nuovi articoli o aggiornare e rimuovere quelli già esistenti a sistema.

#### 1. Nuova Materia Prima (Inserimento Anagrafica)
La pagina consente l'inserimento nel database di un articolo o di un reagente non ancora registrato.
*   **Procedura di inserimento:** Compilare tutti i campi obbligatori relativi alle specifiche del materiale (es. descrizione, unità di misura, soglie) e verificare l'esattezza del Codice Identificativo. Al termine, premere il pulsante di conferma per salvare l'anagrafica nel database.
*   **Regola di Validazione (Codice Univoco):** Per garantire l'integrità dei dati e la tracciabilità, il sistema non permette la duplicazione dei codici. Qualora si tenti di salvare un codice già assegnato a un altro articolo o si riscontrino anomalie nei dati inseriti, l'applicazione bloccherà l'operazione mostrando un messaggio di errore mirato.

#### 2. Registro Materie Prime (Consultazione e Modifica)
Il Registro offre l'elenco completo e centralizzato di tutte le anagrafiche dei materiali salvate nel sistema. Oltre alla sola consultazione, questa pagina funge da pannello di controllo per le modifiche e le cancellazioni.
*   **Modifica di un elemento esistente:** Selezionando con un clic la riga corrispondente alla materia prima di interesse, si sbloccheranno i campi interattivi per la modifica dei dati. Una volta variati i valori, l'operatore può scegliere una delle tre azioni disponibili tramite i rispettivi pulsanti:
    *   **Salva:** Applica e rende definitive le modifiche apportate sul database, aggiornando la scheda del materiale in tempo reale.
    *   **Reset:** Annulla istantaneamente tutte le modifiche testuali appena inserite, ripristinando i valori precedenti senza chiudere la finestra di modifica dell'articolo.
    *   **Elimina:** Rimuove permanentemente l'anagrafica della materia prima dal database di sistema.
    *   > [!WARNING]
        > L'azione di eliminazione è irreversibile. Si consiglia di verificare che non vi siano lotti ancora attivi legati all'articolo prima di procedere con la cancellazione.

---

### 📦 C. Lotti
Questo modulo permette il tracciamento operativo dei singoli lotti associati alle materie prime, consentendo di registrarne la provenienza, le scadenze e i quantitativi in ingresso.

#### 1. Nuovo Lotto (Registrazione e Carico)
La pagina consente il carico in magazzino di una nuova fornitura di materiale.
*   **Procedura di Inserimento:**
    *   **Date di Riferimento:** La *Data di Arrivo* viene impostata automaticamente sul giorno corrente, ma può essere modificata manualmente selezionando il giorno desiderato tramite il calendario integrato. La *Data di Scadenza* del materiale va inserita manualmente.
        > [!IMPORTANT]
        > **Regola di Validazione:** Per garantire la conformità e la sicurezza del magazzino, la data di scadenza deve essere obbligatoriamente successiva alla data di arrivo. In caso contrario, il sistema bloccherà il salvataggio mostrando un messaggio di errore.
    *   **Associazione Materia Prima:** Selezionare il materiale desiderato digitando all'interno del campo di testo o selezionandolo dal menu a tendina. Una volta effettuata la scelta, il sistema compilerà e assocerà automaticamente il relativo Codice Univoco della materia prima.
    *   **Anagrafica Fornitore:** Selezionare il nome del fornitore tramite l'apposito menu a tendina. Nel caso in cui il fornitore non sia ancora censito a sistema, è possibile registrarlo immediatamente premendo il pulsante dedicato per la creazione di un **Nuovo Fornitore**, senza dover abbandonare la pagina di inserimento del lotto.
    *   **Identificativi e Salvataggio:** Completare i restanti campi richiesti (quantità, lotto del produttore, ecc.) e definire il campo **Lotto Interno**.
        > [!IMPORTANT]
        > **Regola di Validazione (Codice Univoco):** Il codice identificativo del lotto interno funge da chiave primaria per la tracciabilità e deve essere rigorosamente univoco. Se si inserisce un codice già registrato, l'applicazione segnalerà l'anomalia.
    *   Premere il pulsante di conferma per salvare i dati e rendere disponibile il lotto per le attività del laboratorio.

#### 2. Registro Lotti (Consultazione e Controllo Qualità)
Il Registro Lotti elenca tutti i lotti caricati a sistema, mostrando a colpo d'occhio le loro caratteristiche principali (codici, giacenze, scadenze). Selezionando una riga con un clic, l'interfaccia si espande per mostrare le informazioni secondarie e sbloccare la modifica dei dati anagrafici. La tabella include una serie di pulsanti interattivi e colonne di stato fondamentali per l'avanzamento operativo del materiale:
*   **Et. Bianca (Etichetta Bianca):** Reindirizza istantaneamente alla pagina di configurazione e stampa delle etichette identificative preliminari per il lotto selezionato.
*   **QC (Controllo Qualità):** Questa colonna monitora lo stato del controllo analitico del lotto attraverso un sistema di segnalazione cromatica a tre stadi:
    *   ⬛ **Grigio (Stato Iniziale):** Indica che il controllo qualità non è ancora stato avviato sul lotto.
    *   🟨 **Giallo (In Preparazione / Selezione Multipla):** Cliccando sul tasto grigio, questo diventa giallo. Questo stato intermedio consente di selezionare più lotti contemporaneamente (anche di lotti diversi).
        > [!TIP]
        > **Annullamento Errore:** Se un lotto viene contrassegnato in giallo per errore, è possibile fare clic con il tasto destro del mouse sulla voce gialla per annullare l'azione e riportare il pulsante allo stato iniziale (grigio).
    *   🟩 **Verde / Consegnato ("QC - Consegnato"):** Cliccando nuovamente sul tasto giallo, il lotto passa allo stato definitivo di conformità/consegna del QC, registrando in automatico la data odierna come data di completamento dell'analisi.
        > [!NOTE]
        > Una volta confermata la selezione dei lotti in giallo, il sistema genera automaticamente un unico file PDF riassuntivo (**Richiesta di Analisi**) all'interno della cartella di sistema `richiesta_analisi/`.
*   **Appr. (Approvazione):** Cliccando su questo comando si apre una finestra di dialogo che permette di registrare la data ufficiale di approvazione del lotto (impostata di default sulla data corrente).
*   **Et. Verde (Etichetta Verde):** Una volta che il lotto ha superato i controlli, questo pulsante indirizza alla pagina di generazione delle etichette verdi di conformità, pronte per essere applicate sui contenitori per autorizzarne l'uso.
*   **CC (Contro campione):** Attiva una scorciatoia che reindirizza l'utente alla pagina di Scarico Manuale, configurando e precompilando automaticamente la causale e i dati del lotto per il prelievo del "contro campione" di laboratorio.
*   **Salva (Lista di Distribuzione):** Questo pulsante esporta e salva direttamente un documento PDF contenente la **lista di distribuzione e tracciabilità** del lotto selezionato all'interno della cartella dedicata `lista_distribuzione/`.

---

### 📉 D. Gestione degli Scarichi di Magazzino
Questo modulo gestisce il prelievo e il consumo dei materiali dal magazzino del laboratorio. Il sistema permette di registrare le movimentazioni in due modalità distinte: Manuale (per prelievi singoli o causali specifiche) e Automatico (legato a ricette o protocolli di sintesi predefiniti).

#### 1. Registrazione Scarico (Pannello Iniziale)
All'accesso alla sezione dedicata, l'operatore si trova davanti a un pannello di selezione iniziale: è presente una barra di ricerca / menu a tendina. Consente di digitare o selezionare la tipologia di scarico da effettuare. Scegliendo la voce generica si accede alla compilazione manuale, mentre selezionando un protocollo specifico si avvia la procedura di scarico automatico per sintesi.

#### 2. Scarico Manuale
La modalità manuale viene utilizzata per registrare prelievi occasionali, correzioni di inventario o campionamenti.
*   **Procedura operativa:**
    1.  **Dati Sessione:** Inserire la data dell'operazione e il nome dell'operatore che effettua il prelievo.
    2.  **Selezione Materiale e Lotto:** Selezionare la materia prima desiderata. Una volta scelta, il sistema mostrerà esclusivamente i lotti fisicamente disponibili in magazzino.
    3.  **Preselezione Automatica:** Il software preseleziona automaticamente il lotto contrassegnato come *"In Uso"*, ovvero quello con la scadenza più vicina (FEFO), per favorire la corretta rotazione dei materiali. L'operatore può comunque variare manualmente la scelta.
    4.  **Quantità e Causale:** Inserire la quantità volumetrica o ponderale da scaricare e specificare la causale del prelievo dall'apposito elenco.
    5.  **Registrazione:** Premere il pulsante per confermare e scalare le giacenze dal database.
*   **Integrazione Contro Campione (Flag CC):** Se la causale selezionata corrisponde a *"Contro campione"*, il sistema applicherà in automatico il contrassegno CC nel Registro Lotti in corrispondenza del lotto utilizzato, garantendone la tracciabilità per scopi ispettivi.

#### 3. Scarico Automatico
La selezione di un profilo di scarico automatico permette di registrare i consumi di un intero blocco di materiali associati a un determinato processo di sintesi del laboratorio (es. ricette per *Picking FDG (Synthera)*, *Trasis*, *FBB*, *FCH*, *PYL*, *DOTA*, ecc.).
*   **Caratteristiche e Funzionalità della Schermata:**
    *   **Selezione Automatica:** Il sistema compila automaticamente l'elenco di tutte le materie prime richieste dal protocollo selezionato, impostando i rispettivi quantitativi standard di ricetta. Se necessario, l'operatore può modificare manualmente le quantità prima della registrazione.
    *   **Assegnazione dei Lotti:** Il software propone per ciascuna voce il lotto attivo corrente. L'operatore mantiene la facoltà di modificare l'assegnazione tramite menu a tendina.
    *   **Indicatori Visivi di Conformità (Stato Approvazione):** Accanto a ogni lotto compare un indicatore cromatico circolare (pallino) che ne attesta lo stato di Controllo Qualità:
        *   🟢 **Verde:** Il lotto è già stato verificato e formalmente approvato dal Controllo Qualità.
        *   🔴 **Rosso:** Il lotto non ha ancora completato l'iter di approvazione del Controllo Qualità.
    *   **Monitoraggio Giacenze:** Per ogni lotto selezionato vengono mostrate in tempo reale la giacenza residua e la data di scadenza.
*   **Opzione "Run in Bianco":**
    *   Sotto la selezione della modalità è presente la funzione speciale **Run in Bianco**.
    *   Attivando questa opzione, il sistema permette di selezionare ed impiegare il lotto di **Acqua Arricchita** (codice `'424'`) anche nel caso in cui non sia ancora stato formalmente approvato dal Controllo Qualità.
    *   In questo scenario specifico, il software non bloccherà l'operazione con un messaggio di errore e provvederà a preselezionare automaticamente il lotto non approvato per velocizzare il flusso di lavoro.
*   **Validazione e Conferma:**
    *   Una volta verificati tutti i campi, premere il pulsante "Registra scarico". Il sistema effettuerà un controllo di congruenza sui dati e sulle giacenze: se l'operazione va a buon fine, il magazzino viene scaricato; in caso contrario, l'applicazione segnalerà l'anomalia riscontrata per permettere la correzione immediata.
    *   > [!IMPORTANT]
        > **Controllo Rigido Scadenza:** Lo scarico automatizzato viene interrotto con errore bloccante se anche uno solo dei lotti selezionati risulta scaduto alla data dello scarico (`data_scadenza < data_scarico`).

#### 4. Storico Scarichi (Registro e Tracciabilità)
La pagina Storico Scarichi costituisce l'archivio digitale centralizzato di tutte le movimentazioni in uscita registrate nel laboratorio, per verificare a ritroso qualsiasi consumo.
*   **Sistema di Filtraggio e Ricerca Rapida:** Nella parte superiore della schermata è presente un pannello dedicato ai filtri di ricerca (Data dell'operazione, Tipologia di scarico, Operatore). La tabella sottostante si aggiorna dinamicamente mostrando una panoramica preliminare delle voci trovate.
*   **Funzionalità di Esportazione e Stampa:** Cliccando sullo scarico è possibile espandere la visualizzazione e guardare tutti i dettagli relativi. Nella vista di dettaglio dello scarico sono presenti due pulsanti di azione rapida per la gestione documentale:
    *   **Salva PDF:** Genera ed esporta automaticamente il documento di scarico in formato PDF, archiviandolo direttamente all'interno della cartella di sistema `picking list/`.
    *   **Stampa picking list:** Richiama immediatamente l'interfaccia di stampa nativa del browser web. Questa funzione permette di stampare direttamente su carta o di salvare la "lista di prelievo" (picking list) sfruttando le stampanti collegate alla postazione.

---

### 🏷️ E. Gestione delle Etichette di Laboratorio
Il modulo Etichette sovrintende alla generazione, al tracciamento e alla stampa dei contrassegni identificativi fisici da applicare sui materiali. Il sistema gestisce due tipologie distinte di etichette: l'Etichetta Bianca (identificazione preliminare all'arrivo) e l'Etichetta Verde (approvazione e conformità all'uso).

#### 1. Nuova Etichetta
Questa pagina consente di emettere i talloncini identificativi per un lotto specifico, verificandone preventivamente lo stato di avanzamento.
*   **Selezione del Lotto e Indicatori di Stato (B e V):** All'apertura del modulo, l'operatore può individuare il lotto di interesse digitando i caratteri di riferimento all'interno della barra di ricerca dedicata. La selezione attiva un menu a tendina interattivo in cui, accanto alle informazioni anagrafiche essenziali di ciascun lotto, compaiono sulla destra due indicatori rapidi di stato, denominati **B (Etichetta Bianca)** e **V (Etichetta Verde)**:
    *   ⚪ **Indicatori Disattivi (Spenti):** Quando i simboli B e V appaiono privi di colore (grigi), significa che per quel determinato lotto non è ancora stata registrata o salvata alcuna etichetta nel database.
    *   🟢⚪ **Indicatori Attivi (Colorati):** Se i simboli B (in bianco) e V (in verde) sono colorati, il sistema segnala che la rispettiva documentazione grafica è già stata precedentemente generata e risulta presente nell'archivio digitale.
*   **Anteprima e Vincoli di Generazione:** Una volta confermata la selezione del lotto, l'interfaccia mostra un pannello con l'anteprima dei contrassegni emettibili:
    *   **Etichetta Bianca:** Risulta sempre disponibile e abilitata alla generazione fin dal primo carico del materiale a magazzino.
    *   **Etichetta Verde:** La sua abilitazione è subordinata al soddisfacimento di rigidi requisiti procedurali e analitici di laboratorio (QC completato, conformità registrata, approvazione valida).
    *   **Aggiornamento Dinamico:** La sezione dei vincoli si aggiorna automaticamente in tempo reale sulla schermata, indicando chiaramente all'operatore quali passaggi mancano per sbloccare l'autorizzazione e ottenere il contrassegno verde.
*   **Flusso di Salvataggio e Stampa:** Per entrambe le tipologie di etichette, la finalizzazione del processo avviene tramite il comando **"Salva & Stampa"**:
    *   **Allineamento dei Dati:** Al clic sul pulsante, l'applicazione registra l'azione a sistema, modificando in automatico i relativi indicatori di stato e aggiornando i dati visualizzabili all'interno del Registro Lotti.
    *   **Output di Stampa:** Il software richiama direttamente l'interfaccia del browser configurata per il layout standard di laboratorio (impaginazione in griglia 3 x 8 su foglio A4), predisponendo i moduli per l'applicazione fisica sui contenitori.
*   **Scorciatoia di Consultazione:** Qualora l'etichetta di un determinato lotto risulti già emessa (indicatori attivi), l'operatore può premere sul pulsante **"Etichetta già disponibile"**: questo comando funge da scorciatoia, reindirizzando l'utente direttamente alla pagina del Registro Etichette con i filtri di ricerca già preimpostati per quel lotto specifico.

#### 2. Registro Etichette (Archivio e Ristampa)
Il Registro Etichette funge da memoria storica e archivio digitale centralizzato di tutti i contrassegni identificativi (sia bianchi che verdi) che sono stati generati e salvati a sistema. Questa schermata consente una rapida consultazione dello stato delle etichette emesse e offre gli strumenti per la loro gestione documentale e ri-emissione fisica.
*   **Pannello di Filtraggio e Ricerca Avanzata:** Nella porzione superiore della pagina è posizionato un modulo di filtraggio dinamico. L'operatore può combinare diversi parametri per circoscrivere l'elenco e rintracciare rapidamente i contrassegni cercati: Codice Lotto, Materia Prima, Tipologia di Etichetta (Bianca/Verde), Data di Creazione.
*   **Tabella Riassuntiva e Funzione di Ristampa:** Sotto l'area dei filtri, il sistema organizza i risultati in una tabella strutturata che espone a colpo d'occhio le informazioni fondamentali di ciascuna emissione (lotto, operatore, data di generazione e layout). In corrispondenza di ciascuna riga è presente un comando operativo dedicato:
    *   **Pulsante "Ristampa":** Cliccando su questo tasto, l'applicazione richiama istantaneamente l'interfaccia di stampa del browser. Questa funzione permette di duplicare fisicamente i contrassegni sul foglio A4 (in griglia standard 3 x 8) in caso di usura, smarrimento del talloncino originale o necessità di etichettatura supplementare dei contenitori in laboratorio, senza dover ripetere la procedura di configurazione da capo.

---

## 🔔 6. Pannello degli Avvisi (Home Page - Monitoraggio Proattivo)

Posizionato sul lato destro della schermata principale, il pannello degli Avvisi funge da sistema di monitoraggio proattivo e di allerta in tempo reale. Il suo scopo principale è richiamare l'attenzione del personale sulle criticità operative del magazzino prima o non appena queste si verifichino.

Il sistema elabora costantemente i dati e gestisce tre tipologie di avvisi. Se il magazzino si trova in uno stato di perfetta conformità e non vi sono anomalie, la colonna rimane vuota, garantendo un'interfaccia pulita.

### Tipologie di Segnalazione

1.  **Avviso Lotti Scaduti:**
    Questo modulo mostra l'elenco di tutti i lotti presenti in magazzino che hanno già superato la loro data di scadenza ufficiale, ma che presentano ancora una giacenza residua maggiore di zero.
    *   **Impatto operativo:** Questa segnalazione è cruciale per impedire l'impiego accidentale di reagenti o materiali scaduti nelle sessioni di analisi o sintesi.
2.  **Avviso Scadenze Imminenti (Alert Scorte Minime):**
    In questa sezione vengono raggruppate tutte le materie prime la cui giacenza totale complessiva (sommando tutti i lotti attivi) è scesa al di sotto della soglia minima di sicurezza impostata nell'anagrafica del prodotto.
    *   **Impatto operativo:** Funge da promemoria per l'ufficio acquisti o per i responsabili del laboratorio per procedere tempestivamente al riordino del materiale, evitando il blocco delle attività.
3.  **Avviso Sotto Scorta Minima (Alert Scadenze nei successivi 30 Giorni):**
    Questa sezione mostra l'elenco cronologico di tutti i lotti in magazzino la cui data di scadenza programmata cadrà nei successivi 30 giorni.
    *   **Impatto operativo:** Permette al personale di pianificare i flussi di lavoro ottimizzando il consumo dei lotti più vicini al fine ciclo di vita, riducendo al minimo gli sprechi di magazzino.

---

## ⚙️ 7. Pulsanti Ausiliari e Funzioni di Amministrazione

Questa sezione descrive le funzionalità accessibili tramite i pulsanti ausiliari posizionati nella barra superiore sulla destra dell'interfaccia principale. Questi strumenti consentono di consultare dati storici, configurare il sistema e monitorare l'andamento del laboratorio.

### 📊 A. Statistiche
La pagina Statistiche è un'area di sola consultazione progettata per offrire una panoramica visiva e immediata sull'andamento delle attività all'interno del laboratorio. Attraverso grafici dinamici e tabelle riassuntive, il sistema elabora automaticamente i dati memorizzati per monitorare l'efficienza dei flussi di lavoro.
*   **Funzionalità principali:** La sezione non richiede l'inserimento di dati o interazioni operative, ma funge da cruscotto informativo per analizzare:
    *   **Tracciamento dei consumi:** Analisi quantitativa dei materiali utilizzati in un determinato arco temporale.
    *   **Storico degli scarichi:** Monitoraggio della frequenza e dei volumi di scarico delle materie prime.
    *   **Ottimizzazione delle scorte:** Rappresentazione visiva dell'utilizzo dei prodotti, utile per prevedere le tempistiche di riordino e minimizzare gli sprechi di magazzino.
    *   *Nota:* I grafici si aggiornano in tempo reale a ogni nuova operazione di carico o scarico registrata nel gestionale, garantendo uno storico sempre allineato e consultabile.

---

### ⚙️ B. Impostazioni
Il menu Impostazioni raggruppa le funzionalità dedicate alla sicurezza dei dati, al tracciamento delle attività e alla manutenzione ordinaria dell'applicazione.

#### 1. Backup & Protezione Dati
La pagina offre gli strumenti necessari per la salvaguardia e il ripristino dell'intero database del laboratorio. Il sistema adotta una politica di protezione automatica, riducendo al minimo l'intervento manuale.
*   **Backup Automatico all'Avvio:** Ogni volta che il software viene avviato, viene generata una copia di sicurezza del database, salvata all'interno della cartella `database/backup/`.
*   **Backup Automatico Giornaliero:** Se il server rimane attivo in modo continuativo per lungo tempo, il gestionale esegue in autonomia un backup ogni 24 ore.
*   **Rotazione dei File:** Per ottimizzare lo spazio sul disco ed evitare l'accumulo di file obsoleti, il sistema mantiene in memoria un massimo di **30 copie**. Raggiunto tale limite, il backup più datato verrà rimosso per fare spazio al nuovo.
*   **Creazione di un Backup Manuale:**
    1.  Accedere alla sezione *Backup*.
    2.  Inserire il proprio nome nel campo **Operatore**.
    3.  Premere il pulsante **"Crea backup"**.
*   **Registro Storico e Ripristino dei Dati:** La tabella *"Registro Storico dei Backup nel Sistema"* elenca cronologicamente tutti i salvataggi disponibili, specificandone l'origine. Per recuperare i dati di una sessione precedente, individuare il backup desiderato e premere il pulsante **"Ripristina"**. Questa azione sovrascriverà il database corrente con i dati memorizzati nella copia selezionata.
    *   > [!IMPORTANT]
        > **Protezione da Sovrascrittura (Emergenza):** Al fine di prevenire perdite accidentali di dati recenti, ogni operazione di ripristino genera automaticamente una copia speculare dello stato corrente del database, rinominata con la dicitura *"Emergenza Pre-Ripristino"*.

#### 2. Registro del Server (Log)
In fondo alla pagina delle Impostazioni è visualizzato in tempo reale il log delle attività del terminale. Questa sezione monitora i processi interni del server ed è utile per scopi diagnostici in caso di anomalie.

#### 3. Storico Operazioni (Audit Trail)
Questa sezione garantisce la piena tracciabilità di ogni azione eseguita sul database del laboratorio (inserimenti, prelievi o modifiche) in linea con i più severi requisiti regolatori (GMP compliant).
*   La pagina mostra l'elenco cronologico di tutte le attività operative registrate dal personale.
*   **Verifica delle modifiche (Variazioni):** Selezionando una voce modificata, il sistema mostra una schermata di confronto immediato tra i valori precedenti (**Pre-Modifica**) e quelli attuali (**Post-Modifica**). Le differenze tra i dati vengono evidenziate visivamente per facilitare il controllo ispettivo e identificare rapidamente eventuali anomalie o errori di inserimento.

#### 4. Spegnimento dell'Applicazione
Una corretta chiusura del software garantisce l'integrità del database e il rilascio sicuro delle risorse di sistema del computer.
*   > [!IMPORTANT]
    > La semplice chiusura della finestra o della scheda del browser web non interrompe l'esecuzione dell'applicazione, che rimarrà attiva in background sul computer principale.
*   **Procedura di arresto sicuro:** Per spegnere definitivamente il server del gestionale, accedere alla pagina delle Impostazioni e premere il pulsante **"Spegni applicazione"**. La procedura salverà in modo sicuro ogni sessione aperta prima di arrestare l'applicazione, scongiurando qualsiasi perdita o corruzione dei dati. Si raccomanda di effettuare questa operazione al termine di ogni giornata lavorativa.

#### 5. Tema Giorno/Notte
Posizionato come ultima voce all'interno del menu Impostazioni, questo comando consente di invertire istantaneamente lo schema cromatico dell'intera interfaccia utente, passando da un tema chiaro a uno scuro.
*   **Interruttore di Tema:** Cliccando sul pulsante, il software adatta i colori delle schermate per rispondere alle preferenze visive dell'operatore o alle condizioni di illuminazione del laboratorio.
*   *Nota di utilizzo:* Il sistema è stato nativamente progettato e ottimizzato per la **Modalità Notte (Tema Scuro)**, che garantisce la massima coerenza visiva e il contrasto ideale tra tutti gli elementi grafici. La Modalità Giorno (Tema Chiaro) va intesa come una funzionalità secondaria; di conseguenza, in alcune schermate l'abbinamento dei colori potrebbe risultare meno uniforme rispetto alla configurazione scura di default.
