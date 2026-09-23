from .models import Listing, SearchCriteria

def total_cost(x: Listing) -> float | None:
    vals=[x.rent,x.admin_fee,x.utilities]
    if not any(v is not None for v in vals): return None
    return round(sum(v or 0 for v in vals),2)

def score_listing(x: Listing, c: SearchCriteria) -> int:
    score=50
    total=x.estimated_monthly_total or total_cost(x)
    if c.max_monthly_total is not None and total is not None:
        score += 25 if total <= c.max_monthly_total else -30
    if c.min_area_m2 is not None and x.area_m2 is not None:
        score += 10 if x.area_m2 >= c.min_area_m2 else -15
    if c.min_rooms is not None and x.rooms is not None:
        score += 8 if x.rooms >= c.min_rooms else -10
    if c.max_rooms is not None and x.rooms is not None:
        score += 4 if x.rooms <= c.max_rooms else -8
    if c.no_agency is True:
        if x.agency is False: score += 7
        elif x.agency is True: score -= 12
    if c.furnished is not None and x.furnished is not None:
        score += 5 if x.furnished == c.furnished else -5
    if c.contract_types and x.contract_type not in c.contract_types:
        score -= 10
    if x.direct_url: score += 5
    if x.risk_level == "high": score -= 20
    elif x.risk_level == "medium": score -= 8
    return max(0,min(100,score))
