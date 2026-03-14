import os
import asyncio
import logging
from dotenv import load_dotenv

from scraper import TwitterScraper
from api_client import DataProcessorAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def main():
    # Define target content keywords
    env_keywords = os.getenv('SCRAPER_KEYWORDS')
    if env_keywords:
        search_keywords = [k.strip() for k in env_keywords.split(',')]
    else:
        search_keywords = [
            "manosphere",
            "incel",
            "women hating", # Note: Twitter search natively handles phrases with spaces
            "red pill"
        ]
    
    logger.info("Initializing TwitterScraper...")
    scraper = TwitterScraper()
    
    try:
        # Authenticate
        await scraper.login()
        
        # Scrape content
        max_t = int(os.getenv('MAX_TWEETS', 5))
        results = await scraper.search_content(search_keywords, max_tweets=max_t)
        
        if not results:
            logger.warning("No tweets found matching the criteria.")
            return

        # Initialize API client and push data
        api_client = DataProcessorAPI()
        
        logger.info(f"Preparing to push {len(results)} formatted tweets...")
        success = api_client.push_data(results)
        
        if success:
            logger.info("Workflow completed successfully.")
        else:
            logger.error("Data processing push failed.")

    except Exception as e:
        logger.error(f"Workflow aborted due to error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
