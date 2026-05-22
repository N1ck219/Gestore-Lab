@echo off
setlocal enabledelayedexpansion
title Ripristino Database di Emergenza - Gestore-Lab
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8

echo ======================================================================
echo          🛡️ RIPRISTINO DATABASE DI EMERGENZA (ESTERNO)
echo ======================================================================
echo  Questa utilita consente di ripristinare una copia storica del
echo  database in caso di corruzione o avvio fallito del server Flask.
echo ======================================================================
echo.

:: ==========================================
:: CONFIGURAZIONE PERCORSI (Dinamica da .env)
:: ==========================================
set "TARGET_DIR=%~dp0"
if "%TARGET_DIR:~-1%"=="\" set "TARGET_DIR=%TARGET_DIR:~0,-1%"

:: Imposta i valori di default
set "DB_PATH=database\database.db"
set "BACKUP_DIR=database\backups"
set "APP_LOG_PATH=database\app.log"

:: Carica e parsa il file .env se esiste
if exist "%TARGET_DIR%\.env" (
    for /f "usebackq tokens=1* delims==" %%I in ("%TARGET_DIR%\.env") do (
        set "key=%%I"
        set "val=%%J"
        if not "!key:~0,1!"=="#" (
            :: Rimuovi virgolette
            set "val=!val:"=!"
            set "val=!val:'=!"
            :: Trim degli spazi
            for /f "tokens=*" %%A in ("!key!") do set "key=%%A"
            for /f "tokens=*" %%A in ("!val!") do set "val=%%A"
            set "!key!=!val!"
        )
    )
)

:: Converte le barre per compatibilità Windows
set "RESOLVED_DB_PATH=!DB_PATH:/=\!"
set "RESOLVED_BACKUP_DIR=!BACKUP_DIR:/=\!"
set "RESOLVED_APP_LOG_PATH=!APP_LOG_PATH:/=\!"

:: Se i percorsi sono relativi, li àncora alla cartella del progetto
if not "!RESOLVED_DB_PATH:~1,1!"==":" (
    if not "!RESOLVED_DB_PATH:~0,1!"=="\" (
        set "RESOLVED_DB_PATH=%TARGET_DIR%\!RESOLVED_DB_PATH!"
    )
)
if not "!RESOLVED_BACKUP_DIR:~1,1!"==":" (
    if not "!RESOLVED_BACKUP_DIR:~0,1!"=="\" (
        set "RESOLVED_BACKUP_DIR=%TARGET_DIR%\!RESOLVED_BACKUP_DIR!"
    )
)
if not "!RESOLVED_APP_LOG_PATH:~1,1!"==":" (
    if not "!RESOLVED_APP_LOG_PATH:~0,1!"=="\" (
        set "RESOLVED_APP_LOG_PATH=%TARGET_DIR%\!RESOLVED_APP_LOG_PATH!"
    )
)

:: Ottiene la cartella genitore del file database
for %%I in ("!RESOLVED_DB_PATH!") do set "DB_DIR=%%~dpI"
if "!DB_DIR:~-1%"=="\" set "DB_DIR=!DB_DIR:~0,-1!"

:: Assicura l'esistenza della cartella dei log
for %%f in ("!RESOLVED_APP_LOG_PATH!") do set "LOG_DIR=%%~dpf"
if not exist "!LOG_DIR!" (
    mkdir "!LOG_DIR!"
)

:: Logga l'avvio dell'utility di ripristino esterno di emergenza
powershell -Command "Add-Content -Path '!RESOLVED_APP_LOG_PATH!' -Value ('[{0}] WARNING in Ripristina_Database: Avviata l''utility batch esterna di ripristino di emergenza Ripristina_Database.bat.' -f [DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss,fff')) -Encoding utf8"
:: ==========================================

if not exist "!RESOLVED_BACKUP_DIR!" (
    echo [ERRORE] La cartella dei backup "!RESOLVED_BACKUP_DIR!" non esiste o e vuota.
    echo Nessun punto di ripristino disponibile.
    goto fine
)

echo Ricerca dei punti di ripristino disponibili (dal piu recente)...
echo.

set "count=0"
:: Scansiona tutti i file .db ordinandoli dal più recente
for /f "tokens=*" %%F in ('dir "!RESOLVED_BACKUP_DIR!\*.db" /B /O:-D 2^>nul') do (
    set /a count+=1
    set "file[!count!]=%%F"
    
    :: Estrae dettagli del file (dimensione e data di modifica)
    set "filepath=!RESOLVED_BACKUP_DIR!\%%F"
    for %%I in ("!filepath!") do (
        set "filesize=%%~zI"
        set "filedate=%%~tI"
    )
    
    :: Converte la dimensione in KB
    set /a size_kb=!filesize! / 1024
    
    echo   [!count!] %%F  [!size_kb! KB - !filedate!]
)

if %count% equ 0 (
    echo [ERRORE] Nessun file di backup (.db) trovato nella cartella "!RESOLVED_BACKUP_DIR!".
    goto fine
)

echo.
:scegli
set /p "scelta=👉 Digita il numero del backup da ripristinare (o 'Q' per annullare): "

if /i "%scelta%"=="Q" goto annulla_scelta

:: Validazione scelta numerica
set "scelta_valida=0"
for /l %%i in (1, 1, %count%) do (
    if "%scelta%"=="%%i" (
        set "scelta_valida=1"
        set "SELECTED_FILE=!file[%%i]!"
    )
)

if "%scelta_valida%"=="0" (
    echo [ERRORE] Scelta non valida. Inserisci un numero tra 1 e %count%.
    echo.
    goto scegli
)

echo.
echo ======================================================================
echo ⚠️ ATTENZIONE: Ripristino Database Imminente
echo ======================================================================
echo  Stai per ripristinare il file:
echo  👉 !SELECTED_FILE!
echo.
echo  Questa azione sovrascrivera il database attivo:
echo  👉 !RESOLVED_DB_PATH!
echo.
echo  Tutte le modifiche successive a questo backup andranno perse!
echo ======================================================================
echo.

:conferma
set /p "conferma_str=Per procedere digita 'RIPRISTINA' (in maiuscolo) o 'A' per annullare: "

if /i "%conferma_str%"=="A" goto annulla_conferma

if "%conferma_str%" neq "RIPRISTINA" (
    echo [ERRORE] Conferma non valida. Digitare esattamente 'RIPRISTINA'.
    echo.
    goto conferma
)

echo.
echo Esecuzione ripristino "salvagente" in corso...

:: Assicura l'esistenza della cartella database
if not exist "!DB_DIR!" mkdir "!DB_DIR!"

:: 1. Creazione del backup di emergenza preventiva esterna
if not exist "!RESOLVED_DB_PATH!" goto esegui_ripristino

for /f "tokens=*" %%a in ('powershell -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"') do set "TIMESTAMP=%%a"
set "EMERGENCY_FILE=database_emergenza_esterno_!TIMESTAMP!.db"
copy "!RESOLVED_DB_PATH!" "!RESOLVED_BACKUP_DIR!\!EMERGENCY_FILE!" >nul
if !errorlevel! equ 0 goto backup_preventivo_ok
goto backup_preventivo_fallito

:backup_preventivo_ok
echo [INFO] Creato backup preventivo di emergenza: !EMERGENCY_FILE!
powershell -Command "Add-Content -Path '!RESOLVED_APP_LOG_PATH!' -Value ('[{0}] WARNING in Ripristina_Database: Creato backup preventivo di emergenza offline !EMERGENCY_FILE!.' -f [DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss,fff')) -Encoding utf8"
goto esegui_ripristino

:backup_preventivo_fallito
echo [ERRORE] Impossibile creare il backup preventivo di emergenza.
echo Operazione interrotta per sicurezza per evitare perdite accidentali.
powershell -Command "Add-Content -Path '!RESOLVED_APP_LOG_PATH!' -Value ('[{0}] ERROR in Ripristina_Database: Fallito tentativo di backup preventivo. Ripristino abortito.' -f [DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss,fff')) -Encoding utf8"
goto fine

:esegui_ripristino
:: 2. Sovrascrittura del file database attivo con la copia storica selezionata
copy "!RESOLVED_BACKUP_DIR!\!SELECTED_FILE!" "!RESOLVED_DB_PATH!" >nul
if !errorlevel! equ 0 goto ripristino_ok
goto ripristino_fallito

:ripristino_ok
echo.
echo ======================================================================
echo  ✔️ RIPRISTINO DI EMERGENZA COMPLETATO CON SUCCESSO!
echo  Il database attivo e stato ripristinato da:
echo  👉 !SELECTED_FILE!
echo ======================================================================
powershell -Command "Add-Content -Path '!RESOLVED_APP_LOG_PATH!' -Value ('[{0}] WARNING in Ripristina_Database: Ripristino di emergenza offline completato da !SELECTED_FILE!.' -f [DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss,fff')) -Encoding utf8"
goto fine

:ripristino_fallito
echo.
echo [ERRORE CRITICO] Impossibile sovrascrivere il file database attivo (!RESOLVED_DB_PATH!).
echo Assicurati che l'applicazione non sia aperta o bloccata da altri processi.
powershell -Command "Add-Content -Path '!RESOLVED_APP_LOG_PATH!' -Value ('[{0}] ERROR in Ripristina_Database: Impossibile sovrascrivere il database attivo con !SELECTED_FILE! durante il ripristino di emergenza offline.' -f [DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss,fff')) -Encoding utf8"
goto fine

:annulla_scelta
echo.
echo [INFO] Operazione annullata dall'operatore.
powershell -Command "Add-Content -Path '!RESOLVED_APP_LOG_PATH!' -Value ('[{0}] INFO in Ripristina_Database: Operazione annullata dall''utente durante la selezione del backup.' -f [DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss,fff')) -Encoding utf8"
goto fine

:annulla_conferma
echo.
echo [INFO] Operazione annullata dall'operatore.
powershell -Command "Add-Content -Path '!RESOLVED_APP_LOG_PATH!' -Value ('[{0}] INFO in Ripristina_Database: Operazione annullata dall''utente nella richiesta di conferma.' -f [DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss,fff')) -Encoding utf8"
goto fine

:fine
powershell -Command "Add-Content -Path '!RESOLVED_APP_LOG_PATH!' -Value ('[{0}] INFO in Ripristina_Database: Chiusura utility batch Ripristina_Database.bat.' -f [DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss,fff')) -Encoding utf8"
echo.
echo Premi un tasto per uscire...
pause >nul
