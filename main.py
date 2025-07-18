
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from bson import ObjectId
# from pymongo import MongoClient
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
from dotenv import load_dotenv
import os
import re
import uvicorn
from enum import Enum
from bson import ObjectId


import urllib.parse


# Initialize FastAPI app
app = FastAPI(
    title="HROne Ecommerce API",
    description="Backend API for ecommerce application",
    version="1.0.0"
)


# Loads variables from .env into environment
load_dotenv()
# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URL, server_api=ServerApi('1'))
db = client.ecommerce

# Collections
products_collection = db.products
orders_collection = db.orders



# Pydantic models
class ProductSizes(BaseModel):
    size: str
    quantity: int

class ProductCreate(BaseModel):
    name: str
    price: float
    sizes: List[ProductSizes]

class Product(BaseModel):
    id: str = Field(alias="_id")
    name: str
    price: float

    class Config:
        allow_population_by_field_name = True

class OrderItem(BaseModel):
    productId: str
    qty: int

class OrderCreate(BaseModel):
    userId: str
    items: List[OrderItem]


# Helper functions
def object_id_to_string(obj):
    """Convert ObjectId to string in MongoDB documents"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, ObjectId):
                obj[key] = str(value)
            elif isinstance(value, dict):
                object_id_to_string(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        object_id_to_string(item)
    return obj

# API Routes

@app.get("/")
async def root():
    return {"message": "HROne Ecommerce API is running!"}

@app.post("/products", status_code=201)
async def create_product(product: ProductCreate):
    """Create a new product"""
    try:
        product_dict = product.dict()

        result = products_collection.insert_one(product_dict)

        return {
            "id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products", status_code=200)
async def list_products(
    name: Optional[str] = Query(None, description="Filter by product name (supports regex)"),
    size: Optional[str] = Query(None, description="Filter by product size"),
    limit: Optional[int] = Query(10, ge=1, le=100, description="Number of products to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of products to skip")
):
    """List products with optional filtering"""
    try:
        # Build query filter
        query_filter = {}

        if name:
            # Use regex for partial name matching
            query_filter["name"] = {"$regex": re.escape(name), "$options": "i"}

        if size:
            query_filter["sizes.size"] = size

        # Get total count for pagination info
        total = products_collection.count_documents(query_filter)

        # Fetch products with pagination
        cursor = products_collection.find(query_filter).skip(offset).limit(limit).sort("_id", 1)
        products = list(cursor)

        # Convert ObjectId to string
        for product in products:
            product = object_id_to_string(product)
        
        next_page_index = offset + limit if (offset + limit) < total else None
        prev_page_index = offset - limit if (offset - limit) >= 0 else None
        return {
            "data": [
                {
                    "id": str(product["_id"]),
                    "name": product["name"],
                    "price": product["price"],
                }
                for product in products
            ],
            "page":{
                "next": next_page_index,
                "limit": limit,
                "previous": prev_page_index
            }
           
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/orders", status_code=201)
async def create_order(order: OrderCreate):
    """Create a new order"""
    try:

        # Create order document
        order_dict = order.dict()
        result = orders_collection.insert_one(order_dict)
        return {
            "id": str(result.inserted_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/{user_id}", status_code=200)
async def get_user_orders(
    user_id: str = Path(..., description="User ID"),
    limit: Optional[int] = Query(10, ge=1, le=100, description="Number of orders to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of orders to skip")
):
    """Get orders for a specific user"""
    try:
        query_filter = {"userId": user_id}  # Note: use correct field as stored in your DB!

        total = orders_collection.count_documents(query_filter)
        cursor = orders_collection.find(query_filter).skip(offset).limit(limit).sort("_id", 1)
        orders = list(cursor)

        results = []
        for order in orders:
            # For each order, build items with product details
            totalOrderPrice = 0
            items = []
            for item in order.get("items", []):
                # Look up product by id
                product = products_collection.find_one({"_id": ObjectId(item["productId"])})
                product_details = {
                    "id": item["productId"],
                    "name": product["name"] if product else None
                }
                items.append({
                    "productDetails": product_details,
                    "qty": item["qty"]
                    # add size if present: "size": item.get("size")
                })
                totalOrderPrice+=product["price"]

            results.append({
                "id": str(order["_id"]),
                "items": items,
                "total": totalOrderPrice,  # or whatever field you use for order total
                # ...add other fields if needed
            })

        # Pagination indexes for next/previous page
        next_page_index = offset + limit if (offset + limit) < total else None
        prev_page_index = offset - limit if (offset - limit) >= 0 else None

        return {
            "data": results,
            "page": {
                "next": next_page_index,
                "limit": limit,
                "previous": prev_page_index
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
