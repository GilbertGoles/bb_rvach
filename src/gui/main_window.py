"""
Главное окно RapidRecon - модульная архитектура
"""
import dearpygui.dearpygui as dpg
from typing import Dict, Any, List, Optional
import logging
import traceback
import sys
import os
import time
import json
import csv
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from gui.network_tree import NetworkTree
from gui.hosts_table import HostsTable
from gui.scope_manager import ScopeManager
from gui.controls_panel import ControlsPanel

class ObsidianTheme:
    """Тема в стиле Obsidian"""
    
    @staticmethod
    def setup_theme():
        with dpg.theme() as obsidian_theme:
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
            
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, colors['bg_primary'])
                dpg.add_theme_color(dpg.mvThemeCol_Text, colors['text_primary'])
                dpg.add_theme_color(dpg.mvThemeCol_Border, colors['border'])
                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 8)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
            
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, colors['bg_tertiary'])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, colors['accent_primary'])
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 4)
            
            with dpg.theme_component(dpg.mvInputText):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, colors['bg_secondary'])
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6)
        
        return obsidian_theme

class DangerTheme:
    """Тема для опасных кнопок"""
    
    @staticmethod
    def setup_theme():
        with dpg.theme() as danger_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, [255, 60, 60, 200])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [255, 80, 80, 255])
                dpg.add_theme_color(dpg.mvThemeCol_Text, [255, 255, 255])
        return danger_theme

class WarningTheme:
    """Тема для предупреждающих кнопок"""
    
    @staticmethod
    def setup_theme():
        with dpg.theme() as warning_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, [255, 179, 64, 200])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [255, 199, 84, 255])
                dpg.add_theme_color(dpg.mvThemeCol_Text, [255, 255, 255])
        return warning_theme

class SuccessTheme:
    """Тема для успешных действий"""
    
    @staticmethod
    def setup_theme():
        with dpg.theme() as success_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, [72, 199, 116, 200])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [92, 219, 136, 255])
                dpg.add_theme_color(dpg.mvThemeCol_Text, [255, 255, 255])
        return success_theme

class MainWindow:
    """
    Главный интерфейс RapidRecon с модульной архитектурой
    """
    
    def __init__(self, engine, module_manager):
        self.engine = engine
        self.module_manager = module_manager
        self.logger = logging.getLogger('RapidRecon.GUI')
        
        # Модули интерфейса
        self.network_tree = NetworkTree()
        self.hosts_table = HostsTable(engine)
        self.scope_manager = ScopeManager()
        self.controls_panel = ControlsPanel(engine)
        
        # Состояние
        self.is_scanning = False
        self.is_paused = False
        self.current_scan_level = "Normal"
        
        # Данные для тестирования
        self.hosts_data = {
            "192.168.1.1": {
                "hostname": "router.local", 
                "status": "active", 
                "ports": [80, 443, 22], 
                "services": ["http", "https", "ssh"],
                "os": "Linux",
                "last_seen": datetime.now().strftime("%H:%M:%S"),
                "tags": ["router", "gateway"]
            },
            "192.168.1.100": {
                "hostname": "pc-01.local", 
                "status": "active", 
                "ports": [3389, 445, 135], 
                "services": ["rdp", "smb", "rpc"],
                "os": "Windows 10",
                "last_seen": datetime.now().strftime("%H:%M:%S"),
                "tags": ["workstation"]
            },
            "192.168.1.150": {
                "hostname": "server.local", 
                "status": "active", 
                "ports": [80, 443, 21, 25], 
                "services": ["http", "https", "ftp", "smtp"],
                "os": "Ubuntu Server",
                "last_seen": datetime.now().strftime("%H:%M:%S"),
                "tags": ["server", "web"]
            }
        }
        
        self.nodes_data = {
            "target_1": {
                "id": "target_1",
                "type": "initial_target",
                "label": "example.com",
                "data": {"ip": "93.184.216.34", "status": "active"},
                "timestamp": time.time()
            },
            "subdomain_1": {
                "id": "subdomain_1", 
                "type": "subdomain",
                "label": "www.example.com",
                "data": {"ip": "93.184.216.34", "parent": "example.com"},
                "timestamp": time.time()
            },
            "host_1": {
                "id": "host_1",
                "type": "active_host", 
                "label": "93.184.216.34",
                "data": {"ports": [80, 443], "services": ["http", "https"]},
                "timestamp": time.time()
            }
        }
        
        self.vulnerabilities_data = [
            "CVE-2021-44228 - Log4Shell",
            "CVE-2021-45046 - Log4j RCE",
            "CVE-2022-22965 - Spring4Shell"
        ]
        
        self.exploitation_results = [
            {"target": "192.168.1.100", "exploit": "EternalBlue", "success": True},
            {"target": "192.168.1.150", "exploit": "Shellshock", "success": False}
        ]

        # Инициализация GUI
        self.initialize_gui()
        
        self.logger.info("Графический интерфейс инициализирован")
    
    def initialize_gui(self):
        """Инициализация GUI"""
        try:
            # Проверяем доступность графической среды
            if not self.check_gui_environment():
                raise RuntimeError("Graphical environment not available")
                
            dpg.create_context()
            
            # Создание тем
            self.obsidian_theme = ObsidianTheme.setup_theme()
            self.danger_theme = DangerTheme.setup_theme()
            self.warning_theme = WarningTheme.setup_theme()
            self.success_theme = SuccessTheme.setup_theme()
            
            # Создание viewport
            dpg.create_viewport(
                title='RapidRecon - Advanced Security Scanner',
                width=1400,
                height=900,
                min_width=1000,
                min_height=700
            )
            
            # Создание главного окна
            self.create_main_window()
            
            # Создание окон настроек
            self.create_settings_window()
            self.create_export_window()
            
            # Настройка и показ GUI
            dpg.bind_theme(self.obsidian_theme)
            dpg.setup_dearpygui()
            dpg.show_viewport()
            dpg.set_primary_window("main_window", True)
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации GUI: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def check_gui_environment(self):
        """Проверка доступности графической среды"""
        try:
            import dearpygui.dearpygui as dpg
            dpg.create_context()
            dpg.destroy_context()
            return True
        except Exception:
            return False
    
    def create_main_window(self):
        """Создание главного окна с модульной архитектурой"""
        with dpg.window(
            tag="main_window",
            label="RapidRecon - Advanced Network Reconnaissance",
            width=1400,
            height=900,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            no_close=True
        ):
            # Боковая панель управления (упрощенная)
            with dpg.child_window(tag="sidebar", width=280, border=False):
                self.create_sidebar()
            
            # Основная область с вкладками
            with dpg.group(horizontal=True, width=-1, height=-1):
                with dpg.child_window(tag="content_area", width=-1, border=False):
                    # Сразу показываем Dashboard при запуске
                    self.create_dashboard_tab()
    
    def create_sidebar(self):
        """Создание упрощенной боковой панели управления"""
        # Логотип и статус
        with dpg.group():
            dpg.add_spacer(height=10)
            dpg.add_text("RapidRecon", color=[123, 97, 255])
            dpg.add_text("Security Scanner", color=[150, 150, 160])
            dpg.add_separator()
            
            # Статус сканирования
            with dpg.group(horizontal=True):
                dpg.add_text("Status:", color=[150, 150, 160])
                dpg.add_text("Ready", tag="scan_status", color=[72, 199, 116])
        
        # Панель управления (ControlsPanel)
        self.controls_panel.create_controls_panel("sidebar")
        
        # Быстрые действия (работающие кнопки)
        with dpg.collapsing_header(label="Quick Navigation", default_open=True):
            dpg.add_button(
                label="Dashboard", 
                width=-1,
                callback=self.show_dashboard
            )
            dpg.add_button(
                label="Network Tree",
                width=-1, 
                callback=self.show_network_tree
            )
            dpg.add_button(
                label="Hosts Table",
                width=-1,
                callback=self.show_hosts_table
            )
            dpg.add_button(
                label="Scope Manager", 
                width=-1,
                callback=self.show_scope_manager
            )
            dpg.add_button(
                label="Vulnerabilities", 
                width=-1,
                callback=self.show_vulnerabilities
            )
        
        # Статистика в реальном времени
        with dpg.collapsing_header(label="Live Statistics", default_open=True):
            dpg.add_text("Network Discovery:", color=[150, 150, 160])
            dpg.add_text("Nodes: 3", tag="stat_nodes")
            dpg.add_text("Hosts: 3", tag="stat_hosts")
            dpg.add_text("Services: 10", tag="stat_services")
            
            dpg.add_text("Security Findings:", color=[150, 150, 160])
            dpg.add_text("Vulnerabilities: 3", tag="stat_vulns", color=[255, 100, 100])
            dpg.add_text("Exploits: 1", tag="stat_exploits", color=[255, 60, 60])
        
        # Управление данными
        with dpg.group():
            dpg.add_separator()
            dpg.add_button(
                label="Engine Settings", 
                width=-1, 
                callback=self.show_settings
            )
            dpg.add_button(
                label="Export Data", 
                width=-1, 
                callback=self.export_all_data
            )
            dpg.add_button(
                label="Clear Data", 
                width=-1, 
                callback=self.clear_everything
            )
    
    def create_dashboard_tab(self):
        """Главная вкладка Dashboard"""
        with dpg.group():
            # Заголовок и быстрый старт
            with dpg.group(horizontal=True):
                with dpg.child_window(width=400):
                    dpg.add_text("Quick Start", color=[123, 97, 255])
                    dpg.add_separator()
                    
                    dpg.add_text("Target Configuration:")
                    dpg.add_input_text(
                        tag="dashboard_target",
                        hint="Enter target (IP, domain, range)",
                        width=-1
                    )
                    
                    dpg.add_text("Scan Intensity:")
                    dpg.add_combo(
                        tag="dashboard_intensity",
                        items=["Stealth", "Normal", "Aggressive", "Full"],
                        default_value="Normal",
                        width=-1,
                        callback=self.on_scan_level_change
                    )
                    
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="Start Scan",
                            callback=self.quick_start_scan
                        )
                        dpg.add_button(
                            label="Add Target",
                            callback=self.add_target_from_dashboard
                        )
                
                with dpg.child_window(width=400):
                    dpg.add_text("System Status", color=[123, 97, 255])
                    dpg.add_separator()
                    
                    dpg.add_text("Engine Status: Running", color=[72, 199, 116])
                    dpg.add_text("Active Modules: 6/6", color=[72, 199, 116])
                    dpg.add_text("Last Scan: Never", color=[255, 179, 64])
                    dpg.add_text("Total Findings: 16", color=[86, 156, 214])
                    
                    dpg.add_separator()
                    dpg.add_text("Quick Actions:")
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="Network Tree",
                            callback=self.show_network_tree
                        )
                        dpg.add_button(
                            label="Hosts Table",
                            callback=self.show_hosts_table
                        )
            
            # Основная область Dashboard
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                # Левая колонка - активность
                with dpg.child_window(width=500):
                    dpg.add_text("Recent Activity", color=[150, 150, 160])
                    dpg.add_separator()
                    
                    dpg.add_input_text(
                        tag="activity_log",
                        multiline=True,
                        height=300,
                        readonly=True,
                        width=-1,
                        default_value="[20:00:00] System initialized\n[20:00:00] GUI loaded successfully\n[20:00:00] Ready for scanning operations\n\nNo active scans running\n\nUse Quick Start panel to begin reconnaissance"
                    )
                
                # Правая колонка - модули и статистика
                with dpg.child_window():
                    dpg.add_text("Security Modules", color=[150, 150, 160])
                    dpg.add_separator()
                    
                    # Модули сканирования
                    modules = [
                        ("Ping Scanner", "Ready", [72, 199, 116]),
                        ("Port Scanner", "Ready", [72, 199, 116]),
                        ("Service Detector", "Ready", [72, 199, 116]),
                        ("Subdomain Scanner", "Ready", [72, 199, 116]),
                        ("Vulnerability Scanner", "Standby", [255, 179, 64]),
                        ("Exploitation Engine", "Standby", [255, 100, 100])
                    ]
                    
                    for name, status, color in modules:
                        with dpg.group(horizontal=True):
                            dpg.add_text(f"{name}:")
                            dpg.add_text(status, color=color)
                    
                    dpg.add_separator()
                    dpg.add_text("Network Overview", color=[150, 150, 160])
                    
                    # Мини-статистика
                    stats = [
                        ("Discovered Hosts", "3"),
                        ("Open Ports", "8"),
                        ("Running Services", "10"),
                        ("Security Issues", "3")
                    ]
                    
                    for name, value in stats:
                        with dpg.group(horizontal=True):
                            dpg.add_text(f"{name}:")
                            dpg.add_text(value, color=[123, 97, 255])
    
    def show_dashboard(self):
        """Показать Dashboard"""
        if dpg.does_item_exist("content_area"):
            dpg.delete_item("content_area", children_only=True)
            self.create_dashboard_tab()
    
    def show_network_tree(self):
        """Показать дерево сети"""
        if dpg.does_item_exist("content_area"):
            dpg.delete_item("content_area", children_only=True)
            self.create_network_tree_tab()
    
    def show_hosts_table(self):
        """Показать таблицу хостов"""
        if dpg.does_item_exist("content_area"):
            dpg.delete_item("content_area", children_only=True)
            self.create_hosts_table_tab()
    
    def show_scope_manager(self):
        """Показать менеджер scope"""
        if dpg.does_item_exist("content_area"):
            dpg.delete_item("content_area", children_only=True)
            self.create_scope_manager_tab()
    
    def show_vulnerabilities(self):
        """Показать уязвимости"""
        if dpg.does_item_exist("content_area"):
            dpg.delete_item("content_area", children_only=True)
            self.create_vulnerabilities_tab()
    
    def create_network_tree_tab(self):
        """Вкладка дерева сети"""
        with dpg.group(parent="content_area"):
            dpg.add_text("Network Topology", color=[123, 97, 255])
            dpg.add_separator()
            
            # Панель управления деревом
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Refresh Tree", 
                    callback=self.refresh_network_tree
                )
                dpg.add_button(
                    label="Statistics",
                    callback=self.show_network_statistics
                )
                dpg.add_button(
                    label="Export Tree", 
                    callback=self.export_network_tree
                )
                dpg.add_button(
                    label="Add All to Scope",
                    callback=self.add_all_nodes_to_scope
                )
            
            # Дерево сети
            self.network_tree.create_tree_panel("content_area")
            
            # Устанавливаем callback для выбора узлов
            self.network_tree.set_node_select_callback(self.on_node_select)
            
            # Инициализируем тестовые данные
            self.network_tree.update_tree(self.nodes_data, self.hosts_data)
    
    def create_hosts_table_tab(self):
        """Вкладка таблицы хостов"""
        with dpg.group(parent="content_area"):
            dpg.add_text("Discovered Hosts", color=[123, 97, 255])
            dpg.add_separator()
            
            # Таблица хостов
            self.hosts_table.create_table_panel("content_area")
            
            # Устанавливаем callback для выбора хостов
            self.hosts_table.set_host_select_callback(self.on_host_select)
            
            # Инициализируем тестовые данные
            self.hosts_table.update_table(self.hosts_data)
    
    def create_scope_manager_tab(self):
        """Вкладка управления scope"""
        with dpg.group(parent="content_area"):
            dpg.add_text("Scope Manager", color=[123, 97, 255])
            dpg.add_separator()
            dpg.add_text("Scope management functionality will be implemented here")
            dpg.add_text("Current scope targets: 0")
            dpg.add_button(label="Import Scope", width=120)
            dpg.add_button(label="Export Scope", width=120)
    
    def create_vulnerabilities_tab(self):
        """Вкладка уязвимостей"""
        with dpg.group(parent="content_area"):
            dpg.add_text("Vulnerability Scanner", color=[255, 100, 100])
            dpg.add_separator()
            dpg.add_text("Vulnerability scanning functionality will be implemented here")
            dpg.add_text("Discovered vulnerabilities: 3")
            dpg.add_button(label="Start Vuln Scan", width=120, callback=self.start_vulnerability_scan)
    
    def create_settings_window(self):
        """Окно настроек движка"""
        with dpg.window(
            tag="settings_window",
            label="Engine Settings",
            width=500,
            height=400,
            show=False,
            pos=[100, 100]
        ):
            with dpg.tab_bar():
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
                
                with dpg.tab(label="Scanning"):
                    dpg.add_text("Scanning Engine Settings")
                    dpg.add_slider_int(
                        tag="settings_threads",
                        label="Thread Count",
                        default_value=10,
                        min_value=1,
                        max_value=50
                    )
                    dpg.add_slider_int(
                        tag="settings_timeout",
                        label="Timeout (seconds)",
                        default_value=5,
                        min_value=1,
                        max_value=30
                    )
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Save Settings",
                    callback=self.save_engine_settings
                )
                dpg.add_button(
                    label="Close",
                    callback=lambda: dpg.hide_item("settings_window")
                )
    
    def create_export_window(self):
        """Окно экспорта данных"""
        with dpg.window(
            tag="export_window",
            label="Export Data",
            width=400,
            height=300,
            show=False,
            pos=[150, 150]
        ):
            dpg.add_text("Export Options")
            dpg.add_separator()
            
            dpg.add_text("Data to Export:")
            dpg.add_checkbox(tag="export_hosts", label="Hosts Data", default_value=True)
            dpg.add_checkbox(tag="export_network", label="Network Tree", default_value=True)
            dpg.add_checkbox(tag="export_vulns", label="Vulnerabilities", default_value=True)
            
            dpg.add_text("Export Format:")
            dpg.add_combo(
                tag="export_format",
                items=["JSON", "CSV", "XML"],
                default_value="JSON",
                width=-1
            )
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Export",
                    callback=self.perform_export
                )
                dpg.add_button(
                    label="Cancel",
                    callback=lambda: dpg.hide_item("export_window")
                )
    
    # === ОСНОВНЫЕ МЕТОДЫ ===
    
    def on_scan_level_change(self, sender, app_data):
        """Изменение уровня сканирования"""
        self.current_scan_level = app_data
        self.add_to_log(f"Scan intensity set to: {app_data}")
    
    def on_node_select(self, node_id):
        """Выбор узла в дереве"""
        self.add_to_log(f"Selected node: {node_id}")
    
    def on_host_select(self, ip):
        """Выбор хоста в таблице"""
        self.add_to_log(f"Selected host: {ip}")
    
    def quick_start_scan(self):
        """Быстрый запуск сканирования"""
        target = dpg.get_value("dashboard_target")
        if not target:
            self.add_to_log("Please enter a target first!")
            return
        
        self.add_to_log(f"Starting {self.current_scan_level} scan for: {target}")
        
        # Используем ControlsPanel для управления сканированием
        self.controls_panel.start_scan(target, self.current_scan_level)
        self.update_scan_state()
        
        # Обновляем активность
        self.update_activity_log(f"Started {self.current_scan_level} scan for {target}")
    
    def add_target_from_dashboard(self):
        """Добавление цели из dashboard"""
        target = dpg.get_value("dashboard_target")
        if target:
            self.add_to_log(f"Added target: {target}")
            self.update_activity_log(f"Target added to scope: {target}")
        else:
            self.add_to_log("Please enter a target first!")
    
    def pause_scan(self):
        """Пауза сканирования"""
        self.controls_panel.pause_scan()
        self.update_scan_state()
        self.update_activity_log("Scan paused")
    
    def resume_scan(self):
        """Возобновление сканирования"""
        self.controls_panel.resume_scan()
        self.update_scan_state()
        self.update_activity_log("Scan resumed")
    
    def stop_scan(self):
        """Остановка сканирования"""
        self.controls_panel.stop_scan()
        self.update_scan_state()
        self.update_activity_log("Scan stopped")
    
    def update_scan_state(self):
        """Обновление состояния сканирования в UI"""
        state = self.controls_panel.get_scan_state()
        self.is_scanning = state['is_scanning']
        self.is_paused = state['is_paused']
        
        dpg.set_value("scan_status", state['status'])
        dpg.configure_item("scan_status", color=state['color'])
    
    def update_activity_log(self, message: str):
        """Обновление лога активности"""
        current_log = dpg.get_value("activity_log")
        timestamp = datetime.now().strftime("%H:%M:%S")
        new_log = f"[{timestamp}] {message}\n{current_log}"
        dpg.set_value("activity_log", new_log)
    
    def start_vulnerability_scan(self):
        """Запуск сканирования уязвимостей"""
        self.add_to_log("Starting vulnerability scan...")
        self.update_activity_log("Vulnerability scan started")
    
    def refresh_network_tree(self):
        """Обновление дерева сети"""
        self.network_tree.update_tree(self.nodes_data, self.hosts_data)
        self.add_to_log("Network tree refreshed")
    
    def refresh_hosts_table(self):
        """Обновление таблицы хостов"""
        self.hosts_table.update_table(self.hosts_data)
        self.add_to_log("Hosts table refreshed")
    
    def show_network_statistics(self):
        """Показать статистику сети"""
        stats = self.calculate_statistics()
        
        if dpg.does_item_exist("network_stats_window"):
            dpg.delete_item("network_stats_window")
        
        with dpg.window(
            tag="network_stats_window",
            label="Network Statistics",
            width=350,
            height=250,
            modal=True
        ):
            dpg.add_text("Network Statistics")
            dpg.add_separator()
            
            for category, count in stats.items():
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{category}:", width=200)
                    dpg.add_text(str(count), color=[123, 97, 255])
        
        self.add_to_log("Showing network statistics")
    
    def export_network_tree(self):
        """Экспорт дерева сети"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"network_tree_{timestamp}.json"
        
        export_data = {
            'nodes': self.nodes_data,
            'hosts': self.hosts_data,
            'export_time': timestamp
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            self.add_to_log(f"Network tree exported to {filename}")
            self.update_activity_log(f"Network tree exported: {filename}")
        except Exception as e:
            self.add_to_log(f"Export failed: {e}")
    
    def add_all_nodes_to_scope(self):
        """Добавить все узлы в scope"""
        count = 0
        for node_id, node in self.nodes_data.items():
            if self.scope_manager.add_to_scope(node):
                count += 1
        
        self.add_to_log(f"Added {count} nodes to scope")
        self.update_activity_log(f"Added {count} nodes to scanning scope")
    
    def scan_selected_hosts(self):
        """Сканирование выбранных хостов"""
        self.hosts_table.scan_selected_hosts()
    
    def add_selected_to_scope(self):
        """Добавление выбранных в scope"""
        self.hosts_table.add_selected_to_scope()
    
    def export_hosts_csv(self):
        """Экспорт хостов в CSV"""
        self.hosts_table.export_hosts_csv()
    
    def show_settings(self):
        """Показать настройки"""
        dpg.show_item("settings_window")
        self.add_to_log("Engine settings opened")
    
    def export_all_data(self):
        """Экспорт всех данных"""
        dpg.show_item("export_window")
        self.add_to_log("Export dialog opened")
    
    def clear_everything(self):
        """Очистка всего"""
        self.nodes_data.clear()
        self.hosts_data.clear()
        self.vulnerabilities_data.clear()
        self.exploitation_results.clear()
        
        self.network_tree.clear()
        self.hosts_table.clear()
        self.scope_manager.clear()
        
        # Сбрасываем статистику
        stats = ["stat_nodes", "stat_hosts", "stat_services", "stat_ports", 
                "stat_vulns", "stat_exploits", "stat_lateral"]
        for stat in stats:
            dpg.set_value(stat, f"{stat.split('_')[1].title()}: 0")
        
        self.add_to_log("Everything cleared")
        self.update_activity_log("All data cleared - fresh start")
    
    def load_vulnerable_targets(self):
        """Загрузка уязвимых целей"""
        vulnerable_targets = []
        for ip, host in self.hosts_data.items():
            if host.get('vulnerabilities'):
                vulnerable_targets.append(ip)
        
        if vulnerable_targets:
            self.add_to_log(f"Loaded {len(vulnerable_targets)} vulnerable targets")
        else:
            self.add_to_log("No vulnerable targets found")
    
    def generate_report(self):
        """Генерация отчета"""
        self.add_to_log("Generating report...")
        self.update_activity_log("Report generation started")
    
    def save_engine_settings(self):
        """Сохранение настроек движка"""
        self.add_to_log("Engine settings saved")
        self.update_activity_log("Engine configuration updated")
        dpg.hide_item("settings_window")
    
    def perform_export(self):
        """Выполнение экспорта данных"""
        export_format = dpg.get_value("export_format")
        self.add_to_log(f"Exporting data in {export_format} format")
        self.update_activity_log(f"Data export completed in {export_format} format")
        dpg.hide_item("export_window")
    
    def calculate_statistics(self):
        """Расчет статистики"""
        return {
            "Total Nodes": len(self.nodes_data),
            "Active Hosts": len([h for h in self.hosts_data.values() if h.get('status') == 'active']),
            "Open Ports": sum(len(h.get('ports', [])) for h in self.hosts_data.values()),
            "Services": sum(len(h.get('services', [])) for h in self.hosts_data.values()),
            "Vulnerabilities": len(self.vulnerabilities_data),
            "Exploits": len([e for e in self.exploitation_results if e.get('success')])
        }
    
    def add_to_log(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)
    
    def handle_engine_event(self, event_type: str, data: Any = None):
        """Обработка событий от движка"""
        try:
            self.logger.info(f"GUI received event: {event_type}")
            
            if event_type in ['node_added', 'node_discovered', 'module_results']:
                # Обновляем данные из движка
                if hasattr(self.engine, 'discovered_nodes'):
                    self.nodes_data = self.engine.discovered_nodes
                
                if hasattr(self.engine, 'hosts_data'):
                    self.hosts_data = self.engine.hosts_data
                
                # Обновляем модули интерфейса
                self.network_tree.update_tree(self.nodes_data, self.hosts_data)
                self.hosts_table.update_table(self.hosts_data)
                
                # Обновляем статистику
                self.update_statistics()
                
                # Обновляем активность
                self.update_activity_log(f"New data received: {event_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling engine event: {e}")
    
    def update_statistics(self):
        """Обновление статистики"""
        try:
            stats = self.calculate_statistics()
            
            dpg.set_value("stat_nodes", f"Nodes: {stats['Total Nodes']}")
            dpg.set_value("stat_hosts", f"Hosts: {stats['Active Hosts']}")
            dpg.set_value("stat_services", f"Services: {stats['Services']}")
            dpg.set_value("stat_vulns", f"Vulnerabilities: {stats['Vulnerabilities']}")
            dpg.set_value("stat_exploits", f"Exploits: {stats['Exploits']}")
            
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")
    
    def run(self):
        """Запуск GUI"""
        try:
            self.logger.info("Запуск графического интерфейса...")
            
            # Инициализируем данные при запуске
            self.update_statistics()
            self.update_activity_log("System initialized and ready")
            
            while dpg.is_dearpygui_running():
                dpg.render_dearpygui_frame()
            
            self.destroy()
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска GUI: {e}")
    
    def destroy(self):
        """Уничтожение GUI"""
        try:
            self.logger.info("Очистка графического интерфейса...")
            dpg.destroy_context()
        except Exception as e:
            self.logger.error(f"Ошибка уничтожения GUI: {e}")
