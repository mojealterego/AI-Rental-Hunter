import asyncio
import os
import threading
import uvicorn

from .monitor import monitor_loop

if __name__ == "__main__":
    threading.Thread(
        target=lambda: asyncio.run(monitor_loop()),
        daemon=True,
        name="rental-monitor",
    ).start()

    uvicorn.run(
        "rental_hunter.server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
    )
