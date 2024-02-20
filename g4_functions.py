#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 17 15:58:00 2023

@author: mariofestersen
"""
import json
import urllib;
from bs4 import BeautifulSoup;
from time import sleep
import csv
import requests
import googlemaps

def getInput(prompt: str, accepted_inputs: list ):
    # A function to handle and return user inputs based on a prompt and accepted_inputs
    accepted_inputs = accepted_inputs.copy()  # Create a copy to avoid modifying the original list
    accepted_inputs.append('n')  # Add 'n' as a default accepted input

    valid_input = False

    if isinstance(accepted_inputs[0], int):
        accepted_range = f"[1, {accepted_inputs[0]}], n"
    else:
        accepted_range = ", ".join(map(str, accepted_inputs))

    while not valid_input:
        user_input = input(f"{prompt} [{accepted_range}]: ").lower()

        if user_input in accepted_inputs:
            valid_input = True
            return user_input
        elif isinstance(accepted_inputs[0], int):
            try:
                user_number = int(user_input)
                if 1 <= user_number <= accepted_inputs[0]:
                    valid_input = True
                    return user_number
                else:
                    print(f"{user_number} is not in the accepted range.")
            except ValueError:
                print("Invalid input. Please enter a number.")
        else:
            print(f"{user_input} is not an accepted value.")
            

def getHTML(url: str):
    # This function takes a url, and returns a html string. It is called by getLinks()
    try:
        request = urllib.request.Request( url )
        response = urllib.request.urlopen( request )
        html = response.read().decode('utf-8')
        sleep(0.5) # We add a delay between each request.
        return {"success": html}
    except Exception as e:
        return {"error" : f"ERROR: {e} - URL: {url}" }

def getPageLinks(main_url: str, numberOfPages: int):
    # This function scrapes pages for their links, and stores the links in a json file.
    returnData = {
        'links': [],
        'errors':[]
        }
    # We scrape each page
    for i in range(1, numberOfPages+1):
        url = f"{main_url}?page={i}"
        html = getHTML(url)
        
        # If our request failed, return the error message from getHTML.
        if 'error' in html:

            returnData['errors'].append(html['error']);
        else:
            soup = BeautifulSoup(html['success'], features='lxml')
            
            # Anchors with the specific title contains href to the pages we need to scrape.
            # We get all the anchor (links) from page 'i'. 
            
            pageLinks = soup.find_all(name = "a", attrs = {"title" : "View this Red Hot Chili Peppers setlist"})
            
            # for each link on the page[i]...
            for link in pageLinks:
                # each achors href start with '../'.
                # We need them to start with ' https://www.setlist.fm/ ' 
                linkString = "https://www.setlist.fm/" + link['href'][3:]
                # We now append the linkStrings to our list in the dictionary.
                returnData['links'].append(linkString)
                
            print(f"{i} out of {numberOfPages}")
            
        
    return returnData;


def writeToFile(data, filename: str, writeMode: str = "w"):
    # function creates a json object with the data from the dictionary, and write it to the filename.
    # returns true if successful. False otherwise.
    if filename.endswith(".csv"):
        headers = []
        try:
            for key in data[0]:
                headers.append(key)
    
            with open(filename, 'w', encoding='UTF-8', newline='') as f:
                writer = csv.writer(f, delimiter = ";")
                writer.writerow(headers)
    
                for i in range(0, len(data)):
                    setlist = data[i]
                    row = []
                    for key in setlist:
                        if key == 'geocodeLat' or key == "geocodeLon":
                            if setlist[key] == "False":
                                print(f"{i} is {setlist[key]}")
                            else:
                                row.append(float(setlist[key]));
                        else:
                            row.append(setlist[key]);
                    writer.writerow(row);
            return True;
        except Exception as e:
            print(e)
            return False
            
    else:
        try:
            json_object = json.dumps(data, indent=4)
        except Exception as e:
            print(f"Error dumping data to json format: {e}")
            return False;
        
        
        # Writing to data to jsonfile.
        try:
            with open(filename, writeMode) as file:
                file.write(json_object)
                file.close()
            return True;
        except FileNotFoundError:
            print(f"{filename} doesnt exist.");
        except Exception as e:
            print(f"Filename: {filename}, Error: {e}")
        return False;

def readFile(filepath: str):
    """ This function needs to return the content of a file. 
    Ideally it should be able to
    read both CSV or JSON """
    
    try:
        file = open(filepath, "r")
    except FileNotFoundError as e:
        print(f"File does already not exist: It will be created.")
        return False;
    except Exception as e:
        print(f"Error: {e}")
        return False;
    
    if filepath.endswith(".json"):
        jsonData = json.load(file)
        return jsonData;
    elif filepath.endswith(".csv"):
        #read csv
        data = []  # List to store dictionaries
        try:
            with open(filepath, 'r') as csvfile:
                # Assuming the first row contains headers
                csv_reader = csv.reader(csvfile, delimiter=';')
    
                # Read and store headers
                headers = next(csv_reader)
    
                # Iterate through each row
                for row in csv_reader:
                    # Create a dictionary using headers and row data
                    row_dict = dict(zip(headers, row))
                    data.append(row_dict)
    
            return data
        except Exception as e:
            print(e)
    else:
        print("Unsupported fileformat.")
        return False
    
    

def getSetlistData(link_url: str):
    return_setlist = {}
    html = getHTML(link_url)
    try:
        soup = BeautifulSoup(html['success'], features='lxml')
    except KeyError as e:
        print("{e}")
        return False;

    
    """ VENUE """
    # Scrape the venue string.
    # infoContainer div contains
    info_container = soup.find("div", attrs = {"class" : "infoContainer" })
    info_container_anchors = info_container.find_all("a")
    venue = info_container_anchors[1].text
    return_setlist['venue'] = venue

    """ TOUR """
    # We scrape the tour name.
    info_container_paragraph = info_container.find('p')
    try:
        return_setlist["tour"] = info_container_paragraph.find_all('span')[2].text
    except AttributeError as e:
        return_setlist["tour"] = ""
        

    """ DATE """
    # We scrape the date, and format it YYYY-MM-DD.
    date_block = soup.find("div", attrs = {"class": "dateBlock"})
    date_list = date_block.find_all("span")

    months = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12
              }
    month = months[date_list[0].text]
    day = int(date_list[1].text)
    year = int(date_list[2].text)

    return_setlist["date"] = f"{year}-{month}-{day}"

    """ SONGS """
    # We scrape the songs as a list, and then join the list, seperated by comma's.
    songsStr = "";
    
    # If there isnt a list of songs, there will be a div with the class name emptySetlist. we first check for this.
    empty = soup.find("div", attrs= {"class": "emptySetlist"})
    if(empty):
        # We react to no songs.
        print(f"Empty setlist: {link_url}")
        return_setlist['songs'] = "No songs in this setlist."
    else:
        song_anchors = soup.find_all("a", attrs = {"class": "songLabel"})
        songs = []
        for song_anchor in song_anchors:
            songs.append(song_anchor.text)
    
        songsStr = ", ".join(songs)
    return_setlist['songs'] = songsStr

    """ GEOLOCATION """
    loc_data = findLocation(venue)
    if loc_data == False:
        latLon = findLocationGmaps(venue)
        if latLon == False:
            return_setlist['geocodeLat'], return_setlist['geocodeLon'] = "", ""
        else:
            return_setlist['geocodeLat'], return_setlist['geocodeLon'] = latLon[0], latLon[1]
    else:
        latLon = getGeocodes(loc_data)
        return_setlist['geocodeLat'], return_setlist['geocodeLon'] = latLon[0], latLon[1]
    
    return return_setlist

def findLocationGmaps(adr: str):
    gmaps_key = "AIzaSyBpqwAaB83fs0Eu9MvXo1oYM93SvEqy_l4"
    gmaps = googlemaps.Client(key=gmaps_key)

    geocode_result = gmaps.geocode(adr)
    
    try:
        lat = geocode_result[0]['geometry']['location']['lat']
        lon = geocode_result[0]['geometry']['location']['lng']
        
        return [round(float(lat), 3), round(float(lon), 3)]
    except Exception as e:
        print(e)
        return False
    sleep(1)

def findLocation(adr, form = 'json'):
    BASE_URL = "https://nominatim.openstreetmap.org/search?"
    form = f"format={form}"
    adr_list = adr.split(", ")
    
    country = adr_list[-1] # Last element is always country
    amenity = adr_list[0] # First element is always amenity, but perhaps not always unique 
    city = adr_list[1] # this is normally a city.
    
    response = requests.get(f"{BASE_URL}{form}&country={country}&amenity={amenity}")
    location_data = response.json()
    
    if len(location_data) == 0:
        # Our request wasnt found. We have to match on different criteria.
        # We try city instead of amenity.
        print(f"No amenity match found on: {adr}. Trying on city instead.")
        
        response = requests.get(f"{BASE_URL}{form}&country={country}&city={city}")
        location_data = response.json()
    

    if len(location_data) > 1:
        # We got too many out. We then try with city aswell.
        
        print(f"{len(location_data)} found. Trying amenity, city, country")
        print(f"Adr is: {adr}")

        # We try city AND amenity.
        response = requests.get(f"{BASE_URL}{form}&country={country}&city={city}&amenity={amenity}")
        location_data = response.json()
        if len(location_data) > 1:
            # We just take the first and best result. Shouldnt happen very often...
            print(f"Several matches found on Amenity, City, Country. Selecting top result: {location_data[0]['display_name']}")
            return location_data[0]
        
    if len(location_data) == 0:
        print(f"No match found for amenity or city. ADR: {adr}")
        return False;
    elif len(location_data) == 1:
        # Perfect. Unique location data. Return it!
        return location_data[0]
    else:
        # More than one location again. Return first.
        return location_data[0]
    
def getGeocodes(ldata: dict):
    try:
        lat = round(float(ldata['lat']), 2)
        lon = round(float(ldata['lon']), 2)
    except TypeError as e:
        print(f"Error converting geoCodes: {e} || {ldata}")
        return [False,False]
    except Exception as e:
        print(f"ERROR: {e}")
        return [False,False]
    return [lat, lon]