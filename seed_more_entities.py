import random
import uuid
from datetime import datetime, timedelta
from app.db.database import SessionLocal
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.core.security import get_password_hash

def seed_more_entities():
    db = SessionLocal()
    
    # 1. Generate Users (Customers)
    num_users = 250
    print(f"Generating {num_users} new users...")
    segments = ["Enterprise", "SMB", "Retail", "Individual"]
    domains = ["gmail.com", "yahoo.com", "corp.com", "startup.io", "tech.net", "global.org"]
    
    first_names = ["James", "Maria", "Robert", "Elena", "Michael", "Sophia", "David", "Wei", "William", "Isabella", "John", "Mia", "Joseph", "Charlotte", "Charles", "Amelia", "Thomas", "Harper", "Christopher", "Evelyn"]
    last_names = ["Smith", "Garcia", "Johnson", "Martinez", "Williams", "Rodriguez", "Brown", "Hernandez", "Jones", "Lopez", "Miller", "Gonzalez", "Davis", "Perez", "Taylor"]
    
    users_to_add = []
    
    for _ in range(num_users):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        uid = str(uuid.uuid4())[:6]
        domain = random.choice(domains)
        email = f"{fname.lower()}.{lname.lower()}_{uid}@{domain}"
        
        user = User(
            full_name=f"{fname} {lname}",
            email=email,
            hashed_password=get_password_hash("password123"),
            is_admin=False,
            segment=random.choice(segments)
        )
        users_to_add.append(user)
        
    db.add_all(users_to_add)
    db.commit()
    print("Users successfully committed.")

    # 2. Generate Products
    num_products = 50
    print(f"Generating {num_products} new products...")
    categories = ["Hardware", "Software", "Peripherals", "Furniture", "Services", "Networking"]
    
    adjectives = ["Pro", "Ultra", "Max", "Enterprise", "Lite", "Advanced", "Basic", "Cloud", "Secure", "Smart"]
    nouns = ["Server", "License", "Router", "Switch", "Monitor", "Desk", "Subscription", "Firewall", "Storage", "Array"]
    
    products_to_add = []
    for _ in range(num_products):
        cat = random.choice(categories)
        base_name = f"{random.choice(adjectives)} {random.choice(nouns)}"
        uid = str(uuid.uuid4())[:4].upper()
        
        # Price correlation to category
        if cat in ["Hardware", "Server"]:
            price = random.uniform(500.0, 10000.0)
            stock = random.randint(0, 100)
        elif cat == "Software":
            price = random.uniform(20.0, 1500.0)
            stock = random.randint(500, 5000) # Infinite stock basically
        else:
            price = random.uniform(10.0, 600.0)
            stock = random.randint(20, 500)
            
        product = Product(
            name=f"{base_name} {uid}",
            category=cat,
            price=round(price, 2),
            stock_quantity=stock,
            sku=f"{cat[:3].upper()}-{uid}"
        )
        products_to_add.append(product)
        
    db.add_all(products_to_add)
    db.commit()
    print("Products successfully committed.")

    # 3. Fetch all current DB state
    users = db.query(User).all()
    products = db.query(Product).all()

    # 4. Generate Mixed Orders explicitly for the new distribution
    num_orders = 8000
    print(f"Generating {num_orders} orders using the expanded demographic set...")
    statuses = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.CANCELLED]
    now = datetime.now()
    
    orders = []
    for _ in range(num_orders):
        user = random.choice(users)
        product = random.choice(products)
        
        if user.segment == "Enterprise":
            quantity = random.randint(10, 100)
        elif user.segment == "SMB":
            quantity = random.randint(3, 15)
        else:
            quantity = random.randint(1, 4)
            
        total_price = product.price * quantity
        days_ago = random.randint(0, 120)  # Spread across 4 months
        delta = timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
        
        status_weights = [0.1, 0.15, 0.15, 0.55, 0.05]
        status = random.choices(statuses, weights=status_weights, k=1)[0]
        
        order = Order(
            customer_id=user.id,
            product_id=product.id,
            quantity=quantity,
            total_price=total_price,
            status=status,
            created_at=now - delta
        )
        orders.append(order)
        
        if len(orders) >= 1000:
            db.add_all(orders)
            db.commit()
            orders = []
            
    if orders:
        db.add_all(orders)
        db.commit()
        
    print(f"Success! Total rows added: {num_users} Users, {num_products} Products, {num_orders} Orders.")

if __name__ == "__main__":
    seed_more_entities()
