import asyncio, json, time
from .store import list_watches, get_new_listings, create_watch
from .models import SearchCriteria
from .search import search

DEFAULT_INTERVAL_MINUTES = 120

def ensure_default_watch():
    watches = list_watches()
    if watches:
        return watches
    criteria = SearchCriteria(
        city="Katowice",
        max_monthly_total=2500,
        max_results=20,
        query="mieszkanie wynajem Katowice do 2500 zł opłaty",
    )
    create_watch(criteria, DEFAULT_INTERVAL_MINUTES)
    return list_watches()

async def monitor_loop():
    ensure_default_watch()
    last = {}
    while True:
        watches = list_watches()
        now = time.time()
        for w in watches:
            interval = max(60, int(w["interval_minutes"]) * 60)
            if now - last.get(w["id"], 0) < interval:
                continue
            last[w["id"]] = now
            try:
                criteria = SearchCriteria(**json.loads(w["criteria"]))
                results = search(criteria)
                new = get_new_listings(w["id"], results)
                print(json.dumps({
                    "event": "new_listings",
                    "watch_id": w["id"],
                    "count": len(new),
                    "total_found": len(results),
                    "listings": [x.model_dump() for x in new],
                }, ensure_ascii=False))
            except Exception as exc:
                print(json.dumps({
                    "event": "monitor_error",
                    "watch_id": w["id"],
                    "error": str(exc),
                }, ensure_ascii=False))
        await asyncio.sleep(30)
