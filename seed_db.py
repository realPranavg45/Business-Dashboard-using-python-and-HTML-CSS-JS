import random
from datetime import datetime, timedelta
from app.db.database import SessionLocal
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.core.security import get_password_hash

def seed_database():
    db = SessionLocal()
    
    # 1. Clear existing data to prevent duplicates (optional, but good for clean seeding)
    print("Clearing existing data...")
    db.query(Order).delete()
    db.query(Product).delete()
    db.query(User).delete()
    db.commit()

    # 2. Seed Users
    print("Seeding users...")
    users = []
    user_data = [
        {"full_name": "Admin User", "email": "admin@example.com", "hashed_password": get_password_hash("password123"), "is_admin": True},
        {"full_name": "Alice Smith", "email": "alice@example.com", "hashed_password": get_password_hash("password123"), "is_admin": False},
        {"full_name": "Bob Johnson", "email": "bob@example.com", "hashed_password": get_password_hash("password123"), "is_admin": False},
        {"full_name": "Charlie Brown", "email": "charlie@example.com", "hashed_password": get_password_hash("password123"), "is_admin": False},
        {"full_name": "Diana Prince", "email": "diana@example.com", "hashed_password": get_password_hash("password123"), "is_admin": False},
    ]
    for u_dict in user_data:
        user = User(**u_dict)
        db.add(user)
        users.append(user)
    db.commit()
    for u in users:
        db.refresh(u)

    # 3. Seed Products
    print("Seeding products...")
    products = []
    product_data = [
        {"name": "Wireless Mouse", "category": "Electronics", "price": 29.99, "stock_quantity": 150, "sku": "WM-01"},
        {"name": "Mechanical Keyboard", "category": "Electronics", "price": 89.50, "stock_quantity": 80, "sku": "MK-02"},
        {"name": "USB-C Hub", "category": "Accessories", "price": 45.00, "stock_quantity": 200, "sku": "USB-03"},
        {"name": "Noise Cancelling Headphones", "category": "Electronics", "price": 199.99, "stock_quantity": 40, "sku": "HP-04"},
        {"name": "Ergonomic Office Chair", "category": "Furniture", "price": 249.99, "stock_quantity": 15, "sku": "OC-05"},
        {"name": "Standing Desk", "category": "Furniture", "price": 399.00, "stock_quantity": 10, "sku": "SD-06"},
        {"name": "27-inch 4K Monitor", "category": "Electronics", "price": 329.99, "stock_quantity": 30, "sku": "MN-07"},
        {"name": "Webcam 1080p", "category": "Accessories", "price": 79.99, "stock_quantity": 100, "sku": "WC-08"},
        {"name": "Laptop Stand", "category": "Accessories", "price": 35.50, "stock_quantity": 120, "sku": "LS-09"},
        {"name": "Bluetooth Speaker", "category": "Electronics", "price": 59.99, "stock_quantity": 60, "sku": "BS-10"},
    ]
    for p_dict in product_data:
        product = Product(**p_dict)
        db.add(product)
        products.append(product)
    db.commit()
    for p in products:
        db.refresh(p)

    # 4. Seed Orders
    print("Seeding orders (randomized dates)...")
    statuses = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.CANCELLED]
    
    now = datetime.now()
    
    for i in range(50):
        # Pick random user and product
        user = random.choice(users[1:]) # Don't use admin for buying
        product = random.choice(products)
        
        # Random quantity 1-3
        quantity = random.randint(1, 3)
        total_price = product.price * quantity
        
        # Assign random creation date within the last 30 days
        random_days_ago = random.randint(1, 30)
        created_at_time = now - timedelta(days=random_days_ago, hours=random.randint(0, 23))
        
        order = Order(
            customer_id=user.id,
            product_id=product.id,
            quantity=quantity,
            total_price=total_price,
            status=random.choice(statuses),
            created_at=created_at_time
        )
        db.add(order)
    
    db.commit()
    print("Successfully seeded database with Users, Products, and Orders!")

if __name__ == "__main__":
    seed_database()
