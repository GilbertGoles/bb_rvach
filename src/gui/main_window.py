"""
Главное окно RapidRecon в стиле Obsidian - ГИБРИДНАЯ РАБОЧАЯ ВЕРСИЯ
"""
import dearpygui.dearpygui as dpg
from typing import Dict, Any, List, Optional, Tuple
import time
import json
from datetime import datetime
import logging
import math
import random
import traceback
import sys
import os

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class ObsidianTheme:
    """Тема в стиле Obsidian"""
    
    @staticmethod
    def setup_theme():
        """Настройка темы Obsidian"""
        
        with dpg.theme() as obsidian_theme:
            # Цветовая схема Obsidian
            colors = {
                'bg_primary': [18, 18, 24],
                'bg_secondary': [28, 28, 36],
                'bg_tertiary': [38, 38, 48],
                'accent_primary': [123, 97, 255],
                'accent_secondary': [86, 156, 214],
                'text_primary': [220, 220, 220],
                'text_secondary': [150, 150, 160],
                'text_muted': [100, 100, 110],
                'success': [72, 199, 116],
                'warning': [255, 179, 64],
                'error': [255, 92, 87],
                'border': [60, 60, 70]
            }
            
            # Основные компоненты
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, colors['bg_primary'])
                dpg.add_theme_color(dpg.mvThemeCol_Text, colors['text_primary'])
                dpg.add_theme_color(dpg.mvThemeCol_Border, colors['border'])
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
                dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 6)
            
            # Кнопки
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, colors['bg_tertiary'])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, colors['accent_primary'])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [103, 77, 235])
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 4)
            
            # Поля ввода
            with dpg.theme_component(dpg.mvInputText):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, colors['bg_secondary'])
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, colors['bg_tertiary'])
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, colors['bg_tertiary'])
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6)
            
            # Вкладки
            with dpg.theme_component(dpg.mvTabBar):
                dpg.add_theme_color(dpg.mvThemeCol_Tab, colors['bg_secondary'])
                dpg.add_theme_color(dpg.mvThemeCol_TabHovered, colors['accent_primary'])
                dpg.add_theme_color(dpg.mvThemeCol_TabActive, colors['accent_primary'])
                dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, colors['bg_secondary'])
                dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, colors['bg_tertiary'])
            
            # Заголовки
            with dpg.theme_component(dpg.mvCollapsingHeader):
                dpg.add_theme_color(dpg.mvThemeCol_Header, colors['bg_secondary'])
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, colors['accent_primary'])
                dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, colors['accent_primary'])
        
        return obsidian_theme

class DangerTheme:
    """Тема для опасных кнопок (красная)"""
    
    @staticmethod
    def setup_theme():
        with dpg.theme() as danger_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, [255, 60, 60, 200])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [255, 80, 80, 255])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [255, 40, 40, 255])
                dpg.add_theme_color(dpg.mvThemeCol_Text, [255, 255, 255])
        return danger_theme

class NetworkGraph:
    """Сетевой граф в стиле Obsidian - УПРОЩЕННАЯ РАБОЧАЯ ВЕРСИЯ"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.node_counter = 0
        self.layout_positions = {}
        
        # Цвета для разных типов узлов (как в NetworkVisualizer)
        self.colors = {
            'initial_target': [72, 199, 116, 200],    # Зеленый
            'subdomain': [86, 156, 214, 180],         # Синий
            'active_host': [255, 179, 64, 200],       # Оранжевый
            'open_ports': [123, 97, 255, 180],        # Фиолетовый
            'service': [158, 118, 255, 180],          # Лавандовый
            'vulnerability': [255, 92, 87, 220],      # Красный
            'exploitation': [255, 60, 60, 220],       # Ярко-красный
            'unknown': [128, 128, 128, 150]           # Серый
        }
        
        self.icons = {
            'initial_target': '🎯',
            'subdomain': '🌐',
            'active_host': '💻',
            'open_ports': '🔓',
            'service': '⚙️',
            'vulnerability': '🔴',
            'exploitation': '💥',
            'unknown': '•'
        }
    
    def add_node(self, node_data: Dict[str, Any]) -> int:
        """Добавить узел - УПРОЩЕННАЯ ВЕРСИЯ"""
        try:
            node_id = self.node_counter
            self.node_counter += 1
            
            node_type = node_data.get('type', 'unknown')
            label = self._get_node_label(node_data)
            position = self._calculate_position(node_id, node_type)
            
            self.nodes[node_id] = {
                'id': node_id,
                'label': label,
                'type': node_type,
                'data': node_data,
                'position': position,
                'color': self.colors.get(node_type, self.colors['unknown']),
                'icon': self.icons.get(node_type, self.icons['unknown']),
                'radius': self._get_radius(node_type)
            }
            
            return node_id
        except Exception as e:
            logging.error(f"Error adding node: {e}")
            return -1
    
    def _get_node_label(self, node_data: Dict[str, Any]) -> str:
        """Получить метку для узла"""
        data = node_data.get('data', 'Unknown')
        node_type = node_data.get('type', '')
        
        # Обрезаем длинные метки
        if len(str(data)) > 20:
            return str(data)[:17] + "..."
        return str(data)
    
    def _get_radius(self, node_type: str) -> int:
        """Получить радиус узла в зависимости от типа"""
        sizes = {
            'initial_target': 25,
            'active_host': 22,
            'exploitation': 23,
            'vulnerability': 19,
            'subdomain': 20,
            'open_ports': 20,
            'service': 18,
            'unknown': 20
        }
        return sizes.get(node_type, 20)
    
    def _calculate_position(self, node_id: int, node_type: str) -> List[float]:
        """Рассчитать позицию узла - УПРОЩЕННЫЙ АЛГОРИТМ"""
        center_x, center_y = 500, 350
        
        if not self.nodes:
            return [center_x, center_y]
        
        # Простое распределение по кругу
        angle = (node_id * 2 * math.pi / len(self.nodes))
        radius = 200 + (len(self.nodes) * 3)
        
        # Слегка смещаем разные типы
        type_offset = {
            'initial_target': (0, -50),
            'subdomain': (-30, -20),
            'active_host': (30, 0),
            'open_ports': (0, 30),
            'vulnerability': (40, 40)
        }
        
        offset_x, offset_y = type_offset.get(node_type, (0, 0))
        
        return [
            center_x + radius * math.cos(angle) + offset_x,
            center_y + radius * math.sin(angle) + offset_y
        ]
    
    def add_edge(self, source_id: int, target_id: int, edge_type: str = "normal"):
        """Добавить связь между узлами"""
        try:
            if source_id in self.nodes and target_id in self.nodes:
                edge_configs = {
                    "normal": {"color": [150, 150, 150, 100], "thickness": 2},
                    "dns": {"color": [86, 156, 214, 120], "thickness": 2},
                    "port": {"color": [123, 97, 255, 120], "thickness": 2},
                    "vulnerability": {"color": [255, 100, 100, 120], "thickness": 2}
                }
                
                config = edge_configs.get(edge_type, edge_configs["normal"])
                
                self.edges.append({
                    'source': source_id,
                    'target': target_id,
                    'type': edge_type,
                    'color': config['color'],
                    'thickness': config['thickness']
                })
        except Exception as e:
            logging.error(f"Error adding edge: {e}")
    
    def draw(self, width: int, height: int):
        """Отрисовать граф - ПРОСТАЯ РАБОЧАЯ ВЕРСИЯ"""
        try:
            # Фон
            dpg.draw_rectangle([0, 0], [width, height], 
                             fill=[25, 25, 32], parent="graph_canvas")
            
            # Сетка
            grid_size = 50
            for x in range(0, width, grid_size):
                dpg.draw_line([x, 0], [x, height], color=[40, 40, 50], 
                            thickness=1, parent="graph_canvas")
            for y in range(0, height, grid_size):
                dpg.draw_line([0, y], [width, y], color=[40, 40, 50], 
                            thickness=1, parent="graph_canvas")
            
            # Связи
            for edge in self.edges:
                source = self.nodes.get(edge['source'])
                target = self.nodes.get(edge['target'])
                if source and target:
                    dpg.draw_line(source['position'], target['position'],
                                color=edge['color'], thickness=edge['thickness'],
                                parent="graph_canvas")
            
            # Узлы
            for node_id, node in self.nodes.items():
                pos = node['position']
                
                # Круг узла
                dpg.draw_circle(pos, node['radius'], fill=node['color'],
                              color=[255, 255, 255, 100], thickness=2,
                              parent="graph_canvas")
                
                # Иконка
                dpg.draw_text([pos[0] - 4, pos[1] - 6], node['icon'],
                            color=[255, 255, 255], size=14, parent="graph_canvas")
                
                # Метка
                dpg.draw_text([pos[0] - len(node['label']) * 3, pos[1] + node['radius'] + 8],
                            node['label'], color=[200, 200, 200], size=11,
                            parent="graph_canvas")
                            
        except Exception as e:
            logging.error(f"Error drawing graph: {e}")
    
    def clear(self):
        """Очистить граф"""
        self.nodes.clear()
        self.edges.clear()
        self.node_counter = 0

class MainWindow:
    """
    Главный интерфейс RapidRecon - РАБОЧАЯ ВЕРСИЯ С ГРАФОМ
    """
    
    def __init__(self, engine, module_manager):
        self.engine = engine
        self.module_manager = module_manager
        self.graph = NetworkGraph()
        self.is_scanning = False
        self.logger = logging.getLogger('RapidRecon.GUI')
        
        # Хранилище данных
        self.all_nodes = {}  # node_id -> ScanNode
        self.graph_nodes = {}  # engine_node_id -> graph_node_id
        self.node_tree_data = {}  # Для дерева зависимостей
        
        # Инициализация GUI
        self.initialize_gui()
        
        self.logger.info("✅ Графический интерфейс инициализирован")
    
    def initialize_gui(self):
        """Инициализация GUI"""
        try:
            dpg.create_context()
            
            # Темы
            self.obsidian_theme = ObsidianTheme.setup_theme()
            self.danger_theme = DangerTheme.setup_theme()
            
            # Viewport
            dpg.create_viewport(
                title='RapidRecon • Advanced Security Scanner',
                width=1600, height=1000,
                min_width=1200, min_height=800
            )
            
            # Главное окно
            self.create_main_window()
            
            # Вспомогательные окна
            self.create_settings_window()
            
            # Запуск
            dpg.bind_theme(self.obsidian_theme)
            dpg.setup_dearpygui()
            dpg.show_viewport()
            dpg.set_primary_window("main_window", True)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации GUI: {e}")
            raise
    
    def create_main_window(self):
        """Создание главного окна"""
        with dpg.window(tag="main_window", label="RapidRecon", width=1600, height=1000,
                       no_move=True, no_resize=True, no_collapse=True, no_close=True):
            
            # Боковая панель
            with dpg.child_window(tag="sidebar", width=300, border=False):
                self.create_sidebar()
            
            # Основная область
            with dpg.group(horizontal=True, width=-1, height=-1):
                with dpg.child_window(tag="content_area", width=-1, border=False):
                    self.create_content_area()
    
    def create_sidebar(self):
        """Боковая панель"""
        # Логотип
        dpg.add_spacer(height=20)
        dpg.add_text("RapidRecon", color=[123, 97, 255])
        dpg.add_text("Security Scanner", color=[150, 150, 160])
        dpg.add_separator()
        
        # Быстрый запуск
        with dpg.collapsing_header(label="⚡ Quick Launch", default_open=True):
            dpg.add_text("Target:", color=[150, 150, 160])
            dpg.add_input_text(tag="quick_target", hint="example.com", width=-1)
            
            dpg.add_button(label="🎯 Start Scan", tag="quick_scan_btn",
                         width=-1, callback=self.quick_start_scan)
            dpg.add_button(label="⏹️ Stop", tag="quick_stop_btn",
                         width=-1, callback=self.stop_scan, show=False)
        
        # Статистика
        with dpg.collapsing_header(label="📈 Statistics", default_open=True):
            dpg.add_text("Discovered:", color=[150, 150, 160])
            dpg.add_text("Nodes: 0", tag="stat_nodes")
            dpg.add_text("Hosts: 0", tag="stat_hosts")
            dpg.add_text("Services: 0", tag="stat_services")
            dpg.add_text("Vulnerabilities: 0", tag="stat_vulns")
        
        # Действия
        dpg.add_separator()
        dpg.add_button(label="🧹 Clear All", width=-1, callback=self.clear_all)
    
    def create_content_area(self):
        """Основная область контента"""
        with dpg.tab_bar(tag="main_tabs"):
            # Вкладка сканирования
            with dpg.tab(label="🎯 Scan"):
                self.create_scan_tab()
            
            # Вкладка графа
            with dpg.tab(label="🌐 Network Map"):
                self.create_graph_tab()
            
            # Вкладка результатов
            with dpg.tab(label="📊 Results"):
                self.create_results_tab()
    
    def create_scan_tab(self):
        """Вкладка сканирования"""
        dpg.add_text("Target Configuration", color=[123, 97, 255])
        
        with dpg.group(horizontal=True):
            with dpg.child_window(width=400):
                dpg.add_text("Targets:")
                dpg.add_input_text(tag="target_input", multiline=True, height=100, width=-1)
            
            with dpg.child_window(width=400):
                dpg.add_text("Modules:")
                dpg.add_checkbox(tag="mod_ping", label="Ping Scanner", default_value=True)
                dpg.add_checkbox(tag="mod_ports", label="Port Scanner", default_value=True)
                dpg.add_checkbox(tag="mod_subdomains", label="Subdomain Scanner", default_value=True)
        
        dpg.add_button(label="🚀 Start Advanced Scan", callback=self.start_scan)
        
        # Лог
        dpg.add_text("Activity Log:")
        dpg.add_input_text(tag="activity_log", multiline=True, height=300, 
                         readonly=True, width=-1)
    
    def create_graph_tab(self):
        """Вкладка графа сети"""
        # Управление
        with dpg.group(horizontal=True):
            dpg.add_button(label="🔄 Refresh", callback=self.update_graph_display)
            dpg.add_button(label="🧹 Clear", callback=self.clear_graph)
            dpg.add_button(label="💾 Export", callback=self.export_graph)
        
        # Легенда
        with dpg.collapsing_header(label="Legend", default_open=True):
            with dpg.table(header_row=False):
                dpg.add_table_column()
                dpg.add_table_column()
                
                legends = [
                    ("🎯", "Initial Target"),
                    ("🌐", "Subdomain"), 
                    ("💻", "Active Host"),
                    ("🔓", "Open Ports"),
                    ("🔴", "Vulnerability"),
                    ("💥", "Exploitation")
                ]
                
                for icon, text in legends:
                    with dpg.table_row():
                        dpg.add_text(icon)
                        dpg.add_text(text)
        
        # Область графа
        with dpg.child_window(tag="graph_container", height=600, border=True):
            with dpg.drawlist(tag="graph_canvas", width=-1, height=-1):
                pass
    
    def create_results_tab(self):
        """Вкладка результатов"""
        with dpg.group(horizontal=True):
            # Дерево узлов
            with dpg.child_window(width=400):
                dpg.add_text("Discovered Nodes:")
                dpg.add_tree_node(tag="nodes_tree", label="Network (0 nodes)", default_open=True)
            
            # Детали
            with dpg.child_window():
                dpg.add_text("Node Details:")
                dpg.add_input_text(tag="node_details", multiline=True, height=500, 
                                 readonly=True, width=-1)
    
    def create_settings_window(self):
        """Окно настроек"""
        with dpg.window(tag="settings_window", label="Settings", 
                       width=600, height=400, show=False):
            dpg.add_text("Engine Settings")
            dpg.add_button(label="Close", callback=lambda: dpg.hide_item("settings_window"))
    
    def quick_start_scan(self):
        """Быстрый старт сканирования"""
        target = dpg.get_value("quick_target")
        if not target:
            self.add_log("❌ Enter target first!")
            return
        
        self.add_log(f"🚀 Starting scan: {target}")
        
        try:
            if hasattr(self.engine, 'add_initial_target'):
                self.engine.add_initial_target(target)
            
            if hasattr(self.engine, 'start_scan'):
                if self.engine.start_scan():
                    self.is_scanning = True
                    dpg.hide_item("quick_scan_btn")
                    dpg.show_item("quick_stop_btn")
                    self.add_log("✅ Scan started!")
        except Exception as e:
            self.add_log(f"❌ Error: {e}")
    
    def stop_scan(self):
        """Остановка сканирования"""
        try:
            if self.is_scanning and hasattr(self.engine, 'stop_scan'):
                self.engine.stop_scan()
                self.is_scanning = False
                dpg.show_item("quick_scan_btn")
                dpg.hide_item("quick_stop_btn")
                self.add_log("⏹️ Scan stopped")
        except Exception as e:
            self.add_log(f"❌ Error stopping: {e}")
    
    def start_scan(self):
        """Расширенное сканирование"""
        targets = dpg.get_value("target_input")
        if not targets:
            self.add_log("❌ Enter targets!")
            return
        
        target_list = [t.strip() for t in targets.split('\n') if t.strip()]
        self.add_log(f"🎯 Starting advanced scan: {len(target_list)} targets")
        
        try:
            if hasattr(self.engine, 'add_initial_target'):
                for target in target_list:
                    self.engine.add_initial_target(target)
            
            if hasattr(self.engine, 'start_scan'):
                if self.engine.start_scan():
                    self.is_scanning = True
                    self.add_log("✅ Advanced scan started!")
        except Exception as e:
            self.add_log(f"❌ Error: {e}")
    
    def handle_engine_event(self, event_type: str, data: Any = None):
        """Обработка событий от движка - КЛЮЧЕВОЙ МЕТОД"""
        try:
            self.logger.info(f"GUI event: {event_type}")
            
            if event_type == 'node_added':
                self.process_node(data, "🎯 Added")
            elif event_type == 'node_discovered':
                self.process_node(data, "🔍 Discovered")
            elif event_type == 'module_results':
                self.process_module_results(data)
            elif event_type == 'scan_completed':
                self.add_log("✅ Scan completed")
                self.is_scanning = False
                dpg.show_item("quick_scan_btn")
                dpg.hide_item("quick_stop_btn")
            
            # Обновляем интерфейс
            self.update_ui()
            
        except Exception as e:
            self.logger.error(f"Error handling event: {e}")
    
    def process_node(self, scan_node, log_prefix: str):
        """Обработать ScanNode и добавить в граф"""
        try:
            if not hasattr(scan_node, 'node_id'):
                return
            
            # Сохраняем оригинальный узел
            self.all_nodes[scan_node.node_id] = scan_node
            
            # Создаем данные для графа
            node_data = self.scan_node_to_dict(scan_node)
            self.add_log(f"{log_prefix}: {node_data.get('data', 'Unknown')}")
            
            # Добавляем в граф
            graph_node_id = self.graph.add_node(node_data)
            if graph_node_id != -1:
                self.graph_nodes[scan_node.node_id] = graph_node_id
                
                # Добавляем связь с источником
                source_id = getattr(scan_node, 'source', None)
                if source_id and source_id in self.graph_nodes:
                    source_graph_id = self.graph_nodes[source_id]
                    edge_type = self.get_edge_type(node_data)
                    self.graph.add_edge(source_graph_id, graph_node_id, edge_type)
                    
        except Exception as e:
            self.logger.error(f"Error processing node: {e}")
    
    def process_module_results(self, results):
        """Обработать результаты модуля"""
        try:
            self.add_log("⚙️ Module results")
            
            # Обрабатываем основную задачу
            task = results.get('task')
            if task and hasattr(task, 'node_id'):
                self.process_node(task, "📊 Processed")
            
            # Обрабатываем открытые порты
            if 'open_ports' in results:
                for ip, ports in results['open_ports'].items():
                    if ports:
                        self.add_log(f"🔓 Ports found on {ip}: {ports}")
                        self.create_ports_node(ip, ports)
                        
        except Exception as e:
            self.logger.error(f"Error processing module results: {e}")
    
    def scan_node_to_dict(self, scan_node) -> Dict[str, Any]:
        """Конвертировать ScanNode в словарь"""
        try:
            node_type = getattr(scan_node, 'type', 'unknown')
            if hasattr(node_type, 'value'):
                node_type = node_type.value
            
            data = getattr(scan_node, 'data', 'Unknown')
            module = getattr(scan_node, 'module', 'unknown')
            
            # Определяем тип для визуализации
            vis_type = 'unknown'
            if node_type == 'initial_target':
                vis_type = 'initial_target'
            elif node_type == 'subdomain':
                vis_type = 'subdomain'
            elif node_type == 'active_host':
                vis_type = 'active_host'
            elif 'port' in module:
                vis_type = 'open_ports'
            elif 'vulnerability' in module:
                vis_type = 'vulnerability'
            
            return {
                'type': vis_type,
                'data': data,
                'source': getattr(scan_node, 'source', None),
                'module': module
            }
        except Exception as e:
            self.logger.error(f"Error converting node: {e}")
            return {'type': 'unknown', 'data': 'Error'}
    
    def create_ports_node(self, ip: str, ports: List):
        """Создать узел для открытых портов"""
        try:
            port_data = {
                'type': 'open_ports',
                'data': f"{ip}:{len(ports)} ports",
                'ports': ports,
                'ip': ip
            }
            
            port_node_id = self.graph.add_node(port_data)
            
            # Связываем с хостом
            for engine_id, graph_id in self.graph_nodes.items():
                node = self.graph.nodes.get(graph_id)
                if node and node.get('data') == ip:
                    self.graph.add_edge(graph_id, port_node_id, 'port')
                    break
                    
        except Exception as e:
            self.logger.error(f"Error creating ports node: {e}")
    
    def get_edge_type(self, node_data: Dict) -> str:
        """Определить тип связи"""
        node_type = node_data.get('type', '')
        module = node_data.get('module', '')
        
        if node_type == 'subdomain':
            return 'dns'
        elif 'port' in module:
            return 'port'
        elif 'vulnerability' in module:
            return 'vulnerability'
        else:
            return 'normal'
    
    def update_ui(self):
        """Обновить весь интерфейс"""
        self.update_statistics()
        self.update_graph_display()
        self.update_nodes_tree()
    
    def update_statistics(self):
        """Обновить статистику"""
        try:
            nodes_count = len(self.graph.nodes)
            hosts_count = sum(1 for n in self.graph.nodes.values() 
                            if n['type'] in ['initial_target', 'active_host'])
            services_count = sum(1 for n in self.graph.nodes.values() 
                               if n['type'] == 'service')
            vulns_count = sum(1 for n in self.graph.nodes.values() 
                            if n['type'] == 'vulnerability')
            
            dpg.set_value("stat_nodes", f"Nodes: {nodes_count}")
            dpg.set_value("stat_hosts", f"Hosts: {hosts_count}")
            dpg.set_value("stat_services", f"Services: {services_count}")
            dpg.set_value("stat_vulns", f"Vulnerabilities: {vulns_count}")
            
        except Exception as e:
            self.logger.error(f"Error updating stats: {e}")
    
    def update_graph_display(self):
        """Обновить отображение графа"""
        try:
            if dpg.does_item_exist("graph_canvas"):
                dpg.delete_item("graph_canvas", children_only=True)
            
            width = dpg.get_item_width("graph_container")
            height = dpg.get_item_height("graph_container")
            self.graph.draw(width - 20, height - 20)
            
        except Exception as e:
            self.logger.error(f"Error updating graph: {e}")
    
    def update_nodes_tree(self):
        """Обновить дерево узлов"""
        try:
            if not dpg.does_item_exist("nodes_tree"):
                return
            
            dpg.delete_item("nodes_tree", children_only=True)
            dpg.set_value("nodes_tree", f"Network ({len(self.graph.nodes)} nodes)")
            
            # Группируем по типам
            by_type = {}
            for node_id, node in self.graph.nodes.items():
                node_type = node['type']
                if node_type not in by_type:
                    by_type[node_type] = []
                by_type[node_type].append(node)
            
            # Создаем дерево
            for node_type, nodes in by_type.items():
                with dpg.tree_node(label=f"{node_type} ({len(nodes)})", parent="nodes_tree"):
                    for node in nodes:
                        with dpg.tree_node(label=node['label']):
                            details = self.get_node_details(node)
                            dpg.add_text(details)
                            
        except Exception as e:
            self.logger.error(f"Error updating tree: {e}")
    
    def get_node_details(self, node: Dict) -> str:
        """Получить детали узла"""
        details = []
        details.append(f"Type: {node['type']}")
        details.append(f"Data: {node['data']}")
        
        if 'ports' in node.get('data', {}):
            details.append(f"Ports: {node['data']['ports']}")
        
        return "\n".join(details)
    
    def add_log(self, message: str):
        """Добавить сообщение в лог"""
        try:
            current = dpg.get_value("activity_log") or ""
            timestamp = datetime.now().strftime("%H:%M:%S")
            new_log = f"[{timestamp}] {message}\n"
            dpg.set_value("activity_log", current + new_log)
            dpg.focus_item("activity_log")
        except Exception as e:
            self.logger.error(f"Error adding log: {e}")
    
    def clear_all(self):
        """Очистить все"""
        try:
            self.graph.clear()
            self.all_nodes.clear()
            self.graph_nodes.clear()
            dpg.set_value("activity_log", "")
            self.update_ui()
            self.add_log("🧹 All cleared")
        except Exception as e:
            self.add_log(f"❌ Clear error: {e}")
    
    def clear_graph(self):
        """Очистить граф"""
        self.graph.clear()
        self.update_graph_display()
        self.add_log("🗺️ Graph cleared")
    
    def export_graph(self):
        """Экспорт графа"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"network_map_{timestamp}.json"
            
            data = {
                'nodes': list(self.graph.nodes.values()),
                'edges': self.graph.edges,
                'export_time': timestamp
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            self.add_log(f"💾 Exported to {filename}")
        except Exception as e:
            self.add_log(f"❌ Export error: {e}")
    
    def run(self):
        """Запуск GUI"""
        try:
            self.logger.info("🚀 Starting GUI...")
            while dpg.is_dearpygui_running():
                dpg.render_dearpygui_frame()
            self.destroy()
        except Exception as e:
            self.logger.error(f"❌ GUI error: {e}")
            raise
    
    def destroy(self):
        """Уничтожение GUI"""
        try:
            self.logger.info("🧹 Cleaning up GUI...")
            dpg.destroy_context()
            self.logger.info("✅ GUI destroyed")
        except Exception as e:
            self.logger.error(f"❌ Destroy error: {e}")
