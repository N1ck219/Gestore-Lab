@echo off
title Avvio Materie Prime Lab
echo Sto avviando il programma... attendi un istante.

:: Controlla se le dipendenze sono installate (opzionale ma consigliato)
:: pip install -r requirements.txt

:: Avvia il browser dopo un piccolo ritardo
start "" http://127.0.0.1:5000

:: Avvia il server Flask
python app.py

pause
