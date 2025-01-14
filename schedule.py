from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import sqlite3
from time import sleep, strftime
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def scrape_flights():
    """Scrape flight data and save to SQLite database."""

    # Configuration de ChromeDriverManager et Selenium
    chrome_service = Service(ChromeDriverManager().install())
    chrome_options = Options()

    options_list = [
        "--headless",  # Mode sans interface graphique
        "--disable-gpu",  # Désactive l'accélération GPU
        "--window-size=1920,1200",  # Définit une taille de fenêtre
        "--ignore-certificate-errors",  # Ignore les erreurs SSL
        "--disable-extensions",  # Désactive les extensions
        "--no-sandbox",  # Nécessaire pour certains environnements Linux
        "--disable-dev-shm-usage",  # Utilise un espace partagé réduit
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    ]
    for option in options_list:
        chrome_options.add_argument(option)

    # Masquer Selenium
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        },
    )

    try:
        # URL de Kayak
        kayak = 'https://www.kayak.fr/flights/PAR-DXB/2025-03-02/2025-05-03?ucs=1fwu1ju&sort=bestflight_a&fs=airlines=-MULT,flylocal;stops=0'
        driver.get(kayak)
        sleep(5)
        print("Driver Title : ", driver.title)

        # Attendre les conteneurs de vols
        try:
            flight_containers = WebDriverWait(driver, 50).until(
                EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "nrc6-inner")]'))
            )
            print(f"{len(flight_containers)} conteneurs de vols trouvés.")
        except Exception as e:
            print(f"Erreur : les conteneurs de vols n'ont pas été chargés : {e}")
            return

        # Fonction de scraping
        def page_scrape():
            """Scrape flight information correctly with association between flights, durations, stops, cities, and airlines."""
            out_durations, return_durations = [], []
            out_times, return_times = [], []
            out_stops, return_stops = [], []
            out_airlines, prices = [], []

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

                    airlines = container.find_elements(By.XPATH, './/div[@class="J0g6-labels-grp"]/div[@class="J0g6-operator-text"]')
                    airline_text = airlines[0].text if airlines else None
                    out_airlines.append(airline_text)

                    price_element = container.find_element(By.XPATH, './/div[contains(@class, "f8F1-price-text")]')
                    prices.append(price_element.text.replace('€', '').strip())
                except Exception as e:
                    print(f"Error processing a container: {e}")

            flights_df = pd.DataFrame({
                'Out Duration': out_durations,
                'Return Duration': return_durations,
                'Out Time': out_times,
                'Return Time': return_times,
                'Out Stops': out_stops,
                'Out Airline': out_airlines,
                'Price': prices,
            })

            flights_df['Scraped Timestamp'] = strftime("%Y-%m-%d %H:%M:%S")
            return flights_df

        # Scraping et sauvegarde
        flights_df = page_scrape()
        if not flights_df.empty:
            conn = sqlite3.connect("flights_data.db")
            flights_df.to_sql("flights", conn, if_exists="append", index=False)
            conn.close()
            print("Data saved to SQLite.")
        else:
            print("No flights data scraped.")
    finally:
        driver.quit()


if __name__ == "__main__":
    scrape_flights()
    print("Done.")
