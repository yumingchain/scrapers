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

URL = 'https://podcasts.apple.com/us/podcast/acquired/id1050462261'

# Initializing console for logging
console = Console()

# Defining the scraper class
class PodcastScraper:

    async def initialize_browser(self):

        def extract_rating(rating_string):
            # Use a regular expression to match the rating at the beginning of the string
            match = re.match(r'(\d+\.\d+)', rating_string)
            if match:
                return match.group(1)
            return None

        async def click_load_more(self):
            
            # Defining the selector for the 'Load More Episodes' button
            # button = self.page.frame_locator("body > div:nth-child(3) > div > div.html-embed.w-embed.w-iframe > iframe").get_by_text("Load More Episodes")
            button = self.page.locator("body > div.ember-view > main > div.animation-wrapper.is-visible > div > section:nth-child(1) > div > div.l-column.small-12.medium-7.large-8.small-valign-top > div.product-hero__tracks > div > div > button")
            console.log("button: ", button)
    
            # Continue clicking the "Load More" button as long as it is visible
            while True:
                try:
                    button = self.page.locator("body > div.ember-view > main > div.animation-wrapper.is-visible > div > section:nth-child(1) > div > div.l-column.small-12.medium-7.large-8.small-valign-top > div.product-hero__tracks > div > div > button")
                    if button.is_visible():
                        await button.click()
                        await self.page.wait_for_timeout(3000)  # Adjust the wait time as needed
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

            #Loading all episodes
            await click_load_more(self)

            
            # Scraping
            podcast_name = await self.page.inner_text("body > div.ember-view > main > div.animation-wrapper.is-visible > div > section:nth-child(1) > div > div.l-column.small-12.medium-7.large-8.small-valign-top > div.l-row > div.l-column.small-7.medium-12.small-valign-top > header > h1 > span.product-header__title")
            #console.log(f"Podcast name: {podcast_name}")    
            
            host = await self.page.inner_text("body > div.ember-view > main > div.animation-wrapper.is-visible > div > section:nth-child(1) > div > div.l-column.small-12.medium-7.large-8.small-valign-top > div.l-row > div.l-column.small-7.medium-12.small-valign-top > header > h1 > span.product-header__identity.podcast-header__identity")
            #console.log(f"Host: {host}")
            
            description = await self.page.inner_text("body > div.ember-view > main > div.animation-wrapper.is-visible > div > section:nth-child(1) > div > div.l-column.small-12.medium-7.large-8.small-valign-top > div.l-row > div.l-column.small-7.medium-12.small-valign-top > header > ul > li:nth-child(1) > ul")
            #console.log(f"Description: {description}")

            rating_string = await self.page.inner_text("body > div.ember-view > main > div.animation-wrapper.is-visible > div > section:nth-child(1) > div > div.l-column.small-12.medium-7.large-8.small-valign-top > div.l-row > div.l-column.small-7.medium-12.small-valign-top > header > ul > li:nth-child(2) > ul > li > figure > figcaption")

            podcast_rating = extract_rating(rating_string)
            console.log(f"Podcast rating: {podcast_rating}")

            page_url = self.page.url


            #Looping through the episodes and getting episode info
            for i in range(1, 194):
                print(f"Episode {i}")
                episode_locator = self.page.locator(f"body > div.ember-view > main > div.animation-wrapper.is-visible > div > section:nth-child(1) > div > div.l-column.small-12.medium-7.large-8.small-valign-top > div.product-hero__tracks > div > ol > li:nth-child({i})")
                episode_name_locator = episode_locator.locator("> div > div > h2 > span > div")
                episode_duration_locator = episode_locator.locator("> div > div > ul.tracks__track__meta.inline-list.inline-list--truncate-single-line.tracks__track__subcopy.tracks__track__meta--has-button > li.inline-list__item.inline-list__item--margin-inline-start-small")
                episode_date_locator = episode_locator.locator("> div > div > ul.inline-list.inline-list--truncate-single-line.tracks__track__eyebrow > li > time")

                episode_name = await episode_name_locator.text_content()
                # console.log(f"Episode name: {episode_name}")
                episode_duration = await episode_duration_locator.text_content()
                # console.log(f"Episode duration: {episode_duration}")
                episode_date = await episode_date_locator.text_content()
                # console.log(f"Episode date: {episode_date}")

                #outputing info
                episode_dict = {
                    "podcast_name": podcast_name,
                    "podcast_rating": podcast_rating,
                    "episode_name": episode_name,
                    "episode_number": "",
                    "episode_duration": episode_duration,
                    "host": host,
                    "episode_date": episode_date,
                    "description": description,
                    "episode_id":"",
                    
                    "page_url": page_url,
                    "youtube_url": "",
                    "apple_url": "",
                    "spotify_url": "",
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