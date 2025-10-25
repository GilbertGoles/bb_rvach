"""
Главное окно RapidRecon в стиле Obsidian - ИСПРАВЛЕННАЯ ВЕРСИЯ с таблицей хостов
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

class GraphVisualization:
    """Визуализация графа в стиле Obsidian"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.node_counter = 0
        self.selected_node = None
    
    def draw_graph(self, width: int, height: int):
        """Отрисовка графа"""
        try:
            # Фон графа
            dpg.draw_rectangle(
                [0, 0], 
                [width, height], 
                fill=[25, 25, 32],
                parent="graph_canvas"
            )
            
            # Сетка
            grid_size = 50
            for x in range(0, width, grid_size):
                dpg.draw_line(
                    [x, 0], [x, height],
                    color=[40, 40, 50],
                    thickness=1,
                    parent="graph_canvas"
                )
            for y in range(0, height, grid_size):
                dpg.draw_line(
                    [0, y], [width, y],
                    color=[40, 40, 50],
                    thickness=1,
                    parent="graph_canvas"
                )
            
            # Отрисовка связей
            for edge in self.edges:
                source = self.nodes.get(edge['source'])
                target = self.nodes.get(edge['target'])
                if source and target:
                    dpg.draw_line(
                        source['position'], target['position'],
                        color=edge['color'],
                        thickness=edge['thickness'],
                        parent="graph_canvas"
                    )
            
            # Отрисовка узлов
            for node_id, node in self.nodes.items():
                pos = node['position']
                
                # Основной круг узла
                dpg.draw_circle(
                    pos, node['radius'],
                    fill=node['color'],
                    color=[255, 255, 255, 100] if node_id != self.selected_node else [255, 255, 0, 200],
                    thickness=3 if node_id == self.selected_node else 2,
                    parent="graph_canvas"
                )
                
                # Иконка узла
                icon = node.get('icon', '•')
                dpg.draw_text(
                    [pos[0] - 4, pos[1] - 6],
                    icon,
                    color=[255, 255, 255],
                    size=14,
                    parent="graph_canvas"
                )
                
                # Текст метки
                dpg.draw_text(
                    [pos[0] - len(node['label']) * 3, pos[1] + node['radius'] + 8],
                    node['label'],
                    color=[200, 200, 200],
                    size=11,
                    parent="graph_canvas"
                )
        except Exception as e:
            logging.error(f"Error drawing graph: {e}")
    
    def add_node(self, node_data: Dict[str, Any]) -> int:
        """Добавить узел"""
        try:
            node_id = self.node_counter
            self.node_counter += 1
            
            node_type = node_data.get('type', 'custom')
            node_config = self._get_node_config(node_type)
            position = self._calculate_node_position(node_id, node_type)
            label = self._get_node_label(node_data)
            
            self.nodes[node_id] = {
                'id': node_id,
                'label': label,
                'type': node_type,
                'data': node_data,
                'position': position,
                'radius': node_config['radius'],
                'color': node_config['color'],
                'icon': node_config['icon'],
                'original_data': node_data
            }
            
            return node_id
        except Exception as e:
            logging.error(f"Error adding node: {e}")
            return -1
    
    def _get_node_label(self, node_data: Dict[str, Any]) -> str:
        """Получить метку для узла"""
        try:
            data = node_data.get('data', '')
            node_type = node_data.get('type', '')
            
            if node_type == 'initial_target':
                return str(data)
            elif node_type == 'subdomain':
                return str(data)
            elif node_type == 'active_host':
                return str(data)
            elif node_type == 'open_ports':
                ports = node_data.get('ports', [])
                return f"Ports: {len(ports)}"
            elif node_type == 'service':
                service = node_data.get('service_name', 'Unknown')
                return f"{service}"
            else:
                return str(data)[:15]
        except:
            return "Unknown"
    
    def _get_node_config(self, node_type: str) -> Dict[str, Any]:
        """Конфигурация узлов по типам"""
        configs = {
            'initial_target': {'color': [72, 199, 116, 200], 'radius': 25, 'icon': '🎯'},
            'subdomain': {'color': [86, 156, 214, 180], 'radius': 20, 'icon': '🌐'},
            'active_host': {'color': [255, 179, 64, 200], 'radius': 22, 'icon': '💻'},
            'open_ports': {'color': [123, 97, 255, 180], 'radius': 20, 'icon': '🔓'},
            'service': {'color': [158, 118, 255, 180], 'radius': 18, 'icon': '⚙️'},
            'vulnerability': {'color': [255, 92, 87, 220], 'radius': 19, 'icon': '🔴'},
            'vulnerability_scan': {'color': [255, 120, 100, 180], 'radius': 20, 'icon': '🔍'},
            'exploitation': {'color': [255, 60, 60, 220], 'radius': 23, 'icon': '💥'},
            'exploitation_success': {'color': [255, 0, 0, 230], 'radius': 28, 'icon': '💀'},
            'internal_scan': {'color': [64, 192, 192, 180], 'radius': 24, 'icon': '🔍'},
            'domain_scan': {'color': [100, 180, 255, 180], 'radius': 21, 'icon': '🌍'}
        }
        return configs.get(node_type, {'color': [128, 128, 128, 150], 'radius': 20, 'icon': '•'})
    
    def _calculate_node_position(self, node_id: int, node_type: str) -> List[float]:
        """Интеллектуальное позиционирование узлов"""
        center_x, center_y = 500, 350
        
        if not self.nodes:
            return [center_x, center_y]
        
        type_positions = {
            'initial_target': [center_x - 200, center_y - 200],
            'subdomain': [center_x - 150, center_y - 100],
            'active_host': [center_x, center_y],
            'open_ports': [center_x + 150, center_y],
            'service': [center_x + 250, center_y + 50],
            'vulnerability': [center_x + 100, center_y + 150],
            'exploitation': [center_x - 100, center_y + 150],
            'exploitation_success': [center_x - 200, center_y + 200],
            'internal_scan': [center_x - 300, center_y]
        }
        
        if node_type in type_positions:
            base_pos = type_positions[node_type]
            return [
                base_pos[0] + random.uniform(-30, 30),
                base_pos[1] + random.uniform(-30, 30)
            ]
        
        angle = (node_id * 2 * math.pi / len(self.nodes))
        radius = 200 + (len(self.nodes) * 5)
        return [
            center_x + radius * math.cos(angle),
            center_y + radius * math.sin(angle)
        ]
    
    def add_edge(self, source_id: int, target_id: int, edge_type: str = "normal"):
        """Добавить связь"""
        try:
            if source_id in self.nodes and target_id in self.nodes:
                edge_configs = {
                    "normal": {"color": [150, 150, 150, 100], "thickness": 2},
                    "exploitation": {"color": [255, 60, 60, 150], "thickness": 3},
                    "vulnerability": {"color": [255, 100, 100, 120], "thickness": 2},
                    "lateral": {"color": [255, 165, 0, 150], "thickness": 3},
                    "dns": {"color": [86, 156, 214, 120], "thickness": 2},
                    "port": {"color": [123, 97, 255, 120], "thickness": 2}
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
    
    def get_node_details(self, node_id: int) -> str:
        """Получить детальную информацию об узле"""
        try:
            if node_id not in self.nodes:
                return "Node not found"
            
            node = self.nodes[node_id]
            details = []
            
            details.append(f"=== {node['label']} ===")
            details.append(f"Type: {node['type']}")
            details.append(f"ID: {node_id}")
            
            if 'original_data' in node:
                data = node['original_data']
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key not in ['position', 'color', 'radius', 'icon']:
                            details.append(f"{key}: {value}")
                else:
                    details.append(f"Data: {data}")
            
            connections = []
            for edge in self.edges:
                if edge['source'] == node_id:
                    target_node = self.nodes.get(edge['target'])
                    if target_node:
                        connections.append(f"→ {target_node['label']} ({edge['type']})")
                elif edge['target'] == node_id:
                    source_node = self.nodes.get(edge['source'])
                    if source_node:
                        connections.append(f"← {source_node['label']} ({edge['type']})")
            
            if connections:
                details.append("\nConnections:")
                details.extend(connections)
            
            return "\n".join(details)
        except Exception as e:
            logging.error(f"Error getting node details: {e}")
            return f"Error getting details: {e}"
    
    def clear(self):
        """Очистить граф"""
        self.nodes.clear()
        self.edges.clear()
        self.node_counter = 0
        self.selected_node = None

class HostManager:
    """Менеджер хостов для табличного отображения"""
    
    def __init__(self):
        self.hosts = {}  # ip -> host_data
        self.selected_host = None
    
    def add_host(self, ip: str, host_data: Dict[str, Any]):
        """Добавить хост"""
        try:
            if ip not in self.hosts:
                self.hosts[ip] = {
                    'ip': ip,
                    'hostname': host_data.get('hostname', 'Unknown'),
                    'ports': host_data.get('ports', []),
                    'services': host_data.get('services', []),
                    'os': host_data.get('os', 'Unknown'),
                    'status': host_data.get('status', 'unknown'),
                    'last_seen': datetime.now().strftime("%H:%M:%S"),
                    'vulnerabilities': host_data.get('vulnerabilities', []),
                    'tags': host_data.get('tags', [])
                }
            else:
                # Обновляем существующий хост
                self.hosts[ip].update(host_data)
                self.hosts[ip]['last_seen'] = datetime.now().strftime("%H:%M:%S")
        except Exception as e:
            logging.error(f"Error adding host: {e}")
    
    def get_host_details(self, ip: str) -> str:
        """Получить детальную информацию о хосте"""
        try:
            if ip not in self.hosts:
                return f"Host {ip} not found"
            
            host = self.hosts[ip]
            details = []
            
            details.append(f"=== {ip} ===")
            details.append(f"Hostname: {host['hostname']}")
            details.append(f"OS: {host['os']}")
            details.append(f"Status: {host['status']}")
            details.append(f"Last Seen: {host['last_seen']}")
            
            if host['ports']:
                details.append(f"\nOpen Ports ({len(host['ports'])}):")
                for port in host['ports']:
                    details.append(f"  - {port}")
            
            if host['services']:
                details.append(f"\nServices ({len(host['services'])}):")
                for service in host['services']:
                    details.append(f"  - {service}")
            
            if host['vulnerabilities']:
                details.append(f"\nVulnerabilities ({len(host['vulnerabilities'])}):")
                for vuln in host['vulnerabilities']:
                    details.append(f"  - {vuln}")
            
            if host['tags']:
                details.append(f"\nTags: {', '.join(host['tags'])}")
            
            return "\n".join(details)
        except Exception as e:
            logging.error(f"Error getting host details: {e}")
            return f"Error getting host details: {e}"
    
    def get_hosts_table_data(self) -> List[List[str]]:
        """Получить данные для таблицы хостов"""
        table_data = []
        for ip, host in self.hosts.items():
            table_data.append([
                ip,
                host['hostname'],
                str(len(host['ports'])),
                host['os'],
                host['status'],
                str(len(host['vulnerabilities'])),
                host['last_seen']
            ])
        return table_data

class MainWindow:
    """
    Главный интерфейс RapidRecon в стиле Obsidian
    """
    
    def __init__(self, engine, module_manager):
        self.engine = engine
        self.module_manager = module_manager
        self.graph = GraphVisualization()
        self.host_manager = HostManager()
        self.is_scanning = False
        self.logger = logging.getLogger('RapidRecon.GUI')
        self.settings_window_open = False
        self.selected_targets = set()
        self.last_update_time = 0
        self.update_interval = 1.0
        self.discovered_nodes = {}
        self.node_id_map = {}
        
        # Инициализация GUI
        self.initialize_gui()
        
        self.logger.info("✅ Графический интерфейс инициализирован")
    
    def initialize_gui(self):
        """Инициализация GUI с улучшенной обработкой ошибок"""
        try:
            self.logger.info("🛠️ Инициализация Dear PyGui...")
            
            # Инициализация DPG
            dpg.create_context()
            
            # Создание тем
            self.obsidian_theme = ObsidianTheme.setup_theme()
            self.danger_theme = DangerTheme.setup_theme()
            
            # Создание viewport
            dpg.create_viewport(
                title='RapidRecon • Advanced Security Scanner',
                width=1600,
                height=1000,
                min_width=1200,
                min_height=800
            )
            
            # Создание главного окна
            self.create_main_window()
            
            # Создание вспомогательных окон
            self.create_settings_window()
            self.create_targets_window()
            
            # Настройка и показ GUI
            dpg.bind_theme(self.obsidian_theme)
            dpg.setup_dearpygui()
            dpg.show_viewport()
            dpg.set_primary_window("main_window", True)
            
            self.logger.info("✅ GUI успешно инициализирован")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации GUI: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def create_main_window(self):
        """Создание главного окна"""
        with dpg.window(
            tag="main_window",
            label="RapidRecon - Advanced Network Reconnaissance",
            width=1600,
            height=1000,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            no_close=True
        ):
            # Боковая панель
            with dpg.child_window(tag="sidebar", width=300, border=False):
                self.create_sidebar()
            
            # Основная область
            with dpg.group(horizontal=True, width=-1, height=-1):
                with dpg.child_window(tag="content_area", width=-1, border=False):
                    self.create_content_area()
    
    def create_sidebar(self):
        """Создание боковой панели"""
        # Логотип
        with dpg.group():
            dpg.add_spacer(height=20)
            dpg.add_text("RapidRecon", color=[123, 97, 255])
            dpg.add_text("Advanced Security Scanner", color=[150, 150, 160])
            dpg.add_separator()
        
        # Быстрый запуск
        with dpg.collapsing_header(label="⚡ Quick Launch", default_open=True):
            dpg.add_text("Primary Target:", color=[150, 150, 160])
            dpg.add_input_text(tag="quick_target_input", hint="example.com / 192.168.1.1", width=-1)
            
            dpg.add_text("Scan Intensity:", color=[150, 150, 160])
            dpg.add_combo(
                tag="scan_level",
                items=["🚀 Stealth", "⚡ Normal", "💥 Aggressive", "🔥 Full Attack", "💀 Pentest"],
                default_value="⚡ Normal",
                width=-1,
                callback=self._on_scan_level_change
            )
            
            dpg.add_button(
                label="🎯 Start Reconnaissance",
                tag="quick_scan_button",
                width=-1,
                callback=self.quick_start_scan
            )
            dpg.add_button(
                label="⏹️ Stop All Scans", 
                tag="quick_stop_button",
                width=-1,
                callback=self.stop_scan,
                show=False
            )
        
        # Модули
        with dpg.collapsing_header(label="🔧 Capabilities", default_open=True):
            dpg.add_text("Available Modules:", color=[150, 150, 160])
            modules = [
                "• Ping Scanner", "• Port Scanner", "• Service Detector",
                "• Subdomain Scanner", "• Vulnerability Scanner", 
                "• Exploitation Engine", "• Lateral Movement"
            ]
            for module in modules:
                color = [200, 200, 200]
                if "Vulnerability" in module: color = [255, 100, 100]
                if "Exploitation" in module: color = [255, 60, 60]
                if "Lateral" in module: color = [255, 165, 0]
                dpg.add_text(module, color=color)
        
        # Статистика
        with dpg.collapsing_header(label="📈 Live Statistics", default_open=True):
            dpg.add_text("Network:", color=[150, 150, 160])
            dpg.add_text("Nodes: 0", tag="stat_nodes")
            dpg.add_text("Hosts: 0", tag="stat_hosts")
            dpg.add_text("Services: 0", tag="stat_services")
            dpg.add_text("Targets: 0", tag="stat_targets")
            
            dpg.add_text("Security:", color=[150, 150, 160])
            dpg.add_text("Vulnerabilities: 0", tag="stat_vulns")
            dpg.add_text("Exploits: 0", tag="stat_exploits")
            dpg.add_text("Lateral Moves: 0", tag="stat_lateral")
        
        # Действия
        with dpg.group():
            dpg.add_separator()
            dpg.add_button(label="⚙️ Engine Settings", width=-1, callback=self.show_settings)
            dpg.add_button(label="📤 Export All Data", width=-1, callback=self.export_all_data)
            dpg.add_button(label="🧹 Clear Everything", width=-1, callback=self.clear_everything)
    
    def create_content_area(self):
        """Создание основной области контента"""
        with dpg.tab_bar(tag="main_tabs"):
            # Вкладка сканирования
            with dpg.tab(label="🎯 Reconnaissance", tag="scan_tab"):
                self.create_scan_tab()
            
            # Вкладка графа
            with dpg.tab(label="🌐 Network Map", tag="graph_tab"):
                self.create_graph_tab()
            
            # Вкладка результатов
            with dpg.tab(label="📊 Results & Analysis", tag="results_tab"):
                self.create_results_tab()
            
            # Вкладка эксплуатации
            with dpg.tab(label="💥 Exploitation", tag="exploit_tab"):
                self.create_exploit_tab()
    
    def create_scan_tab(self):
        """Создание вкладки сканирования"""
        with dpg.group():
            dpg.add_text("Advanced Reconnaissance Configuration", color=[123, 97, 255])
            
            # Конфигурация целей
            with dpg.collapsing_header(label="🎯 Target Configuration", default_open=True):
                with dpg.group(horizontal=True):
                    with dpg.child_window(width=400):
                        dpg.add_text("Primary Targets")
                        dpg.add_input_text(
                            tag="target_input",
                            hint="Enter domains, IPs or ranges...",
                            width=-1,
                            height=60,
                            multiline=True
                        )
                    
                    with dpg.child_window(width=400):
                        dpg.add_text("Module Selection")
                        dpg.add_checkbox(tag="mod_ping", label="Ping Scanner", default_value=True)
                        dpg.add_checkbox(tag="mod_ports", label="Port Scanner", default_value=True)
                        dpg.add_checkbox(tag="mod_services", label="Service Detection", default_value=True)
                        dpg.add_checkbox(tag="mod_subdomains", label="Subdomain Discovery", default_value=True)
                        dpg.add_checkbox(tag="mod_vulns", label="Vulnerability Scanning", default_value=True)
            
            # Кнопки управления
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="🚀 Start Advanced Scan",
                    tag="adv_scan_button",
                    callback=self.start_scan
                )
                dpg.add_button(
                    label="⏹️ Stop Scan", 
                    tag="adv_stop_button",
                    callback=self.stop_scan,
                    show=False
                )
                dpg.add_button(label="🧹 Clear Results", callback=self.clear_results)
        
        # Лог
        dpg.add_text("Activity Log")
        dpg.add_input_text(
            tag="activity_log",
            multiline=True,
            height=300,
            readonly=True,
            width=-1
        )
    
    def create_graph_tab(self):
        """Создание вкладки графа"""
        with dpg.group():
            # Панель управления
            with dpg.group(horizontal=True):
                dpg.add_button(label="🔄 Refresh Map", callback=self.update_graph)
                dpg.add_button(label="🧹 Clear Map", callback=self.clear_graph)
                dpg.add_button(label="💾 Export Map", callback=self.export_graph)
                dpg.add_button(label="🔴 Show Vulnerabilities", callback=self.highlight_vulnerabilities)
            
            # Легенда
            with dpg.collapsing_header(label="🎨 Map Legend", default_open=True):
                with dpg.table(header_row=False):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    
                    legends = [
                        ("🎯", "Initial Target", [72, 199, 116]),
                        ("🌐", "Subdomain", [86, 156, 214]),
                        ("💻", "Active Host", [255, 179, 64]),
                        ("🔓", "Open Ports", [123, 97, 255]),
                        ("🔴", "Vulnerability", [255, 92, 87]),
                        ("💥", "Exploitation", [255, 60, 60])
                    ]
                    
                    for icon, text, color in legends:
                        with dpg.table_row():
                            dpg.add_text(icon, color=color)
                            dpg.add_text(text)
            
            # Область графа
            with dpg.child_window(tag="graph_container", height=650, border=True):
                with dpg.drawlist(tag="graph_canvas", width=-1, height=-1):
                    pass
    
    def create_results_tab(self):
        """Создание вкладки результатов с таблицей хостов"""
        with dpg.group(horizontal=True):
            # Левая панель - таблица хостов
            with dpg.child_window(width=600):
                dpg.add_text("Discovered Hosts")
                
                # Таблица хостов
                with dpg.table(
                    tag="hosts_table",
                    header_row=True,
                    borders_innerH=True,
                    borders_outerH=True,
                    borders_innerV=True,
                    borders_outerV=True,
                    resizable=True,
                    policy=dpg.mvTable_SizingStretchProp,
                    row_background=True,
                    reorderable=True,
                    hideable=True,
                    sortable=True,
                    context_menu_in_body=True,
                    height=400
                ):
                    # Заголовки таблицы
                    headers = ["IP Address", "Hostname", "Ports", "OS", "Status", "Vulns", "Last Seen"]
                    for header in headers:
                        dpg.add_table_column(label=header)
                
                # Дерево инфраструктуры
                dpg.add_text("Network Infrastructure")
                dpg.add_tree_node(tag="nodes_tree", label="Network Topology (0 nodes)", default_open=True)
            
            # Правая панель - детальная информация
            with dpg.child_window():
                dpg.add_text("Host & Node Details")
                dpg.add_input_text(
                    tag="node_details",
                    multiline=True,
                    height=600,
                    readonly=True,
                    width=-1
                )
    
    def create_exploit_tab(self):
        """Создание вкладки эксплуатации"""
        with dpg.group():
            dpg.add_text("Advanced Exploitation Engine", color=[255, 60, 60])
            
            with dpg.group(horizontal=True):
                with dpg.child_window(width=400):
                    dpg.add_text("Target Selection")
                    dpg.add_listbox(tag="exploit_targets", items=[], num_items=8, width=-1)
                    dpg.add_button(label="🎯 Load Vulnerable Targets", callback=self.load_vulnerable_targets)
                
                with dpg.child_window(width=400):
                    dpg.add_text("Exploitation Options")
                    dpg.add_checkbox(tag="auto_exploit", label="Auto-Exploit Vulnerabilities")
                    dpg.add_checkbox(tag="lateral_movement", label="Enable Lateral Movement", default_value=True)
            
            # Кнопки эксплуатации
            with dpg.group(horizontal=True):
                exploit_button = dpg.add_button(label="💥 Start Exploitation", callback=self.start_exploitation)
                dpg.bind_item_theme(exploit_button, self.danger_theme)
                dpg.add_button(label="🔍 Scan for Exploits", callback=self.scan_for_exploits)
            
            # Результаты
            dpg.add_text("Exploitation Results")
            dpg.add_input_text(
                tag="exploitation_log",
                multiline=True,
                height=300,
                readonly=True,
                width=-1
            )
    
    def create_settings_window(self):
        """Создание окна настроек"""
        with dpg.window(tag="settings_window", label="Engine Settings", width=700, height=600, show=False):
            with dpg.tab_bar():
                with dpg.tab(label="General"):
                    dpg.add_text("General Settings")
                    dpg.add_input_text(tag="settings_scan_dir", label="Scan Directory", default_value="./scans/", width=-1)
                    dpg.add_checkbox(tag="settings_auto_save", label="Auto-save results", default_value=True)
                
                with dpg.tab(label="Scanning"):
                    dpg.add_text("Scanning Engine Settings")
                    dpg.add_slider_int(tag="settings_default_threads", label="Default Threads", default_value=15, min_value=1, max_value=100)
                    dpg.add_slider_int(tag="settings_default_timeout", label="Default Timeout (s)", default_value=5, min_value=1, max_value=30)
            
            with dpg.group(horizontal=True):
                dpg.add_button(label="💾 Save Settings", callback=self.save_settings)
                dpg.add_button(label="❌ Close", callback=lambda: dpg.hide_item("settings_window"))
    
    def create_targets_window(self):
        """Создание окна выбора целей"""
        with dpg.window(tag="targets_window", label="Select Targets", width=800, height=600, show=False):
            dpg.add_text("Discovered Targets")
            dpg.add_listbox(tag="discovered_targets_list", items=[], num_items=15, width=-1)
            
            with dpg.group(horizontal=True):
                dpg.add_button(label="🎯 Add Selected Targets", callback=self.add_selected_targets)
                dpg.add_button(label="❌ Close", callback=lambda: dpg.hide_item("targets_window"))

    def quick_start_scan(self):
        """Быстрый запуск сканирования"""
        try:
            target = dpg.get_value("quick_target_input")
            if not target:
                self.add_to_log("❌ Please enter a target first!")
                return
            
            self.add_to_log(f"🚀 Quick scan started for: {target}")
            
            if hasattr(self.engine, 'add_initial_target'):
                self.engine.add_initial_target(target)
            
            if hasattr(self.engine, 'start_scan'):
                if self.engine.start_scan():
                    self.is_scanning = True
                    dpg.hide_item("quick_scan_button")
                    dpg.show_item("quick_stop_button")
                    dpg.hide_item("adv_scan_button")
                    dpg.show_item("adv_stop_button")
                    self.add_to_log("✅ Scan started successfully!")
                    self._start_ui_updates()
                
        except Exception as e:
            self.logger.error(f"Error in quick_start_scan: {e}")
            self.add_to_log(f"❌ Error starting scan: {e}")
    
    def stop_scan(self):
        """Остановка сканирования"""
        try:
            if self.is_scanning and hasattr(self.engine, 'stop_scan'):
                self.engine.stop_scan()
                self.is_scanning = False
                dpg.show_item("quick_scan_button")
                dpg.hide_item("quick_stop_button")
                dpg.show_item("adv_scan_button")
                dpg.hide_item("adv_stop_button")
                self.add_to_log("⏹️ Scan stopped by user")
        except Exception as e:
            self.logger.error(f"Error stopping scan: {e}")
            self.add_to_log(f"❌ Error stopping scan: {e}")
    
    def start_scan(self):
        """Запуск расширенного сканирования"""
        try:
            targets_text = dpg.get_value("target_input")
            if not targets_text:
                self.add_to_log("❌ Please enter targets first!")
                return False
                
            targets = [t.strip() for t in targets_text.split('\n') if t.strip()]
            self.add_to_log(f"🎯 Starting advanced scan for {len(targets)} targets")
            
            if hasattr(self.engine, 'add_initial_target'):
                for target in targets:
                    self.engine.add_initial_target(target)
            
            if hasattr(self.engine, 'start_scan'):
                if self.engine.start_scan():
                    self.is_scanning = True
                    dpg.hide_item("quick_scan_button")
                    dpg.show_item("quick_stop_button")
                    dpg.hide_item("adv_scan_button")
                    dpg.show_item("adv_stop_button")
                    self.add_to_log("✅ Advanced scan started successfully!")
                    self._start_ui_updates()
                    return True
                
        except Exception as e:
            self.logger.error(f"Error in start_scan: {e}")
            self.add_to_log(f"❌ Error starting advanced scan: {e}")
        return False

    def handle_engine_event(self, event_type: str, data: Any = None):
        """Обработка событий от движка - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        try:
            self.logger.info(f"GUI received engine event: {event_type}")
            
            if event_type == 'node_added':
                self._handle_node_added(data)
            elif event_type == 'node_discovered':
                self._handle_node_discovered(data)
            elif event_type == 'module_results':
                self._handle_module_results(data)
            elif event_type == 'scan_completed':
                self._handle_scan_completed()
            elif event_type == 'vulnerability_found':
                self._handle_vulnerability_found(data)
            
            # Обновляем интерфейс после каждого события
            self.update_graph()
            self._update_statistics()
            self._update_nodes_tree()
            self._update_hosts_table()
                
        except Exception as e:
            self.logger.error(f"Error handling engine event: {e}")
    
    def _handle_node_added(self, node):
        """Обработка добавления узла"""
        try:
            self.add_to_log(f"🎯 Target added: {getattr(node, 'data', 'Unknown')}")
            self._process_scan_node(node)
        except Exception as e:
            self.logger.error(f"Error handling node added: {e}")
    
    def _handle_node_discovered(self, node):
        """Обработка обнаруженного узла"""
        try:
            self.add_to_log(f"🔍 Node discovered: {getattr(node, 'data', 'Unknown')}")
            self._process_scan_node(node)
        except Exception as e:
            self.logger.error(f"Error handling node discovered: {e}")
    
    def _handle_module_results(self, results):
        """Обработка результатов модуля"""
        try:
            self.add_to_log(f"⚙️ Module results received")
            
            # Обрабатываем основную задачу
            task = results.get('task')
            if task:
                self._process_scan_node(task)
            
            # Обрабатываем открытые порты
            if 'open_ports' in results:
                for ip, ports in results['open_ports'].items():
                    if ports:
                        self.add_to_log(f"🔓 Open ports found on {ip}: {ports}")
                        # Добавляем хост в менеджер хостов
                        self.host_manager.add_host(ip, {
                            'ports': ports,
                            'status': 'active',
                            'tags': ['port_scan']
                        })
                        # Создаем узел для открытых портов
                        port_node_data = {
                            'type': 'open_ports',
                            'data': f"{ip} ports",
                            'ports': ports,
                            'ip': ip
                        }
                        port_node_id = self.graph.add_node(port_node_data)
                        # Связываем с хостом
                        self._add_edge_to_host(ip, port_node_id, 'port')
            
        except Exception as e:
            self.logger.error(f"Error handling module results: {e}")
    
    def _process_scan_node(self, scan_node):
        """Обработать ScanNode и добавить в граф"""
        try:
            if not hasattr(scan_node, 'node_id'):
                return
                
            node_data = self._convert_scan_node_to_dict(scan_node)
            graph_node_id = self._add_node_to_graph(scan_node.node_id, node_data)
            
            if graph_node_id != -1:
                # Добавляем связь с источником если есть
                source = getattr(scan_node, 'source', None)
                if source and source in self.node_id_map:
                    source_graph_id = self.node_id_map[source]
                    edge_type = self._determine_edge_type(node_data)
                    self.graph.add_edge(source_graph_id, graph_node_id, edge_type)
                    
        except Exception as e:
            self.logger.error(f"Error processing scan node: {e}")
    
    def _convert_scan_node_to_dict(self, scan_node) -> Dict[str, Any]:
        """Конвертировать ScanNode в словарь для графа"""
        try:
            # Получаем основные атрибуты
            node_type = getattr(scan_node, 'type', 'unknown')
            if hasattr(node_type, 'value'):
                node_type = node_type.value
            
            node_data = {
                'type': node_type,
                'data': getattr(scan_node, 'data', 'Unknown'),
                'source': getattr(scan_node, 'source', 'unknown'),
                'module': getattr(scan_node, 'module', 'unknown'),
                'depth': getattr(scan_node, 'depth', 0),
                'timestamp': getattr(scan_node, 'timestamp', 0)
            }
            
            # Определяем тип узла для визуализации
            if node_data['type'] == 'initial_target':
                node_data['type'] = 'initial_target'
            elif node_data['type'] == 'subdomain':
                node_data['type'] = 'subdomain'
            elif node_data['type'] == 'active_host':
                node_data['type'] = 'active_host'
                # Добавляем хост в таблицу
                self.host_manager.add_host(node_data['data'], {
                    'status': 'active',
                    'tags': ['host_discovery']
                })
            elif 'port' in node_data['module']:
                node_data['type'] = 'open_ports'
            elif 'vulnerability' in node_data['module']:
                node_data['type'] = 'vulnerability'
            elif 'exploit' in node_data['module']:
                node_data['type'] = 'exploitation'
                
            return node_data
        except Exception as e:
            self.logger.error(f"Error converting scan node: {e}")
            return {'type': 'unknown', 'data': 'Conversion error'}
    
    def _add_node_to_graph(self, engine_node_id: str, node_data: Dict[str, Any]) -> int:
        """Добавить узел в граф"""
        try:
            # Проверяем, не добавлен ли уже узел
            if engine_node_id in self.node_id_map:
                return self.node_id_map[engine_node_id]
            
            # Добавляем узел в граф
            graph_node_id = self.graph.add_node(node_data)
            if graph_node_id != -1:
                self.node_id_map[engine_node_id] = graph_node_id
                return graph_node_id
            return -1
        except Exception as e:
            self.logger.error(f"Error adding node to graph: {e}")
            return -1
    
    def _add_edge_to_host(self, ip: str, target_node_id: int, edge_type: str):
        """Добавить связь к хосту по IP"""
        try:
            # Ищем узел с соответствующим IP
            for engine_id, graph_id in self.node_id_map.items():
                node = self.graph.nodes.get(graph_id)
                if node and node.get('data') == ip:
                    self.graph.add_edge(graph_id, target_node_id, edge_type)
                    self.add_to_log(f"🔗 Connected {ip} to ports node")
                    break
        except Exception as e:
            self.logger.error(f"Error adding edge to host: {e}")
    
    def _determine_edge_type(self, node_data: Dict[str, Any]) -> str:
        """Определить тип связи"""
        node_type = node_data.get('type', '')
        module = node_data.get('module', '')
        
        if 'dns' in module or node_type == 'subdomain':
            return 'dns'
        elif 'port' in module:
            return 'port'
        elif 'vulnerability' in module:
            return 'vulnerability'
        elif 'exploit' in module:
            return 'exploitation'
        else:
            return 'normal'
    
    def _handle_scan_completed(self):
        """Обработка завершения сканирования"""
        self.add_to_log("✅ Scan completed")
        self.is_scanning = False
        dpg.show_item("quick_scan_button")
        dpg.hide_item("quick_stop_button")
        dpg.show_item("adv_scan_button")
        dpg.hide_item("adv_stop_button")
    
    def _handle_vulnerability_found(self, data):
        """Обработка найденной уязвимости"""
        self.add_to_log(f"🔴 Vulnerability found: {data}")
        current_vulns = int(dpg.get_value("stat_vulns").split(": ")[1])
        dpg.set_value("stat_vulns", f"Vulnerabilities: {current_vulns + 1}")
    
    def update_graph(self):
        """Обновление графа"""
        try:
            if dpg.does_item_exist("graph_canvas"):
                dpg.delete_item("graph_canvas", children_only=True)
            
            container_width = dpg.get_item_width("graph_container")
            container_height = dpg.get_item_height("graph_container")
            self.graph.draw_graph(container_width - 20, container_height - 20)
            
        except Exception as e:
            self.logger.error(f"Error updating graph: {e}")
    
    def _update_statistics(self):
        """Обновление статистики"""
        try:
            nodes_count = len(self.graph.nodes)
            hosts_count = len(self.host_manager.hosts)
            services_count = sum(1 for node in self.graph.nodes.values() if node['type'] == 'service')
            targets_count = sum(1 for node in self.graph.nodes.values() if node['type'] in ['initial_target', 'active_host'])
            vulnerabilities_count = sum(1 for node in self.graph.nodes.values() if node['type'] == 'vulnerability')
            
            dpg.set_value("stat_nodes", f"Nodes: {nodes_count}")
            dpg.set_value("stat_hosts", f"Hosts: {hosts_count}")
            dpg.set_value("stat_services", f"Services: {services_count}")
            dpg.set_value("stat_targets", f"Targets: {targets_count}")
            dpg.set_value("stat_vulns", f"Vulnerabilities: {vulnerabilities_count}")
            
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")
    
    def _update_nodes_tree(self):
        """Обновление дерева узлов"""
        try:
            if not dpg.does_item_exist("nodes_tree"):
                return
                
            # Очищаем старое дерево
            dpg.delete_item("nodes_tree", children_only=True)
            
            # Обновляем заголовок
            dpg.set_value("nodes_tree", f"Network Topology ({len(self.graph.nodes)} nodes)")
            
            # Группируем узлы по типам
            nodes_by_type = {}
            for node_id, node in self.graph.nodes.items():
                node_type = node['type']
                if node_type not in nodes_by_type:
                    nodes_by_type[node_type] = []
                nodes_by_type[node_type].append(node)
            
            # Добавляем узлы в дерево
            for node_type, nodes in nodes_by_type.items():
                with dpg.tree_node(label=f"{node_type.title()} ({len(nodes)})", parent="nodes_tree"):
                    for node in nodes:
                        node_label = f"{node['label']} ({node['id']})"
                        with dpg.tree_node(label=node_label):
                            # Добавляем кнопку для просмотра деталей
                            def make_callback(node_id):
                                return lambda: self._show_node_details(node_id)
                            
                            dpg.add_button(
                                label="🔍 View Details", 
                                callback=make_callback(node['id'])
                            )
                            
        except Exception as e:
            self.logger.error(f"Error updating nodes tree: {e}")
    
    def _update_hosts_table(self):
        """Обновление таблицы хостов"""
        try:
            if not dpg.does_item_exist("hosts_table"):
                return
            
            # Очищаем таблицу (кроме заголовков)
            dpg.delete_item("hosts_table", children_only=True)
            
            # Добавляем заголовки
            headers = ["IP Address", "Hostname", "Ports", "OS", "Status", "Vulns", "Last Seen"]
            for header in headers:
                dpg.add_table_column(label=header, parent="hosts_table")
            
            # Добавляем строки с данными
            table_data = self.host_manager.get_hosts_table_data()
            for row_data in table_data:
                with dpg.table_row(parent="hosts_table"):
                    for i, cell_data in enumerate(row_data):
                        # Для IP адреса делаем кликабельным
                        if i == 0:
                            dpg.add_selectable(label=cell_data, callback=lambda s, d, ip=cell_data: self._show_host_details(ip))
                        else:
                            dpg.add_text(cell_data)
                            
        except Exception as e:
            self.logger.error(f"Error updating hosts table: {e}")
    
    def _show_node_details(self, node_id: int):
        """Показать детали узла"""
        try:
            details = self.graph.get_node_details(node_id)
            dpg.set_value("node_details", details)
        except Exception as e:
            self.logger.error(f"Error showing node details: {e}")
    
    def _show_host_details(self, ip: str):
        """Показать детали хоста"""
        try:
            details = self.host_manager.get_host_details(ip)
            dpg.set_value("node_details", details)
        except Exception as e:
            self.logger.error(f"Error showing host details: {e}")
    
    def add_to_log(self, message: str):
        """Добавить сообщение в лог"""
        try:
            current_log = dpg.get_value("activity_log")
            timestamp = datetime.now().strftime("%H:%M:%S")
            new_message = f"[{timestamp}] {message}\n"
            
            if current_log:
                new_log = current_log + new_message
            else:
                new_log = new_message
                
            dpg.set_value("activity_log", new_log)
            dpg.focus_item("activity_log")
        except Exception as e:
            self.logger.error(f"Error adding to log: {e}")
    
    def _start_ui_updates(self):
        """Запуск обновлений интерфейса"""
        def update_ui():
            current_time = time.time()
            if current_time - self.last_update_time >= self.update_interval:
                self.last_update_time = current_time
                
                if self.is_scanning:
                    try:
                        self._update_statistics()
                        self.update_graph()
                        self._update_nodes_tree()
                        self._update_hosts_table()
                    except Exception as e:
                        self.logger.error(f"Error in UI update: {e}")
        
        dpg.set_render_callback(update_ui)
    
    def _on_scan_level_change(self):
        """Обработчик изменения уровня сканирования"""
        scan_level = dpg.get_value("scan_level")
        self.add_to_log(f"🎛️ Scan intensity: {scan_level}")
    
    def show_settings(self):
        """Показать окно настроек"""
        try:
            if not self.settings_window_open:
                dpg.show_item("settings_window")
                self.settings_window_open = True
                dpg.focus_item("settings_window")
            else:
                dpg.hide_item("settings_window")
                self.settings_window_open = False
        except Exception as e:
            self.logger.error(f"Error showing settings: {e}")
    
    def clear_results(self):
        """Очистка результатов"""
        try:
            if hasattr(self.engine, 'clear_results'):
                self.engine.clear_results()
            self.graph.clear()
            self.host_manager.hosts.clear()
            self.discovered_nodes.clear()
            self.node_id_map.clear()
            dpg.set_value("activity_log", "")
            dpg.set_value("node_details", "")
            
            dpg.set_value("stat_nodes", "Nodes: 0")
            dpg.set_value("stat_hosts", "Hosts: 0")
            dpg.set_value("stat_services", "Services: 0")
            dpg.set_value("stat_targets", "Targets: 0")
            dpg.set_value("stat_vulns", "Vulnerabilities: 0")
            dpg.set_value("stat_exploits", "Exploits: 0")
            dpg.set_value("stat_lateral", "Lateral Moves: 0")
            
            self._update_hosts_table()
            self._update_nodes_tree()
            
            self.add_to_log("🧹 All results cleared")
        except Exception as e:
            self.logger.error(f"Error clearing results: {e}")
            self.add_to_log(f"❌ Error clearing results: {e}")
    
    def clear_graph(self):
        """Очистка графа"""
        try:
            self.graph.clear()
            if dpg.does_item_exist("graph_canvas"):
                dpg.delete_item("graph_canvas", children_only=True)
            self.add_to_log("🗺️ Graph cleared")
        except Exception as e:
            self.logger.error(f"Error clearing graph: {e}")
    
    def export_graph(self):
        """Экспорт графа"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"network_map_{timestamp}.json"
            
            export_data = {
                'nodes': list(self.graph.nodes.values()),
                'edges': self.graph.edges,
                'export_time': timestamp
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            self.add_to_log(f"💾 Graph exported to {filename}")
        except Exception as e:
            self.logger.error(f"Error exporting graph: {e}")
            self.add_to_log(f"❌ Export failed: {str(e)}")
    
    def highlight_vulnerabilities(self):
        """Подсветка уязвимостей"""
        self.add_to_log("🔴 Highlighting vulnerabilities...")
    
    def load_vulnerable_targets(self):
        """Загрузка уязвимых целей"""
        self.add_to_log("🎯 Loading vulnerable targets...")
    
    def start_exploitation(self):
        """Запуск эксплуатации"""
        self.add_to_log("💥 Starting exploitation...")
    
    def scan_for_exploits(self):
        """Сканирование на наличие эксплойтов"""
        self.add_to_log("🔍 Scanning for exploits...")
    
    def add_selected_targets(self):
        """Добавить выбранные цели"""
        self.add_to_log("🎯 Adding selected targets...")
    
    def save_settings(self):
        """Сохранение настроек"""
        self.add_to_log("💾 Settings saved")
    
    def export_all_data(self):
        """Экспорт всех данных"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Экспорт графа
            graph_filename = f"network_map_{timestamp}.json"
            graph_data = {
                'nodes': list(self.graph.nodes.values()),
                'edges': self.graph.edges,
                'hosts': self.host_manager.hosts,
                'export_time': timestamp
            }
            
            with open(graph_filename, 'w') as f:
                json.dump(graph_data, f, indent=2)
            
            # Экспорт хостов
            hosts_filename = f"hosts_{timestamp}.csv"
            with open(hosts_filename, 'w') as f:
                f.write("IP,Hostname,Ports,OS,Status,Vulnerabilities,LastSeen\n")
                for ip, host in self.host_manager.hosts.items():
                    ports = ','.join(map(str, host['ports']))
                    vulns = ','.join(host['vulnerabilities'])
                    f.write(f"{ip},{host['hostname']},{ports},{host['os']},{host['status']},{vulns},{host['last_seen']}\n")
            
            self.add_to_log(f"📤 All data exported: {graph_filename}, {hosts_filename}")
        except Exception as e:
            self.logger.error(f"Error exporting all data: {e}")
            self.add_to_log(f"❌ Export failed: {str(e)}")
    
    def clear_everything(self):
        """Очистка всего"""
        try:
            self.clear_results()
            self.clear_graph()
            self.add_to_log("🧹 Everything cleared")
        except Exception as e:
            self.logger.error(f"Error clearing everything: {e}")
            self.add_to_log(f"❌ Error clearing everything: {e}")
    
    def run(self):
        """Запуск GUI"""
        try:
            self.logger.info("🚀 Запуск графического интерфейса...")
            
            while dpg.is_dearpygui_running():
                dpg.render_dearpygui_frame()
            
            self.destroy()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска GUI: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def destroy(self):
        """Уничтожение GUI"""
        try:
            self.logger.info("🧹 Очистка графического интерфейса...")
            # Исправляем ошибку с is_dearpygui_initialized
            try:
                dpg.destroy_context()
            except Exception as e:
                self.logger.warning(f"Warning during context destruction: {e}")
            self.logger.info("✅ Графический интерфейс уничтожен")
        except Exception as e:
            self.logger.error(f"❌ Ошибка уничтожения GUI: {e}")
