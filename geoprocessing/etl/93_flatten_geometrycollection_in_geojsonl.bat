@echo off
setlocal

echo ========================================
echo Flatten GeometryCollection
echo ========================================
echo. 
echo Select a geojsonl to flatten...
echo.

REM -- 2) Select source GeoJSONL via file dialog --
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $dlg=New-Object System.Windows.Forms.OpenFileDialog; $dlg.Filter='GeoJSONL (*.geojsonl)|*.geojsonl|All files (*.*)|*.*'; if ($dlg.ShowDialog() -eq 'OK') { $dlg.FileName | Out-File -FilePath '%TEMP%\src.txt' -Encoding ascii }"
if not exist "%TEMP%\src.txt" (
  echo No file selected, exiting...
  goto END
)
set /p SRC=<%TEMP%\src.txt
del "%TEMP%\src.txt"

REM -- 3) Compute output file and layer name --
for %%F in ("%SRC%") do (
  set "DIR=%%~dpF"
  set "BASE=%%~nF"
)
set "FIXED=%DIR%%BASE%_poly.geojsonl"
set "LAYER=%BASE%"

echo.
echo ----- Flatten GeometryCollection -----
echo Input  : %SRC%
echo Output : %FIXED%
echo Layer  : %LAYER%
echo.

REM -- 4) Run ogr2ogr with SQLite SQL to extract polygons from GeometryCollection --
ogr2ogr -progress -f GeoJSONSeq "%FIXED%" "%SRC%" -dialect sqlite  -sql "SELECT ST_CollectionExtract(geometry,3) AS geometry, * FROM \"%LAYER%\""

echo.
echo Conversion complete!
echo Output file: %FIXED%

:END
echo.
pause
endlocal
