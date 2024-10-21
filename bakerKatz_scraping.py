import os
import asyncio
from playwright.async_api import async_playwright
import re
import time
from utils import export_to_excell, send_email
from dotenv import load_dotenv


async def scrape_bakerkatz(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Accéder à l'URL cible
        await page.goto("https://bakerkatz.com/properties/")

        # Attendre que le contenu soit chargé (tu peux ajuster en fonction des éléments spécifiques)
        await page.wait_for_load_state("networkidle")

        # Extraire les éléments sous div.filter-content
        filter_cols = await page.query_selector_all('div.filter-content div.filter-col')

        properties_list = []
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

        # Parcourir les cols
        for filter_col in filter_cols:
            # Extraire le texte du <h6>
            h6_element = await filter_col.query_selector('h6')
            if h6_element:
                h6_text = await h6_element.inner_text()

                # Vérifier si "For Sale" est dans le texte
                if "For Sale" in h6_text:
                    # Extraire les informations demandées
                    # "name" dans div.content-info h5
                    name_element = await filter_col.query_selector('div.content-info h5')
                    name = await name_element.inner_text() if name_element else 'N/A'

                    # "address" dans div.detail-content h2
                    address_element = await filter_col.query_selector('div.detail-content h2')
                    address = await address_element.inner_text() if address_element else 'N/A'

                    # "town" dans div.detail-content p
                    town_element = await filter_col.query_selector('div.detail-content p')
                    town = await town_element.inner_text() if town_element else 'N/A'

                    # "flyer_url" dans div.btn_wrap a
                    flyer_element = await filter_col.query_selector('div.btn_wrap a')
                    flyer_url = await flyer_element.get_attribute('href') if flyer_element else 'N/A'

                    # "details" dans div.bottom-content ul > li
                    details = []
                    detail_elements = await filter_col.query_selector_all('div.bottom-content ul li')
                    for detail_element in detail_elements:
                        details.append(await detail_element.inner_text())

                    # "broker_name" dans div.img_content h6
                    broker_name_element = await filter_col.query_selector('div.img_content h6')
                    broker_name = await broker_name_element.inner_text() if broker_name_element else 'N/A'

                    broker_email = "N/A"
                    broker_tel = "N/A"
                    contact_links = await filter_col.query_selector_all('div.img_content a[href]')
                    for link in contact_links:
                        href_value = await link.get_attribute('href')
                        if href_value.startswith('mailto:'):
                            contact_value = href_value.replace("mailto:", "")
                            print(contact_value)
                            if re.match(email_regex, contact_value):
                                broker_email = contact_value
                            else:
                                broker_tel = contact_value

                    # Ajouter les données extraites à un dictionnaire
                    property_data = {
                        "name": name,
                        "address": address,
                        "town": town,
                        "flyer_url": flyer_url,
                        "details": details,
                        "broker_name": broker_name,
                        "broker_email": broker_email,
                        "broker_tel": broker_tel
                    }

                    # Ajouter le dictionnaire à la liste des propriétés
                    properties_list.append(property_data)
                    # print(property_data)

        # Fermer le navigateur
        await browser.close()
        return properties_list


if __name__ == "__main__":
    start_time = time.time()
    load_dotenv()
    url_site = "https://bakerkatz.com/properties/"
    broker_firm = "BakerKatz"

    result_list = asyncio.run(scrape_bakerkatz(url_site))
    nb_properties = len(result_list)
    filename, file_path, current_date = export_to_excell(result_list, broker_firm,)
    end_time = time.time()
    duration = (end_time - start_time)
    print("durée totale en secondes: ", int(duration), "pour: ", nb_properties)
    body = f"Le scraping du broker Bakerkatz au {current_date}, \nconcerne {nb_properties} terrains ou bâtiments à vendre.\nMerci de les consulter en fichier joint"

    subject = "[Bakerkatz Excel en pièce jointe]"
    print("debug: ", subject,"; ", file_path )
    send_email(subject, body, file_path)
