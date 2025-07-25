"""
Website Ingest Agent
Handles web scraping, content extraction, and initial processing
"""

import asyncio
import aiohttp
import hashlib
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import feedparser
from bs4 import BeautifulSoup
import trafilatura
from newspaper import Article
from loguru import logger

from ..config.settings import settings
from ..models.database import Website, ContentItem, ScrapingJob
from ..models.schemas import ContentItemCreate
from ..core.database import get_db
from ..utils.text_processor import TextProcessor


class WebsiteIngestAgent:
    """
    Agent responsible for scraping and ingesting content from websites
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.text_processor = TextProcessor()
        self.scraped_urls = set()  # Track URLs scraped in current session
        
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=settings.scraping.timeout)
        connector = aiohttp.TCPConnector(limit=settings.scraping.concurrent_requests)
        
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=connector,
            headers={
                'User-Agent': settings.scraping.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def scrape_website(self, website: Website) -> Dict[str, Any]:
        """
        Scrape a single website and extract content
        
        Args:
            website: Website model instance
            
        Returns:
            Dict with scraping results and statistics
        """
        logger.info(f"Starting scrape for website: {website.url}")
        
        results = {
            'website_id': website.id,
            'website_url': str(website.url),
            'status': 'pending',
            'items_found': 0,
            'items_scraped': 0,
            'items_failed': 0,
            'errors': [],
            'started_at': datetime.utcnow()
        }
        
        try:
            # Determine scraping strategy based on website type
            if self._is_rss_feed(str(website.url)):
                content_items = await self._scrape_rss_feed(website)
            else:
                content_items = await self._scrape_website_pages(website)
            
            results['items_found'] = len(content_items)
            
            # Process and save content items
            db = next(get_db())
            try:
                for item_data in content_items:
                    try:
                        content_item = await self._process_and_save_content(item_data, website, db)
                        if content_item:
                            results['items_scraped'] += 1
                    except Exception as e:
                        logger.error(f"Failed to process content item: {e}")
                        results['items_failed'] += 1
                        results['errors'].append(str(e))
                
                results['status'] = 'completed'
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Website scraping failed for {website.url}: {e}")
            results['status'] = 'failed'
            results['errors'].append(str(e))
        
        results['completed_at'] = datetime.utcnow()
        logger.info(f"Scraping completed for {website.url}. Results: {results}")
        
        return results
    
    async def _scrape_rss_feed(self, website: Website) -> List[Dict[str, Any]]:
        """Scrape content from RSS/Atom feeds"""
        try:
            async with self.session.get(str(website.url)) as response:
                content = await response.text()
                
            feed = feedparser.parse(content)
            content_items = []
            
            for entry in feed.entries:
                # Extract basic information from feed entry
                item_data = {
                    'url': entry.get('link', ''),
                    'title': entry.get('title', ''),
                    'content': entry.get('description', '') or entry.get('summary', ''),
                    'author': entry.get('author', ''),
                    'published_date': self._parse_date(entry.get('published'))
                }
                
                # If we have a link, try to get the full content
                if item_data['url'] and item_data['url'] not in self.scraped_urls:
                    full_content = await self._extract_full_content(item_data['url'])
                    if full_content:
                        item_data['content'] = full_content
                    
                    self.scraped_urls.add(item_data['url'])
                    content_items.append(item_data)
                    
                    # Rate limiting
                    await asyncio.sleep(settings.scraping.delay)
            
            return content_items
            
        except Exception as e:
            logger.error(f"RSS feed scraping failed for {website.url}: {e}")
            return []
    
    async def _scrape_website_pages(self, website: Website) -> List[Dict[str, Any]]:
        """Scrape content from regular website pages"""
        content_items = []
        
        try:
            # First, try to find article links on the main page
            article_urls = await self._discover_article_urls(str(website.url), website.selector_config)
            
            # Process discovered URLs
            for url in article_urls[:20]:  # Limit to 20 articles per run
                if url not in self.scraped_urls:
                    try:
                        item_data = await self._scrape_single_article(url)
                        if item_data:
                            content_items.append(item_data)
                            self.scraped_urls.add(url)
                        
                        # Rate limiting
                        await asyncio.sleep(settings.scraping.delay)
                        
                    except Exception as e:
                        logger.error(f"Failed to scrape article {url}: {e}")
            
        except Exception as e:
            logger.error(f"Website page scraping failed for {website.url}: {e}")
        
        return content_items
    
    async def _discover_article_urls(self, base_url: str, selector_config: Optional[Dict]) -> List[str]:
        """Discover article URLs from a website's main page or sitemap"""
        urls = set()
        
        try:
            # Try to get URLs from the main page
            async with self.session.get(base_url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
            # Use custom selectors if provided
            if selector_config and 'article_links' in selector_config:
                links = soup.select(selector_config['article_links'])
            else:
                # Default selectors for common article link patterns
                selectors = [
                    'article a[href]',
                    '.post a[href]',
                    '.entry a[href]',
                    'h1 a[href]', 'h2 a[href]', 'h3 a[href]',
                    'a[href*="article"]',
                    'a[href*="post"]',
                    'a[href*="blog"]'
                ]
                
                links = []
                for selector in selectors:
                    links.extend(soup.select(selector))
            
            # Extract and normalize URLs
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if self._is_valid_article_url(full_url, base_url):
                        urls.add(full_url)
            
            # Try sitemap if not enough URLs found
            if len(urls) < 5:
                sitemap_urls = await self._get_sitemap_urls(base_url)
                urls.update(sitemap_urls)
            
        except Exception as e:
            logger.error(f"URL discovery failed for {base_url}: {e}")
        
        return list(urls)
    
    async def _scrape_single_article(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape a single article using multiple extraction methods"""
        try:
            async with self.session.get(url) as response:
                html = await response.text()
            
            # Method 1: Try trafilatura (best for article extraction)
            content = trafilatura.extract(html, include_comments=False, include_tables=True)
            
            # Method 2: Fallback to newspaper3k
            if not content or len(content) < 100:
                article = Article(url)
                article.set_html(html)
                article.parse()
                content = article.text
                
                # Use newspaper's metadata if available
                title = article.title or ''
                author = ', '.join(article.authors) if article.authors else ''
                published_date = article.publish_date
            else:
                # Extract metadata from HTML
                soup = BeautifulSoup(html, 'html.parser')
                title = self._extract_title(soup)
                author = self._extract_author(soup)
                published_date = self._extract_published_date(soup)
            
            if content and len(content.strip()) >= settings.content.min_text_length:
                return {
                    'url': url,
                    'title': title,
                    'content': content,
                    'author': author,
                    'published_date': published_date
                }
            
        except Exception as e:
            logger.error(f"Article scraping failed for {url}: {e}")
        
        return None
    
    async def _extract_full_content(self, url: str) -> Optional[str]:
        """Extract full content from a URL"""
        try:
            async with self.session.get(url) as response:
                html = await response.text()
                
            # Use trafilatura for content extraction
            content = trafilatura.extract(html, include_comments=False, include_tables=True)
            return content
            
        except Exception as e:
            logger.error(f"Content extraction failed for {url}: {e}")
            return None
    
    async def _process_and_save_content(self, item_data: Dict[str, Any], website: Website, db) -> Optional[ContentItem]:
        """Process extracted content and save to database"""
        try:
            # Skip if URL is empty or invalid
            if not item_data.get('url'):
                return None
            
            # Check if content already exists
            content_hash = self._generate_content_hash(item_data.get('content', ''))
            existing_item = db.query(ContentItem).filter(
                ContentItem.content_hash == content_hash
            ).first()
            
            if existing_item:
                logger.debug(f"Content already exists: {item_data['url']}")
                return existing_item
            
            # Clean and process content
            cleaned_content = self.text_processor.clean_text(item_data.get('content', ''))
            
            # Skip if content is too short after cleaning
            if len(cleaned_content) < settings.content.min_text_length:
                logger.debug(f"Content too short after cleaning: {item_data['url']}")
                return None
            
            # Create content item
            content_item = ContentItem(
                website_id=website.id,
                url=item_data['url'],
                title=item_data.get('title', ''),
                content=item_data.get('content', ''),
                cleaned_content=cleaned_content,
                author=item_data.get('author', ''),
                published_date=item_data.get('published_date'),
                content_hash=content_hash,
                word_count=len(cleaned_content.split()),
                language=self.text_processor.detect_language(cleaned_content),
                scraped_at=datetime.utcnow()
            )
            
            db.add(content_item)
            db.commit()
            db.refresh(content_item)
            
            logger.info(f"Saved content item: {content_item.id} - {content_item.title}")
            return content_item
            
        except Exception as e:
            logger.error(f"Failed to process and save content: {e}")
            db.rollback()
            return None
    
    def _is_rss_feed(self, url: str) -> bool:
        """Check if URL appears to be an RSS/Atom feed"""
        url_lower = url.lower()
        rss_indicators = ['/rss', '/feed', '/atom', '.rss', '.xml', 'feed.xml', 'rss.xml']
        return any(indicator in url_lower for indicator in rss_indicators)
    
    def _is_valid_article_url(self, url: str, base_url: str) -> bool:
        """Check if URL is a valid article URL"""
        parsed_url = urlparse(url)
        parsed_base = urlparse(base_url)
        
        # Must be from the same domain
        if parsed_url.netloc != parsed_base.netloc:
            return False
        
        # Skip common non-article paths
        skip_patterns = [
            '/tag/', '/category/', '/author/', '/page/',
            '/wp-admin/', '/wp-content/', '/search',
            '#', 'javascript:', 'mailto:', 'tel:'
        ]
        
        url_lower = url.lower()
        return not any(pattern in url_lower for pattern in skip_patterns)
    
    async def _get_sitemap_urls(self, base_url: str) -> List[str]:
        """Try to get URLs from sitemap"""
        sitemap_urls = [
            urljoin(base_url, '/sitemap.xml'),
            urljoin(base_url, '/sitemap_index.xml'),
            urljoin(base_url, '/robots.txt')  # Check robots.txt for sitemap
        ]
        
        urls = set()
        
        for sitemap_url in sitemap_urls:
            try:
                async with self.session.get(sitemap_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        if 'sitemap' in sitemap_url.lower():
                            # Parse sitemap XML
                            soup = BeautifulSoup(content, 'xml')
                            for loc in soup.find_all('loc'):
                                urls.add(loc.text.strip())
                        else:
                            # Parse robots.txt for sitemap references
                            for line in content.split('\n'):
                                if line.lower().startswith('sitemap:'):
                                    sitemap_ref = line.split(':', 1)[1].strip()
                                    urls.add(sitemap_ref)
                
            except Exception as e:
                logger.debug(f"Could not fetch sitemap {sitemap_url}: {e}")
        
        return list(urls)[:50]  # Limit sitemap URLs
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from HTML"""
        # Try multiple selectors
        selectors = ['h1', 'title', '.entry-title', '.post-title', '.article-title']
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return ''
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author from HTML metadata"""
        # Try meta tags first
        author_meta = soup.find('meta', {'name': 'author'}) or soup.find('meta', {'property': 'article:author'})
        if author_meta:
            return author_meta.get('content', '')
        
        # Try common author selectors
        selectors = ['.author', '.byline', '.post-author', '[rel="author"]']
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return ''
    
    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract published date from HTML metadata"""
        # Try meta tags
        date_meta = soup.find('meta', {'property': 'article:published_time'}) or \
                   soup.find('meta', {'name': 'publish_date'}) or \
                   soup.find('meta', {'name': 'date'})
        
        if date_meta:
            date_str = date_meta.get('content', '')
            return self._parse_date(date_str)
        
        # Try time elements
        time_element = soup.find('time')
        if time_element:
            datetime_attr = time_element.get('datetime')
            if datetime_attr:
                return self._parse_date(datetime_attr)
        
        return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            # Try common date formats
            from dateutil.parser import parse
            return parse(date_str)
        except:
            return None
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash for content deduplication"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


async def run_scheduled_scraping():
    """Run scheduled scraping for all active websites"""
    logger.info("Starting scheduled scraping job")
    
    db = next(get_db())
    try:
        # Get websites that need scraping
        cutoff_time = datetime.utcnow() - timedelta(hours=1)  # Default check interval
        
        websites = db.query(Website).filter(
            Website.is_active == True,
            Website.scraping_enabled == True,
            (Website.last_scraped.is_(None) | (Website.last_scraped < cutoff_time))
        ).all()
        
        logger.info(f"Found {len(websites)} websites to scrape")
        
        async with WebsiteIngestAgent() as agent:
            for website in websites:
                try:
                    # Create scraping job record
                    job = ScrapingJob(
                        website_id=website.id,
                        job_type="scheduled",
                        status="running",
                        started_at=datetime.utcnow()
                    )
                    db.add(job)
                    db.commit()
                    
                    # Run scraping
                    results = await agent.scrape_website(website)
                    
                    # Update job status
                    job.status = results['status']
                    job.completed_at = results['completed_at']
                    job.items_scraped = results['items_scraped']
                    job.items_failed = results['items_failed']
                    
                    if results['errors']:
                        job.error_message = '; '.join(results['errors'][:3])  # First 3 errors
                    
                    # Update website last_scraped
                    website.last_scraped = datetime.utcnow()
                    
                    db.commit()
                    
                except Exception as e:
                    logger.error(f"Scraping failed for website {website.id}: {e}")
                    db.rollback()
    
    finally:
        db.close()
    
    logger.info("Scheduled scraping job completed")
