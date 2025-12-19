@echo off
echo.
echo ========================================
echo  EmuladorMODBUSRTU v1.0.0
echo ========================================
echo.

REM Verificar se dependencias estao instaladas
python -c "import PyQt6" 2>nul
if errorlevel 1 (
    echo [!] Dependencias nao instaladas
    echo [+] Instalando dependencias...
    pip install -r requirements.txt
    echo [OK] Dependencias instaladas
    echo.
)

REM Executar aplicacao
echo [+] Iniciando EmuladorMODBUSRTU...
echo.
python src\main.py

pause
