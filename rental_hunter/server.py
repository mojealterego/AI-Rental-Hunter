from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
from .models import SearchCriteria, Listing
from .search import search
from .scoring import total_cost, score_listing

mcp=FastMCP(
    "AI Rental Hunter",
    instructions="Search Polish rental listings. Preserve direct listing URLs, separate all recurring costs, identify contract type, flag risks, and never invent missing information.",
    stateless_http=True,
)

@mcp.tool()
def create_rental_watch(city:str="Katowice",max_monthly_total:float|None=None,min_rooms:int|None=None,min_area_m2:float|None=None,no_agency:bool|None=None,contract_types:list[str]|None=None,query:str|None=None,interval_minutes:int=120)->dict:
    """Create a recurring rental search. interval_minutes is the minimum polling interval; recommended 60 or 120."""
    from .store import create_watch
    if interval_minutes < 60: raise ValueError("Minimum monitoring interval is 60 minutes.")
    c=SearchCriteria(city=city,max_monthly_total=max_monthly_total,min_rooms=min_rooms,min_area_m2=min_area_m2,no_agency=no_agency,contract_types=contract_types or [],query=query,max_results=20)
    return {"watch_id":create_watch(c,interval_minutes),"interval_minutes":interval_minutes,"criteria":c.model_dump()}

@mcp.tool()
def list_rental_watches()->dict:
    """List active recurring rental searches."""
    from .store import list_watches
    return {"watches":list_watches()}

@mcp.tool()
def scan_watch_now(watch_id:int)->dict:
    """Run one immediate scan for an existing watch and return only newly discovered listings."""
    import json
    from .store import list_watches,get_new_listings
    from .search import search
    w=next((x for x in list_watches() if x["id"]==watch_id),None)
    if not w: return {"error":"watch_not_found"}
    c=SearchCriteria(**json.loads(w["criteria"]))
    new=get_new_listings(watch_id,search(c))
    return {"watch_id":watch_id,"new_listings":[x.model_dump() for x in new]}

@mcp.tool()
def search_rentals(city:str="Katowice",max_monthly_total:float|None=None,min_rooms:int|None=None,max_rooms:int|None=None,min_area_m2:float|None=None,max_area_m2:float|None=None,districts:list[str]|None=None,no_agency:bool|None=None,furnished:bool|None=None,available_now:bool|None=None,contract_types:list[str]|None=None,query:str|None=None,max_results:int=20)->dict:
    """Find current Polish rental listings and return direct URLs plus normalized costs and risk signals."""
    c=SearchCriteria(city=city,max_monthly_total=max_monthly_total,min_rooms=min_rooms,max_rooms=max_rooms,min_area_m2=min_area_m2,max_area_m2=max_area_m2,districts=districts or [],no_agency=no_agency,furnished=furnished,available_now=available_now,contract_types=contract_types or [],query=query,max_results=max_results)
    return {"criteria":c.model_dump(),"listings":[x.model_dump() for x in search(c)]}

@mcp.tool()
def rank_listings(listings:list[dict],city:str="Katowice",max_monthly_total:float|None=None,min_rooms:int|None=None,min_area_m2:float|None=None,no_agency:bool|None=None)->dict:
    """Rank already collected listings against renter criteria."""
    c=SearchCriteria(city=city,max_monthly_total=max_monthly_total,min_rooms=min_rooms,min_area_m2=min_area_m2,no_agency=no_agency)
    xs=[]
    for raw in listings:
        x=Listing(**raw); x.estimated_monthly_total=total_cost(x); x.score=score_listing(x,c); xs.append(x)
    return {"listings":[x.model_dump() for x in sorted(xs,key=lambda z:z.score,reverse=True)]}

@mcp.tool()
def calculate_total_cost(rent:float|None=None,admin_fee:float|None=None,utilities:float|None=None,deposit:float|None=None)->dict:
    """Calculate recurring monthly housing cost and one-off deposit."""
    monthly=round(sum(v or 0 for v in [rent,admin_fee,utilities]),2)
    return {"monthly_total":monthly,"deposit":deposit,"first_month_known_cost":round(monthly+(deposit or 0),2)}

@mcp.tool()
def analyze_listing(title:str,url:str,rent:float|None=None,admin_fee:float|None=None,utilities:float|None=None,deposit:float|None=None,contract_type:str="unknown",agency:bool|None=None)->dict:
    """Screen a single listing for basic cost and contractual risk signals."""
    risks=[]
    if not url.startswith(("http://","https://")): risks.append("URL is not a full web URL.")
    if contract_type=="assignment": risks.append("Cesja: obtain written confirmation from the original landlord/manager before paying.")
    if contract_type=="institutional": risks.append("Najem instytucjonalny: verify the full agreement and notarial statement requirements.")
    if agency is True: risks.append("Agency involved: verify commission and who pays it.")
    monthly=round(sum(v or 0 for v in [rent,admin_fee,utilities]),2)
    return {"title":title,"direct_url":url,"monthly_total":monthly,"deposit":deposit,"contract_type":contract_type,"risk_level":"high" if len(risks)>=2 else ("medium" if risks else "low"),"risk_notes":risks}

app=mcp.streamable_http_app(stateless_http=True)

if __name__=="__main__":
    import asyncio, threading, uvicorn
    from .monitor import monitor_loop
    threading.Thread(target=lambda: asyncio.run(monitor_loop()),daemon=True).start()
    uvicorn.run("rental_hunter.server:app",host="0.0.0.0",port=8000)
