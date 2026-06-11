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
    building_structure: str = ""     # 構造・工法
    zoning: str = ""                 # 用途地域
    building_ratio: str = ""         # 建ぺい率・容積率
    private_road: str = ""           # 私道負担・道路
    other_restrictions: str = ""     # その他制限事項
    handover_date: str = ""          # 引渡可能時期
    transaction_area: str = ""       # 売買対象面積
    features: str = ""               # JSON: kitchen/bath/floor-plan amenities
    surroundings: str = ""           # JSON: nearby facilities with distances
    agent_company: str = ""          # 不動産会社名 (公開義務情報)
    agent_license: str = ""          # 免許番号 (公開義務情報)
    next_update: str = ""            # 次回更新予定日 — skip re-scrape until this date
