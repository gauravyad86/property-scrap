import time
import json
import base64
import requests
import os
from urllib.parse import quote
from bs4 import BeautifulSoup
from app.utils.chrome_driver import get_chrome_driver

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

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
    desired_count = page * 250
    properties = []
    driver = get_chrome_driver()
    driver.get(url)
    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    while len(properties) < desired_count:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for card in soup.find_all('div', class_='nb__2_XSE'):
            if len(properties) >= desired_count:
                break
            name_tag = card.find('h2', class_='heading-6')
            name = name_tag.text if name_tag else None
            address_tag = card.find('div', class_='text-gray-light')
            address = address_tag.text if address_tag else None
            link_tag = card.find('a', href=True)
            link = link_tag['href'] if link_tag else None
            price_tag = card.find('div', class_='font-semi-bold heading-6')
            price = price_tag.text if price_tag else None
            per_sqft_tag = card.find('div', class_='heading-7')
            per_sqft_price = per_sqft_tag.text if per_sqft_tag else None
            emi_tag = card.find('div', class_='heading-6', id='roomType')
            emi = emi_tag.text if emi_tag else None
            built_up_tag = card.find('div', class_='flex', id='unitCode')
            built_up = built_up_tag.text if built_up_tag else None
            facing_tag = card.find('div', class_='font-semibold')
            facing = facing_tag.text if facing_tag else None
            apt_type_label = card.find('div', class_='font-semibold', string='Apartment Type')
            apartment_type = apt_type_label.find_previous('div').text if apt_type_label else None
            bathrooms_label = card.find('div', class_='font-semibold', string='Bathrooms')
            bathrooms = bathrooms_label.find_previous('div').text if bathrooms_label else None
            parking_label = card.find('div', class_='font-semibold', string='Parking')
            parking = parking_label.find_previous('div').text if parking_label else None
            image = None
            image_meta = card.find('meta', itemprop='image')
            if image_meta:
                image_content = image_meta.get('content')
                image = f"https://images.nobroker.in/images/{image_content}" if image_content else None
            if name and address and link:
                full_link = f"https://www.nobroker.in{link}"
                latitude, longitude = extract_lat_lon_from_nobroker(full_link)
                property_details = {
                    "city": city,
                    "locality": locality,
                    "name": name,
                    "address": address,
                    "link": full_link,
                    "price": price,
                    "perSqftPrice": per_sqft_price,
                    "emi": emi,
                    "builtUp": built_up,
                    "facing": facing,
                    "apartmentType": apartment_type,
                    "bathrooms": bathrooms,
                    "parking": parking,
                    "image": [image] if image else None,
                    "latitude": latitude,
                    "longitude": longitude,
                    "possessionStatus": None,
                    "possessionDate": None,
                    "agentName": None,
                    "description": None,
                    "source": "nobroker"
                }
                properties.append(property_details)
    driver.quit()
    start = (page - 1) * 250
    end = page * 250
    return properties[start:end]
