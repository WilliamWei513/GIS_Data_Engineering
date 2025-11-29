# patch_missing_features.py
# Purpose: Inspect a merged .geojsonl, report duplicates, and patch missing OBJECTIDs from an API.
# Flow:
# 1) Ask for API URL and select a target .geojsonl file
# 2) Report duplicate OBJECTIDs (and save a CSV report)
# 3) Identify missing OBJECTIDs, fetch them from the API, and append to the file

import json
import requests
import os
from collections import Counter
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from datetime import datetime

# Read existing OBJECTIDs from a line-delimited GeoJSON file
def extract_existing_objectids(geojsonl_path):
    object_ids = set()
    with open(geojsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                feat = json.loads(line)
                oid = feat.get("properties", {}).get("OBJECTID")
                if oid is not None:
                    object_ids.add(oid)
            except Exception as e:
                print(f"Warning: Error reading line: {e}")
    return object_ids

# Count occurrences of OBJECTIDs and log duplicates to CSV if requested
def find_duplicate_objectids(geojsonl_path, log_path=None):
    counter = Counter()
    with open(geojsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                feat = json.loads(line)
                oid = feat.get("properties", {}).get("OBJECTID")
                if oid is not None:
                    counter[oid] += 1
            except Exception as e:
                print(f"Warning: Error parsing line: {e}")

    duplicates = {k: v for k, v in counter.items() if v > 1}
    print(f"\nFound {len(duplicates)} duplicate OBJECTIDs.")
    for oid, count in sorted(duplicates.items(), key=lambda x: -x[1])[:10]:
        print(f"  - OBJECTID {oid} appears {count} times")

    if log_path:
        with open(log_path, "w", encoding="utf-8") as logf:
            logf.write("objectid,count\n")
            for oid, count in sorted(duplicates.items()):
                logf.write(f"{oid},{count}\n")
            print(f"Duplicate report saved to: {log_path}")

    if not duplicates:
        print("No duplicate OBJECTIDs found.")
    return duplicates

# Fetch features from the API by a list of OBJECTIDs (batched)
def fetch_features(api_url, objectid_list):
    features = []
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    ids = list(objectid_list)
    chunk_size = 500  # common ArcGIS constraint
    for i in range(0, len(ids), chunk_size):
        chunk = ids[i:i+chunk_size]
        where = f"OBJECTID in ({','.join(map(str, chunk))})"
        params = {
            "where": where,
            "outFields": "*",
            "f": "geojson"
        }
        try:
            r = requests.get(api_url + "/query", params=params, timeout=60)
            r.raise_for_status()
            data = r.json()
            feats = data.get("features", [])
            features.extend(feats)
            print(f"Retrieved {len(feats)} features for OBJECTIDs {chunk[0]}-{chunk[-1]}")
        except Exception as e:
            print(f"Failed to fetch chunk {chunk[0]}-{chunk[-1]}: {e}")
    return features

# Determine missing OBJECTIDs and append fetched features to the file
def patch_missing(api_url, geojsonl_path, expected_total):
    existing_ids = extract_existing_objectids(geojsonl_path)
    print(f"Existing OBJECTIDs: {len(existing_ids)}")

    missing_ids = [i for i in range(1, expected_total+1) if i not in existing_ids]
    print(f"Missing OBJECTIDs: {len(missing_ids)}")

    if not missing_ids:
        print("No missing OBJECTIDs. Your data is complete.")
        return

    patch_feats = fetch_features(api_url, missing_ids)
    with open(geojsonl_path, "a", encoding="utf-8") as fout:
        for feat in patch_feats:
            fout.write(json.dumps(feat, ensure_ascii=False) + "\n")
    print(f"Patched {len(patch_feats)} missing features.")

    # Write patch log (summary of appended features)
    patch_log = geojsonl_path.replace(".geojsonl", "_patch_log.txt")
    with open(patch_log, "w", encoding="utf-8") as logf:
        logf.write(f"Patched {len(patch_feats)} features\n")
        logf.write(f"OBJECTIDs: {[f.get('properties', {}).get('OBJECTID') for f in patch_feats]}\n")
    print(f"Patch log saved to: {patch_log}")

# CLI entrypoint: collect inputs and run checks/patch
def main():
    api_url = input("Please Enter API URL: ").strip()

    # Select target merged .geojsonl via file dialog
    root = Tk()
    root.withdraw()
    geojsonl_path = askopenfilename(title="选择合并后的 .geojsonl 文件", filetypes=[("GeoJSONL", "*.geojsonl")])
    root.destroy()

    if not geojsonl_path:
        print("No file selected, exitting...")
        return

    expected_total = int(input("Enter expected total number of features: ").strip())

    if not os.path.exists(geojsonl_path):
        print("Provided .geojsonl file does not exist.")
        return

    print("\nChecking for duplicates...")
    dup_log_path = geojsonl_path.replace(".geojsonl", "_duplicates.csv")
    find_duplicate_objectids(geojsonl_path, log_path=dup_log_path)

    print("\nChecking and patching missing features...")
    patch_missing(api_url, geojsonl_path, expected_total)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\nAn unexpected error occurred:\n")
        import traceback
        traceback.print_exc()
    finally:
        try:
            input("\nPress Enter to close this window...")
        except EOFError:
            pass