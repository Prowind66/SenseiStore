import time
import csv
import requests
import pandas as pd
import os
from fake_useragent import UserAgent
import random 
import datetime

from urllib.parse import urlsplit, unquote
# Selenium Modules
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException,TimeoutException,ElementNotInteractableException
from selenium.webdriver.common.keys import Keys

current_directory = os.getcwd()
image_folder = os.path.join(current_directory, "images")
os.makedirs(image_folder, exist_ok=True)

def driver_setup():
    options = Options()
    ua = UserAgent()
    user_agent = ua.random
    options.add_argument(f'user-agent={user_agent}')
    options.add_argument('window-size=1920,1080')
    options.add_argument("--disable-gpu")  # Fixes GPU rendering issues
    # options.add_experimental_option("detach", True)
    # Don't show browser when scraping , will be faster
    # options.add_argument("--headless")
    driver =  webdriver.Chrome(options=options)

    return driver

def file_exists_check():
    drinks_content_csv_path = current_directory + "/drinks_content.csv"
    if os.path.isfile(drinks_content_csv_path):
        print("File Indeed Exists")
    else:
        # Creating an empty DataFrame without specifying data types
        df = pd.DataFrame(columns=['product_id', 'product_name', 'product_company',
                                   'product_original_price', 'product_discounted_price', 'product_image', 
                                   'product_image_path','product_category', 
                                   'product_bottle_type',"product_dietary_attribute"])
        df.to_csv("drinks_content.csv", index=False, encoding="utf-8-sig")
        # encoding="utf-8-sig" , this forces excel to read as utf-8 , solve the problem for the encoding because now the windows system read as cp-1252
        return "File Does Not Exists , So File Creation Completed"

def download_image(image_url, folder_path,file_name):
    try:
        response = requests.get(image_url, timeout=10)
        local_path = os.path.join(folder_path, file_name)

        with open(local_path, 'wb') as f:
            f.write(response.content)

        return os.path.abspath(local_path)
    except Exception as e:
        print(f"Failed to download {image_url}: {e}")
        return ""
    
def get_beverages_contents(driver):
    # https://www.fairprice.com.sg/brand/f--n
    base_url = "https://www.fairprice.com.sg/brand/f--n"
    driver.get(base_url)

    product_id = 1
    # product_name = ""
    product_company = "Pokka"
    # product_original_price = ""
    # product_discounted_price = ""
    # product_image = ""
    # product_image_path = ""
    product_category = "Drinks"
    # product_bottle_type = ""
    # product_dietary_attribute = ""

   
    try:
        drink_section = driver.find_element(By.XPATH,"//div[contains(@class,'sc-84b21786-6 iTtMbI')]")
    except NoSuchElementException:
        print("No Drink Objects")

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load page
        time.sleep(4)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    try:
        card_objects = drink_section.find_elements(By.XPATH,".//div[contains(@class,'sc-e68f503d-0 kxZjUB product-container')]")
    except NoSuchElementException:
        print("No Card Objects")

    for card in card_objects:
        
        product_info_container = card.find_element(By.XPATH,".//div[contains(@class,'sc-e68f503d-32 jvFTSZ')]//div[contains(@class,'sc-e68f503d-8 kRpkxd')]")
        product_price_container = product_info_container.find_elements(By.XPATH,".//div[contains(@class,'sc-e68f503d-11 iYFArc')]//div[contains(@class,'sc-e68f503d-10 dksglq')]")[0]
        product_prices = product_price_container.find_elements(By.TAG_NAME, "span")
        try:
            product_original_price = product_prices[0].get_attribute("innerText")
        except NoSuchElementException:
            print("No product_original_price")
        try:
            product_discounted_price = product_prices[2].get_attribute("innerText")
        except NoSuchElementException:
            print("No product_discounted_price")
        except IndexError:
            print("No product_discounted_price")
            product_discounted_price = 0
        product_name_container = product_info_container.find_elements(By.XPATH,".//div[contains(@class,'sc-e68f503d-7 cEAugL')]//div[contains(@class,'sc-408392be-0 capxft')]")[0]
        product_names = product_name_container.find_elements(By.TAG_NAME, "span")

        product_name = product_names[1].get_attribute("innerText")

        product_quantity_halal_or_not_container = product_info_container.find_elements(By.XPATH,".//div[contains(@class,'sc-e68f503d-7 cEAugL')]//div[contains(@class,'sc-e68f503d-31 jaFXRP')]//div[contains(@class,'sc-e94e62e6-1 daFmNg')]")[0]
        product_quantity_halal_or_not = product_quantity_halal_or_not_container.find_elements(By.TAG_NAME, "span")

        product_bottle_type = product_quantity_halal_or_not[0].get_attribute("innerText")
        try:
            product_dietary_attribute = product_quantity_halal_or_not[1].get_attribute("innerText")
        except NoSuchElementException:
            print("No product_dietary_attribute")
        except IndexError:
            product_dietary_attribute = ""
        new_file_name = product_name + product_bottle_type + ".jpg"
        print(WebDriverWait(card, 3).until(EC.visibility_of_element_located((By.XPATH,".//div[contains(@class,'sc-e68f503d-4 jdonid')]//span//img[contains(@class,'sc-aca6d870-0 janHcI')]"))).get_attribute("src"))
        product_image = card.find_element(By.XPATH,".//div[contains(@class,'sc-e68f503d-4 jdonid')]//span//img[contains(@class,'sc-aca6d870-0 janHcI')]")
        # image_elements = product_image_container.find_elements(By.TAG_NAME, "img")
        image_url = product_image.get_attribute("src")
        print(product_image.get_attribute("src"))
        
        image_path = download_image(image_url, image_folder,new_file_name)
        product_id += 1
        
        product_list = []
        product_list.append({
            "product_id": product_id,
            "product_name": product_name,
            "product_company": product_company,
            "product_original_price": product_original_price,
            "product_discounted_price": product_discounted_price,
            "product_image": image_url,
            "product_image_path": image_path,
            "product_category": product_category,
            "product_bottle_type": product_bottle_type,
            "product_dietary_attribute": product_dietary_attribute
        })
        df = pd.DataFrame(product_list)
        csv_path = os.path.join(current_directory, "drinks_content.csv")
        df.to_csv(csv_path, mode='a', header=False, index=False, encoding="utf-8-sig")



def main():
    file_exists_check()
    driver = driver_setup()
    get_beverages_contents(driver)
    driver.quit()
    print("Scraping Completed Successfully!")

if __name__ == "__main__":
    main()