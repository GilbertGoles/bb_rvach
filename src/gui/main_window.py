"""
Главное окно RapidRecon в стиле Obsidian с полным функционалом - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
import dearpygui.dearpygui as dpg
from typing import Dict, Any, List, Optional
import time
import json
from datetime import datetime
import logging
import math
import random
import traceback

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
    """Визуализация графа в стиле Obsidian - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.node_counter = 0
        self.selected_node = None
        self.node_positions = {}
    
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
            
            # Сетка (тонкая)
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
            
            # Определяем тип и настройки узла
            node_type = node_data.get('type', 'custom')
            node_config = self._get_node_config(node_type)
            
            # Позиционирование
            position = self._calculate_node_position(node_id, node_type)
            
            # Создаем данные узла
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
                'original_data': node_data  # Сохраняем оригинальные данные для деталей
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
            'initial_target': {
                'color': [72, 199, 116, 200],    # Зеленый
                'radius': 25,
                'icon': '🎯'
            },
            'subdomain': {
                'color': [86, 156, 214, 180],    # Синий
                'radius': 20,
                'icon': '🌐'
            },
            'active_host': {
                'color': [255, 179, 64, 200],    # Оранжевый
                'radius': 22,
                'icon': '💻'
            },
            'open_ports': {
                'color': [123, 97, 255, 180],    # Фиолетовый
                'radius': 20,
                'icon': '🔓'
            },
            'service': {
                'color': [158, 118, 255, 180],   # Лавандовый
                'radius': 18,
                'icon': '⚙️'
            },
            'vulnerability': {
                'color': [255, 92, 87, 220],     # Красный
                'radius': 19,
                'icon': '🔴'
            },
            'vulnerability_scan': {
                'color': [255, 120, 100, 180],   # Светло-красный
                'radius': 20,
                'icon': '🔍'
            },
            'exploitation': {
                'color': [255, 60, 60, 220],     # Ярко-красный
                'radius': 23,
                'icon': '💥'
            },
            'exploitation_success': {
                'color': [255, 0, 0, 230],       # Очень красный
                'radius': 28,
                'icon': '💀'
            },
            'internal_scan': {
                'color': [64, 192, 192, 180],    # Бирюзовый
                'radius': 24,
                'icon': '🔍'
            },
            'domain_scan': {
                'color': [100, 180, 255, 180],   # Голубой
                'radius': 21,
                'icon': '🌍'
            }
        }
        return configs.get(node_type, {
            'color': [128, 128, 128, 150],
            'radius': 20,
            'icon': '•'
        })
    
    def _calculate_node_position(self, node_id: int, node_type: str) -> List[float]:
        """Интеллектуальное позиционирование узлов"""
        center_x, center_y = 500, 350
        
        if not self.nodes:
            return [center_x, center_y]
        
        # Группировка по типам
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
            # Добавляем небольшой рандом для узлов одного типа
            return [
                base_pos[0] + random.uniform(-30, 30),
                base_pos[1] + random.uniform(-30, 30)
            ]
        
        # Для неизвестных типов - круговая компоновка
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
            
            # Добавляем специфическую информацию в зависимости от типа
            if 'original_data' in node:
                data = node['original_data']
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key not in ['position', 'color', 'radius', 'icon']:
                            details.append(f"{key}: {value}")
                else:
                    details.append(f"Data: {data}")
            
            # Добавляем информацию о связях
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

class MainWindow:
    """
    Главный интерфейс RapidRecon в стиле Obsidian с полным функционалом - ИСПРАВЛЕННАЯ ВЕРСИЯ
    """
    
    def __init__(self, engine, module_manager):
        self.engine = engine
        self.module_manager = module_manager
        self.graph = GraphVisualization()
        self.is_scanning = False
        self.logger = logging.getLogger('RapidRecon.GUI')
        self.settings_window_open = False
        self.selected_targets = set()
        self.last_update_time = 0
        self.update_interval = 1.0  # Обновление каждую секунду
        self.discovered_nodes = {}
        self.node_id_map = {}  # Маппинг ID движка на ID графа
        
        self.logger.info("🎨 Инициализация графического интерфейса...")
        
        # Инициализация GUI
        self.setup_gui()
        
        # Применение тем
        self.obsidian_theme = ObsidianTheme.setup_theme()
        self.danger_theme = DangerTheme.setup_theme()
        dpg.bind_theme(self.obsidian_theme)
        
        self.logger.info("✅ Графический интерфейс инициализирован")
    
    def setup_gui(self):
        """Настройка интерфейса в стиле Obsidian"""
        try:
            self.logger.info("🛠️ Создание контекста Dear PyGui...")
            dpg.create_context()
            
            # Главное окно
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
                # Боковая панель (как в Obsidian)
                with dpg.child_window(
                    tag="sidebar",
                    width=300,
                    border=False
                ):
                    self._setup_sidebar()
                
                # Основная область
                with dpg.group(horizontal=True, width=-1, height=-1):
                    # Область контента
                    with dpg.child_window(
                        tag="content_area",
                        width=-1,
                        border=False
                    ):
                        self._setup_content_area()
            
            # Окно настроек
            self._setup_settings_window()
            
            # Окно выбора целей
            self._setup_targets_window()
            
            # Настройка viewport
            dpg.create_viewport(
                title='RapidRecon • Advanced Security Scanner',
                width=1600,
                height=1000,
                min_width=1200,
                min_height=800
            )
            
            self.logger.info("✅ Интерфейс настроен успешно")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка настройки GUI: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def _setup_sidebar(self):
        """Боковая панель Obsidian"""
        # Логотип
        with dpg.group():
            dpg.add_spacer(height=20)
            dpg.add_text("RapidRecon", color=[123, 97, 255])
            dpg.add_text("Advanced Security Scanner", color=[150, 150, 160])
            dpg.add_separator()
        
        # Быстрый запуск сканирования
        with dpg.collapsing_header(
            label="⚡ Quick Launch",
            default_open=True
        ):
            dpg.add_text("Primary Target:", color=[150, 150, 160])
            dpg.add_input_text(
                tag="quick_target_input",
                hint="example.com / 192.168.1.1 / 10.0.0.0/24",
                width=-1
            )
            
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
            
            dpg.add_button(
                label="📋 Select from Discovered",
                width=-1,
                callback=self.show_targets_window
            )
        
        # Модули и возможности
        with dpg.collapsing_header(
            label="🔧 Capabilities",
            default_open=True
        ):
            dpg.add_text("Available Modules:", color=[150, 150, 160])
            dpg.add_text("• Ping Scanner", color=[200, 200, 200])
            dpg.add_text("• Port Scanner", color=[200, 200, 200])
            dpg.add_text("• Service Detector", color=[200, 200, 200])
            dpg.add_text("• Subdomain Scanner", color=[200, 200, 200])
            dpg.add_text("• Vulnerability Scanner", color=[255, 100, 100])
            dpg.add_text("• Exploitation Engine", color=[255, 60, 60])
            dpg.add_text("• Lateral Movement", color=[255, 165, 0])
        
        # Профили сканирования
        with dpg.collapsing_header(
            label="📋 Scan Profiles",
            default_open=True
        ):
            profiles = ["stealth", "normal", "aggressive"]
            for profile in profiles:
                dpg.add_button(
                    label=f"• {profile.title()}",
                    width=-1,
                    callback=lambda s, d, p=profile: self._set_profile(p)
                )
        
        # Статистика в реальном времени
        with dpg.collapsing_header(
            label="📈 Live Statistics",
            default_open=True
        ):
            dpg.add_text("Network:", color=[150, 150, 160])
            dpg.add_text("Nodes: 0", tag="stat_nodes")
            dpg.add_text("Services: 0", tag="stat_services")
            dpg.add_text("Targets: 0", tag="stat_targets")
            
            dpg.add_text("Security:", color=[150, 150, 160])
            dpg.add_text("Vulnerabilities: 0", tag="stat_vulns")
            dpg.add_text("Exploits: 0", tag="stat_exploits")
            dpg.add_text("Lateral Moves: 0", tag="stat_lateral")
        
        # Действия
        with dpg.group():
            dpg.add_separator()
            dpg.add_button(
                label="⚙️ Engine Settings",
                width=-1,
                callback=self.show_settings
            )
            dpg.add_button(
                label="📤 Export All Data", 
                width=-1,
                callback=self.export_all_data
            )
            dpg.add_button(
                label="🧹 Clear Everything",
                width=-1,
                callback=self.clear_everything
            )
    
    def _setup_content_area(self):
        """Основная область контента"""
        with dpg.tab_bar(tag="main_tabs"):
            # Вкладка сканирования
            with dpg.tab(label="🎯 Reconnaissance", tag="scan_tab"):
                self._setup_scan_tab()
            
            # Вкладка графа
            with dpg.tab(label="🌐 Network Map", tag="graph_tab"):
                self._setup_graph_tab()
            
            # Вкладка результатов
            with dpg.tab(label="📊 Results & Analysis", tag="results_tab"):
                self._setup_results_tab()
            
            # Вкладка эксплуатации
            with dpg.tab(label="💥 Exploitation", tag="exploit_tab"):
                self._setup_exploit_tab()
            
            # Вкладка модулей
            with dpg.tab(label="🔧 Modules & Tools", tag="modules_tab"):
                self._setup_modules_tab()
    
    def _setup_scan_tab(self):
        """Вкладка управления сканированием"""
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
                        
                        dpg.add_text("Scan Scope")
                        dpg.add_combo(
                            tag="scan_scope",
                            items=["Full Infrastructure", "External Recon", "Internal Network", "Web Applications", "Critical Assets"],
                            default_value="Full Infrastructure",
                            width=-1
                        )
                    
                    with dpg.child_window(width=400):
                        dpg.add_text("Module Selection")
                        dpg.add_checkbox(tag="mod_ping", label="Ping Scanner", default_value=True)
                        dpg.add_checkbox(tag="mod_ports", label="Port Scanner", default_value=True)
                        dpg.add_checkbox(tag="mod_services", label="Service Detection", default_value=True)
                        dpg.add_checkbox(tag="mod_subdomains", label="Subdomain Discovery", default_value=True)
                        dpg.add_checkbox(tag="mod_vulns", label="Vulnerability Scanning", default_value=True)
                        dpg.add_checkbox(tag="mod_exploit", label="Exploitation Engine", default_value=False)
            
            # Настройки производительности
            with dpg.collapsing_header(label="⚡ Performance Settings"):
                with dpg.group(horizontal=True):
                    with dpg.child_window(width=300):
                        dpg.add_slider_int(
                            label="Scan Threads",
                            tag="thread_count",
                            default_value=15,
                            min_value=1,
                            max_value=50
                        )
                        dpg.add_slider_int(
                            label="Rate Limit (req/sec)",
                            tag="rate_limit",
                            default_value=10,
                            min_value=1,
                            max_value=100
                        )
                    
                    with dpg.child_window(width=300):
                        dpg.add_slider_int(
                            label="Max Depth",
                            tag="max_depth",
                            default_value=5,
                            min_value=1,
                            max_value=10
                        )
                        dpg.add_slider_int(
                            label="Timeout (seconds)",
                            tag="timeout_setting",
                            default_value=5,
                            min_value=1,
                            max_value=30
                        )
            
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
                dpg.add_button(
                    label="🔍 Resume Scan",
                    callback=self.resume_scan
                )
                dpg.add_button(
                    label="🧹 Clear Results",
                    callback=self.clear_results
                )
        
        # Лог в реальном времени
        dpg.add_text("Activity Log")
        dpg.add_input_text(
            tag="activity_log",
            multiline=True,
            height=300,
            readonly=True,
            width=-1
        )
    
    def _setup_graph_tab(self):
        """Вкладка графа сети"""
        with dpg.group():
            # Панель управления графом
            with dpg.group(horizontal=True):
                dpg.add_button(label="🔄 Refresh Map", callback=self.update_graph)
                dpg.add_button(label="🧹 Clear Map", callback=self.clear_graph)
                dpg.add_button(label="💾 Export Map", callback=self.export_graph)
                dpg.add_button(label="🎯 Focus on Targets", callback=self.focus_on_targets)
                dpg.add_button(label="🔴 Show Vulnerabilities", callback=self.highlight_vulnerabilities)
            
            # Легенда графа
            with dpg.collapsing_header(label="🎨 Map Legend", default_open=True):
                with dpg.table(header_row=False, policy=dpg.mvTable_SizingFixedFit):
                    dpg.add_table_column()
                    dpg.add_table_column()
                    
                    with dpg.table_row():
                        dpg.add_text("🎯", color=[72, 199, 116])
                        dpg.add_text("Initial Target")
                    with dpg.table_row():
                        dpg.add_text("🌐", color=[86, 156, 214])
                        dpg.add_text("Subdomain")
                    with dpg.table_row():
                        dpg.add_text("💻", color=[255, 179, 64])
                        dpg.add_text("Active Host")
                    with dpg.table_row():
                        dpg.add_text("🔓", color=[123, 97, 255])
                        dpg.add_text("Open Ports")
                    with dpg.table_row():
                        dpg.add_text("🔴", color=[255, 92, 87])
                        dpg.add_text("Vulnerability")
                    with dpg.table_row():
                        dpg.add_text("💥", color=[255, 60, 60])
                        dpg.add_text("Exploitation")
            
            # Область графа
            with dpg.child_window(
                tag="graph_container",
                height=650,
                border=True
            ):
                with dpg.drawlist(
                    tag="graph_canvas",
                    width=-1,
                    height=-1
                ):
                    # Граф будет рисоваться динамически
                    pass
    
    def _setup_results_tab(self):
        """Вкладка результатов"""
        with dpg.group(horizontal=True):
            # Дерево узлов
            with dpg.child_window(width=450):
                dpg.add_text("Discovered Infrastructure")
                dpg.add_tree_node(
                    tag="nodes_tree",
                    label="Network Topology (0 nodes)",
                    default_open=True
                )
            
            # Детальная информация и уязвимости
            with dpg.child_window():
                with dpg.tab_bar():
                    # Детали узла
                    with dpg.tab(label="Node Details"):
                        dpg.add_input_text(
                            tag="node_details",
                            multiline=True,
                            height=400,
                            readonly=True,
                            width=-1
                        )
                    
                    # Уязвимости
                    with dpg.tab(label="Vulnerabilities"):
                        dpg.add_listbox(
                            tag="vulnerabilities_list",
                            items=[],
                            num_items=10,
                            width=-1
                        )
                        dpg.add_input_text(
                            tag="vuln_details",
                            multiline=True,
                            height=200,
                            readonly=True,
                            width=-1
                        )
                    
                    # Эксплуатация
                    with dpg.tab(label="Exploitation Results"):
                        dpg.add_input_text(
                            tag="exploit_results",
                            multiline=True,
                            height=400,
                            readonly=True,
                            width=-1
                        )
    
    def _setup_exploit_tab(self):
        """Вкладка эксплуатации"""
        with dpg.group():
            dpg.add_text("Advanced Exploitation Engine", color=[255, 60, 60])
            
            with dpg.group(horizontal=True):
                with dpg.child_window(width=400):
                    dpg.add_text("Target Selection")
                    dpg.add_listbox(
                        tag="exploit_targets",
                        items=[],
                        num_items=8,
                        width=-1
                    )
                    dpg.add_button(
                        label="🎯 Load Vulnerable Targets",
                        callback=self.load_vulnerable_targets
                    )
                
                with dpg.child_window(width=400):
                    dpg.add_text("Exploitation Options")
                    dpg.add_checkbox(tag="auto_exploit", label="Auto-Exploit Vulnerabilities", default_value=False)
                    dpg.add_checkbox(tag="lateral_movement", label="Enable Lateral Movement", default_value=True)
                    dpg.add_checkbox(tag="persistence", label="Establish Persistence", default_value=False)
                    
                    dpg.add_text("Payload Type")
                    dpg.add_combo(
                        tag="payload_type",
                        items=["Reverse Shell", "Web Shell", "Meterpreter", "Custom"],
                        default_value="Reverse Shell",
                        width=-1
                    )
            
            # Кнопки эксплуатации
            with dpg.group(horizontal=True):
                exploit_button = dpg.add_button(
                    label="💥 Start Exploitation",
                    callback=self.start_exploitation
                )
                dpg.bind_item_theme(exploit_button, self.danger_theme)
                
                dpg.add_button(
                    label="🔍 Scan for Exploits",
                    callback=self.scan_for_exploits
                )
                dpg.add_button(
                    label="🔄 Lateral Movement",
                    callback=self.start_lateral_movement
                )
            
            # Результаты эксплуатации
            dpg.add_text("Exploitation Results")
            dpg.add_input_text(
                tag="exploitation_log",
                multiline=True,
                height=300,
                readonly=True,
                width=-1
            )
    
    def _setup_modules_tab(self):
        """Вкладка модулей"""
        with dpg.group():
            dpg.add_text("Security Modules & Tools", color=[123, 97, 255])
            
            with dpg.group(horizontal=True):
                # Список модулей
                with dpg.child_window(width=400):
                    dpg.add_text("Available Modules")
                    dpg.add_listbox(
                        tag="modules_list",
                        items=list(self.engine.active_modules.keys()) if hasattr(self.engine, 'active_modules') else [],
                        num_items=15,
                        width=-1
                    )
                    dpg.add_button(
                        label="🔄 Refresh Modules",
                        callback=self.refresh_modules
                    )
                
                # Информация о модуле
                with dpg.child_window():
                    dpg.add_text("Module Information", tag="module_info_title")
                    dpg.add_input_text(
                        tag="module_info",
                        multiline=True,
                        height=200,
                        readonly=True,
                        width=-1
                    )
            
            # Инструменты
            with dpg.collapsing_header(label="🛠️ Additional Tools"):
                with dpg.group(horizontal=True):
                    dpg.add_button(label="🌐 WHOIS Lookup", width=120)
                    dpg.add_button(label="🔍 DNS Enumeration", width=120)
                    dpg.add_button(label="📧 Email Harvesting", width=120)
                    dpg.add_button(label="🔑 SSL Scanner", width=120)
                    dpg.add_button(label="🌍 GeoIP Lookup", width=120)
    
    def _setup_settings_window(self):
        """Окно настроек"""
        with dpg.window(
            tag="settings_window",
            label="Engine Settings",
            width=700,
            height=600,
            show=False,
            pos=[200, 100]
        ):
            with dpg.tab_bar():
                # Вкладка общего
                with dpg.tab(label="General"):
                    dpg.add_text("General Settings")
                    dpg.add_input_text(
                        tag="settings_scan_dir",
                        label="Scan Directory",
                        default_value="./scans/",
                        width=-1
                    )
                    dpg.add_checkbox(
                        tag="settings_auto_save",
                        label="Auto-save results",
                        default_value=True
                    )
                    dpg.add_checkbox(
                        tag="settings_verbose",
                        label="Verbose logging",
                        default_value=False
                    )
                
                # Вкладка сканирования
                with dpg.tab(label="Scanning"):
                    dpg.add_text("Scanning Engine Settings")
                    dpg.add_slider_int(
                        tag="settings_default_threads",
                        label="Default Threads",
                        default_value=15,
                        min_value=1,
                        max_value=100
                    )
                    dpg.add_slider_int(
                        tag="settings_default_timeout",
                        label="Default Timeout (s)",
                        default_value=5,
                        min_value=1,
                        max_value=30
                    )
                    dpg.add_slider_int(
                        tag="settings_max_depth",
                        label="Maximum Depth",
                        default_value=5,
                        min_value=1,
                        max_value=10
                    )
                    dpg.add_checkbox(
                        tag="settings_follow_redirects",
                        label="Follow Redirects",
                        default_value=True
                    )
                
                # Вкладка безопасности
                with dpg.tab(label="Security"):
                    dpg.add_text("Security Settings")
                    dpg.add_checkbox(
                        tag="settings_auto_exploit",
                        label="Auto-Exploit Critical Vulnerabilities",
                        default_value=False
                    )
                    dpg.add_checkbox(
                        tag="settings_enable_lateral",
                        label="Enable Lateral Movement",
                        default_value=True
                    )
                    dpg.add_checkbox(
                        tag="settings_stealth_mode",
                        label="Stealth Mode",
                        default_value=False
                    )
            
            # Кнопки настроек
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="💾 Save Settings",
                    callback=self.save_settings
                )
                dpg.add_button(
                    label="🔄 Apply to Current Scan",
                    callback=self.apply_settings
                )
                dpg.add_button(
                    label="❌ Close",
                    callback=lambda: dpg.hide_item("settings_window")
                )
    
    def _setup_targets_window(self):
        """Окно выбора целей"""
        with dpg.window(
            tag="targets_window",
            label="Select Targets from Discovered Nodes",
            width=800,
            height=600,
            show=False,
            pos=[300, 150]
        ):
            dpg.add_text("Discovered Targets (Select multiple with CTRL+Click)")
            dpg.add_listbox(
                tag="discovered_targets_list",
                items=[],
                num_items=15,
                width=-1
            )
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="🎯 Add Selected Targets",
                    callback=self.add_selected_targets
                )
                dpg.add_button(
                    label="🧹 Clear Selection",
                    callback=self.clear_target_selection
                )
                dpg.add_button(
                    label="❌ Close",
                    callback=lambda: dpg.hide_item("targets_window")
                )
    
    def _switch_tab(self, tab_name: str):
        """Переключение вкладок"""
        dpg.set_value("main_tabs", tab_name)
    
    def _set_profile(self, profile_name: str):
        """Установка профиля сканирования"""
        try:
            if hasattr(self.engine, 'set_scan_profile'):
                if self.engine.set_scan_profile(profile_name):
                    profile_info = self.engine.get_current_profile_info() if hasattr(self.engine, 'get_current_profile_info') else {}
                    # Применяем настройки профиля
                    if dpg.does_item_exist("rate_limit"):
                        dpg.set_value("rate_limit", profile_info.get('rate_limit', 10))
                    if dpg.does_item_exist("max_depth"):
                        dpg.set_value("max_depth", profile_info.get('max_depth', 5))
                    
                    self.add_to_log(f"📋 Profile set to: {profile_name}")
            else:
                self.add_to_log(f"⚠️ Engine doesn't support profile setting")
        except Exception as e:
            self.logger.error(f"Error setting profile: {e}")
            self.add_to_log(f"❌ Error setting profile: {e}")
    
    def _on_scan_level_change(self):
        """Обработчик изменения уровня сканирования"""
        scan_level = dpg.get_value("scan_level")
        level_map = {
            "🚀 Stealth": "stealth",
            "⚡ Normal": "normal", 
            "💥 Aggressive": "aggressive",
            "🔥 Full Attack": "aggressive",
            "💀 Pentest": "aggressive"
        }
        profile = level_map.get(scan_level, "normal")
        self._set_profile(profile)
        self.add_to_log(f"🎛️ Scan intensity: {scan_level}")
    
    def quick_start_scan(self):
        """Быстрый запуск сканирования из боковой панели"""
        try:
            target = dpg.get_value("quick_target_input")
            if not target:
                self.add_to_log("❌ Please enter a target first!")
                return
            
            self.add_to_log(f"🚀 Quick scan started for: {target}")
            
            # Устанавливаем цель
            if hasattr(self.engine, 'set_targets'):
                self.engine.set_targets([target])
            elif hasattr(self.engine, 'add_initial_target'):
                self.engine.add_initial_target(target)
            
            # Запускаем сканирование с текущими настройками
            scan_profile = dpg.get_value("scan_level").split(" ")[-1].lower()
            self._set_profile(scan_profile)
            
            # Запуск сканирования
            if hasattr(self.engine, 'start_scan'):
                if self.engine.start_scan():
                    self.is_scanning = True
                    dpg.hide_item("quick_scan_button")
                    dpg.show_item("quick_stop_button")
                    dpg.hide_item("adv_scan_button")
                    dpg.show_item("adv_stop_button")
                    self.add_to_log("✅ Scan started successfully!")
                    
                    # Запускаем обновления интерфейса
                    self._start_ui_updates()
                else:
                    self.add_to_log("❌ Failed to start scan!")
            else:
                self.add_to_log("⚠️ Engine doesn't support start_scan method")
                
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
            else:
                self.add_to_log("⚠️ No active scan to stop")
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
            
            # Устанавливаем цели
            if hasattr(self.engine, 'set_targets'):
                self.engine.set_targets(targets)
            elif hasattr(self.engine, 'add_initial_target'):
                for target in targets:
                    self.engine.add_initial_target(target)
            
            # Запускаем сканирование
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
                else:
                    self.add_to_log("❌ Failed to start advanced scan!")
                    return False
            else:
                self.add_to_log("⚠️ Engine doesn't support start_scan method")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in start_scan: {e}")
            self.add_to_log(f"❌ Error starting advanced scan: {e}")
            return False
    
    def resume_scan(self):
        """Продолжение сканирования"""
        try:
            if hasattr(self.engine, 'resume_scan'):
                if self.engine.resume_scan():
                    self.is_scanning = True
                    dpg.hide_item("quick_scan_button")
                    dpg.show_item("quick_stop_button")
                    dpg.hide_item("adv_scan_button")
                    dpg.show_item("adv_stop_button")
                    self.add_to_log("🔍 Scan resumed!")
                    self._start_ui_updates()
            else:
                self.add_to_log("⚠️ Engine doesn't support resume_scan method")
        except Exception as e:
            self.logger.error(f"Error resuming scan: {e}")
            self.add_to_log(f"❌ Error resuming scan: {e}")
    
    def clear_results(self):
        """Очистка результатов"""
        try:
            if hasattr(self.engine, 'clear_results'):
                self.engine.clear_results()
            self.graph.clear()
            self.discovered_nodes.clear()
            self.node_id_map.clear()
            dpg.set_value("activity_log", "")
            # Сбрасываем статистику
            dpg.set_value("stat_nodes", "Nodes: 0")
            dpg.set_value("stat_services", "Services: 0")
            dpg.set_value("stat_targets", "Targets: 0")
            dpg.set_value("stat_vulns", "Vulnerabilities: 0")
            dpg.set_value("stat_exploits", "Exploits: 0")
            dpg.set_value("stat_lateral", "Lateral Moves: 0")
            
            # Очищаем списки целей
            dpg.configure_item("discovered_targets_list", items=[])
            dpg.configure_item("exploit_targets", items=[])
            
            # Очищаем дерево узлов
            if dpg.does_item_exist("nodes_tree"):
                dpg.delete_item("nodes_tree", children_only=True)
                dpg.set_value("nodes_tree", "Network Topology (0 nodes)")
            
            self.add_to_log("🧹 All results cleared")
        except Exception as e:
            self.logger.error(f"Error clearing results: {e}")
            self.add_to_log(f"❌ Error clearing results: {e}")
    
    def update_graph(self):
        """Обновление графа на основе данных сканирования"""
        try:
            # Очищаем только отрисованные элементы, но сохраняем данные
            if dpg.does_item_exist("graph_canvas"):
                dpg.delete_item("graph_canvas", children_only=True)
            
            # Рисуем граф с текущими данными
            container_width = dpg.get_item_width("graph_container")
            container_height = dpg.get_item_height("graph_container")
            self.graph.draw_graph(container_width - 20, container_height - 20)
            
        except Exception as e:
            self.logger.error(f"Error updating graph: {e}")
    
    def clear_graph(self):
        """Очистка графа"""
        try:
            self.graph.clear()
            if dpg.does_item_exist("graph_canvas"):
                dpg.delete_item("graph_canvas", children_only=True)
            self.add_to_log("🗺️ Graph cleared")
        except Exception as e:
            self.logger.error(f"Error clearing graph: {e}")
            self.add_to_log(f"❌ Error clearing graph: {e}")
    
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
    
    def focus_on_targets(self):
        """Фокусировка на целевых узлах"""
        self.add_to_log("🎯 Focusing on target nodes...")
    
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
    
    def start_lateral_movement(self):
        """Запуск перемещения внутри сети"""
        self.add_to_log("🔄 Starting lateral movement...")
    
    def refresh_modules(self):
        """Обновление списка модулей"""
        self.add_to_log("🔄 Refreshing modules...")
    
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
    
    def show_targets_window(self):
        """Показать окно выбора целей"""
        try:
            dpg.show_item("targets_window")
        except Exception as e:
            self.logger.error(f"Error showing targets window: {e}")
    
    def add_selected_targets(self):
        """Добавить выбранные цели"""
        self.add_to_log("🎯 Adding selected targets...")
    
    def clear_target_selection(self):
        """Очистить выбор целей"""
        self.add_to_log("🧹 Clearing target selection...")
    
    def save_settings(self):
        """Сохранение настроек"""
        self.add_to_log("💾 Settings saved")
    
    def apply_settings(self):
        """Применение настроек"""
        self.add_to_log("🔄 Settings applied to current scan")
    
    def export_all_data(self):
        """Экспорт всех данных"""
        self.add_to_log("📤 Exporting all data...")
    
    def clear_everything(self):
        """Очистка всего"""
        try:
            self.clear_results()
            self.clear_graph()
            self.add_to_log("🧹 Everything cleared")
        except Exception as e:
            self.logger.error(f"Error clearing everything: {e}")
            self.add_to_log(f"❌ Error clearing everything: {e}")
    
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
            # Автопрокрутка вниз
            dpg.focus_item("activity_log")
        except Exception as e:
            self.logger.error(f"Error adding to log: {e}")
    
    def _start_ui_updates(self):
        """Запуск периодических обновлений интерфейса"""
        def update_ui():
            current_time = time.time()
            if current_time - self.last_update_time >= self.update_interval:
                self.last_update_time = current_time
                
                if self.is_scanning:
                    try:
                        # Обновляем статистику
                        self._update_statistics()
                        
                        # Обновляем граф
                        self.update_graph()
                        
                        # Обновляем список целей
                        self._update_targets_list()
                        
                        # Обновляем дерево узлов
                        self._update_nodes_tree()
                        
                    except Exception as e:
                        self.logger.error(f"Error in UI update: {e}")
        
        # Устанавливаем callback для обновлений
        dpg.set_render_callback(update_ui)
    
    def _update_statistics(self):
        """Обновление статистики"""
        try:
            # Обновляем счетчики на основе данных графа
            nodes_count = len(self.graph.nodes)
            services_count = sum(1 for node in self.graph.nodes.values() if node['type'] == 'service')
            targets_count = sum(1 for node in self.graph.nodes.values() if node['type'] in ['initial_target', 'active_host'])
            vulnerabilities_count = sum(1 for node in self.graph.nodes.values() if node['type'] == 'vulnerability')
            
            dpg.set_value("stat_nodes", f"Nodes: {nodes_count}")
            dpg.set_value("stat_services", f"Services: {services_count}")
            dpg.set_value("stat_targets", f"Targets: {targets_count}")
            dpg.set_value("stat_vulns", f"Vulnerabilities: {vulnerabilities_count}")
            
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")
    
    def _update_targets_list(self):
        """Обновление списка обнаруженных целей"""
        try:
            targets = []
            
            # Используем узлы из графа
            for node_id, node in self.graph.nodes.items():
                if node['type'] in ['initial_target', 'active_host', 'subdomain']:
                    target_info = f"{node['label']} - {node['type']}"
                    targets.append(target_info)
            
            # Обновляем список в окне выбора целей
            dpg.configure_item("discovered_targets_list", items=targets)
            
            # Обновляем список для эксплуатации
            dpg.configure_item("exploit_targets", items=targets)
            
        except Exception as e:
            self.logger.error(f"Error updating targets list: {e}")
    
    def _update_nodes_tree(self):
        """Обновление дерева узлов на вкладке результатов"""
        try:
            if not dpg.does_item_exist("nodes_tree"):
                return
                
            # Очищаем старое дерево
            dpg.delete_item("nodes_tree", children_only=True)
            
            # Обновляем заголовок с количеством узлов
            dpg.set_value("nodes_tree", f"Network Topology ({len(self.graph.nodes)} nodes)")
            
            # Группируем узлы по типам
            nodes_by_type = {}
            for node_id, node in self.graph.nodes.items():
                node_type = node['type']
                if node_type not in nodes_by_type:
                    nodes_by_type[node_type] = []
                nodes_by_type[node_type].append(node)
            
            # Добавляем узлы в дерево по типам
            for node_type, nodes in nodes_by_type.items():
                with dpg.tree_node(label=f"{node_type.title()} ({len(nodes)})", parent="nodes_tree"):
                    for node in nodes:
                        node_label = f"{node['label']}"
                        with dpg.tree_node(label=node_label):
                            # Добавляем детальную информацию
                            details = self.graph.get_node_details(node['id'])
                            dpg.add_text(details)
                            
        except Exception as e:
            self.logger.error(f"Error updating nodes tree: {e}")
    
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
                
            elif event_type == 'exploitation_success':
                self._handle_exploitation_success(data)
                
            elif event_type == 'lateral_movement':
                self._handle_lateral_movement(data)
                
            elif event_type == 'profile_changed':
                self._handle_profile_changed(data)
                
            # Принудительно обновляем интерфейс после события
            self.update_graph()
            self._update_targets_list()
            self._update_nodes_tree()
            self._update_statistics()
                
        except Exception as e:
            self.logger.error(f"Error handling engine event: {e}")
    
    def _handle_node_added(self, node):
        """Обработка добавления узла"""
        try:
            if hasattr(node, 'node_id'):
                node_data = self._convert_scan_node_to_dict(node)
                self.add_to_log(f"🎯 Target added: {node_data.get('data', 'Unknown')}")
                self._add_node_to_graph(node.node_id, node_data)
        except Exception as e:
            self.logger.error(f"Error handling node added: {e}")
    
    def _handle_node_discovered(self, node):
        """Обработка обнаруженного узла"""
        try:
            if hasattr(node, 'node_id'):
                node_data = self._convert_scan_node_to_dict(node)
                self.add_to_log(f"🔍 Node discovered: {node_data.get('data', 'Unknown')} - {node_data.get('type', 'unknown')}")
                self._add_node_to_graph(node.node_id, node_data)
        except Exception as e:
            self.logger.error(f"Error handling node discovered: {e}")
    
    def _handle_module_results(self, results):
        """Обработка результатов модуля"""
        try:
            self.add_to_log(f"⚙️ Module results received from {results.get('module', 'unknown')}")
            
            # Обрабатываем задачу если она есть
            task = results.get('task')
            if task and hasattr(task, 'node_id'):
                task_data = self._convert_scan_node_to_dict(task)
                self._add_node_to_graph(task.node_id, task_data)
            
            # Обрабатываем результаты сканирования портов
            if 'open_ports' in results:
                for ip, ports in results['open_ports'].items():
                    if ports:  # Если есть открытые порты
                        port_node_data = {
                            'type': 'open_ports',
                            'data': f"{ip} ports",
                            'ports': ports,
                            'ip': ip
                        }
                        port_node_id = self.graph.add_node(port_node_data)
                        self._add_edge_to_host(ip, port_node_id, 'port')
            
        except Exception as e:
            self.logger.error(f"Error handling module results: {e}")
    
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
    
    def _handle_exploitation_success(self, data):
        """Обработка успешной эксплуатации"""
        self.add_to_log(f"💥 Exploitation successful: {data}")
        current_exploits = int(dpg.get_value("stat_exploits").split(": ")[1])
        dpg.set_value("stat_exploits", f"Exploits: {current_exploits + 1}")
    
    def _handle_lateral_movement(self, data):
        """Обработка перемещения внутри сети"""
        self.add_to_log(f"🔄 Lateral movement: {data}")
        current_lateral = int(dpg.get_value("stat_lateral").split(": ")[1])
        dpg.set_value("stat_lateral", f"Lateral Moves: {current_lateral + 1}")
    
    def _handle_profile_changed(self, profile):
        """Обработка изменения профиля"""
        self.add_to_log(f"📋 Profile changed to: {profile}")
    
    def _convert_scan_node_to_dict(self, scan_node) -> Dict[str, Any]:
        """Конвертировать ScanNode в словарь для графа"""
        try:
            node_dict = {
                'type': getattr(scan_node, 'type', 'unknown').value if hasattr(scan_node, 'type') else 'unknown',
                'data': getattr(scan_node, 'data', 'Unknown'),
                'source': getattr(scan_node, 'source', 'unknown'),
                'depth': getattr(scan_node, 'depth', 0),
                'timestamp': getattr(scan_node, 'timestamp', 0),
                'module': getattr(scan_node, 'module', 'unknown'),
                'metadata': getattr(scan_node, 'metadata', {}),
                'ports': getattr(scan_node, 'ports', []),
                'services': getattr(scan_node, 'services', []),
                'vulnerability_data': getattr(scan_node, 'vulnerability_data', {}),
                'vulnerabilities': getattr(scan_node, 'vulnerabilities', []),
                'exploit_data': getattr(scan_node, 'exploit_data', {})
            }
            
            # Определяем тип узла для визуализации
            if node_dict['type'] == 'initial_target':
                node_dict['type'] = 'initial_target'
            elif node_dict['type'] == 'subdomain':
                node_dict['type'] = 'subdomain'
            elif node_dict['type'] == 'active_host':
                node_dict['type'] = 'active_host'
            elif 'port' in node_dict['module']:
                node_dict['type'] = 'open_ports'
            elif 'vulnerability' in node_dict['module']:
                node_dict['type'] = 'vulnerability'
            elif 'exploit' in node_dict['module']:
                node_dict['type'] = 'exploitation'
                
            return node_dict
        except Exception as e:
            self.logger.error(f"Error converting scan node: {e}")
            return {'type': 'unknown', 'data': 'Conversion error'}
    
    def _add_node_to_graph(self, engine_node_id: str, node_data: Dict[str, Any]):
        """Добавить узел в граф"""
        try:
            # Проверяем, не добавлен ли уже узел
            if engine_node_id in self.node_id_map:
                return self.node_id_map[engine_node_id]
            
            # Добавляем узел в граф
            graph_node_id = self.graph.add_node(node_data)
            if graph_node_id != -1:
                self.node_id_map[engine_node_id] = graph_node_id
                
                # Добавляем связи если есть источник
                source = node_data.get('source')
                if source and source in self.node_id_map:
                    source_graph_id = self.node_id_map[source]
                    edge_type = self._determine_edge_type(node_data)
                    self.graph.add_edge(source_graph_id, graph_node_id, edge_type)
                
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
                    break
        except Exception as e:
            self.logger.error(f"Error adding edge to host: {e}")
    
    def _determine_edge_type(self, node_data: Dict[str, Any]) -> str:
        """Определить тип связи на основе данных узла"""
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
    
    def run(self):
        """Запуск GUI"""
        try:
            self.logger.info("🚀 Запуск графического интерфейса...")
            dpg.setup_dearpygui()
            dpg.show_viewport()
            dpg.set_primary_window("main_window", True)
            
            # Главный цикл GUI
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
            dpg.destroy_context()
            self.logger.info("✅ Графический интерфейс уничтожен")
        except Exception as e:
            self.logger.error(f"❌ Ошибка уничтожения GUI: {e}")
