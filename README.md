# Ecommerce Backend API

A FastAPI + MongoDB powered backend for a simple ecommerce app, containerized with Docker.

---

## Table of Contents

* [Project Structure](#project-structure)
* [Features & API Overview](#features--api-overview)
* [Code Walkthrough](#code-walkthrough)
* [Running Locally](#running-locally)
* [Running with Docker](#running-with-docker)
* [Environment Variables](#environment-variables)
* [Example API Usage](#example-api-usage)
* [Notes](#notes)

---

## Project Structure

```
/
├── main.py           # FastAPI application with all route and DB logic
├── requirements.txt  # Python dependencies
├── Dockerfile        # Container instructions for deployment
├── .env.example      # Sample for required environment variables
└── README.md         # This documentation
```

## Code Walkthrough

### `main.py`

* **Configuration:**

  * Loads environment variables using `python-dotenv`
  * Connects to MongoDB via the `MONGO_URL` environment variable (defaults to `mongodb://localhost:27017/`)

* **Data Models:**

  * `ProductCreate`: (`name`, `price`, `sizes` — where each size has string `size` and integer `quantity`)
  * `OrderCreate`: (`userId`, and a list of `OrderItem` objects — each with `productId` and `qty`)

* **Helper Function:**

  * `object_id_to_string(obj)`: Recursively turns all MongoDB ObjectIds into strings for JSON responses

* **Routes:**

  * `POST /products`: Adds a product, returns new product ID
  * `GET /products`: Lists products, supports optional name regex & size filtering, paginates results
  * `POST /orders`: Places an order; returns the new order ID
  * `GET /orders/{user_id}`: Lists one user’s orders, with each item expanded to include product name and computes total order cost

* **Pagination:**

  * All listing APIs (`products` and user’s `orders`) include `limit`, `offset`, and next/previous page indices

* **Entry Point:**

  * If run directly, launches the server at `0.0.0.0:8000`

### `Dockerfile`

* Based on `python:3.11-slim`
* Sets `/app` as the working directory
* Installs system and Python dependencies
* Copies all source code into the image
* Launches the app using `python main.py`

---

## Running Locally

1. **Set up your environment variables:**

   * Copy `.env.example` to `.env`:

     ```bash
     cp .env.example .env
     ```
   * Fill in your real MongoDB connection string in `.env`.

2. **Install dependencies and run development server:**

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

3. **Visit** [http://localhost:8000](http://localhost:8000) in your browser to test.

---

## Running with Docker

1. **Build Docker image:**

```bash
docker build -t ecommerce-api .
```

2. **Run the container:**

```bash
docker run --env-file .env -p 8000:8000 ecommerce-api
```

3. The app is live on your machine at [http://localhost:8000](http://localhost:8000).

---

## Environment Variables

* **`.env` file (sample in `.env.example`):**

```env
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/ecommerce?retryWrites=true&w=majority
```

---

## Example API Usage

### Create Product

```json
POST /products
{
    "name": "oneplus15",
    "price": 100,
    "sizes": [
        {
            "size": "Large",
            "quantity": 2
        }
    ]
}
```

![Create Product](./images/CreateProduct.png)

### List Products

```http
GET /products?name=Shirt&size=M&limit=10&offset=0
```

![List Product](./images/GetProducts.png)

### Create Order

```json
POST /orders
{
    "userId": "user_4",
    "items":[
        {
            "productId": "687ab82135127910505f517e",
            "qty": 1
        },
        {
            "productId": "687acb081e59c12739d80ef7",
            "qty": 1
        }
    ]
}
```

![Create Orders](./images/CreateOrders.png)

### Get List of Orders

```http
GET /orders/user_4
```

![List Orders](./images/GetOrders.png)

Returns all of user\_4 orders, each with product details and computed total price.

---

## Notes

* This project assumes a running MongoDB instance. You can use Atlas or run MongoDB locally.

---

<div style="text-align: center">⁂</div>
