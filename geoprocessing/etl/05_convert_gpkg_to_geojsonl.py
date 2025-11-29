import fiona
import os
import json
import pandas as pd
import numpy as np
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely import wkt
from tkinter import Tk, filedialog
from tqdm import tqdm

print("""
========================================
GeoPackage to GeoJSON (line-delimited) Convertor 
========================================

Select a GeoPackage to convert into geojsonl...
""")

def convert_all_layers_to_geojsonl(gpkg_path):
    try:
        out_path = os.path.splitext(gpkg_path)[0] + '.geojsonl'
        print(f'Merging layers from: {gpkg_path}')

        layers = fiona.listlayers(gpkg_path)
        if not layers:
            print(f"No layers found in {gpkg_path}")
            return False, 0, 0

        output_feature_count = 0
        input_feature_count = 0

        with open(out_path, 'w', encoding='utf-8') as out_file:
            for layer in layers:
                print(f"Reading layer: {layer}")
                with fiona.open(gpkg_path, layer=layer) as src:
                    input_feature_count += len(src)
                    for feat in tqdm(src, total=len(src), desc=f"{os.path.basename(gpkg_path)}:{layer}"):
                        try:
                            raw_geometry = feat.get('geometry')
                            if raw_geometry is None:
                                continue  # skip features with null geometry

                            # Convert to valid GeoJSON format using shapely
                            try:
                                geom = shape(raw_geometry)
                                geometry = mapping(geom)
                            except Exception as geom_error:
                                print(f"Geometry conversion error: {geom_error}")
                                continue

                            props = {}
                            for k, v in feat['properties'].items():
                                if pd.isna(v):
                                    props[k] = None
                                elif isinstance(v, (np.generic, pd.Timestamp)):
                                    props[k] = str(v)
                                else:
                                    props[k] = v

                            feature = {
                                "type": "Feature",
                                "geometry": geometry,
                                "properties": props
                            }

                            out_file.write(json.dumps(feature) + '\n')
                            output_feature_count += 1
                        except (TypeError, ValueError) as fe:
                            print(f'JSON serialization error: {fe}')
                            continue
                        except Exception as fe:
                            print(f'Skipped feature due to error: {fe}')
                            continue

        print(f'Saved to: {out_path}')
        print(f'Total features written: {output_feature_count}')
        if input_feature_count != output_feature_count:
            print(f'Mismatch: read {input_feature_count}, wrote {output_feature_count}')
        else:
            print(f'All features written correctly')
        return True, input_feature_count, output_feature_count

    except Exception as e:
        print(f'Failed to convert {gpkg_path}: {e}')
        return False, 0, 0

if __name__ == '__main__':
    try:
        while True:
            Tk().withdraw()
            file_paths = filedialog.askopenfilenames(
                title='Select GPKG files to convert',
                filetypes=[("GeoPackage files", "*.gpkg")]
            )

            if not file_paths:
                print("No files selected.")
                retry = input("Do you want to select files again? (y/n): ").strip().lower()
                if retry != 'y':
                    break
                continue
            else:
                for gpkg in file_paths:
                    try:
                        success, input_count, output_count = convert_all_layers_to_geojsonl(gpkg)
                        if not success:
                            print(f'Conversion failed for {gpkg}')
                        elif input_count != output_count:
                            print(f'Feature count mismatch for {gpkg}: input={input_count}, output={output_count}')
                    except Exception as e:
                        print(f'Unexpected error during conversion: {e}')

            again = input("Do you want to convert more files? (y/n): ").strip().lower()
            if again != 'y':
                break

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred:\n")
        import traceback
        traceback.print_exc()
    finally:
        # Always keep terminal open for review
        try:
            input("\nPress Enter to close this window...")
        except (EOFError, KeyboardInterrupt):
            pass