# Flights-Scraper

## Project Goal
The *Flights-Scraper* project aims to **automatically retrieve** flight information (schedules, durations, prices, emissions, etc.) from various sources (**Kayak** website, **Google Flights** API). The data collected via **Selenium** is stored in an SQLite database, then **merged** (by retrieving GitHub Actions artifacts) and **cleaned**, making it easier to analyze and export to CSV.  
The goal is to gradually build a **reliable** and **comprehensive** dataset over time for research, data science, or any other study related to air travel.

### Problem Statement
- Provide a search engine to **identify** and **predict** the cheapest flights for a given destination and a specific time period.  
- Predict **CO₂ emissions** associated with flights to raise awareness of the ecological impact of travel choices.  
- Predict **flight prices** to help users **save money**.

**Use Case**:  
- Scraping data for the **Paris (CDG) – Dubai (DXB)** route from **March 2, 2025** to **May 4, 2025 / May 5, 2025**, using **Kayak** and **Google Flights** as sources.

**Feasibility**:  
- Scraping tests with **Selenium** and **SerpAPI** confirmed the feasibility of retrieving relevant information such as flight duration, schedules, layovers, airlines, prices, and CO₂ emissions.  
- The collected data can be used for **predictive analytics** and **trend** visualization.

---

## Architecture


![image](https://github.com/user-attachments/assets/09ae1e84-c941-4036-b847-297ea32563ae)



This repository is organized to clearly separate:

1. **Jupyter notebooks** in the `WebScraping/` folder:  
   - **`Scraping_Selenium.ipynb`**: Manually creates and updates `flights_data.db` / `flights.csv`. The data is collected throughout the day by running the script repeatedly.  
     - The `schedule.py` script gathers the code from this notebook to **automate** Kayak scraping every hour via GitHub Actions.  
   - **`Scraping_API.ipynb`**: Generates `flights_emissions_data.csv`, containing data retrieved from Google Flights via the SerpAPI API.

2. **Python scripts** in the `scripts/` folder:  
   - **`download_merge.py`**: Merges the artifacts produced by GitHub Actions. Since each `schedule.py` run generates a new `merged_flights.db`/ `artifacts_flights_cleaned.csv` file.  
   - **`clean_sqlite_db.py`**: Cleans the database before converting it to CSV (removing empty rows, etc.).

3. **ML folder**: The ML folder contains machine learning models and scripts for predictive analysis based on the collected flight data.
   - **ML_CO2_Predictions.ipynb**: A Jupyter notebook focused on predicting CO₂ emissions for flights. It leverages features like flight duration, stopovers, and airline type to estimate emissions. The notebook includes feature importance analysis and model evaluation metrics.
   - **ML_Price_Detection.ipynb**: A Jupyter notebook aimed at predicting flight ticket prices. It uses attributes such as airline, duration, and time of scraping to forecast prices. The notebook compares different regression models (e.g., Random Forest, XGBoost) and evaluates their performance.

4. **GitHub Actions configuration** in `.github/workflows/`:  
   - Enables the automated execution of `schedule.py`.

![image](https://github.com/user-attachments/assets/2b6eef88-834f-4931-aa68-4de3f5913dfc)

5. **Streamlit App**: This Streamlit application uses **NLP (Natural Language Processing)** and **NER (Named Entity Recognition)** powered by **SpaCy** to extract travel-related information from free-text input (in French or English). Users can input a query like:
> "I want to leave from Paris to Dubai between 2025-03-01 and 2025-03-10 with a budget of $800."

The app analyzes this query to extract:
- Departure and destination cities,
- Departure and return dates,
- Budget.

<img width="284" alt="image" src="https://github.com/user-attachments/assets/7c2f54fb-dcb0-4518-bc87-f9a9bb3cceae" />

It then generates a dynamic URL for the Kayak website to directly search for corresponding flights.

---

## Automation
Thanks to **GitHub Actions**, the project can be **scheduled** to regularly fetch new flight data. The `schedule.py` script is executed at **defined intervals** (every hour or on manual trigger). The results are stored as **artifacts** in the repository’s **Actions** tab.  
This automation ensures a **continuous feed** of data with no human intervention, making it easy to keep the database regularly updated.
