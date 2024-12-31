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
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configurations
csv_file = "websites.csv"  # CSV file with website URLs
hdf5_file = "scraped_data.h5"  # File for saving the results

def load_websites():
    """
    Loads the URLs from the CSV file.
    """
    return pd.read_csv(csv_file)

def scrape_website(url, parser_func):
    """
    Fetches the contents of a webpage and parses the relevant data.
    Args:
        url (str): URL of the webpage.
        parser_func (function): Parsing function using Selenium.
    Returns:
        dict: A dictionary with the extracted data.
    """
    try:
        return parser_func(url)
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def parse_yahoo_finance(url):
    """
    Extracts the stock price for AAPL from Yahoo Finance using Selenium.
    """
    options = Options()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    service = Service(r"C:\Users\49157\OneDrive\Desktop\Sadri\Driver\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 120)

        # Dismiss cookie banner
        try:
            cookie_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='consent-page']/div/div/div/form/div[2]/div[2]/button[1]")))
            driver.execute_script("arguments[0].scrollIntoView(true);", cookie_button)
            cookie_button.click()
        except TimeoutException:
            print("Cookie banner did not load in time.")

        # Extract stock price
        try:
            price_element = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='nimbus-app']/section/section/section/article/section[1]/div[2]/div[1]/section/div/section[1]/div[1]/div[1]/span")))
            stock_price = price_element.text.strip()
            return {"AAPL_stock_price": float(stock_price.replace(",", ""))}
        except TimeoutException:
            print("Stock price did not load in time.")
            return {}
    finally:
        driver.quit()

def parse_weather_com(url):
    """
    Extracts weather data from Weather.com using Selenium.
    """
    options = Options()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    service = Service(r"C:\Users\49157\OneDrive\Desktop\Sadri\Driver\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 120)

        # Extract temperature
        try:
            temperature_element = wait.until(EC.presence_of_element_located((By.XPATH, "//span[@class='CurrentConditions--tempValue--3KcTQ']")))
            temperature = temperature_element.text.strip()
            return {"Temperature": temperature}
        except TimeoutException:
            print("Temperature element did not load in time.")
            return {}
    finally:
        driver.quit()

def parse_who_dashboard(url):
    """
    Extracts data from the WHO Dashboard using Selenium.
    """
    options = Options()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    service = Service(r"C:\Users\49157\OneDrive\Desktop\Sadri\Driver\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 120)

        # Extract cases
        try:
            cases_element = wait.until(EC.presence_of_element_located((By.XPATH, "//span[contains(@class, 'value') and @data-testid='dataDotViz-epiRollingFactoid-change']")))
            cases = cases_element.text.strip()
            return {"Cases": cases}
        except TimeoutException:
            print("Cases element did not load in time.")
            return {}
    finally:
        driver.quit()

def save_to_hdf5(data, hdf5_file):
    """
    Saves the data to an HDF5 file.
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with h5py.File(hdf5_file, "a") as f:
            for key, value in data.items():
                group = f.require_group(key)
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        group.create_dataset(f"{timestamp}_{sub_key}", data=float(sub_value) if sub_value else 0.0)
                else:
                    group.create_dataset(timestamp, data=float(value) if value else 0.0)
        print(f"Data successfully saved to {hdf5_file}.")
    except Exception as e:
        print(f"Error saving to HDF5 file: {e}")

def daily_scrape():
    """
    Executes the daily scraping process.
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
            print(f"Unknown parser: {parser_name}")
            continue

        if data:
            all_data[row['name']] = data

    save_to_hdf5(all_data, hdf5_file)
    print(f"Data successfully saved at {datetime.now()}")

schedule.every().day.at("08:00").do(daily_scrape)

if __name__ == "__main__":
    print("Automated scraper started. Press Ctrl+C to stop.")
    end_time = datetime.now() + timedelta(minutes=2)  # Adjust runtime
    daily_scrape()
    while datetime.now() < end_time:
        schedule.run_pending()
        time.sleep(60)
    print("Automated scraper stopped.")
