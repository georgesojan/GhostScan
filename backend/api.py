from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import sqlite3
import json
import os
from scanner_core import AsyncScanner
from intel_bridge import IntelligenceBridge

app = FastAPI(title="GhostScan API")

# Pathing for static files
BASE_DIR = os.path.dirname(__file__)
DIST_DIR = os.path.abspath(os.path.join(BASE_DIR, "../frontend/dist"))
DB_PATH = os.path.join(BASE_DIR, "ghostscan.db")

class ScanRequest(BaseModel):
    ips: List[str]
    ports: List[int]

async def run_scan_task(ips: List[str], ports: List[int]):
    scanner = AsyncScanner(concurrency=100)
    intel_bridge = IntelligenceBridge()
    
    results = await scanner.scan_range(ips, ports)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for ip, open_ports in results.items():
        if open_ports:
            # Fetch intel for active devices
            intel = await intel_bridge.fetch_ip_intel(ip)
            
            cursor.execute('''
                INSERT INTO devices (ip, ports, services, location, source)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                ip, 
                ",".join(map(str, open_ports)), 
                json.dumps(intel.get("services", [])),
                intel.get("location", "Unknown"),
                "scanner"
            ))
            
            # Cache full intel
            cursor.execute('''
                INSERT OR REPLACE INTO intel_cache (ip, data)
                VALUES (?, ?)
            ''', (ip, json.dumps(intel)))
            
    conn.commit()
    conn.close()

@app.post("/scan")
async def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_scan_task, request.ips, request.ports)
    return {"status": "Scan started in background", "target_count": len(request.ips)}

@app.get("/devices")
async def get_devices():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM devices ORDER BY last_seen DESC LIMIT 100")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/status")
async def get_status():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM devices")
    device_count = cursor.fetchone()[0]
    conn.close()
    return {"device_count": device_count, "engine": "GhostScan v1.0"}

# Serve Frontend
if os.path.exists(DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # API routes are already handled above
        # If the file exists in dist, serve it, otherwise serve index.html
        local_path = os.path.join(DIST_DIR, full_path)
        if os.path.isfile(local_path):
            return FileResponse(local_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
