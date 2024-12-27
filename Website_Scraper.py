import matplotlib.pyplot as plt
import pandas as pd
import h5py
import schedule
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# configurations
csv_file = "websites.csv"  # csv file with website urls
hdf5_file = "scraped_data.h5"  # file for saving the results

# setup websites
def load_websites():
    """
    loads the urls saved in the csv file
    """
    return pd.read_csv(csv_file)

# webscraping function
def scrape_website(url, parser_func):
    """
    Fetches the content of a webpage and parses the relevant data.
    Args:
        url (str): URL of the webpage.
        parser_func (function): Parser function that Selenium.
    Returns:
        dict: A dictionary containing the extracted data.
    """

    try:
        return parser_func(url)
    except Exception as e:
        print(f"Fehler beim Scraping von {url}: {e}")
        return None

def create_selenium_driver():
    options = Options()
    options.add_argument("--headless") # browser is executed in the background
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    service = Service(r"C:\Users\49157\OneDrive\Desktop\Sadri\Driver\chromedriver.exe")
    return webdriver.Chrome(service=service, options=options)
# Yahoo Finance parser
def parse_yahoo_finance(url):

    driver = create_selenium_driver()

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 30)

        # click cookie banner
        try:
            cookie_button = wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//*[@id='consent-page']/div/div/div/form/div[2]/div[2]/button[1]")
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", cookie_button)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='consent-page']/div/div/div/form/div[2]/div[2]/button[1]"))).click()
            print("Cookie-Banner erfolgreich weggeklickt.")
        except TimeoutException:
            print("Cookie-Banner wurde nicht rechtzeitig geladen.")
        except Exception as e:
            print(f"Fehler beim Wegklicken des Cookie-Banners: {e}")

        # extract closed price value from the day before
        try:
            price_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[2]/main/section/section/section/article/div[2]/ul/li[1]/span[2]/fin-streamer")
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

# weather.com parser
def parse_weather_com(url):
    """
    Extracts weather data from weather.com with the help of selenium
    """
    driver = create_selenium_driver()
 
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 30)

        # extract temperature
        try:
            temp_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/div[1]/main/div[2]/main/div[1]/div/section/div/div/div[2]/div[1]/div[1]/span")
            ))
            temperature = temp_element.text.strip()
            print(f"Gefundene Temperatur: {temperature}")
            return {"Temperature": temperature}
        except TimeoutException:
            print("Temperaturwert wurde nicht rechtzeitig geladen.")
            driver.save_screenshot("debug_temp_error.png")
            return {}
        except Exception as e:
            print(f"Fehler beim Extrahieren der Temperatur: {e}")
            driver.save_screenshot("debug_temp_error.png")
            return {}
    finally:
        driver.quit()

# WHO dashboard parser
def parse_who_dashboard(url):
    """
    Extracts data from the WHO dashboard with the help of selenium
    """
    driver = create_selenium_driver()

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 30)

        # extract data of total number of covid-19 cases worldwide
        try:
            element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "/html/body/main/section/div[3]/div[1]/div/div[1]/div/div[2]/div[2]/div[1]/div/div[4]/div/p[1]/strong")
            ))
            cases = element.text.strip()
            print(f"Gefundene Fälle: {cases}")
            return {"Cases": cases}
        except TimeoutException:
            print("Datenwert wurde nicht rechtzeitig geladen.")
            driver.save_screenshot("debug_cases_error.png")
            return {}
        except Exception as e:
            print(f"Fehler beim Extrahieren der Daten: {e}")
            driver.save_screenshot("debug_cases_error.png")
            return {}
    finally:
        driver.quit()

# data is saved in the hdf5 file "scraped_data.h5"
def save_to_hdf5(data, hdf5_file):
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with h5py.File(hdf5_file, "a") as f:
            for key, value in data.items():
                group = f.require_group(key)
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        group.create_dataset(f"{timestamp}_{sub_key}", data=str(sub_value))
                else:
                    group.create_dataset(timestamp, data=str(value))
        print(f"Daten erfolgreich in {hdf5_file} gespeichert.")
    except Exception as e:
        print(f"Fehler beim Speichern in die HDF5-Datei: {e}")

# daily automation
def daily_scrape():
    """
    Performs the daily scraping process
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

# setup schedule
schedule.every().day.at("08:00").do(daily_scrape)

# Visualization of the data collected in the hdf5 file

def visualize_data(hdf5_file, group_name):
    """
    Visualizes the temporal development of data from the HDF5 file.
    
    Args:
        hdf5_file (str): Path to the HDF5 file.
        group_name (str): Name of the group in the HDF5 file.
    """
    try:
        # Open the HDF5 file and read it
        with h5py.File(hdf5_file, "r") as h5_file:
            if group_name not in h5_file:
                print(f"Group '{group_name}' not found in the file.")
                return
            
            data = h5_file[group_name]
            timestamps = []
            values = []
            
            for key in data.keys():
                # Extract timestamp
                timestamps.append(pd.to_datetime(key.split('_')[0]))
                raw_value = data[key][()]  # Extract value
                
                # Decode bytes if necessary
                if isinstance(raw_value, bytes):
                    raw_value = raw_value.decode("utf-8")
                
                # Clean the value (remove °, commas, etc.)
                cleaned_value = raw_value.replace(",", "").replace("°", "").strip()
                
                try:
                    # Convert to float
                    values.append(float(cleaned_value))
                except ValueError:
                    print(f"Could not convert value to float: {cleaned_value}")
                    values.append(None)  # Append None for invalid values
            
            # Create a DataFrame
            df = pd.DataFrame({"Timestamp": timestamps, "Value": values})
            df = df.dropna()  # Remove rows with invalid values
            df = df.sort_values("Timestamp")
            
            if df.empty:
                print("No valid data to visualize.")
                print("DataFrame preview:")
                print(df)
                return
            
            # Plot the data
            plt.figure(figsize=(10, 6))
            plt.plot(df["Timestamp"], df["Value"], marker="o", linestyle="-", label=group_name)
            plt.title(f"Temporal Development of {group_name}")
            plt.xlabel("Time")
            plt.ylabel("Value")
            plt.grid(True)
            plt.legend()
            plt.tight_layout()
            plt.show()
    
    except Exception as e:
        print(f"Error in visualization: {e}")

# Loop for automation
if __name__ == "__main__":
    print("Automatisierter Scraper gestartet. Drücken Sie Strg+C zum Beenden.")
    end_time = datetime.now() + timedelta(minutes=2)  # runtime of the scraper // can be edited
    daily_scrape()
    while datetime.now() < end_time:
        schedule.run_pending()
        time.sleep(60)
    print("Automatisierter Scraper beendet.")
