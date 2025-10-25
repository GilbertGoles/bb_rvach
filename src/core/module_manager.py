"""
Менеджер модулей RapidRecon
"""
import importlib
import os
from pathlib import Path
from typing import Dict, Any
import json

class ModuleManager:
    def __init__(self, modules_dir: str = "src/modules"):
        self.modules_dir = Path(modules_dir)
        self.available_modules = {}
        self.loaded_modules = {}
    
    def discover_modules(self):
        """Обнаружение всех доступных модулей"""
        if not self.modules_dir.exists():
            self.modules_dir.mkdir(parents=True)
            return
        
        for module_file in self.modules_dir.glob("*/module_info.json"):
            with open(module_file, 'r') as f:
                module_info = json.load(f)
                self.available_modules[module_info['name']] = {
                    'info': module_info,
                    'path': module_file.parent
                }
    
    def load_module(self, module_name: str):
        """Загрузка конкретного модуля"""
        if module_name not in self.available_modules:
            raise ValueError(f"Модуль {module_name} не найден")
        
        module_path = self.available_modules[module_name]['path']
        # Здесь будет динамическая загрузка модуля
        # Пока заглушка
        self.loaded_modules[module_name] = {
            'status': 'loaded',
            'path': module_path
        }
    
    def get_module_input_output(self, module_name: str) -> Dict[str, Any]:
        """Получить входные/выходные данные модуля"""
        # Заглушка - в будущем будет из module_info.json
        return {
            'input': ['domain', 'ip'],
            'output': ['subdomains', 'open_ports'],
            'triggers': ['subdomain_scan', 'port_scan']
        }
