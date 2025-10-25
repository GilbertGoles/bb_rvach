"""
Главное окно RapidRecon в стиле Obsidian
"""
import dearpygui.dearpygui as dpg
from typing import Dict, Any, List, Optional
import time
import json
from datetime import datetime
import logging
import math

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

class GraphVisualization:
    """Визуализация графа в стиле Obsidian"""
    
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.node_counter = 0
        self.selected_node = None
    
    def draw_graph(self, width: int, height: int):
        """Отрисовка графа"""
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
                    color=[123, 97, 255, 100],
                    thickness=2,
                    parent="graph_canvas"
                )
        
        # Отрисовка узлов
        for node_id, node in self.nodes.items():
            pos = node['position']
            color = node['color']
            
            # Основной круг узла
            dpg.draw_circle(
                pos, node['radius'],
                fill=color,
                color=[255, 255, 255, 50] if node_id != self.selected_node else [255, 255, 0, 200],
                thickness=3 if node_id == self.selected_node else 2,
                parent="graph_canvas"
            )
            
            # Текст метки
            dpg.draw_text(
                [pos[0] - len(node['label']) * 3, pos[1] + node['radius'] + 5],
                node['label'],
                color=[220, 220, 220],
                size=12,
                parent="graph_canvas"
            )
    
    def add_node(self, node_data: Dict[str, Any]) -> int:
        """Добавить узел"""
        node_id = self.node_counter
        self.node_counter += 1
        
        # Цвета узлов по типам (в стиле Obsidian)
        type_colors = {
            'initial_target': [72, 199, 116],    # Зеленый
            'subdomain': [86, 156, 214],         # Синий
            'active_host': [255, 179, 64],       # Оранжевый
            'open_ports': [123, 97, 255],        # Фиолетовый
            'service': [158, 118, 255],          # Лавандовый
            'vulnerability': [255, 92, 87],      # Красный
            'exploitation': [255, 92, 87],       # Красный
            'exploitation_success': [255, 92, 87], # Ярко-красный
            'internal_scan': [64, 192, 192]      # Бирюзовый
        }
        
        # Позиционирование (простая круговая компоновка)
        angle = (node_id * 2 * math.pi / max(1, len(self.nodes)))
        radius = 150 + (len(self.nodes) * 10)
        center_x, center_y = 400, 300
        
        position = [
            center_x + radius * math.cos(angle),
            center_y + radius * math.sin(angle)
        ]
        
        self.nodes[node_id] = {
            'id': node_id,
            'label': self._truncate_label(node_data.get('data', 'Node')),
            'type': node_data.get('type', 'custom'),
            'data': node_data,
            'position': position,
            'radius': 20,
            'color': type_colors.get(node_data.get('type', 'custom'), [128, 128, 128])
        }
        
        return node_id
    
    def add_edge(self, source_id: int, target_id: int):
        """Добавить связь"""
        if source_id in self.nodes and target_id in self.nodes:
            self.edges.append({
                'source': source_id,
                'target': target_id
            })
    
    def _truncate_label(self, label: str, max_length: int = 15) -> str:
        """Обрезать длинные метки"""
        return label if len(label) <= max_length else label[:max_length-3] + "..."
    
    def clear(self):
        """Очистить граф"""
        self.nodes.clear()
        self.edges.clear()
        self.node_counter = 0
        self.selected_node = None

class ObsidianMainWindow:
    """
    Главный интерфейс RapidRecon в стиле Obsidian
    """
    
    def __init__(self, engine, module_manager):
        self.engine = engine
        self.module_manager = module_manager
        self.graph = GraphVisualization()
        self.is_scanning = False
        self.logger = logging.getLogger('RapidRecon.GUI')
        self.settings_window_open = False
        
        # Инициализация GUI
        self.setup_gui()
        
        # Применение темы
        self.theme = ObsidianTheme.setup_theme()
        dpg.bind_theme(self.theme)
    
    def setup_gui(self):
        """Настройка интерфейса в стиле Obsidian"""
        dpg.create_context()
        
        # Главное окно
        with dpg.window(
            tag="main_window",
            label="RapidRecon",
            width=1400,
            height=900,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            no_close=True
        ):
            # Боковая панель (как в Obsidian)
            with dpg.child_window(
                tag="sidebar",
                width=250,
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
        
        # Настройка viewport
        dpg.create_viewport(
            title='RapidRecon • Security Reconnaissance',
            width=1400,
            height=900,
            min_width=1000,
            min_height=700
        )
    
    def _setup_sidebar(self):
        """Боковая панель Obsidian"""
        # Логотип
        with dpg.group():
            dpg.add_spacer(height=20)
            dpg.add_text("RapidRecon", color=[123, 97, 255])
            dpg.add_text("Security Tool", color=[150, 150, 160])
            dpg.add_separator()
        
        # Навигация
        with dpg.collapsing_header(
            label="🧭 Navigation",
            default_open=True,
            closable=False
        ):
            dpg.add_button(
                label="🎯 Scan Control",
                width=-1,
                callback=lambda: self._switch_tab("scan_tab")
            )
            dpg.add_button(
                label="🌐 Network Graph", 
                width=-1,
                callback=lambda: self._switch_tab("graph_tab")
            )
            dpg.add_button(
                label="📊 Results",
                width=-1,
                callback=lambda: self._switch_tab("results_tab")
            )
            dpg.add_button(
                label="🔧 Modules",
                width=-1,
                callback=lambda: self._switch_tab("modules_tab")
            )
        
        # Быстрый запуск сканирования
        with dpg.collapsing_header(
            label="⚡ Quick Actions",
            default_open=True
        ):
            dpg.add_text("Target:", color=[150, 150, 160])
            dpg.add_input_text(
                tag="quick_target_input",
                hint="example.com / 192.168.1.1",
                width=-1
            )
            
            dpg.add_text("Scan Level:", color=[150, 150, 160])
            dpg.add_combo(
                tag="scan_level",
                items=["🚀 Stealth", "⚡ Normal", "💥 Aggressive", "🔥 Full Attack"],
                default_value="⚡ Normal",
                width=-1,
                callback=self._on_scan_level_change
            )
            
            dpg.add_button(
                label="▶️ Start Scan",
                tag="quick_scan_button",
                width=-1,
                callback=self.quick_start_scan
            )
            dpg.add_button(
                label="⏹️ Stop Scan", 
                tag="quick_stop_button",
                width=-1,
                callback=self.stop_scan,
                show=False
            )
        
        # Профили сканирования
        with dpg.collapsing_header(
            label="📋 Scan Profiles",
            default_open=True
        ):
            profiles = self.engine.get_available_profiles()
            for profile in profiles:
                dpg.add_button(
                    label=f"• {profile.title()}",
                    width=-1,
                    callback=lambda s, d, p=profile: self._set_profile(p)
                )
        
        # Статистика
        with dpg.collapsing_header(
            label="📈 Quick Stats",
            default_open=True
        ):
            dpg.add_text("Nodes: 0", tag="stat_nodes")
            dpg.add_text("Targets: 0", tag="stat_targets")
            dpg.add_text("Vulnerabilities: 0", tag="stat_vulns")
            dpg.add_text("Exploits: 0", tag="stat_exploits")
        
        # Действия
        with dpg.group():
            dpg.add_separator()
            dpg.add_button(
                label="⚙️ Settings",
                width=-1,
                callback=self.show_settings
            )
            dpg.add_button(
                label="📤 Export Data", 
                width=-1,
                callback=self.export_results
            )
    
    def _setup_content_area(self):
        """Основная область контента"""
        with dpg.tab_bar(tag="main_tabs"):
            # Вкладка сканирования
            with dpg.tab(label="🎯 Scan", tag="scan_tab"):
                self._setup_scan_tab()
            
            # Вкладка графа
            with dpg.tab(label="🌐 Graph", tag="graph_tab"):
                self._setup_graph_tab()
            
            # Вкладка результатов
            with dpg.tab(label="📊 Results", tag="results_tab"):
                self._setup_results_tab()
            
            # Вкладка модулей
            with dpg.tab(label="🔧 Modules", tag="modules_tab"):
                self._setup_modules_tab()
    
    def _setup_scan_tab(self):
        """Вкладка управления сканированием"""
        # Основная панель сканирования
        with dpg.group():
            dpg.add_text("Advanced Scan Configuration", color=[123, 97, 255])
            
            with dpg.group(horizontal=True):
                with dpg.child_window(width=400):
                    dpg.add_text("Target Configuration")
                    dpg.add_input_text(
                        tag="target_input",
                        hint="Enter domain, IP or range...",
                        width=-1
                    )
                    
                    dpg.add_text("Scan Type")
                    dpg.add_combo(
                        tag="scan_type",
                        items=["Full Reconnaissance", "Subdomain Discovery", "Port Scanning", "Vulnerability Assessment"],
                        default_value="Full Reconnaissance",
                        width=-1
                    )
                
                with dpg.child_window(width=400):
                    dpg.add_text("Performance Settings")
                    dpg.add_slider_int(
                        label="Threads",
                        tag="thread_count",
                        default_value=10,
                        min_value=1,
                        max_value=50
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
                dpg.add_button(label="🔄 Refresh Graph", callback=self.update_graph)
                dpg.add_button(label="🧹 Clear Graph", callback=self.clear_graph)
                dpg.add_button(label="💾 Export Graph", callback=self.export_graph)
                dpg.add_text("Zoom:")
                dpg.add_slider_float(
                    tag="graph_zoom",
                    default_value=1.0,
                    min_value=0.5,
                    max_value=2.0,
                    width=100
                )
            
            # Область графа
            with dpg.child_window(
                tag="graph_container",
                height=600,
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
            with dpg.child_window(width=400):
                dpg.add_text("Discovered Nodes")
                dpg.add_tree_node(
                    tag="nodes_tree",
                    label="Network Structure",
                    default_open=True
                )
            
            # Детальная информация
            with dpg.child_window():
                dpg.add_text("Node Details")
                dpg.add_input_text(
                    tag="node_details",
                    multiline=True,
                    height=400,
                    readonly=True,
                    width=-1
                )
    
    def _setup_modules_tab(self):
        """Вкладка модулей"""
        with dpg.group():
            dpg.add_text("Available Modules")
            dpg.add_listbox(
                tag="modules_list",
                items=list(self.engine.active_modules.keys()),
                num_items=15,
                width=-1
            )
            
            dpg.add_text("Module Information", tag="module_info_title")
            dpg.add_input_text(
                tag="module_info",
                multiline=True,
                height=200,
                readonly=True,
                width=-1
            )
    
    def _setup_settings_window(self):
        """Окно настроек"""
        with dpg.window(
            tag="settings_window",
            label="Settings",
            width=600,
            height=500,
            show=False,
            pos=[100, 100]
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
                    dpg.add_text("Scanning Settings")
                    dpg.add_slider_int(
                        tag="settings_default_threads",
                        label="Default Threads",
                        default_value=10,
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
                    dpg.add_checkbox(
                        tag="settings_follow_redirects",
                        label="Follow Redirects",
                        default_value=True
                    )
                
                # Вкладка модулей
                with dpg.tab(label="Modules"):
                    dpg.add_text("Module Settings")
                    dpg.add_checkbox(
                        tag="settings_auto_load",
                        label="Auto-load modules",
                        default_value=True
                    )
                    dpg.add_checkbox(
                        tag="settings_auto_update",
                        label="Auto-update modules",
                        default_value=False
                    )
            
            # Кнопки настроек
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="💾 Save Settings",
                    callback=self.save_settings
                )
                dpg.add_button(
                    label="❌ Close",
                    callback=lambda: dpg.hide_item("settings_window")
                )
    
    def _switch_tab(self, tab_name: str):
        """Переключение вкладок"""
        dpg.set_value("main_tabs", tab_name)
    
    def _set_profile(self, profile_name: str):
        """Установка профиля сканирования"""
        if self.engine.set_scan_profile(profile_name):
            self.add_to_log(f"📋 Profile set to: {profile_name}")
    
    def _on_scan_level_change(self):
        """Обработчик изменения уровня сканирования"""
        scan_level = dpg.get_value("scan_level")
        level_map = {
            "🚀 Stealth": "stealth",
            "⚡ Normal": "normal", 
            "💥 Aggressive": "aggressive",
            "🔥 Full Attack": "aggressive"
        }
        profile = level_map.get(scan_level, "normal")
        self._set_profile(profile)
        self.add_to_log(f"🎛️ Scan level: {scan_level}")
    
    def quick_start_scan(self):
        """Быстрый запуск сканирования из боковой панели"""
        target = dpg.get_value("quick_target_input")
        if not target:
            self.add_to_log("❌ Please enter a target in the sidebar")
            return
        
        # Устанавливаем уровень сканирования
        self._on_scan_level_change()
        
        self.start_scan_with_target(target)
    
    def start_scan_with_target(self, target: str):
        """Запуск сканирования с указанной целью"""
        self.is_scanning = True
        self._update_ui_state()
        
        # Применяем настройки
        self.engine.rate_limit = dpg.get_value("rate_limit") if dpg.does_item_exist("rate_limit") else 10
        self.engine.max_depth = dpg.get_value("max_depth") if dpg.does_item_exist("max_depth") else 5
        
        # Запускаем сканирование
        self.engine.add_initial_target(target)
        
        self.add_to_log(f"🚀 Started scanning: {target}")
        dpg.set_value("status_text", "Status: Scanning...")
    
    def start_scan(self):
        """Запуск сканирования из основной вкладки"""
        target = dpg.get_value("target_input")
        if not target:
            self.add_to_log("❌ Please enter a target")
            return
        
        self.start_scan_with_target(target)
    
    def stop_scan(self):
        """Остановка сканирования"""
        self.engine.stop_engine()
        self.is_scanning = False
        self._update_ui_state()
        dpg.set_value("status_text", "Status: Stopped")
        self.add_to_log("⏹️ Scan stopped")
    
    def _update_ui_state(self):
        """Обновление состояния UI"""
        # Боковая панель
        dpg.configure_item("quick_scan_button", show=not self.is_scanning)
        dpg.configure_item("quick_stop_button", show=self.is_scanning)
        
        # Основная вкладка
        if dpg.does_item_exist("adv_scan_button"):
            dpg.configure_item("adv_scan_button", show=not self.is_scanning)
        if dpg.does_item_exist("adv_stop_button"):
            dpg.configure_item("adv_stop_button", show=self.is_scanning)
    
    def show_settings(self):
        """Показать окно настроек"""
        dpg.show_item("settings_window")
        dpg.bring_item_to_front("settings_window")
    
    def save_settings(self):
        """Сохранение настроек"""
        self.add_to_log("⚙️ Settings saved")
        dpg.hide_item("settings_window")
    
    def clear_results(self):
        """Очистка результатов"""
        self.graph.clear()
        dpg.delete_item("graph_canvas", children_only=True)
        dpg.set_value("activity_log", "")
        dpg.set_value("node_details", "")
        self.add_to_log("🧹 Results cleared")
    
    def add_to_log(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        current_log = dpg.get_value("activity_log")
        new_log = log_entry + (current_log or "")
        dpg.set_value("activity_log", new_log)
    
    def update_graph(self):
        """Обновление графа"""
        self.graph.clear()
        
        # Добавляем узлы из движка
        node_map = {}
        for node in self.engine.discovered_nodes:
            node_id = self.graph.add_node({
                'type': node.type.value,
                'data': node.data,
                'depth': node.depth
            })
            node_map[node.node_id] = node_id
        
        # Добавляем связи
        for node in self.engine.discovered_nodes:
            if node.source and node.source in node_map:
                self.graph.add_edge(
                    node_map[node.source],
                    node_map[node.node_id]
                )
        
        # Перерисовываем граф
        dpg.delete_item("graph_canvas", children_only=True)
        self.graph.draw_graph(800, 600)
    
    def clear_graph(self):
        """Очистка графа"""
        self.graph.clear()
        dpg.delete_item("graph_canvas", children_only=True)
        self.add_to_log("🧹 Graph cleared")
    
    def export_results(self):
        """Экспорт результатов"""
        filename = f"rapidrecon_export_{int(time.time())}.json"
        self.engine.export_results(filename)
        self.add_to_log(f"💾 Results exported to: {filename}")
    
    def export_graph(self):
        """Экспорт графа"""
        graph_data = {
            'nodes': list(self.graph.nodes.values()),
            'edges': self.graph.edges
        }
        filename = f"rapidrecon_graph_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump(graph_data, f, indent=2)
        self.add_to_log(f"🌐 Graph exported to: {filename}")
    
    def handle_engine_event(self, event_type: str, data: Any = None):
        """Обработчик событий движка"""
        try:
            if event_type in ['node_discovered', 'node_added']:
                node_data = data.data if data else 'Unknown'
                self.add_to_log(f"🔍 Discovered: {node_data}")
                self.update_graph()
            elif event_type == 'scan_completed':
                self.add_to_log("✅ Scan completed")
                self.is_scanning = False
                self._update_ui_state()
                if dpg.does_item_exist("status_text"):
                    dpg.set_value("status_text", "Status: Completed")
            elif event_type == 'vulnerability_found':
                self.add_to_log(f"🔴 Vulnerability: {data.get('cve', 'Unknown')}")
            elif event_type == 'exploitation_success':
                self.add_to_log(f"💥 Exploitation success: {data.get('access_type', 'Unknown')}")
            
            # Обновляем статистику
            self._update_statistics()
            
        except Exception as e:
            self.logger.error(f"Error handling engine event: {e}")
    
    def _update_statistics(self):
        """Обновление статистики"""
        stats = self.engine.get_statistics()
        dpg.set_value("stat_nodes", f"Nodes: {stats.get('discovered_nodes', 0)}")
        dpg.set_value("stat_targets", f"Targets: {stats.get('total_scans', 0)}")
        dpg.set_value("stat_vulns", f"Vulnerabilities: {stats.get('vulnerabilities_found', 0)}")
        dpg.set_value("stat_exploits", f"Exploits: {stats.get('exploits_successful', 0)}")
    
    def run(self):
        """Запуск GUI"""
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        
        # Главный цикл
        while dpg.is_dearpygui_running():
            # Периодическое обновление статистики
            if self.is_scanning:
                self._update_statistics()
            dpg.render_dearpygui_frame()
        
        dpg.destroy_context()

# Сохраняем как основной MainWindow для совместимости
MainWindow = ObsidianMainWindow
