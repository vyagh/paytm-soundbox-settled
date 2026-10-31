from . import log

DONE = "done (mock)"


def _act(shop, action, **fields):
    log.add(shop.id, "follow-up", action=f"{action} (mock)", **fields)
    return DONE


def charge_rent(shop, plan):
    return _act(shop, "charge rent", outcome="charged", rule=f"₹{plan.price} a month, {plan.name}")


def hold_rent(shop):
    return _act(shop, "hold rent", outcome="held")


def open_ticket(shop, why):
    return _act(shop, "open ticket", rule=why)


def book_pickup(shop):
    return _act(shop, "book pickup")


def tell_manager(shop, reason):
    return _act(shop, "tell manager", reason=reason)


def send_plan_details(shop):
    return _act(shop, "send plan details")
