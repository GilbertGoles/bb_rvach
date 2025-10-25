import asyncio
from typing import Dict, Any, List

class ServiceDetector:
    def __init__(self, rate_limit: int = 5):
        self.rate_limit = rate_limit
        self.name = "service_detector"
        self.service_signatures = {
            21: "ftp",
            22: "ssh", 
            80: "http",
            443: "https",
            53: "dns",
            25: "smtp"
        }
    
    async def scan(self, open_ports_data: Dict[str, Any]) -> Dict[str, Any]:
        results = {"services": {}, "module": self.name}
        
        for host, ports in open_ports_data.items():
            results["services"][host] = []
            for port_info in ports:
                service = await self.detect_service(host, port_info["port"])
                results["services"][host].append({
                    **port_info,
                    "service": service,
                    "banner": await self.get_banner(host, port_info["port"])
                })
            await asyncio.sleep(1 / self.rate_limit)
        
        return results
    
    async def detect_service(self, host: str, port: int) -> str:
        return self.service_signatures.get(port, "unknown")
    
    async def get_banner(self, host: str, port: int, timeout: float = 2.0) -> str:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=timeout
            )
            
            if port == 80:
                writer.write(b"HEAD / HTTP/1.0\r\n\r\n")
                await writer.drain()
            
            banner = await asyncio.wait_for(reader.read(1024), timeout=1.0)
            writer.close()
            await writer.wait_closed()
            
            return banner.decode('utf-8', errors='ignore')[:500]
        except:
            return ""
