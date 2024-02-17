import random
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import json
import os
import shutil
import re
import dbinit
import embedding
import uuid
from urllib.parse import urlparse

def select_half_randomly(result_set):
    # Shuffle the result set
    random.shuffle(result_set)

    # Calculate half length
    half_length = len(result_set) // 2
    if half_length > 100:
        half_length = 99
    # Select the first half
    return result_set[:half_length]


def scrape_website(website):
    def get_base_url(url):
        parsed_url = urlparse(url)
        base_url = f"https://{parsed_url.netloc}/"
        return base_url
    def replace_multiple_spaces(text):
        return re.sub(r'\s+', ' ', text)
    def ensure_trailing_slash(s):
        """Ensure the string ends with a forward slash."""
        if not s.endswith('/'):
            return s + '/'
        return s
    # create empty dict
    website_cleaned = get_base_url(website)
    website_parent = ensure_trailing_slash(website_cleaned)
    dict_href_links = {}
    dirname = website_parent.replace("http://", "").replace("https://", "").replace("/", "_")

    if os.path.exists(dirname):
        shutil.rmtree(dirname)
        print(f"Folder deleted: {dirname}")

    def getdata(url):
        headers = { 
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36', 
            'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
            'Accept-Language' : 'en-US,en;q=0.5',
            'Accept-Encoding' : 'gzip', 
            'DNT' : '1', # Do Not Track Request Header 
            'Connection' : 'close'
        }
        r = requests.get(url, headers = headers)
        return r.text
    
   

    def get_links(parent_link, website_link):
        try:
            html_data = getdata(website_link)
            print("links count = ", html_data.count("href"))
            soup = BeautifulSoup(html_data, "html.parser")
            list_links = []
            print("parent_link = ", website_link)
            set_links = soup.find_all("a", href=True)
            # if len(set_links) >= 80:
            #     set_links = select_half_randomly(set_links)
            
            print("links count after filter = ", len(set_links))

            for link in set_links:
                # Append to list if new link contains original link
                if "email-protection" in str(link["href"]):
                    print("email-protection link skipped = ", str(link["href"]))
                    continue
                if "/search?" in str(link["href"]):
                    print("search link skipped = ", str(link["href"]))
                    continue
                if str(link["href"]).count("/") > 3:
                    if not str(link["href"]).endswith("/"):
                        print("too much sublinks, link skipped = ", str(link["href"]))
                        continue
                if str(link["href"]).count("?") > 0:
                    print("query string, link skipped = ", str(link["href"]))
                    continue
                if str(link["href"]).count("&") > 1:
                    print("too much parameters, link skipped = ", str(link["href"]))
                    continue
                if str(link["href"]).startswith((str(website_link))):
                    print("link href = ", link["href"])
                    html_data2 = getdata(link["href"])
                    soup2 = BeautifulSoup(html_data2, "html.parser")
                    text = soup2.get_text(separator='. ')
                    save_json(dirname, link["href"], text)
                    list_links.append(link["href"])

                # Include all href that do not start with website link but with "/"
                if str(link["href"]).startswith("/"):
                    if str(link["href"]).count("/") > 2:
                        if not str(link["href"]).endswith("/"):
                            print("too much sublinks for href, link skipped = ", str(link["href"]))
                            continue
                        
                    if link["href"] not in dict_href_links:
                        dict_href_links[link["href"]] = None
                        link_with_www = parent_link + link["href"][1:]
                        print("adjusted link =", link_with_www)
                        html_data2 = getdata(link_with_www)
                        soup2 = BeautifulSoup(html_data2, "html.parser")
                        text = soup2.get_text(separator='. ')
                        save_json(dirname, link_with_www, text)
                        list_links.append(link_with_www)

            # Convert list of links to dictionary and define keys as the links and the values as "Not-checked"
            dict_links = dict.fromkeys(list_links, "Not-checked")
            text = soup.get_text(separator='. ')

            full_path = os.path.join(dirname, "data.json")
            if not os.path.exists(dirname):
                # Create the folder if it doesn't exist
                os.makedirs(dirname)
                print(f"Folder created: {dirname}")
                

            save_json(dirname, website_link, text)

            a_file = open(full_path, "w")
            json.dump(dict_links, a_file)
            a_file.close()
            return dict_links
        except Exception as ex:
            print("Error = ", ex)
            return {}
        
        

    def save_json(parentfolder, link, html_text):
        """
        Save link and HTML text as JSON to a file.

        :param link: The URL to be saved.
        :param html_text: The HTML text to be saved.
        :param filename: The name of the file to save the data. Default is 'data.json'.
        """
        # Create a filename from the link
        filename = link.replace("http://", "").replace("https://", "").replace("/", "_") + '.json'
        full_path = os.path.join(parentfolder, filename)

        # Create the data dictionary
        data = {
            "link": link,
            "text": replace_multiple_spaces(html_text.replace("\n.", ""))
        }

        # Convert the dictionary to a JSON string
        json_data = json.dumps(data, indent=4)

        if not os.path.exists(parentfolder):
            # Create the folder if it doesn't exist
            os.makedirs(parentfolder)
            print(f"Folder created: {parentfolder}")

        # Save the JSON string to a file
        with open(full_path, 'w') as file:
            file.write(json_data)

        print(f"JSON file '{full_path}' created successfully.")

    def get_subpage_links(l):
        for link in l:
            try:
                print("link in get_subpage_links = ", link)
                #if link has more than 2 _ then skip
                if link.count("/") > 3:
                    print("link skipped = ", link)
                    l[link] = "Checked"
                    dict_links_subpages = {}
                else:
                    # If not crawled through this page start crawling and get links
                    if l[link] == "Not-checked":
                        dict_links_subpages = get_links(website_parent, link)
                        # Change the dictionary value of the link to "Checked"
                        l[link] = "Checked"
                    else:
                        # Create an empty dictionary in case every link is checked
                        dict_links_subpages = {}
            
                # Add new dictionary to old dictionary
                l = {**dict_links_subpages, **l}
            except Exception as ex:
                l[link] = "Checked"
                dict_links_subpages = {}
            
        return l

    # create dictionary of website
    dict_links = {website_cleaned: "Not-checked"}

    counter, counter2 = None, 0
    while counter != 0:
        counter2 += 1
        dict_links2 = get_subpage_links(dict_links)
        # Count number of non-values and set counter to 0 if there are no values within the dictionary equal to the string "Not-checked"
        # https://stackoverflow.com/questions/48371856/count-the-number-of-occurrences-of-a-certain-value-in-a-dictionary-in-python
        counter = sum(value == "Not-checked" for value in dict_links2.values())
        # Print some statements
        print("")
        print("THIS IS LOOP ITERATION NUMBER", counter2)
        print("LENGTH OF DICTIONARY WITH LINKS =", len(dict_links2))
        print("NUMBER OF 'Not-checked' LINKS = ", counter)
        print("")
        dict_links = dict_links2

        try: 
            # Save list in json file
            full_path = os.path.join(dirname, "data.json")
            a_file = open(full_path, "w")
            json.dump(dict_links, a_file)
            a_file.close()
            print("JSON file saved ", full_path)        
        except Exception as ex:
            print("Error for main cycle json saving = ", ex)
            dict_links = {}
            break
        


# scrape_website("https://tech.eu/")
# dbinit.create_table_with_vector_support()
