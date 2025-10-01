# SmartCatcher: Discount & Coupon Aggregator Bot

A comprehensive price monitoring and discount tracking system with Telegram bot integration, built with FastAPI, PostgreSQL, Redis, and Celery.

## Features

- **User Management**: JWT-based authentication with Telegram integration
- **Product Tracking**: Monitor prices across multiple stores and marketplaces
- **Smart Subscriptions**: Subscribe to products, brands, categories, or keywords
- **Price Alerts**: Get notified when prices drop below thresholds or by percentage
- **Multiple Scrapers**: Support for demo sites, WebScraper.io, eBay API, and Etsy API
- **Telegram Bot**: Full-featured bot for managing subscriptions and receiving notifications
- **Background Tasks**: Automated scraping and notification system with Celery
- **RESTful API**: Complete OpenAPI documentation with FastAPI
- **Production Ready**: Docker containerization, CI/CD, comprehensive testing

## Architecture

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
         └──────────────►│   PostgreSQL    │◄─────────────┘
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

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- UV package manager
- PostgreSQL 15+
- Redis 7+

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/smartcatcher.git
cd smartcatcher
cp .env.example .env
# Edit .env with your configuration
```

### 2. Environment Variables

Update `.env` file with your settings:

```env
# Database
DATABASE_URL=postgresql+asyncpg://smartcatcher:password@localhost:5432/smartcatcher

# Security
SECRET_KEY=your-super-secret-key-change-in-production

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather

# External APIs
EBAY_CLIENT_ID=your-ebay-client-id
EBAY_CLIENT_SECRET=your-ebay-client-secret
ETSY_API_KEY=your-etsy-api-key
```

### 3. Start with Docker Compose

```bash
# Build and start all services
make dev
# OR
docker-compose up --build -d

# Check service health
make healthcheck
```

### 4. Run Database Migrations

```bash
# Apply database migrations
make upgrade
```

### 5. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000/api/v1
- **Health Check**: http://localhost:8000/health
- **Telegram Bot**: Start chatting with your bot on Telegram

## Development Setup

### Local Installation

```bash
# Install dependencies
make install

# Activate virtual environment
source .venv/bin/activate

# Install pre-commit hooks
pre-commit install
```

### Running Services Locally

```bash
# Start database services
docker-compose up postgres redis -d

# Run migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload

# Start Celery worker (separate terminal)
celery -A worker.celery_app worker --loglevel=info

# Start Celery scheduler (separate terminal)
celery -A worker.celery_app beat --loglevel=info

# Start Telegram bot (separate terminal)
python bot/main.py
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh tokens
- `POST /api/v1/auth/change-password` - Change password
- `POST /api/v1/auth/link-telegram` - Link Telegram account

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update user profile
- `GET /api/v1/users/telegram/{telegram_id}` - Get user by Telegram ID

### Products
- `GET /api/v1/products/` - List products with search
- `GET /api/v1/products/{id}` - Get product details
- `POST /api/v1/products/` - Create product (admin)
- `GET /api/v1/products/{id}/history` - Get price history

### Subscriptions
- `GET /api/v1/subscriptions/` - List user subscriptions
- `POST /api/v1/subscriptions/` - Create subscription
- `PUT /api/v1/subscriptions/{id}` - Update subscription
- `DELETE /api/v1/subscriptions/{id}` - Delete subscription

## Telegram Bot Commands

- `/start` - Start bot and link account
- `/subscribe <url>` - Subscribe to product price alerts
- `/subscribe brand <brand_name>` - Subscribe to brand alerts
- `/subscribe category <category>` - Subscribe to category alerts
- `/unsubscribe <id>` - Remove subscription
- `/list` - Show your subscriptions
- `/profile` - View your profile
- `/help` - Get help information

## Scraper Implementation

### Supported Scrapers

1. **Demo Scraper** - For testing with sample HTML
2. **WebScraper.io** - Educational scraping site
3. **eBay API** - Official eBay Browse API
4. **Etsy API** - Official Etsy Open API v3

### Adding New Scrapers

1. Create new scraper class inheriting from `BaseScraper`:

```python
from app.scrapers.base import BaseScraper, ProductData

class MyStoreScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "mystore"
    
    @property
    def supported_domains(self) -> list[str]:
        return ["mystore.com"]
    
    def scrape_product(self, url: str) -> ProductData:
        # Implement scraping logic
        pass
```

2. Register in scraper factory
3. Add configuration if needed
4. Update documentation

### Rate Limiting & Ethics

- Respect robots.txt files
- Implement exponential backoff
- Use reasonable delays between requests
- Monitor rate limit headers
- Only scrape publicly available data

## Testing

### Run Tests

```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests
make test-integration

# Run with coverage
make coverage
```

### Test Structure

```
tests/
├── conftest.py              # Test configuration
├── test_auth.py            # Authentication tests
├── test_products.py        # Product service tests
├── test_subscriptions.py   # Subscription tests
├── test_scrapers.py        # Scraper tests
└── integration/
    ├── test_api.py         # API integration tests
    └── test_bot.py         # Bot integration tests
```

## Deployment

### Production Environment

1. **Environment Setup**:
   ```bash
   export ENVIRONMENT=production
   export DEBUG=false
   # Set secure SECRET_KEY
   # Configure production database
   ```

2. **Database Setup**:
   ```bash
   # Run migrations
   alembic upgrade head
   
   # Create superuser
   python -c "from app.seeds.create_superuser import main; main()"
   ```

3. **SSL/HTTPS**:
   - Configure nginx or load balancer
   - Set up SSL certificates
   - Update CORS settings

4. **Monitoring**:
   - Set up logging aggregation
   - Configure health checks
   - Monitor Celery queues
   - Track API metrics

### Docker Production

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
    restart: unless-stopped
  # ... other services
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Deployment environment | `development` |
| `DEBUG` | Enable debug mode | `true` |
| `SECRET_KEY` | JWT secret key | Required |
| `DATABASE_URL` | PostgreSQL connection | Required |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Required |
| `EBAY_CLIENT_ID` | eBay API client ID | Required |
| `ETSY_API_KEY` | Etsy API key | Required |

### Scraper Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `SCRAPER_DELAY_MIN` | Minimum delay between requests (seconds) | `1` |
| `SCRAPER_DELAY_MAX` | Maximum delay between requests (seconds) | `3` |
| `SCRAPER_MAX_RETRIES` | Maximum retry attempts | `3` |
| `SCRAPER_USER_AGENT` | User agent string | `SmartCatcher Bot 1.0` |

## Security

- JWT tokens with configurable expiration
- Password hashing with bcrypt
- SQL injection prevention with SQLAlchemy
- CORS configuration for web clients
- Rate limiting on API endpoints
- Input validation with Pydantic
- Secure headers and HTTPS support

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Install development dependencies: `make install`
4. Run tests: `make test`
5. Run linting: `make lint`
6. Commit changes: `git commit -m 'Add amazing feature'`
7. Push branch: `git push origin feature/amazing-feature`
8. Open Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all functions
- Add docstrings for classes and methods
- Write comprehensive tests
- Update documentation

### Testing Requirements

- Maintain >80% test coverage
- Include unit tests for new features
- Add integration tests for API endpoints
- Test error handling and edge cases

## Performance Optimization

### Database Optimization

- Use appropriate indexes on query fields
- Implement pagination for large datasets
- Use database connection pooling
- Regular VACUUM and ANALYZE operations

### Caching Strategy

- Redis caching for frequently accessed data
- API response caching with TTL
- Rate limiting with Redis
- Background task result caching

### Monitoring & Alerts

- Application performance monitoring
- Database query performance
- Celery task monitoring
- Error tracking and alerts
- Resource usage monitoring

## Troubleshooting

### Common Issues

**Database Connection Issues**:
```bash
# Check database status
make healthcheck
docker-compose logs postgres

# Reset database
make clean
make dev
make upgrade
```

**Celery Worker Issues**:
```bash
# Check worker status
docker-compose logs worker

# Restart workers
docker-compose restart worker scheduler
```

**Telegram Bot Issues**:
```bash
# Check bot logs
docker-compose logs bot

# Verify bot token
curl https://api.telegram.org/bot<TOKEN>/getMe
```

**API Issues**:
```bash
# Check backend health
curl http://localhost:8000/health

# View API logs
docker-compose logs backend
```

### Debug Mode

Enable debug mode for detailed error information:
```bash
export DEBUG=true
# Restart services
docker-compose restart
```

## API Examples

### cURL Examples

**Register User**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
  }'
```

**Login**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

**Create Subscription**:
```bash
curl -X POST "http://localhost:8000/api/v1/subscriptions/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subscription_type": "product",
    "product_id": 1,
    "price_threshold": 50.00,
    "notification_types": ["price_drop"],
    "notify_telegram": true
  }'
```

**Search Products**:
```bash
curl -X GET "http://localhost:8000/api/v1/products/?query=headphones&limit=10" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Python SDK Example

```python
import aiohttp
import asyncio

class SmartCatcherClient:
    def __init__(self, base_url: str, token: str = None):
        self.base_url = base_url
        self.token = token
    
    async def login(self, email: str, password: str):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"email": email, "password": password}
            ) as response:
                data = await response.json()
                self.token = data["tokens"]["access_token"]
                return data
    
    async def create_subscription(self, subscription_data: dict):
        headers = {"Authorization": f"Bearer {self.token}"}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/v1/subscriptions/",
                json=subscription_data,
                headers=headers
            ) as response:
                return await response.json()

# Usage
async def main():
    client = SmartCatcherClient("http://localhost:8000")
    await client.login("user@example.com", "password")
    
    subscription = await client.create_subscription({
        "subscription_type": "brand",
        "target_brand": "Apple",
        "percentage_threshold": 20,
        "notify_telegram": True
    })
    print(subscription)

asyncio.run(main())
```

## Telegram Bot Usage Examples

### Subscribe to Product Price Drops

1. **Direct URL Subscription**:
   ```
   /subscribe https://example.com/product/123
   ```
   Bot will extract product information and create a subscription.

2. **Brand Subscription**:
   ```
   /subscribe brand Apple
   ```
   Get notified about all Apple products.

3. **Category Subscription**:
   ```
   /subscribe category Electronics
   ```
   Monitor electronics category for deals.

### Managing Subscriptions

1. **List Subscriptions**:
   ```
   /list
   ```
   Shows all active subscriptions with IDs.

2. **Unsubscribe**:
   ```
   /unsubscribe 123
   ```
   Remove subscription by ID.

3. **Set Price Threshold**:
   ```
   /subscribe https://example.com/product/123 $50
   ```
   Get notified when price drops below $50.

## Monitoring & Maintenance

### Health Checks

```bash
# API Health
curl http://localhost:8000/health

# Database Health
docker-compose exec postgres pg_isready -U smartcatcher

# Redis Health
docker-compose exec redis redis-cli ping

# Service Status
docker-compose ps
```

### Log Management

```bash
# View logs
make logs

# Specific service logs
make logs-backend
make logs-worker
make logs-bot

# Follow logs
docker-compose logs -f --tail=100
```

### Backup & Recovery

```bash
# Database backup
docker-compose exec postgres pg_dump -U smartcatcher smartcatcher > backup.sql

# Database restore
docker-compose exec -T postgres psql -U smartcatcher smartcatcher < backup.sql

# Redis backup
docker-compose exec redis redis-cli BGSAVE
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## Support

- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and community
- **Documentation**: This README and inline code documentation
- **API Docs**: Available at `/docs` when running in development

## Acknowledgments

- FastAPI for the excellent async web framework
- aiogram for the Telegram bot framework
- SQLAlchemy for the robust ORM
- Celery for distributed task processing
- All contributors and the open-source community

---

**SmartCatcher** - Never miss a deal again! 🎯