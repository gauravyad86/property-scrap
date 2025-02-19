import time
import json
import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from app.utils.chrome_driver import get_chrome_driver

def generate_housing_url(city, locality, page=1):
    city_encoded = quote(city.replace(" ", "_").lower())
    locality_encoded = quote(locality.replace(" ", "_").lower())
    url = f"https://housing.com/in/buy/{city_encoded}/{locality_encoded}"
    if page > 1:
        url += f"?page={page}"
    return url

def extract_lat_lon_second_image(url):
    response = requests.get(url)
    if response.status_code != 200:
        return None, None, None
    soup = BeautifulSoup(response.text, 'html.parser')
    json_script = soup.find("script", {"type": "application/ld+json"})
    latitude = longitude = None
    if json_script:
        try:
            json_data = json.loads(json_script.string)
            if isinstance(json_data, list):
                for item in json_data:
                    if "@type" in item and "geo" in item:
                        latitude = item["geo"].get("latitude")
                        longitude = item["geo"].get("longitude")
                        break
            elif isinstance(json_data, dict):
                if "geo" in json_data:
                    latitude = json_data["geo"].get("latitude")
                    longitude = json_data["geo"].get("longitude")
        except Exception:
            pass
    second_image = None
    gallery_section = soup.find("div", {"data-q": "gallery"})
    if gallery_section:
        all_images = gallery_section.find_all("img", src=True)
        if len(all_images) > 1:
            second_image = all_images[1]["src"]
            if second_image.startswith("//"):
                second_image = "https:" + second_image
    return latitude, longitude, second_image

def scrape_housing(city: str, locality: str, page: int = 1):
    desired_count = page * 250
    properties = []
    current_site_page = 1
    while len(properties) < desired_count:
        url = generate_housing_url(city, locality, current_site_page)
        driver = get_chrome_driver()
        driver.get(url)
        SCROLL_PAUSE_TIME = 2
        for _ in range(10):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
        driver.execute_script("""
            let images = document.querySelectorAll('img');
            images.forEach(img => {
                if (img.getAttribute('data-src')) {
                    img.setAttribute('src', img.getAttribute('data-src'));
                }
            });
        """)
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        page_properties = []
        for card in soup.find_all('article', {'data-testid': 'card-container'}):
            if len(page_properties) >= desired_count:
                break
            name_tag = card.find('h2', class_='T_4d93cd45')
            name = name_tag.text if name_tag else None
            emi_tag = card.find('span', class_='_9jtlke')
            emi = emi_tag.text if emi_tag else None
            price_tag = card.find('div', {'data-testid': 'priceid'})
            price = price_tag.text if price_tag else None
            link_tag = card.find('a', {'data-q': 'title'}, href=True)
            link = link_tag['href'] if link_tag else None
            full_link = f"https://housing.com{link}" if link else None
            latitude, longitude, image_url = extract_lat_lon_second_image(full_link) if full_link else (None, None, None)
            if name and full_link:
                property_details = {
                    "city": city,
                    "locality": locality,
                    "name": name,
                    "address": None,
                    "link": full_link,
                    "price": price,
                    "perSqftPrice": None,
                    "emi": emi,
                    "builtUp": None,
                    "facing": None,
                    "apartmentType": None,
                    "bathrooms": None,
                    "parking": None,
                    "image": [image_url] if image_url else None,
                    "latitude": latitude,
                    "longitude": longitude,
                    "possessionStatus": None,
                    "possessionDate": None,
                    "agentName": None,
                    "description": None,
                    "source": "housing"
                }
                page_properties.append(property_details)
        driver.quit()
        if not page_properties:
            break
        properties.extend(page_properties)
        current_site_page += 1
    start = (page - 1) * 250
    end = page * 250
    return properties[start:end]
