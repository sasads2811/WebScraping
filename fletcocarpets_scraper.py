import os

import requests
from bs4 import BeautifulSoup
import csv
from tqdm import tqdm

# Base URL for the website
base_url = 'https://www.fletcocarpets.com'

# URL of the page you want to scrape
url = 'https://www.fletcocarpets.com/en/products/wall-to-wall-carpets'
params = {
    'feed': 'true',
    'DoNotShowVariantsAsSingleProducts': 'True'
}
# Send a GET request to fetch the HTML content
response = requests.get(url,params=params)


# Check if the request was successful
if response.status_code == 200:
    products = list()
    try:
        json_data = response.json()
        data = json_data[0].get('ProductsContainer')
        for d in data:
            product_name = d['Product'][0]['googleImpression']['name']
            product_link = base_url + d['Product'][0]['googleImpression']['url']
            products.append({'product_name': product_name, 'product_link': product_link})

    except ValueError:
        print("No JSON data found in the response.")

    for product in tqdm(products, desc="Downloading Products", unit="product"):
        product_name = product['product_name']
        product_page = requests.get(product['product_link'])
        soup = BeautifulSoup(product_page.content, 'html.parser')

        # Create product directory (replace spaces or slashes in names)
        product_folder = os.path.join("fletcocarpets_products", product_name.replace(' ', '_').replace('/', '_'))
        os.makedirs(product_folder, exist_ok=True)

        # Subdirectories for images and documents
        images_folder = os.path.join(product_folder, "images")
        os.makedirs(images_folder, exist_ok=True)

        docs_folder = os.path.join(product_folder, "doc_files")
        os.makedirs(docs_folder, exist_ok=True)

        available_colours_folder = os.path.join(product_folder, "available_colours")
        os.makedirs(available_colours_folder, exist_ok=True)

        product_info_div = soup.find('div', class_='page')

        # Extract image
        image_div = product_info_div.find('div', class_='background-image image-filter image-filter--none dw-mod')
        image_url = base_url + image_div.find('img')['src']
        # Create the full image name
        image_name = image_url.split('/')[-1]

        # Download image
        response = requests.get(image_url)
        if response.status_code == 200:
            image_path = os.path.join(images_folder, image_name)
            with open(image_path, 'wb') as file:
                file.write(response.content)
        else:
            print(f"Failed to download image. Status code: {response.status_code}, URL: {image_url}")

        other_data_div = product_info_div.find('div', class_='grid grid--align-content-start')

        # Extract available in colours

        avin_divs = other_data_div.find_all('div', class_='variant__wrapper')

        # Available colours
        for avin_div in avin_divs:
            image = avin_div.find('img')
            if image:
                image_url = base_url + image['src']

                image_data = avin_div.find_all('p')
                color_name = image_data[1].get_text(strip=True)
                variant_name = image_data[0].get_text(strip=True)

                # Create the image name by combining color and variant
                image_name = f"{color_name}-{variant_name}.{image_url.split('.')[-1]}"

                # Download the image
                response = requests.get(image_url)
                if response.status_code == 200:
                    image_path = os.path.join(available_colours_folder, image_name)
                    with open(image_path, 'wb') as file:
                        file.write(response.content)
                else:
                    print(f"Failed to download image. Status code: {response.status_code}, URL: {image_url}")

        # Extract description
        desc_div = other_data_div.find('div', class_="grid__col-md-12 u-margin-bottom")
        paragraphs = desc_div.find_all('p')

        desc = ''
        for paragraph in paragraphs:
            if paragraph.get_text() != '':
                desc += paragraph.get_text(strip=True)
            else:
                break
        product.update({'description': desc})

        # Extract doc files
        doc_files_div = other_data_div.find_all('div', class_='grid__col-md-6 grid__col-sm-12 grid__col-xs-12')[-1]
        doc_files = doc_files_div.find_all('a', class_="product__document dw-mod")
        for doc_file in doc_files:
            file_url = base_url + doc_file['href']

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
