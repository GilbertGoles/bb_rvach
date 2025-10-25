import asyncio
import subprocess
from typing import List, Dict, Any

class PingScanner:
    def __init__(self, rate_limit: int = 10):
        self.rate_limit = rate_limit
        self.name = "ping_scanner"
    
    async def scan(self, targets: List[str]) -> Dict[str, Any]:
        results = {"active_hosts": [], "module": self.name}
        
        for target in targets:
            if await self.ping_host(target):
                results["active_hosts"].append({
                    "ip": target,
                    "hostname": target,
                    "status": "active"
                })
            await asyncio.sleep(1 / self.rate_limit)
        
        return results
    
    async def ping_host(self, host: str) -> bool:
        try:
            process = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', '1', host,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            await process.wait()
            return process.returncode == 0
        except:
            return False
