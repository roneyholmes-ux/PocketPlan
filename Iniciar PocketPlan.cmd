@echo off
setlocal
cd /d "%~dp0"
title PocketPlan
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 goto erro
)
".venv\Scripts\python.exe" -c "import pypdf, openpyxl, cryptography, rapidocr, onnxruntime, PIL" >nul 2>&1
if errorlevel 1 (
  echo Preparando o PocketPlan para o primeiro uso...
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto erro
)
echo Mantenha esta janela aberta enquanto usar o PocketPlan.
echo Para encerrar, pressione Ctrl+C.
".venv\Scripts\python.exe" app.py --open
if errorlevel 1 goto erro
exit /b 0
:erro
echo.
echo Nao foi possivel iniciar. Confira a mensagem acima.
pause
exit /b 1
