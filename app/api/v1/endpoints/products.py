"""
app/api/v1/endpoints/products.py
---------------------------------
Product API endpoints for CRUD operations.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.schemas.common import PaginatedResponse
from app.api.deps import get_current_user, get_current_active_admin
from app.models.user import User
from sqlalchemy import cast, String

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[ProductResponse])
def get_products(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    sort_by: str = "id",
    sort_order: str = "desc",
    category: Optional[str] = None
):
    """List products with pagination, search, and category filtering."""
    query = db.query(Product).filter(Product.is_active == True)
    
    if category:
        query = query.filter(Product.category == category)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(search_filter)) | 
            (Product.sku.ilike(search_filter)) | 
            (Product.category.ilike(search_filter))
        )
        
    total = query.count()
    
    # Sorting
    sort_attr = getattr(Product, sort_by, Product.id)
    if sort_order == "desc":
        query = query.order_by(sort_attr.desc())
    else:
        query = query.order_by(sort_attr.asc())
        
    products = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": products,
        "page": (skip // limit) + 1,
        "limit": limit
    }


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product_in: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_admin)):
    """Create a new product."""
    # Check if SKU already exists
    if product_in.sku:
        existing = db.query(Product).filter(Product.sku == product_in.sku).first()
        if existing:
            raise HTTPException(status_code=400, detail="Product with this SKU already exists")
            
    db_product = Product(**product_in.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product_in: ProductUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_admin)):
    """Update product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
        
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_admin)):
    """Deactivate product (soft delete)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    product.is_active = False
    db.commit()
    return None

