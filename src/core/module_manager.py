"""
Менеджер модулей RapidRecon
"""
import importlib
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import logging
from dataclasses import dataclass
from enum import Enum

class ModuleStatus(Enum):
    """Статусы модулей"""
    DISCOVERED = "discovered"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    ERROR = "error"
    DISABLED = "disabled"

class ModuleType(Enum):
    """Типы модулей"""
    SCANNER = "scanner"
    ANALYZER = "analyzer"
    ENUMERATOR = "enumerator"
    EXPLOITER = "exploiter"
    REPORT = "report"
    CUSTOM = "custom"

@dataclass
class ModuleInfo:
    """Информация о модуле"""
    name: str
    version: str
    description: str
    author: str
    module_type: ModuleType
    input_types: List[str]
    output_types: List[str]
    triggers: List[str]
    dependencies: List[str]
    config_schema: Dict[str, Any]
    enabled: bool = True
    priority: int = 1

class ModuleManager:
    """
    Менеджер модулей для динамической загрузки и управления модулями сканирования
    """
    
    def __init__(self, modules_dir: str = "src/modules"):
        self.modules_dir = Path(modules_dir)
        self.available_modules: Dict[str, Dict[str, Any]] = {}
        self.loaded_modules: Dict[str, Any] = {}
        self.module_instances: Dict[str, Any] = {}
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('ModuleManager')
        
        # Автоматическое обнаружение модулей при инициализации
        self.discover_modules()
    
    def discover_modules(self) -> Dict[str, ModuleInfo]:
        """
        Обнаружение всех доступных модулей в директории
        
        Returns:
            Dict с информацией о найденных модулях
        """
        self.logger.info(f"Поиск модулей в директории: {self.modules_dir}")
        
        if not self.modules_dir.exists():
            self.logger.warning(f"Директория модулей не существует: {self.modules_dir}")
            self.modules_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Создана директория модулей: {self.modules_dir}")
            return {}
        
        discovered_count = 0
        for module_file in self.modules_dir.glob("*/module_info.json"):
            try:
                with open(module_file, 'r', encoding='utf-8') as f:
                    module_data = json.load(f)
                
                # Валидация обязательных полей
                required_fields = ['name', 'version', 'description', 'author', 'module_type']
                if not all(field in module_data for field in required_fields):
                    self.logger.warning(f"Пропущен модуль с неполной информацией: {module_file}")
                    continue
                
                # Создание объекта ModuleInfo
                module_info = ModuleInfo(
                    name=module_data['name'],
                    version=module_data.get('version', '1.0.0'),
                    description=module_data.get('description', ''),
                    author=module_data.get('author', 'Unknown'),
                    module_type=ModuleType(module_data.get('module_type', 'custom')),
                    input_types=module_data.get('input_types', []),
                    output_types=module_data.get('output_types', []),
                    triggers=module_data.get('triggers', []),
                    dependencies=module_data.get('dependencies', []),
                    config_schema=module_data.get('config_schema', {}),
                    enabled=module_data.get('enabled', True),
                    priority=module_data.get('priority', 1)
                )
                
                self.available_modules[module_info.name] = {
                    'info': module_info,
                    'path': module_file.parent,
                    'status': ModuleStatus.DISCOVERED
                }
                
                discovered_count += 1
                self.logger.info(f"Обнаружен модуль: {module_info.name} v{module_info.version}")
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                self.logger.error(f"Ошибка загрузки модуля {module_file}: {e}")
                continue
        
        self.logger.info(f"Обнаружено модулей: {discovered_count}")
        return {name: data['info'] for name, data in self.available_modules.items()}
    
    def load_module(self, module_name: str) -> bool:
        """
        Динамическая загрузка конкретного модуля
        
        Args:
            module_name: Имя модуля для загрузки
            
        Returns:
            True если модуль успешно загружен
        """
        if module_name not in self.available_modules:
            self.logger.error(f"Модуль {module_name} не найден в доступных модулях")
            return False
        
        module_data = self.available_modules[module_name]
        module_path = module_data['path']
        module_info = module_data['info']
        
        if not module_info.enabled:
            self.logger.warning(f"Модуль {module_name} отключен и не будет загружен")
            return False
        
        try:
            # Добавляем путь модуля в sys.path для импорта
            if str(module_path) not in sys.path:
                sys.path.insert(0, str(module_path))
            
            # Импортируем основной модуль
            main_module_file = module_path / "main.py"
            if not main_module_file.exists():
                self.logger.error(f"Основной файл модуля не найден: {main_module_file}")
                return False
            
            # Динамический импорт
            spec = importlib.util.spec_from_file_location(module_name, main_module_file)
            if spec is None or spec.loader is None:
                self.logger.error(f"Не удалось создать spec для модуля {module_name}")
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Сохраняем загруженный модуль
            self.loaded_modules[module_name] = {
                'module': module,
                'info': module_info,
                'path': module_path,
                'status': ModuleStatus.LOADED
            }
            
            # Инициализируем экземпляр модуля, если есть класс Module
            if hasattr(module, 'Module'):
                module_instance = module.Module()
                self.module_instances[module_name] = module_instance
                self.loaded_modules[module_name]['status'] = ModuleStatus.INITIALIZED
                self.loaded_modules[module_name]['instance'] = module_instance
            
            self.logger.info(f"Модуль успешно загружен: {module_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка загрузки модуля {module_name}: {e}")
            self.available_modules[module_name]['status'] = ModuleStatus.ERROR
            return False
    
    def load_all_modules(self) -> Dict[str, bool]:
        """
        Загрузка всех доступных модулей
        
        Returns:
            Dict с результатами загрузки каждого модуля
        """
        results = {}
        for module_name in self.available_modules.keys():
            results[module_name] = self.load_module(module_name)
        return results
    
    def get_module(self, module_name: str) -> Optional[Any]:
        """
        Получить экземпляр загруженного модуля
        
        Args:
            module_name: Имя модуля
            
        Returns:
            Экземпляр модуля или None
        """
        return self.module_instances.get(module_name)
    
    def get_module_info(self, module_name: str) -> Optional[ModuleInfo]:
        """
        Получить информацию о модуле
        
        Args:
            module_name: Имя модуля
            
        Returns:
            ModuleInfo или None если модуль не найден
        """
        if module_name in self.available_modules:
            return self.available_modules[module_name]['info']
        return None
    
    def get_module_input_output(self, module_name: str) -> Dict[str, Any]:
        """
        Получить входные/выходные данные модуля
        
        Args:
            module_name: Имя модуля
            
        Returns:
            Dict с информацией о входах/выходах
        """
        module_info = self.get_module_info(module_name)
        if module_info:
            return {
                'input': module_info.input_types,
                'output': module_info.output_types,
                'triggers': module_info.triggers,
                'dependencies': module_info.dependencies
            }
        
        # Fallback для ненайденных модулей
        self.logger.warning(f"Информация о модуле {module_name} не найдена, возвращаем заглушку")
        return {
            'input': ['domain', 'ip'],
            'output': ['subdomains', 'open_ports'],
            'triggers': ['subdomain_scan', 'port_scan'],
            'dependencies': []
        }
    
    def get_modules_by_type(self, module_type: ModuleType) -> List[str]:
        """
        Получить список модулей по типу
        
        Args:
            module_type: Тип модуля для фильтрации
            
        Returns:
            Список имен модулей
        """
        return [
            name for name, data in self.available_modules.items()
            if data['info'].module_type == module_type and data['info'].enabled
        ]
    
    def get_modules_by_output(self, output_type: str) -> List[str]:
        """
        Получить модули, которые производят указанный тип вывода
        
        Args:
            output_type: Тип выходных данных
            
        Returns:
            Список подходящих модулей
        """
        return [
            name for name, data in self.available_modules.items()
            if output_type in data['info'].output_types and data['info'].enabled
        ]
    
    def enable_module(self, module_name: str) -> bool:
        """Включить модуль"""
        if module_name in self.available_modules:
            self.available_modules[module_name]['info'].enabled = True
            self.logger.info(f"Модуль включен: {module_name}")
            return True
        return False
    
    def disable_module(self, module_name: str) -> bool:
        """Отключить модуль"""
        if module_name in self.available_modules:
            self.available_modules[module_name]['info'].enabled = False
            self.logger.info(f"Модуль отключен: {module_name}")
            return True
        return False
    
    def get_loaded_modules_count(self) -> int:
        """Получить количество загруженных модулей"""
        return len([m for m in self.loaded_modules.values() if m['status'] == ModuleStatus.INITIALIZED])
    
    def get_available_modules_count(self) -> int:
        """Получить количество доступных модулей"""
        return len(self.available_modules)
    
    def list_modules(self) -> Dict[str, Dict[str, Any]]:
        """
        Получить список всех модулей с их статусами
        
        Returns:
            Dict с информацией о модулях
        """
        modules_list = {}
        for name, data in self.available_modules.items():
            modules_list[name] = {
                'info': {
                    'name': data['info'].name,
                    'version': data['info'].version,
                    'description': data['info'].description,
                    'type': data['info'].module_type.value,
                    'enabled': data['info'].enabled,
                    'priority': data['info'].priority
                },
                'status': data.get('status', ModuleStatus.DISCOVERED).value,
                'loaded': name in self.loaded_modules
            }
        return modules_list

# Пример использования
if __name__ == "__main__":
    # Тестирование менеджера модулей
    manager = ModuleManager("src/modules")
    
    print("=== Обнаруженные модули ===")
    for name, info in manager.list_modules().items():
        print(f"- {name}: {info['info']['description']} (статус: {info['status']})")
    
    print(f"\n=== Загрузка модулей ===")
    results = manager.load_all_modules()
    for module_name, success in results.items():
        status = "УСПЕХ" if success else "ОШИБКА"
        print(f"- {module_name}: {status}")
    
    print(f"\n=== Статистика ===")
    print(f"Доступно модулей: {manager.get_available_modules_count()}")
    print(f"Загружено модулей: {manager.get_loaded_modules_count()}")
    
    # Пример получения информации о входах/выходах
    if manager.available_modules:
        first_module = list(manager.available_modules.keys())[0]
        io_info = manager.get_module_input_output(first_module)
        print(f"\n=== IO информация для {first_module} ===")
        print(f"Входы: {io_info['input']}")
        print(f"Выходы: {io_info['output']}")
