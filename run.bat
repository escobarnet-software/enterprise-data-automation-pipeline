@echo off
REM Usa el venv local del proyecto (siempre funciona, sin depender del PATH)
"%~dp0.venv\Scripts\python.exe" "%~dp0main.py" %*
