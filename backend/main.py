from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

app = FastAPI(title="Mock API Server", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class User(BaseModel):
    id: Optional[str] = None
    username: str
    email: str
    full_name: Optional[str] = None
    created_at: Optional[datetime] = None

class Product(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0
    created_at: Optional[datetime] = None

class Order(BaseModel):
    id: Optional[str] = None
    user_id: str
    products: List[dict]
    total: float
    status: str = "pending"
    created_at: Optional[datetime] = None

# In-memory storage (mock database)
users_db = {}
products_db = {}
orders_db = {}

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Welcome to Mock API Server",
        "version": "1.0.0",
        "endpoints": {
            "users": "/users",
            "products": "/products",
            "orders": "/orders",
            "docs": "/docs"
        }
    }

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# User endpoints
@app.get("/users", response_model=List[User])
def get_users():
    return list(users_db.values())

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.post("/users", response_model=User)
def create_user(user: User):
    user.id = str(uuid.uuid4())
    user.created_at = datetime.now()
    users_db[user.id] = user
    return user

@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: str, user: User):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    user.id = user_id
    user.created_at = users_db[user_id].created_at
    users_db[user_id] = user
    return user

@app.delete("/users/{user_id}")
def delete_user(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    del users_db[user_id]
    return {"message": "User deleted successfully"}

# Product endpoints
@app.get("/products", response_model=List[Product])
def get_products():
    return list(products_db.values())

@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: str):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return products_db[product_id]

@app.post("/products", response_model=Product)
def create_product(product: Product):
    product.id = str(uuid.uuid4())
    product.created_at = datetime.now()
    products_db[product.id] = product
    return product

@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: str, product: Product):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    product.id = product_id
    product.created_at = products_db[product_id].created_at
    products_db[product_id] = product
    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: str):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    del products_db[product_id]
    return {"message": "Product deleted successfully"}

# Order endpoints
@app.get("/orders", response_model=List[Order])
def get_orders():
    return list(orders_db.values())

@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders_db[order_id]

@app.post("/orders", response_model=Order)
def create_order(order: Order):
    # Validate user exists
    if order.user_id not in users_db:
        raise HTTPException(status_code=400, detail="User not found")
    
    order.id = str(uuid.uuid4())
    order.created_at = datetime.now()
    orders_db[order.id] = order
    return order

@app.put("/orders/{order_id}/status")
def update_order_status(order_id: str, status: str):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    orders_db[order_id].status = status
    return {"message": f"Order status updated to {status}"}

# Add some sample data on startup
@app.on_event("startup")
def startup_event():
    # Add sample users
    sample_user = User(
        id="1",
        username="john_doe",
        email="john@example.com",
        full_name="John Doe",
        created_at=datetime.now()
    )
    users_db[sample_user.id] = sample_user
    
    # Add sample products
    sample_products = [
        Product(
            id="1",
            name="Laptop",
            description="High-performance laptop",
            price=999.99,
            stock=10,
            created_at=datetime.now()
        ),
        Product(
            id="2",
            name="Mouse",
            description="Wireless mouse",
            price=29.99,
            stock=50,
            created_at=datetime.now()
        ),
        Product(
            id="3",
            name="Keyboard",
            description="Mechanical keyboard",
            price=79.99,
            stock=25,
            created_at=datetime.now()
        )
    ]
    
    for product in sample_products:
        products_db[product.id] = product

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)