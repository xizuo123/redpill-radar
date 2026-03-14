import asyncio
import os
import logging
from twikit import Client
from typing import List, Dict

logger = logging.getLogger(__name__)

class TwitterScraper:
    def __init__(self, cookies_file='cookies.json'):
        self.client = Client('en-US')
        self.cookies_file = cookies_file
        self.username = os.getenv('TWITTER_USERNAME')
        self.email = os.getenv('TWITTER_EMAIL')
        self.password = os.getenv('TWITTER_PASSWORD')

    async def login(self):
        """
        Logs in to Twitter. Attempts to use cookies first, falls back to credentials.
        """
        logger.info(f"Attempting login for user: {self.username}")
        try:
            if os.path.exists(self.cookies_file):
                logger.info("Loading existing cookies...")
                self.client.load_cookies(self.cookies_file)
            else:
                logger.info("No cookies found. Logging in with credentials...")
                if not all([self.username, self.email, self.password]):
                    raise ValueError("Twitter credentials are not fully set in the environment variables.")

                await self.client.login(
                    auth_info_1=self.username,
                    auth_info_2=self.email,
                    password=self.password
                )
                self.client.save_cookies(self.cookies_file)
                logger.info("Successfully logged in and saved cookies.")
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise

    async def search_content(self, keywords: List[str], max_tweets: int = 50) -> List[Dict[str, str]]:
        """
        Searches for specific keywords and formats the results.
        """
        all_results = []
        
        for keyword in keywords:
            logger.info(f"Searching for keyword: '{keyword}'")
            try:
                logger.info(f"Sending search request for '{keyword}'...")
                # Get initial batch of tweets, filtering for English only
                search_query = f"{keyword} lang:en"
                tweets = await self.client.search_tweet(search_query, 'Latest')
                logger.info(f"Successfully retrieved results for '{keyword}'")
                
                count = 0
                while tweets and count < max_tweets:
                    for tweet in tweets:
                        if count >= max_tweets:
                            break
                        
                        # Format the output as required
                        # twikit Tweet object has .id and .text
                        formatted_tweet = {
                            "id": str(tweet.id),
                            "text": tweet.text
                        }
                        
                        # Add to results if we haven't seen this ID yet to prevent duplicates across keyword searches
                        if not any(t['id'] == formatted_tweet['id'] for t in all_results):
                            all_results.append(formatted_tweet)
                            count += 1
                    
                    if count < max_tweets and tweets.next_cursor:
                        logger.debug("Fetching next page of tweets...")
                        tweets = await tweets.next()
                    else:
                        break
                        
            except Exception as e:
                logger.error(f"Error searching for '{keyword}': {e}")
                
        logger.info(f"Total unique tweets collected: {len(all_results)}")
        return all_results
