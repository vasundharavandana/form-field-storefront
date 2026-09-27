from collections import Counter
from pathlib import Path
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent

PRODUCTS = [
    {
        "id": "arc-lamp",
        "name": "Arc Table Lamp",
        "category": "Lighting",
        "price": 12800,
        "color": "Chalk / butter",
        "badge": "BESTSELLER",
        "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=85",
        "alt": "Sculptural table lamp glowing on a side table",
    },
    {
        "id": "form-vase",
        "name": "Form Stoneware Vase",
        "category": "Objects",
        "price": 6400,
        "color": "Speckled white",
        "badge": "JUST IN",
        "image": "https://images.unsplash.com/photo-1578500494198-246f612d3b3d?auto=format&fit=crop&w=900&q=85",
        "alt": "Minimal ceramic vase with a sculptural silhouette",
    },
    {
        "id": "linen-throw",
        "name": "Everyday Linen Throw",
        "category": "Textiles",
        "price": 11200,
        "color": "Rust / oat",
        "badge": "",
        "image": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=900&q=85",
        "alt": "Soft throw draped over a contemporary armchair",
    },
    {
        "id": "orbit-chair",
        "name": "Orbit Lounge Chair",
        "category": "Furniture",
        "price": 38900,
        "color": "Forest green",
        "badge": "LOW STOCK",
        "image": "https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?auto=format&fit=crop&w=900&q=85",
        "alt": "Contemporary lounge chair in a light-filled room",
    },
    {
        "id": "daily-cup",
        "name": "Daily Ceramic Cup",
        "category": "Objects",
        "price": 2800,
        "color": "Moss glaze",
        "badge": "",
        "image": "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?auto=format&fit=crop&w=900&q=85",
        "alt": "Handmade ceramic cup on a bright tabletop",
    },
    {
        "id": "fold-stool",
        "name": "Fold Side Table",
        "category": "Furniture",
        "price": 17600,
        "color": "Natural ash",
        "badge": "",
        "image": "https://images.unsplash.com/photo-1499933374294-4584851497cc?auto=format&fit=crop&w=900&q=85",
        "alt": "Compact wood side table beside a reading chair",
    },
    {
        "id": "soft-glow",
        "name": "Soft Glow Pendant",
        "category": "Lighting",
        "price": 21400,
        "color": "Citrus / white",
        "badge": "JUST IN",
        "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=900&q=85",
        "alt": "Warm pendant light above a carefully set interior",
    },
    {
        "id": "grid-cushion",
        "name": "Grid Cotton Cushion",
        "category": "Textiles",
        "price": 5800,
        "color": "Poppy / cream",
        "badge": "",
        "image": "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?auto=format&fit=crop&w=900&q=85",
        "alt": "Textured cushion adding a bright accent to a sofa",
    },
]

PRODUCT_BY_ID = {product["id"]: product for product in PRODUCTS}
STOCK = {product["id"]: 12 for product in PRODUCTS}
CHECKOUT_LOCK = Lock()

app = FastAPI(title="Form & Field Shop", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


class CartLine(BaseModel):
    product_id: str
    quantity: int = Field(gt=0, le=20)


class CheckoutRequest(BaseModel):
    items: list[CartLine] = Field(min_length=1, max_length=30)


@app.get("/")
def storefront():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/products")
def list_products():
    return [dict(product, stock=STOCK[product["id"]]) for product in PRODUCTS]


@app.post("/api/checkout")
def checkout(request: CheckoutRequest):
    quantities = Counter()
    for line in request.items:
        quantities[line.product_id] += line.quantity

    if any(product_id not in PRODUCT_BY_ID for product_id in quantities):
        raise HTTPException(status_code=404, detail="One or more products were not found.")
    if any(quantity > 20 for quantity in quantities.values()):
        raise HTTPException(status_code=422, detail="A maximum of 20 of each item can be ordered.")

    with CHECKOUT_LOCK:
        if any(quantity > STOCK[product_id] for product_id, quantity in quantities.items()):
            raise HTTPException(status_code=409, detail="An item in your bag is no longer available in that quantity.")

        total = sum(PRODUCT_BY_ID[product_id]["price"] * quantity for product_id, quantity in quantities.items())
        for product_id, quantity in quantities.items():
            STOCK[product_id] -= quantity

    return {
        "order_id": "FF-" + uuid4().hex[:8].upper(),
        "item_count": sum(quantities.values()),
        "total": total,
        "currency": "USD",
        "message": "Your order is confirmed. Thanks for shopping small.",
    }
