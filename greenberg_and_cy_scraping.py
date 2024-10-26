import os
import asyncio
from playwright.async_api import async_playwright
import re
import time
from utils import export_to_excell, send_email
from dotenv import load_dotenv


async def intercept_and_filter_requests(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        results = []

        # Intercepter les requêtes réseau
        async def log_request(request):
            low_url = request.url.lower()  # Convertir l'URL en minuscules pour éviter les problèmes de casse
            if "buildout.com" in low_url and low_url.endswith("inventory"):
                results.append(request.url)

        page.on("request", log_request)
        # Accéder à l'URL
        await page.goto(url)
        # Attendre quelques secondes pour que toutes les requêtes soient faites
        await asyncio.sleep(5)
        # Fermer le navigateur
        await browser.close()
        return results


async def scrape_greenberg(url):
    async with async_playwright() as p:
        log_msg = ""
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # Accéder à l'URL cible
        await page.goto(url)
        # Attendre la fin des appels réseaux
        await page.wait_for_load_state("networkidle")
        # attendre que la div.js-listing-container monte dans le DOM
        await page.wait_for_selector('div.js-listing-container')

        # PAGINATION :Récupérer le nombre total de pages
        pagination_buttons = await page.query_selector_all('div.js-paginate-btn')
        total_pages = len(pagination_buttons)
        log_msg = log_msg + f"this scraping has : {total_pages} pages\n"
        print(f"Nombre total de pages : {total_pages}")

        data_deals = []
        # Boucle sur chaque page pour récupérer les deals
        for current_page in range(total_pages):
            print(f"Scraping page {current_page + 1}")
            log_msg = log_msg + f"Scraping page {current_page + 1}\n"

            # Si ce n'est pas la première page, cliquer sur le bouton de pagination
            if current_page > 0:
                # Cliquer sur le bouton de pagination correspondant à la page
                next_page_button = await page.query_selector(f'div.js-paginate-btn[data-page="{current_page}"]')
                # Vérifier et supprimer l'élément obstructif s'il existe
                await page.evaluate("""
                    const element = document.querySelector('div.cover.collapse');
                    if (element) {
                        element.remove();
                    }
                """)

                await next_page_button.click()

                # Attendre que le contenu de la page se charge
                await page.wait_for_load_state("networkidle")
                time.sleep(3)

            # Extraire les deals de la page actuelle
            deals = await page.query_selector_all('div.js-listing-container div.col-md-6.col-12.mb-3')
            print(f"nb de deals totaux de la page {current_page + 1} : ", len(deals))
            log_msg = log_msg + f"nb de deals totaux sur la page {current_page + 1} : {len(deals)}\n"

            # Extraire les deals "For Sale"
            sale_deals = []

            for deal in deals:
                deal_type_element = await deal.query_selector('div.list-item-banner.overlay')
                if deal_type_element:
                    deal_type = (await deal_type_element.inner_text()).lower()
                    if "for sale" in deal_type:
                        sale_deals.append(deal)
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
                        # print(data_deal)

            print(f"nb de deals à vendre de la page {current_page + 1}: ", len(sale_deals))
            log_msg = log_msg + f"nb de deals à vendre sur la page {current_page + 1} : {len(sale_deals)}\n"
        # Fermer le navigateur
        await browser.close()
        return data_deals, log_msg


if __name__ == "__main__":
    start_time = time.time()
    load_dotenv()
    url_site = "https://www.greenbergcompany.com/inventory"
    broker_firm = "GreenbergCompany"

    intercepted_urls = asyncio.run(intercept_and_filter_requests(url_site))
    # on garde la première filtrée
    url2scrap = intercepted_urls[0]
    # on lance le scraping
    result_list, log = asyncio.run(scrape_greenberg(url2scrap))
    nb_properties = len(result_list)
    filename, file_path, current_date = export_to_excell(result_list, broker_firm)
    end_time = time.time()
    duration = (end_time - start_time)
    print("durée totale en secondes: ", int(duration), "pour: ", nb_properties, ", à vendre")
    body = f"Le scraping du broker {broker_firm} au {current_date}, \nconcerne {nb_properties} terrains ou bâtiments à vendre.\nMerci de les consulter en fichier joint\n"
    body = body + log
    subject = f"[{broker_firm} Excel en pièce jointe]"
    # print("debug: ", subject, "; ", file_path)
    send_email(subject, body, file_path)
