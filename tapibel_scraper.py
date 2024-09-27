import os

import requests
from bs4 import BeautifulSoup
import csv
from tqdm import tqdm

# Base URL for the website
base_url = 'https://www.tapibel.be'

# URL of the page you want to scrape
url = 'https://www.tapibel.be/collections'

# Send a GET request to fetch the HTML content
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the list of products
    product_list = soup.find('div', class_='collections_row')

    products = list()

    # Iterate through each product (inside <li> tags)
    for product in product_list.find_all('div', class_='collection_content'):
        product_link = product.find('a')['href']
        product_name = product.find('a').get_text(strip=True)
        product_link = base_url + product_link if base_url not in product_link else product_link
        products.append({'product_name': product_name, 'product_link': product_link})

    for product in tqdm(products, desc="Downloading Products", unit="product"):
        product_name = product['product_name']
        product_page = requests.get(product['product_link'])
        soup = BeautifulSoup(product_page.content, 'html.parser')
        main_div = soup.find('div', class_='sections_group')

        # Create product directory (replace spaces or slashes in names)
        product_folder = os.path.join("products", product_name.replace(' ', '_').replace('/', '_'))
        os.makedirs(product_folder, exist_ok=True)

        # Subdirectories for images and documents
        images_folder = os.path.join(product_folder, "images")
        os.makedirs(images_folder, exist_ok=True)

        docs_folder = os.path.join(product_folder, "doc_files")
        os.makedirs(docs_folder, exist_ok=True)

        available_colours_folder = os.path.join(product_folder, "available_colours")
        os.makedirs(available_colours_folder, exist_ok=True)

        # Image download
        images = main_div.find('div', class_='product_slider')
        image_list = images.find_all('img')
        for image in image_list:
            image_url = image['src']

            # Extract the portion of the URL after 'cover-'
            image_name = image_url.split('/')[-1]
            # image_name = image_name.replace('/', '-')

            # Download image
            response = requests.get(image_url)
            if response.status_code == 200:
                image_path = os.path.join(images_folder, image_name)
                with open(image_path, 'wb') as file:
                    file.write(response.content)
            else:
                print(f"Failed to download image. Status code: {response.status_code}, image url: {image_url}")

        # Extract product description
        product_head = main_div.find('div', class_='product_head')
        content_wrapper = product_head.find('div', class_='the_content_wrapper')
        description_paragraphs = product_head.find_all('p')

        # Concatenate all paragraph texts into a single string
        description_text = ''.join(paragraph.get_text(strip=True) for paragraph in description_paragraphs)

        # Update the product dictionary with the description
        product.update({'description': description_text})

        # Extract available locations
        available_in_div = main_div.find('div', class_='cusrow')
        product_buttons_div = available_in_div.find('div', class_='product_btns')

        # Find all anchor tags and extract their text
        locations = product_buttons_div.find_all('a')
        available_in = '\n'.join(location.get_text(strip=True) for location in locations)

        # Update the product dictionary with available locations
        product.update({'available_in': available_in})

        # Extract available colors
        colors_div = main_div.find('div', class_='beschikbare_kleuren_inner')
        thumbs_div = colors_div.find('div', class_='thumbs ff')
        image_list = thumbs_div.find_all('div', class_="productSlide")

        # Loop through each image and download
        for image in image_list:
            image_url = image.find('img')['src']
            h5_text = image.find('h5').get_text(strip=True)
            extension = os.path.splitext(image_url)[1]

            image_name = f"{product['product_name']}-{h5_text}{extension}"

            # Download the image
            response = requests.get(image_url)
            if response.status_code == 200:
                image_path = os.path.join(available_colours_folder, image_name)
                with open(image_path, 'wb') as file:
                    file.write(response.content)
            else:
                print(f"Failed to download image. Status code: {response.status_code}, URL: {image_url}")

        # Extract technical details
        details_div = main_div.find('div', class_='technische-details_inner')
        paragraphs = details_div.find_all('p')

        # Loop through each paragraph and extract the text
        technical_details = '\n'.join(p.get_text(strip=True) for p in paragraphs)

        # Update the product dictionary
        product.update({'technical_details': technical_details})

        # Extract doc files
        doc = details_div.find_all('a')
        for d in doc:
            file_url = d['href']

            # Extract the image name from the URL (last part of the URL path)
            file_name = file_url.split('/')[-1]

            # Download the image
            if file_url != '':
                response = requests.get(file_url)
                if response.status_code == 200:
                    image_path = os.path.join(docs_folder, file_name)
                    with open(image_path, 'wb') as file:
                        file.write(response.content)
                else:
                    print(f"Failed to download image. Status code: {response.status_code}, URL: {file_url}")

        # Remove items from dict
        product.pop('product_link')

        # Write the product details to a CSV file
        csv_file_path = os.path.join(product_folder, 'product_data.csv')
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=product.keys())
            writer.writeheader()
            writer.writerow(product)
