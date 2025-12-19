@echo off
echo ========================================
echo  Compilando EmuladorMODBUSRTU
echo ========================================
echo.

REM Verificar se PyInstaller está instalado
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [ERRO] PyInstaller nao encontrado!
    echo Instalando PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar PyInstaller
        pause
        exit /b 1
    )
)

echo [1/3] Limpando builds anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [2/3] Compilando com PyInstaller...
pyinstaller build.spec --clean

if errorlevel 1 (
    echo.
    echo [ERRO] Falha na compilacao!
    pause
    exit /b 1
)

echo [3/3] Verificando resultado...
if exist "dist\EmuladorMODBUSRTU\EmuladorMODBUSRTU.exe" (
    echo.
    echo ========================================
    echo  SUCESSO! Executavel criado em:
    echo  dist\EmuladorMODBUSRTU\
    echo ========================================
    echo.
    echo Arquivos gerados:
    dir /b "dist\EmuladorMODBUSRTU"
) else (
    echo [ERRO] Executavel nao encontrado!
    pause
    exit /b 1
)

echo.
pause
