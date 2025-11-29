@echo off
setlocal enabledelayedexpansion

echo ========================================
echo FEMA Geometry Validator
echo ========================================
echo.
echo Select a GeoPackage to validate its geom...
echo.

REM -- Prompt for FEMA Flood Hazard GPKG
echo Please select the GeoPackage (.gpkg) file:
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title = 'Select GeoPackage (.gpkg)'; $d.Filter='GeoPackage (*.gpkg)|*.gpkg'; if ($d.ShowDialog() -eq 'OK') { $d.FileName | Out-File '%TEMP%\gpkg_in.txt' -Encoding ascii }"
if not exist "%TEMP%\gpkg_in.txt" (
  echo No file selected. Exiting...
  pause
  exit /b 1
)
set /p GPKG_PATH=<%TEMP%\gpkg_in.txt
del %TEMP%\gpkg_in.txt
echo.

REM -- Prompt for layer name inside GPKG
echo Please type the layer name inside your GPKG file (you can find it via ogrinfo):
set /p GPKG_LAYER=Layer name: 
REM -- Remove quotes if present
set GPKG_LAYER=%GPKG_LAYER:"=%
echo.

REM -- Set output file path
set OUTPUT_DIR=%~dp0validated
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM -- Compose output filename
for %%F in ("%GPKG_PATH%") do (
    set FILE_NAME=%%~nxF
)
set OUTPUT_FILE=%OUTPUT_DIR%\validated_%FILE_NAME%
echo Validated file will be saved as: %OUTPUT_FILE%
echo.

REM -- Run ogr2ogr with -makevalid and -skipfailures
echo Running GDAL to repair geometries...
ogr2ogr -f GPKG "%OUTPUT_FILE%" "%GPKG_PATH%" "%GPKG_LAYER%" ^
  -makevalid -skipfailures -progress

if errorlevel 1 (
  echo.
  echo ERROR: Geometry repair failed. Please check the input file or layer name.
  pause
  exit /b
)

echo.
echo Geometry repair complete. File saved at:
echo    %OUTPUT_FILE%
pause
exit /b
