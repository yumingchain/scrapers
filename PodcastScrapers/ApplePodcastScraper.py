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

# Initializing console for logging
console = Console()

# Defining the scraper class
class PodcastScraper:

    async def initialize_scraper(self):

        async def extract_podcast_urls(page_url):
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(page_url)

                # Extract all Apple Podcast URLs from the page
                podcast_urls = await page.evaluate('''() => {
                    const links = Array.from(document.querySelectorAll('a'));
                    return [...new Set(links
                        .map(link => link.href)
                        .filter(href => href.includes('podcasts.apple.com')))];
                }''')

                await browser.close()
                return podcast_urls

        def extract_rating(rating_string):
            # Use a regular expression to match the rating at the beginning of the string
            match = re.match(r'(\d+\.\d+)', rating_string)
            if match:
                return match.group(1)
            return None

        async def click_load_more(self):
            # Defining the selector for the 'Load More Episodes' button
            button_selector = "body > div.ember-view > main > div.animation-wrapper.is-visible > div > section:nth-child(1) > div > div.l-column.small-12.medium-7.large-8.small-valign-top > div.product-hero__tracks > div > div > button"
            button = self.page.locator(button_selector)

            # Continue clicking the "Load More" button as long as it is visible
            while True:
                try:
                    if await button.is_visible():
                        await button.click()
                        await self.page.wait_for_timeout(3000)  # Adjust the wait time as needed
                    else:
                        break
                except Exception as e:
                    print(f"An error occurred: {e}")
                    break

        def extract_number_of_episodes(text):
            # Use a regular expression to match the number at the beginning of the string, including commas
            match = re.match(r'([\d,]+)', text)
            if match:
                # Remove commas and convert the result to an integer
                return int(match.group(1).replace(',', ''))
            return None

        try:
            page_url = 'https://www.podcastinsights.com/top-us-podcasts/'
            podcast_urls = await extract_podcast_urls(page_url)
            for index, URL in enumerate(podcast_urls, start=1):
                print(f"{index}: {URL}")

            console.print("Initialization of Browser...")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()

            for index, URL in enumerate(podcast_urls, start=1):
                console.print(f"Scraping commenced for: {URL}")
                await self.page.goto(URL)

                # Loading all episodes
                await click_load_more(self)

                # Scraping
                podcast_name = await self.page.inner_text("body > div.ember-view > main > div.animation-wrapper.is-visible > div > section:nth-child(1) > div > div.l-column.small-12.medium-7.large-8.small-valign-top > div.l-row > div.l-column.small-7.medium-12.small-valign-top > header > h1 > span.product-header__title")

                host = await self.page.inner_text("body > div.ember-view > main > div.animation-wrapper.is-visible > div > section:nth-child(1) > div > div.l-column.small-12.medium-7.large-8.small-valign-top > div.l-row > div.l-column.small-7.medium-12.small-valign-top > header > h1 > span.product-header__identity.podcast-header__identity")

                description = await self.page.inner_text("body > div.ember-view > main > div.animation-wrapper.is-visible > div > section:nth-child(1) > div > div.l-column.small-12.medium-7.large-8.small-valign-top > div.l-row > div.l-column.small-7.medium-12.small-valign-top > header > ul > li:nth-child(1) > ul")

                number_of_episodes_text = await self.page.inner_text("body > div.ember-view > main > div.animation-wrapper.is-visible > div > section:nth-child(1) > div > div.l-column.medium-5.large-4.small-valign-top.small-hide.medium-show-inlineblock > div.product-artwork__caption.small-hide.medium-show > p")
                number_of_episodes = extract_number_of_episodes(number_of_episodes_text)
                console.print(f"Number of episodes: {number_of_episodes}")

                rating_string = await self.page.inner_text("body > div.ember-view > main > div.animation-wrapper.is-visible > div > section:nth-child(1) > div > div.l-column.small-12.medium-7.large-8.small-valign-top > div.l-row > div.l-column.small-7.medium-12.small-valign-top > header > ul > li:nth-child(2) > ul > li > figure > figcaption")

                podcast_rating = extract_rating(rating_string)
                page_url = self.page.url

                # Looping through the episodes and getting episode info
                for i in range(1, number_of_episodes + 1):
                    console.print(f"Episode {i}")
                    episode_locator = self.page.locator(f"body > div.ember-view > main > div.animation-wrapper.is-visible > div > section:nth-child(1) > div > div.l-column.small-12.medium-7.large-8.small-valign-top > div.product-hero__tracks > div > ol > li:nth-child({i})")
                    episode_name_locator = episode_locator.locator("> div > div > h2 > span > div")
                    episode_duration_locator = episode_locator.locator("> div > div > ul.tracks__track__meta.inline-list.inline-list--truncate-single-line.tracks__track__subcopy.tracks__track__meta--has-button > li.inline-list__item.inline-list__item--margin-inline-start-small")
                    episode_date_locator = episode_locator.locator("> div > div > ul.inline-list.inline-list--truncate-single-line.tracks__track__eyebrow > li > time")

                    episode_name = await episode_name_locator.text_content() if await episode_name_locator.count() > 0 else ""
                    episode_duration = await episode_duration_locator.text_content() if await episode_duration_locator.count() > 0 else ""
                    episode_date = await episode_date_locator.text_content() if await episode_date_locator.count() > 0 else ""

                    # Outputting info
                    episode_dict = {
                        "podcast_name": podcast_name,
                        "podcast_rating": podcast_rating,
                        "number_of_episodes": number_of_episodes,
                        "episode_name": episode_name,
                        "episode_number": i,
                        "episode_duration": episode_duration,
                        "host": host,
                        "episode_date": episode_date,
                        "description": description,
                        "episode_id": "",
                        "page_url": page_url,
                        "youtube_url": "",
                        "apple_url": "",
                        "spotify_url": "",
                    }
                    console.print(episode_dict)

                console.print(f"Scraping completed for Podcast Number {index}: {podcast_name}")

        except Exception as e:
            console.print(f"Error during browser initialization: {e}")
            raise

    async def scrape(self):
        try:
            await self.initialize_scraper()
        except Exception as e:
            console.print(f"Error during scraping: {e}")
        finally:
            if hasattr(self, 'browser'):
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()

if __name__ == "__main__":
    scraper = PodcastScraper()
    asyncio.run(scraper.scrape())
