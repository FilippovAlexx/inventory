from .auth import router as auth
from .products import router as products
from .locations import router as locations
from .inventory import router as inventory
from .purchase_orders import router as purchase_orders

__all__ = ["auth", "products", "locations", "inventory", "purchase_orders"]
