import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox

print("""
========================================
Check GeoJSON (line-delimited) Format
========================================

Select a .geojsonl file to check format...
""")

def check_geojsonl_format(file_path, max_lines=1000):
    """Validate that a file is line-delimited GeoJSON (GeoJSONL).

    Reads up to max_lines, counting valid Feature lines vs invalid ones.
    Shows a message box with the summary result.
    """
    valid_lines = 0
    invalid_lines = 0

    try:
        # Open file and check each non-empty line is a valid GeoJSON Feature
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if obj.get("type") != "Feature":
                        invalid_lines += 1
                    else:
                        valid_lines += 1
                except json.JSONDecodeError:
                    invalid_lines += 1
    except Exception as e:
        # Show error if the file cannot be opened/read
        messagebox.showerror("Error", f"Error opening file: {e}")
        return

    summary = f"Valid Feature lines: {valid_lines}\nInvalid or skipped lines: {invalid_lines}\n"
    if valid_lines == 0:
        summary += "ERROR: This file is not a valid GeoJSONL file."
        messagebox.showerror("Validation Result", summary)
    elif invalid_lines > 0:
        summary += "WARNING: Some lines are invalid GeoJSON Features."
        messagebox.showwarning("Validation Result", summary)
    else:
        summary += "OK: File is a valid GeoJSONL format for ogr2ogr."
        messagebox.showinfo("Validation Result", summary)

if __name__ == "__main__":
    try:
        # Prompt user to select a .geojsonl file
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(title="Select a GeoJSONL file to validate", filetypes=[("GeoJSONL Files", "*.geojsonl"), ("All Files", "*.*")])

        if file_path and os.path.isfile(file_path):
            # Run validation and show results
            check_geojsonl_format(file_path)
        else:
            print("No valid file was selected")

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
