from .adapter_factory import AdapterFactory
from .almin7_adapter import Almin7Adapter
from .base_adapter import BaseAdapter
from .grabscholarship_adapter import GrabScholarshipAdapter
from .scholars4dev_adapter import Scholars4DevAdapter
from .wordpress_api_adapter import WordPressApiAdapter

__all__ = [
    "BaseAdapter",
    "WordPressApiAdapter",
    "Almin7Adapter",
    "GrabScholarshipAdapter",
    "Scholars4DevAdapter",
    "AdapterFactory",
]
