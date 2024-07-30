import sys
import os
import re
sys.path.append("..")

import asyncio
from playwright.async_api import async_playwright, TimeoutError, Page
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from rich.console import Console
from dotenv import load_dotenv
import time

load_dotenv()

URL = 'https://www.stitcherstudios.com/shows/99-invisible'

# Initializing console for logging
console = Console()

# Defining the scraper class
class PodcastScraper:

    async def initialize_browser(self):

        async def click_load_more(self):
            
            # Defining the selector for the 'Load More Episodes' button
            button = self.page.frame_locator("body > div:nth-child(3) > div > div.html-embed.w-embed.w-iframe > iframe").get_by_text("Load More Episodes")
            console.log("button: ", button)
    
            # Continue clicking the "Load More" button as long as it is visible
            while True:
                try:
                    button = self.page.frame_locator("body > div:nth-child(3) > div > div.html-embed.w-embed.w-iframe > iframe").get_by_text("Load More Episodes")
                    if button.is_visible():
                        await button.click()
                        await self.page.wait_for_timeout(1000)  # Adjust the wait time as needed
                    else:
                        break
                except:
                    break
            
        try:
            console.log("Initialization of Browser...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=False)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            await self.page.goto(URL)

            
            # Scraping
            podcast_name = await self.page.inner_text("body > div.section.show-page-hero > div > div > div.show-page-text-div > h1")
            host = await self.page.inner_text("body > div:nth-child(3) > div > div.div-block-32 > div:nth-child(3) > div.person > div > p")
            
            spotify_url = await self.page.get_attribute("body > div.section.show-page-hero > div > div > div.show-page-text-div > div.subscribe-buttons-div > div > a:nth-child(5)", "href")
            apple_url = await self.page.get_attribute("body > div.section.show-page-hero > div > div > div.show-page-text-div > div.subscribe-buttons-div > div > a:nth-child(3)", "href")
            page_url = self.page.url

            #Loading all episodes
            await click_load_more(self)
            # await self.page.wait_for_timeout(20000)  # Adjust the wait time as needed

            #Defining iframe locator
            frame_locator = self.page.frame_locator("body > div:nth-child(3) > div > div.html-embed.w-embed.w-iframe > iframe")

            #Looping through the episodes and getting episode info
            for i in range(1, 667):
                print(f"Episode {i}")
                episode_locator = frame_locator.locator(f"body > div > div > div > div > div.episodes > div > button:nth-child({i})")
                episode_number_locator = episode_locator.locator("span.number")
                episode_name_locator = episode_locator.locator("span.title > div")
                episode_duration_locator = episode_locator.locator("span.duration")

                episode_number = await episode_number_locator.text_content()
                # console.log(f"Episode number: {episode_number}")
                episode_name = await episode_name_locator.text_content()
                # console.log(f"Episode name: {episode_name}")
                episode_duration = await episode_duration_locator.text_content()
                # console.log(f"Episode duration: {episode_duration}")

                #outputing info
                episode_dict = {
                    "podcast_name": podcast_name,
                    "episode_name": episode_name,
                    "episode_number": episode_number,
                    "episode_duration": episode_duration,
                    "host": host,
                    "episode_date": "",
                    "description": "",
                    "episode_id":"",
                    
                    "page_url": page_url,
                    "youtube_url": "",
                    "apple_url": apple_url,
                    "spotify_url": spotify_url,
                }
                # print(episode_dict)
                console.log(episode_dict)

        
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
    scraper = PodcastScraper()
    asyncio.run(scraper.scrape())