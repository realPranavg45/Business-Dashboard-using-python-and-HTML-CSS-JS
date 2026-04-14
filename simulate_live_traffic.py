import time
import random
from datetime import datetime
from app.db.database import SessionLocal
from app.models.user import User
from app.models.product import Product
from app.models.order import Order, OrderStatus

def simulate_live_traffic():
    print("Starting Live Traffic Simulator...")
    print("This script will continuously generate new orders in real-time.")
    print("Keep this running in the background and watch your 'Live Monitoring' dashboard light up!\n")
    print("Press Ctrl+C to stop.\n")
    
    db = SessionLocal()
    users = db.query(User).all()
    products = db.query(Product).all()
    
    if not users or not products:
        print("Error: Make sure the DB is seeded with users and products first.")
        return

    statuses = [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.SHIPPED, OrderStatus.DELIVERED]
    
    while True:
        # Sleep randomly between 1 and 4 seconds
        delay = random.uniform(1.0, 4.0)
        time.sleep(delay)
        
        user = random.choice(users)
        product = random.choice(products)
        quantity = random.randint(1, 5)
        
        order = Order(
            customer_id=user.id,
            product_id=product.id,
            quantity=quantity,
            total_price=product.price * quantity,
            status=random.choice(statuses),
            created_at=datetime.now()
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Live Order Inserted -> User: {user.full_name} | Product: {product.name} | Total: ${order.total_price:,.2f}")

if __name__ == "__main__":
    try:
        simulate_live_traffic()
    except KeyboardInterrupt:
        print("\nLive traffic simulation stopped.")
