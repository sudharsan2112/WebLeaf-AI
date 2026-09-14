import asyncio
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from typing import Set
import hashlib

from .config import settings
from .extractor import Extractor
from .chunker import Chunker
from .embedder import Embedder
from .vector_store import VectorStore
from .database import upsert_kb
from .utils import get_logger

logger = get_logger(__name__)

class WebCrawler:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.kb_id = hashlib.md5(base_url.encode()).hexdigest()
        self.visited: Set[str] = set()
        self.queue = [(base_url, 0)]
        
        self.chunker = Chunker()
        self.embedder = Embedder()
        self.vector_store = VectorStore(self.kb_id)
        
        self.pages_crawled = 0
        self.chunks_created = 0
        
        self.base_domain = urlparse(base_url).netloc

    def is_valid_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.netloc != self.base_domain:
            return False
        if any(url.lower().endswith(ext) for ext in settings.IGNORE_EXTENSIONS):
            return False
        if parsed.scheme not in ["http", "https"]:
            return False
        if url.startswith("mailto:") or url.startswith("javascript:"):
            return False
        return True

    async def crawl(self):
        upsert_kb(self.kb_id, self.base_url, "crawling", 0, 0)
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                while self.queue and self.pages_crawled < settings.MAX_CRAWL_PAGES:
                    current_url, depth = self.queue.pop(0)
                    
                    if current_url in self.visited or depth > settings.MAX_CRAWL_DEPTH:
                        continue
                        
                    self.visited.add(current_url)
                    logger.info(f"Crawling: {current_url} (Depth: {depth})")
                    
                    try:
                        response = await page.goto(current_url, timeout=30000, wait_until="domcontentloaded")
                        if not response or response.status >= 400:
                            continue
                            
                        html = await page.content()
                        
                        extractor = Extractor(html, current_url)
                        doc = extractor.extract_content()
                        chunks = self.chunker.chunk_document(doc)
                        
                        if chunks:
                            texts = [c["text"] for c in chunks]
                            embeddings = await self.embedder.generate_embeddings(texts)
                            self.vector_store.add_embeddings(embeddings, chunks)
                            self.chunks_created += len(chunks)
                            
                        self.pages_crawled += 1
                        upsert_kb(self.kb_id, self.base_url, "crawling", self.pages_crawled, self.chunks_created)
                        
                        soup = BeautifulSoup(html, "lxml")
                        for a_tag in soup.find_all("a", href=True):
                            next_url = urljoin(current_url, a_tag["href"])
                            next_url = next_url.split("#")[0] # clean fragments
                            if self.is_valid_url(next_url) and next_url not in self.visited:
                                self.queue.append((next_url, depth + 1))
                                
                    except Exception as e:
                        logger.error(f"Error crawling {current_url}: {e}")
                
                await browser.close()
            
            upsert_kb(self.kb_id, self.base_url, "completed", self.pages_crawled, self.chunks_created)
            logger.info(f"Crawling completed for {self.base_url}")
            
        except Exception as e:
            upsert_kb(self.kb_id, self.base_url, "error", self.pages_crawled, self.chunks_created, str(e))
            logger.error(f"Crawl failed: {e}")

    @staticmethod
    def start_crawl_task(base_url: str) -> str:
        import threading
        import sys
        
        crawler = WebCrawler(base_url)
        
        def run_crawl():
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            asyncio.run(crawler.crawl())
            
        thread = threading.Thread(target=run_crawl, daemon=True)
        thread.start()
        return crawler.kb_id
