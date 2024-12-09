from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import sqlite3
from time import sleep, strftime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def scrape_flights():
    """Scrape flight data and save to SQLite database."""

    # Configure ChromeDriverManager et Selenium
    chrome_service = Service(ChromeDriverManager().install())

    chrome_options = Options()
    options = [
        "--headless",
        "--disable-gpu",
        "--window-size=1920,1200",
        "--ignore-certificate-errors",
        "--disable-extensions",
        "--no-sandbox",
        "--disable-dev-shm-usage"
    ]
    for option in options:
        chrome_options.add_argument(option)

    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    try:
        # URL de Kayak
        kayak = 'https://www.kayak.fr/flights/CDG-DXB/2025-03-02/2025-05-04?ucs=1yezklu&sort=bestflight_a'
        driver.get(kayak)
        sleep(3)
        print("Driver Title : ", driver.title)
        #print("Page Html : ", driver.page_source)

        # Gérer le popup
        try:
            reject_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[.//div[contains(text(), "Tout refuser")]]'))
            )
            reject_button.click()
        except Exception as e:
            print(f"Popup handling error: {e}")

        # Fonction de scraping
        def page_scrape():
            """Scrape flight information correctly with association between flights, durations, stops, cities, and airlines."""
            xp_flight_containers = '//div[contains(@class, "nrc6-inner")]'
            flight_containers = driver.find_elements(By.XPATH, xp_flight_containers)

            out_durations, return_durations = [], []
            out_times, return_times = [], []
            out_stops, return_stops = [], []
            out_stop_cities, return_stop_cities = [], []
            out_airlines, return_airlines = [], []
            prices = []

            for container in flight_containers:
                try:
                    durations = container.find_elements(By.XPATH, './/div[contains(@class, "xdW8-mod-full-airport")]/div[contains(@class, "vmXl-mod-variant-default")]')
                    out_durations.append(durations[0].text if len(durations) > 0 else None)
                    return_durations.append(durations[1].text if len(durations) > 1 else None)

                    times = container.find_elements(By.XPATH, './/div[contains(@class, "vmXl-mod-variant-large")]')
                    out_times.append(times[0].text if len(times) > 0 else None)
                    return_times.append(times[1].text if len(times) > 1 else None)

                    stops = container.find_elements(By.XPATH, './/div[contains(@class, "JWEO")]/div[contains(@class, "vmXl-mod-variant-default")]/span[contains(@class, "JWEO-stops-text")]')
                    out_stops.append(stops[0].text if len(stops) > 0 else "direct")
                    return_stops.append(stops[1].text if len(stops) > 1 else "direct")

                    stop_cities = container.find_elements(By.XPATH, './/div[contains(@class, "JWEO")]/div[contains(@class, "c_cgF-mod-variant-full-airport")]/span/span')
                    out_stop_cities.append(stop_cities[0].text if len(stop_cities) > 0 else None)
                    return_stop_cities.append(stop_cities[1].text if len(stop_cities) > 1 else None)

                    airlines = container.find_elements(By.XPATH, './/div[@class="J0g6-labels-grp"]/div[@class="J0g6-operator-text"]')
                    airline_text = airlines[0].text if airlines else None
                    if airline_text:
                        airline_split = airline_text.split(", ")
                        out_airlines.append(airline_split[0] if len(airline_split) > 0 else None)
                        return_airlines.append(airline_split[1] if len(airline_split) > 1 else airline_split[0])
                    else:
                        out_airlines.append(None)
                        return_airlines.append(None)

                    price_element = container.find_element(By.XPATH, './/div[contains(@class, "f8F1-price-text")]')
                    prices.append(price_element.text.replace('€', '').strip() if price_element else None)

                except Exception as e:
                    out_durations.append(None)
                    return_durations.append(None)
                    out_times.append(None)
                    return_times.append(None)
                    out_stops.append(None)
                    return_stops.append(None)
                    out_stop_cities.append(None)
                    return_stop_cities.append(None)
                    out_airlines.append(None)
                    return_airlines.append(None)
                    prices.append(None)
                    print(f"Error processing a container: {e}")

            flights_df = pd.DataFrame({
                'Out Duration': out_durations,
                'Return Duration': return_durations,
                'Out Time': out_times,
                'Return Time': return_times,
                'Out Stops': out_stops,
                'Return Stops': return_stops,
                'Out Stop Cities': out_stop_cities,
                'Return Stop Cities': return_stop_cities,
                'Out Airline': out_airlines,
                'Return Airline': return_airlines,
                'Price': prices,
            })

            flights_df['Scraped Timestamp'] = strftime("%Y-%m-%d %H:%M:%S")
            return flights_df

        # Scraping et sauvegarde
        flights_df = page_scrape()
        print("flights df : ",flights_df)
        #flights_df.to_csv("test.csv", index=False)
        conn = sqlite3.connect("flights_data.db")
        flights_df.to_sql("flights", conn, if_exists="append", index=False)
        conn.close()
        print("Data saved to SQLite.")
    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_flights()
    print("Done.")


