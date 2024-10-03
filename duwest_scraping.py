import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
from utils import export_to_excell
from dotenv import load_dotenv


def scrape_properties():
    with sync_playwright() as p:
        # Lancement du navigateur
        browser = p.chromium.launch(headless=False)  # Set headless=True if you don't want the browser UI
        page = browser.new_page()

        # Accéder à la page des propriétés
        url = "https://duwestrealty.com/properties?post=0&forlease=0&forsale=1&padsitesale=1&padsitelease=0"
        page.goto(url)

        # Attendre que les éléments de la page se chargent
        page.wait_for_selector("a.property")

        # Cliquer sur chaque propriété et scraper les données
        property_links = page.query_selector_all("a.property")
        properties_data = []

        for link in property_links:
            # print(link)
            try:
                post_id = link.get_attribute("data-post-id")
                selector = f'a.property[data-post-id="{post_id}"]'
                print(f"Processing property with post-id: {post_id}")
                link = page.query_selector(selector)

                if link:
                    link.click(force=True)
                    time.sleep(2)
                    page.wait_for_selector(".embed-responsive-4by3")

                    html = page.content()
                    # Utiliser BeautifulSoup pour extraire les informations
                    soup = BeautifulSoup(html, 'html.parser')

                    # Extraire le titre, la description, l'adresse et l'email
                    title = soup.select_one('h2.border-none').get_text(strip=True) if soup.select_one(
                        'h2.border-none') else ''
                    address = soup.select_one('.content-container > p').get_text(strip=True) if soup.select_one(
                        '.content-container > p') else ''
                    # description = soup.select_one('.content-container div.col-12').get_text(
                    #     strip=True) if soup.select_one(
                    #     '.content-container div.col-12') else ''
                    descriptions = soup.select("div.col-12 > p") if soup.select("div.col-12 > p") else ''
                    list_desc = []
                    for description in descriptions:
                        if soup.select("div.col-12 > p.p1 > i"):
                            list_desc.append(description.get_text(strip=True))
                        else:
                            for paragraph in description:
                                list_desc.append(paragraph.get_text(strip=True))

                    email = soup.select_one('a[href*="mailto:"]').get_text(strip=True) if soup.select_one(
                        'a[href*="mailto:"]') else ''
                    tel = soup.select_one('a[href*="tel:"]').get_text(strip=True) if soup.select_one(
                        'a[href*="mailto:"]') else ''

                    # Ajouter les données dans une liste
                    properties_data.append({
                        'title': title,
                        'address': address,
                        'description': list_desc,
                        'contact-tel': tel,
                        'contact-email': email
                    })

                    # Fermer la page de détail en cliquant sur le bouton de fermeture
                    close_button = page.query_selector('button.close')
                    if close_button:
                        close_button.click(force=True)
                        time.sleep(1)  # Attendre un peu après la fermeture

            except Exception as e:
                print(f"Erreur lors du traitement d'une propriété: {e}")
                continue  # Passer à la propriété suivante si une erreur survient

        # Fermer le navigateur
        browser.close()

        # renvoyer les résultats
        return properties_data


if __name__ == "__main__":
    start_time = time.time()
    result_list = scrape_properties()
    nb_properties = len(result_list)
    filename, file_path, current_date = export_to_excell(result_list, "Land_retail_us_south_scraping")
    end_time = time.time()
    duration = (end_time - start_time)
    print("durée totale en secondes: ", int(duration), "pour: ", nb_properties )
    body = f"Le scraping du broker DuWest au {current_date}, \nconcerne {nb_properties} terrains ou bâtiments à vendre.\nMerci de les consulter en fichier joint"

    load_dotenv()

    sender_email = os.getenv("sender_email")
    sender_password = os.getenv("sender_password")
    recipient_email = os.getenv("recipient")
    subject = "[DuWest Excel en pièce jointe]"
    cc_email = os.getenv("cc_email")

    # send_email_with_attachment(sender_email, sender_password, recipient_email, subject, body, file_path, cc_email)



