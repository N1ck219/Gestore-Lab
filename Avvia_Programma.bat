@echo off
title Avvio Materie Prime Lab
echo Sto avviando il programma... attendi un istante.

:: ==========================================
:: CONFIGURAZIONE PERCORSI (Dinamica)
:: ==========================================
:: Imposta automaticamente la cartella in cui si trova il file .bat
set "TARGET_DIR=%~dp0"
:: Rimuove il backslash finale se presente per compatibilità
if "%TARGET_DIR:~-1%"=="\" set "TARGET_DIR=%TARGET_DIR:~0,-1%"

:: Rileva automaticamente se esiste .venv o venv
set "VENV_NAME=venv"
if exist "%TARGET_DIR%\.venv\Scripts\activate.bat" (
    set "VENV_NAME=.venv"
) else if exist "%TARGET_DIR%\venv\Scripts\activate.bat" (
    set "VENV_NAME=venv"
) else (
    :: Di default usa .venv se non esiste nessuno dei due
    set "VENV_NAME=.venv"
)
:: ==========================================

echo.
echo [1/4] Verifica di Python...

set "PYTHON_EXE=python"

:: 1. Controlla se python è disponibile nel PATH e funziona
python -c "import sys" >nul 2>&1
if %errorlevel% equ 0 (
    echo Python rilevato nel sistema.
    goto python_pronto
)

:: 2. Controlla se python è presente nella cartella utente standard (es. Python 3.12 o 3.11)
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
echo Python non e installato o non e configurato correttamente nel PATH.
echo Avvio del download di Python 3.11.9 in corso...

:: Crea la cartella temp se non esiste
if not exist "%temp%" mkdir "%temp%"

:: Download tramite curl (disponibile nativamente su Windows 10/11)
curl -L -o "%temp%\python_installer.exe" https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
if %errorlevel% neq 0 (
    echo [ERRORE] Impossibile scaricare Python. Controlla la tua connessione Internet.
    goto errore_arresto
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
    goto errore_arresto
)

:python_pronto

echo.
echo [2/4] Verifica del Virtual Environment (%VENV_NAME%)...

:: Controlla se esiste il virtual environment
if exist "%TARGET_DIR%\%VENV_NAME%\Scripts\activate.bat" goto venv_pronto

echo Virtual environment "%VENV_NAME%" non trovato in "%TARGET_DIR%".
echo Creazione del virtual environment in corso...

:: Assicurati che la cartella target esista
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"
if %errorlevel% neq 0 (
    echo [ERRORE] Impossibile creare la cartella di destinazione "%TARGET_DIR%".
    goto errore_arresto
)

:: Crea il virtual environment usando l'eseguibile Python trovato
"%PYTHON_EXE%" -m venv "%TARGET_DIR%\%VENV_NAME%"
if %errorlevel% neq 0 (
    echo [ERRORE] Impossibile creare il virtual environment in "%TARGET_DIR%\%VENV_NAME%".
    goto errore_arresto
)
echo Virtual environment creato con successo.

:: Se presente requirements.txt, installa le dipendenze
if not exist "%TARGET_DIR%\requirements.txt" goto venv_pronto

echo Installazione delle dipendenze da "%TARGET_DIR%\requirements.txt"...
:: Aggiorna pip nel venv
"%TARGET_DIR%\%VENV_NAME%\Scripts\python.exe" -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo [ERRORE] Impossibile aggiornare pip nel virtual environment.
    goto errore_arresto
)

:: Installa requirements
"%TARGET_DIR%\%VENV_NAME%\Scripts\pip.exe" install -r "%TARGET_DIR%\requirements.txt"
if %errorlevel% neq 0 (
    echo [ERRORE] Si e verificato un errore durante l'installazione delle dipendenze.
    goto errore_arresto
)

:venv_pronto
echo Virtual environment pronto ed esistente in "%TARGET_DIR%\%VENV_NAME%".

echo.
echo [3/4] Attivazione dell'ambiente virtuale...

:: Spostati nella cartella del progetto
cd /d "%TARGET_DIR%"
if %errorlevel% neq 0 (
    echo [ERRORE] Impossibile accedere alla cartella del progetto "%TARGET_DIR%".
    goto errore_arresto
)

:: Attiva il virtual environment
if not exist "%VENV_NAME%\Scripts\activate.bat" (
    echo [ERRORE] Il file di attivazione "%VENV_NAME%\Scripts\activate.bat" non esiste.
    goto errore_arresto
)

call "%VENV_NAME%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [ERRORE] Impossibile attivare il virtual environment.
    goto errore_arresto
)

echo.
echo [4/4] Apertura della pagina web e avvio del server Flask...

:: Avvia in background un comando che attende 2 secondi per l'avvio di Flask e poi apre il browser
echo Avvio del browser programmato tra 2 secondi...
start /b "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000"
if %errorlevel% neq 0 (
    echo [ATTENZIONE] Impossibile programmare l'apertura del browser. Puoi aprirlo manualmente su http://127.0.0.1:5000
)

:: Avvia l'applicazione Flask
python app.py
if %errorlevel% neq 0 (
    echo [ERRORE] L'applicazione Flask ha riscontrato un errore durante l'esecuzione.
    goto errore_arresto
)

echo.
echo Applicazione chiusa correttamente.
pause
exit /b 0

:errore_arresto
echo.
echo ======================================================================
echo [ERRORE CRITICO] Si e verificato un problema e l'avvio e stato interrotto.
echo Controlla i messaggi sopra riportati per capire il motivo del fallimento.
echo ======================================================================
echo.
pause
exit /b 1
