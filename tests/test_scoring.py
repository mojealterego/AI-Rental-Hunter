from rental_hunter.models import Listing, SearchCriteria
from rental_hunter.scoring import total_cost, score_listing

def test_total_cost():
    x=Listing(title="x",direct_url="https://example.com",rent=2000,admin_fee=500,utilities=100)
    assert total_cost(x)==2600

def test_budget_score():
    x=Listing(title="x",direct_url="https://example.com",rent=2000,admin_fee=300)
    x.estimated_monthly_total=2300
    c=SearchCriteria(max_monthly_total=2500)
    assert score_listing(x,c)>50
