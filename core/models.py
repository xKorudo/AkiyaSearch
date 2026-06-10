from dataclasses import dataclass
from typing import Optional

@dataclass
class Listing:
    id: str
    title: str
    prefecture: str
    city: str
    price_jpy: Optional[int]
    price_label: str
    size_m2: Optional[float]
    land_m2: Optional[float]
    image_url: str
    source_url: str
    source: str
    description: str
    title_en: str = ""
    description_en: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None
    rooms: str = ""
    built_year: Optional[int] = None
    condition: str = ""
    images: str = ""   # JSON array of image URLs
    traffic: str = ""
    first_seen: str = ""
    listed_at: Optional[str] = None  # SUUMO 情報提供日 as YYYY-MM-DD
