from bs4 import BeautifulSoup
import requests
import re
import json
import pandas as pd
from datetime import date

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

import sys
import os
import mimetypes

def get_wishlist(url):
    #   Load the wishlist
    response = requests.get(url)
    page_html = response.text
    #   Parse the page
    soup = BeautifulSoup(page_html, 'html.parser')
    return soup

def get_book_titles(soup):
    title_list  = []
    for match in soup.find_all('a', id=re.compile("itemName_")):
        title = match.string.strip()
        title_list.append(re.sub(r'\s*[\(\[].*?[\)\]]\s*', '', title).strip())
    return title_list


def get_authors(soup):
    author_list = []
    for match in soup.find_all("span", id=re.compile("item-byline-")):
        author = match.string.strip()
        author_list.append(re.sub(r'\s*[\(\[].*?[\)\]]\s*', '', author[3:]))
    return author_list


def get_wishlist_name(soup):
    return soup.find("span", id=re.compile("profile-list-name")).string.strip()


def get_paginator(soup):
    paginator = None
    ##  Find the paginator
    if soup.find("div", {"id": "endOfListMarker"}) is None:
        #   If the end tag doesn't exist, continue
        for match in soup.find_all('input', class_="showMoreUrl"):
            paginator = "https://www.amazon.it" + match.attrs["value"]
    else:
        paginator = None
    return paginator

def get_all(url):
    counter = 0
    paginator = url
    wishlist_name = ""
    wishlist_info = {"Title":[], "Author": []}
    while paginator is not None:
        counter = counter + 1
        soup = get_wishlist(paginator)
        if counter == 1:
            wishlist_name = get_wishlist_name(soup)
            print("Wishlist \'" + wishlist_name + "\'")
        print( "Getting page " + str(counter))
        wishlist_info["Title"] = wishlist_info["Title"] + get_book_titles(soup)
        wishlist_info["Author"] = wishlist_info["Author"] + get_authors(soup)
        paginator = get_paginator(soup)
    wishlist_info["Wishlist Name"] = [wishlist_name] * len(wishlist_info["Title"])
        
    return wishlist_info



def main():

    urls_filename = ''
    today = date.today().strftime("%d%m%Y")
    output_filename = 'wishlist_'+today+'.csv'
    if len(sys.argv) > 1:
        urls_filename = sys.argv[1]

    urls = []
    with open(urls_filename, 'r') as file:
        for line in file:
            urls.append(line)
    
    df = pd.DataFrame(columns=["Title", "Author", "Wishlist Name"])
    for url in urls:
        df = pd.concat([df, pd.DataFrame(get_all(url))], ignore_index=True)  
    
    df.to_csv(output_filename, index=False)

    # upload to Google Drive
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)

    # read Google Drive folder id from config file
    with open('config.json', 'r') as file:
        config = json.load(file)
    
    folder_id = config['folder_id']

    file = drive.CreateFile({
        'title': 'wishlist_'+today+'.csv',
        'parents': [{'id': folder_id}]
    })
    file.SetContentFile(output_filename)
    file.Upload()

if __name__ == "__main__":
    main()