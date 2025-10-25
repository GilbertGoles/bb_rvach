"""
Главное окно RapidRecon на Dear PyGui
"""
import dearpygui.dearpygui as dpg
from typing import Callable, Dict, Any, List
import asyncio
import threading
import time
import json
from datetime import datetime

class MainWindow:
    """
    Главный интерфейс RapidRecon с расширенным функционалом
    """
    
    def __init__(self, engine, module_manager):
        self.engine = engine
        self.module_manager = module_manager
        self.is_scanning = False
        self.scan_stats = {}
        self.real_time_data = []
        self.setup_gui()
        
        # Настройка темы
        self.setup_theme()
        
        # Привязка callback для обновления UI
        self.setup_callbacks()
    
    def setup_gui(self):
        """Настройка основного интерфейса"""
        dpg.create_context()
        
        # Создание меню
        with dpg.viewport_menu_bar():
            with dpg.menu(label="Файл"):
                dpg.add_menu_item(label="Экспорт результатов", callback=self.export_results)
                dpg.add_menu_item(label="Настройки", callback=self.show_settings)
                dpg.add_separator()
                dpg.add_menu_item(label="Выход", callback=self.exit_app)
            
            with dpg.menu(label="Сканирование"):
                dpg.add_menu_item(label="Быстрое сканирование", callback=self.quick_scan)
                dpg.add_menu_item(label="Глубокое сканирование", callback=self.deep_scan)
                dpg.add_menu_item(label="Кастомное сканирование", callback=self.custom_scan)
            
            with dpg.menu(label="Модули"):
                dpg.add_menu_item(label="Управление модулями", callback=self.show_module_manager)
                dpg.add_menu_item(label="Обновить модули", callback=self.refresh_modules)
            
            with dpg.menu(label="Справка"):
                dpg.add_menu_item(label="О программе", callback=self.show_about)
        
        with dpg.window(tag="Primary Window", label="RapidRecon - Инструмент разведки"):
            # Основная панель управления
            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    tag="target_input", 
                    hint="Введите домен, IP или диапазон",
                    width=300
                )
                dpg.add_button(
                    label="▶️ Сканировать", 
                    callback=self.start_scan,
                    tag="scan_button"
                )
                dpg.add_button(
                    label="⏹️ Стоп", 
                    callback=self.stop_scan,
                    tag="stop_button"
                )
                dpg.add_button(
                    label="🧹 Очистить", 
                    callback=self.clear_results
                )
                dpg.add_spacer(width=20)
                dpg.add_text("Статус:", tag="status_text")
                dpg.add_text("Ожидание", tag="current_status")
            
            # Панель быстрых настроек
            with dpg.collapsing_header(label="⚙️ Быстрые настройки", default_open=True):
                with dpg.group(horizontal=True):
                    with dpg.child_window(width=300):
                        dpg.add_text("Скорость сканирования:")
                        dpg.add_slider_int(
                            label="Пакетов/секунду",
                            default_value=50, min_value=1, max_value=1000,
                            tag="rate_limit",
                            callback=self.update_rate_limit
                        )
                        dpg.add_combo(
                            label="Профиль скорости",
                            items=["Стелс", "Нормальный", "Агрессивный", "Безумный"],
                            default_value="Нормальный",
                            tag="speed_profile",
                            callback=self.update_speed_profile
                        )
                    
                    with dpg.child_window(width=300):
                        dpg.add_text("Глубина сканирования:")
                        dpg.add_slider_int(
                            label="Макс. глубина",
                            default_value=3, min_value=1, max_value=10,
                            tag="max_depth",
                            callback=self.update_max_depth
                        )
                        dpg.add_checkbox(
                            label="Рекурсивное сканирование",
                            default_value=True,
                            tag="recursive_scan"
                        )
                    
                    with dpg.child_window(width=300):
                        dpg.add_text("Модули:")
                        dpg.add_combo(
                            label="Тип сканирования",
                            items=["Авто", "Только поддомены", "Порты и сервисы", "Уязвимости"],
                            default_value="Авто",
                            tag="scan_type"
                        )
                        dpg.add_checkbox(
                            label="Пассивное сканирование",
                            default_value=False,
                            tag="passive_scan"
                        )
            
            # Вкладки для различных типов информации
            with dpg.tab_bar(tag="main_tab_bar"):
                # Вкладка результатов в реальном времени
                with dpg.tab(label="🔍 Результаты"):
                    with dpg.group(horizontal=True):
                        # Дерево обнаруженных узлов
                        with dpg.child_window(width=400, tag="nodes_tree_window"):
                            dpg.add_text("Обнаруженные узлы:")
                            dpg.add_tree_node(
                                label="Корневые цели",
                                tag="root_nodes",
                                default_open=True
                            )
                        
                        # Детальная информация
                        with dpg.child_window(tag="details_window"):
                            dpg.add_text("Детальная информация:", tag="details_title")
                            dpg.add_text("Выберите узел для просмотра деталей", tag="details_content")
                
                # Вкладка статистики
                with dpg.tab(label="📊 Статистика"):
                    with dpg.group(horizontal=True):
                        with dpg.child_window(width=300):
                            dpg.add_text("Общая статистика:")
                            dpg.add_text("Целей: 0", tag="stats_targets")
                            dpg.add_text("Найдено узлов: 0", tag="stats_nodes")
                            dpg.add_text("Завершено сканирований: 0", tag="stats_scans")
                            dpg.add_text("Активных модулей: 0", tag="stats_modules")
                            dpg.add_separator()
                            dpg.add_text("Время работы: 00:00:00", tag="stats_uptime")
                        
                        with dpg.child_window():
                            dpg.add_text("Графики (заглушка):")
                            dpg.add_text("Здесь будут графики активности")
                
                # Вкладка логов
                with dpg.tab(label="📝 Логи"):
                    dpg.add_input_text(
                        tag="log_output",
                        multiline=True,
                        readonly=True,
                        height=400,
                        width=-1
                    )
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Очистить логи", callback=self.clear_logs)
                        dpg.add_button(label="Экспорт логов", callback=self.export_logs)
                        dpg.add_checkbox(label="Автопрокрутка", default_value=True, tag="auto_scroll")
                
                # Вкладка модулей
                with dpg.tab(label="🔧 Модули"):
                    self.setup_modules_tab()
    
    def setup_modules_tab(self):
        """Настройка вкладки управления модулями"""
        with dpg.group(horizontal=True):
            # Список модулей
            with dpg.child_window(width=400):
                dpg.add_text("Доступные модули:")
                dpg.add_listbox(
                    items=[],
                    tag="modules_list",
                    num_items=15,
                    callback=self.on_module_select
                )
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Загрузить", callback=self.load_selected_module)
                    dpg.add_button(label="Выгрузить", callback=self.unload_selected_module)
                    dpg.add_button(label="Обновить", callback=self.refresh_modules_list)
            
            # Информация о модуле
            with dpg.child_window(tag="module_info_window"):
                dpg.add_text("Информация о модуле:", tag="module_info_title")
                dpg.add_text("Выберите модуль из списка", tag="module_info_content")
    
    def setup_theme(self):
        """Настройка темы оформления"""
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (40, 40, 40), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Button, (60, 60, 80), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (80, 80, 100), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (100, 100, 120), category=dpg.mvThemeCat_Core)
        
        dpg.bind_theme(global_theme)
    
    def setup_callbacks(self):
        """Настройка callback функций"""
        # Регистрация callback для обновления UI в реальном времени
        if hasattr(self.engine, 'callbacks'):
            self.engine.callbacks['node_discovered'] = self.on_node_discovered
            self.engine.callbacks['scan_completed'] = self.on_scan_completed
    
    def start_scan(self):
        """Запуск сканирования"""
        target = dpg.get_value("target_input")
        if not target:
            self.log_message("❌ Ошибка: Введите цель для сканирования")
            return
        
        self.is_scanning = True
        self.update_ui_state()
        
        # Добавление цели в движок
        self.engine.add_initial_target(target)
        
        # Запуск асинхронного сканирования в отдельном потоке
        scan_thread = threading.Thread(target=self.run_scan_async)
        scan_thread.daemon = True
        scan_thread.start()
        
        self.log_message(f"🚀 Начато сканирование: {target}")
        dpg.set_value("current_status", "Сканирование...")
    
    def run_scan_async(self):
        """Запуск асинхронного сканирования"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.engine.process_queue())
        except Exception as e:
            self.log_message(f"❌ Ошибка сканирования: {e}")
        finally:
            loop.close()
            self.is_scanning = False
            self.update_ui_state()
            dpg.set_value("current_status", "Завершено")
            self.log_message("✅ Сканирование завершено")
    
    def stop_scan(self):
        """Остановка сканирования"""
        self.engine.stop_engine()
        self.is_scanning = False
        self.update_ui_state()
        dpg.set_value("current_status", "Остановлено")
        self.log_message("⏹️ Сканирование остановлено пользователем")
    
    def clear_results(self):
        """Очистка результатов"""
        # Здесь будет логика очистки результатов
        self.log_message("🧹 Результаты очищены")
        dpg.set_value("current_status", "Ожидание")
    
    def update_ui_state(self):
        """Обновление состояния UI элементов"""
        dpg.configure_item("scan_button", enabled=not self.is_scanning)
        dpg.configure_item("stop_button", enabled=self.is_scanning)
    
    def on_node_discovered(self, node):
        """Callback при обнаружении нового узла"""
        message = f"🔍 Обнаружен: {node.type.value} -> {node.data}"
        self.log_message(message)
        self.update_nodes_tree(node)
    
    def on_scan_completed(self, task):
        """Callback при завершении сканирования"""
        message = f"✅ Завершено: {task.data}"
        self.log_message(message)
        self.update_statistics()
    
    def log_message(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        current_log = dpg.get_value("log_output")
        new_log = current_log + log_entry
        
        dpg.set_value("log_output", new_log)
        
        # Автопрокрутка
        if dpg.get_value("auto_scroll"):
            # Прокрутка вниз (будет реализовано в будущих версиях DPG)
            pass
    
    def update_nodes_tree(self, node):
        """Обновление дерева узлов"""
        # Здесь будет логика обновления дерева обнаруженных узлов
        pass
    
    def update_statistics(self):
        """Обновление статистики"""
        stats = self.engine.get_statistics()
        dpg.set_value("stats_targets", f"Целей: {stats.get('total_scans', 0)}")
        dpg.set_value("stats_nodes", f"Найдено узлов: {stats.get('nodes_discovered', 0)}")
        dpg.set_value("stats_scans", f"Завершено сканирований: {stats.get('successful_scans', 0)}")
        dpg.set_value("stats_modules", f"Активных модулей: {stats.get('active_modules', 0)}")
    
    def refresh_modules_list(self):
        """Обновление списка модулей"""
        modules = self.module_manager.list_modules()
        module_names = list(modules.keys())
        dpg.configure_item("modules_list", items=module_names)
        self.log_message("📋 Список модулей обновлен")
    
    def on_module_select(self, sender, app_data):
        """Обработка выбора модуля"""
        selected_module = app_data
        module_info = self.module_manager.get_module_info(selected_module)
        
        if module_info:
            info_text = f"""
Название: {module_info.name}
Версия: {module_info.version}
Автор: {module_info.author}
Тип: {module_info.module_type.value}
Описание: {module_info.description}

Входные данные: {', '.join(module_info.input_types)}
Выходные данные: {', '.join(module_info.output_types)}
Триггеры: {', '.join(module_info.triggers)}
Статус: {'✅ Включен' if module_info.enabled else '❌ Выключен'}
"""
            dpg.set_value("module_info_content", info_text)
    
    def load_selected_module(self):
        """Загрузка выбранного модуля"""
        selected_module = dpg.get_value("modules_list")
        if selected_module:
            success = self.module_manager.load_module(selected_module)
            if success:
                self.log_message(f"✅ Модуль загружен: {selected_module}")
            else:
                self.log_message(f"❌ Ошибка загрузки модуля: {selected_module}")
    
    def unload_selected_module(self):
        """Выгрузка выбранного модуля"""
        # Здесь будет логика выгрузки модулей
        self.log_message("⚠️ Выгрузка модулей пока не реализована")
    
    def export_results(self):
        """Экспорт результатов"""
        filename = f"rapidrecon_scan_{int(time.time())}.json"
        self.engine.export_results(filename)
        self.log_message(f"💾 Результаты экспортированы в: {filename}")
    
    def export_logs(self):
        """Экспорт логов"""
        logs = dpg.get_value("log_output")
        filename = f"rapidrecon_logs_{int(time.time())}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(logs)
        self.log_message(f"📄 Логи экспортированы в: {filename}")
    
    def clear_logs(self):
        """Очистка логов"""
        dpg.set_value("log_output", "")
        self.log_message("🧹 Логи очищены")
    
    def update_rate_limit(self):
        """Обновление ограничения скорости"""
        rate = dpg.get_value("rate_limit")
        self.log_message(f"⚡ Установлена скорость: {rate} пакетов/секунду")
    
    def update_speed_profile(self):
        """Обновление профиля скорости"""
        profile = dpg.get_value("speed_profile")
        self.log_message(f"🎛️ Установлен профиль: {profile}")
    
    def update_max_depth(self):
        """Обновление максимальной глубины"""
        depth = dpg.get_value("max_depth")
        self.engine.max_depth = depth
        self.log_message(f"📏 Установлена глубина: {depth}")
    
    def show_settings(self):
        """Показать настройки"""
        self.log_message("⚙️ Открыты настройки")
    
    def show_module_manager(self):
        """Показать менеджер модулей"""
        self.log_message("🔧 Открыт менеджер модулей")
    
    def show_about(self):
        """Показать информацию о программе"""
        about_text = """
RapidRecon v1.0.0

Мощный инструмент для автоматизированной 
разведки и сканирования сетевой инфраструктуры.

Разработано с ❤️ для сообщества безопасности.
"""
        self.log_message("ℹ️ " + about_text.replace('\n', ' '))
    
    def quick_scan(self):
        """Быстрое сканирование"""
        dpg.set_value("speed_profile", "Нормальный")
        dpg.set_value("max_depth", 2)
        self.log_message("🚀 Настроено быстрое сканирование")
    
    def deep_scan(self):
        """Глубокое сканирование"""
        dpg.set_value("speed_profile", "Агрессивный")
        dpg.set_value("max_depth", 5)
        self.log_message("🔍 Настроено глубокое сканирование")
    
    def custom_scan(self):
        """Кастомное сканирование"""
        self.log_message("🎛️ Открыты настройки кастомного сканирования")
    
    def exit_app(self):
        """Выход из приложения"""
        if self.is_scanning:
            self.stop_scan()
        self.destroy()
    
    def show(self):
        """Показать окно"""
        dpg.create_viewport(
            title='RapidRecon v1.0.0', 
            width=1400, 
            height=900,
            min_width=1000,
            min_height=700
        )
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Primary Window", True)
        
        # Инициализация данных
        self.refresh_modules_list()
        self.update_ui_state()
        
        dpg.start_dearpygui()
    
    def destroy(self):
        """Очистка"""
        dpg.destroy_context()

# Пример использования
if __name__ == "__main__":
    # Демонстрация работы интерфейса
    from propagation_engine import PropagationEngine
    from module_manager import ModuleManager
    
    engine = PropagationEngine()
    module_manager = ModuleManager()
    
    app = MainWindow(engine, module_manager)
    app.show()
