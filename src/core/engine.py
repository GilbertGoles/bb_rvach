"""
Ядро RapidRecon - движок распространения сканирования
"""
import asyncio
import json
from queue import Queue
from typing import Dict, List, Any
import logging

class PropagationEngine:
    """Движок авто-распространения сканирования"""
    
    def __init__(self):
        self.discovered_nodes = []  # Все найденные узлы
        self.pending_scans = Queue()  # Очередь задач
        self.completed_scans = {}  # Результаты сканирований
        self.active_modules = {}  # Активные модули
        self.scan_depth = 0
        self.max_depth = 10
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('RapidRecon')
    
    def add_initial_target(self, target: str):
        """Добавить начальную цель для сканирования"""
        self.logger.info(f"Добавлена начальная цель: {target}")
        initial_node = {
            'type': 'initial_target',
            'data': target,
            'source': 'user_input',
            'depth': 0
        }
        self.discovered_nodes.append(initial_node)
        self.pending_scans.put(initial_node)
    
    def register_module(self, module_name: str, module_class):
        """Регистрация модуля в системе"""
        self.active_modules[module_name] = module_class
        self.logger.info(f"Модуль зарегистрирован: {module_name}")
    
    async def process_queue(self):
        """Асинхронная обработка очереди задач"""
        while not self.pending_scans.empty():
            task = self.pending_scans.get()
            await self.execute_task(task)
    
    async def execute_task(self, task: Dict[str, Any]):
        """Выполнение одной задачи"""
        self.logger.info(f"Выполняется задача: {task['type']} -> {task['data']}")
        
        # Здесь будет логика выбора модуля для задачи
        # Пока просто логируем
        await asyncio.sleep(0.1)  # Заглушка
        
        # Симуляция найденных данных
        new_nodes = self.simulate_findings(task)
        for node in new_nodes:
            self.discovered_nodes.append(node)
            self.pending_scans.put(node)
    
    def simulate_findings(self, task: Dict) -> List[Dict]:
        """Временная функция для симуляции находок"""
        if task['type'] == 'initial_target':
            return [{
                'type': 'subdomain',
                'data': f'api.{task["data"]}',
                'source': task['data'],
                'depth': task['depth'] + 1
            }]
        return []
