import random
from datetime import datetime, timedelta
from app.db.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.core.security import get_password_hash

def seed_database():
    # Ensure tables exist
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    print("Seeding users with segments...")
    segments = ["Enterprise", "SMB", "Retail", "Individual"]
    user_data = [
        {"full_name": "Admin User", "email": "admin@example.com", "hashed_password": get_password_hash("password123"), "is_admin": True, "segment": "Enterprise"},
        {"full_name": "Global Corp", "email": "business@global.com", "hashed_password": get_password_hash("password123"), "is_admin": False, "segment": "Enterprise"},
        {"full_name": "Local Shop", "email": "owner@local.com", "hashed_password": get_password_hash("password123"), "is_admin": False, "segment": "SMB"},
        {"full_name": "John Retail", "email": "john@gmail.com", "hashed_password": get_password_hash("password123"), "is_admin": False, "segment": "Retail"},
        {"full_name": "Sarah Smith", "email": "sarah@yahoo.com", "hashed_password": get_password_hash("password123"), "is_admin": False, "segment": "Individual"},
    ]
    
    users = []
    for u_dict in user_data:
        user = User(**u_dict)
        db.add(user)
        users.append(user)
    db.commit()

    print("Seeding diverse products...")
    product_data = [
        {"name": "Enterprise Server X1", "category": "Hardware", "price": 4999.99, "stock_quantity": 5, "sku": "SRV-X1"},
        {"name": "Standard Laptop", "category": "Hardware", "price": 1200.00, "stock_quantity": 50, "sku": "LP-02"},
        {"name": "Cloud License Pro", "category": "Software", "price": 299.00, "stock_quantity": 1000, "sku": "SW-LIC"},
        {"name": "Security Suite", "category": "Software", "price": 550.00, "stock_quantity": 500, "sku": "SW-SEC"},
        {"name": "Ultra-Wide Monitor", "category": "Peripherals", "price": 450.00, "stock_quantity": 30, "sku": "PR-MN"},
        {"name": "Mechanical Keyboard", "category": "Peripherals", "price": 120.00, "stock_quantity": 100, "sku": "PR-KB"},
        {"name": "Basic Mouse", "category": "Peripherals", "price": 25.00, "stock_quantity": 200, "sku": "PR-MS"},
        {"name": "Ergonomic Desk", "category": "Furniture", "price": 850.00, "stock_quantity": 12, "sku": "FN-DK"},
    ]
    
    products = []
    for p_dict in product_data:
        product = Product(**p_dict)
        db.add(product)
        products.append(product)
    db.commit()

    print("Seeding randomized orders...")
    statuses = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.SHIPPED, OrderStatus.DELIVERED]
    
    now = datetime.now()
    
    # Generate 100 random orders over the last 60 days
    for i in range(100):
        user = random.choice(users)
        product = random.choice(products)
        
        # Quantity depends on segment
        if user.segment == "Enterprise":
            quantity = random.randint(10, 50)
        else:
            quantity = random.randint(1, 4)
            
        total_price = product.price * quantity
        
        # Random date over last 60 days
        days_ago = random.randint(0, 60)
        created_at = now - timedelta(days=days_ago, hours=random.randint(0, 23))
        
        order = Order(
            customer_id=user.id,
            product_id=product.id,
            quantity=quantity,
            total_price=total_price,
            status=random.choice(statuses),
            created_at=created_at
        )
        db.add(order)
    
    db.commit()
    print("Database re-seeded successfully with 60 days of data, 4 segments, and 4 categories.")

if __name__ == "__main__":
    seed_database()
