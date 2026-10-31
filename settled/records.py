import json
from pathlib import Path

from .models import Plan, Shop

SHOPS = Path(__file__).resolve().parent.parent / "data" / "shops.json"


def _read():
    with open(SHOPS, encoding="utf-8") as f:
        return json.load(f)


def shop_ids():
    return list(_read()["shops"])


def load(shop_id):
    data = _read()
    if shop_id not in data["shops"]:
        raise KeyError(f"no shop {shop_id!r}, known shops: {', '.join(data['shops'])}")
    s = data["shops"][shop_id]
    return Shop(
        id=shop_id,
        name=s["name"],
        owner=s.get("owner"),
        signup=s.get("signup"),
        delivery=s.get("delivery"),
        returned=s.get("return"),
        plans=[Plan(**p) for p in data["plans"]],
        language=s.get("language", "hi"),
    )


def missing(shop):
    names = {"sign-up": shop.signup, "delivery": shop.delivery, "return": shop.returned}
    return [name for name, record in names.items() if record is None]
