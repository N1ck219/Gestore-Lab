# 🧪 Gestore-Lab — Gestione Magazzino & Tracciabilità Materie Prime

Benvenuto in **Gestore-Lab**, un'applicazione web locale sviluppata in Python con Flask e SQLite, progettata specificamente per la gestione del magazzino, il tracciamento dei lotti e l'automazione dei prelievi (scarichi) all'interno di un **laboratorio chimico o radiofarmaceutico**.

L'applicazione offre un'interfaccia elegante con **tema scuro (dark mode)** ad alto contrasto per facilitare l'utilizzo in ambienti di laboratorio, garantendo al contempo un tracciamento rigoroso e conforme ai requisiti di qualità.

---

## 🛠️ Tecnologie Utilizzate

*   **Backend:** Python 3 + Flask (Micro-framework web)
*   **Database:** SQLite 3 (Database relazionale leggero incorporato in `database/database.db`)
*   **Generazione Documenti:** FPDF (Generazione dinamica delle Picking List in formato PDF)
*   **Frontend:** HTML5, CSS3 (con foglio di stile personalizzato in `static/css/style.css`), JavaScript Vanilla
*   **Ambiente di esecuzione:** Script di avvio automatico `.bat` per Windows

---

## 📋 Funzionalità Principali

### 1. Dashboard di Controllo
La pagina principale offre un accesso immediato a tutte le aree gestionali del software, suddivise per colore ed area di competenza:
*   📊 **Stato Magazzino (Azzurro):** Monitoraggio globale.
*   ➕/📋 **Anagrafica Materie Prime (Indaco):** Configurazione e consultazione dei prodotti.
*   📦/🔍 **Gestione Lotti (Viola):** Registrazione degli arrivi e controllo qualità (QC).
*   📉/📜 **Scarichi e Movimenti (Arancione):** Prelievi e storico dei consumi.

### 2. Stato Magazzino & Giacenze
*   Aggrega in tempo reale tutti i lotti attivi calcolando la **giacenza totale** per ogni materia prima.
*   Visualizza alert visivi se la giacenza scende sotto la **scorta minima** impostata.
*   Mostra automaticamente la **data di scadenza più imminente** per ogni prodotto.
*   Raggruppa le materie prime per **categoria di magazzino** con intestazioni visive chiare.

### 3. Tracciabilità Completa dei Lotti (Qualità & QC)
Ogni lotto in ingresso viene registrato singolarmente con:
*   Codice lotto interno e codice lotto del fornitore originale.
*   Data di arrivo, data di scadenza e quantità ricevuta.
*   Tracciamento dei parametri di Controllo Qualità: **Data consegna QC**, **Data Approvazione** e stato **Approvato (OK)**.
*   Tracciamento dei **Controcampioni (CC)** e della **Distribuzione**.

### 4. Registrazione Scarichi
Il software gestisce le uscite dal magazzino in due modalità:
*   **Scarico Manuale:** Consente all'operatore di prelevare una quantità specifica da un lotto per scopi generici (analisi, controcampionamento, scarto, ecc.). Previene automaticamente lo scarico di quantità superiori alla giacenza attuale.
*   **Scarico Automatico (Picking List di Produzione):**
    *   È la funzione più avanzata del sistema. Consente di selezionare il profilo di una specifica produzione o sintesi (es. *FMC*, *FMC KIT ACC*, *FCH*, *PYL*, *DOTA*, *FET*, *FBB*, *FDG*, ecc.).
    *   Il sistema carica la ricetta standard con tutte le materie prime e le quantità predefinite necessarie per quel ciclo.
    *   Applica automaticamente la logica **FIFO (First-In, First-Out)** proponendo l'utilizzo dei lotti approvati con la scadenza più vicina.
    *   Consente di stampare ed esportare in tempo reale una **Picking List in PDF** ufficiale per gli operatori di camera calda.
    *   Conferma lo scarico massivo aggiornando all'istante le giacenze nel database SQLite.

### 5. Storico Scarichi & Audit Log
*   Mostra un registro cronologico dettagliato di tutti i movimenti in uscita.
*   Identifica visivamente se si è trattato di uno scarico manuale o di un picking associato a un lotto di produzione specifico (es. *Picking FDG TRASIS*, *Picking DOTA*, ecc.).

---

## 💾 Struttura del Database (SQLite)

Il database si trova in `database/database.db` ed è composto dalle seguenti tabelle principali:
1.  **`Elenco_MP`:** Anagrafica e dettagli tecnici delle singole materie prime (codici interni, nomi, unità di misura, destinazione d'uso, scorta minima).
2.  **`Lotti_Interni`:** Record dei singoli lotti di reagenti inseriti, con relative giacenze aggiornate in tempo reale, date QC e stato di utilizzo.
3.  **`Scarichi`:** Registro dei prelievi effettuati, indicante la data, il lotto interno di provenienza, la quantità consumata, l'operatore e l'eventuale lotto di produzione finale (lotto_prod).
4.  **`Fornitori`:** Anagrafica dei fornitori qualificati.

---

## 🚀 Come Avviare il Progetto (Windows)

Il progetto è pre-configurato per essere avviato su Windows in modo estremamente semplice, senza dover configurare manualmente Python o le dipendenze.

### Avvio Rapido (Consigliato):
1.  Fai doppio clic sul file **`Avvia_Programma.bat`** presente nella cartella principale del progetto.
2.  Lo script eseguirà in automatico i seguenti passaggi:
    *   Verifica se Python è installato nel sistema (in caso contrario, scarica e installa in modalità silenziosa la versione **Python 3.11**).
    *   Crea l'ambiente virtuale (`venv`) locale per isolare le librerie.
    *   Aggiorna `pip` e installa automaticamente tutte le dipendenze necessarie (come `Flask`, `fpdf`, ecc.) contenute in `requirements.txt`.
    *   Apre in automatico il tuo browser web preferito all'indirizzo **`http://127.0.0.1:5000`**.
    *   Avvia il server Flask in modalità di sviluppo.

---

## 🔒 Passaggio in Produzione (Waitress)

Durante la fase di sviluppo, il server è configurato in modalità debug (`debug=True`) per consentire il ricaricamento automatico del codice in caso di modifiche.

Quando il software sarà pronto per l'utilizzo quotidiano da parte degli operatori di laboratorio, è fortemente consigliato configurare l'applicazione per l'avvio tramite **Waitress** (un server di produzione WSGI leggero e nativo per Windows), che garantisce stabilità assoluta ed evita avvisi nel terminale.

### Come configurare Waitress:
1.  Assicurati che sia installato:
    ```bash
    pip install waitress
    ```
2.  Nel file `app.py`, in fondo al documento, sostituisci il blocco finale:
    ```python
    if __name__ == '__main__':
        app.run(debug=True)
    ```
    con il seguente codice di produzione:
    ```python
    from waitress import serve

    if __name__ == '__main__':
        print("Avvio del server di produzione con Waitress su http://127.0.0.1:5000")
        serve(app, host='127.0.0.1', port=5000)
    ```
3.  Salva il file. Al successivo avvio tramite `Avvia_Programma.bat`, l'applicazione sarà protetta ed altamente stabile.

---

## 📁 Struttura delle Cartelle del Progetto

```text
Gestore-Lab/
│
├── database/
│   └── database.db           # Database SQLite principale dell'applicazione
│
├── static/
│   ├── css/
│   │   └── style.css         # Nuova veste grafica scura ed elegante (Premium Dark theme)
│   └── img/                  # Eventuali risorse grafiche o icone
│
├── templates/                # File HTML (Template Jinja2 per Flask)
│   ├── base.html             # Layout base condiviso da tutte le pagine
│   ├── index.html            # Dashboard principale del laboratorio
│   ├── list.html             # Registro anagrafica Materie Prime
│   ├── add_product.html      # Form per l'inserimento di una nuova materia prima
│   ├── lotti_list.html       # Registro globale e modifica dei lotti
│   ├── add_lotto.html        # Form per la registrazione di un nuovo lotto in arrivo
│   ├── magazzino.html        # Stato giacenze aggregate in tempo reale
│   ├── scarico_manuale.html  # Interfaccia per il prelievo singolo manuale
│   ├── scarico_automatico.html # Sezione per le Picking List di produzione (sintesi)
│   └── storico_scarichi.html # Registro storico dei consumi e dei prelievi
│
├── app.py                    # Codice backend principale dell'applicazione Flask
├── requirements.txt          # Elenco delle dipendenze Python necessarie
├── Avvia_Programma.bat       # Script Batch per l'automazione dell'avvio su Windows
└── README.md                 # Questo manuale di istruzioni
```
