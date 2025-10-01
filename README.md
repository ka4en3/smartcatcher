# SmartCatcher: Discount & Coupon Aggregator Bot

A production-ready service that allows users to subscribe to products/brands and receive price drop notifications. It also collects discounts/coupons through parsers/adapters and supports affiliate links.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   FastAPI API   │    │  Celery Worker  │
│                 │    │                 │    │                 │
│ • User Commands │◄──►│ • Authentication│◄──►│ • Price Scraping│
│ • Notifications │    │ • CRUD Endpoints│    │ • Notifications │
│ • Subscriptions │    │ • OpenAPI Docs  │    │ • Periodic Tasks│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └─────────────►│   PostgreSQL    │◄─────────────┘
                        │                 │
                        │ • Users         │
                        │ • Products      │
                        │ • Subscriptions │
                        │ • Notifications │
                        │ • Price History │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │     Redis       │
                        │                 │
                        │ • Task Queue    │
                        │ • Rate Limiting │
                        │ • Caching       │
                        └─────────────────┘
```

### 🔧 Components

- **Backend**: FastAPI REST API with JWT authentication
- **Database**: PostgreSQL with async SQLAlchemy/SQLModel
- **Queue System**: Celery with Redis as broker
- **Bot**: aiogram-based Telegram bot
- **Scrapers**: Pluggable scrapers for eBay, Etsy, and demo sites
- **Background Tasks**: Periodic price monitoring and notifications

## ✨ Features

- **🔐 User Management**: Registration, login with JWT tokens
- **📦 Product Subscriptions**: Subscribe to products/brands with price thresholds
- **📊 Price Monitoring**: Automated price tracking and history storage
- **🔔 Smart Notifications**: Telegram notifications for price drops
- **🌐 Multi-Source Scraping**: eBay API, Etsy API, and HTML scrapers
- **💰 Affiliate Support**: Support for affiliate links
- **🔌 Extensible**: Easy to add new scrapers and notification channels

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for development)
- UV (for dependency management)

### Environment Setup

1. Copy the environment file:
```bash
cp .env.example .env
```

2. Fill in your API keys in `.env`:
```env
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
EBAY_CLIENT_ID=your-ebay-client-id
EBAY_CLIENT_SECRET=your-ebay-client-secret
ETSY_API_KEY=your-etsy-api-key
```

### 🐳 Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d --build
```

### 💻 Development Setup

1. Install dependencies:
```bash
uv sync --dev
```

2. Set up pre-commit hooks:
```bash
pre-commit install
```

3. Run database migrations:
```bash
cd backend
alembic upgrade head
```

4. Start development servers:
```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Worker
cd worker
celery -A celery_app worker --loglevel=info

# Scheduler
celery -A celery_app beat --loglevel=info

# Bot
cd bot
python main.py
```

## 📚 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user (returns access/refresh tokens)
- `POST /auth/refresh` - Refresh access token

### User Management
- `GET /users/me` - Get current user profile

### Products
- `GET /products` - List/search products
- `GET /products/{id}` - Get product details
- `POST /products` - Add product (admin only)

### Subscriptions
- `POST /subscriptions` - Subscribe to product/brand
- `GET /subscriptions` - List user subscriptions
- `DELETE /subscriptions/{id}` - Unsubscribe

## 🤖 Telegram Bot Commands

- `/start` - Link account or create new account
- `/subscribe <url>` - Subscribe to product price changes
- `/list` - Show active subscriptions
- `/unsubscribe <id>` - Remove subscription

## 🕷️ Scrapers

### Currently Supported:
1. **Demo Scraper**: Parses example HTML pages (for testing)
2. **WebScraper.io**: Scrapes webscraper.io test sites
3. **eBay API**: Uses official eBay Browse API
4. **Etsy API**: Uses official Etsy Open API v3

### Adding New Scrapers

1. Create a new scraper class inheriting from `BaseScraper`:

```python
from backend.app.scrapers.base import BaseScraper, ScrapedProduct

class NewSiteScraper(BaseScraper):
    def __init__(self):
        super().__init__("newsite")
    
    async def scrape_product(self, url: str) -> ScrapedProduct:
        # Implementation here
        pass
    
    def can_handle_url(self, url: str) -> bool:
        return "newsite.com" in url
```

2. Register it in `backend/app/scrapers/__init__.py`

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov=bot --cov=worker

# Run specific test file
pytest tests/test_scrapers.py -v
```

## 🚀 Deployment

### Production Environment

1. Update environment variables for production
2. Set up SSL certificates
3. Configure reverse proxy (nginx)
4. Set up monitoring and logging

### Docker Production Build

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## 💡 Example Usage

### API Example (curl)

```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user@example.com", "password": "securepassword"}'

# Subscribe to product (with auth token)
curl -X POST http://localhost:8000/subscriptions \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_url": "https://www.ebay.com/itm/123456789", "price_threshold": 100.0}'
```

### Bot Interaction Example

```
User: /start
Bot: Welcome! Please link your account or register:
     Link existing: /link your@email.com password
     New user: /register your@email.com password

User: /subscribe https://www.ebay.com/itm/123456789
Bot: ✅ Subscribed to iPhone 14 Pro Max
     Current price: $999.99
     You'll be notified if price drops below $950.00

Bot: 🔔 Price Alert!
     iPhone 14 Pro Max price dropped!
     Was: $999.99 → Now: $899.99 (-$100.00)
     Buy now: https://ebay.com/itm/123456789?affiliate=...
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📝 Changelog

See CHANGELOG.md for version history and changes.

---

<div align="center">
Made with ❤️ by the SmartCatcher team
</div>