@echo off
setlocal ENABLEDELAYEDEXPANSION

echo ========================================
echo Fix GeoJSON(L): makevalid + EPSG:4326 + GeoJSONSeq
echo ========================================
echo.
echo Select a geojsonl to validate...
echo.

REM ---- 1) Check GDAL (ogr2ogr) availability ----
where ogr2ogr >NUL 2>&1
if errorlevel 1 (
  echo [Error] ogr2ogr not found in PATH.
  echo Please install GDAL and ensure ogr2ogr is available, or run this script from OSGeo4W Shell.
  echo.
  echo Press any key to exit...
  pause >nul
  exit /b 1
)

REM ---- 2) Open file picker to choose input (.geojsonl or .geojson) ----
for /f "usebackq delims=" %%F in (`powershell -NoProfile -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $ofd = New-Object System.Windows.Forms.OpenFileDialog; $ofd.Title = 'Select a GeoJSONL/GeoJSON file'; $ofd.Filter = 'GeoJSON Lines (*.geojsonl)|*.geojsonl|GeoJSON (*.geojson)|*.geojson|All files (*.*)|*.*'; if ($ofd.ShowDialog() -eq 'OK') { Write-Output $ofd.FileName }"`) do set "INPUT=%%F"

if not defined INPUT (
  echo No file selected. Exiting.
  echo.
  echo Press any key to exit...
  pause >nul
  exit /b 0
)

REM ---- 3) Build output path: same folder, *_fixed.geojsonl ----
for %%A in ("%INPUT%") do (
  set "IN_DIR=%%~dpA"
  set "IN_NAME=%%~nA"
)
set "OUTPUT=%IN_DIR%%IN_NAME%_fixed.geojsonl"

REM ---- 4) Confirm overwrite if output exists ----
if exist "%OUTPUT%" (
  echo [Warning] Output already exists:
  echo   "%OUTPUT%"
  choice /M "Overwrite?"
  if errorlevel 2 (
    echo Aborted by user.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 0
  )
  del /f /q "%OUTPUT%"
)

echo.
echo [Step] Running ogr2ogr...
echo  - Input : "%INPUT%"
echo  - Output: "%OUTPUT%"
echo.

REM ---- 5) Run ogr2ogr: makevalid + unify geometry + reproject + export as GeoJSONSeq ----
ogr2ogr -f Geo
if errorlevel 1 (
  echo.
  echo [Error] ogr2ogr failed to run.
  echo Press any key to exit...
  pause >nul
  exit /b 1
)
