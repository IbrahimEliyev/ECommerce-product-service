# src/app/repositories/v1/product.py
from sqlalchemy import delete, and_
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from .base import BaseRepository
from src.app.models.v1 import Product, ProductCategory, Category
from src.app.schemas.v1 import ProductCreate

class ProductRepository(BaseRepository[Product]):
    def __init__(self, db_session: Session):
        super().__init__(Product, db_session)

    def create_with_categories(self, obj_in: ProductCreate) -> Product:
        # ✅ FIXED: Use category_ids
        db_product = self.create(obj_in)
        for category_id in obj_in.category_ids:  # ✅ category_ids
            pc = ProductCategory(product_id=db_product.id, category_id=category_id)
            self.db_session.add(pc)
        self.db_session.commit()
        return db_product

    def update_with_categories(self, id: UUID, obj_in: ProductCreate) -> Optional[Product]:
        db_product = self.update(id, obj_in)
        if db_product:
            # Replace categories
            self.db_session.execute(delete(ProductCategory).where(ProductCategory.product_id == id))
            for category_id in obj_in.category_ids:  # ✅ category_ids
                pc = ProductCategory(product_id=id, category_id=category_id)
                self.db_session.add(pc)
            self.db_session.commit()
        return db_product

    # ✅ NEW METHODS FOR FULL MANY-TO-MANY
    def get_categories_for_product(self, product_id: UUID) -> List[Category]:
        """Get ALL categories for a product"""
        return self.db_session.query(Category).join(
            ProductCategory,
            ProductCategory.category_id == Category.id
        ).filter(ProductCategory.product_id == product_id).all()

    def add_category(self, product_id: UUID, category_id: UUID) -> bool:
        """Add SINGLE category to product"""
        existing = self.db_session.query(ProductCategory).filter(
            and_(
                ProductCategory.product_id == product_id,
                ProductCategory.category_id == category_id
            )
        ).first()
        if existing:
            return False
        
        pc = ProductCategory(product_id=product_id, category_id=category_id)
        self.db_session.add(pc)
        self.db_session.commit()
        return True

    def remove_category(self, product_id: UUID, category_id: UUID) -> bool:
        """Remove SINGLE category from product"""
        pc = self.db_session.query(ProductCategory).filter(
            and_(
                ProductCategory.product_id == product_id,
                ProductCategory.category_id == category_id
            )
        ).first()
        if pc:
            self.db_session.delete(pc)
            self.db_session.commit()
            return True
        return False

    def get_products_in_category(self, category_id: UUID, skip: int = 0, limit: int = 100) -> List[Product]:
        """Get ALL products in a category"""
        return self.db_session.query(Product).join(
            ProductCategory,
            ProductCategory.product_id == Product.id
        ).filter(ProductCategory.category_id == category_id).offset(skip).limit(limit).all()