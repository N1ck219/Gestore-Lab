from .main import register_main_routes
from .products import register_products_routes
from .lotti import register_lotti_routes
from .scarichi import register_scarichi_routes
from .etichette import register_etichette_routes
from .settings import register_settings_routes
from .stats import register_stats_routes
from .search import register_search_routes

def init_routes(app):
    register_main_routes(app)
    register_products_routes(app)
    register_lotti_routes(app)
    register_scarichi_routes(app)
    register_etichette_routes(app)
    register_settings_routes(app)
    register_stats_routes(app)
    register_search_routes(app)

