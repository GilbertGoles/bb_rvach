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
        self.current_scan_level = "⚡ Normal"
        
        # Данные
        self.hosts_data = {}
        self.nodes_data = {}
        self.vulnerabilities_data = []
        self.exploitation_results = []
        
        # Инициализация GUI
        self.initialize_gui()
        
        self.logger.info("✅ Графический интерфейс инициализирован")
    
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
                title='RapidRecon • Advanced Security Scanner',
                width=1600,
                height=1000,
                min_width=1200,
                min_height=800
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
            self.logger.error(f"❌ Ошибка инициализации GUI: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def check_gui_environment(self):
        """Проверка доступности графической среды"""
        try:
            # Простая проверка возможности создания окна
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
            width=1600,
            height=1000,
            no_move=True,
            no_resize=True,
            no_collapse=True,
            no_close=True
        ):
            # Боковая панель управления
            with dpg.child_window(tag="sidebar", width=300, border=False):
                self.create_sidebar()
            
            # Основная область с вкладками
            with dpg.group(horizontal=True, width=-1, height=-1):
                with dpg.child_window(tag="content_area", width=-1, border=False):
                    self.create_content_area()
    
    def create_sidebar(self):
        """Создание боковой панели управления"""
        # Логотип и статус
        with dpg.group():
            dpg.add_spacer(height=20)
            dpg.add_text("RapidRecon", color=[123, 97, 255])
            dpg.add_text("Advanced Security Scanner", color=[150, 150, 160])
            dpg.add_separator()
            
            # Статус сканирования
            with dpg.group(horizontal=True):
                dpg.add_text("Status:", color=[150, 150, 160])
                dpg.add_text("Ready", tag="scan_status", color=[72, 199, 116])
        
        # Панель управления (ControlsPanel)
        self.controls_panel.create_controls_panel("sidebar")
        
        # Модули и возможности
        with dpg.collapsing_header(label="🔧 Modules & Capabilities", default_open=True):
            dpg.add_text("Active Modules:", color=[150, 150, 160])
            
            modules = [
                ("✅", "Ping Scanner", [200, 200, 200]),
                ("✅", "Port Scanner", [200, 200, 200]),
                ("✅", "Service Detector", [200, 200, 200]),
                ("✅", "Subdomain Scanner", [200, 200, 200]),
                ("🔴", "Vulnerability Scanner", [255, 100, 100]),
                ("💀", "Exploitation Engine", [255, 60, 60]),
                ("🟡", "Lateral Movement", [255, 165, 0])
            ]
            
            for icon, name, color in modules:
                with dpg.group(horizontal=True):
                    dpg.add_text(icon, color=color)
                    dpg.add_text(name, color=color)
        
        # Статистика в реальном времени
        with dpg.collapsing_header(label="📈 Live Statistics", default_open=True):
            dpg.add_text("Network Discovery:", color=[150, 150, 160])
            dpg.add_text("Nodes: 0", tag="stat_nodes")
            dpg.add_text("Hosts: 0", tag="stat_hosts")
            dpg.add_text("Services: 0", tag="stat_services")
            dpg.add_text("Ports: 0", tag="stat_ports")
            
            dpg.add_text("Security Findings:", color=[150, 150, 160])
            dpg.add_text("Vulnerabilities: 0", tag="stat_vulns", color=[255, 100, 100])
            dpg.add_text("Exploits: 0", tag="stat_exploits", color=[255, 60, 60])
            dpg.add_text("Lateral: 0", tag="stat_lateral", color=[255, 165, 0])
        
        # Быстрые действия
        with dpg.collapsing_header(label="🚀 Quick Actions", default_open=True):
            dpg.add_button(
                label="🌐 View Network Tree", 
                width=-1,
                callback=lambda: dpg.set_value("main_tabs", "tree_tab")
            )
            dpg.add_button(
                label="📊 View Hosts Table",
                width=-1, 
                callback=lambda: dpg.set_value("main_tabs", "table_tab")
            )
            dpg.add_button(
                label="🎯 Scope Manager",
                width=-1,
                callback=lambda: dpg.set_value("main_tabs", "scope_tab")
            )
            dpg.add_button(
                label="🔍 Vulnerability Scan", 
                width=-1,
                callback=self.start_vulnerability_scan
            )
            dpg.add_button(
                label="💥 Exploitation", 
                width=-1,
                callback=self.start_exploitation
            )
        
        # Управление данными
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
    
    def create_content_area(self):
        """Создание основной области с вкладками модулей"""
        with dpg.tab_bar(tag="main_tabs"):
            # 1. Вкладка дерева сети 🌐
            with dpg.tab(label="🌐 Network Tree", tag="tree_tab"):
                self.create_network_tree_tab()
            
            # 2. Вкладка таблицы хостов 📊
            with dpg.tab(label="📊 Hosts Table", tag="table_tab"):
                self.create_hosts_table_tab()
            
            # 3. Вкладка управления scope 🎯
            with dpg.tab(label="🎯 Scope Manager", tag="scope_tab"):
                self.create_scope_manager_tab()
            
            # 4. Вкладка уязвимостей 🔴
            with dpg.tab(label="🔴 Vulnerabilities", tag="vulns_tab"):
                self.create_vulnerabilities_tab()
            
            # 5. Вкладка эксплуатации 💥
            with dpg.tab(label="💥 Exploitation", tag="exploit_tab"):
                self.create_exploitation_tab()
            
            # 6. Вкладка отчетов 📋
            with dpg.tab(label="📋 Reports", tag="reports_tab"):
                self.create_reports_tab()
    
    def create_network_tree_tab(self):
        """Вкладка дерева сети"""
        with dpg.group():
            # Панель управления деревом
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="🔄 Refresh Tree", 
                    callback=self.refresh_network_tree
                )
                dpg.add_button(
                    label="📊 Statistics",
                    callback=self.show_network_statistics
                )
                dpg.add_button(
                    label="💾 Export Tree", 
                    callback=self.export_network_tree
                )
                dpg.add_button(
                    label="🎯 Add All to Scope",
                    callback=self.add_all_nodes_to_scope
                )
            
            # Дерево сети
            self.network_tree.create_tree_panel("tree_tab")
            
            # Устанавливаем callback для выбора узлов
            self.network_tree.set_node_select_callback(self.on_node_select)
    
    def create_hosts_table_tab(self):
        """Вкладка таблицы хостов"""
        with dpg.group():
            # Панель управления таблицей
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="🔄 Refresh Table",
                    callback=self.refresh_hosts_table
                )
                dpg.add_button(
                    label="🔍 Scan Selected",
                    callback=self.scan_selected_hosts
                )
                dpg.add_button(
                    label="🎯 Add to Scope",
                    callback=self.add_selected_to_scope
                )
                dpg.add_button(
                    label="💾 Export CSV",
                    callback=self.export_hosts_csv
                )
            
            # Таблица хостов
            self.hosts_table.create_table_panel("table_tab")
            
            # Устанавливаем callback для выбора хостов
            self.hosts_table.set_host_select_callback(self.on_host_select)
    
    def create_scope_manager_tab(self):
        """Вкладка управления scope"""
        # Используем ScopeManager модуль
        self.scope_manager.create_scope_panel("scope_tab")
    
    def create_vulnerabilities_tab(self):
        """Вкладка уязвимостей"""
        with dpg.group():
            dpg.add_text("🔴 Vulnerability Scanner", color=[255, 100, 100])
            dpg.add_separator()
            
            with dpg.group(horizontal=True):
                with dpg.child_window(width=400):
                    dpg.add_text("Scan Configuration")
                    dpg.add_checkbox(tag="vuln_scan_ports", label="Scan Open Ports", default_value=True)
                    dpg.add_checkbox(tag="vuln_scan_services", label="Service Detection", default_value=True)
                    dpg.add_checkbox(tag="vuln_scan_web", label="Web Application Scan", default_value=True)
                    
                    dpg.add_text("Intensity Level:")
                    dpg.add_combo(
                        tag="vuln_intensity",
                        items=["Low", "Medium", "High", "Aggressive"],
                        default_value="Medium",
                        width=-1
                    )
                    
                    vuln_btn = dpg.add_button(
                        label="🔍 Start Vulnerability Scan",
                        width=-1,
                        callback=self.start_vulnerability_scan
                    )
                    dpg.bind_item_theme(vuln_btn, self.danger_theme)
                
                with dpg.child_window():
                    dpg.add_text("Discovered Vulnerabilities")
                    dpg.add_listbox(
                        tag="vulnerabilities_list",
                        items=[],
                        num_items=12,
                        width=-1
                    )
                    
                    dpg.add_text("Vulnerability Details:")
                    dpg.add_input_text(
                        tag="vuln_details",
                        multiline=True,
                        height=200,
                        readonly=True,
                        width=-1
                    )
    
    def create_exploitation_tab(self):
        """Вкладка эксплуатации"""
        with dpg.group():
            dpg.add_text("💥 Exploitation Engine", color=[255, 60, 60])
            dpg.add_separator()
            
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
                    
                    dpg.add_text("Exploitation Options")
                    dpg.add_checkbox(tag="auto_exploit", label="Auto-Exploit", default_value=False)
                    dpg.add_checkbox(tag="lateral_movement", label="Lateral Movement", default_value=True)
                    
                    exploit_btn = dpg.add_button(
                        label="💥 Start Exploitation",
                        width=-1,
                        callback=self.start_exploitation
                    )
                    dpg.bind_item_theme(exploit_btn, self.danger_theme)
                
                with dpg.child_window():
                    dpg.add_text("Exploitation Results")
                    dpg.add_input_text(
                        tag="exploitation_log",
                        multiline=True,
                        height=400,
                        readonly=True,
                        width=-1
                    )
    
    def create_reports_tab(self):
        """Вкладка отчетов"""
        with dpg.group():
            dpg.add_text("📋 Reporting Engine", color=[86, 156, 214])
            dpg.add_separator()
            
            with dpg.group(horizontal=True):
                with dpg.child_window(width=300):
                    dpg.add_text("Report Types")
                    dpg.add_button(label="📊 Executive Summary", width=-1)
                    dpg.add_button(label="🔍 Technical Details", width=-1)
                    dpg.add_button(label="🔴 Vulnerability Report", width=-1)
                    dpg.add_button(label="💥 Exploitation Report", width=-1)
                    dpg.add_button(label="🌐 Full Network Report", width=-1)
                    
                    dpg.add_separator()
                    dpg.add_text("Export Format:")
                    dpg.add_combo(
                        items=["PDF", "HTML", "JSON", "CSV", "Markdown"],
                        default_value="PDF",
                        width=-1
                    )
                    
                    dpg.add_button(
                        label="💾 Generate Report",
                        width=-1,
                        callback=self.generate_report
                    )
                
                with dpg.child_window():
                    dpg.add_text("Report Preview")
                    dpg.add_input_text(
                        tag="report_preview",
                        multiline=True,
                        height=500,
                        readonly=True,
                        width=-1
                    )
    
    def create_settings_window(self):
        """Окно настроек движка"""
        with dpg.window(
            tag="settings_window",
            label="Engine Settings",
            width=600,
            height=500,
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
                    label="💾 Save Settings",
                    callback=self.save_engine_settings
                )
                dpg.add_button(
                    label="❌ Close",
                    callback=lambda: dpg.hide_item("settings_window")
                )
    
    def create_export_window(self):
        """Окно экспорта данных"""
        with dpg.window(
            tag="export_window",
            label="Export Data",
            width=500,
            height=400,
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
                    label="💾 Export",
                    callback=self.perform_export
                )
                dpg.add_button(
                    label="❌ Cancel",
                    callback=lambda: dpg.hide_item("export_window")
                )
    
    # === ОСНОВНЫЕ МЕТОДЫ ===
    
    def on_scan_level_change(self, sender, app_data):
        """Изменение уровня сканирования"""
        self.current_scan_level = app_data
        self.add_to_log(f"🎛️ Scan intensity set to: {app_data}")
    
    def on_node_select(self, node_id):
        """Выбор узла в дереве"""
        self.add_to_log(f"🔍 Selected node: {node_id}")
    
    def on_host_select(self, ip):
        """Выбор хоста в таблице"""
        self.add_to_log(f"🔍 Selected host: {ip}")
    
    def quick_start_scan(self):
        """Быстрый запуск сканирования"""
        target = dpg.get_value("quick_target_input")
        if not target:
            self.add_to_log("❌ Please enter a target first!")
            return
        
        self.add_to_log(f"🚀 Starting {self.current_scan_level} scan for: {target}")
        
        # Используем ControlsPanel для управления сканированием
        self.controls_panel.start_scan(target, self.current_scan_level)
        self.update_scan_state()
    
    def pause_scan(self):
        """Пауза сканирования"""
        self.controls_panel.pause_scan()
        self.update_scan_state()
    
    def resume_scan(self):
        """Возобновление сканирования"""
        self.controls_panel.resume_scan()
        self.update_scan_state()
    
    def stop_scan(self):
        """Остановка сканирования"""
        self.controls_panel.stop_scan()
        self.update_scan_state()
    
    def update_scan_state(self):
        """Обновление состояния сканирования в UI"""
        state = self.controls_panel.get_scan_state()
        self.is_scanning = state['is_scanning']
        self.is_paused = state['is_paused']
        
        dpg.set_value("scan_status", state['status'])
        dpg.configure_item("scan_status", color=state['color'])
    
    def start_vulnerability_scan(self):
        """Запуск сканирования уязвимостей"""
        self.add_to_log("🔍 Starting vulnerability scan...")
        dpg.set_value("main_tabs", "vulns_tab")
    
    def start_exploitation(self):
        """Запуск эксплуатации"""
        self.add_to_log("💥 Starting exploitation...")
        dpg.set_value("main_tabs", "exploit_tab")
    
    def refresh_network_tree(self):
        """Обновление дерева сети"""
        self.network_tree.update_tree(self.nodes_data, self.hosts_data)
        self.add_to_log("🔄 Network tree refreshed")
    
    def refresh_hosts_table(self):
        """Обновление таблицы хостов"""
        self.hosts_table.update_table(self.hosts_data)
        self.add_to_log("🔄 Hosts table refreshed")
    
    def show_network_statistics(self):
        """Показать статистику сети"""
        stats = self.calculate_statistics()
        
        if dpg.does_item_exist("network_stats_window"):
            dpg.delete_item("network_stats_window")
        
        with dpg.window(
            tag="network_stats_window",
            label="Network Statistics",
            width=400,
            height=300,
            modal=True
        ):
            dpg.add_text("📊 Network Statistics")
            dpg.add_separator()
            
            for category, count in stats.items():
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{category}:", width=200)
                    dpg.add_text(str(count), color=[123, 97, 255])
        
        self.add_to_log("📊 Showing network statistics")
    
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
            self.add_to_log(f"💾 Network tree exported to {filename}")
        except Exception as e:
            self.add_to_log(f"❌ Export failed: {e}")
    
    def add_all_nodes_to_scope(self):
        """Добавить все узлы в scope"""
        count = 0
        for node_id, node in self.nodes_data.items():
            if self.scope_manager.add_to_scope(node):
                count += 1
        
        self.add_to_log(f"🎯 Added {count} nodes to scope")
    
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
        self.add_to_log("⚙️ Engine settings opened")
    
    def export_all_data(self):
        """Экспорт всех данных"""
        dpg.show_item("export_window")
        self.add_to_log("📤 Export dialog opened")
    
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
        
        self.add_to_log("🧹 Everything cleared")
    
    def load_vulnerable_targets(self):
        """Загрузка уязвимых целей"""
        vulnerable_targets = []
        for ip, host in self.hosts_data.items():
            if host.get('vulnerabilities'):
                vulnerable_targets.append(ip)
        
        dpg.configure_item("exploit_targets", items=vulnerable_targets)
        self.add_to_log(f"🎯 Loaded {len(vulnerable_targets)} vulnerable targets")
    
    def generate_report(self):
        """Генерация отчета"""
        self.add_to_log("📋 Generating report...")
    
    def save_engine_settings(self):
        """Сохранение настроек движка"""
        self.add_to_log("💾 Engine settings saved")
        dpg.hide_item("settings_window")
    
    def perform_export(self):
        """Выполнение экспорта данных"""
        export_format = dpg.get_value("export_format")
        self.add_to_log(f"💾 Exporting data in {export_format} format")
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
                
        except Exception as e:
            self.logger.error(f"Error handling engine event: {e}")
    
    def update_statistics(self):
        """Обновление статистики"""
        try:
            stats = self.calculate_statistics()
            
            dpg.set_value("stat_nodes", f"Nodes: {stats['Total Nodes']}")
            dpg.set_value("stat_hosts", f"Hosts: {stats['Active Hosts']}")
            dpg.set_value("stat_services", f"Services: {stats['Services']}")
            dpg.set_value("stat_ports", f"Ports: {stats['Open Ports']}")
            dpg.set_value("stat_vulns", f"Vulnerabilities: {stats['Vulnerabilities']}")
            dpg.set_value("stat_exploits", f"Exploits: {stats['Exploits']}")
            
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")
    
    def run(self):
        """Запуск GUI"""
        try:
            self.logger.info("🚀 Запуск графического интерфейса...")
            
            while dpg.is_dearpygui_running():
                dpg.render_dearpygui_frame()
            
            self.destroy()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска GUI: {e}")
    
    def destroy(self):
        """Уничтожение GUI"""
        try:
            self.logger.info("🧹 Очистка графического интерфейса...")
            dpg.destroy_context()
        except Exception as e:
            self.logger.error(f"❌ Ошибка уничтожения GUI: {e}")
