import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import h5py
import schedule
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
import urllib3
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configurations
csv_file = "websites.csv"  # csv file with website urls
hdf5_file = "scraped_data.h5"  # file for saving the results

# Step 1: Setup websites
def load_websites():
    """
    Lädt die URLs aus der CSV-Datei.
    """
    return pd.read_csv(csv_file)

# Step 2: Web Scraping-Funktion
def scrape_website(url, parser_func):
    """
    Ruft die Inhalte einer Webseite ab und parst die relevanten Daten.
    Args:
        url (str): URL der Webseite.
        parser_func (function): Parser-Funktion, die BeautifulSoup verwendet.
    Returns:
        dict: Ein Dictionary mit den extrahierten Daten.
    """
    try:
        if parser_func == parse_yahoo_finance:
            return parser_func(url)  # Selenium für Yahoo Finance
        else:
            response = requests.get(url, verify=False)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            return parser_func(soup)  # BeautifulSoup für andere Parser
    except Exception as e:
        print(f"Fehler beim Scraping von {url}: {e}")
        return None

# Beispiel-Parser für Yahoo Finance
#def parse_yahoo_finance(soup):
    """
    Extracts the stock price for AAPL from Yahoo Finance.
    """
    try:
        price_element = soup.find("span", {"data-testid":"qsp-price",
                                  "class":"base    yf-ipw1h0"})
        if price_element:
            stock_price = price_element.text.strip()
            return {"AAPL_stock_price": float(stock_price)}
        else:
            print("Preis-Element nicht gefunden.")
            return {}
    except Exception as e:
        print(f"Error parsing Yahoo Finance: {e}")
        return {}
    
def parse_yahoo_finance(url):
    
    options = Options()
    # Entferne "--headless" für Debugging
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    service = Service(r"C:\Users\49157\OneDrive\Desktop\Sadri\Driver\chromedriver.exe")  # Pfad zum ChromeDriver anpassen
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 120)

        # Cookie-Banner wegklicken
        try:
            cookie_button = wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//*[@id='consent-page']/div/div/div/form/div[2]/div[2]/button[1]")
            ))
            # Scroll zum Button, falls er nicht sichtbar ist
            driver.execute_script("arguments[0].scrollIntoView(true);", cookie_button)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='consent-page']/div/div/div/form/div[2]/div[2]/button[1]"))).click()
            print("Cookie-Banner erfolgreich weggeklickt.")
        except TimeoutException:
            print("Cookie-Banner wurde nicht rechtzeitig geladen.")
        except Exception as e:
            print(f"Fehler beim Wegklicken des Cookie-Banners: {e}")

        # Preiswert extrahieren
        try:
            price_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id='nimbus-app']/section/section/section/article/section[1]/div[2]/div[1]/section/div/section[1]/div[1]/div[1]/span")
            ))
            stock_price = price_element.text.strip()
            print(f"Gefundener Preis: {stock_price}")
            return {"AAPL_stock_price": float(stock_price.replace(",", ""))}  # Falls der Preis ein Komma enthält
        except TimeoutException:
            print("Preiswert wurde nicht rechtzeitig geladen.")
            driver.save_screenshot("debug_price_error.png")
            return {}
        except Exception as e:
            print(f"Fehler beim Extrahieren des Preises: {e}")
            driver.save_screenshot("debug_price_error.png")
            return {}
    except Exception as e:
        print(f"Allgemeiner Fehler mit Selenium: {e}")
        return {}
    finally:
        driver.quit()

# Beispiel-Parser für Weather.com
def parse_weather_com(soup):
    """
    Extrahiert Wetterdaten von Weather.com.
    """
    data = {}
    # Hier anpassen: Parser-Logik für spezifische Wetterdaten
    data['Temperature'] = soup.find("span", class_="CurrentConditions--tempValue--3KcTQ").text
    return data

# Beispiel-Parser für WHO Dashboard
def parse_who_dashboard(url):
    """
    Extrahiert Daten vom WHO-Dashboard mithilfe von Selenium.
    """
    data = {}
    
    # ChromeDriver-Optionen
    options = Options()
    #options.add_argument("--headless")  # Browser im Hintergrund starten
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    service = Service(r"C:\Pfad\zum\chromedriver.exe")  # Pfad zum ChromeDriver anpassen
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Lade die WHO-Dashboard-Seite
        driver.get(url)

        # Warte auf das Element mit den gewünschten Attributen
        wait = WebDriverWait(driver, 30)
        element = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//span[contains(@class, 'value') and @data-testid='dataDotViz-epiRollingFactoid-change']")
        ))
        
        # Extrahiere den Text des Elements
        data['Cases'] = element.text.strip()
    except TimeoutException:
        print("Timeout: Das Element wurde nicht rechtzeitig geladen.")
        data['Cases'] = None
    except NoSuchElementException:
        print("Das gewünschte Element konnte nicht gefunden werden.")
        data['Cases'] = None
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        data['Cases'] = None
    finally:
        # Beende den Browser
        driver.quit()

    return data

# Step 3: Speicherung in HDF5
def save_to_hdf5(data, hdf5_file):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with h5py.File(hdf5_file, "a") as f:
            for key, value in data.items():
                group = f.require_group(key)
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        group.create_dataset(f"{timestamp}_{sub_key}", data=float(sub_value))
                else:
                    group.create_dataset(timestamp, data=float(value))
        print(f"Daten erfolgreich in {hdf5_file} gespeichert.")
    except Exception as e:
        print(f"Fehler beim Speichern in die HDF5-Datei: {e}")

# Step 4: Tägliche Automatisierung
def daily_scrape():
    """
    Führt den täglichen Scraping-Prozess durch.
    """
    websites = load_websites()
    all_data = {}
    for _, row in websites.iterrows():
        url = row['url']
        parser_name = row['parser']
        if parser_name == "parse_yahoo_finance":
            data = scrape_website(url, parse_yahoo_finance)
        elif parser_name == "parse_weather_com":
            data = scrape_website(url, parse_weather_com)
        elif parser_name == "parse_who_dashboard":
            data = scrape_website(url, parse_who_dashboard)
        else:
            print(f"Unbekannter Parser: {parser_name}")
            continue
        
        if data:
            all_data[row['name']] = data
    
    save_to_hdf5(all_data, hdf5_file)
    print(f"Daten erfolgreich gespeichert um {datetime.now()}")

# Scheduler einrichten
schedule.every().day.at("08:00").do(daily_scrape)

# Endlos-Schleife für Automatisierung
if __name__ == "__main__":
    print("Automatisierter Scraper gestartet. Drücken Sie Strg+C zum Beenden.")
    end_time = datetime.now() + timedelta(minutes=2)  # 6 Minuten Laufzeit
    daily_scrape()
    while datetime.now() < end_time:
        schedule.run_pending()
        time.sleep(60)
    print("Automatisierter Scraper beendet.")



#if os.path.exists(hdf5_file):
    #print(f"Die Datei {hdf5_file} wurde erfolgreich erstellt.")
#else:
    #print(f"Die Datei {hdf5_file} wurde NICHT erstellt.")