import requests
import json
import time
import os
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class SarasotaZoningDownloader:
    PAGE_LOAD_TIMEOUT = 40
    ELEMENT_WAIT_TIMEOUT = 20
    REQUESTS_TIMEOUT = 60
    
    def __init__(self, download_dir="./downloads"):
        self.download_dir = download_dir
        self.url = "https://library.municode.com/fl/sarasota/codes/zoning?nodeId=ZOCO"
        self.driver = None
        self.events = []  
        
        os.makedirs(download_dir, exist_ok=True)
    
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        prefs = {
            "download.default_directory": os.path.abspath(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True,
            "download.open_pdf_in_system_reader": False
        }
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.set_capability('goog:loggingPrefs', {"performance": "ALL"})

        self.driver = webdriver.Chrome(options=chrome_options)
        
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        })

        try:
            self.driver.execute_cdp_cmd("Network.enable", {})
        except Exception:
            pass
        self.driver.implicitly_wait(10)
    
    def navigate_to_page(self):
        print(f"Navigating to: {self.url}")
        self._event("info", f"Navigate → {self.url}")
        self.driver.get(self.url)
        time.sleep(random.uniform(1.5, 3.5))
        
        WebDriverWait(self.driver, self.PAGE_LOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("Page loaded successfully")
        self._event("ok", "Page loaded")
        time.sleep(random.uniform(0.5, 1.5))
    
    def find_download_button(self):
        try:
            print("Looking for download menu...")
            self._event("info", "Try strategy A: open Downloads menu → select Zoning")
            
            downloads_menu = WebDriverWait(self.driver, self.ELEMENT_WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Download publication PDFs')]"))
            )
            downloads_menu.click()
            print("Clicked Downloads menu")
            self._event("ok", "Clicked Downloads menu")
            time.sleep(random.uniform(0.8, 1.8))
            
            zoning_download = WebDriverWait(self.driver, self.ELEMENT_WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Zoning') and contains(@class, 'btn-pdf-download')]"))
            )
            zoning_download.click()
            print("Clicked Zoning download option")
            self._event("ok", "Clicked Zoning download option")
            time.sleep(random.uniform(0.8, 1.8))

            download_btn = WebDriverWait(self.driver, self.ELEMENT_WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "get-pdf-download-btn"))
            )
            download_btn.click()
            time.sleep(random.uniform(0.5, 1.2))
            print("Clicked DOWNLOAD PDF button")
            self._event("ok", "Clicked DOWNLOAD PDF in modal")
            
            return True
            
        except TimeoutException:
            print("Download menu not found, trying alternative method...")
            self._event("warn", "Strategy A timeout; fallback to strategy B (modal direct)")
            return self.try_alternative_download()
    
    def try_alternative_download(self):
        try:
            print("Trying to find download button in modal...")
            self._event("info", "Try strategy B: locate modal → click DOWNLOAD PDF")
            
            modal = WebDriverWait(self.driver, self.ELEMENT_WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pdf-download-modal"))
            )
            
            download_btn = WebDriverWait(self.driver, self.ELEMENT_WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "get-pdf-download-btn"))
            )
            download_btn.click()
            time.sleep(random.uniform(0.5, 1.2))
            print("Clicked DOWNLOAD PDF button")
            self._event("ok", "Clicked DOWNLOAD PDF in modal (strategy B)")
            
            return True
            
        except TimeoutException:
            print("Download button not found")
            self._event("error", "Modal DOWNLOAD PDF not found (strategy B)")
            return False

    def capture_pdf_url(self, timeout=30):
        print("Capturing PDF URL from network logs...")
        self._event("info", "Capture PDF URL via CDP Network logs")
        end_time = time.time() + timeout
        seen_request_ids = set()
        pdf_url = None
        while time.time() < end_time and pdf_url is None:
            try:
                entries = self.driver.get_log('performance')
            except Exception:
                entries = []
            for entry in entries:
                try:
                    msg = json.loads(entry.get('message', '{}')).get('message', {})
                    method = msg.get('method')
                    params = msg.get('params', {})
                    if method == 'Network.responseReceived':
                        response = params.get('response', {})
                        url = response.get('url', '')
                        mime = response.get('mimeType', '')
                        status = response.get('status')
                        req_id = params.get('requestId')
                        if req_id in seen_request_ids:
                            continue
                        seen_request_ids.add(req_id)
                        if mime == 'application/pdf' or url.lower().endswith('.pdf'):
                            pdf_url = url
                            self._event("ok", f"Response PDF detected (status={status}): {url}")
                            break
                    elif method == 'Network.requestWillBeSent':
                        request = params.get('request', {})
                        url = request.get('url', '')
                        if url.lower().endswith('.pdf'):
                            pdf_url = url
                            self._event("ok", f"Request for PDF detected: {url}")
                            break
                except Exception:
                    continue
            if pdf_url:
                break
            time.sleep(0.5)
        if pdf_url:
            print(f"Captured PDF URL: {pdf_url}")
            self._event("ok", "Captured PDF URL from logs")
        else:
            print("No PDF URL captured from network logs")
            self._event("warn", "No PDF URL seen in logs")
        return pdf_url

    def detect_new_tab_url(self, timeout=10):
        try:
            original_handles = set(self.driver.window_handles)
            end = time.time() + timeout
            while time.time() < end:
                handles = set(self.driver.window_handles)
                new_handles = list(handles - original_handles)
                if new_handles:
                    h = new_handles[0]
                    self._event("info", f"New tab detected: {h}")
                    try:
                        self.driver.switch_to.window(h)
                        url = self.driver.current_url
                        self._event("ok", f"New tab URL: {url}")
                        orig = list(original_handles)[0]
                        self.driver.switch_to.window(orig)
                        return url
                    except Exception as e:
                        self._event("warn", f"Failed to read new tab URL: {e}")
                        return None
                time.sleep(0.1)
        except Exception as e:
            self._event("warn", f"detect_new_tab_url error: {e}")
        return None

    def download_via_requests(self, url):
        if not url:
            return False
        self._event("info", f"Try direct download via requests: {url}")
        try:
            sess = requests.Session()
            for c in self.driver.get_cookies():
                cookie_kwargs = dict(
                    name=c.get('name'), value=c.get('value'),
                    domain=c.get('domain'), path=c.get('path', '/'),
                )
                if c.get('expiry'):
                    cookie_kwargs['expires'] = c['expiry']
                sess.cookies.set(**cookie_kwargs)

            resp = sess.get(url, stream=True, timeout=self.REQUESTS_TIMEOUT)
            ct = resp.headers.get('Content-Type', '')
            cd = resp.headers.get('Content-Disposition', '')
            if resp.status_code != 200:
                self._event("warn", f"requests GET status={resp.status_code}, ct={ct}")
                return False
            if 'pdf' not in ct.lower() and not url.lower().endswith('.pdf'):
                self._event("warn", f"Not a PDF content-type: {ct}")
            filename = None
            if 'filename=' in cd:
                filename = cd.split('filename=')[-1].strip('"; ')
            if not filename:
                filename = os.path.basename(url.split('?')[0]) or f"download_{int(time.time())}.pdf"
            out_path = os.path.join(self.download_dir, filename)
            with open(out_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            self._event("ok", f"Saved via requests: {out_path}")
            print(f"Saved via requests: {out_path}")
            return True
        except Exception as e:
            self._event("warn", f"requests download failed: {e}")
            return False
    
    def wait_for_download(self, timeout=120):
        print("Waiting for download to complete...")
        self._event("info", f"Wait for file in {os.path.abspath(self.download_dir)} (timeout={timeout}s)")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            items = os.listdir(self.download_dir)
            in_progress = [f for f in items if f.endswith('.crdownload')]
            if in_progress:
                self._event("info", f"Browser downloading: {in_progress}")
            pdf_files = [f for f in items if f.endswith('.pdf')]
            if pdf_files:
                print(f"Download completed: {pdf_files}")
                self._event("ok", f"File present: {pdf_files}")
                return True
            time.sleep(2)
        
        print("Download timeout")
        self._event("error", "Timeout waiting for .pdf in download dir")
        return False

    def _event(self, level, message):
        ts = time.strftime('%H:%M:%S')
        self.events.append((ts, level, message))

    def _print_summary(self):
        print("\n===== Download Summary =====")
        for ts, level, msg in self.events:
            tag = {
                'info': '[INFO]',
                'ok': '[ OK ]',
                'warn': '[WARN]',
                'error': '[FAIL]'
            }.get(level, '[INFO]')
            print(f"{ts} {tag} {msg}")
    
    def download_zoning_code(self):
        try:
            self.setup_driver()
            self.navigate_to_page()
            
            if self.find_download_button():
                pdf_url = None
                try:
                    tab_url = self.detect_new_tab_url()
                    if tab_url:
                        pdf_url = tab_url
                except Exception:
                    pass
                try:
                    if not pdf_url:
                        pdf_url = self.capture_pdf_url()
                except Exception:
                    pass

                success = self.wait_for_download()
                if not success and pdf_url:
                    self._event("info", "Browser file not found yet; try direct requests download")
                    success = self.download_via_requests(pdf_url)
                if not success:
                    success = self.wait_for_download()
                if success:
                    print("Download completed successfully.")
                    self._event("ok", "Download finished: success")
                    self._print_summary()
                    return True
                else:
                    print("Download failed or timeout")
                    self._event("error", "Download failed or timeout")
                    self._print_summary()
                    return False
            else:
                print("Unable to find download button")
                self._event("error", "No clickable download button found")
                self._print_summary()
                return False
                
        except Exception as e:
            print(f"Error during download: {str(e)}")
            self._event("error", f"Exception: {e}")
            self._print_summary()
            return False
        finally:
            if self.driver:
                self.driver.quit()

def main():
    print("Sarasota Zoning Code Auto Downloader")
    print("=" * 50)
    
    downloader = SarasotaZoningDownloader()
    success = downloader.download_zoning_code()
    
    if success:
        print("\nDownload completed. Please check the downloads folder.")
    else:
        print("\nDownload failed. Please check the network connection and retry.")
    pause_for_exit()

if __name__ == "__main__":
    main()

def pause_for_exit():
    try:
        import msvcrt
        print("\nPress any key to exit...")
        try:
            msvcrt.getch()
        except Exception:
            pass
    except Exception:
        try:
            input("\nPress Enter to exit...")
        except Exception:
            pass