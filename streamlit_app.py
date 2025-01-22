import streamlit as st
import spacy
import re
from langdetect import detect

def extract_info(input_text):

    try:
        lang = detect(input_text)
    except Exception as e:
        return {"error": f"Erreur de détection de la langue : {e}"}

    if lang == "fr":
        nlp = spacy.load("fr_core_news_md")
        location_label = "LOC"  
    elif lang == "en":
        nlp = spacy.load("en_core_web_md")
        location_label = "GPE" 
    else:
        return {"error": "Langue non supportée (seulement français et anglais)."}

    # Analyse text with SpaCy
    doc = nlp(input_text)

    print(doc.ents)
    for ent in doc.ents:
        print(ent.text, ent.label_)

    extracted_info = {
        "Ville de départ": None,
        "Destination": None,
        "Date de départ": None,
        "Date de retour": None,
        "Budget": None,
    }

    # NER (Named Entity Recognition) with SpaCy
    for ent in doc.ents:
        if ent.label_ == location_label:  
            if not extracted_info["Ville de départ"]:
                extracted_info["Ville de départ"] = ent.text
            elif not extracted_info["Destination"]:
                extracted_info["Destination"] = ent.text
        elif ent.label_ == "MONEY":  
            budget_match = re.match(r"(\d+(?:[.,]\d+)?)", ent.text)
            if budget_match:
                extracted_info["Budget"] = budget_match.group(1)

    # Detection of dates with regex patterns
    date_pattern = r"\d{4}-\d{2}-\d{2}"
    date_matches = re.findall(date_pattern, input_text)
    if len(date_matches) >= 2:
        extracted_info["Date de départ"] = date_matches[0]
        extracted_info["Date de retour"] = date_matches[1]
    elif len(date_matches) == 1:
        extracted_info["Date de départ"] = date_matches[0]

    # if spacy not able to extract the budget, we try :
    if not extracted_info["Budget"]:
        budget_pattern = r"(\d+(?:[.,]\d+)?)\s*(€|\$|USD|EUR)"
        match_budget = re.search(budget_pattern, input_text)
        if match_budget:
            extracted_info["Budget"] = match_budget.group(1)  # group(1) is the first match

    return extracted_info



iata_codes = {
    "Paris": "PAR",
    "New York": "NYC",
    "London": "LON",
    "Tokyo": "TYO",
    "Dubai": "DXB",
    "Los Angeles": "LAX",
    "Sydney": "SYD",
    "Beijing": "BJS",
    "Shanghai": "SHA",
}

def generate_kayak_url(info):
    """Generate a dynamic Kayak URL based on extracted information."""
    base_url = "https://www.kayak.fr/flights/"
    departure_city = iata_codes.get(info.get("Ville de départ", ""), "").upper()
    print(departure_city)
    destination_city = iata_codes.get(info.get("Destination", ""), "").upper()
    print(destination_city)
    departure_date = info.get("Date de départ", "")
    return_date = info.get("Date de retour", "")

    if not departure_city or not destination_city or not departure_date:
        raise ValueError("Informations de voyage insuffisantes pour générer l'URL.")

    url = f"{base_url}{departure_city}-{destination_city}/{departure_date}/{return_date}?sort=bestflight_a"
    return url


# Interface Streamlit
st.title("🔍 Générateur d'URL Kayak avec NLP ✈️")

input_text = st.text_area(
    "Entrez votre requête de voyage (en français ou en anglais) :", 
    "Je veux partir de Paris à Dubai entre le 2025-03-01 et le 2025-03-10 avec un budget de 800€."
)

if st.button("Analyser et Générer l'URL"):

    extracted_info = extract_info(input_text)
    st.subheader("Informations extraites")
    st.write(extracted_info)

    url = generate_kayak_url(extracted_info)
    st.subheader("URL générée")
    if "http" in url:
        st.markdown(f"[Cliquez ici pour voir les vols sur Kayak]({url})")
    else:
        st.error(url)
