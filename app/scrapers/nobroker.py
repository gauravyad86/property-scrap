import time
import json
import base64
import requests
import os
from urllib.parse import quote
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from app.utils.chrome_driver import get_chrome_driver

GOOGLE_API_KEY = GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def get_place_details(city, locality):
    search_query = f"{locality}, {city}"
    api_url = (
        "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        f"?input={quote(search_query)}&inputtype=textquery&fields=geometry,place_id&key={GOOGLE_API_KEY}"
    )
    response = requests.get(api_url)
    data = response.json()
    if data["status"] == "OK" and data.get("candidates"):
        candidate = data["candidates"][0]
        place_id = candidate.get("place_id")
        lat = candidate["geometry"]["location"]["lat"]
        lon = candidate["geometry"]["location"]["lng"]
        return place_id, lat, lon
    else:
        return None, None, None

def get_nobroker_url(city, locality):
    place_id, lat, lon = get_place_details(city, locality)
    if not place_id:
        return None
    search_param_data = [{
        "lat": lat,
        "lon": lon,
        "placeId": place_id,
        "placeName": locality.upper()
    }]
    encoded_search_param = base64.b64encode(json.dumps(search_param_data).encode()).decode()
    base_url = (
        f"https://www.nobroker.in/property/sale/{quote(city)}/{quote(locality)}"
        f"?searchParam={encoded_search_param}&radius=2.0&city={quote(city)}&locality={quote(locality)}"
    )
    return base_url

def extract_lat_lon_from_nobroker(property_url):
    response = requests.get(property_url)
    if response.status_code != 200:
        return None, None
    soup = BeautifulSoup(response.text, 'html.parser')
    geo_tag = soup.find("span", itemprop="geo")
    if geo_tag:
        latitude_meta = geo_tag.find("meta", itemprop="latitude")
        longitude_meta = geo_tag.find("meta", itemprop="longitude")
        if latitude_meta and longitude_meta:
            return latitude_meta["content"], longitude_meta["content"]
    return None, None

def scrape_nobroker(city: str, locality: str, page: int = 1):
    url = get_nobroker_url(city, locality)
    if not url:
        return []
    driver = get_chrome_driver()
    driver.get(url)
    SCROLL_PAUSE_TIME = 2
    properties = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    while len(properties) < page * 10:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for card in soup.find_all('div', class_='nb__2_XSE'):
            if len(properties) >= page * 10:
                break
            name = card.find('h2', class_='heading-6').text if card.find('h2', class_='heading-6') else None
            address = card.find('div', class_='text-gray-light').text if card.find('div', class_='text-gray-light') else None
            link = card.find('a', href=True)['href'] if card.find('a', href=True) else None
            price = card.find('div', class_='font-semi-bold heading-6').text if card.find('div', class_='font-semi-bold heading-6') else None
            per_sqft_price = card.find('div', class_='heading-7').text if card.find('div', class_='heading-7') else None
            emi = card.find('div', class_='heading-6', id='roomType').text if card.find('div', class_='heading-6', id='roomType') else None
            built_up = card.find('div', class_='flex', id='unitCode').text if card.find('div', class_='flex', id='unitCode') else None
            facing = card.find('div', class_='font-semibold').text if card.find('div', class_='font-semibold') else None
            apartment_type = card.find('div', class_='font-semibold', string='Apartment Type')
            apartment_type = apartment_type.find_previous('div').text if apartment_type else None
            bathrooms = card.find('div', class_='font-semibold', string='Bathrooms')
            bathrooms = bathrooms.find_previous('div').text if bathrooms else None
            parking = card.find('div', class_='font-semibold', string='Parking')
            parking = parking.find_previous('div').text if parking else None
            image = None
            if card.find('meta', itemprop='image'):
                image_meta = card.find('meta', itemprop='image')['content']
                image = f"https://images.nobroker.in/images/{image_meta}" if image_meta else None
            if name and address and link:
                full_link = f"https://www.nobroker.in{link}"
                latitude, longitude = extract_lat_lon_from_nobroker(full_link)
                property_details = {
                    'name': name,
                    'address': address,
                    'link': full_link,
                    'latitude': latitude,
                    'longitude': longitude,
                    'price': price,
                    'per_sqft_price': per_sqft_price,
                    'emi': emi,
                    'built_up': built_up,
                    'facing': facing,
                    'apartment_type': apartment_type,
                    'bathrooms': bathrooms,
                    'parking': parking,
                    'image': image
                }
                properties.append(property_details)
    driver.quit()
    start = (page - 1) * 10
    end = page * 10
    return properties[start:end]
