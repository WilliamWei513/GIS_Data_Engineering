@echo off
setlocal

echo ========================================
echo GeoPackage to GeoJSON or GeoJSON (line-delimited) Convertor
echo ========================================
echo.
echo A file dialog will now open to select the input GeoJSON/GeoJSONL file...
echo.

REM 1) Popup to select GeoJSON or GeoJSONL input
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title = 'Select GeoJSON or GeoJSONL Input File'; $d.Filter='GeoJSON/GeoJSONL (*.geojson;*.geojsonl)|*.geojson;*.geojsonl'; if ($d.ShowDialog() -eq 'OK') { $d.FileName | Out-File '%TEMP%\in.txt' -Encoding ascii }"
if not exist "%TEMP%\in.txt" (
    echo No input file selected.
    goto :end
)
set /p IN=<%TEMP%\in.txt
del "%TEMP%\in.txt"

echo An additional file dialog will now open to select the output folder...
echo.

REM 2) Popup to select output folder
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description = 'Select Output Folder'; if ($d.ShowDialog() -eq 'OK') { $d.SelectedPath | Out-File '%TEMP%\outdir.txt' -Encoding ascii }"
if not exist "%TEMP%\outdir.txt" (
    echo No output folder selected.
    goto :end
)
set /p OUT_DIR=<%TEMP%\outdir.txt
del "%TEMP%\outdir.txt"

REM 3) Create output file path and detect input extension
for %%F in ("%IN%") do (
    set "FILENAME=%%~nF"
    set "EXT=%%~xF"
)
set "OUT=%OUT_DIR%\%FILENAME%.gpkg"

REM 3.1) Configure ogr2ogr options based on input type
set "OGR_EXTRA_OPTS="
if /I "%EXT%"==".geojsonl" set "OGR_EXTRA_OPTS=-oo FEATURE_COLLECTION=NO"

REM 4) Run ogr2ogr with progress (adds spatial index); sets layer name as filename
echo Converting "%IN%" to "%OUT%" (type: %EXT%)
ogr2ogr -progress -f GPKG "%OUT%" "%IN%" %OGR_EXTRA_OPTS% -dsco SPATIAL_INDEX=YES -nln "%FILENAME%"

REM 5) Report result and keep the window open (avoid accidental terminal close)
if %errorlevel%==0 (
    echo Conversion successful!
    echo Output file: %OUT%
) else (
    echo Conversion failed. Please verify the input file and GDAL installation.
)

:end
pause