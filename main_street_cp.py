import json
import os
import re

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from utils import send_email_with_attachment, export_to_excell


def parse_main_street(site, path_to_driver):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service(path_to_driver)  # Remplacez par le chemin de votre chromedriver
    driver = webdriver.Chrome(service=service, options=chrome_options)

    deals_data = []
    try:
        driver.get(site)
        time.sleep(5)
        html_content = driver.page_source

        # with open("tmp/html.html", "w") as fi:
        #     fi.write(html_content)

        soup = BeautifulSoup(html_content, "html.parser")
        # # on limite la regex à un subset pour accélérer
        # start_span = soup.find(id='line207')
        # end_span = soup.find(id='line208')
        # print(start_span.text)
        # print(end_span.text)
        #
        # html_subset = ''
        # if start_span and end_span:
        #     for element in start_span.find_all_next():
        #         if element == end_span:
        #             break
        #         html_subset += str(element)
        #

        pattern = r"\{\"id\"\:\"[1-9][0-9]{0,2}\",\"title\":.*?png\"\}\]\}"
        matches = re.findall(pattern, html_content, re.DOTALL)

        # Liste pour stocker les objets JSON analysés
        for match in matches:
            try:
                # formater le JSON pour être analysé
                json_data = json.loads(match)
                lat = json_data["location"]["lat"]
                lng = json_data["location"]["lng"]
                address = json_data["address"]
                price = "See Details"
                built_area = "See Details"
                zip_code = "See Details"
                property_type = "See Details"
                detail = json_data["location"]["extra_fields"]["brochure"]
                url = detail.replace("\\", "")

                deal_data = {
                    "Address": address,
                    "Zip_code": zip_code,
                    "Detail URL and contact page": url,
                    "Price": price,
                    "Built sqft or acres": built_area,
                    "Property Type": property_type,
                    "Latitude": lat,
                    "Longitude": lng
                }
                # print(deal_data)
                deals_data.append(deal_data)

            except json.JSONDecodeError as e:
                print(f"Erreur lors du parsing du JSON : {e}")
    finally:
        driver.quit()
        return deals_data


if __name__ == "__main__":
    start_time = time.time()
    load_dotenv()
    site_url = "https://mainstcp.com/our-properties/"

    data = parse_main_street(site_url, os.getenv('driver'))

    nb_properties = len(data)
    filename, file_path, current_date = export_to_excell(data, "Main_Street_CP")

    end_time = time.time()
    duration = (end_time - start_time)
    print("durée totale en secondes: ", int(duration), "pour: ", nb_properties)
    body = f"Le scraping du broker Main Street CP au {current_date}, \nconcerne {nb_properties} terrains ou bâtiments à vendre.\nMerci de les consulter en fichier joint"

    sender_email = os.getenv("sender_email")
    sender_password = os.getenv("sender_password")
    recipient_email = os.getenv("recipient")
    subject = "[Main Street CP Excel en pièce jointe]"
    cc_email = os.getenv("cc_email")

    send_email_with_attachment(sender_email, sender_password, recipient_email, subject, body, file_path, cc_email)
