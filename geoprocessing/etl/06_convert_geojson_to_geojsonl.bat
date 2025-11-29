@echo off
setlocal

echo ========================================
echo GeoJSON to GeoJSON (line-delimited) Convertor
echo ========================================
echo.
echo Select a geojson to convert into geojsonl...
echo.

REM —— 2) Popup to select GeoJSON input ——  
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dlg=New-Object System.Windows.Forms.OpenFileDialog; $dlg.Filter='GeoJSON 文件 (*.geojson)|*.geojson|所有文件 (*.*)|*.*'; if ($dlg.ShowDialog() -eq 'OK') { $dlg.FileName | Out-File -FilePath '%TEMP%\infile.txt' -Encoding ascii }"
if not exist "%TEMP%\infile.txt" (
  echo No file selected, exiting...
  pause
  exit /b 1
)
set /p INPUT=<%TEMP%\infile.txt
del "%TEMP%\infile.txt"

REM —— 3) Generate output path (same name but with .geojsonl extension) ——  
for %%F in ("%INPUT%") do (
  set "OUT=%%~dpF%%~nF.geojsonl"
)

echo.
echo Converting: %INPUT%
echo To       : %OUT%
echo.

REM —— 4) Call ogr2ogr GeoJSONSeq and show progress ——  
ogr2ogr -progress -f GeoJSONSeq "%OUT%" "%INPUT%"

echo.
echo Conversion complete!
echo Output file: %OUT%
pause
endlocal
