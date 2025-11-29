# services/demo_server/main.py
import logging
import sys
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import random
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

current_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(current_dir / "templates"))

UPDATE_PRICE_INTERVAL = 60

# products config
PRODUCTS = {
    "watch": {
        "title": "Smart Fitness Watch Pro",
        "brand": "TechGear",
        "image": "https://placehold.co/300x300/007bff/ffffff?text=Smart+Watch",
        "base_price": 130.99,
    },
    "headphones": {
        "title": "Premium Wireless Headphones",
        "brand": "SoundMax",
        "image": "https://placehold.co/300x300/28a745/ffffff?text=Headphones",
        "base_price": 199.99,
    },
    "band": {
        "title": "Basic Fitness Tracker Band",
        "brand": "FitStep",
        "image": "https://placehold.co/300x300/dc3545/ffffff?text=Fitness+Band",
        "base_price": 49.99,
    }
}

# Storing current prices
current_prices = {key: info["base_price"] for key, info in PRODUCTS.items()}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Background task: updates prices every 60 seconds"""
    task = asyncio.create_task(update_all_prices())
    yield
    task.cancel()


async def update_all_prices():
    """The price of each item is randomly changed by ±10%"""
    while True:
        for key in PRODUCTS.keys():
            base = current_prices[key]
            variation = 0.10
            min_price = base * (1 - variation)
            max_price = base * (1 + variation)
            new_price = round(random.uniform(min_price, max_price), 2)
            current_prices[key] = new_price
            logger.info(f"[Demo Server] {key.capitalize()} price updated to: ${new_price}")
        await asyncio.sleep(UPDATE_PRICE_INTERVAL)


app = FastAPI(title="SmartCatcher Demo Server",
              lifespan=lifespan, )


@app.get("/")
async def index():
    """Redirect or product list"""
    return {"message": "Demo server running", "products": [f"/{k}" for k in PRODUCTS]}


@app.get("/{product_id}")
async def product_page(request: Request, product_id: str):
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")

    config = PRODUCTS[product_id]
    price_str = f"${current_prices[product_id]:.2f}"
    sku = f"DEMO-{product_id.upper()}-001"

    return templates.TemplateResponse(
        "product.html",
        {
            "request": request,
            "title": config["title"],
            "brand": config["brand"],
            "price": price_str,
            "image_url": config["image"],
            "sku": sku,
            "product_id": product_id,
        }
    )


@app.get("/{product_id}.html")
async def product_page_with_extension(request: Request, product_id: str):
    """Support URLs with .html extension"""
    return await product_page(request, product_id)


@app.post("/set-price/{product_id}/{price}")
async def set_price(product_id: str, price: float):
    if product_id not in PRODUCTS:
        raise HTTPException(status_code=404, detail="Product not found")
    if price <= 0:
        raise HTTPException(status_code=400, detail="Price must be positive")

    current_prices[product_id] = round(price, 2)
    logger.info(f"[Demo Server] {product_id} price manually set to: ${price:.2f}")
    return {"product": product_id, "price": f"${price:.2f}"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
