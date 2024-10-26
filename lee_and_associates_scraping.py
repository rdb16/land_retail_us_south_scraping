import os
import asyncio
from playwright.async_api import async_playwright
import re
import time
from utils import export_to_excell, send_email
from utils_playwright import filter_requests
from dotenv import load_dotenv


async def scrap_lee(url):
    async with async_playwright() as p:
        log_msg = ""
        page_number = 1
        has_page_next = True
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Accéder à l'URL cible
        await page.goto(url)

        # Récupérer et afficher le nb de deals avant sélecteur
        await page.wait_for_load_state('networkidle')
        time.sleep(3)
        total_before = await page.inner_text('span.js-total-container')
        msg = f"NB de deals avant sélecteur : {total_before}\n"
        print(msg)
        log_msg += msg

        # on trie sur les ventes
        await page.select_option('select#q_sale_or_lease_eq', 'sale')
        await page.wait_for_load_state('networkidle')  # Attendre que toutes les requêtes se terminent
        time.sleep(3)
        # Récupérer et afficher le texte du span après la sélection
        total_after_sale = await page.inner_text('span.js-total-container')
        msg = f"NB de deals après sélecteur pour les ventes : {total_after_sale}\n"
        print(msg)
        log_msg += msg

        # TRI : Sélectionner les options "Development", "Land" et "Retail" dans le multi-select
        await page.select_option('select#q_type_use_offset_eq_any', ['1005', '5', '2'])
        await page.wait_for_load_state('networkidle')  # Attendre que les requêtes réseau se terminent
        time.sleep(3)
        # Récupérer et afficher le texte du span après la sélection
        total_after_types = await page.inner_text('span.js-total-container')
        msg = f"Nb de deals après sélection du type : {total_after_types}\n"
        print(msg)
        log_msg += msg

        # Extraire les éléments sous div.filter-content
        await page.wait_for_selector('span.js-next.mx-2.clickable.border-bottom')
        print("span next trouvé")
        # Lancer la boucle qui scrape la page et clique next
        match = re.search(r'(\d+)', total_after_types)
        if match:
            max_deals = int(match.group(1))
        else:
            print("ERREUR dans le nb de deal")
            exit(1)

        scraped = 0
        data_deals = []
        while has_page_next:
            # scraper ici
            pagination = await page.inner_text('span.js-pagination-container')
            msg = f"scrap des deals de  {pagination}\n"
            print(msg)
            log_msg += msg

            # on scrape la page
            deals_info_list = await page.query_selector_all(
                'div.col-xs-6.col-sm-6.col-lg-4.col-xl-3.grid-index-card')
            time.sleep(2)
            # print("il y a ", len(deals_info_list), "deals dans ce passage")
            nb_element = await page.query_selector('span.js-pagination-container')
            nb_element_text = await nb_element.inner_text()
            print(f"Dans la page {page_number}, la plage vaut {nb_element_text}")

            for deal in deals_info_list:
                flyer_element = await deal.query_selector('a')
                flyer_url = await flyer_element.get_attribute('href') if flyer_element else None
                name_element = await deal.query_selector('h5.mb-0.text-truncate')
                name = await name_element.inner_text() if name_element else None
                address_element = await deal.query_selector('div.p-2-5 div.text-truncate')
                address = await address_element.inner_text() if address_element else None
                # Récupérer les détails (les couples clé/valeur dans le tableau <tr>)
                details = {}
                detail_rows = await deal.query_selector_all('div.p-2-5 table tbody tr')
                for row in detail_rows:
                    key_element = await row.query_selector('td:nth-child(1)')
                    value_element = await row.query_selector('td:nth-child(2)')
                    key = await key_element.inner_text() if key_element else None
                    value = await value_element.inner_text() if value_element else None
                    if key and value:
                        details[key] = value
                data_deal = {
                    "name": name,
                    "address": address,
                    "flyer_url": flyer_url,
                    "details": details,
                    "broker_name": "see flyer",
                    "broker_email": "see flyer",
                    "broker_tel": "see flyer"
                }
                data_deals.append(data_deal)
                scraped += 1
                print(f"scraped {scraped} deals")
                # print(data_deal)
            # end for
            if scraped >= int(max_deals):
                has_page_next = False
                print("Max atteint, on sort")
                break

            # Vérifier si le texte dans la balise span commence par "Next"
            next_button_element = await page.query_selector('span.js-next.mx-2.clickable.border-bottom')
            next_button_text = await next_button_element.inner_text()

            if next_button_text.startswith("Next"):
                # Si c'est le cas, cliquer sur le bouton
                await next_button_element.click()
                # Attendre que la page suivante se charge
                await page.wait_for_load_state('networkidle')
                time.sleep(2)

                print("Next page loaded.")
                page_number += 1
            else:
                # Si le texte ne commence pas par "Next", on arrête le scraping
                print("Dernière page atteinte ou le bouton 'Next' n'est pas trouvé. Scraping terminé.")
                has_page_next = False

        # Fermer le navigateur
        print("Nb de pages: {}".format(page_number))
        await browser.close()
        return data_deals, log_msg


if __name__ == "__main__":
    start_time = time.time()
    load_dotenv()
    broker_firm = "Lee and Associates"
    # Exécuter le script asynchrone
    url_site = "https://www.lee-associates.com/properties/"
    filters = ["buildout.com", "inventory"]
    returned = asyncio.run(filter_requests(url_site, filters))
    print(returned[0])
    result_list, log = asyncio.run(scrap_lee(returned[0]))

    nb_properties = len(result_list)
    filename, file_path, current_date = export_to_excell(result_list, broker_firm)
    end_time = time.time()
    duration = (end_time - start_time)
    print("durée totale en secondes: ", int(duration), "pour: ", nb_properties, ", lots à vendre")
    body = f"Le scraping du broker {broker_firm} au {current_date}, \nconcerne {nb_properties} terrains ou bâtiments à vendre.\nMerci de les consulter en fichier joint\n"
    body = body + log
    subject = f"[{broker_firm} Excel en pièce jointe]"
    # print("debug: ", subject, "; ", file_path)
    send_email(subject, body, file_path)
