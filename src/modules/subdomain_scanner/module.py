import asyncio
from typing import List, Dict, Any

class SubdomainScanner:
    def __init__(self, rate_limit: int = 5):
        self.rate_limit = rate_limit
        self.name = "subdomain_scanner"
        self.common_subdomains = ["www", "api", "dev", "test", "admin", "mail", "ftp"]
    
    async def scan(self, targets: List[str]) -> Dict[str, Any]:
        results = {"subdomains": [], "module": self.name}
        
        for target in targets:
            if "." in target:  # Это домен
                found_subs = await self.find_subdomains(target)
                results["subdomains"].extend(found_subs)
            await asyncio.sleep(1 / self.rate_limit)
        
        return results
    
    async def find_subdomains(self, domain: str) -> List[Dict]:
        found = []
        for sub in self.common_subdomains:
            subdomain = f"{sub}.{domain}"
            if await self.check_subdomain(subdomain):
                found.append({
                    "subdomain": subdomain,
                    "type": "subdomain",
                    "source": domain
                })
        return found
    
    async def check_subdomain(self, subdomain: str) -> bool:
        try:
            import socket
            socket.gethostbyname(subdomain)
            return True
        except:
            return False
