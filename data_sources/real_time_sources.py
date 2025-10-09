"""Real-time data sources for up-to-date CS/IT information."""

import logging
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import json
import time

logger = logging.getLogger(__name__)


class RealTimeDataSources:
    """Real-time data sources for current CS/IT information."""
    
    def __init__(self):
        """Initialize real-time data sources."""
        self.name = "Real-Time Data Sources"
        
        # RSS feeds for CS/IT news
        self.rss_feeds = {
            'hackernews': 'https://hnrss.org/frontpage',
            'reddit_programming': 'https://www.reddit.com/r/programming.rss',
            'reddit_machinelearning': 'https://www.reddit.com/r/MachineLearning.rss',
            'reddit_compsci': 'https://www.reddit.com/r/compsci.rss',
            'reddit_artificial': 'https://www.reddit.com/r/artificial.rss',
            'techcrunch': 'https://techcrunch.com/feed/',
            'arstechnica': 'https://feeds.arstechnica.com/arstechnica/index/',
            'wired': 'https://www.wired.com/feed/rss',
            'ieee_spectrum': 'https://spectrum.ieee.org/rss/fulltext',
            'acm_news': 'https://cacm.acm.org/rss/',
        }
        
        # API endpoints for real-time data
        self.api_endpoints = {
            'github_trending': 'https://api.github.com/search/repositories',
            'stackoverflow_questions': 'https://api.stackexchange.com/2.3/questions',
            'product_hunt': 'https://api.producthunt.com/v2/api/graphql',
        }
        
        logger.info(f"Initialized {self.name} with {len(self.rss_feeds)} RSS feeds")
    
    def fetch_rss_feed(self, feed_url: str, max_items: int = 10) -> List[Dict[str, Any]]:
        """Fetch items from an RSS feed."""
        try:
            feed = feedparser.parse(feed_url)
            items = []
            
            for entry in feed.entries[:max_items]:
                # Parse publication date
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6])
                
                item = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'summary': entry.get('summary', ''),
                    'published': pub_date,
                    'source': feed.feed.get('title', 'RSS Feed'),
                    'tags': [tag.term for tag in entry.get('tags', [])]
                }
                items.append(item)
            
            return items
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")
            return []
    
    def fetch_github_trending(self, topic: str = None, language: str = None, page: int = 1) -> List[Dict[str, Any]]:
        """Fetch GitHub repositories related to a topic with pagination support."""
        try:
            # GitHub API requires authentication for higher rate limits
            # This is a simplified version
            url = "https://api.github.com/search/repositories"
            
            # Build query - just search for topic like ArXiv does
            query_parts = []
            
            if topic:
                # Add topic to search query
                query_parts.append(topic)
            
            if language:
                query_parts.append(f'language:{language}')
            
            # If no query parts, default to general search
            if not query_parts:
                query_parts.append('stars:>1000')
            
            params = {
                'q': ' '.join(query_parts),
                'per_page': 20,
                'page': page
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            repositories = []
            
            for repo in data.get('items', []):
                repo_data = {
                    'name': repo.get('name', ''),
                    'full_name': repo.get('full_name', ''),
                    'description': repo.get('description', ''),
                    'html_url': repo.get('html_url', ''),
                    'stars': repo.get('stargazers_count', 0),
                    'forks': repo.get('forks_count', 0),
                    'language': repo.get('language', ''),
                    'created_at': repo.get('created_at', ''),
                    'updated_at': repo.get('updated_at', ''),
                    'source': 'GitHub Trending'
                }
                repositories.append(repo_data)
            
            return repositories
            
        except Exception as e:
            logger.error(f"Error fetching GitHub trending: {e}")
            return []
    
    def fetch_stackoverflow_questions(self, tags: List[str], max_questions: int = 10, page: int = 1) -> List[Dict[str, Any]]:
        """Fetch recent questions from Stack Overflow with pagination support."""
        try:
            url = "https://api.stackexchange.com/2.3/questions"
            params = {
                'order': 'desc',
                'sort': 'creation',
                'tagged': ';'.join(tags),
                'site': 'stackoverflow',
                'pagesize': max_questions,
                'page': page,
                'fromdate': int((datetime.now() - timedelta(days=7)).timestamp())
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            questions = []
            
            for question in data.get('items', []):
                question_data = {
                    'title': question.get('title', ''),
                    'link': question.get('link', ''),
                    'tags': question.get('tags', []),
                    'score': question.get('score', 0),
                    'view_count': question.get('view_count', 0),
                    'answer_count': question.get('answer_count', 0),
                    'creation_date': datetime.fromtimestamp(question.get('creation_date', 0)),
                    'source': 'Stack Overflow'
                }
                questions.append(question_data)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error fetching Stack Overflow questions: {e}")
            return []
    
    def fetch_reddit_posts(self, subreddit: str, max_posts: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent posts from a subreddit."""
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json"
            headers = {'User-Agent': 'CS-Research-Bot/1.0'}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            for post in data.get('data', {}).get('children', [])[:max_posts]:
                post_data = post.get('data', {})
                post_item = {
                    'title': post_data.get('title', ''),
                    'url': f"https://reddit.com{post_data.get('permalink', '')}",
                    'score': post_data.get('score', 0),
                    'num_comments': post_data.get('num_comments', 0),
                    'created_utc': datetime.fromtimestamp(post_data.get('created_utc', 0)),
                    'subreddit': subreddit,
                    'source': 'Reddit'
                }
                posts.append(post_item)
            
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching Reddit posts from r/{subreddit}: {e}")
            return []
    
    def fetch_tech_news(self, topic: str, max_articles: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent tech news articles."""
        articles = []
        
        # Fetch from multiple tech news sources
        tech_feeds = ['techcrunch', 'arstechnica', 'wired', 'ieee_spectrum']
        
        for feed_name in tech_feeds:
            if feed_name in self.rss_feeds:
                feed_items = self.fetch_rss_feed(self.rss_feeds[feed_name], max_items=max_articles//len(tech_feeds))
                
                # Filter items related to the topic
                for item in feed_items:
                    if self._is_topic_related(topic, item['title'] + ' ' + item['summary']):
                        articles.append(item)
        
        return articles[:max_articles]
    
    def fetch_conference_papers(self, topic: str, max_papers: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent conference papers and proceedings."""
        try:
            # This would integrate with conference APIs like DBLP, ACM, IEEE
            # For now, we'll simulate this with ArXiv data
            from .cs_research_fetcher import CSResearchFetcher
            
            fetcher = CSResearchFetcher()
            arxiv_papers = fetcher.fetch_arxiv_papers(topic, max_results=max_papers)
            
            # Filter for conference papers (papers with specific patterns)
            conference_papers = []
            for paper in arxiv_papers:
                if any(keyword in paper['title'].lower() for keyword in [
                    'conference', 'proceedings', 'workshop', 'symposium', 'icml', 'neurips', 
                    'iclr', 'aaai', 'ijcai', 'kdd', 'icdm', 'www', 'chi', 'uist'
                ]):
                    paper['source'] = 'Conference Proceedings'
                    conference_papers.append(paper)
            
            return conference_papers
            
        except Exception as e:
            logger.error(f"Error fetching conference papers: {e}")
            return []
    
    def fetch_industry_reports(self, topic: str, max_reports: int = 5) -> List[Dict[str, Any]]:
        """Fetch industry reports and whitepapers."""
        try:
            # This would integrate with industry report sources
            # For now, we'll create a placeholder
            reports = [
                {
                    'title': f'Industry Report: {topic}',
                    'description': f'Latest industry insights on {topic}',
                    'url': f'https://example.com/reports/{topic.replace(" ", "-")}',
                    'published': datetime.now() - timedelta(days=30),
                    'source': 'Industry Reports',
                    'type': 'whitepaper'
                }
            ]
            
            return reports
            
        except Exception as e:
            logger.error(f"Error fetching industry reports: {e}")
            return []
    
    def fetch_comprehensive_realtime_data(self, topic: str, github_page: int = 1, stackoverflow_page: int = 1) -> Dict[str, Any]:
        """Fetch comprehensive real-time data for a topic with pagination support."""
        logger.info(f"Fetching real-time data for topic: {topic} (github_page: {github_page}, so_page: {stackoverflow_page})")
        
        data = {
            'topic': topic,
            'timestamp': datetime.now().isoformat(),
            'sources': {},
            'total_items': 0
        }
        
        # Fetch from RSS feeds
        tech_news = self.fetch_tech_news(topic, max_articles=10)
        data['sources']['tech_news'] = tech_news
        data['total_items'] += len(tech_news)
        
        # Fetch from Reddit
        reddit_sources = ['programming', 'MachineLearning', 'compsci', 'artificial']
        reddit_posts = []
        for subreddit in reddit_sources:
            posts = self.fetch_reddit_posts(subreddit, max_posts=3)
            reddit_posts.extend(posts)
        data['sources']['reddit'] = reddit_posts
        data['total_items'] += len(reddit_posts)
        
        # Fetch GitHub trending with pagination
        github_repos = self.fetch_github_trending(topic=topic, page=github_page)
        data['sources']['github'] = github_repos
        data['total_items'] += len(github_repos)
        
        # Fetch Stack Overflow questions with pagination
        so_questions = self.fetch_stackoverflow_questions([topic], max_questions=5, page=stackoverflow_page)
        data['sources']['stackoverflow'] = so_questions
        data['total_items'] += len(so_questions)
        
        # Fetch conference papers
        conference_papers = self.fetch_conference_papers(topic, max_papers=5)
        data['sources']['conferences'] = conference_papers
        data['total_items'] += len(conference_papers)
        
        logger.info(f"Fetched {data['total_items']} real-time items")
        return data
    
    def _is_topic_related(self, topic: str, content: str) -> bool:
        """Check if content is related to the topic."""
        topic_words = set(topic.lower().split())
        content_words = set(content.lower().split())
        
        if not topic_words:
            return False
        
        # Calculate word overlap
        overlap = len(topic_words.intersection(content_words))
        return overlap >= len(topic_words) * 0.3  # At least 30% word overlap
