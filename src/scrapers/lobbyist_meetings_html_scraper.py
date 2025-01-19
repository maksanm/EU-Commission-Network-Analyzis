from dotenv import load_dotenv
load_dotenv()

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from os import path
from datetime import datetime
import json
import os

class LobbyistMeetingsScraper:

    def __init__(self):
        # Configure Selenium WebDriver using Chrome
        self.options = Options()
        #self.options.add_argument("--headless=new")
        self.options.add_argument("--log-level=1")
        self.service = Service(ChromeDriverManager().install())
        self.lobbyist_driver = webdriver.Chrome(service=self.service, options=self.options)
        self.pagination_driver = webdriver.Chrome(service=self.service, options=self.options)
        self.unique_attendees = set()

        self.lobbyfacts_url = os.getenv("LOBBYFACTS_URL")
        self.comission_start = datetime(2019, 12, 1)
        self.comission_end = datetime(2024, 10, 31)


    def _get_lobbyist_links(self):
        # Get current page HTML
        page_source = self.pagination_driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # The lobbyist links are in the main table on the page
        lobbyists_table = soup.find(id='results-container').find('table')
        lobbyist_links = []

        # Check if the table was found
        if not lobbyists_table:
            print("Could not find the lobbyists table on the page.")
            return lobbyist_links

        # Loop through the table, looking for links to lobbyists
        rows = lobbyists_table.find('tbody').find_all('tr')
        for row in rows:
            link_tag = row.find('a', href=True)
            if link_tag:
                lobbyist_name = link_tag.get_text(strip=True)
                if lobbyist_name == "Name":
                    continue
                lobbyist_href = link_tag['href']
                lobbyist_url = f'{self.lobbyfacts_url}{lobbyist_href}'
                lobbyist_links.append((lobbyist_name, lobbyist_url))
                continue
        return lobbyist_links


    def _process_lobbyist(self, lobbyist_name, lobbyist_url, output_path):
        # Open lobbyist page with list of meetings using lobbyist_driver
        self.lobbyist_driver.get(lobbyist_url)

        soup = BeautifulSoup(self.lobbyist_driver.page_source, 'html.parser')

        # Find all meeting entries
        meetings = []
        meeting_tables = soup.find_all('table', class_='unstriped meetings')
        if not meeting_tables:
            print(f"No meetings found for {lobbyist_name}")
            return

        # Extract meetings and attendees
        for table in meeting_tables:
            rows = table.find_all('tr')
            meeting_attendees = []
            for row in rows:
                caption_cell = row.find('td', class_='table-caption')
                content_cell = row.find('td', class_='table-content')
                if content_cell:
                    # Extract meetings that correspond to desired commission dates only
                    if caption_cell.get_text(strip=True) == 'Date':
                        date_format = "%d %b %Y"
                        date_string = content_cell.get_text(strip=True)
                        parsed_date = datetime.strptime(date_string, date_format)
                        if parsed_date < self.comission_start or parsed_date > self.comission_end:
                            break
                    elif caption_cell.get_text(strip=True) == 'Attending':
                        attendees_list = content_cell.find_all('li')
                        for attendee in attendees_list:
                            attendee_name = attendee.get_text(strip=True)
                            self.unique_attendees.add(attendee_name)
                            meeting_attendees.append(attendee_name)
            if meeting_attendees:
                meetings.append(meeting_attendees)

        if meetings:
            # Clean lobbyist name for filename
            safe_filename = "".join(c for c in lobbyist_name if c.isalpha() or c.isdigit() or c in (' ', '_', '.')).rstrip()
            data = {"meetings": meetings}

            # Save all meetings to lobbyist JSON
            with open(path.join(output_path, f"{safe_filename}.json"), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Saved {len(meetings)} meetings for {lobbyist_name}")
        else:
            print(f"No meetings with attendees found for {lobbyist_name}")


    def _next_button_click(self):
        # Try to find the 'next' button
        next_button = self.pagination_driver.find_element(By.CSS_SELECTOR, 'li.pagination-next a')
        if next_button:
            # Scroll to the 'next' button and click it
            self.pagination_driver.execute_script("arguments[0].scrollIntoView();", next_button)
            next_button.click()
            return True
        else:
            print("No more pages to process.")
            return False


    def scrape(self, output_path=os.getenv("MEETINGS_PATH")):
        # Open main page with lists of lobbyists using pagination_driver
        self.pagination_driver.get(self.lobbyfacts_url)

        page_number = 1
        lobbyist_number = 1
        while True:
            print(f"Processing lobbyists on page {page_number}")
            lobbyist_links = self._get_lobbyist_links()

            # Process each lobbyist on the page using lobbyist_driver
            for name, url in lobbyist_links:
                print(f"{lobbyist_number}. Processing lobbyist: {name}")
                self._process_lobbyist(name, url, output_path)
                lobbyist_number += 1

            try:
                # Click the 'next' button if exists
                if not self._next_button_click():
                    break
                page_number += 1
            except Exception as e:
                print(e)
                break

        # Save unique meetings attendees to separate JSON file for future processing
        data = {"unique_attendees": list(self.unique_attendees)}
        with open(path.join(output_path, f"unique_attendees.json"), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Saved {len(self.unique_attendees)} unique attendees")

        self.lobbyist_driver.quit()
        self.pagination_driver.quit()


# Example usage
if __name__ == "__main__":
    scraper = LobbyistMeetingsScraper()
    scraper.scrape()