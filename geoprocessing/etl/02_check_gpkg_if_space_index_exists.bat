@echo off
setlocal

echo ========================================
echo Space Index Checker
echo ========================================
echo.
echo Select a GeoPackage to check if space index exists...
echo.

REM -- Open a file dialog to select the GeoPackage --
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title = 'Select GeoPackage (.gpkg)'; $d.Filter='GeoPackage (*.gpkg)|*.gpkg'; if ($d.ShowDialog() -eq 'OK') { $d.FileName | Out-File '%TEMP%\gpkg_in.txt' -Encoding ascii }"
if not exist "%TEMP%\gpkg_in.txt" (
  echo No file selected. Exiting...
  pause
  exit /b 1
)
set /p GPKG=<%TEMP%\gpkg_in.txt
del %TEMP%\gpkg_in.txt

echo.
REM -- Show which file was selected --
echo Selected file: %GPKG%

echo ----------------------------------------------------
REM -- List layers within the selected GeoPackage --
echo Available layers:
ogrinfo "%GPKG%"

echo.
REM -- Ask the user to choose a layer name from the list --
set /p LAYER=2) Type one of the layer names listed above, then press Enter:

if not defined LAYER (
  echo No layer name entered. Exiting...
  pause
  exit /b 1
)

echo.
echo ----------------------------------------------------
REM -- Display summary metadata for the selected layer --
echo Showing metadata for layer "%LAYER%" in "%GPKG%"...
echo.

REM -- Call ogrinfo -so to print layer details --  
ogrinfo -so "%GPKG%" "%LAYER%"

echo.
REM -- Check whether the expected R-Tree index table exists for this layer --
echo R-Tree index table presence:
ogrinfo %GPKG% -dialect sqlite -sql ^
  "SELECT name FROM sqlite_master WHERE type='table' AND name='rtree_%LAYER%_geom';"

echo.
REM -- Count rows in the layer's R-Tree index table (if present) --
echo Number of entries in the index table:
ogrinfo "%GPKG%" -sql "SELECT COUNT(*) AS cnt FROM rtree_%LAYER%_geom" -q

REM -- Keep the terminal open until the user decides to close --
pause
endlocal
