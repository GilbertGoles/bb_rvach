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
import dearpygui.dearpygui as dpg

# Добавление корневой директории в путь для импортов
sys.path.insert(0, str(Path(__file__).parent))

from core.engine import PropagationEngine
from core.module_manager import ModuleManager
from core.config import ConfigManager
from gui.main_window import MainWindow

# Импорт модулей (КЛАССОВ, а не экземпляров)
from modules.ping_scanner.module import PingScanner
from modules.port_scanner.module import PortScanner
from modules.service_detector.module import ServiceDetector
from modules.subdomain_scanner.module import SubdomainScanner
from modules.vulnerability_scanner.module import VulnerabilityScanner
from modules.exploitation.module import Exploitation

class RapidRecon:
    """
    Основной класс приложения RapidRecon
    Координирует работу движка, менеджера модулей и интерфейса
    """
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config_manager = ConfigManager(config_file)
        self.config = self.config_manager.load_config()
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
        self.update_interval = 0.5
        
        # Инициализация компонентов
        self.initialize_components()
        
        # Настройка обработчиков сигналов
        self.setup_signal_handlers()
    
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
        
        # Очищаем существующие обработчики
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            
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
            
            # Инициализация движка БЕЗ параметров конфигурации
            self.engine = PropagationEngine(update_callback=self.on_engine_update)
            
            # Загрузка и регистрация модулей
            self.load_and_register_modules()
            
            # Инициализация GUI БЕЗ config_manager
            self.gui = MainWindow(self.engine, self.module_manager)
            
            # Настройка интервала обновления из конфигурации
            self.update_interval = self.config['app'].get('update_interval', 0.5)
            
            self.logger.info("✅ Все компоненты инициализированы")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации компонентов: {e}")
            raise
    
    def load_and_register_modules(self):
        """Загрузка и регистрация модулей в движке"""
        try:
            # Регистрируем модули в движке (передаем КЛАССЫ)
            module_classes = {
                'ping_scanner': PingScanner,
                'port_scanner': PortScanner,
                'service_detector': ServiceDetector,
                'subdomain_scanner': SubdomainScanner,
                'vulnerability_scanner': VulnerabilityScanner,
                'exploitation': Exploitation
            }
            
            registered_count = 0
            
            for name, module_class in module_classes.items():
                try:
                    self.engine.register_module(name, module_class)
                    registered_count += 1
                    self.logger.info(f"✅ Модуль зарегистрирован: {name}")
                except Exception as e:
                    self.logger.error(f"❌ Ошибка регистрации модуля {name}: {e}")
            
            self.logger.info(f"📋 Зарегистрировано модулей: {registered_count}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки модулей: {e}")
    
    def on_engine_update(self, event_type: str, data: Any = None):
        """
        Callback при обновлении движка для синхронизации с GUI
        """
        try:
            current_time = time.time()
            
            # Ограничиваем частоту обновлений чтобы не перегружать GUI
            if current_time - self.last_update_time < self.update_interval:
                return
                
            self.last_update_time = current_time
            
            # Передаем событие в GUI
            if self.gui:
                self.gui.handle_engine_event(event_type, data)
            
            # Логируем важные события
            if event_type in ['vulnerability_found', 'exploitation_success']:
                self.logger.info(f"Engine event: {event_type} - {data}")
                
        except Exception as e:
            self.logger.warning(f"Ошибка в engine callback: {e}")
    
    def setup_signal_handlers(self):
        """Настройка обработчиков сигналов для graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"📶 Получен сигнал {signum}. Завершение работы...")
            self.shutdown()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start_engine_async(self):
        """Запуск асинхронного движка в отдельном потоке"""
        try:
            self.logger.info("🔧 Запуск асинхронного движка...")
            
            # Создание нового event loop для потока
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            
            # Постоянная обработка задач
            while self.is_running:
                if self.engine and not self.engine.pending_scans.empty():
                    try:
                        self.event_loop.run_until_complete(self.engine.process_queue())
                    except Exception as e:
                        self.logger.error(f"Ошибка обработки очереди: {e}")
                else:
                    # Короткая пауза если нет задач
                    time.sleep(0.1)
                        
        except Exception as e:
            self.logger.error(f"❌ Ошибка в асинхронном движке: {e}")
        finally:
            if self.event_loop:
                self.event_loop.close()
    
    def run_gui(self):
        """Запуск GUI в главном потоке"""
        try:
            self.logger.info("🎨 Запуск графического интерфейса...")
            if self.gui:
                self.gui.run()
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска GUI: {e}")
            # Показываем сообщение об ошибке в консоли
            print(f"❌ Ошибка запуска GUI: {e}")
            print("💡 Попробуйте установить зависимости: pip install dearpygui")
            raise
    
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
            
            # Информация о загруженных модулях
            builtin_modules = self.config['modules'].get('builtin_modules', [])
            self.logger.info(f"📦 Встроенные модули: {', '.join(builtin_modules)}")
            
            # Запуск асинхронного движка в отдельном потоке
            self.engine_thread = threading.Thread(
                target=self.start_engine_async,
                daemon=True,
                name="EngineThread"
            )
            self.engine_thread.start()
            
            # Запуск GUI в ГЛАВНОМ потоке (блокирующий вызов)
            self.run_gui()
            
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
                self.engine_thread.join(timeout=3.0)
                if self.engine_thread.is_alive():
                    self.logger.warning("⚠️ Поток движка не завершился корректно")
                else:
                    self.logger.info("✅ Поток движка завершен")
            
            # Уничтожение GUI
            if self.gui:
                try:
                    self.gui.destroy()
                    self.logger.info("✅ GUI уничтожен")
                except Exception as e:
                    self.logger.warning(f"⚠️ Ошибка уничтожения GUI: {e}")
            
            # Сохранение конфигурации
            self.config_manager.save_config()
            self.config_manager.save_profiles()
            self.config_manager.save_module_configs()
            self.logger.info("✅ Все конфигурации сохранены")
            
            # Экспорт результатов если есть
            if self.engine and self.engine.discovered_nodes:
                results_file = f"rapidrecon_results_{int(time.time())}.json"
                self.engine.export_results(results_file)
                self.logger.info(f"💾 Результаты экспортированы в: {results_file}")
            
            # Отчет о найденных уязвимостях и успешных атаках
            if hasattr(self.engine, 'stats'):
                vuln_count = self.engine.stats.get('vulnerabilities_found', 0)
                exploit_count = self.engine.stats.get('exploits_successful', 0)
                
                if vuln_count > 0:
                    self.logger.warning(f"🔴 Обнаружено уязвимостей: {vuln_count}")
                if exploit_count > 0:
                    self.logger.critical(f"💥 Успешных атак: {exploit_count}")
            
            self.logger.info("🎉 RapidRecon завершил работу")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка при завершении работы: {e}")
    
    def show_error_message(self, message: str):
        """Показать сообщение об ошибке"""
        print(f"❌ Ошибка: {message}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получение статуса приложения
        
        Returns:
            Dict с информацией о статусе
        """
        engine_stats = self.engine.get_statistics() if self.engine else {}
        
        return {
            'is_running': self.is_running,
            'engine_status': engine_stats,
            'threads_active': threading.active_count(),
            'uptime': getattr(self, 'start_time', 0),
            'last_update': self.last_update_time,
            'active_profile': getattr(self.config_manager, 'active_profile', 'normal'),
            'vulnerabilities_found': engine_stats.get('vulnerabilities_found', 0),
            'exploits_successful': engine_stats.get('exploits_successful', 0)
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
        self.update_interval = max(0.1, interval)
        self.logger.info(f"🔄 Установлен интервал обновления GUI: {interval}с")
    
    def reload_config(self):
        """
        Перезагрузка конфигурации
        """
        self.config = self.config_manager.load_config()
        self.logger.info("🔄 Конфигурация перезагружена")
        
        # Применяем новые настройки к компонентам
        if self.engine:
            engine_config = self.config['engine']
            self.engine.max_depth = engine_config.get('max_depth', 5)
            self.engine.rate_limit = engine_config.get('rate_limit', 50)
            self.engine.max_concurrent_tasks = engine_config.get('max_concurrent_tasks', 5)
        
        self.update_interval = self.config['app'].get('update_interval', 0.5)


def main():
    """
    Точка входа в приложение
    """
    # Установка времени начала работы
    start_time = time.time()
    
    try:
        # Создание и запуск приложения
        app = RapidRecon()
        app.start_time = start_time
        app.run()
    except Exception as e:
        logging.getLogger('RapidRecon').error(f"💥 Необработанная ошибка: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
