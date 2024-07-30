# Import necessary libraries
import sys
import os
import re
sys.path.append("..")

# Import specific modules from libraries
import asyncio
from playwright.async_api import async_playwright, TimeoutError, Page
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from rich.console import Console
from dotenv import load_dotenv
import time

load_dotenv()

URL = 'https://www.founderspodcast.com/'

# Initializing console for logging
console = Console()

# Defining the scraper class
class FoundersScraper:
    async def initialize_browser(self):

        def extract_date_and_episode(input_string):
            # Regular expression pattern to match the date and episode number
            pattern = r"([A-Z]+ \d+TH, \d{4}) \| E(\d+)"
            match = re.search(pattern, input_string)
            
            if match:
                date = match.group(1)
                episode_number = match.group(2)
                return date, episode_number
            else:
                # Return None if the pattern does not match
                return None, None
        
        
        try:
            console.log("Initialization of Browser...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            await self.page.goto(URL)

            list_selector = "div.q-list > div > div"

            await self.page.wait_for_selector(list_selector)

            episode_list = await self.page.query_selector_all(list_selector)

            current_index: int = 0
            visited = set()
            page_number = 1
            new_url = URL + f"?prod-episode-release-desc%5Bpage%5D={page_number}"

            while current_index <= len(episode_list):

                await self.page.wait_for_selector(list_selector)
                episode_list = await self.page.query_selector_all(list_selector)

                # console.log("finding episode")

                # console.log("episode_list length: ", len(episode_list), "current_index: ", current_index)

                episode = episode_list[current_index]
                
                await episode.wait_for_element_state("visible")
                await episode.click()
                
                # console.log("Clicked on the episode")
                # time.sleep(1)

                # Get the data from the episode page
                episode_name = await self.page.inner_text("#q-app > div > div > main > div > div.col-12.col-sm-12.col-md-10 > div > div.col-12.col-sm-10.q-pl-sm.q-py-md > div.q-pt-sm > span")
                # console.log(f"episode_name: {episode_name}")

                if episode_name in visited:
                    current_index += 1
                    break
                else:   
                    date_and_epidode_number = await self.page.inner_text("#q-app > div > div > main > div > div.col-12.col-sm-12.col-md-10 > div > div.col-12.col-sm-10.q-pl-sm.q-py-md > div:nth-child(3) > span")
                    date, episode_number = extract_date_and_episode(date_and_epidode_number)
                    # console.log(f"date: {date}, episode_number: {episode_number}")

                    
                    page_url = self.page.url
                    # console.log(f"page_url: {page_url}")

                    apple_url = await self.page.get_attribute("#q-app > div > div > main > div > div.col-12.col-sm-12.col-md-10 > div > div.col-12.col-sm-10.q-pl-sm.q-py-md > div.q-px-sm > div > div:nth-child(2) > a", "href")
                    # console.log(f"apple_url: {apple_url}")
                                                        
                    spotify_url = await self.page.get_attribute("#q-app > div > div > main > div > div.col-12.col-sm-12.col-md-10 > div > div.col-12.col-sm-10.q-pl-sm.q-py-md > div.q-px-sm > div > div:nth-child(3) > a", "href")
                    # console.log(f"spotify_url: {spotify_url}")
                    

                    episode_dict = {
                        "episode_name": episode_name,
                        "description": "",
                        "episode_id":"",
                        "episode_number": episode_number,
                        "episode_date": date,
                        
                        "page_url": page_url,
                        "youtube_url": "",
                        "apple_url": apple_url,
                        "spotify_url": spotify_url,
                    }
                    # print(episode_dict)
                    console.log(episode_dict)   
                    
                if current_index == len(episode_list) - 1:
                    current_index = 0
                    page_number += 1
                else:
                    current_index += 1
                new_url = URL + f"?prod-episode-release-desc%5Bpage%5D={page_number}"
                await self.page.goto(new_url)
                    
                visited.add(episode_name)

        
        except Exception as e:
            console.log(f"Error during browser initialization: {e}")
            raise


    async def scrape(self):
        try:
            await self.initialize_browser()
        except Exception as e:
            console.log(f"Error during scraping: {e}")
        finally:
            if hasattr(self, 'browser'):
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()


if __name__ == "__main__":
    scraper = FoundersScraper()
    asyncio.run(scraper.scrape())