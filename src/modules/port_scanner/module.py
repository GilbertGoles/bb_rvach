import asyncio
import socket
from typing import List, Dict, Any

class PortScanner:
    def __init__(self, rate_limit: int = 10):
        self.rate_limit = rate_limit
        self.common_ports = [21, 22, 23, 25, 53, 80, 110, 443, 993, 995, 8080, 8443]
        self.name = "port_scanner"
    
    async def scan(self, targets: List[str]) -> Dict[str, Any]:
        results = {"open_ports": {}, "module": self.name}
        
        for target in targets:
            results["open_ports"][target] = await self.scan_ports(target)
            await asyncio.sleep(1 / self.rate_limit)
        
        return results
    
    async def scan_ports(self, host: str) -> List[Dict]:
        open_ports = []
        
        for port in self.common_ports:
            if await self.check_port(host, port):
                open_ports.append({
                    "port": port,
                    "protocol": "tcp",
                    "status": "open"
                })
        
        return open_ports
    
    async def check_port(self, host: str, port: int, timeout: float = 1.0) -> bool:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
