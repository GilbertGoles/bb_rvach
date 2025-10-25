import asyncio
import socket
from typing import List, Dict, Any, Optional
import logging

class PortScanner:
    """
    Модуль сканирования портов для RapidRecon
    Поддерживает асинхронное сканирование с ограничением скорости
    """
    
    def __init__(self, rate_limit: int = 10, config: Dict = None):
        self.rate_limit = rate_limit
        self.config = config or {}
        self.common_ports = self.get_ports_from_config()
        self.name = "port_scanner"
        self.logger = logging.getLogger('PortScanner')
        
        # Настройки из конфигурации
        self.timeout = self.config.get("timeout", 1.0)
        self.max_ports_per_scan = self.config.get("max_ports_per_scan", 1000)
        self.scan_method = self.config.get("scan_method", "connect")  # connect или syn (заглушка)
        
        self.logger.info(f"Инициализирован PortScanner с {len(self.common_ports)} портами, timeout={self.timeout}s")
    
    def get_ports_from_config(self) -> List[int]:
        """Получить порты из конфигурации"""
        ports_config = self.config.get("ports", [])
        
        if ports_config == "full":
            # Полное сканирование первых 1000 портов
            return list(range(1, 1001))
        elif ports_config == "common":
            # Стандартные распространенные порты
            return [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995, 8080, 8443, 3306, 5432, 27017]
        elif ports_config == "web":
            # Веб-порты
            return [80, 443, 8080, 8443, 3000, 5000, 8000, 9000]
        elif ports_config == "services":
            # Порты сервисов
            return [21, 22, 23, 25, 53, 110, 143, 993, 995, 3306, 5432, 27017, 6379]
        elif isinstance(ports_config, list):
            # Пользовательский список портов
            return ports_config
        else:
            # По умолчанию - основные порты
            return [21, 22, 23, 25, 53, 80, 110, 443, 993, 995, 8080, 8443]
    
    async def scan(self, targets: List[str]) -> Dict[str, Any]:
        """
        Сканирование портов на целевых хостах
        
        Args:
            targets: Список IP-адресов или хостов для сканирования
            
        Returns:
            Dict с результатами сканирования
        """
        self.logger.info(f"Начато сканирование портов для {len(targets)} целей")
        results = {
            "open_ports": {},
            "module": self.name,
            "scan_config": {
                "ports_count": len(self.common_ports),
                "timeout": self.timeout,
                "rate_limit": self.rate_limit
            }
        }
        
        try:
            for target in targets:
                self.logger.info(f"Сканирование портов для {target}")
                open_ports = await self.scan_ports(target)
                results["open_ports"][target] = open_ports
                
                # Логируем результаты
                if open_ports:
                    port_list = [port["port"] for port in open_ports]
                    self.logger.info(f"Найдено открытых портов на {target}: {port_list}")
                else:
                    self.logger.info(f"Открытых портов не найдено на {target}")
                
                # Ограничение скорости сканирования
                if len(targets) > 1:
                    await asyncio.sleep(1 / self.rate_limit)
        
        except Exception as e:
            self.logger.error(f"Ошибка при сканировании портов: {e}")
            results["error"] = str(e)
        
        self.logger.info("Сканирование портов завершено")
        return results
    
    async def scan_ports(self, host: str) -> List[Dict]:
        """
        Сканирование портов на конкретном хосте
        
        Args:
            host: IP-адрес или хост для сканирования
            
        Returns:
            List с информацией об открытых портах
        """
        open_ports = []
        
        # Проверяем доступность хоста перед сканированием
        if not await self.is_host_alive(host):
            self.logger.warning(f"Хост {host} недоступен, пропускаем сканирование портов")
            return open_ports
        
        # Создаем задачи для асинхронного сканирования портов
        tasks = []
        for port in self.common_ports:
            task = self.check_port(host, port)
            tasks.append(task)
        
        # Запускаем все задачи параллельно с ограничением
        semaphore = asyncio.Semaphore(self.rate_limit * 10)  # Увеличиваем лимит для параллельных проверок
        
        async def bounded_check(host, port):
            async with semaphore:
                return await self.check_port(host, port)
        
        # Выполняем проверки портов
        port_results = []
        for i in range(0, len(tasks), self.rate_limit * 5):
            batch = tasks[i:i + self.rate_limit * 5]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            port_results.extend(batch_results)
            
            # Задержка между батчами для соблюдения rate limit
            if i + self.rate_limit * 5 < len(tasks):
                await asyncio.sleep(0.1)
        
        # Обрабатываем результаты
        for port, is_open in zip(self.common_ports, port_results):
            if is_open and not isinstance(is_open, Exception):
                service_info = await self.detect_service(host, port)
                open_ports.append({
                    "port": port,
                    "protocol": "tcp",
                    "status": "open",
                    "service": service_info.get("service", "unknown"),
                    "banner": service_info.get("banner", ""),
                    "confidence": service_info.get("confidence", 0.0)
                })
        
        return open_ports
    
    async def check_port(self, host: str, port: int) -> bool:
        """
        Проверка открыт ли порт на хосте
        
        Args:
            host: IP-адрес или хост
            port: Номер порта для проверки
            
        Returns:
            True если порт открыт, False в противном случае
        """
        try:
            if self.scan_method == "connect":
                return await self.connect_scan(host, port)
            else:
                # По умолчанию используем connect scan
                return await self.connect_scan(host, port)
                
        except Exception as e:
            self.logger.debug(f"Ошибка при проверке порта {host}:{port}: {e}")
            return False
    
    async def connect_scan(self, host: str, port: int) -> bool:
        """TCP Connect сканирование"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
            return False
        except Exception as e:
            self.logger.debug(f"Неожиданная ошибка при connect сканировании {host}:{port}: {e}")
            return False
    
    async def is_host_alive(self, host: str) -> bool:
        """
        Проверка доступности хоста
        
        Args:
            host: IP-адрес или хост для проверки
            
        Returns:
            True если хост доступен
        """
        try:
            # Пытаемся подключиться к порту 80 или 443 для проверки доступности
            for port in [80, 443, 22]:
                if await self.connect_scan(host, port):
                    return True
            return False
        except:
            return False
    
    async def detect_service(self, host: str, port: int) -> Dict[str, Any]:
        """
        Определение сервиса на порту
        
        Args:
            host: IP-адрес или хост
            port: Номер порта
            
        Returns:
            Dict с информацией о сервисе
        """
        common_services = {
            21: {"service": "ftp", "confidence": 0.9},
            22: {"service": "ssh", "confidence": 0.95},
            23: {"service": "telnet", "confidence": 0.9},
            25: {"service": "smtp", "confidence": 0.9},
            53: {"service": "dns", "confidence": 0.8},
            80: {"service": "http", "confidence": 0.95},
            110: {"service": "pop3", "confidence": 0.9},
            143: {"service": "imap", "confidence": 0.9},
            443: {"service": "https", "confidence": 0.95},
            993: {"service": "imaps", "confidence": 0.9},
            995: {"service": "pop3s", "confidence": 0.9},
            3306: {"service": "mysql", "confidence": 0.8},
            5432: {"service": "postgresql", "confidence": 0.8},
            8080: {"service": "http-proxy", "confidence": 0.7},
            8443: {"service": "https-alt", "confidence": 0.7},
            27017: {"service": "mongodb", "confidence": 0.8}
        }
        
        # Возвращаем известный сервис или пытаемся получить баннер
        if port in common_services:
            return common_services[port]
        
        # Пытаемся получить баннер для неизвестных портов
        banner = await self.get_banner(host, port)
        if banner:
            return {
                "service": "unknown",
                "banner": banner,
                "confidence": 0.5
            }
        
        return {"service": "unknown", "confidence": 0.1}
    
    async def get_banner(self, host: str, port: int) -> str:
        """
        Попытка получения баннера с сервиса
        
        Args:
            host: IP-адрес или хост
            port: Номер порта
            
        Returns:
            Баннер сервиса или пустая строка
        """
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=2.0
            )
            
            # Ждем данные от сервиса
            try:
                banner = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                banner_text = banner.decode('utf-8', errors='ignore').strip()
                writer.close()
                await writer.wait_closed()
                return banner_text
            except:
                writer.close()
                await writer.wait_closed()
                return ""
                
        except:
            return ""
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        Обновление конфигурации сканера
        
        Args:
            new_config: Новая конфигурация
        """
        self.config.update(new_config)
        self.common_ports = self.get_ports_from_config()
        self.timeout = self.config.get("timeout", self.timeout)
        self.rate_limit = self.config.get("rate_limit", self.rate_limit)
        
        self.logger.info(f"Конфигурация PortScanner обновлена: {len(self.common_ports)} портов")

# Пример использования
async def main():
    """Демонстрация работы PortScanner"""
    # Конфигурация сканера
    config = {
        "ports": "common",
        "timeout": 1.0,
        "rate_limit": 10
    }
    
    scanner = PortScanner(rate_limit=5, config=config)
    
    # Тестовые цели
    targets = ["127.0.0.1", "localhost"]
    
    # Запуск сканирования
    results = await scanner.scan(targets)
    
    print("Результаты сканирования портов:")
    for target, ports in results["open_ports"].items():
        print(f"\n{target}:")
        for port_info in ports:
            print(f"  Порт {port_info['port']} ({port_info['service']}) - открыт")

if __name__ == "__main__":
    asyncio.run(main())
