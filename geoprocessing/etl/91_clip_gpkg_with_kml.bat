@echo off
chcp 65001>nul
setlocal

:: —— 1) 记录开始时间 —— 
for /f "delims=" %%T in ('powershell -NoProfile -Command "Get-Date -Format \"yyyy-MM-dd HH:mm:ss\""') do set "START_TIME=%%T"

::: —— 2) 选择输入 GeoPackage —— 
echo Please select the input GeoPackage (.gpkg) in the popup dialog...
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title='Select input GeoPackage (.gpkg)'; $d.Filter='GeoPackage (*.gpkg)|*.gpkg|All files (*.*)|*.*'; if ($d.ShowDialog() -eq 'OK') { $d.FileName | Out-File -FilePath '%TEMP%\gpkg_in.txt' -Encoding ascii }"
if not exist "%TEMP%\gpkg_in.txt" (
  echo Warning: no GeoPackage selected. Exiting.
  pause & exit /b 1
)
set /p INPUT_GPKG=<%TEMP%\gpkg_in.txt
del "%TEMP%\gpkg_in.txt"

::: —— 3) 选择裁剪用 KML —— 
echo Please select the KML file for clipping in the popup dialog...
echo.
echo =====================================================
echo If you don't have a KML file, please draw a polygon using Google Earth Pro and save as KML.
echo =====================================================
echo.
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title='Select KML file for clipping'; $d.Filter='KML (*.kml)|*.kml|All files (*.*)|*.*'; if ($d.ShowDialog() -eq 'OK') { $d.FileName | Out-File -FilePath '%TEMP%\kml_in.txt' -Encoding ascii }"
if not exist "%TEMP%\kml_in.txt" (
  echo Warning: no KML selected. Exiting.
  pause & exit /b 1
)
set /p CLIP_KML=<%TEMP%\kml_in.txt
del "%TEMP%\kml_in.txt"

::: —— 4) 计算 KML 的 bbox（xmin ymin xmax ymax）—— 
for %%F in ("%CLIP_KML%") do (
  set "CLIP_DIR=%%~dpF"
  set "CLIP_NAME=%%~nF"
)
echo Calculating bbox from KML via GDAL...
for /f "tokens=2,3,5,6 delims=(), " %%A in ('ogrinfo -so -al "%CLIP_KML%" ^| findstr /C:"Extent:"') do (
  set "xmin=%%A"
  set "ymin=%%B"
  set "xmax=%%C"
  set "ymax=%%D"
)
if "%xmin%"=="" (
  echo Error: failed to determine bbox from KML. Please ensure GDAL is installed and KML is valid.
  pause & exit /b 1
)

:::: —— 5) 选择导出文件夹（一次）—— 
echo Please choose the output folder for the clipped files in the popup dialog...
powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='Select output folder for clipped files'; if ($d.ShowDialog() -eq 'OK') { $d.SelectedPath | Out-File -FilePath '%TEMP%\out_dir.txt' -Encoding ascii }"
if not exist "%TEMP%\out_dir.txt" (
  echo Warning: no output folder selected. Exiting.
  pause & exit /b 1
)
set /p OUT_DIR=<%TEMP%\out_dir.txt
del "%TEMP%\out_dir.txt"

echo.
echo Input GPKG: %INPUT_GPKG%
echo Clip KML  : %CLIP_KML%
echo BBox       : %xmin% %ymin% %xmax% %ymax%
echo.

::: —— 6) 定义临时和输出路径 —— 
set "TMP_GPKG=%~dp0tmp_bbox.gpkg"
set "OUTPUT_GPKG=%OUT_DIR%\%CLIP_NAME%_clipped.gpkg"
set "OUTPUT_GEOJSON=%OUT_DIR%\%CLIP_NAME%_clipped.geojson"
if exist "%OUTPUT_GPKG%" del "%OUTPUT_GPKG%"
if exist "%OUTPUT_GEOJSON%" del "%OUTPUT_GEOJSON%"

:: —— 7) 第一步：按 bbox 空间索引预筛 —— 
echo =====================================================
echo 1) Spatial filter (using index) – this may take a while…
echo =====================================================
ogr2ogr -progress -f GPKG "%TMP_GPKG%" "%INPUT_GPKG%" -spat %xmin% %ymin% %xmax% %ymax% -lco SPATIAL_INDEX=YES
echo.
echo -- Spatial filter complete --
echo.

::: —— 8) 第二步：多边形精剪 —— 
echo =====================================================
echo 2) Precise clip by KML – please wait…
echo =====================================================
ogr2ogr -progress -f GPKG "%OUTPUT_GPKG%" "%TMP_GPKG%" -clipsrc "%CLIP_KML%" -lco SPATIAL_INDEX=YES
ogr2ogr -progress -f GeoJSON "%OUTPUT_GEOJSON%" "%TMP_GPKG%" -clipsrc "%CLIP_KML%"
echo.
echo -- Precise clip complete (GPKG & GeoJSON) --
echo.

:: —— 9) 删除临时 —— 
del "%TMP_GPKG%"

:: —— 10) 记录结束时间 —— 
for /f "delims=" %%T in ('powershell -NoProfile -Command "Get-Date -Format \"yyyy-MM-dd HH:mm:ss\""') do set "END_TIME=%%T"

::: —— 11) 抓要素总数 —— 
for /f "tokens=3" %%F in (
  'ogrinfo -q -so "%OUTPUT_GPKG%" ^| findstr /C:"Feature Count"'
) do set "FEAT_COUNT_GPKG=%%F"
for /f "tokens=3" %%F in (
  'ogrinfo -q -so "%OUTPUT_GEOJSON%" ^| findstr /C:"Feature Count"'
) do set "FEAT_COUNT_GEOJSON=%%F"

:: —— 12) 计算耗时 —— 
for /f "delims=" %%D in ('powershell -NoProfile -Command "(New-TimeSpan -Start ''%START_TIME%'' -End ''%END_TIME%'').ToString()"') do set "DURATION=%%D"

::: —— 13) 写日志 —— 
(
  echo Start Time         : %START_TIME%
  echo End Time           : %END_TIME%
  echo Duration           : %DURATION%
  echo Input GPKG         : %INPUT_GPKG%
  echo Clip KML           : %CLIP_KML%
  echo Output Dir         : %OUT_DIR%
  echo Output GPKG        : %OUTPUT_GPKG%
  echo Output GeoJSON     : %OUTPUT_GEOJSON%
  echo Feature Count GPKG : %FEAT_COUNT_GPKG%
  echo Feature Count JSON : %FEAT_COUNT_GEOJSON%
) > "%~dp0clip_log.txt"

echo.
echo Done!
echo Output GPKG : %OUTPUT_GPKG%
echo Output JSON : %OUTPUT_GEOJSON%
echo Log file    : %~dp0clip_log.txt
pause
endlocal
