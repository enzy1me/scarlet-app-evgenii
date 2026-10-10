"""
Scarlet Roasters' catalog as Python data — the same rows as products.csv and the
coffees table of schema v1.0. This is a stand-in for the database: in Week 6 this
file is deleted and the catalog view reads from the products table instead.

Do not edit prices here; the database is the source of truth, this is a copy.
"""

COFFEES = [
    # coffee, origin, roast_level
    {"coffee": "Colombia Huila", "origin": "Colombia", "roast": "Medium"},
    {"coffee": "Decaf Colombia", "origin": "Colombia (Swiss Water)", "roast": "Medium"},
    {"coffee": "Ethiopia Guji", "origin": "Ethiopia", "roast": "Light"},
    {"coffee": "Guatemala Antigua", "origin": "Guatemala", "roast": "Medium"},
    {"coffee": "Kilimanjaro", "origin": "Tanzania", "roast": "Medium-light"},
    {"coffee": "Midnight Roast", "origin": "Brazil / Sumatra", "roast": "Dark"},
    {"coffee": "Raritan Blend", "origin": "Brazil / Colombia", "roast": "Medium"},
    {"coffee": "Sumatra Mandheling", "origin": "Indonesia", "roast": "Dark"},
]

_ROAST = {c["coffee"]: c["roast"] for c in COFFEES}
_ORIGIN = {c["coffee"]: c["origin"] for c in COFFEES}


def _p(sku, name, coffee, size, retail, active=True):
    return {
        "sku": sku,
        "name": name,
        "coffee": coffee,
        "origin": _ORIGIN.get(coffee, ""),
        "roast": _ROAST.get(coffee, ""),
        "size": size,
        "retail_price": retail,
        "active": active,
    }


PRODUCTS = [
    _p("COL-12", "Colombia Huila 12 oz", "Colombia Huila", "12 oz bag", 17.00),
    _p("COL-2LB", "Colombia Huila 2 lb", "Colombia Huila", "2 lb bag", 42.00),
    _p("COL-5LB", "Colombia Huila 5 lb", "Colombia Huila", "5 lb bulk bag", 94.00),
    _p("DEC-12", "Decaf Colombia 12 oz", "Decaf Colombia", "12 oz bag", 18.00),
    _p("DEC-2LB", "Decaf Colombia 2 lb", "Decaf Colombia", "2 lb bag", 45.00),
    _p("DEC-5LB", "Decaf Colombia 5 lb", "Decaf Colombia", "5 lb bulk bag", 99.00),
    _p("ETH-12", "Ethiopia Guji 12 oz", "Ethiopia Guji", "12 oz bag", 21.00),
    _p("ETH-2LB", "Ethiopia Guji 2 lb", "Ethiopia Guji", "2 lb bag", 52.00),
    _p("ETH-5LB", "Ethiopia Guji 5 lb", "Ethiopia Guji", "5 lb bulk bag", 116.00),
    _p("GUA-12", "Guatemala Antigua 12 oz", "Guatemala Antigua", "12 oz bag", 18.00),
    _p("GUA-2LB", "Guatemala Antigua 2 lb", "Guatemala Antigua", "2 lb bag", 45.00),
    _p("GUA-5LB", "Guatemala Antigua 5 lb", "Guatemala Antigua", "5 lb bulk bag", 99.00),
    _p("KIL-12", "Kilimanjaro 12 oz", "Kilimanjaro", "12 oz bag", 19.00),
    _p("KIL-2LB", "Kilimanjaro 2 lb", "Kilimanjaro", "2 lb bag", 48.00),
    _p("KIL-5LB", "Kilimanjaro 5 lb", "Kilimanjaro", "5 lb bulk bag", 104.00),
    _p("MID-12", "Midnight Roast 12 oz", "Midnight Roast", "12 oz bag", 17.00),
    _p("MID-2LB", "Midnight Roast 2 lb", "Midnight Roast", "2 lb bag", 42.00),
    _p("MID-5LB", "Midnight Roast 5 lb", "Midnight Roast", "5 lb bulk bag", 94.00),
    _p("RAR-12", "Raritan Blend 12 oz", "Raritan Blend", "12 oz bag", 16.00),
    _p("RAR-2LB", "Raritan Blend 2 lb", "Raritan Blend", "2 lb bag", 40.00),
    _p("RAR-5LB", "Raritan Blend 5 lb", "Raritan Blend", "5 lb bulk bag", 88.00),
    _p("SUM-12", "Sumatra Mandheling 12 oz", "Sumatra Mandheling", "12 oz bag", 18.00),
    _p("SUM-2LB", "Sumatra Mandheling 2 lb", "Sumatra Mandheling", "2 lb bag", 45.00),
    _p("SUM-5LB", "Sumatra Mandheling 5 lb", "Sumatra Mandheling", "5 lb bulk bag", 99.00, active=False),
    _p("TOTE", "Scarlet tote bag", None, None, 18.00),
]
