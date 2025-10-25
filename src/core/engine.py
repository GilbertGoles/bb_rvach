"""
Ядро RapidRecon - движок распространения сканирования
"""
import asyncio
import json
from queue import Queue
from typing import Dict, List, Any, Optional, Callable
import logging
import time
from dataclasses import dataclass
from enum import Enum
import random

class NodeType(Enum):
    """Типы обнаруживаемых узлов"""
    INITIAL_TARGET = "initial_target"
    SUBDOMAIN = "subdomain"
    IP_ADDRESS = "ip_address"
    SERVICE = "service"
    VULNERABILITY = "vulnerability"
    ACTIVE_HOST = "active_host"
    OPEN_PORTS = "open_ports"
    CUSTOM = "custom"

@dataclass
class ScanNode:
    """Унифицированная структура узла для сканирования"""
    node_id: str
    type: NodeType
    data: Any
    source: str
    depth: int
    timestamp: float
    module: str = "default"
    metadata: Dict[str, Any] = None
    ports: List[int] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.ports is None:
            self.ports = []

class PropagationEngine:
    """Движок авто-распространения сканирования"""
    
    def __init__(self, max_depth: int = 10, max_concurrent_tasks: int = 5, rate_limit: int = 10, update_callback: Optional[Callable] = None):
        self.discovered_nodes: List[ScanNode] = []
        self.pending_scans = Queue()
        self.completed_scans: Dict[str, Dict] = {}
        self.active_modules: Dict[str, Any] = {}
        self.scan_depth = 0
        self.max_depth = max_depth
        self.max_concurrent_tasks = max_concurrent_tasks
        self.rate_limit = rate_limit
        self.is_running = False
        self.update_callback = update_callback  # Callback для обновления GUI
        
        self.stats = {
            'total_scans': 0,
            'successful_scans': 0,
            'failed_scans': 0,
            'nodes_discovered': 0,
            'modules_executed': 0
        }
        
        # Настройка логирования
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('RapidRecon')
    
    def add_initial_target(self, target: str):
        """Добавить начальную цель для сканирования"""
        self.logger.info(f"Добавлена начальная цель: {target}")
        initial_node = ScanNode(
            node_id=f"initial_{target}_{int(time.time())}",
            type=NodeType.INITIAL_TARGET,
            data=target,
            source='user_input',
            depth=0,
            timestamp=time.time(),
            module='ping_scanner',
            metadata={'priority': 'high'}
        )
        self.discovered_nodes.append(initial_node)
        self.pending_scans.put(initial_node)
        self.stats['nodes_discovered'] += 1
        
        # Уведомляем GUI о новом узле
        self._notify_gui_update('node_added', initial_node)
    
    def add_custom_node(self, node_type: NodeType, data: Any, source: str, depth: int, 
                       module: str = "default", metadata: Dict = None, ports: List[int] = None):
        """Добавить кастомный узел для сканирования"""
        node = ScanNode(
            node_id=f"{node_type.value}_{hash(str(data))}_{int(time.time())}",
            type=node_type,
            data=data,
            source=source,
            depth=depth,
            timestamp=time.time(),
            module=module,
            metadata=metadata or {},
            ports=ports or []
        )
        self.discovered_nodes.append(node)
        self.pending_scans.put(node)
        self.stats['nodes_discovered'] += 1
        self.logger.info(f"Добавлен кастомный узел: {node_type.value} -> {data} (модуль: {module})")
        
        # Уведомляем GUI о новом узле
        self._notify_gui_update('node_added', node)
    
    def register_module(self, module_name: str, module_class):
        """Регистрация модуля в системе"""
        self.active_modules[module_name] = module_class(self.rate_limit)
        self.logger.info(f"Модуль зарегистрирован: {module_name}")
        
        # Уведомляем GUI о новом модуле
        self._notify_gui_update('module_registered', module_name)
    
    def register_callback(self, event_type: str, callback: Callable):
        """Регистрация callback-функций для событий"""
        if not hasattr(self, 'callbacks'):
            self.callbacks = {}
        self.callbacks[event_type] = callback
        self.logger.info(f"Callback зарегистрирован для события: {event_type}")
    
    def _notify_gui_update(self, event_type: str, data: Any = None):
        """Уведомление GUI об обновлении"""
        if self.update_callback:
            try:
                self.update_callback(event_type, data)
            except Exception as e:
                self.logger.warning(f"Ошибка при вызове GUI callback: {e}")
    
    async def process_queue(self):
        """Асинхронная обработка очереди задач"""
        self.is_running = True
        self.logger.info("Запуск обработки очереди задач...")
        
        # Уведомляем GUI о начале сканирования
        self._notify_gui_update('scan_started')
        
        semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        
        async def process_with_semaphore(task):
            async with semaphore:
                return await self.execute_task(task)
        
        while self.is_running and not self.pending_scans.empty():
            tasks = []
            # Собираем задачи для параллельного выполнения
            while len(tasks) < self.max_concurrent_tasks and not self.pending_scans.empty():
                task = self.pending_scans.get()
                if task.depth <= self.max_depth:
                    task_coroutine = process_with_semaphore(task)
                    tasks.append(task_coroutine)
            
            # Запускаем задачи конкурентно
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Уведомляем GUI о прогрессе
            self._notify_gui_update('progress_update', {
                'pending_tasks': self.pending_scans.qsize(),
                'completed_tasks': len(self.completed_scans),
                'discovered_nodes': len(self.discovered_nodes)
            })
        
        self.logger.info("Обработка очереди завершена")
        self.is_running = False
        
        # Уведомляем GUI о завершении сканирования
        self._notify_gui_update('scan_completed')
    
    async def execute_task(self, task: ScanNode):
        """Выполнение одной задачи сканирования"""
        self.logger.info(f"Выполняется задача: {task.module} -> {task.data} (глубина: {task.depth})")
        self.stats['total_scans'] += 1
        
        # Уведомляем GUI о начале задачи
        self._notify_gui_update('task_started', task)
        
        try:
            # Логика выбора и выполнения модуля
            module = self.select_module_for_task(task)
            
            if module:
                # Выполнение модуля с таймаутом
                await asyncio.wait_for(
                    self.run_module(module, task),
                    timeout=30.0
                )
                self.stats['modules_executed'] += 1
            else:
                # Поведение по умолчанию при отсутствии модуля
                await self.default_scan_behavior(task)
            
            self.stats['successful_scans'] += 1
            self.completed_scans[task.node_id] = {
                'status': 'completed',
                'result': 'success',
                'timestamp': time.time(),
                'module': task.module
            }
            
            # Уведомляем GUI о завершении задачи
            self._notify_gui_update('task_completed', task)
            
            # Вызов callback при успешном выполнении
            if hasattr(self, 'callbacks') and 'scan_completed' in self.callbacks:
                self.callbacks['scan_completed'](task)
                
        except asyncio.TimeoutError:
            self.logger.warning(f"Таймаут задачи: {task.data}")
            self.stats['failed_scans'] += 1
            self.completed_scans[task.node_id] = {
                'status': 'failed',
                'error': 'timeout',
                'timestamp': time.time(),
                'module': task.module
            }
            
            # Уведомляем GUI об ошибке
            self._notify_gui_update('task_failed', {
                'task': task,
                'error': 'timeout'
            })
            
        except Exception as e:
            self.logger.error(f"Ошибка выполнения задачи {task.data}: {e}")
            self.stats['failed_scans'] += 1
            self.completed_scans[task.node_id] = {
                'status': 'failed',
                'error': str(e),
                'timestamp': time.time(),
                'module': task.module
            }
            
            # Уведомляем GUI об ошибке
            self._notify_gui_update('task_failed', {
                'task': task,
                'error': str(e)
            })
    
    async def run_module(self, module, task: ScanNode):
        """Запуск модуля сканирования"""
        # Если модуль имеет метод scan, используем его
        if hasattr(module, 'scan'):
            results = await module.scan([task.data])
            await self.process_module_results(results, task)
        else:
            # Запасной вариант для кастомных модулей
            await self.default_scan_behavior(task)
    
    async def process_module_results(self, results: Dict[str, Any], source_task: ScanNode):
        """Обработка результатов модуля сканирования"""
        
        # Обработка результатов ping_scanner
        if results.get("module") == "ping_scanner" and results.get("active_hosts"):
            for host in results["active_hosts"]:
                new_node = ScanNode(
                    node_id=f"active_host_{host['ip']}_{int(time.time())}",
                    type=NodeType.ACTIVE_HOST,
                    data=host["ip"],
                    source=source_task.node_id,  # Используем node_id для точной связи
                    depth=source_task.depth + 1,
                    timestamp=time.time(),
                    module='port_scanner',
                    metadata={'host_status': 'active', 'response_time': host.get('response_time')}
                )
                await self.add_discovered_node(new_node)
        
        # Обработка результатов port_scanner
        elif results.get("module") == "port_scanner" and results.get("open_ports"):
            for host, ports in results["open_ports"].items():
                if ports:  # Если есть открытые порты
                    new_node = ScanNode(
                        node_id=f"open_ports_{host}_{int(time.time())}",
                        type=NodeType.OPEN_PORTS,
                        data=host,
                        source=source_task.node_id,
                        depth=source_task.depth + 1,
                        timestamp=time.time(),
                        module='service_detector',
                        metadata={'port_count': len(ports)},
                        ports=ports
                    )
                    await self.add_discovered_node(new_node)
        
        # Обработка результатов service_detector
        elif results.get("module") == "service_detector" and results.get("services"):
            for service_info in results["services"]:
                new_node = ScanNode(
                    node_id=f"service_{service_info['port']}_{service_info['type']}_{int(time.time())}",
                    type=NodeType.SERVICE,
                    data=f"{service_info['host']}:{service_info['port']}",
                    source=source_task.node_id,
                    depth=source_task.depth + 1,
                    timestamp=time.time(),
                    module='vulnerability_scanner',
                    metadata={
                        'service_type': service_info.get('type'),
                        'banner': service_info.get('banner'),
                        'port': service_info.get('port')
                    }
                )
                await self.add_discovered_node(new_node)
        
        # Обработка общих результатов для других модулей
        else:
            new_nodes = self.simulate_findings(source_task)
            await self.process_findings(new_nodes, source_task)
        
        # Уведомляем GUI о результатах модуля
        self._notify_gui_update('module_results', {
            'task': source_task,
            'results': results
        })
    
    async def add_discovered_node(self, node: ScanNode):
        """Добавление обнаруженного узла в систему"""
        if node.depth <= self.max_depth:
            self.discovered_nodes.append(node)
            self.pending_scans.put(node)
            self.stats['nodes_discovered'] += 1
            
            self.logger.info(f"Обнаружен новый узел: {node.type.value} -> {node.data}")
            
            # Уведомляем GUI о новом узле
            self._notify_gui_update('node_discovered', node)
            
            # Вызов callback при обнаружении нового узла
            if hasattr(self, 'callbacks') and 'node_discovered' in self.callbacks:
                self.callbacks['node_discovered'](node)
    
    async def default_scan_behavior(self, task: ScanNode):
        """Поведение по умолчанию при отсутствии модуля"""
        # Имитация работы модуля
        await asyncio.sleep(0.1)
        new_nodes = self.simulate_findings(task)
        await self.process_findings(new_nodes, task)
    
    async def process_findings(self, new_nodes: List[ScanNode], parent_task: ScanNode):
        """Обработка найденных узлов"""
        for node in new_nodes:
            await self.add_discovered_node(node)
    
    def select_module_for_task(self, task: ScanNode) -> Optional[Any]:
        """Выбор подходящего модуля для задачи"""
        # Используем модуль из задачи или выбираем по типу
        module_name = task.module if task.module != "default" else None
        
        if not module_name:
            # Базовая логика выбора модуля по типу узла
            module_map = {
                NodeType.INITIAL_TARGET: 'ping_scanner',
                NodeType.SUBDOMAIN: 'subdomain_scanner',
                NodeType.IP_ADDRESS: 'port_scanner',
                NodeType.ACTIVE_HOST: 'port_scanner',
                NodeType.OPEN_PORTS: 'service_detector',
                NodeType.SERVICE: 'vulnerability_scanner',
                NodeType.VULNERABILITY: 'report_generator'
            }
            module_name = module_map.get(task.type)
        
        return self.active_modules.get(module_name)
    
    def simulate_findings(self, task: ScanNode) -> List[ScanNode]:
        """Временная функция для симуляции находок (для демонстрации)"""
        if task.type == NodeType.INITIAL_TARGET:
            subdomains = ['api', 'admin', 'test', 'dev', 'staging']
            return [
                ScanNode(
                    node_id=f"subdomain_{sd}_{task.data}_{int(time.time())}",
                    type=NodeType.SUBDOMAIN,
                    data=f'{sd}.{task.data}',
                    source=task.node_id,  # Используем node_id для точной связи
                    depth=task.depth + 1,
                    timestamp=time.time(),
                    module='subdomain_scanner',
                    metadata={'confidence': 0.8}
                ) for sd in subdomains
            ]
        elif task.type == NodeType.SUBDOMAIN:
            # Симуляция обнаружения IP-адресов
            return [
                ScanNode(
                    node_id=f"ip_{task.data.replace('.', '_')}_{int(time.time())}",
                    type=NodeType.IP_ADDRESS,
                    data=f'192.168.1.{random.randint(1, 254)}',
                    source=task.node_id,
                    depth=task.depth + 1,
                    timestamp=time.time(),
                    module='ping_scanner',
                    metadata={'type': 'A_record'}
                )
            ]
        elif task.type == NodeType.ACTIVE_HOST:
            # Симуляция сканирования портов
            open_ports = random.sample([80, 443, 22, 21, 25, 53, 110, 143], random.randint(1, 4))
            return [
                ScanNode(
                    node_id=f"ports_{task.data}_{int(time.time())}",
                    type=NodeType.OPEN_PORTS,
                    data=task.data,
                    source=task.node_id,
                    depth=task.depth + 1,
                    timestamp=time.time(),
                    module='service_detector',
                    metadata={'port_count': len(open_ports)},
                    ports=open_ports
                )
            ]
        return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики сканирования"""
        return {
            **self.stats,
            'pending_tasks': self.pending_scans.qsize(),
            'completed_tasks': len(self.completed_scans),
            'discovered_nodes': len(self.discovered_nodes),
            'active_modules': len(self.active_modules),
            'is_running': self.is_running,
            'rate_limit': self.rate_limit,
            'max_depth': self.max_depth
        }
    
    def export_results(self, filename: str):
        """Экспорт результатов сканирования"""
        results = {
            'statistics': self.get_statistics(),
            'discovered_nodes': [
                {
                    'id': node.node_id,
                    'type': node.type.value,
                    'data': node.data,
                    'source': node.source,
                    'depth': node.depth,
                    'timestamp': node.timestamp,
                    'module': node.module,
                    'metadata': node.metadata,
                    'ports': node.ports
                } for node in self.discovered_nodes
            ],
            'completed_scans': self.completed_scans
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Результаты экспортированы в: {filename}")
        
        # Уведомляем GUI об экспорте
        self._notify_gui_update('results_exported', filename)
    
    def stop_engine(self):
        """Остановка движка"""
        self.is_running = False
        self.logger.info("Движок сканирования остановлен")
        
        # Уведомляем GUI об остановке
        self._notify_gui_update('engine_stopped')

# Пример использования с GUI callback
def gui_update_callback(event_type: str, data: Any = None):
    """Пример callback функции для обновления GUI"""
    print(f"GUI Update - Event: {event_type}, Data: {data}")

# Пример использования
async def main():
    """Демонстрация работы движка"""
    engine = PropagationEngine(
        max_depth=3, 
        max_concurrent_tasks=3, 
        rate_limit=10,
        update_callback=gui_update_callback
    )
    
    # Добавляем начальные цели
    engine.add_initial_target("example.com")
    engine.add_initial_target("test.org")
    
    # Запускаем обработку
    await engine.process_queue()
    
    # Выводим статистику
    stats = engine.get_statistics()
    print(f"Статистика: {stats}")
    
    # Экспортируем результаты
    engine.export_results("scan_results.json")

if __name__ == "__main__":
    asyncio.run(main())
