import csv
import socket
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def read_hosts_from_csv(filename):
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        return [row[0] for row in reader if row]

def is_port_open(host, port, timeout=1):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, socket.error):
        return False
    
def detect_redirect(url):
    """
    Detects if a URL has a redirect (HTTP 301/302 or Meta Refresh).
    
    :param url: The URL to check for redirects.
    :return: True if a redirect is detected, False otherwise.
    """
    try:
        # Check HTTP status code for 301/302 redirects
        response = requests.get(url, timeout=5, allow_redirects=False)
        if response.status_code in [301, 302]:
            print(f"Redirect detected: {url} -> {response.headers.get('Location')}")
            return True  # Redirect detected
        
        # Check for Meta Refresh (client-side redirect)
        if 'refresh' in response.headers.get('Content-Type', ''):
            if 'meta' in response.text.lower() and 'refresh' in response.text.lower():
                print(f"Meta Refresh detected on {url}")
                return True  # Meta refresh detected
        
    except requests.RequestException as e:
        print(f"Error checking redirects for {url}: {e}")
    
    return False  # No redirect detected

def capture_screenshot(url, output_path):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280x1024')
    options.add_argument('--ignore-certificate-errors')  # Voorkom SSL-fouten
    options.add_argument('--allow-insecure-localhost')  # Accepteer onveilige certificaten
    options.add_argument('--ignore-ssl-errors=yes')
    options.add_argument("--disable-features=StrictOriginPolicy")
    options.add_argument('--disable-features=SecureDNS')
    options.add_argument('--disable-http2')
    options.add_argument('--disable-https')
    options.add_argument("--disable-cache")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        driver.get(url)
        time.sleep(2)  # Wacht even voor het volledig laden van de pagina
        final_url = driver.current_url
        url = url+"/"
        if detect_redirect(final_url):
            print(f"Redirect detected for {url}, skipping screenshot.")
            return True  # Indicate that a redirect was found
        driver.save_screenshot(output_path)
        print(f"Screenshot opgeslagen: {output_path}")
        return False
    except Exception as e:
        print(f"Fout bij het laden van {url}: {e}")
        return False
    finally:
        driver.quit()

def main(csv_file, scan_http, scan_https):
    hosts = read_hosts_from_csv(csv_file)
    for host in hosts:
        redirected = False
        host_https = host
        host_http = host
        
        if scan_https and is_port_open(host_https, 443):
            print(f"Poort 443 is open op {host_https}, maak een screenshot van HTTPS...")
            redirected = capture_screenshot(f'https://{host_https}', f'screenshots/{host_https}_https.png')
        elif scan_https == False:
            print(f"Poort 443 wordt overgeslagen op {host_https}")
        else:
            print(f"Poort 443 is gesloten op {host_https}")

        if not redirected == True and scan_http and is_port_open(host_http, 80):
            print(f"Poort 80 is open op {host_http}, maak een screenshot van HTTP...")
            capture_screenshot(f'http://{host_http}', f'screenshots/{host_http}_http.png')
        elif scan_http == False:
            print(f"Poort 80 wordt overgeslagen op {host_http}")
        else:
            print(f"Poort 80 is gesloten op {host_http}")

if __name__ == "__main__":
    main('hosts.csv', scan_http=True, scan_https=True)
