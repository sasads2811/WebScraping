import os
import re

import requests
from bs4 import BeautifulSoup
import csv
from tqdm import tqdm

# Base URL for the website
base_url = 'https://www.bolon.com'

# URL of the page you want to scrape
url = 'https://www.bolon.com/en/products/floors'

# Send a GET request to fetch the HTML content
response = requests.get(url)

# Check if the request was successful
if response.status_code == 200:
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the list of products
    product_list = soup.find('ul', class_='product-list columns')
    products = list()

    # Iterate through each product (inside <li> tags)
    for product in product_list.find_all('li', class_='product-list__item'):
        product_link = product.find('a')['href']
        product_name = product.find('h4', class_='product-list__item-title').get_text(strip=True)
        product_link = base_url + product_link if base_url not in product_link else product_link
        products.append({'product_name': product_name, 'product_link': product_link})

    number_of_products = len(products)
    current_number = 1
    # Go through all products
    for product in tqdm(products, desc="Downloading Products", unit="product"):
        product_name = product['product_name']
        product_page = requests.get(product['product_link'])
        soup = BeautifulSoup(product_page.content, 'html.parser')
        # print(f"{current_number}/{number_of_products} Downloading {product_name} data \n")

        # Create product directory (replace spaces or slashes in names)
        product_folder = os.path.join("products", product_name.replace(' ', '_').replace('/', '_'))
        os.makedirs(product_folder, exist_ok=True)

        # Subdirectories for images and documents
        images_folder = os.path.join(product_folder, "images")
        os.makedirs(images_folder, exist_ok=True)

        docs_folder = os.path.join(product_folder, "doc_files")
        os.makedirs(docs_folder, exist_ok=True)

        # Extract description
        desc_div = soup.find('div', class_='row show-for-medium-up')
        desc = desc_div.find('p', class_='paragraphed-gen5').get_text(strip=True)
        product.update({'desc': desc})

        # Extract available types
        available_in_div = soup.find('div', class_='row baseline-offset--1')

        # Extract categories with data
        avin = available_in_div.find_all('div', class_='small-12 columns')

        rolls = {}
        av_rolls = avin[1].find('div', id='b-rolls')
        if av_rolls:
            desc = av_rolls.find('p').get_text(strip=True)
            table = av_rolls.find_all('tr')
            for row in table:
                header = row.find('td', class_='product-types__info__item__table__header').get_text(strip=True)
                value = row.find('td', class_='product-types__info__item__table__value').get_text(strip=True)
                rolls['desc'] = desc
                rolls[header] = value
            product.update({'Rolls': rolls})

        tiles = {}
        av_tiles = avin[1].find('div', id='b-tiles')
        if av_tiles:
            desc = av_tiles.find('p').get_text(strip=True)
            table = av_tiles.find_all('tr')
            for row in table:
                header = row.find('td', class_='product-types__info__item__table__header').get_text(strip=True)
                value = row.find('td', class_='product-types__info__item__table__value').get_text(strip=True)
                tiles['desc'] = desc
                tiles[header] = value
            product.update({'Tiles': tiles})

        acoustictiles = {}
        av_acoustictiles = avin[1].find('div', id='b-acoustictiles')
        if av_acoustictiles:
            desc = av_acoustictiles.find('p').get_text(strip=True)
            desc_list = av_acoustictiles.find('ul')
            list_items = desc_list.find_all('li')

            # Extract text from each list item and create a list of strings
            item_texts = [item.get_text(strip=True) for item in list_items]

            # Join the texts with a comma and space
            formatted_text = ', '.join(item_texts)
            desc += formatted_text
            table = av_acoustictiles.find_all('tr')
            for row in table:
                header = row.find('td', class_='product-types__info__item__table__header').get_text(strip=True)
                value = row.find('td', class_='product-types__info__item__table__value').get_text(strip=True)
                acoustictiles['desc'] = desc
                acoustictiles[header] = value
            product.update({'Acoustictiles': acoustictiles})

        studio = {}
        av_studio = avin[1].find('div', id='b-studio')
        if av_studio:
            p_elements = av_studio.find_all('p', class_="paragraphed-gen5")
            desc = p_elements[0].get_text(strip=True)

            p_elements.pop(0)

            merged_text = ', '.join([p.get_text(strip=True) for p in p_elements])
            desc += merged_text
            studio['desc'] = desc
            product.update({'Studio': studio})

        # Image download
        images = soup.find('section', class_='product-slideshow')
        ul = images.find('ul', class_='product-slideshow__thumbs small-block-grid-2')
        for image in ul.find_all('img'):
            image_url = image['src']
            full_image_url = base_url + image_url

            # Extract the portion of the URL after 'cover-'
            image_name = image_url.split('cover-')[-1] if 'cover-' in image_url else image_url.split('contain-')[-1]
            image_name = image_name.replace('/', '-')

            # Download image
            response = requests.get(full_image_url)
            if response.status_code == 200:
                image_path = os.path.join(images_folder, image_name)
                with open(image_path, 'wb') as file:
                    file.write(response.content)
            else:
                print(f"Failed to download image. Status code: {response.status_code}")

        # Extract document links
        doc_links = []
        div = soup.find_all('section')
        for section in div[3].find_all('div', class_='row baseline-offset--0-5 baseline-offset-bottom--0-5'):
            a = section.find('a')['href']
            b = section.find('a')
            c = b.get('data-url')
            doc_file = b.get_text(strip=True)
            link = base_url + c if c else base_url + a
            doc_links.append({'link_name': doc_file, 'link': link})

        # Download document files
        for doc_link in doc_links:
            if doc_link['link_name'] == 'Installation Guide':
                # Create a directory for Installation Guide
                installation_guide_folder = os.path.join("products", 'Installation_Guide')
                os.makedirs(installation_guide_folder, exist_ok=True)

                # Check if the folder already contains files
                if not os.listdir(installation_guide_folder):
                    response = requests.get(doc_link['link'])
                    soup = BeautifulSoup(response.content, 'html.parser')
                    div = soup.find_all('div', class_='item-slider item-slider--full-width item-slider--medium-spacing')
                    # Find all <a> tags
                    links = soup.find_all('a', href=True)

                    # Filter links that contain 'asset' in their href
                    filtered_links = [link for link in links if 'asset' in link['href']]

                    # Download each file
                    for link in filtered_links:
                        file_url = base_url + link['href']
                        response = requests.get(file_url)
                        content_disposition = response.headers.get("Content-Disposition")
                        if content_disposition:
                            # Extract the filename using a regex pattern
                            filename_match = re.search(r'filename="(.+?)"', content_disposition)
                            if filename_match:
                                filename = filename_match.group(1)
                            else:
                                filename = f"file_1.pdf"  # Default filename if parsing fails
                        else:
                            filename = f"file_1.pdf"  # Default filename if header is missing

                        if response.status_code == 200:
                            doc_file_path = os.path.join(installation_guide_folder, filename)
                            with open(doc_file_path, "wb") as file:
                                file.write(response.content)
                            # print(f"Downloaded: {doc_file_path}")
                        else:
                            print(f"Failed to download file {link['href']}: Status code {response.status_code}")

            elif doc_link['link_name'] == 'Cleaning Guide':
                # Create a directory for Installation Guide
                installation_guide_folder = os.path.join("products", 'Cleaning_Guide')
                os.makedirs(installation_guide_folder, exist_ok=True)

                # Check if the folder already contains files
                if not os.listdir(installation_guide_folder):
                    response = requests.get(doc_link['link'])
                    soup = BeautifulSoup(response.content, 'html.parser')
                    div = soup.find('div', class_='downloads-overlay')
                    links = div.find_all('a', href=True)

                    # Filter links that contain 'asset' in their href
                    filtered_links = [link['href'] for link in links if 'asset' in link['href']]

                    # Download each file
                    for link in filtered_links:
                        file_url = base_url + link
                        response = requests.get(file_url)
                        content_disposition = response.headers.get("Content-Disposition")
                        if content_disposition:
                            # Extract the filename using a regex pattern
                            filename_match = re.search(r'filename="(.+?)"', content_disposition)
                            if filename_match:
                                filename = filename_match.group(1)
                            else:
                                filename = f"file_1.pdf"  # Default filename if parsing fails
                        else:
                            filename = f"file_1.pdf"  # Default filename if header is missing

                        if response.status_code == 200:
                            doc_file_path = os.path.join(installation_guide_folder, filename)
                            with open(doc_file_path, "wb") as file:
                                file.write(response.content)
                            # print(f"Downloaded: {doc_file_path}")
                        else:
                            print(f"Failed to download file {link['href']}: Status code {response.status_code}")

            elif doc_link['link_name'] == 'Product Specification':
                # Create a directory for Installation Guide
                installation_guide_folder = os.path.join("products", 'Product_Specification')
                os.makedirs(installation_guide_folder, exist_ok=True)

                # Check if the folder already contains files
                if not os.listdir(installation_guide_folder):
                    response = requests.get(doc_link['link'])
                    content_disposition = response.headers.get("Content-Disposition")
                    if content_disposition:
                        # Extract the filename using a regex pattern
                        filename_match = re.search(r'filename="(.+?)"', content_disposition)
                        if filename_match:
                            filename = filename_match.group(1)
                        else:
                            filename = f"file_1.pdf"  # Default filename if parsing fails
                    else:
                        filename = f"file_1.pdf"  # Default filename if header is missing

                    if response.status_code == 200:
                        doc_file_path = os.path.join(installation_guide_folder, filename)
                        with open(doc_file_path, "wb") as file:
                            file.write(response.content)
                        # print(f"Downloaded: {doc_file_path}")
                    else:
                        print(f"Failed to download file {doc_link['link']}: Status code {response.status_code}")

            # elif doc_link['link_name'] == 'CAD (BIM)':
            elif doc_link['link_name'] == 'Declaration of Performance':
                # Create a directory for Installation Guide
                installation_guide_folder = os.path.join("products", 'Declaration_of_Performance')
                os.makedirs(installation_guide_folder, exist_ok=True)

                # Check if the folder already contains files
                if not os.listdir(installation_guide_folder):
                    response = requests.get(doc_link['link'])
                    content_disposition = response.headers.get("Content-Disposition")
                    if content_disposition:
                        # Extract the filename using a regex pattern
                        filename_match = re.search(r'filename="(.+?)"', content_disposition)
                        if filename_match:
                            filename = filename_match.group(1)
                        else:
                            filename = f"file_1.pdf"  # Default filename if parsing fails
                    else:
                        filename = f"file_1.pdf"  # Default filename if header is missing

                    if response.status_code == 200:
                        doc_file_path = os.path.join(installation_guide_folder, filename)
                        with open(doc_file_path, "wb") as file:
                            file.write(response.content)
                        # print(f"Downloaded: {doc_file_path}")
                    else:
                        print(f"Failed to download file {doc_link['link']}: Status code {response.status_code}")

            elif doc_link['link_name'] == 'Light Reflectance Value':
                # Create a directory for Installation Guide
                installation_guide_folder = os.path.join("products", 'Light_Reflectance_Value')
                os.makedirs(installation_guide_folder, exist_ok=True)

                # Check if the folder already contains files
                if not os.listdir(installation_guide_folder):
                    response = requests.get(doc_link['link'])
                    content_disposition = response.headers.get("Content-Disposition")
                    if content_disposition:
                        # Extract the filename using a regex pattern
                        filename_match = re.search(r'filename="(.+?)"', content_disposition)
                        if filename_match:
                            filename = filename_match.group(1)
                        else:
                            filename = f"file_1.pdf"  # Default filename if parsing fails
                    else:
                        filename = f"file_1.pdf"  # Default filename if header is missing

                    if response.status_code == 200:
                        doc_file_path = os.path.join(installation_guide_folder, filename)
                        with open(doc_file_path, "wb") as file:
                            file.write(response.content)
                        # print(f"Downloaded: {doc_file_path}")
                    else:
                        print(f"Failed to download file {doc_link['link']}: Status code {response.status_code}")

            elif doc_link['link_name'] == 'Texture':
                response = requests.get(doc_link['link'])
                content_disposition = response.headers.get("Content-Disposition")
                if content_disposition:
                    # Extract the filename using a regex pattern
                    filename_match = re.search(r'filename="(.+?)"', content_disposition)
                    if filename_match:
                        filename = filename_match.group(1)
                    else:
                        filename = f"file_1.pdf"  # Default filename if parsing fails
                else:
                    filename = f"file_1.pdf"  # Default filename if header is missing

                if response.status_code == 200:
                    doc_file_path = os.path.join(docs_folder, filename)
                    with open(doc_file_path, "wb") as file:
                        file.write(response.content)
                    # print(f"Downloaded: {doc_file_path}")
                else:
                    print(f"Failed to download file {doc_link['link']}: Status code {response.status_code}")

            elif doc_link['link_name'].strip() == 'High resolution images (.zip)':
                response = requests.get(doc_link['link'])
                content_disposition = response.headers.get("Content-Disposition")
                if content_disposition:
                    # Extract the filename using a regex pattern
                    filename_match = re.search(r'filename="(.+?)"', content_disposition)
                    if filename_match:
                        filename = filename_match.group(1)
                    else:
                        filename = f"file_1.pdf"  # Default filename if parsing fails
                else:
                    filename = f"file_1.pdf"  # Default filename if header is missing

                if response.status_code == 200:
                    doc_file_path = os.path.join(docs_folder, filename)
                    with open(doc_file_path, "wb") as file:
                        file.write(response.content)
                    # print(f"Downloaded: {doc_file_path}")
                else:
                    print(f"Failed to download file {doc_link['link']}: Status code {response.status_code}")

        # Remove items from dict
        product.pop('product_link')

        data = ': \n'.join(doc['link_name'] for doc in doc_links if 'BIM' not in doc['link_name'])
        data += ':'
        # Update the product dictionary with the concatenated data
        product.update({'Product documentation & files': data})

        # Write the product details to a CSV file
        csv_file_path = os.path.join(product_folder, 'product_data.csv')
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=product.keys())
            writer.writeheader()
            writer.writerow(product)

        current_number+=1
else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
