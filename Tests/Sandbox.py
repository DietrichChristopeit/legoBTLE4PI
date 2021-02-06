import asyncio
from random import uniform
from time import sleep


class Crawler:
    
    def __init__(self, urls, max_workers=10):
        self.urls = urls
        # create a queue that only allows a maximum of two items
        self.fetching = asyncio.Queue()
        self.max_workers = max_workers
    
    async def crawl(self):
        # DON'T await here; start consuming things out of the queue, and
        # meanwhile execution of this function continues. We'll start two
        # coroutines for fetching and two coroutines for processing.
        all_the_coros = asyncio.gather(
            *[self._worker(i) for i in range(self.max_workers)])
        
        # place all URLs on the queue
        for url in self.urls:
            await self.fetching.put(url)
        
        # now put a bunch of `None`'s in the queue as signals to the workers
        # that there are no more items in the queue.
        for _ in range(self.max_workers):
            await self.fetching.put(None)
        
        # now make sure everything is done
        await all_the_coros
    
    async def _worker(self, i):
        while True:
            url = await self.fetching.get()
            if url is None:
                # this coroutine is done; simply return to exit
                return
            
            print(f'Fetch worker {i} is fetching a URL: {url}')
            page = await asyncio.to_thread(self.fetch, url)
            await self.process(page, i)
    
    def fetch(self, url):
        print("Fetching URL: " + url)
        sleep(uniform(2.0, 5.0))
        return f"the contents of {url}"
    
    async def process(self, page, i):
        print(f'{i} processed page: {page}')


# main loop
c = Crawler(['http://www.google.com', 'http://www.yahoo.com',
             'http://www.cnn.com', 'http://www.gamespot.com',
             'http://www.facebook.com', 'http://www.evergreen.edu', 'http://www.ard.de', 'http://www.zdf.de'])
asyncio.run(c.crawl())