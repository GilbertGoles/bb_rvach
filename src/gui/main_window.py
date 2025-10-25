"""
Главное окно RapidRecon на Dear PyGui
"""
import dearpygui.dearpygui as dpg
from typing import Callable, Dict, Any, List, Optional
import asyncio
import threading
import time
import json
from datetime import datetime

class GraphView:
    """Компонент для визуализации графа обнаруженных узлов"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = {}
        self.node_counter = 0
        self.setup_graph_theme()
    
    def setup_graph_theme(self):
        """Настройка темы для графа"""
        with dpg.theme(tag="graph_theme"):
            with dpg.theme_component(dpg.mvNode):
                dpg.add_theme_color(dpg.mvNodeCol_TitleBar, (70, 70, 100))
                dpg.add_theme_color(dpg.mvNodeCol_TitleBarHovered, (90, 90, 120))
                dpg.add_theme_color(dpg.mvNodeCol_TitleBarSelected, (110, 110, 140))
            
            with dpg.theme_component(dpg.mvNodeAttribute):
                dpg.add_theme_color(dpg.mvNodeCol_Attr, (60, 60, 80))
    
    def setup_graph_tab(self):
        """Настройка вкладки графа"""
        with dpg.tab(label="🌐 Граф сети", tag="graph_tab"):
            with dpg.group(horizontal=True):
                # Панель управления графом
                with dpg.child_window(width=200):
                    dpg.add_text("Управление графом:")
                    dpg.add_button(label="Обновить граф", callback=self.update_graph)
                    dpg.add_button(label="Очистить граф", callback=self.clear_graph)
                    dpg.add_button(label="Экспорт графа", callback=self.export_graph)
                    dpg.add_separator()
                    dpg.add_text("Настройки отображения:")
                    dpg.add_checkbox(label="Показывать типы", default_value=True, tag="show_types")
                    dpg.add_checkbox(label="Группировать по типу", default_value=False, tag="group_by_type")
                    dpg.add_slider_float(label="Масштаб", default_value=1.0, min_value=0.1, max_value=2.0, tag="graph_scale")
                
                # Область графа
                with dpg.child_window(tag="graph_window"):
                    with dpg.node_editor(
                        tag="node_editor",
                        minimap=True,
                        minimap_location=dpg.mvNodeMiniMap_Location_BottomRight
                    ):
                        pass  # Узлы будут добавляться динамически
    
    def add_node(self, node_data: Dict[str, Any]) -> int:
        """Добавить узел в граф"""
        node_id = self.node_counter
        self.node_counter += 1
        
        # Определяем цвет узла по типу
        node_colors = {
            'initial_target': (100, 200, 100),
            'subdomain': (100, 150, 200),
            'ip_address': (200, 150, 100),
            'active_host': (200, 100, 100),
            'open_ports': (150, 100, 200),
            'service': (100, 200, 200),
            'vulnerability': (200, 100, 150)
        }
        
        color = node_colors.get(node_data.get('type', 'custom'), (150, 150, 150))
        
        with dpg.node(
            parent="node_editor",
            label=f"{node_data.get('type', 'node')}",
            tag=f"node_{node_id}",
            pos=[100 + (node_id % 5) * 200, 100 + (node_id // 5) * 150]
        ):
            # Заголовок узла
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_text(f"Данные: {node_data.get('data', 'N/A')}")
            
            # Дополнительная информация
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                if 'depth' in node_data:
                    dpg.add_text(f"Глубина: {node_data['depth']}")
                if 'module' in node_data:
                    dpg.add_text(f"Модуль: {node_data['module']}")
            
            # Входной порт
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input, tag=f"in_{node_id}"):
                dpg.add_text("Вход")
            
            # Выходной порт
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output, tag=f"out_{node_id}"):
                dpg.add_text("Выход")
        
        # Применяем тему
        dpg.bind_item_theme(f"node_{node_id}", "graph_theme")
        
        self.nodes[node_id] = {
            'data': node_data,
            'dpg_id': f"node_{node_id}"
        }
        
        return node_id
    
    def add_edge(self, source_node_id: int, target_node_id: int):
        """Добавить связь между узлами"""
        if source_node_id in self.nodes and target_node_id in self.nodes:
            edge_id = f"edge_{source_node_id}_{target_node_id}"
            dpg.add_node_link(
                f"out_{source_node_id}",
                f"in_{target_node_id}",
                parent="node_editor",
                tag=edge_id
            )
            self.edges[edge_id] = (source_node_id, target_node_id)
    
    def clear_graph(self):
        """Очистить граф"""
        dpg.delete_item("node_editor", children_only=True)
        self.nodes.clear()
        self.edges.clear()
        self.node_counter = 0
    
    def update_graph(self):
        """Обновить отображение графа"""
        # В будущем можно добавить автоматическую компоновку
        pass
    
    def export_graph(self):
        """Экспорт графа в файл"""
        graph_data = {
            'nodes': [
                {**node['data'], 'graph_id': node_id}
                for node_id, node in self.nodes.items()
            ],
            'edges': list(self.edges.values())
        }
        
        filename = f"rapidrecon_graph_{int(time.time())}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        
        return filename

class MainWindow:
    """
    Главный интерфейс RapidRecon с расширенным функционалом
    """
    
    def __init__(self, engine, module_manager):
        self.engine = engine
        self.module_manager = module_manager
        self.graph_view = GraphView()
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
                dpg.add_menu_item(label="Экспорт графа", callback=self.export_graph)
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
            
            with dpg.menu(label="Вид"):
                dpg.add_menu_item(label="Обновить граф", callback=self.update_graph_from_engine)
                dpg.add_menu_item(label="Очистить граф", callback=self.graph_view.clear_graph)
            
            with dpg.menu(label="Справка"):
                dpg.add_menu_item(label="О программе", callback=self.show_about)
        
        with dpg.window(tag="Primary Window", label="RapidRecon - Инструмент разведки"):
            # Панель вкладок
            with dpg.tab_bar(tag="main_tab_bar"):
                # Вкладка сканирования
                self.setup_scan_tab()
                
                # Вкладка графа
                self.graph_view.setup_graph_tab()
                
                # Вкладка результатов
                self.setup_results_tab()
                
                # Вкладка модулей
                self.setup_modules_tab()
    
    def setup_scan_tab(self):
        """Вкладка управления сканированием"""
        with dpg.tab(label="🎯 Сканирование"):
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
            
            # Лог сканирования
            dpg.add_text("Лог сканирования:")
            dpg.add_input_text(
                tag="scan_log", 
                multiline=True, 
                height=200,
                readonly=True,
                width=-1
            )
    
    def setup_results_tab(self):
        """Вкладка детальных результатов"""
        with dpg.tab(label="📊 Результаты"):
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
                    dpg.add_input_text(
                        tag="detailed_results",
                        multiline=True,
                        height=300,
                        readonly=True,
                        width=-1
                    )
            
            # Статистика
            with dpg.collapsing_header(label="📈 Статистика"):
                with dpg.group(horizontal=True):
                    with dpg.child_window(width=300):
                        dpg.add_text("Общая статистика:")
                        dpg.add_text("Целей: 0", tag="stats_targets")
                        dpg.add_text("Найдено узлов: 0", tag="stats_nodes")
                        dpg.add_text("Завершено сканирований: 0", tag="stats_scans")
                        dpg.add_text("Активных модулей: 0", tag="stats_modules")
                        dpg.add_separator()
                        dpg.add_text("Время работы: 00:00:00", tag="stats_uptime")
    
    def setup_modules_tab(self):
        """Настройка вкладки управления модулями"""
        with dpg.tab(label="🔧 Модули"):
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
            self.add_to_log("❌ Ошибка: Введите цель для сканирования")
            return
        
        self.is_scanning = True
        self.update_ui_state()
        
        # Добавление цели в движок
        self.engine.add_initial_target(target)
        
        # Запуск асинхронного сканирования в отдельном потоке
        scan_thread = threading.Thread(target=self.run_scan_async)
        scan_thread.daemon = True
        scan_thread.start()
        
        self.add_to_log(f"🚀 Начато сканирование: {target}")
        dpg.set_value("current_status", "Сканирование...")
    
    def run_scan_async(self):
        """Запуск асинхронного сканирования"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.engine.process_queue())
            # Обновляем граф после завершения сканирования
            self.update_graph_from_engine()
        except Exception as e:
            self.add_to_log(f"❌ Ошибка сканирования: {e}")
        finally:
            loop.close()
            self.is_scanning = False
            self.update_ui_state()
            dpg.set_value("current_status", "Завершено")
            self.add_to_log("✅ Сканирование завершено")
    
    def stop_scan(self):
        """Остановка сканирования"""
        self.engine.stop_engine()
        self.is_scanning = False
        self.update_ui_state()
        dpg.set_value("current_status", "Остановлено")
        self.add_to_log("⏹️ Сканирование остановлено пользователем")
    
    def clear_results(self):
        """Очистка результатов"""
        self.graph_view.clear_graph()
        dpg.set_value("detailed_results", "")
        dpg.set_value("scan_log", "")
        self.add_to_log("🧹 Результаты очищены")
        dpg.set_value("current_status", "Ожидание")
    
    def update_ui_state(self):
        """Обновление состояния UI элементов"""
        dpg.configure_item("scan_button", enabled=not self.is_scanning)
        dpg.configure_item("stop_button", enabled=self.is_scanning)
    
    def on_node_discovered(self, node):
        """Callback при обнаружении нового узла"""
        message = f"🔍 Обнаружен: {node.type.value} -> {node.data}"
        self.add_to_log(message)
        self.update_statistics()
    
    def on_scan_completed(self, task):
        """Callback при завершении сканирования"""
        message = f"✅ Завершено: {task.data}"
        self.add_to_log(message)
        self.update_statistics()
    
    def add_to_log(self, message: str):
        """Добавить сообщение в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        current_log = dpg.get_value("scan_log")
        new_log = log_entry + current_log  # Новые сообщения сверху
        
        dpg.set_value("scan_log", new_log)
    
    def update_graph_from_engine(self):
        """Обновить граф на основе данных движка"""
        self.graph_view.clear_graph()
        
        # Создаем маппинг данных для связей
        node_map = {}
        
        # Добавляем все узлы в граф
        for node in self.engine.discovered_nodes:
            node_id = self.graph_view.add_node({
                'type': node.type.value,
                'data': node.data,
                'depth': node.depth,
                'module': node.module,
                'ports': node.ports
            })
            node_map[node.node_id] = node_id
        
        # Создаем связи между узлами
        for node in self.engine.discovered_nodes:
            if node.source and node.source in node_map:
                source_id = node_map.get(node.source)
                target_id = node_map.get(node.node_id)
                if source_id is not None and target_id is not None:
                    self.graph_view.add_edge(source_id, target_id)
        
        self.graph_view.update_graph()
        self.update_detailed_results()
    
    def update_detailed_results(self):
        """Обновить детальную информацию"""
        results_text = "Обнаруженные узлы:\n\n"
        
        for node in self.engine.discovered_nodes:
            depth_indent = "  " * node.depth
            node_type = getattr(node.type, 'value', str(node.type))
            results_text += f"{depth_indent}• {node_type}: {node.data}\n"
            
            if node.ports:
                results_text += f"{depth_indent}  Порта: {node.ports}\n"
            
            if hasattr(node, 'metadata') and node.metadata:
                results_text += f"{depth_indent}  Метаданные: {node.metadata}\n"
        
        dpg.set_value("detailed_results", results_text)
    
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
        self.add_to_log("📋 Список модулей обновлен")
    
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
                self.add_to_log(f"✅ Модуль загружен: {selected_module}")
            else:
                self.add_to_log(f"❌ Ошибка загрузки модуля: {selected_module}")
    
    def unload_selected_module(self):
        """Выгрузка выбранного модуля"""
        selected_module = dpg.get_value("modules_list")
        if selected_module:
            # Здесь будет логика выгрузки модулей
            self.add_to_log(f"⚠️ Выгрузка модуля {selected_module} пока не реализована")
    
    def export_results(self):
        """Экспорт результатов"""
        filename = f"rapidrecon_scan_{int(time.time())}.json"
        self.engine.export_results(filename)
        self.add_to_log(f"💾 Результаты экспортированы в: {filename}")
    
    def export_graph(self):
        """Экспорт графа"""
        filename = self.graph_view.export_graph()
        self.add_to_log(f"🌐 Граф экспортирован в: {filename}")
    
    def update_rate_limit(self):
        """Обновление ограничения скорости"""
        rate = dpg.get_value("rate_limit")
        self.engine.rate_limit = rate
        self.add_to_log(f"⚡ Установлена скорость: {rate} пакетов/секунду")
    
    def update_speed_profile(self):
        """Обновление профиля скорости"""
        profile = dpg.get_value("speed_profile")
        self.add_to_log(f"🎛️ Установлен профиль: {profile}")
    
    def update_max_depth(self):
        """Обновление максимальной глубины"""
        depth = dpg.get_value("max_depth")
        self.engine.max_depth = depth
        self.add_to_log(f"📏 Установлена глубина: {depth}")
    
    def show_settings(self):
        """Показать настройки"""
        self.add_to_log("⚙️ Открыты настройки")
    
    def show_module_manager(self):
        """Показать менеджер модулей"""
        self.add_to_log("🔧 Открыт менеджер модулей")
    
    def show_about(self):
        """Показать информацию о программе"""
        about_text = """
RapidRecon v1.0.0

Мощный инструмент для автоматизированной 
разведки и сканирования сетевой инфраструктуры.

Разработано с ❤️ для сообщества безопасности.
"""
        self.add_to_log("ℹ️ " + about_text.replace('\n', ' '))
    
    def quick_scan(self):
        """Быстрое сканирование"""
        dpg.set_value("speed_profile", "Нормальный")
        dpg.set_value("max_depth", 2)
        self.add_to_log("🚀 Настроено быстрое сканирование")
    
    def deep_scan(self):
        """Глубокое сканирование"""
        dpg.set_value("speed_profile", "Агрессивный")
        dpg.set_value("max_depth", 5)
        self.add_to_log("🔍 Настроено глубокое сканирование")
    
    def custom_scan(self):
        """Кастомное сканирование"""
        self.add_to_log("🎛️ Открыты настройки кастомного сканирования")
    
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
    from core.engine import PropagationEngine
    from core.module_manager import ModuleManager
    
    engine = PropagationEngine()
    module_manager = ModuleManager()
    
    app = MainWindow(engine, module_manager)
    app.show()
