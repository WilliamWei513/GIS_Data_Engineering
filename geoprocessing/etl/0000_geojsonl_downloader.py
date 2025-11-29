#!/usr/bin/env python3
import os
import sys
import json
import requests
from datetime import datetime
from threading import Thread, Lock
from tkinter import Tk
from tkinter.filedialog import askdirectory
import traceback

print("""
========================================
GeoJSON (line-delimited) Downloader
========================================
""")

# Config
THREADS = 2
REPORT_INTERVAL = 100_000

# Global progress tracking
progress = {}
progress_lock = Lock()

def choose_folder_dialog():
    root = Tk(); root.withdraw()
    folder = askdirectory(title="Select Download Folder")
    root.destroy()
    if not folder:
        print("Warning: no folder selected, exiting")
        sys.exit(1)
    return folder

def prompt(msg, default=None):
    v = input(msg + (" " if default is None else f"[{default}] ")).strip()
    return v or default

def get_max_record_count(api_url):
    r = requests.get(api_url + "?f=json", timeout=30)
    r.raise_for_status()
    return int(r.json().get("maxRecordCount", 500))

def get_total_count(api_url):
    r = requests.get(api_url + "/query", params={
        "where": "1=1", "returnCountOnly": "true", "f": "json"
    }, timeout=30)
    r.raise_for_status()
    return int(r.json().get("count", 0))

def save_progress(progress_path, tid, offset, downloaded):
    with progress_lock:
        progress[tid] = {"offset": offset, "downloaded": downloaded}
        with open(progress_path, "w", encoding="utf-8") as pf:
            json.dump(progress, pf, indent=2)

def download_thread(api_url, start, end, page_size, out_file, ckpt_file, tid, start_time, folder, basename):
    # checkpoint resume
    if os.path.exists(ckpt_file):
        with open(ckpt_file) as f:
            offset = int(f.read())
        mode = "a"
        print(f"[T{tid}] Resuming at offset {offset}")
    else:
        offset = start
        mode = "w"
        if os.path.exists(out_file):
            os.remove(out_file)

    downloaded = offset - start
    next_report = REPORT_INTERVAL
    progress_path = os.path.join(folder, f"{basename}_progress.json")

    with open(out_file, mode, encoding="utf-8") as f:
        while offset <= end:
            params = {
                "where": "1=1",
                "outFields": "*",
                "f": "geojson",
                "orderByFields": "OBJECTID ASC",  # ensure stable order
                "resultOffset": offset,
                "resultRecordCount": page_size
            }

            # auto retry up to 3 times
            for attempt in range(3):
                try:
                    r = requests.get(api_url + "/query", params=params, timeout=60)
                    r.raise_for_status()
                    break
                except Exception as e:
                    print(f"[T{tid}] Retry {attempt+1}/3 failed at offset {offset}: {e}")
                    if attempt == 2:
                        print(f"[T{tid}] Aborting after 3 failed attempts.")
                        save_progress(progress_path, tid, offset, downloaded)
                        return

            data = r.json()
            feats = data.get("features", [])

            if not feats:
                # Empty page: skip ahead
                print(f"[T{tid}] Empty page at offset {offset}, skipping ahead.")
                offset += page_size
                continue

            for feat in feats:
                f.write(json.dumps(feat, ensure_ascii=False) + "\n")

            count = len(feats)
            downloaded += count
            offset += count
            with open(ckpt_file, "w") as c:
                c.write(str(offset))

            # periodic progress save
            if downloaded >= next_report:
                pct = downloaded / (end - start + 1)
                elapsed = datetime.now() - start_time
                print(f"[T{tid}] Downloaded {downloaded:,}/{end-start+1:,} ({pct:.1%}), elapsed {elapsed}")
                save_progress(progress_path, tid, offset, downloaded)
                next_report += REPORT_INTERVAL

    print(f"[T{tid}] Finished at offset {offset}, total {downloaded:,}")

def merge_geojsonl(folder, basename):
    import hashlib
    
    def get_oid(feature):
        props = feature.get("properties", {})
        return props.get("OBJECTID") or props.get("FID") or None

    in_paths = [os.path.join(folder, f"{basename}_t{tid}.geojsonl") for tid in range(1, THREADS+1)]
    out_path = os.path.join(folder, f"{basename}.geojsonl")

    seen = set()
    kept = 0
    dupes = 0

    with open(out_path, "w", encoding="utf-8") as fout:
        for p in in_paths:
            with open(p, "r", encoding="utf-8") as fin:
                for line in fin:
                    try:
                        feat = json.loads(line)
                        oid = get_oid(feat)
                        if oid is not None:
                            if oid in seen:
                                dupes += 1
                                continue
                            seen.add(oid)
                        else:
                            # fallback to hashing the geometry+props
                            sig = hashlib.md5(line.encode()).hexdigest()
                            if sig in seen:
                                dupes += 1
                                continue
                            seen.add(sig)
                        fout.write(json.dumps(feat, ensure_ascii=False) + "\n")
                        kept += 1
                    except Exception as e:
                        print(f"Warning: Error reading line from {p}: {e}")
            os.remove(p)

    print(f"Merged into {out_path}, kept: {kept}, removed duplicates: {dupes}")
    return out_path

def to_featurecollection(in_geojsonl, out_geojson, total):
    print(f"Wrapping lines to FeatureCollection: {out_geojson}")
    with open(in_geojsonl, "r", encoding="utf-8") as fin, \
         open(out_geojson, "w", encoding="utf-8") as fout:
        fout.write('{"type":"FeatureCollection","features":[\n')
        first = True
        count = 0
        for line in fin:
            if not first:
                fout.write(",\n")
            fout.write(line.strip())
            first = False
            count += 1
            if count % (total//10 or 1) == 0:
                print(f"  wrap progress {count/total:.0%}")
        fout.write("\n]}")
    print("Wrap done.")

def main():
    print("Please select a folder to start download")
    folder = choose_folder_dialog()
    basename = prompt("2) Enter output base name (no extension):")
    api_url = prompt("3) Enter API service URL:")
    only_l = prompt("4) Only output geojsonl? (y/n):", "n").lower().startswith("y")

    start_time = datetime.now()
    print(f"\n>>> Start download @ {start_time} <<<\n")

    total = get_total_count(api_url)
    page_size = get_max_record_count(api_url)
    print(f"Total features: {total:,}, page size: {page_size}\n")

    per = total // THREADS
    threads = []
    for i in range(THREADS):
        s = i * per
        e = (i+1) * per - 1 if i < THREADS-1 else total - 1
        out_file = os.path.join(folder, f"{basename}_t{i+1}.geojsonl")
        ckpt_file = os.path.join(folder, f"{basename}_t{i+1}.chk")
        t = Thread(target=download_thread,
                   args=(api_url, s, e, page_size, out_file, ckpt_file, i+1, start_time, folder, basename))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    confirm = input("\nAll threads finished. Merge now? (y/n): ").lower()
    if confirm != "y":
        print("Skipping merge. You can inspect geojsonl shards manually.")
        return

    geojsonl = merge_geojsonl(folder, basename)
    final = geojsonl
    if not only_l:
        out_fc = os.path.join(folder, f"{basename}.geojson")
        to_featurecollection(geojsonl, out_fc, total)
        final = out_fc

    # Write log file (includes actual downloaded count)
    log_path = os.path.join(folder, f"{basename}_download_log.txt")
    end_time = datetime.now()

    actual_downloaded = 0
    progress_path = os.path.join(folder, f"{basename}_progress.json")
    if os.path.exists(progress_path):
        with open(progress_path, "r", encoding="utf-8") as pf:
            progress_data = json.load(pf)
            actual_downloaded = sum(t["downloaded"] for t in progress_data.values())

    with open(log_path, "w", encoding="utf-8") as lg:
        lg.write(f"API URL       : {api_url}\n")
        lg.write(f"Format        : geojsonl\n")
        lg.write(f"Output file   : {final}\n")
        lg.write(f"Expected total: {total}\n")
        lg.write(f"Downloaded    : {actual_downloaded}\n")  
        lg.write(f"Start time    : {start_time}\n")
        lg.write(f"End time      : {end_time}\n")
        lg.write(f"Elapsed       : {end_time - start_time}\n")

    print(f"\n>>> Done in {end_time - start_time}, log: {log_path} <<<")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\nAn unexpected error occurred:\n")
        traceback.print_exc()
    finally:
        try:
            input("\nPress Enter to close this window...")
        except EOFError:
            pass