import geopandas as gpd
import os
import threading
from tkinter import Tk, filedialog
from math import ceil
import sys
import traceback

print("""
========================================
Large Data Splitter (FEMA)
========================================

Select a GeoPackage to split into shards...
""")

# --- File selection dialog helper ---
def select_file():
    """Open a file dialog to pick a .gpkg and return its path."""
    try:
        root = Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            title="Select FEMA Flood Zones GPKG",
            filetypes=[("GeoPackage files", "*.gpkg")]
        )
        root.destroy()
        return file_path
    except Exception as e:
        # Guard against UI-related failures
        print("ERROR: File selection failed:", e)
        input("Press Enter to exit...")
        sys.exit(1)

# --- Writer for a chunk into a single-layer GPKG ---
def save_chunk_to_single_layer_gpkg(gdf_chunk, out_path, layer_name, thread_idx):
    """Write a GeoDataFrame chunk into a GPKG layer; runs in a thread."""
    try:
        total = len(gdf_chunk)
        if total == 0:
            print(f"[Thread {thread_idx}] No features to write for {out_path}")
            return

        print(f"[Thread {thread_idx}] Writing {total} features to {out_path} (layer: {layer_name})")
        gdf_chunk.to_file(out_path, driver='GPKG', layer=layer_name)
        print(f"[Thread {thread_idx}] Completed {out_path}")

    except Exception as e:
        # Log and surface errors (also attempt a GUI message if possible)
        print(f"ERROR: Failed saving chunk to {out_path}: {e}")
        traceback.print_exc()
        try:
            from tkinter import messagebox
            messagebox.showerror("Save Error", f"Error saving chunk to {out_path}:\n{e}")
        except:
            pass
        input("Press Enter to exit...")
        os._exit(1)  # Force exit all threads

# --- Main pipeline ---
def main():
    try:
        # 1) Input selection
        print("Please select the .gpkg file")
        input_path = select_file()
        if not input_path:
            print("No file selected. Exiting.")
            input("Press Enter to exit...")
            return

        # 2) List layers and pick the first one
        print(f"Reading GeoPackage: {input_path}")
        import fiona
        try:
            layers = fiona.listlayers(input_path)
        except Exception as e:
            print(f"ERROR: Failed reading layers: {e}")
            traceback.print_exc()
            input("Press Enter to exit...")
            return

        if not layers:
            print("ERROR: No layers found.")
            input("Press Enter to exit...")
            return
        layer_name = layers[0]
        print(f"Using first layer: {layer_name}")

        # 3) Read the chosen layer into memory (timed)
        import time
        try:
            start_time = time.time()
            gdf = gpd.read_file(input_path, layer=layer_name)
            elapsed = time.time() - start_time
            print(f"File read completed in {elapsed:.2f} seconds.")
        except Exception as e:
            print(f"ERROR: Failed reading file: {e}")
            traceback.print_exc()
            input("Press Enter to exit...")
            return

        # 4) Validate features count
        total = len(gdf)
        print(f"Total features: {total}")

        if total == 0:
            print("ERROR: No features found in the layer.")
            input("Press Enter to exit...")
            return

        # 5) Determine chunk size and output directory
        chunk_size = ceil(total / 10)
        threads = []
        output_dir = os.path.join(os.path.dirname(input_path), "floodzone_split_10parts")
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            print(f"❌ Error creating output directory: {e}")
            traceback.print_exc()
            input("Press Enter to exit...")
            return

        # 6) Create and start threads to write each chunk
        for i in range(10):
            start = i * chunk_size
            end = min((i + 1) * chunk_size, total)
            gdf_chunk = gdf.iloc[start:end]
            out_file = os.path.join(output_dir, f"flood_split_{i+1}.gpkg")
            layer = f"flood_split_{i+1}"
            print(f"Writing features {start} to {end} --> {out_file} (layer: {layer})")

            t = threading.Thread(target=save_chunk_to_single_layer_gpkg, args=(gdf_chunk, out_file, layer, i+1))
            t.start()
            threads.append(t)

        # 7) Wait for all threads to finish
        for t in threads:
            t.join()

        # 8) Report completion
        print(f"All 10 chunks saved to: {output_dir}")
        input("Press Enter to exit...")

    except Exception as e:
        # Catch-all for any fatal errors
        print("ERROR: A fatal error occurred:")
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
