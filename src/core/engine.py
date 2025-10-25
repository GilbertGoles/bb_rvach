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

class NodeType(Enum):
    """Типы обнаруживаемых узлов"""
    INITIAL_TARGET = "initial_target"
    SUBDOMAIN = "subdomain"
    IP_ADDRESS = "ip_address"
    SERVICE = "service"
    VULNERABILITY = "vulnerability"
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
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class PropagationEngine:
    """Движок авто-распространения сканирования"""
    
    def __init__(self, max_depth: int = 10, max_concurrent_tasks: int = 5):
        self.discovered_nodes: List[ScanNode] = []
        self.pending_scans = Queue()
        self.completed_scans: Dict[str, Dict] = {}
        self.active_modules: Dict[str, Any] = {}
        self.scan_depth = 0
        self.max_depth = max_depth
        self.max_concurrent_tasks = max_concurrent_tasks
        self.is_running = False
        self.stats = {
            'total_scans': 0,
            'successful_scans': 0,
            'failed_scans': 0,
            'nodes_discovered': 0
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
            metadata={'priority': 'high'}
        )
        self.discovered_nodes.append(initial_node)
        self.pending_scans.put(initial_node)
        self.stats['nodes_discovered'] += 1
    
    def add_custom_node(self, node_type: NodeType, data: Any, source: str, depth: int, metadata: Dict = None):
        """Добавить кастомный узел для сканирования"""
        node = ScanNode(
            node_id=f"{node_type.value}_{hash(str(data))}_{int(time.time())}",
            type=node_type,
            data=data,
            source=source,
            depth=depth,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        self.discovered_nodes.append(node)
        self.pending_scans.put(node)
        self.stats['nodes_discovered'] += 1
        self.logger.info(f"Добавлен кастомный узел: {node_type.value} -> {data}")
    
    def register_module(self, module_name: str, module_class):
        """Регистрация модуля в системе"""
        self.active_modules[module_name] = module_class
        self.logger.info(f"Модуль зарегистрирован: {module_name}")
    
    def register_callback(self, event_type: str, callback: Callable):
        """Регистрация callback-функций для событий"""
        if not hasattr(self, 'callbacks'):
            self.callbacks = {}
        self.callbacks[event_type] = callback
        self.logger.info(f"Callback зарегистрирован для события: {event_type}")
    
    async def process_queue(self):
        """Асинхронная обработка очереди задач"""
        self.is_running = True
        self.logger.info("Запуск обработки очереди задач...")
        
        semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        
        async def process_with_semaphore(task):
            async with semaphore:
                return await self.execute_task(task)
        
        tasks = []
        while self.is_running and not self.pending_scans.empty():
            task = self.pending_scans.get()
            if task.depth <= self.max_depth:
                task_coroutine = process_with_semaphore(task)
                tasks.append(task_coroutine)
        
        # Запускаем все задачи конкурентно
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.logger.info("Обработка очереди завершена")
        self.is_running = False
    
    async def execute_task(self, task: ScanNode):
        """Выполнение одной задачи сканирования"""
        self.logger.info(f"Выполняется задача: {task.type.value} -> {task.data} (глубина: {task.depth})")
        self.stats['total_scans'] += 1
        
        try:
            # Здесь будет логика выбора и выполнения модуля
            module = self.select_module_for_task(task)
            
            if module:
                # Выполнение модуля с таймаутом
                await asyncio.wait_for(
                    self.run_module(module, task),
                    timeout=30.0
                )
            else:
                # Заглушка для демонстрации
                await self.default_scan_behavior(task)
            
            self.stats['successful_scans'] += 1
            self.completed_scans[task.node_id] = {
                'status': 'completed',
                'result': 'success',
                'timestamp': time.time()
            }
            
            # Вызов callback при успешном выполнении
            if hasattr(self, 'callbacks') and 'scan_completed' in self.callbacks:
                self.callbacks['scan_completed'](task)
                
        except asyncio.TimeoutError:
            self.logger.warning(f"Таймаут задачи: {task.data}")
            self.stats['failed_scans'] += 1
            self.completed_scans[task.node_id] = {
                'status': 'failed',
                'error': 'timeout',
                'timestamp': time.time()
            }
        except Exception as e:
            self.logger.error(f"Ошибка выполнения задачи {task.data}: {e}")
            self.stats['failed_scans'] += 1
            self.completed_scans[task.node_id] = {
                'status': 'failed',
                'error': str(e),
                'timestamp': time.time()
            }
    
    async def run_module(self, module, task: ScanNode):
        """Запуск модуля сканирования"""
        # Заглушка для реализации модулей
        await asyncio.sleep(0.1)
        new_nodes = self.simulate_findings(task)
        await self.process_findings(new_nodes, task)
    
    async def default_scan_behavior(self, task: ScanNode):
        """Поведение по умолчанию при отсутствии модуля"""
        await asyncio.sleep(0.1)
        new_nodes = self.simulate_findings(task)
        await self.process_findings(new_nodes, task)
    
    async def process_findings(self, new_nodes: List[ScanNode], parent_task: ScanNode):
        """Обработка найденных узлов"""
        for node in new_nodes:
            if node.depth <= self.max_depth:
                self.discovered_nodes.append(node)
                self.pending_scans.put(node)
                self.stats['nodes_discovered'] += 1
                
                self.logger.info(f"Обнаружен новый узел: {node.type.value} -> {node.data}")
                
                # Вызов callback при обнаружении нового узла
                if hasattr(self, 'callbacks') and 'node_discovered' in self.callbacks:
                    self.callbacks['node_discovered'](node)
    
    def select_module_for_task(self, task: ScanNode) -> Optional[Any]:
        """Выбор подходящего модуля для задачи"""
        # Базовая логика выбора модуля
        module_map = {
            NodeType.INITIAL_TARGET: 'domain_scanner',
            NodeType.SUBDOMAIN: 'subdomain_scanner',
            NodeType.IP_ADDRESS: 'port_scanner',
            NodeType.SERVICE: 'service_analyzer'
        }
        
        module_name = module_map.get(task.type)
        return self.active_modules.get(module_name)
    
    def simulate_findings(self, task: ScanNode) -> List[ScanNode]:
        """Временная функция для симуляции находок"""
        if task.type == NodeType.INITIAL_TARGET:
            subdomains = ['api', 'admin', 'test', 'dev', 'staging']
            return [
                ScanNode(
                    node_id=f"subdomain_{sd}_{task.data}_{int(time.time())}",
                    type=NodeType.SUBDOMAIN,
                    data=f'{sd}.{task.data}',
                    source=task.data,
                    depth=task.depth + 1,
                    timestamp=time.time(),
                    metadata={'confidence': 0.8}
                ) for sd in subdomains
            ]
        elif task.type == NodeType.SUBDOMAIN:
            # Симуляция обнаружения IP-адресов
            return [
                ScanNode(
                    node_id=f"ip_{task.data.replace('.', '_')}_{int(time.time())}",
                    type=NodeType.IP_ADDRESS,
                    data=f'192.168.1.{hash(task.data) % 255}',
                    source=task.data,
                    depth=task.depth + 1,
                    timestamp=time.time(),
                    metadata={'type': 'A_record'}
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
            'is_running': self.is_running
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
                    'metadata': node.metadata
                } for node in self.discovered_nodes
            ],
            'completed_scans': self.completed_scans
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Результаты экспортированы в: {filename}")
    
    def stop_engine(self):
        """Остановка движка"""
        self.is_running = False
        self.logger.info("Движок сканирования остановлен")

# Пример использования
async def main():
    """Демонстрация работы движка"""
    engine = PropagationEngine(max_depth=3, max_concurrent_tasks=3)
    
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
