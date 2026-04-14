import random
from datetime import datetime, timedelta
from app.db.database import SessionLocal
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderStatus

def generate_massive_data():
    db = SessionLocal()
    
    print("Fetching existing users and products...")
    users = db.query(User).all()
    products = db.query(Product).all()
    
    if not users or not products:
        print("Error: No users or products found. Please run seed_db.py first to establish baseline.")
        return
        
    print(f"Found {len(users)} users and {len(products)} products.")
    
    target_records = 5000
    print(f"Generating {target_records} new orders to simulate thousands of records...")
    
    statuses = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.CANCELLED]
    now = datetime.now()
    
    orders = []
    
    for i in range(target_records):
        user = random.choice(users)
        product = random.choice(products)
        
        if user.segment == "Enterprise":
            quantity = random.randint(10, 100)
        elif user.segment == "SMB":
            quantity = random.randint(3, 15)
        else:
            quantity = random.randint(1, 3)
            
        total_price = product.price * quantity
        
        # Spread data out over the last 90 days to populate timeline charts fully
        days_ago = random.randint(0, 90)
        # Randomize minutes and seconds as well
        delta = timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59), seconds=random.randint(0, 59))
        created_at = now - delta
        
        # Assign probabilities to order statuses
        status_weights = [0.1, 0.1, 0.2, 0.55, 0.05]
        status = random.choices(statuses, weights=status_weights, k=1)[0]
        
        order = Order(
            customer_id=user.id,
            product_id=product.id,
            quantity=quantity,
            total_price=total_price,
            status=status,
            created_at=created_at
        )
        orders.append(order)
        
        # We commit in batches to preserve memory and increase insertion speed
        if len(orders) >= 1000:
            db.add_all(orders)
            db.commit()
            print(f"Inserted batch of 1000 orders...")
            orders = []
            
    # Commit any remaining orders
    if orders:
        db.add_all(orders)
        db.commit()
        print(f"Inserted final batch of {len(orders)} orders...")
        
    print(f"Successfully generated and inserted {target_records} new rows into the database!")

if __name__ == "__main__":
    generate_massive_data()
