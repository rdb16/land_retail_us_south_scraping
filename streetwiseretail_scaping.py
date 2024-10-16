import base64
import json
import os
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
from utils import send_email_with_attachment, export_to_excell
from webdriver_manager.chrome import ChromeDriverManager


def parse_streetwise_retail(base_url):
    # Configure Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    data_deals = []

    page_source = None
    try:
        driver.get(base_url)
        time.sleep(5)
        page_source = driver.page_source
        # with open('streetwise_retail_sale.html', 'wb') as f:
        #     f.write(page_source.encode('utf-8'))

        # pattern = r"data-widget-config<\/span>=\"<span class=\"html-attribute-value\">(.+?)<\/span>"
        pattern = r"data-widget-config=\"(.+?)data-widget-initialized"

        matches = re.findall(pattern, page_source, re.DOTALL)
        print("nb de matchs : ", len(matches))
        # on a deux matchs et seu le second contient les datas
        data_match = matches[1]

        decoded_data = base64.b64decode(data_match).decode('utf-8')
        # Charger la chaîne JSON
        json_data = json.loads(decoded_data)
        # print(json_data)
        print("nb-properties ", len(json_data['propertyList']))

        # # debug on enregistre le json
        # with open('streetwise_retail.json', 'w') as outfile:
        #     json.dump(json_data, outfile)

        # on extrait les data pour chaque prop
        for prop in json_data.get("propertyList", []):
            if 'For Sale' not in prop['status']:
                continue

            if 'Commercial' in prop['categoryType']:
                continue

            name = prop.get("propertyName", "N/A")
            address = prop.get("address", "N/A")
            lat = prop.get("latitude", "N/A")
            lng = prop.get("longitude", "N/A")
            price = prop.get("price", "N/A")
            lot_size = prop.get("lotSize", "N/A")
            built_area = "See Details"
            zip_code = "See Address"
            property_type = prop.get("categoryType", "N/A")
            url = "https://streetwiseretail.com" + prop.get("page_item_url", "N/A")
            brochure = prop.get("pdfLink", "N/A")
            prop_data = {
                "name": name,
                "Address": address,
                "Zip Code": zip_code,
                "Detail URL ": url,
                "Brochure": brochure,
                "Price": price,
                "Lot Size": lot_size,
                "Built sqft": built_area,
                "Property Type": property_type,
                "Latitude": lat,
                "Longitude": lng
            }

            data_deals.append(prop_data)
            # print(prop_data)
    finally:
        driver.quit()
        return data_deals


if __name__ == "__main__":
    start_time = time.time()
    load_dotenv()
    site_url = "https://www.streetwiseretail.com/listings?ss360Query=sale"
    broker_firm = "Streetwise Retail"

    data = parse_streetwise_retail(site_url)

    nb_properties = len(data)
    filename, file_path, current_date = export_to_excell(data, broker_firm)
    end_time = time.time()
    duration = (end_time - start_time)
    print("durée totale en secondes: ", int(duration), "pour: ", nb_properties)
    body = f"Le scraping du broker {broker_firm} au {current_date}, \nconcerne {nb_properties} terrains ou bâtiments à vendre.\nMerci de les consulter en fichier joint"

    sender_email = os.getenv("sender_email")
    sender_password = os.getenv("sender_password")
    recipient_email = os.getenv("recipient")
    subject = f"[{broker_firm}: Excel en pièce jointe]"
    cc_email = os.getenv("cc_email")

    send_email_with_attachment(sender_email, sender_password, recipient_email, subject, body, file_path, cc_email)
