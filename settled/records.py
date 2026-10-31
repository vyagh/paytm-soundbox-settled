import json
from pathlib import Path

from .models import Plan, Shop

SHOPS = Path(__file__).resolve().parent.parent / "data" / "shops.json"


def _read():
    with open(SHOPS, encoding="utf-8") as f:
        return json.load(f)


def shop_ids():
    return list(_read()["shops"])


def _signup(data, s):
    signup = s.get("signup")
    if not signup:
        return signup
    man = data["salesmen"].get(signup.get("salesman"), {})
    return {**signup, "salesman": {"id": signup.get("salesman"), "name": man.get("name", "the salesman"), "say": man.get("say", {})}}


def load(shop_id):
    data = _read()
    if shop_id not in data["shops"]:
        raise KeyError(f"no shop {shop_id!r}, known shops: {', '.join(data['shops'])}")
    s = data["shops"][shop_id]
    return Shop(
        id=shop_id,
        name=s["name"],
        owner=s.get("owner"),
        signup=_signup(data, s),
        delivery=s.get("delivery"),
        returned=s.get("return"),
        plans=[Plan(**p) for p in data["plans"]],
        language=s.get("language", "hi"),
        say=s.get("say", {}),
        mobile=s.get("mobile"),
    )


def record(shop_id):
    """The shop's record as Paytm's systems would show it, for the board."""
    data = _read()
    s = {k: v for k, v in data["shops"][shop_id].items() if k != "say"}
    signup = _signup(data, s)
    if signup:
        s["signup"] = {**signup, "salesman": {"id": signup["salesman"]["id"], "name": signup["salesman"]["name"]}}
    return s


def missing(shop):
    names = {"sign-up": shop.signup, "delivery": shop.delivery, "return": shop.returned}
    return [name for name, record in names.items() if record is None]
