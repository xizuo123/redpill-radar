import asyncio
from twikit import Client

async def main():
    client = Client('en-US')
    client.load_cookies('cookies.json')
    tweets = await client.search_tweet('test', 'Latest')
    tweet = tweets[0]
    print("Tweet attributes:", [a for a in dir(tweet) if not a.startswith('_')])
    print("User attributes:", [a for a in dir(tweet.user) if not a.startswith('_')])
    print("Screen name:", getattr(tweet.user, 'screen_name', 'Not found'))
    print("Name:", getattr(tweet.user, 'name', 'Not found'))

asyncio.run(main())
