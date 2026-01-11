import tkinter as tk
import customtkinter as ctk
import asyncio
import threading
import socket
import logging
import json
import sqlite3
import os
import aiohttp
import random
from aiohttp_socks import ProxyConnector, open_connection as socks_open_connection
from datetime import datetime
from PIL import Image

# --- Logger ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ghostscan_native.db")
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")

# --- Database Logic ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            ports TEXT,
            location TEXT,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# --- Scanner Logic ---
class AsyncScanner:
    def __init__(self, timeout=1.0, concurrency=100, proxy=None):
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(concurrency)
        self.proxy = proxy # e.g. "socks5://127.0.0.1:9050"

    async def scan_port(self, ip, port):
        async with self.semaphore:
            try:
                if self.proxy:
                    # Port scanning over Tor (SOCKS5)
                    proxy_host, proxy_port = self.proxy.replace("socks5://", "").split(":")
                    conn = socks_open_connection(proxy_host, int(proxy_port), ip, port)
                else:
                    conn = asyncio.open_connection(ip, port)
                
                reader, writer = await asyncio.wait_for(conn, timeout=self.timeout)
                writer.close()
                await writer.wait_closed()
                return port, True
            except:
                return port, False

    async def scan_range(self, ip_range, ports, callback):
        tasks = []
        for ip in ip_range:
            for port in ports:
                tasks.append(self.scan_port(ip, port))
        
        results = await asyncio.gather(*tasks)
        
        findings = {}
        for i, (port, is_open) in enumerate(results):
            ip = ip_range[i // len(ports)]
            if is_open:
                if ip not in findings: findings[ip] = []
                findings[ip].append(port)
                callback(ip, port)
        return findings

# --- Global Explorer (GIS Integration) ---
class GlobalExplorer:
    def __init__(self, log_callback):
        self.log_callback = log_callback
        self.topics = [
            "Industrial Control Systems", "Unprotected Webcams", 
            "Database Servers", "IoT Sensors", "Cloud Infrastructure",
            "Public Web Servers", "SSH Gateways", "Development Boards"
        ]
    
    def brainstorm(self):
        topic = random.choice(self.topics)
        self.log_callback(f"[BRAINSTORMING] targeting: {topic}...")
        return topic

    async def harvest(self, topic):
        # Simulated harvesting for the demo (normally hits Shodan/Censys/Github)
        # We generate a few distinct public IPs for discovery
        self.log_callback(f"[HARVESTING] gathering global targets for {topic}...")
        await asyncio.sleep(2)
        
        mock_ips = [
            f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
            for _ in range(5)
        ]
        return mock_ips

# --- GUI Application ---
class GhostScanApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GhostScan Native Recon")
        self.geometry("1000x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        # Grid config
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Logo
        if os.path.exists(LOGO_PATH):
            my_image = ctk.CTkImage(light_image=Image.open(LOGO_PATH),
                                    dark_image=Image.open(LOGO_PATH),
                                    size=(180, 180))
            self.logo_label = ctk.CTkLabel(self.sidebar, image=my_image, text="")
            self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.title_label = ctk.CTkLabel(self.sidebar, text="GHOSTSCAN", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.grid(row=1, column=0, padx=20, pady=10)

        # Inputs
        self.ip_label = ctk.CTkLabel(self.sidebar, text="IP Range / Target:", anchor="w")
        self.ip_label.grid(row=2, column=0, padx=20, pady=(10, 0))
        self.ip_entry = ctk.CTkEntry(self.sidebar, placeholder_text="192.168.1.1/24")
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.grid(row=3, column=0, padx=20, pady=(5, 10))

        self.scan_btn = ctk.CTkButton(self.sidebar, text="Initialize Scan", command=self.start_scan_thread)
        self.scan_btn.grid(row=4, column=0, padx=20, pady=10)

        self.global_btn = ctk.CTkButton(self.sidebar, text="START GLOBAL RECON", fg_color="#ff00ff", hover_color="#cc00cc", command=self.toggle_global_recon)
        self.global_btn.grid(row=5, column=0, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self.sidebar, text="SYSTEM: STANDBY", text_color="#00ff9d")
        self.status_label.grid(row=6, column=0, padx=20, pady=(10, 0))

        # Stealth Mode Toggle
        self.stealth_var = tk.BooleanVar(value=False)
        self.stealth_switch = ctk.CTkSwitch(self.sidebar, text="STEALTH MODE (TOR)", variable=self.stealth_var, onvalue=True, offvalue=False, command=self.toggle_stealth)
        self.stealth_switch.grid(row=7, column=0, padx=20, pady=20)

        self.verify_btn = ctk.CTkButton(self.sidebar, text="Verify Identity", fg_color="transparent", border_width=1, command=self.verify_identity)
        self.verify_btn.grid(row=8, column=0, padx=20, pady=10)

        # Target Intel Section
        self.intel_label = ctk.CTkLabel(self.sidebar, text="TARGET INTEL (DNS/GEO):", anchor="w")
        self.intel_label.grid(row=9, column=0, padx=20, pady=(20, 0))
        self.intel_entry = ctk.CTkEntry(self.sidebar, placeholder_text="example.com")
        self.intel_entry.grid(row=10, column=0, padx=20, pady=(5, 10))
        self.intel_btn = ctk.CTkButton(self.sidebar, text="Resolve & Mapping", command=self.resolve_target_intel)
        self.intel_btn.grid(row=11, column=0, padx=20, pady=10)

        # Main Content
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.header_label = ctk.CTkLabel(self.main_frame, text="Active Discovery Log", font=ctk.CTkFont(size=18, weight="bold"))
        self.header_label.grid(row=0, column=0, sticky="w", pady=(0, 20))

        self.log_box = ctk.CTkTextbox(self.main_frame, font=ctk.CTkFont(family="Courier", size=12))
        self.log_box.grid(row=1, column=0, sticky="nsew")
        
        self.log_box.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] Console Initialized. Ready for Recon.\n")

        # Async loop for background tasks
        self.loop = asyncio.new_event_loop()
        self.scanner = AsyncScanner()
        self.explorer = GlobalExplorer(self.add_log)
        self.is_global_active = False

    def add_log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{ts}] {msg}\n")
        self.log_box.see("end")

    def on_discovery(self, ip, port):
        msg = f"FIND: {ip}:{port} is OPEN [UNMASKED]"
        self.after(10, lambda: self.add_log(msg))
        
        # Save to DB
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO devices (ip, ports, location) VALUES (?, ?, ?)", (ip, str(port), "Local/Simulated"))
        conn.commit()
        conn.close()

    def start_scan_thread(self):
        targets = self.ip_entry.get()
        self.add_log(f"Starting Scan on {targets}...")
        self.status_label.configure(text="SYSTEM: SCANNING", text_color="#ffcc00")
        
        # Simple parser for list
        ips = [t.strip() for t in targets.split(",")]
        ports = [22, 80, 443, 3389, 8000, 8080, 8443]
        
        # Configure scanner with current proxy settings
        proxy_url = "socks5://127.0.0.1:9050" if self.stealth_var.get() else None
        self.scanner.proxy = proxy_url
        self.scanner.timeout = 2.0 if proxy_url else 1.0 # Tor is slower
        
        def run_async():
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.scanner.scan_range(ips, ports, self.on_discovery))
            self.after(10, lambda: self.status_label.configure(text="SYSTEM: STANDBY", text_color="#00ff9d"))
            self.after(10, lambda: self.add_log("Scan Complete."))

        threading.Thread(target=run_async, daemon=True).start()

    def toggle_stealth(self):
        active = self.stealth_var.get()
        if active:
            self.add_log("GHOST PROXY: Stealth Mode ACTIVATED. Routing via Tor.")
            self.status_label.configure(text="SYSTEM: ANONYMOUS", text_color="#ff00ff")
        else:
            self.add_log("GHOST PROXY: Stealth Mode DEACTIVATED. Using Direct Link.")
            self.status_label.configure(text="SYSTEM: STANDBY", text_color="#00ff9d")

    def verify_identity(self):
        self.add_log("Verifying outgoing IP signature...")
        
        async def check_ip():
            proxy = "socks5://127.0.0.1:9050" if self.stealth_var.get() else None
            connector = ProxyConnector.from_url(proxy) if proxy else None
            
            try:
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get("https://api.ipify.org?format=json", timeout=10) as resp:
                        data = await resp.json()
                        ip = data.get("ip")
                        self.after(10, lambda: self.add_log(f"CURRENT IDENTITY: {ip}"))
            except Exception as e:
                self.after(10, lambda: self.add_log(f"IDENTITY ERROR: {str(e)}"))

        threading.Thread(target=lambda: asyncio.run(check_ip()), daemon=True).start()

    def toggle_global_recon(self):
        if not self.is_global_active:
            self.is_global_active = True
            self.global_btn.configure(text="STOP GLOBAL RECON", fg_color="#440044")
            self.stealth_var.set(True) # Force stealth
            self.toggle_stealth()
            self.add_log("CENTRAL INTELLIGENCE: Initializing Global Recon Loop...")
            threading.Thread(target=self.run_global_loop, daemon=True).start()
        else:
            self.is_global_active = False
            self.global_btn.configure(text="START GLOBAL RECON", fg_color="#ff00ff")
            self.add_log("CENTRAL INTELLIGENCE: Halting Global Recon.")

    def run_global_loop(self):
        asyncio.set_event_loop(self.loop)
        while self.is_global_active:
            topic = self.explorer.brainstorm()
            targets = self.loop.run_until_complete(self.explorer.harvest(topic))
            
            self.after(10, lambda: self.add_log(f"TARGETS ACQUIRED: Scanning {len(targets)} global nodes..."))
            
            # Use Tor for global scans
            self.scanner.proxy = "socks5://127.0.0.1:9050"
            self.scanner.timeout = 2.0
            
            ports = [80, 443, 22, 8080]
            self.loop.run_until_complete(self.scanner.scan_range(targets, ports, self.on_discovery))
            
            self.loop.run_until_complete(asyncio.sleep(10)) # Interval between waves

    def resolve_target_intel(self):
        target = self.intel_entry.get()
        if not target: return
        
        self.add_log(f"[*] INITIALIZING INTEL GATHERING: {target}")
        
        def run_resolve():
            # 1. Resolve IP
            try:
                ip = socket.gethostbyname(target)
                self.after(10, lambda: self.add_log(f"[+] RESOLVED IP: {ip}"))
            except:
                self.after(10, lambda: self.add_log(f"[-] RESOLUTION FAILED: {target}"))
                return

            # 2. Fetch GeoIP (Direct or Tor depending on stealth)
            async def fetch_geo():
                proxy = "socks5://127.0.0.1:9050" if self.stealth_var.get() else None
                connector = ProxyConnector.from_url(proxy) if proxy else None
                try:
                    async with aiohttp.ClientSession(connector=connector) as session:
                        async with session.get(f"http://ip-api.com/json/{ip}", timeout=10) as resp:
                            data = await resp.json()
                            if data.get("status") == "success":
                                info = f"MAP: {data.get('city')}, {data.get('country')} | ISP: {data.get('isp')}"
                                self.after(10, lambda: self.add_log(f"[+] {info}"))
                                # Auto-inject into scan entry
                                self.after(10, lambda: self.ip_entry.delete(0, 'end'))
                                self.after(10, lambda: self.ip_entry.insert(0, ip))
                            else:
                                self.after(10, lambda: self.add_log("[-] GEO-DATA UNAVAILABLE"))
                except Exception as e:
                    self.after(10, lambda: self.add_log(f"[-] GEO-ERROR: {str(e)}"))

            asyncio.run(fetch_geo())

        threading.Thread(target=run_resolve, daemon=True).start()

if __name__ == "__main__":
    init_db()
    app = GhostScanApp()
    app.mainloop()
