"""Specialized data fetcher for CS/IT research with ArXiv and other sources."""

import logging
import arxiv
import requests
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import time
import re

logger = logging.getLogger(__name__)


class CSResearchFetcher:
    """Specialized fetcher for computer science and IT research data."""
    
    def __init__(self):
        """Initialize the CS research fetcher."""
        self.name = "CS Research Fetcher"
        
        # CS/IT related ArXiv categories
        self.arxiv_categories = [
            'cs.AI',      # Artificial Intelligence
            'cs.CC',      # Computational Complexity
            'cs.CE',      # Computational Engineering, Finance, and Science
            'cs.CG',      # Computational Geometry
            'cs.CL',      # Computation and Language
            'cs.CR',      # Cryptography and Security
            'cs.CV',      # Computer Vision and Pattern Recognition
            'cs.CY',      # Computers and Society
            'cs.DB',      # Databases
            'cs.DC',      # Distributed, Parallel, and Cluster Computing
            'cs.DL',      # Digital Libraries
            'cs.DM',      # Discrete Mathematics
            'cs.DS',      # Data Structures and Algorithms
            'cs.ET',      # Emerging Technologies
            'cs.FL',      # Formal Languages and Automata Theory
            'cs.GL',      # General Literature
            'cs.GR',      # Graphics
            'cs.GT',      # Computer Science and Game Theory
            'cs.HC',      # Human-Computer Interaction
            'cs.IR',      # Information Retrieval
            'cs.IT',      # Information Theory
            'cs.LG',      # Machine Learning
            'cs.LO',      # Logic in Computer Science
            'cs.MA',      # Multiagent Systems
            'cs.MM',      # Multimedia
            'cs.MS',      # Mathematical Software
            'cs.NA',      # Numerical Analysis
            'cs.NE',      # Neural and Evolutionary Computing
            'cs.NI',      # Networking and Internet Architecture
            'cs.OH',      # Other Computer Science
            'cs.OS',      # Operating Systems
            'cs.PF',      # Performance
            'cs.PL',      # Programming Languages
            'cs.RO',      # Robotics
            'cs.SC',      # Symbolic Computation
            'cs.SD',      # Sound
            'cs.SE',      # Software Engineering
            'cs.SI',      # Social and Information Networks
            'cs.SY',      # Systems and Control
            'cs.TH',      # Hardware Architecture
            'cs.UR',      # Human-Computer Interaction
        ]
        
        # Additional CS/IT sources
        self.additional_sources = {
            'github_trending': 'https://github.com/trending',
            'hackernews': 'https://hn.algolia.com/api/v1/search',
            'stackoverflow': 'https://api.stackexchange.com/2.3/questions',
            'ieee_xplore': 'https://ieeexploreapi.ieee.org/api/v1/search/articles',
            'acm_digital_library': 'https://dl.acm.org/api/search',
        }
        
        logger.info(f"Initialized {self.name} with {len(self.arxiv_categories)} ArXiv categories")
    
    def is_cs_it_topic(self, topic: str) -> bool:
        """Check if a topic is related to CS/IT domains."""
        cs_it_keywords = [
            'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
            'computer vision', 'natural language processing', 'nlp', 'data science',
            'software engineering', 'programming', 'algorithm', 'data structure',
            'database', 'cybersecurity', 'cryptography', 'blockchain', 'distributed system',
            'cloud computing', 'web development', 'mobile development', 'devops',
            'computer science', 'information technology', 'computing', 'technology',
            'software', 'hardware', 'networking', 'operating system', 'computer graphics',
            'human computer interaction', 'hci', 'robotics', 'automation', 'ai',
            'ml', 'dl', 'cv', 'nlp', 'api', 'framework', 'library', 'tool',
            'platform', 'architecture', 'design pattern', 'optimization', 'performance',
            'scalability', 'reliability', 'security', 'privacy', 'data mining',
            'big data', 'analytics', 'visualization', 'user interface', 'ux', 'ui'
        ]
        
        topic_lower = topic.lower()
        return any(keyword in topic_lower for keyword in cs_it_keywords)
    
    def fetch_arxiv_papers(self, topic: str, max_results: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Fetch recent papers from ArXiv related to the topic with pagination support."""
        logger.info(f"Fetching ArXiv papers for topic: {topic} (offset: {offset}, max: {max_results})")
        
        try:
            # Create search query
            query = f'all:{topic}'
            
            # Search ArXiv with offset for pagination
            # ArXiv API uses 'start' parameter for pagination
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            # Skip papers up to the offset
            for idx, paper in enumerate(search.results()):
                if idx < offset:
                    continue
                if idx >= offset + max_results:
                    break
                    
                # Filter by CS/IT categories
                if any(cat in paper.categories for cat in self.arxiv_categories):
                    paper_data = {
                        'title': paper.title,
                        'authors': [author.name for author in paper.authors],
                        'abstract': paper.summary,
                        'published': paper.published,
                        'updated': paper.updated,
                        'categories': paper.categories,
                        'url': paper.entry_id,
                        'pdf_url': paper.pdf_url,
                        'source': 'ArXiv',
                        'relevance_score': self._calculate_relevance_score(topic, paper.title, paper.summary)
                    }
                    papers.append(paper_data)
            
            logger.info(f"Found {len(papers)} relevant ArXiv papers")
            return papers
            
        except Exception as e:
            logger.error(f"Error fetching ArXiv papers: {e}")
            return []
    
    def fetch_github_trending(self, topic: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetch trending GitHub repositories related to the topic."""
        logger.info(f"Fetching GitHub trending for topic: {topic}")
        
        try:
            # This is a simplified implementation
            # In practice, you'd use GitHub API with proper authentication
            trending_data = {
                'source': 'GitHub Trending',
                'description': f'Trending repositories related to {topic}',
                'url': f'https://github.com/trending?since=weekly&spoken_language_code=en',
                'relevance_score': 0.7
            }
            
            return [trending_data]
            
        except Exception as e:
            logger.error(f"Error fetching GitHub trending: {e}")
            return []
    
    def fetch_hackernews(self, topic: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetch relevant posts from Hacker News."""
        logger.info(f"Fetching Hacker News posts for topic: {topic}")
        
        try:
            # Hacker News API
            url = "https://hn.algolia.com/api/v1/search"
            params = {
                'query': topic,
                'tags': 'story',
                'hitsPerPage': max_results,
                'numericFilters': f'created_at_i>{int((datetime.now() - timedelta(days=30)).timestamp())}'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            for hit in data.get('hits', []):
                post_data = {
                    'title': hit.get('title', ''),
                    'url': hit.get('url', ''),
                    'points': hit.get('points', 0),
                    'comments': hit.get('num_comments', 0),
                    'created_at': datetime.fromtimestamp(hit.get('created_at_i', 0)),
                    'source': 'Hacker News',
                    'relevance_score': self._calculate_relevance_score(topic, hit.get('title', ''), '')
                }
                posts.append(post_data)
            
            logger.info(f"Found {len(posts)} relevant Hacker News posts")
            return posts
            
        except Exception as e:
            logger.error(f"Error fetching Hacker News: {e}")
            return []
    
    def fetch_recent_news(self, topic: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent news articles related to the topic."""
        logger.info(f"Fetching recent news for topic: {topic}")
        
        try:
            # This is a placeholder for news API integration
            # You would integrate with news APIs like NewsAPI, Google News, etc.
            news_data = {
                'source': 'Recent News',
                'description': f'Recent news articles about {topic}',
                'url': f'https://news.google.com/search?q={topic.replace(" ", "+")}',
                'relevance_score': 0.6
            }
            
            return [news_data]
            
        except Exception as e:
            logger.error(f"Error fetching recent news: {e}")
            return []
    
    def fetch_comprehensive_data(self, topic: str, arxiv_offset: int = 0) -> Dict[str, Any]:
        """Fetch comprehensive data from all sources with pagination support."""
        logger.info(f"Fetching comprehensive data for CS/IT topic: {topic} (arxiv_offset: {arxiv_offset})")
        
        # Validate topic is CS/IT related
        if not self.is_cs_it_topic(topic):
            logger.warning(f"Topic '{topic}' may not be CS/IT related")
        
        all_data = {
            'topic': topic,
            'is_cs_it_related': self.is_cs_it_topic(topic),
            'sources': {},
            'total_items': 0,
            'fetch_timestamp': datetime.now().isoformat()
        }
        
        # Fetch from ArXiv (primary source) with offset
        arxiv_papers = self.fetch_arxiv_papers(topic, max_results=15, offset=arxiv_offset)
        all_data['sources']['arxiv'] = arxiv_papers
        all_data['total_items'] += len(arxiv_papers)
        
        # Fetch from Hacker News
        hn_posts = self.fetch_hackernews(topic, max_results=8)
        all_data['sources']['hackernews'] = hn_posts
        all_data['total_items'] += len(hn_posts)
        
        # Fetch GitHub trending
        github_trending = self.fetch_github_trending(topic, max_results=5)
        all_data['sources']['github'] = github_trending
        all_data['total_items'] += len(github_trending)
        
        # Fetch recent news
        recent_news = self.fetch_recent_news(topic, max_results=5)
        all_data['sources']['news'] = recent_news
        all_data['total_items'] += len(recent_news)
        
        logger.info(f"Fetched {all_data['total_items']} total items from {len(all_data['sources'])} sources")
        
        return all_data
    
    def _calculate_relevance_score(self, topic: str, title: str, content: str) -> float:
        """Calculate relevance score for a piece of content."""
        topic_words = set(topic.lower().split())
        content_words = set((title + ' ' + content).lower().split())
        
        if not topic_words:
            return 0.0
        
        # Calculate word overlap
        overlap = len(topic_words.intersection(content_words))
        relevance = overlap / len(topic_words)
        
        # Boost score for exact phrase matches
        if topic.lower() in (title + ' ' + content).lower():
            relevance += 0.3
        
        return min(relevance, 1.0)
    
    def get_domain_specific_insights(self, topic: str) -> Dict[str, Any]:
        """Get domain-specific insights for CS/IT topics."""
        insights = {
            'domain': 'Computer Science & Information Technology',
            'suggested_categories': [],
            'research_directions': [],
            'key_technologies': [],
            'recent_trends': []
        }
        
        # Analyze topic for domain-specific insights
        topic_lower = topic.lower()
        
        # AI/ML related
        if any(keyword in topic_lower for keyword in ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning']):
            insights['suggested_categories'].extend(['cs.AI', 'cs.LG', 'cs.CV', 'cs.CL'])
            insights['research_directions'].extend(['Neural Networks', 'Deep Learning', 'Computer Vision', 'NLP'])
            insights['key_technologies'].extend(['TensorFlow', 'PyTorch', 'Transformers', 'GANs'])
        
        # Software Engineering
        if any(keyword in topic_lower for keyword in ['software', 'programming', 'development', 'engineering']):
            insights['suggested_categories'].extend(['cs.SE', 'cs.PL', 'cs.DS'])
            insights['research_directions'].extend(['Software Architecture', 'Code Quality', 'Testing', 'DevOps'])
            insights['key_technologies'].extend(['Git', 'Docker', 'Kubernetes', 'CI/CD'])
        
        # Cybersecurity
        if any(keyword in topic_lower for keyword in ['security', 'cybersecurity', 'cryptography', 'privacy']):
            insights['suggested_categories'].extend(['cs.CR', 'cs.CY'])
            insights['research_directions'].extend(['Cryptography', 'Network Security', 'Privacy', 'Threat Detection'])
            insights['key_technologies'].extend(['Blockchain', 'Zero-Knowledge Proofs', 'Encryption'])
        
        # Data Science
        if any(keyword in topic_lower for keyword in ['data', 'analytics', 'database', 'big data']):
            insights['suggested_categories'].extend(['cs.DB', 'cs.DS', 'cs.LG'])
            insights['research_directions'].extend(['Data Mining', 'Big Data', 'Data Visualization', 'Analytics'])
            insights['key_technologies'].extend(['Hadoop', 'Spark', 'Pandas', 'SQL'])
        
        return insights
