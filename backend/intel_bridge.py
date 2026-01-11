import json
import logging
import aiohttp
import os

logger = logging.getLogger(__name__)

class IntelligenceBridge:
    def __init__(self, shodan_key=None):
        self.shodan_key = shodan_key or os.getenv("SHODAN_API_KEY")

    async def fetch_ip_intel(self, ip):
        """Fetches intelligence about an IP from Shodan (Simulated if no key)."""
        if not self.shodan_key:
            return self._get_mock_intel(ip)
        
        url = f"https://api.shodan.io/shodan/host/{ip}?key={self.shodan_key}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"Shodan API error: {response.status}")
                        return self._get_mock_intel(ip)
        except Exception as e:
            logger.error(f"Failed to fetch Shodan intel: {e}")
            return self._get_mock_intel(ip)

    def _get_mock_intel(self, ip):
        """Mock intelligence for demonstration without an API key."""
        return {
            "ip": ip,
            "os": "Linux 4.x/5.x",
            "location": "Simulated City, World",
            "services": ["HTTP", "SSH"],
            "vulnerabilities": ["None Detected (Simulated)"]
        }

if __name__ == "__main__":
    import asyncio
    bridge = IntelligenceBridge()
    async def test():
        intel = await bridge.fetch_ip_intel("8.8.8.8")
        print(f"Intel for 8.8.8.8: {json.dumps(intel, indent=2)}")
    asyncio.run(test())
