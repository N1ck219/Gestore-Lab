@echo off
title Avvio Materie Prime Lab
echo Sto avviando il programma... attendi un istante.

:: ==========================================
:: CONFIGURAZIONE PERCORSI
:: ==========================================
:: Rileva dinamicamente la cartella in cui risiede questo script batch
set "TARGET_DIR=%~dp0"
if "%TARGET_DIR:~-1%"=="\" set "TARGET_DIR=%TARGET_DIR:~0,-1%"
:: Nome della cartella per il virtual environment
set "VENV_NAME=venv"
:: ==========================================

echo.
echo [1/4] Verifica di Python...

set "PYTHON_EXE=python"

:: 1. Controlla se python e disponibile nel PATH e funziona
python -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    echo Python rilevato nel sistema.
    goto python_pronto
)

:: 2. Controlla se python e presente nella cartella utente standard (es. Python 3.12 o 3.11)
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
    echo Python 3.12 trovato in LocalAppData.
    goto python_pronto
)
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
    echo Python 3.11 trovato in LocalAppData.
    goto python_pronto
)

:: 3. Se non trovato, procedi al download e all'installazione silenziosa
echo Python non e installato o non e configurato correttamente.
echo Avvio del download di Python 3.11.9 in corso...

:: Crea la cartella temp se non esiste
if not exist "%temp%" mkdir "%temp%"

:: Download tramite curl (disponibile nativamente su Windows 10/11)
curl -L -o "%temp%\python_installer.exe" https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
if %errorlevel% neq 0 (
    echo [ERRORE] Impossibile scaricare Python. Controlla la tua connessione Internet.
    pause
    exit /b
)

echo Download completato. Installazione silenziosa in corso...
:: InstallAllUsers=0 (installa solo per l'utente corrente, evitando richieste di amministratore)
:: PrependPath=1 (aggiunge al PATH per sessioni future)
start /wait "" "%temp%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
del "%temp%\python_installer.exe"

:: Ricerca del Python appena installato nella cartella LocalAppData
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
    echo Python 3.11.9 installato con successo!
) else (
    echo [ERRORE] L'installazione di Python sembra essere fallita o non si trova nel percorso previsto.
    pause
    exit /b
)

:python_pronto

echo.
echo [2/4] Verifica del Virtual Environment (venv)...

:: Controlla se esiste il virtual environment
if not exist "%TARGET_DIR%\%VENV_NAME%\Scripts\activate.bat" (
    echo Virtual environment non trovato in "%TARGET_DIR%\%VENV_NAME%".
    echo Creazione del venv in corso...
    
    :: Assicurati che la cartella target esista
    if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"
    
    :: Crea il virtual environment usando l'eseguibile Python trovato
    "%PYTHON_EXE%" -m venv "%TARGET_DIR%\%VENV_NAME%"
    if %errorlevel% neq 0 (
        echo [ERRORE] Impossibile creare il virtual environment.
        pause
        exit /b
    )
    echo Virtual environment creato con successo.
    
    :: Se presente requirements.txt, installa le dipendenze
    if exist "%TARGET_DIR%\requirements.txt" (
        echo Installazione delle dipendenze da "%TARGET_DIR%\requirements.txt"...
        :: Aggiorna pip nel venv
        "%TARGET_DIR%\%VENV_NAME%\Scripts\python.exe" -m pip install --upgrade pip
        :: Installa requirements
        "%TARGET_DIR%\%VENV_NAME%\Scripts\pip.exe" install -r "%TARGET_DIR%\requirements.txt"
        if %errorlevel% neq 0 (
            echo [ATTENZIONE] Si e verificato un errore durante l'installazione delle dipendenze.
        )
    )
) else (
    echo Virtual environment gia esistente in "%TARGET_DIR%\%VENV_NAME%".
)

echo.
echo [3/4] Attivazione dell'ambiente e avvio dell'applicazione...

:: Spostati nella cartella del progetto
cd /d "%TARGET_DIR%"

:: Attiva il virtual environment
call "%VENV_NAME%\Scripts\activate.bat"

echo.
echo [4/4] Apertura della pagina web e avvio del server Flask...

:: Avvia il browser con l'indirizzo dell'applicazione
start "" http://127.0.0.1:5000

:: Avvia l'applicazione Flask
python app.py

pause
