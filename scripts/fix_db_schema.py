
from app.db.database import SessionLocal
from sqlalchemy import text

def add_cost_price_column():
    db = SessionLocal()
    try:
        print("Checking if 'cost_price' column exists...")
        # Check if table exists and column exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='products' AND column_name='cost_price';
        """)
        result = db.execute(check_query).fetchone()
        
        if not result:
            print("Column 'cost_price' not found. Adding it now...")
            add_query = text("ALTER TABLE products ADD COLUMN cost_price FLOAT;")
            db.execute(add_query)
            
            print("Initializing cost_price to 70% of price...")
            update_query = text("UPDATE products SET cost_price = price * 0.7 WHERE cost_price IS NULL;")
            db.execute(update_query)
            
            db.commit()
            print("Schema updated successfully!")
        else:
            print("Column 'cost_price' already exists.")
            
    except Exception as e:
        db.rollback()
        print(f"Error updating schema: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_cost_price_column()
