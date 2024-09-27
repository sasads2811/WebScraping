import os

import requests
from bs4 import BeautifulSoup
import csv
from tqdm import tqdm

# Base URL for the website
base_url = 'https://www.lano.com'

# URL of the page you want to scrape
url = 'https://www.lano.com/en/hospitality'

# Send a GET request to fetch the HTML content
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the list of products
    product_list = soup.find('ul', class_='product-overview')

    products = list()

    # Iterate through each product (inside <li> tags)
    for product in product_list.find_all('div', class_='va-m'):
        product_link = product.find('a')['href']
        product_name = product.find('a').get_text(strip=True)
        product_link = base_url + product_link if base_url not in product_link else product_link
        products.append({'product_name': product_name, 'product_link': product_link})

    for product in tqdm(products, desc="Downloading Products", unit="product"):
        product_name = product['product_name']
        product_page = requests.get(product['product_link'])
        soup = BeautifulSoup(product_page.content, 'html.parser')

        # Create product directory (replace spaces or slashes in names)
        product_folder = os.path.join("lano_hospitality_products", product_name.replace(' ', '_').replace('/', '_'))
        os.makedirs(product_folder, exist_ok=True)

        # Subdirectories for images and documents
        images_folder = os.path.join(product_folder, "images")
        os.makedirs(images_folder, exist_ok=True)

        docs_folder = os.path.join(product_folder, "doc_files")
        os.makedirs(docs_folder, exist_ok=True)

        available_colours_folder = os.path.join(product_folder, "available_colours")
        os.makedirs(available_colours_folder, exist_ok=True)

        product_info_div = soup.find('div', class_='page-wrap')

        # Image download
        images_div = product_info_div.find('div', class_='product-slideshow-wrapper')
        slideshow_div = images_div.find('div', class_='cycle-slideshow')
        image_elements = slideshow_div.find_all('img')

        for image in image_elements:
            image_url = image['src']

            # Extract folder name and image name from the URL
            url_parts = image_url.strip('/').split('/')
            folder_name = url_parts[-2]
            image_filename = url_parts[-1]

            # Create the full image name
            image_name = f"{folder_name}-{image_filename}"

            # Download image
            response = requests.get(image_url)
            if response.status_code == 200:
                image_path = os.path.join(images_folder, image_name)
                with open(image_path, 'wb') as file:
                    file.write(response.content)
            else:
                print(f"Failed to download image. Status code: {response.status_code}, URL: {image_url}")

        # Extract product description
        product_head = product_info_div.find('div', class_='description')
        description_text = product_head.find('p').get_text(strip=True) if product_head.find('p') else ''

        # Update the product dictionary with the description
        product.update({'description': description_text})

        # Extract available colors
        colors_div = product_info_div.find('ul', class_='product-thumbs')
        image_list = colors_div.find_all('img')

        # Loop through each image and download
        for image in image_list:
            image_url = image['src']

            image_name = image_url.split('/')[-1]

            # Download the image
            response = requests.get(image_url)
            if response.status_code == 200:
                image_path = os.path.join(available_colours_folder, image_name)
                with open(image_path, 'wb') as file:
                    file.write(response.content)
            else:
                print(f"Failed to download image. Status code: {response.status_code}, URL: {image_url}")

        # Extract technical details
        details_div = product_info_div.find('dl', class_='product-data')
        technical_details = ''

        for dt, dd in zip(details_div.find_all('dt'), details_div.find_all('dd')):
            key = dt.get_text(strip=True) if dt.get_text(strip=True) else '' # Remove the colon from the key
            value = dd.get_text(strip=True) if dd.get_text(strip=True) else ''  # Handle empty values as None
            technical_details += f'{key} {value}\n'

        # Update the product dictionary
        product.update({'technical_details': technical_details})

        # Extract doc files
        tools_div = product_info_div.find('ul', class_='tools')
        doc = tools_div.find_all('a')
        for d in doc:
            if d['title'] == 'Download PDF':
                file_url = d['href']

                # Extract the image name from the URL (last part of the URL path)
                file_name = product_name + '.pdf'

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
