import g4_functions


""" WRITE TO JSON (EASIER TO AUGMENT) """


if __name__ == '__main__':
    setlist_filename = "setlists.json"
    links_filename = "links.json"
    running = True;
    while running:
        # Which action do we wish to do?
        actionString = """
        Which action do you wish to take?
        1. Get and store the links for each setlist.
        2. Get and store data for each setlist.  
        3. convert the jsonfile to csv.
        """
        action = g4_functions.getInput(actionString, ["1","2","3"])
        if action == "1":
            """ """
            mainurl = "https://www.setlist.fm/setlists/red-hot-chili-peppers-13d68969.html";
            nPages = g4_functions.getInput("How many pages do you wish to scrape?", [188]) # 188

            if nPages != 'n':
                links = g4_functions.getPageLinks(mainurl, nPages)
                if links != False:
                    response = g4_functions.writeToFile(filename = links_filename, data = links)
                if response: print(f"{len(links['links'])} links written to file.")
        elif action == "2":
            """ SCRAPE EACH LINKS PAGE TO GET THE SETLIST DATA """
            # We first need to read the links file
            links = g4_functions.readFile(links_filename)
            setlist_data = g4_functions.readFile(setlist_filename)
            
            if not setlist_data:
                # File doesnt exist. Define setlist_data
                n = 0
                setlist_data = []
            else:
                j = 0
                for element in setlist_data:
                    if element['id'] > j:
                        j = element['id']
                n = j
            if links:
                # Scrape setlist data from each link.
                scrapes = g4_functions.getInput("How many links do you wish to scrape?", [len(links['links'])])
                if scrapes == "n":
                    running = False
                else:
                    for i in range(scrapes):
                        n += 1
                        setlist_link = links['links'].pop()
                        temp_data = g4_functions.getSetlistData(setlist_link)
                        if temp_data != False:
                            temp_data['id'] = int(n)
                            setlist_data.append(temp_data)
                        else:
                            print(f"Some error occured at this link: {setlist_link}")
                    
                    # Loop done. Write data to each file.
                    response = g4_functions.writeToFile(filename = setlist_filename, data = setlist_data)
                    if response: print("setlist_data written to file")
                    response = g4_functions.writeToFile(filename = links_filename, data = links)
                    if response: print("(Updated) links written to file.")
            else:
                # File probably doesnt exist.
                print("Else: File does not exist.")
        elif action == "3":
            """ WRITE JSON TO CSV """
            setlist_data = g4_functions.readFile(setlist_filename)
            response = g4_functions.writeToFile(data = setlist_data, filename="setlist_csv_data.csv")
            if response:
                print("Successfully written data to csv.")
        elif action == "n":
            running = False;
        else:
            print("Invalid input.")

