import asyncio
import socket
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class AsyncScanner:
    def __init__(self, timeout=0.5, concurrency=500):
        self.timeout = timeout
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)

    async def scan_port(self, ip, port):
        """Probes a single port on a given IP."""
        async with self.semaphore:
            try:
                # Use wait_for to enforce timeout on the connection attempt
                conn = asyncio.open_connection(ip, port)
                reader, writer = await asyncio.wait_for(conn, timeout=self.timeout)
                writer.close()
                await writer.wait_closed()
                return port, True
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                return port, False

    async def scan_range(self, ip_range, ports):
        """Scans a list of IPs and ports concurrently."""
        tasks = []
        for ip in ip_range:
            for port in ports:
                tasks.append(self.scan_port(ip, port))
        
        results = await asyncio.gather(*tasks)
        
        # Organize results by IP
        findings = {}
        for i, (port, is_open) in enumerate(results):
            ip = ip_range[i // len(ports)]
            if ip not in findings:
                findings[ip] = []
            if is_open:
                findings[ip].append(port)
                logger.info(f"FIND: {ip}:{port} is OPEN")
        
        return findings

async def main_test():
    scanner = AsyncScanner(concurrency=100)
    test_ips = ["127.0.0.1", "192.168.1.1"] # Local test
    test_ports = [22, 80, 443, 3000, 8000, 8001]
    
    start_time = datetime.now()
    print(f"Starting Scan at {start_time}")
    results = await scanner.scan_range(test_ips, test_ports)
    end_time = datetime.now()
    
    print(f"\nScan Results (Duration: {end_time - start_time}):")
    for ip, open_ports in results.items():
        print(f"  {ip}: {open_ports if open_ports else 'No open ports found'}")

if __name__ == "__main__":
    asyncio.run(main_test())
