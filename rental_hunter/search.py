import json, re, hashlib
from urllib.parse import urlparse
from openai import OpenAI
from .models import SearchCriteria, Listing
from .scoring import score_listing, total_cost

SYSTEM = """You are AI Rental Hunter, a Polish rental-listing research agent.
Search public web pages for current residential rental offers. Never invent data.
Always preserve the direct individual listing URL when available. Do not return search-result pages as the listing URL.
Separate advertised rent, administration, utilities and deposit.
Identify contract type when stated: private, occasional, institutional, assignment, agency, unknown.
Flag uncertainty and suspicious conditions. Return JSON only.
"""

def clean_url(url:str)->str:
    p=urlparse(url.strip())
    return f"{p.scheme}://{p.netloc}{p.path}" if p.scheme and p.netloc else url.strip()

def lid(url:str)->str:
    return hashlib.sha256(clean_url(url).encode()).hexdigest()[:16]

def search(criteria: SearchCriteria) -> list[Listing]:
    key=__import__("os").getenv("OPENAI_API_KEY")
    if not key: raise RuntimeError("OPENAI_API_KEY is required")
    model=__import__("os").getenv("OPENAI_MODEL","gpt-5.6")
    client=OpenAI(api_key=key)
    prompt=f"""Perform a DEEP WEB RESEARCH pass. Search multiple independent sources and domains, including Polish rental portals, local real-estate sites, agency sites, classifieds, public/indexed social-media pages and other publicly searchable sources. Do not stop after the first relevant domain. Try alternative Polish query formulations, district names and synonyms. For each result verify the individual listing URL when possible.Find current rental apartment listings matching:
{json.dumps(criteria.model_dump(),ensure_ascii=False,indent=2)}
Search Polish portals and property sites. Prefer individual listing pages. Return up to {criteria.max_results} distinct offers.
JSON schema:
{{"listings":[{{"title":"string","direct_url":"https://...","source":"string","city":"string|null","district":"string|null","address":"string|null","area_m2":"number|null","rooms":"number|null","rent":"number|null","admin_fee":"number|null","utilities":"number|null","deposit":"number|null","agency":"boolean|null","contract_type":"private|occasional|institutional|assignment|agency|unknown","available_from":"string|null","furnished":"boolean|null","risk_level":"low|medium|high|unknown","risk_notes":["string"],"why_matches":["string"]}}]}}
Only include URLs actually found in the web research. Missing values must be null."""
    r=client.responses.create(model=model,tools=[{"type":"web_search"}],input=[{"role":"system","content":SYSTEM},{"role":"user","content":prompt}])
    raw=r.output_text
    m=re.search(r"\{.*\}",raw,re.S)
    if not m: return []
    data=json.loads(m.group(0))
    out=[]; seen=set()
    for raw_item in data.get("listings",[]):
        url=raw_item.get("direct_url")
        if not url: continue
        url=clean_url(url); keyid=lid(url)
        if keyid in seen: continue
        seen.add(keyid)
        item=Listing(**{**raw_item,"direct_url":url})
        item.estimated_monthly_total=total_cost(item)
        if criteria.max_monthly_total is not None and item.estimated_monthly_total > criteria.max_monthly_total:
            continue
        if criteria.no_agency is True and item.agency is True:
            continue
        if criteria.min_rooms is not None and item.rooms is not None and item.rooms < criteria.min_rooms:
            continue
        if criteria.max_rooms is not None and item.rooms is not None and item.rooms > criteria.max_rooms:
            continue
        if criteria.min_area_m2 is not None and item.area_m2 is not None and item.area_m2 < criteria.min_area_m2:
            continue
        if criteria.max_area_m2 is not None and item.area_m2 is not None and item.area_m2 > criteria.max_area_m2:
            continue
        if criteria.furnished is not None and item.furnished is not None and item.furnished != criteria.furnished:
            continue
        if criteria.contract_types and item.contract_type not in criteria.contract_types:
            continue
        item.score=score_listing(item,criteria)
        out.append(item)
    return sorted(out,key=lambda x:x.score,reverse=True)[:criteria.max_results]
