@echo off
setlocal

echo ========================================
echo Space Index Creator
echo ========================================
echo.
echo A file dialog will now open to select the input GeoPackage file...
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
echo.

REM -- List all layers in the GeoPackage --  
echo Available layers:
ogrinfo "%GPKG%"

REM -- Prompt the user to enter a layer name --  
echo.
set /p LAYER=2) Type one of the layer names listed above, then press Enter:

if not defined LAYER (
  echo No layer name entered. Exiting...
  pause
  exit /b 1
)

echo.
REM -- Create a spatial index for the selected layer's 'geom' column --
echo Preparing to create a spatial index on the 'geom' column for layer "%LAYER%"...
ogrinfo "%GPKG%" -dialect sqlite -sql "SELECT CreateSpatialIndex('%LAYER%','geom')"

echo.
REM -- Confirm completion and keep the window open --
echo Spatial index created successfully.
pause
endlocal
