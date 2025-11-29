# Mapbox & GIS Data Management, a guide
This guide explains how to download, upload/process, visualize, & deploy/update GIS data for Algoma App working with Mapbox Studio

**01 | Download** GIS data following [Download GIS Data](#01--download-gis-data)  
**02 | Upload/Process** Jump to [Upload Under 300MB](#021--upload-under-300mb) / [Upload Above 300MB](#022--upload-above-300mb) depending on the size of your data  
**03 | Visualize** Follow [Visualize Data](#03--visualize-data) to visualize the new data layer using Mapbox Studio `Style Editor`  
**04 | Deploy/Update** Submit a ticket at [Notion page - Create A Ticket](https://www.notion.so/algoma/Create-a-Ticket-222aab45600880809933cf9d0caebe8f?source=copy_link) and work with our SDE team to [Deploy/Update](#04--deploy-and-update-data) the new data layers  

```bash
QUICK START

# Download Data-Engineering Scripts
1. Our available geo-processing scripts are in the repo at `/data-engineering/geoprocessing`
2. Click the green button `<> Code` and `Download ZIP` under the tab `local`
3. Extract the ZIP file to your local disk

# Install Dependencies
## Python 3.13 (64-bit) or above 
Download and install Python 3.13+ from [python.org](https://www.python.org/downloads/)

## Python Packages
pip install -r python_requirements.txt ### download the list & run this command line through cmd where it's located

## GDAL 3.11.0 "Eganville"
conda install -c conda-forge gdal=3.11.0

-- Add the GDAL bin folder (e.g., `C:\OSGeo4W64\bin`) to your Windows System Environment Variables
-- Open Command Prompt and type `ogr2ogr --version` to confirm installation

## Tilesets CLI of Mapbox Tiling Service 
pip install mapbox-tilesets
```

## 01 | Download GIS Data
You can find our standard GIS data source archived at [Notion page - GIS Data Sources](https://www.notion.so/algoma/22caab45600880069002c3990ed1e3b6?v=22caab4560088097ad17000c5bc6ed73&source=copy_link)  
Please use the script `0000_geojsonl_downloader.py` in `/data-engineering/geoprocessing` to download geojsonl data for most APIs

## 02.1 | Upload Under 300MB
**GeoJSON, Shapefile (zipped), KML, GPX, CSV, & Geo-TIFF below 300MB can be directly uploaded in Mapbox Studio GUI**

1. Login to [Mapbox Studio](https://www.bing.com/ck/a?!&&p=37c529251936080d3e44caef1e35854b703cc6a80ab8fe3af3d2ff461dd8e6ebJmltdHM9MTc1NTgyMDgwMA&ptn=3&ver=2&hsh=4&fclid=0e880a61-c8cc-68dc-1f69-1c6ec9ae6988&psq=mapbox+studio+login&u=a1aHR0cHM6Ly9hY2NvdW50Lm1hcGJveC5jb20vYXV0aC9zaWduaW4v&ntb=1) using one password credentials
2. Navigate to Mapbox Studio GUI tab `Data Manager` on the left column 
3. Click upload blue button `New tilset` to select & upload your GIS data
4. A new tileset will be listed under the tab of `Tilesets` in `Data Manager`, if your upload succeeds

## 02.2 | Upload Above 300MB
**You are required to use `Tilesets CLI` of Mapbox Tiling Service if your data is larger than 300MB**

1. Navigate to the repo at `/data-engineering/geoprocessing` 
2. Read [Why Geoprocessing](#why-geoprocessing) to know strictly what `type/format` of data is required for `Tilesets CLI`
3. Read [How Geoprocessing](#how-geoprocessing) to know how to use the scripts for different purposes
4. Follow [Mapbox Tiling Service](#mapbox-tiling-service) to upload your processed GIS data using `Tilesets CLI`


### Why Geoprocessing
1. Tilesets CLI of Mapbox Tiling Service ONLY accepts line-delimited GeoJSON data `.geojsonl`, when the data is larger than 300MB. Format difference: [Newline-delimited GeoJSON](https://stevage.github.io/ndgeojson/)  
2. The data format downloadablee from those open source API archived at our [Notion page - GIS Data Sources](https://www.notion.so/algoma/22caab45600880069002c3990ed1e3b6?v=22caab4560088097ad17000c5bc6ed73&source=copy_link) are always GeoJSON  
3. Our geoprocessing scripts can do converting, threading, slicing, patching, and deduplicating according to the requirements by Mapbox

### How Geoprocessing
1. Find the scripts at your local folder `/data-engineering/geoprocessing`  
2. The scripts are organized in a logical workflow sequence, with batch files (.bat) for Windows OS and Python scripts for more complex processing tasks  
3. The scripts are not hard coded with specific file path, so you can simply **double-click to run them**. For Python scripts (`.py`), you may have to right-click the file and select **"Open with" > "Python"**  
4. All scripts will display hints, pop-up windows, or command-line prompts to guide you through the required inputs and options  

**Phase 1 | Data Acquisition**  
Download Data (`0000_geojsonl_downloader.py`)
> _Download large datasets from ArcGIS APIs_

Convert to GeoPackage (`00_convert_geojson_or_geojsonl_to_gpkg.bat`)
> _Convert GeoJSON/GeoJSONL to GeoPackage for smaller file size and processing efficiency_

**Phase 2 | Data Optimization**
Create Spatial Index (`01_create_space_index_for_gpkg.bat`)
> _Spatial index is required for better performance of commands like searching & clipping_

Split Large Datasets (`04_split_gpkg_data_by_index.py`)
> _Mapbox requires each single tile source to be smaller than 20GB_

**Phase 3 | Quality Assurance**  
Verify Spatial Index (`02_check_gpkg_if_space_index_exists.bat`)
> _Confirm spatial index was created successfully_

Validate Geometry (`03_validate_geom_of_gpkg.bat`)
> _Check for geometry errors and invalid features_

Validate Format (`92_check_geojsonl_format.py` or `07_validate_geojsonl.bat`)
> _Ensure data format integrity_

Clip Data (`91_clip_gpkg_with_kml.bat`)
> _Use this script to extract a sample data and cross check with other online data sources if you have a specific site you wanna double check_
> _You need to prepare a kml as the extent you use to clip the larger data_

Patch Missing Features* (`000_patch_missing_features.py`)
> _Don't use this script, unless you are sure that you missed some part of data during the downloading process_

**Phase 4 | Conversion for Upload**  
Convert Back to GeoJSONL (`05_convert_gpkg_to_geojsonl.py` or `06_convert_geojson_to_geojsonl.bat`)
> _The Tilesets CLI by Mapbox Tiling Service only accept geojosnl to upload_

Flatten GeometryCollection (`93_flatten_geometrycollection_in_geojsonl.bat`)
> _Tilesets CLI will flag error if you are uploading a geojsonl as a GeometryCollection (containing multiple types of geometry: point/line/polygon)_  
---

Output Files
- GeoJSONL | Line-delimited format, one feature per line
- GeoPackage | SQLite-based format with spatial indexing
- Log files | Processing logs with timing and feature counts
- Progress files | JSON files tracking download progress
- Checkpoint files | Resume points for interrupted operations  

Important Notes
- Memory Usage | Large dataset processing may require significant RAM & time
- Network Stability | Download scripts include retry logic but require stable internet  

Troubleshooting
- GDAL not found | Ensure ogr2ogr is in your system PATH
- Memory errors | Use the splitter script for very large datasets
- Network timeouts | Check internet connection and API availability  
---

### Mapbox Tiling Service

1. [This](https://docs.mapbox.com/help/tutorials/get-started-mts-and-tilesets-cli/?step=0) is the official step-by-step tutorial by Mapbox. Please follow the tutorial to start (note: we don't upload raster data) 
>You need a secret Mapbox Access Token to set as an environment variable to run `Tilesets CLI` of Mapbox Tiling Service. Please ask William for the secret token

2. Your upload will be stored as a `tile source` hosted by Mapbox server. The largest single `tile source` should be **20GB**. You can upload multiple files to constitute a single tile source, only if their sum is smaller than **20GB**
3. Please use our geoprocessing scripts to split huge data (especially FEMA FHZ) into parts smaller than **20GB**
4. After creating the tile source, create a JSON recipe to prescribe the zoom level & tile source constituents for the final `tileset` under `Data Manager`. Please follow the official step-by-step tutorial mentioned above to create the final tileset
>Zoom level has a huge effect on CUs (computing units calculated by Mapbox Studio to BILL our usage). Please ask William for advide, if you are not sure how to get a proper zoom level range. Generally you should keep the max zoom level down to 14, unless it's necessary to retain high fidelity at higher zoom level at cost exponential price

5. Please find below as two examples of the JSON recipes:

RECIPE | FEMA Flood Hazard Zone
```json
{
    "version": 1,
    "layers": {
      "fema_fhz_01": {
        "source": "mapbox://tileset-source/jjbromo/fema-fhz-01",
        "minzoom": 10,
        "maxzoom": 14
      },
      "fema_fhz_02": {
        "source": "mapbox://tileset-source/jjbromo/fema-fhz-02",
        "minzoom": 10,
        "maxzoom": 14
      },
      "fema_fhz_03": {
        "source": "mapbox://tileset-source/jjbromo/fema-fhz-03",
        "minzoom": 10,
        "maxzoom": 14
      },
      "fema_fhz_04": {
        "source": "mapbox://tileset-source/jjbromo/fema-fhz-04",
        "minzoom": 10,
        "maxzoom": 14
      },
      "fema_fhz_05": {
        "source": "mapbox://tileset-source/jjbromo/fema-fhz-05",
        "minzoom": 10,
        "maxzoom": 14
      }
    }
  }  
  ```

RECIPE | FEMA National Risk Index - Strong Wind
```json
{
  "version": 1,
  "layers": {
    "FEMA Strong Wind National Risk Index": {
      "source": "mapbox://tileset-source/jjbromo/fema-strongwind-nri",
      "minzoom": 3,
      "maxzoom": 12
    }
  }
}
```

- [This](https://github.com/mapbox/tilesets-cli/blob/master/README.md#upload-source) is the official GitHub page of the `Tileset CLI`. Please dig into this if you need, but **DO NOT use the `append` command line** in that. 

## 03 | Visualize Data
1. Navigate to Mapbox Studio Sytle Editor on the left column of GUI after logging into Mapbox Studio
2. Under tab `Styles` click to enter **Algoma App Map -  with layers** 
3. On the left side bar: click `Layers` > `Custom layer` > `Source` > `None selected` > search & add the `Tilesets` you created under `Data Manager` from the previous steps
4. Define the `Type` of the layer (commonly as fill, line, or symbol). We use type: symbol to display the data as text labels
5. After adding the new layer, click on it and tweak around its properties to create a proper visual representation of the data. (Tweak `opacity` for fading effects)
6. Use `Add another condition` to filter through values of the data attribute table for specific visual differentiation
7. Turn on/off other existing layers around to eliminate visual errors & conflicts

## 04 | Deploy and Update Data
1. Link to [Notion page - Submit a Ticket](https://www.notion.so/algoma/Create-a-Ticket-222aab45600880809933cf9d0caebe8f?source=copy_link). Describe what updates you have made & assign the product team to review the updated style
2. After both the updates have been approved, hit the `Publish` button on the top right corner of `Algoma App Map - with layers` in Mapbox Studio Style Editor
3. Submit another ticket to work with the SDE team to update the frontend codes, which is required to finally deploy the updates for our app


### 
```bash
Basic Lexicon

Data Manager # The Mapbox Studio interface section for uploading, managing, and organizing your data and tilesets

Tilesets # Datasets processed into vector or raster tiles for use under Data Manager

Style Editor # The Mapbox Studio tool for visually designing and editing map styles
Mapbox Style # A JSON-based configuration that defines the appearance and behavior of a map under Style Editor

Mapbox Tiling Service # A CLI based portal by Mapbox for uploading data larger than 300MB

Tilesets CLI # The command-line tool for uploading, managing, and publishing tilesets with Mapbox Tiling Service

Tile Source # The original geospatial data file or dataset (not displayed anywhere on the Mapbox Studio GUI) used as input for creating tilesets

Recipe # A JSON file that specifies how source data is transformed and tiled by the Mapbox Tiling Service

tileset_id # The unique identifier for a tileset in Mapbox, used to reference and manage the tileset

source_id # The unique identifier for a tile source in Mapbox, referenced in recipes for composing tilesets
```