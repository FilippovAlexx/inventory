from .products import router as products
from .locations import router as locations
from .inventory import router as inventory
from .purchase_orders import router as purchase

__all__ = ["products", "locations", "inventory", "purchase"]
