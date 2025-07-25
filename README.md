# AutoCurate - AI-Powered Personalized Knowledge Feed

**AutoCurate** is a smart agent-based system that scrapes and ingests content from user-defined websites, understands the structure and meaning of that content, collects user preferences via a dynamic survey, and delivers hyper-personalized summaries to each user.

## 🎯 Features

### ✨ **Smart Web Ingestion**
- Crawl and scrape websites using intelligent selectors
- Support for RSS feeds and sitemaps
- Clean and process text using advanced NLP
- Handle multiple content formats (articles, blogs, research papers)

### 🧠 **AI-Powered Processing**
- Convert content into vector embeddings using OpenAI or Sentence Transformers
- Store in vector databases (FAISS, Pinecone, or ChromaDB)
- Intelligent content chunking and deduplication

### 📋 **Dynamic User Preferences**
- Interactive survey system to collect user interests
- Adaptive preference learning from user feedback
- Support for multiple content formats and delivery schedules

### 🤖 **Personalized Summarization**
- LLM-powered summary generation using RAG (Retrieval-Augmented Generation)
- Customizable summary formats (bullets, narrative, tabular)
- Multiple delivery frequencies (daily, weekly, monthly)

### 📊 **Continuous Learning**
- User feedback collection and analysis
- Preference adaptation based on interactions
- Content performance analytics

## 🏗️ Architecture

AutoCurate follows a modular agent-based design:

| Agent | Responsibility |
|-------|---------------|
| `WebsiteIngestAgent` | Scrapes, parses, and chunks web data |
| `VectorStorageAgent` | Embeds and stores content in vector DB |
| `UserPreferenceAgent` | Manages user preferences and surveys |
| `SummaryAgent` | Generates personalized summaries using RAG |
| `FeedbackAgent` | Collects feedback and improves recommendations |

## 🛠️ Tech Stack

- **Backend**: FastAPI + SQLAlchemy
- **Database**: PostgreSQL (with Supabase)
- **Vector DB**: FAISS (with Pinecone/ChromaDB options)
- **LLM**: OpenAI GPT-4
- **Task Queue**: Celery + Redis
- **Web Scraping**: trafilatura, newspaper3k, BeautifulSoup
- **ML**: Sentence Transformers, LangChain

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL or Supabase account
- OpenAI API key
- Redis (for background tasks)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/imthadh-ahamed/AutoCurate.git
cd AutoCurate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Initialize the database**
```bash
python run.py init-db
```

### Running the Application

**Start the API server:**
```bash
python run.py api
```

**Run background workers (in separate terminals):**
```bash
# Worker for background tasks
python run.py worker

# Scheduler for periodic tasks
python run.py scheduler

# Optional: Task monitoring UI
python run.py flower
```

**Manual operations:**
```bash
# Run content scraping
python run.py scrape

# Process content for embeddings
python run.py process

# Generate test summary
python run.py test-summary

# Check application status
python run.py status
```

## 📖 API Usage

The API will be available at `http://localhost:8000` with interactive documentation at `/docs`.

### Key Endpoints

**Websites Management:**
- `POST /api/websites` - Add new website to scrape
- `GET /api/websites` - List all websites
- `PUT /api/websites/{id}` - Update website settings

**User Management:**
- `POST /api/users` - Create new user
- `GET /api/users/{id}/survey` - Get preference survey
- `POST /api/users/{id}/survey` - Submit survey response

**Content & Summaries:**
- `GET /api/content` - Browse scraped content
- `POST /api/users/{id}/summaries` - Generate personalized summary
- `GET /api/users/{id}/summaries` - Get user's summaries

**Feedback & Analytics:**
- `POST /api/users/{id}/interactions` - Record content interaction
- `POST /api/users/{id}/summaries/{id}/feedback` - Submit summary feedback
- `GET /api/users/{id}/analytics` - Get user engagement analytics

**Search:**
- `GET /api/search?q=query` - Vector-based content search

## 🔧 Configuration

Key configuration options in `.env`:

```bash
# LLM Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Vector Database
VECTOR_DB_TYPE=faiss  # faiss, pinecone, chroma

# Content Processing
CHUNK_SIZE=512
MAX_CONTENT_LENGTH=10000

# Scheduling
INGESTION_SCHEDULE_MINUTES=60
```

## 📊 Sample Dataset

The project includes a curated dataset of AI/Tech websites in `dataset/websites_dataset.csv`:

- AI Research blogs (OpenAI, Google AI, Hugging Face)
- Tech news sites (TechCrunch, The Verge)
- Research publications (arXiv feeds)
- Developer resources (GitHub releases, Dev.to)

## 🎨 Example Use Cases

| User Type | Websites | Output |
|-----------|----------|--------|
| **AI Researcher** | arXiv, Nature, Google AI | Technical summaries of latest papers |
| **Product Manager** | TechCrunch, Hacker News | Market trend highlights |
| **Developer** | Dev.to, GitHub | Weekly digest of tools and tutorials |
| **Investor** | Bloomberg, CNBC | Market signals and risk alerts |

## 🔄 Background Tasks

AutoCurate runs several automated background tasks:

- **Hourly**: Website content scraping
- **Every 30min**: Content processing and embedding
- **Daily 9 AM**: Generate daily summaries
- **Weekly Monday**: Generate weekly roundups
- **Monthly 1st**: Generate monthly overviews
- **Daily 2 AM**: Update learning models
- **Weekly Sunday**: Data cleanup

## 🧪 Development

**Project Structure:**
```
AutoCurate/
├── src/
│   ├── agents/          # Core AI agents
│   ├── models/          # Database & API models
│   ├── config/          # Configuration management
│   ├── core/            # Database connections
│   ├── tasks/           # Celery background tasks
│   ├── utils/           # Utility functions
│   └── main.py          # FastAPI application
├── dataset/             # Sample website data
├── requirements.txt     # Python dependencies
├── run.py              # Main application runner
└── README.md
```

**Adding New Websites:**
```python
# Via API
POST /api/websites
{
    "url": "https://example.com/feed",
    "category": "Tech News",
    "name": "Example Site",
    "scraping_frequency_hours": 12
}
```

**Custom Content Selectors:**
```python
# For non-standard websites
{
    "selector_config": {
        "article_links": ".post-title a",
        "title_selector": "h1.article-title",
        "content_selector": ".article-content"
    }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 and embedding models
- Hugging Face for Sentence Transformers
- FastAPI team for the excellent web framework
- The open-source community for the amazing tools

---

**Built with ❤️ for the AI community**

For questions or support, please open an issue or contact [imthadh.ahamed@gmail.com](mailto:imthadh.ahamed@gmail.com).