"""
Главный файл RapidRecon
"""
import asyncio
import threading
import sys
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Type, Callable
import signal
import time
import importlib

# Добавление корневой директории в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

from core.engine import PropagationEngine
from core.module_manager import ModuleManager
from gui.main_window import MainWindow

class RapidRecon:
    """
    Основной класс приложения RapidRecon
    Координирует работу движка, менеджера модулей и интерфейса
    """
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        
        # Инициализация компонентов
        self.engine: Optional[PropagationEngine] = None
        self.module_manager: Optional[ModuleManager] = None
        self.gui: Optional[MainWindow] = None
        
        # Состояние приложения
        self.is_running = False
        self.engine_thread: Optional[threading.Thread] = None
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.last_update_time = 0
        self.update_interval = 0.5  # Интервал обновления GUI в секундах
        
        # Инициализация компонентов
        self.initialize_components()
        
        # Настройка обработчиков сигналов
        self.setup_signal_handlers()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Загрузка конфигурации приложения
        
        Returns:
            Dict с конфигурацией
        """
        default_config = {
            "app": {
                "name": "RapidRecon",
                "version": "1.0.0",
                "debug": False,
                "max_threads": 10,
                "update_interval": 0.5
            },
            "engine": {
                "max_depth": 5,
                "max_concurrent_tasks": 5,
                "rate_limit": 50
            },
            "modules": {
                "directory": "src/modules",
                "auto_load": True,
                "auto_discover": True,
                "builtin_modules": [
                    "ping_scanner",
                    "port_scanner", 
                    "service_detector"
                ]
            },
            "gui": {
                "width": 1400,
                "height": 900,
                "theme": "dark"
            },
            "logging": {
                "level": "INFO",
                "file": "rapidrecon.log",
                "max_size_mb": 10
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                import json
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Рекурсивное обновление конфигурации по умолчанию
                    self._update_dict_recursive(default_config, loaded_config)
            
            # Сохранение конфигурации (создание файла если не существует)
            self.save_config(default_config)
            
        except Exception as e:
            print(f"⚠️ Ошибка загрузки конфигурации: {e}. Используются значения по умолчанию.")
        
        return default_config
    
    def _update_dict_recursive(self, target: Dict, source: Dict):
        """Рекурсивное обновление словаря"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_dict_recursive(target[key], value)
            else:
                target[key] = value
    
    def save_config(self, config: Dict[str, Any]):
        """Сохранение конфигурации в файл"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            import json
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Ошибка сохранения конфигурации: {e}")
    
    def setup_logging(self):
        """Настройка системы логирования"""
        log_config = self.config['logging']
        log_level = getattr(logging, log_config['level'].upper(), logging.INFO)
        
        # Форматтер для логов
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Обработчик для файла
        file_handler = logging.FileHandler(
            log_config['file'],
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        # Обработчик для консоли
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Настройка корневого логгера
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Логгер для приложения
        self.logger = logging.getLogger('RapidRecon')
        self.logger.info("✅ Система логирования инициализирована")
    
    def initialize_components(self):
        """Инициализация основных компонентов приложения"""
        try:
            # Инициализация менеджера модулей
            modules_dir = self.config['modules']['directory']
            self.module_manager = ModuleManager(modules_dir)
            
            # Автоматическое обнаружение модулей
            if self.config['modules']['auto_discover']:
                discovered = self.module_manager.discover_modules()
                self.logger.info(f"🔍 Обнаружено модулей: {len(discovered)}")
            
            # Инициализация движка с callback для обновления GUI
            engine_config = self.config['engine']
            self.engine = PropagationEngine(
                max_depth=engine_config['max_depth'],
                max_concurrent_tasks=engine_config['max_concurrent_tasks'],
                rate_limit=engine_config['rate_limit'],
                update_callback=self.on_engine_update
            )
            
            # Регистрация модулей
            self.register_modules()
            
            # Автоматическая загрузка модулей из директории
            if self.config['modules']['auto_load']:
                load_results = self.module_manager.load_all_modules()
                loaded_count = sum(1 for result in load_results.values() if result)
                self.logger.info(f"📦 Загружено модулей: {loaded_count}/{len(load_results)}")
                
                # Регистрация загруженных модулей в движке
                for module_name, success in load_results.items():
                    if success:
                        module_instance = self.module_manager.get_module(module_name)
                        if module_instance:
                            self.engine.register_module(module_name, module_instance)
            
            # Инициализация GUI
            self.gui = MainWindow(self.engine, self.module_manager)
            
            # Настройка интервала обновления из конфигурации
            self.update_interval = self.config['app'].get('update_interval', 0.5)
            
            self.logger.info("✅ Все компоненты инициализированы")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации компонентов: {e}")
            raise
    
    def register_modules(self):
        """Регистрация всех модулей в движке"""
        self.logger.info("🔧 Регистрация модулей...")
        
        builtin_modules = self.config['modules'].get('builtin_modules', [])
        registered_count = 0
        
        # Регистрация встроенных модулей
        for module_name in builtin_modules:
            try:
                module_class = self.load_builtin_module(module_name)
                if module_class:
                    self.engine.register_module(module_name, module_class)
                    registered_count += 1
                    self.logger.info(f"✅ Зарегистрирован встроенный модуль: {module_name}")
                else:
                    self.logger.warning(f"⚠️ Не удалось загрузить встроенный модуль: {module_name}")
            except Exception as e:
                self.logger.error(f"❌ Ошибка регистрации модуля {module_name}: {e}")
        
        self.logger.info(f"📋 Зарегистрировано встроенных модулей: {registered_count}")
    
    def load_builtin_module(self, module_name: str) -> Optional[Type]:
        """
        Загрузка встроенного модуля по имени
        
        Args:
            module_name: Имя модуля для загрузки
            
        Returns:
            Класс модуля или None если не удалось загрузить
        """
        module_paths = {
            "ping_scanner": "modules.ping_scanner.module.PingScanner",
            "port_scanner": "modules.port_scanner.module.PortScanner",
            "service_detector": "modules.service_detector.module.ServiceDetector"
        }
        
        if module_name not in module_paths:
            self.logger.warning(f"⚠️ Неизвестный встроенный модуль: {module_name}")
            return None
        
        try:
            module_path = module_paths[module_name]
            module_parts = module_path.split('.')
            class_name = module_parts[-1]
            module_path = '.'.join(module_parts[:-1])
            
            # Динамический импорт модуля
            module = importlib.import_module(module_path)
            module_class = getattr(module, class_name)
            
            return module_class
            
        except ImportError as e:
            self.logger.warning(f"⚠️ Модуль {module_name} не найден: {e}")
            return None
        except AttributeError as e:
            self.logger.warning(f"⚠️ Класс модуля {module_name} не найден: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки модуля {module_name}: {e}")
            return None
    
    def on_engine_update(self, event_type: str, data: Any = None):
        """
        Callback при обновлении движка для синхронизации с GUI
        
        Args:
            event_type: Тип события от движка
            data: Данные связанные с событием
        """
        try:
            current_time = time.time()
            
            # Ограничиваем частоту обновлений чтобы не перегружать GUI
            if current_time - self.last_update_time < self.update_interval:
                return
                
            self.last_update_time = current_time
            
            # Обработка различных событий от движка
            if event_type in ['node_discovered', 'node_added', 'task_completed']:
                if self.gui:
                    # Обновляем граф и статистику
                    self.gui.update_graph_from_engine()
                    self.gui.update_statistics()
                    
            elif event_type == 'scan_started':
                if self.gui:
                    self.gui.on_scan_started(data)
                    
            elif event_type == 'scan_completed':
                if self.gui:
                    self.gui.on_scan_completed(data)
                    
            elif event_type == 'task_failed':
                if self.gui:
                    self.gui.on_task_failed(data)
                    
            elif event_type == 'progress_update':
                if self.gui:
                    self.gui.on_progress_update(data)
                    
            elif event_type == 'module_results':
                if self.gui:
                    self.gui.on_module_results(data)
            
            # Логируем важные события
            if event_type in ['node_discovered', 'task_failed', 'scan_completed']:
                self.logger.debug(f"Engine event: {event_type} - {data}")
                
        except Exception as e:
            self.logger.warning(f"Ошибка в engine callback: {e}")
    
    def setup_signal_handlers(self):
        """Настройка обработчиков сигналов для graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"📶 Получен сигнал {signum}. Завершение работы...")
            self.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler) # Сигнал завершения
    
    def start_engine_async(self):
        """Запуск асинхронного движка в отдельном потоке"""
        try:
            self.logger.info("🔧 Запуск асинхронного движка...")
            
            # Создание нового event loop для потока
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            
            # Постоянная обработка задач
            if self.engine:
                while self.is_running:
                    # Проверяем есть ли задачи в очереди
                    if not self.engine.pending_scans.empty():
                        self.event_loop.run_until_complete(self.engine.process_queue())
                    else:
                        # Ждем новые задачи
                        time.sleep(0.1)
                        
        except Exception as e:
            self.logger.error(f"❌ Ошибка в асинхронном движке: {e}")
        finally:
            if self.event_loop:
                self.event_loop.close()
    
    def run(self):
        """
        Основной метод запуска приложения
        """
        try:
            self.is_running = True
            
            print("🚀 RapidRecon запускается...")
            self.logger.info("🚀 Запуск приложения RapidRecon")
            
            app_config = self.config['app']
            self.logger.info(f"📋 Версия: {app_config['version']}")
            self.logger.info(f"🐛 Режим отладки: {app_config['debug']}")
            
            # Вывод информации о модулях
            engine_stats = self.engine.get_statistics()
            self.logger.info(f"🔧 Активных модулей: {engine_stats.get('active_modules', 0)}")
            self.logger.info(f"📊 Макс. глубина: {self.engine.max_depth}")
            self.logger.info(f"⚡ Лимит скорости: {self.engine.rate_limit}/сек")
            self.logger.info(f"🔄 Интервал обновления GUI: {self.update_interval}с")
            
            # Запуск асинхронного движка в отдельном потоке
            self.engine_thread = threading.Thread(
                target=self.start_engine_async,
                daemon=True,
                name="EngineThread"
            )
            self.engine_thread.start()
            
            # Запуск GUI (блокирующий вызов)
            self.logger.info("🎨 Запуск графического интерфейса...")
            self.gui.show()
            
        except KeyboardInterrupt:
            self.logger.info("⏹️ Прервано пользователем (Ctrl+C)")
        except Exception as e:
            self.logger.error(f"💥 Критическая ошибка: {e}")
            self.show_error_message(f"Критическая ошибка: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """
        Корректное завершение работы приложения
        """
        if not self.is_running:
            return
            
        self.is_running = False
        self.logger.info("🔚 Завершение работы RapidRecon...")
        
        try:
            # Остановка движка
            if self.engine:
                self.engine.stop_engine()
                self.logger.info("✅ Движок остановлен")
            
            # Завершение асинхронного event loop
            if self.event_loop and self.event_loop.is_running():
                self.event_loop.stop()
                self.logger.info("✅ Event loop остановлен")
            
            # Ожидание завершения потока движка
            if self.engine_thread and self.engine_thread.is_alive():
                self.engine_thread.join(timeout=5.0)
                if self.engine_thread.is_alive():
                    self.logger.warning("⚠️ Поток движка не завершился корректно")
                else:
                    self.logger.info("✅ Поток движка завершен")
            
            # Уничтожение GUI
            if self.gui:
                self.gui.destroy()
                self.logger.info("✅ GUI уничтожен")
            
            # Экспорт текущей конфигурации
            self.save_config(self.config)
            self.logger.info("✅ Конфигурация сохранена")
            
            # Экспорт результатов если есть
            if self.engine and self.engine.discovered_nodes:
                results_file = f"rapidrecon_results_{int(time.time())}.json"
                self.engine.export_results(results_file)
                self.logger.info(f"💾 Результаты экспортированы в: {results_file}")
            
            self.logger.info("🎉 RapidRecon завершил работу")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка при завершении работы: {e}")
        
        finally:
            # Принудительное завершение при необходимости
            if threading.active_count() > 1:
                self.logger.warning("⚠️ Принудительное завершение работы")
                os._exit(1)
    
    def show_error_message(self, message: str):
        """Показать сообщение об ошибке (для использования когда GUI не доступен)"""
        print(f"❌ Ошибка: {message}")
        # В будущем можно добавить диалоговое окно с ошибкой
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получение статуса приложения
        
        Returns:
            Dict с информацией о статусе
        """
        engine_stats = self.engine.get_statistics() if self.engine else {}
        module_stats = {
            'available_modules': self.module_manager.get_available_modules_count() if self.module_manager else 0,
            'loaded_modules': self.module_manager.get_loaded_modules_count() if self.module_manager else 0,
            'builtin_modules': len(self.config['modules'].get('builtin_modules', []))
        }
        
        return {
            'is_running': self.is_running,
            'engine_status': engine_stats,
            'modules_status': module_stats,
            'threads_active': threading.active_count(),
            'uptime': getattr(self, 'start_time', 0),
            'last_update': self.last_update_time
        }
    
    def add_scan_target(self, target: str):
        """
        Добавление цели для сканирования
        
        Args:
            target: Цель для сканирования (домен, IP, диапазон)
        """
        if self.engine:
            self.engine.add_initial_target(target)
            self.logger.info(f"🎯 Добавлена цель для сканирования: {target}")
        else:
            self.logger.error("❌ Движок не инициализирован")
    
    def set_update_interval(self, interval: float):
        """
        Установка интервала обновления GUI
        
        Args:
            interval: Интервал в секундах
        """
        self.update_interval = max(0.1, interval)  # Минимальный интервал 0.1 секунды
        self.logger.info(f"🔄 Установлен интервал обновления GUI: {interval}с")


def main():
    """
    Точка входа в приложение
    """
    # Установка времени начала работы
    start_time = time.time()
    
    # Создание и запуск приложения
    app = RapidRecon()
    app.start_time = start_time
    
    try:
        app.run()
    except Exception as e:
        logging.getLogger('RapidRecon').error(f"💥 Необработанная ошибка: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
