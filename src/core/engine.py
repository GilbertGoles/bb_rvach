"""
Ядро RapidRecon - движок распространения сканирования с поддержкой эксплуатации и lateral movement
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
import ipaddress
import inspect

from .config import ConfigManager  # ← ДОБАВЛЕН импорт ConfigManager

class NodeType(Enum):
    """Типы обнаруживаемых узлов"""
    INITIAL_TARGET = "initial_target"
    SUBDOMAIN = "subdomain"
    IP_ADDRESS = "ip_address"
    SERVICE = "service"
    VULNERABILITY = "vulnerability"
    ACTIVE_HOST = "active_host"
    OPEN_PORTS = "open_ports"
    DOMAIN_SCAN = "domain_scan"
    VULNERABILITY_SCAN = "vulnerability_scan"
    EXPLOITATION = "exploitation"
    EXPLOITATION_SUCCESS = "exploitation_success"
    INTERNAL_SCAN = "internal_scan"
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
    services: List[Dict] = None
    vulnerability_data: Dict = None
    vulnerabilities: List[Dict] = None
    exploit_data: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.ports is None:
            self.ports = []
        if self.services is None:
            self.services = []
        if self.vulnerability_data is None:
            self.vulnerability_data = {}
        if self.vulnerabilities is None:
            self.vulnerabilities = []
        if self.exploit_data is None:
            self.exploit_data = {}

class PropagationEngine:
    """Движок авто-распространения сканирования с поддержкой эксплуатации"""
    
    def __init__(self, update_callback: Optional[Callable] = None):
        # Инициализация ConfigManager внутри движка
        self.config_manager = ConfigManager()
        
        # Получаем настройки из конфига
        engine_config = self.config_manager.get_engine_config()
        app_config = self.config_manager.get_app_config()
        
        # Используем настройки из конфига вместо хардкода
        self.max_depth = engine_config.get('max_depth', 10)
        self.max_concurrent_tasks = engine_config.get('max_concurrent_tasks', 5)
        self.rate_limit = engine_config.get('rate_limit', 10)
        
        # Инициализация остальных атрибутов
        self.discovered_nodes: List[ScanNode] = []
        self.pending_scans = Queue()
        self.completed_scans: Dict[str, Dict] = {}
        self.active_modules: Dict[str, Any] = {}
        self.scan_depth = 0
        self.is_running = False
        self.update_callback = update_callback
        
        self.stats = {
            'total_scans': 0,
            'successful_scans': 0,
            'failed_scans': 0,
            'nodes_discovered': 0,
            'modules_executed': 0,
            'vulnerabilities_found': 0,
            'exploits_attempted': 0,
            'exploits_successful': 0,
            'lateral_movements': 0
        }
        
        # Настройка логирования с использованием конфига
        logging_config = self.config_manager.get_app_config()
        debug_mode = logging_config.get('debug', True)
        
        logging.basicConfig(
            level=logging.DEBUG if debug_mode else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('RapidRecon')
        
        self.logger.info(f"PropagationEngine инициализирован с настройками из конфига")
        self.logger.info(f"Глубина: {self.max_depth}, Потоки: {self.max_concurrent_tasks}, Лимит: {self.rate_limit}/сек")
    
    def set_scan_profile(self, profile_name: str) -> bool:
        """Установить профиль сканирования"""
        success = self.config_manager.set_profile(profile_name)
        if success:
            # Обновляем настройки из нового профиля
            profile_config = self.config_manager.get_active_config()
            self.rate_limit = profile_config.get('rate_limit', self.rate_limit)
            self.max_depth = profile_config.get('max_depth', self.max_depth)
            
            # Обновляем настройки модулей
            for module_name, module in self.active_modules.items():
                if hasattr(module, 'update_config'):
                    module_config = self.config_manager.get_module_config(module_name)
                    module.update_config(module_config)
            
            self.logger.info(f"Профиль сканирования изменен на: {profile_name}")
            self._notify_gui_update('profile_changed', profile_name)
        
        return success
    
    def get_available_profiles(self) -> List[str]:
        """Получить список доступных профилей"""
        return self.config_manager.get_available_profiles()
    
    def get_current_profile_info(self) -> Dict[str, Any]:
        """Получить информацию о текущем профиле"""
        profile_name = self.config_manager.active_profile
        profile_config = self.config_manager.get_active_config()
        
        return {
            'name': profile_name,
            'rate_limit': profile_config.get('rate_limit'),
            'max_depth': profile_config.get('max_depth'),
            'modules': profile_config.get('modules', []),
            'description': profile_config.get('description', 'Нет описания')
        }
    
    def reload_config(self) -> bool:
        """Перезагрузить конфигурацию из файлов"""
        try:
            # Перезагружаем все конфиги
            self.config_manager.load_config()
            self.config_manager.load_profiles()
            self.config_manager.load_modules_config()
            
            # Обновляем настройки движка
            engine_config = self.config_manager.get_engine_config()
            self.max_depth = engine_config.get('max_depth', self.max_depth)
            self.max_concurrent_tasks = engine_config.get('max_concurrent_tasks', self.max_concurrent_tasks)
            self.rate_limit = engine_config.get('rate_limit', self.rate_limit)
            
            self.logger.info("Конфигурация перезагружена из файлов")
            self._notify_gui_update('config_reloaded')
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка перезагрузки конфигурации: {e}")
            return False
    
    def add_initial_target(self, target: str):
        """Добавить начальную цель для сканирования"""
        self.logger.info(f"Добавлена начальная цель: {target}")
        
        # Определяем тип цели и соответствующий модуль
        if self._is_domain(target):
            module = 'subdomain_scanner'
            node_type = NodeType.INITIAL_TARGET
        elif self._is_ip_address(target):
            module = 'ping_scanner'
            node_type = NodeType.INITIAL_TARGET
        else:
            module = 'ping_scanner'  # fallback
            node_type = NodeType.INITIAL_TARGET
        
        initial_node = ScanNode(
            node_id=f"initial_{target}_{int(time.time())}",
            type=node_type,
            data=target,
            source='user_input',
            depth=0,
            timestamp=time.time(),
            module=module,
            metadata={'priority': 'high', 'target_type': self._get_target_type(target)}
        )
        self.discovered_nodes.append(initial_node)
        self.pending_scans.put(initial_node)
        self.stats['nodes_discovered'] += 1
        
        # Уведомляем GUI о новом узле
        self._notify_gui_update('node_added', initial_node)
    
    def _is_domain(self, target: str) -> bool:
        """Проверка, является ли цель доменным именем"""
        if '.' not in target:
            return False
        if target.replace('.', '').isdigit():
            return False
        try:
            ipaddress.ip_address(target)
            return False
        except ValueError:
            return True
    
    def _is_ip_address(self, target: str) -> bool:
        """Проверка, является ли цель IP-адресом"""
        try:
            ipaddress.ip_address(target)
            return True
        except ValueError:
            return False
    
    def _get_target_type(self, target: str) -> str:
        """Определение типа цели"""
        if self._is_domain(target):
            return 'domain'
        elif self._is_ip_address(target):
            return 'ip_address'
        else:
            return 'unknown'
    
    def add_custom_node(self, node_type: NodeType, data: Any, source: str, depth: int, 
                       module: str = "default", metadata: Dict = None, ports: List[int] = None,
                       services: List[Dict] = None, vulnerability_data: Dict = None,
                       vulnerabilities: List[Dict] = None, exploit_data: Dict = None):
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
            ports=ports or [],
            services=services or [],
            vulnerability_data=vulnerability_data or {},
            vulnerabilities=vulnerabilities or [],
            exploit_data=exploit_data or {}
        )
        self.discovered_nodes.append(node)
        self.pending_scans.put(node)
        self.stats['nodes_discovered'] += 1
        self.logger.info(f"Добавлен кастомный узел: {node_type.value} -> {data} (модуль: {module})")
        
        # Уведомляем GUI о новом узле
        self._notify_gui_update('node_added', node)
    
    def register_module(self, module_name: str, module_class):
        """Регистрация модуля в системе"""
        # Получаем конфигурацию модуля
        module_config = self.config_manager.get_module_config(module_name)
        
        # Создаем экземпляр модуля с конфигурацией
        try:
            # Пробуем передать конфиг в конструктор
            if hasattr(module_class, '__init__'):
                # Проверяем сигнатуру конструктора
                sig = inspect.signature(module_class.__init__)
                params = list(sig.parameters.keys())
                
                if len(params) > 1 and 'config' in params[1]:
                    module_instance = module_class(module_config)
                else:
                    module_instance = module_class()
                    if hasattr(module_instance, 'update_config'):
                        module_instance.update_config(module_config)
            else:
                module_instance = module_class()
                
            self.active_modules[module_name] = module_instance
            self.logger.info(f"Модуль зарегистрирован: {module_name}")
            
            # Уведомляем GUI о новом модуле
            self._notify_gui_update('module_registered', module_name)
            
        except Exception as e:
            self.logger.error(f"Ошибка создания модуля {module_name}: {e}")
            # Создаем модуль без конфига как fallback
            try:
                module_instance = module_class()
                self.active_modules[module_name] = module_instance
                self.logger.info(f"Модуль зарегистрирован (без конфига): {module_name}")
            except Exception as e2:
                self.logger.error(f"Не удалось создать модуль {module_name}: {e2}")
    
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
                'discovered_nodes': len(self.discovered_nodes),
                'vulnerabilities_found': self.stats['vulnerabilities_found'],
                'exploits_successful': self.stats['exploits_successful']
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
            # Получаем таймаут из конфига модуля
            module_config = self.config_manager.get_module_config(task.module)
            timeout = module_config.get('timeout', 30.0)
            
            # Логика выбора и выполнения модуля
            module = self.select_module_for_task(task)
            
            if module:
                # Выполнение модуля с таймаутом из конфига
                await asyncio.wait_for(
                    self.run_module(module, task),
                    timeout=timeout
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
            # Передаем дополнительные данные если есть
            scan_data = [task.data]
            if task.services:
                # Для vulnerability_scanner передаем информацию о сервисах
                scan_data = [task.data, task.services]
            elif task.vulnerabilities:
                # Для exploitation модуля передаем уязвимости
                scan_data = [task.data, task.vulnerabilities]
            
            results = await module.scan(scan_data)
            await self.process_module_results(results, task)
        else:
            # Запасной вариант для кастомных модулей
            await self.default_scan_behavior(task)
    
    async def process_module_results(self, results: Dict[str, Any], source_task: ScanNode):
        """Обработка результатов модуля сканирования"""
        
        # Обработка результатов subdomain_scanner
        if results.get("module") == "subdomain_scanner" and results.get("subdomains"):
            for subdomain_info in results["subdomains"]:
                new_node = ScanNode(
                    node_id=f"subdomain_{subdomain_info['subdomain']}_{int(time.time())}",
                    type=NodeType.SUBDOMAIN,
                    data=subdomain_info["subdomain"],
                    source=source_task.node_id,
                    depth=source_task.depth + 1,
                    timestamp=time.time(),
                    module='ping_scanner',
                    metadata={
                        'confidence': subdomain_info.get('confidence', 0.8),
                        'source': subdomain_info.get('source', 'unknown')
                    }
                )
                await self.add_discovered_node(new_node)
        
        # Обработка результатов ping_scanner
        elif results.get("module") == "ping_scanner" and results.get("active_hosts"):
            for host in results["active_hosts"]:
                new_node = ScanNode(
                    node_id=f"active_host_{host['ip']}_{int(time.time())}",
                    type=NodeType.ACTIVE_HOST,
                    data=host["ip"],
                    source=source_task.node_id,
                    depth=source_task.depth + 1,
                    timestamp=time.time(),
                    module='port_scanner',
                    metadata={
                        'host_status': 'active', 
                        'response_time': host.get('response_time'),
                        'original_target': source_task.data
                    }
                )
                await self.add_discovered_node(new_node)
            
            # Дополнительная логика: для доменов запускаем поиск поддоменов
            if (source_task.type == NodeType.INITIAL_TARGET and 
                self._is_domain(source_task.data)):
                domain_scan_node = ScanNode(
                    node_id=f"domain_scan_{source_task.data}_{int(time.time())}",
                    type=NodeType.DOMAIN_SCAN,
                    data=source_task.data,
                    source=source_task.node_id,
                    depth=source_task.depth + 1,
                    timestamp=time.time(),
                    module='subdomain_scanner',
                    metadata={'triggered_by': 'ping_scanner_results'}
                )
                await self.add_discovered_node(domain_scan_node)
        
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
                        ports=[port_info["port"] for port_info in ports]
                    )
                    await self.add_discovered_node(new_node)
        
        # Обработка результатов service_detector
        elif results.get("module") == "service_detector" and results.get("services"):
            for host, services in results["services"].items():
                if services:  # Если есть сервисы
                    # Создаем узел для сканирования уязвимостей
                    vulnerability_scan_node = ScanNode(
                        node_id=f"vuln_scan_{host}_{int(time.time())}",
                        type=NodeType.VULNERABILITY_SCAN,
                        data=host,
                        source=source_task.node_id,
                        depth=source_task.depth + 1,
                        timestamp=time.time(),
                        module='vulnerability_scanner',
                        metadata={'service_count': len(services)},
                        services=services
                    )
                    await self.add_discovered_node(vulnerability_scan_node)
                    
                    # Также создаем узлы для каждого обнаруженного сервиса
                    for service_info in services:
                        service_node = ScanNode(
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
                                'port': service_info.get('port'),
                                'protocol': service_info.get('protocol', 'tcp')
                            }
                        )
                        await self.add_discovered_node(service_node)
        
        # Обработка результатов vulnerability_scanner
        elif results.get("module") == "vulnerability_scanner" and results.get("vulnerabilities"):
            vulnerabilities = results["vulnerabilities"]
            
            for vuln in vulnerabilities:
                self.stats['vulnerabilities_found'] += 1
                
                vulnerability_node = ScanNode(
                    node_id=f"vuln_{vuln.get('cve', vuln['type'])}_{int(time.time())}",
                    type=NodeType.VULNERABILITY,
                    data=f"{vuln.get('cve', vuln['type'])} - {vuln['description']}",
                    source=source_task.node_id,
                    depth=source_task.depth + 1,
                    timestamp=time.time(),
                    module='report_generator',
                    metadata={
                        'severity': vuln.get('severity', 'unknown'),
                        'confidence': vuln.get('confidence', 0.0),
                        'cvss_score': vuln.get('cvss_score', 0.0)
                    },
                    vulnerability_data=vuln
                )
                await self.add_discovered_node(vulnerability_node)
                
                # Логируем найденную уязвимость
                self.logger.warning(
                    f"🔴 Найдена уязвимость: {vuln.get('cve', vuln['type'])} "
                    f"(Severity: {vuln.get('severity', 'unknown')}) "
                    f"на {source_task.data}"
                )
            
            # ОБРАБОТКА ЭКСПЛУАТАЦИИ - запускаем эксплуатацию для эксплуатируемых уязвимостей
            exploitable_vulns = [
                vuln for vuln in vulnerabilities
                if vuln.get('exploit_available', False) or 
                   vuln.get('type') in ['anonymous_ftp', 'exposed_endpoint', 'weak_password']
            ]
            
            if exploitable_vulns:
                self.stats['exploits_attempted'] += len(exploitable_vulns)
                
                exploitation_node = ScanNode(
                    node_id=f"exploitation_{source_task.data}_{int(time.time())}",
                    type=NodeType.EXPLOITATION,
                    data=f"Exploit {len(exploitable_vulns)} vulns on {source_task.data}",
                    source=source_task.node_id,
                    depth=source_task.depth + 1,
                    timestamp=time.time(),
                    module='exploitation',
                    metadata={
                        'target': source_task.data,
                        'vulnerability_count': len(exploitable_vulns),
                        'vulnerability_types': [vuln.get('type') for vuln in exploitable_vulns]
                    },
                    vulnerabilities=exploitable_vulns
                )
                await self.add_discovered_node(exploitation_node)
                
                self.logger.info(f"🚀 Запуск эксплуатации {len(exploitable_vulns)} уязвимостей на {source_task.data}")
        
        # Обработка результатов эксплуатации
        elif (results.get("module") == "exploitation" and 
              results.get("exploitation_results")):
            
            for exploit_result in results["exploitation_results"]:
                if exploit_result.get("success"):
                    self.stats['exploits_successful'] += 1
                    
                    exploit_node = ScanNode(
                        node_id=f"exploit_success_{source_task.data}_{int(time.time())}",
                        type=NodeType.EXPLOITATION_SUCCESS,
                        data=f"{exploit_result['access_type']} доступ - Успех",
                        source=source_task.node_id,
                        depth=source_task.depth + 1,
                        timestamp=time.time(),
                        module='report_generator',
                        metadata={
                            'severity': 'critical',
                            'access_type': exploit_result.get('access_type'),
                            'credentials_obtained': bool(exploit_result.get('credentials')),
                            'shell_obtained': exploit_result.get('shell_obtained', False)
                        },
                        exploit_data=exploit_result
                    )
                    await self.add_discovered_node(exploit_node)
                    
                    self.logger.critical(
                        f"💥 УСПЕШНАЯ ЭКСПЛУАТАЦИЯ: {exploit_result.get('access_type')} "
                        f"доступ к {source_task.data}"
                    )
                    
                    # Если получили доступ к системе - запускаем внутреннее сканирование
                    if exploit_result.get("access_type") in ["ssh_access", "shell_access", "remote_code_execution"]:
                        await self.start_lateral_movement(exploit_result, source_task)
        
        # Обработка результатов internal_scanner (lateral movement)
        elif results.get("module") == "internal_scanner" and results.get("internal_hosts"):
            self.stats['lateral_movements'] += 1
            
            for host_info in results["internal_hosts"]:
                # Создаем узлы для внутренних хостов
                internal_node = ScanNode(
                    node_id=f"internal_host_{host_info['ip']}_{int(time.time())}",
                    type=NodeType.ACTIVE_HOST,
                    data=host_info["ip"],
                    source=source_task.node_id,
                    depth=source_task.depth + 1,
                    timestamp=time.time(),
                    module='port_scanner',
                    metadata={
                        'host_status': 'active',
                        'internal_network': True,
                        'source_exploit': source_task.exploit_data.get('access_type'),
                        'lateral_movement': True
                    }
                )
                await self.add_discovered_node(internal_node)
        
        # Обработка общих результатов для других модулей
        else:
            new_nodes = self.simulate_findings(source_task)
            await self.process_findings(new_nodes, source_task)
        
        # Уведомляем GUI о результатах модуля
        self._notify_gui_update('module_results', {
            'task': source_task,
            'results': results
        })
    
    async def start_lateral_movement(self, exploit_result: Dict, source_task: ScanNode):
        """Начать перемещение внутри сети после успешной эксплуатации"""
        self.logger.info(f"🚀 Начинаем lateral movement с {source_task.data}")
        
        if exploit_result.get("access_type") in ["ssh_access", "shell_access", "remote_code_execution"]:
            # Получаем информацию о сети изнутри
            internal_scan_node = ScanNode(
                node_id=f"internal_scan_{source_task.data}_{int(time.time())}",
                type=NodeType.INTERNAL_SCAN,
                data=f"Internal scan from {exploit_result.get('credentials', {}).get('username', 'unknown')}@{source_task.data}",
                source=source_task.node_id,
                depth=source_task.depth + 1,
                timestamp=time.time(),
                module='internal_scanner',
                metadata={
                    'access_type': exploit_result.get('access_type'),
                    'credentials_available': bool(exploit_result.get('credentials')),
                    'lateral_movement': True
                },
                exploit_data=exploit_result
            )
            await self.add_discovered_node(internal_scan_node)
            
            self.logger.info(f"🔍 Запуск внутреннего сканирования с компрометированной системы {source_task.data}")

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
            # Расширенная логика выбора модуля по типу узла
            module_map = {
                NodeType.INITIAL_TARGET: 'ping_scanner',
                NodeType.SUBDOMAIN: 'ping_scanner',
                NodeType.IP_ADDRESS: 'ping_scanner',
                NodeType.DOMAIN_SCAN: 'subdomain_scanner',
                NodeType.ACTIVE_HOST: 'port_scanner',
                NodeType.OPEN_PORTS: 'service_detector',
                NodeType.SERVICE: 'vulnerability_scanner',
                NodeType.VULNERABILITY_SCAN: 'vulnerability_scanner',
                NodeType.VULNERABILITY: 'report_generator',
                NodeType.EXPLOITATION: 'exploitation',
                NodeType.EXPLOITATION_SUCCESS: 'report_generator',
                NodeType.INTERNAL_SCAN: 'internal_scanner'
            }
            module_name = module_map.get(task.type)
        
        return self.active_modules.get(module_name)
    
    def simulate_findings(self, task: ScanNode) -> List[ScanNode]:
        """Временная функция для симуляции находок (для демонстрации)"""
        if task.type == NodeType.INITIAL_TARGET and self._is_domain(task.data):
            # Для доменов - находим поддомены
            subdomains = ['api', 'admin', 'test', 'dev', 'staging', 'www', 'mail', 'ftp']
            return [
                ScanNode(
                    node_id=f"subdomain_{sd}_{task.data}_{int(time.time())}",
                    type=NodeType.SUBDOMAIN,
                    data=f'{sd}.{task.data}',
                    source=task.node_id,
                    depth=task.depth + 1,
                    timestamp=time.time(),
                    module='ping_scanner',
                    metadata={'confidence': 0.8, 'simulated': True}
                ) for sd in subdomains
            ]
        elif task.type == NodeType.SUBDOMAIN:
            # Симуляция обнаружения IP-адресов для поддоменов
            return [
                ScanNode(
                    node_id=f"ip_{task.data.replace('.', '_')}_{int(time.time())}",
                    type=NodeType.ACTIVE_HOST,
                    data=f'192.168.1.{random.randint(1, 254)}',
                    source=task.node_id,
                    depth=task.depth + 1,
                    timestamp=time.time(),
                    module='port_scanner',
                    metadata={'type': 'A_record', 'simulated': True}
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
                    metadata={'port_count': len(open_ports), 'simulated': True},
                    ports=open_ports
                )
            ]
        elif task.type == NodeType.DOMAIN_SCAN:
            # Симуляция поиска поддоменов
            subdomains = ['ns1', 'ns2', 'cdn', 'assets', 'static']
            return [
                ScanNode(
                    node_id=f"subdomain_{sd}_{task.data}_{int(time.time())}",
                    type=NodeType.SUBDOMAIN,
                    data=f'{sd}.{task.data}',
                    source=task.node_id,
                    depth=task.depth + 1,
                    timestamp=time.time(),
                    module='ping_scanner',
                    metadata={'confidence': 0.7, 'simulated': True}
                ) for sd in subdomains
            ]
        elif task.type == NodeType.VULNERABILITY_SCAN:
            # Симуляция обнаружения уязвимостей
            vulnerabilities = [
                {
                    'type': 'weak_password',
                    'cve': 'CVE-2023-12345',
                    'description': 'Weak SSH password detected',
                    'severity': 'high',
                    'confidence': 0.9,
                    'cvss_score': 7.5,
                    'exploit_available': True
                },
                {
                    'type': 'outdated_software',
                    'cve': 'CVE-2023-54321',
                    'description': 'Outdated Apache version',
                    'severity': 'medium',
                    'confidence': 0.8,
                    'cvss_score': 5.5,
                    'exploit_available': False
                }
            ]
            return [
                ScanNode(
                    node_id=f"vuln_{vuln['cve']}_{int(time.time())}",
                    type=NodeType.VULNERABILITY,
                    data=f"{vuln['cve']} - {vuln['description']}",
                    source=task.node_id,
                    depth=task.depth + 1,
                    timestamp=time.time(),
                    module='report_generator',
                    metadata={
                        'severity': vuln['severity'],
                        'confidence': vuln['confidence'],
                        'cvss_score': vuln['cvss_score'],
                        'simulated': True
                    },
                    vulnerability_data=vuln
                ) for vuln in vulnerabilities
            ]
        elif task.type == NodeType.EXPLOITATION:
            # Симуляция успешной эксплуатации
            exploit_results = [
                {
                    'success': True,
                    'access_type': 'ssh_access',
                    'credentials': {'username': 'admin', 'password': 'admin123'},
                    'shell_obtained': True,
                    'internal_network_access': True
                }
            ]
            return [
                ScanNode(
                    node_id=f"exploit_success_{task.data}_{int(time.time())}",
                    type=NodeType.EXPLOITATION_SUCCESS,
                    data=f"SSH доступ - Успех",
                    source=task.node_id,
                    depth=task.depth + 1,
                    timestamp=time.time(),
                    module='report_generator',
                    metadata={
                        'severity': 'critical',
                        'access_type': 'ssh_access',
                        'credentials_obtained': True,
                        'shell_obtained': True,
                        'simulated': True
                    },
                    exploit_data=exploit_results[0]
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
            'max_depth': self.max_depth,
            'current_profile': self.get_current_profile_info()
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
                    'ports': node.ports,
                    'services': node.services,
                    'vulnerability_data': node.vulnerability_data,
                    'vulnerabilities': node.vulnerabilities,
                    'exploit_data': node.exploit_data
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
    """Демонстрация работы движка с поддержкой эксплуатации"""
    # Теперь создаем движок БЕЗ параметров конфигурации
    engine = PropagationEngine(update_callback=gui_update_callback)
    
    # Можем изменить профиль сканирования
    engine.set_scan_profile("aggressive")
    
    # Добавляем начальные цели разных типов
    engine.add_initial_target("example.com")  # Домен
    engine.add_initial_target("192.168.1.1")  # IP-адрес
    
    # Запускаем обработку
    await engine.process_queue()
    
    # Выводим статистику
    stats = engine.get_statistics()
    print(f"Статистика: {stats}")

if __name__ == "__main__":
    asyncio.run(main())
