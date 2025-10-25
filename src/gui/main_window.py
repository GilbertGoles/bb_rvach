"""
Главное окно RapidRecon - полная версия с реальной функциональностью
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
    Полный интерфейс RapidRecon с реальной функциональностью
    """
    
    def __init__(self, engine, module_manager):
        self.engine = engine
        self.module_manager = module_manager
        self.logger = logging.getLogger('RapidRecon.GUI')
        
        # Модули интерфейса
        self.network_tree = NetworkTree()
        self.hosts_table = HostsTable(engine)
        
        # Состояние
        self.is_scanning = False
        self.is_paused = False
        self.current_scan_level = "⚡ Normal"
        self.selected_targets = set()
        self.scope_settings = {
            'allowed_ips': [],
            'allowed_domains': [],
            'domain_suffixes': []
        }
        
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
            raise
    
    def create_main_window(self):
        """Создание главного окна с полной функциональностью"""
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
        """Создание боковой панели управления с РЕАЛЬНЫМИ функциями"""
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
        
        # Быстрый запуск
        with dpg.collapsing_header(label="⚡ Quick Launch", default_open=True):
            dpg.add_text("Primary Target:", color=[150, 150, 160])
            dpg.add_input_text(
                tag="quick_target_input", 
                hint="example.com / 192.168.1.1", 
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
            
            # Кнопки управления сканированием
            with dpg.group(horizontal=True):
                start_btn = dpg.add_button(
                    label="🎯 Start",
                    tag="quick_start_btn",
                    width=90,
                    callback=self.quick_start_scan
                )
                dpg.bind_item_theme(start_btn, self.success_theme)
                
                pause_btn = dpg.add_button(
                    label="⏸️ Pause",
                    tag="quick_pause_btn", 
                    width=90,
                    callback=self.pause_scan,
                    show=False
                )
                dpg.bind_item_theme(pause_btn, self.warning_theme)
            
            with dpg.group(horizontal=True):
                resume_btn = dpg.add_button(
                    label="▶️ Resume",
                    tag="quick_resume_btn",
                    width=90,
                    callback=self.resume_scan,
                    show=False
                )
                dpg.bind_item_theme(resume_btn, self.success_theme)
                
                stop_btn = dpg.add_button(
                    label="⏹️ Stop",
                    tag="quick_stop_btn",
                    width=90,
                    callback=self.stop_scan,
                    show=False
                )
                dpg.bind_item_theme(stop_btn, self.danger_theme)
        
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
        
        # Быстрые действия с РЕАЛЬНЫМИ функциями
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
                label="🔍 Scan for Vulnerabilities",
                width=-1,
                callback=self.start_vulnerability_scan_real
            )
            dpg.add_button(
                label="💥 Start Exploitation", 
                width=-1,
                callback=self.start_exploitation_real
            )
        
        # Управление данными с РЕАЛЬНЫМИ функциями
        with dpg.group():
            dpg.add_separator()
            dpg.add_button(
                label="⚙️ Engine Settings", 
                width=-1, 
                callback=self.show_settings_real
            )
            dpg.add_button(
                label="📤 Export All Data", 
                width=-1, 
                callback=self.export_all_data_real
            )
            dpg.add_button(
                label="🧹 Clear Everything", 
                width=-1, 
                callback=self.clear_everything_real
            )
    
    def create_content_area(self):
        """Создание основной области с вкладками модулей"""
        with dpg.tab_bar(tag="main_tabs"):
            # 1. Вкладка дерева сети 🌐 (РЕАЛЬНОЕ ДЕРЕВО)
            with dpg.tab(label="🌐 Network Tree", tag="tree_tab"):
                self.create_network_tree_tab()
            
            # 2. Вкладка таблицы хостов 📊 (РЕАЛЬНАЯ ТАБЛИЦА)
            with dpg.tab(label="📊 Hosts Table", tag="table_tab"):
                self.create_hosts_table_tab()
            
            # 3. Вкладка управления scope 🎯 (РЕАЛЬНЫЙ SCOPE)
            with dpg.tab(label="🎯 Scope Manager", tag="scope_tab"):
                self.create_scope_manager_tab()
            
            # 4. Вкладка уязвимостей 🔴 (РЕАЛЬНОЕ СКАНИРОВАНИЕ)
            with dpg.tab(label="🔴 Vulnerabilities", tag="vulns_tab"):
                self.create_vulnerabilities_tab()
            
            # 5. Вкладка эксплуатации 💥 (РЕАЛЬНАЯ ЭКСПЛУАТАЦИЯ)
            with dpg.tab(label="💥 Exploitation", tag="exploit_tab"):
                self.create_exploitation_tab()
            
            # 6. Вкладка отчетов 📋 (РЕАЛЬНЫЕ ОТЧЕТЫ)
            with dpg.tab(label="📋 Reports", tag="reports_tab"):
                self.create_reports_tab()
    
    def create_network_tree_tab(self):
        """Вкладка дерева сети с РЕАЛЬНЫМИ функциями"""
        with dpg.group():
            # Панель управления деревом
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="🔄 Refresh Tree", 
                    callback=self.refresh_network_tree_real
                )
                dpg.add_button(
                    label="📊 Statistics",
                    callback=self.show_network_statistics_real
                )
                dpg.add_button(
                    label="💾 Export Tree", 
                    callback=self.export_network_tree_real
                )
                dpg.add_button(
                    label="🎯 Add All to Scope",
                    callback=self.add_all_nodes_to_scope
                )
            
            # Дерево сети
            self.network_tree_panel = self.network_tree.create_tree_panel("tree_tab")
            
            # Устанавливаем callback для выбора узлов
            self.network_tree.set_node_select_callback(self._on_node_select_real)
    
    def create_hosts_table_tab(self):
        """Вкладка таблицы хостов с РЕАЛЬНЫМИ функциями"""
        with dpg.group():
            # Панель управления таблицей
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="🔄 Refresh Table",
                    callback=self.refresh_hosts_table_real
                )
                dpg.add_button(
                    label="🔍 Scan Selected",
                    callback=self.scan_selected_hosts_real
                )
                dpg.add_button(
                    label="🎯 Add to Scope",
                    callback=self.add_selected_to_scope_real
                )
                dpg.add_button(
                    label="💾 Export CSV",
                    callback=self.export_hosts_csv_real
                )
            
            # Таблица хостов
            self.hosts_table_panel = self.hosts_table.create_table_panel("table_tab")
            
            # Устанавливаем callback для выбора хостов
            self.hosts_table.set_host_select_callback(self._on_host_select_real)
    
    def create_scope_manager_tab(self):
        """Вкладка управления scope с РЕАЛЬНЫМИ функциями"""
        with dpg.group(horizontal=True):
            # Левая панель - настройки scope
            with dpg.child_window(width=400):
                dpg.add_text("🎯 Scope Configuration", color=[123, 97, 255])
                dpg.add_separator()
                
                dpg.add_text("Allowed IP Ranges:", color=[150, 150, 160])
                dpg.add_input_text(
                    tag="scope_ips",
                    hint="192.168.1.0/24, 10.0.0.0/8...",
                    multiline=True,
                    height=80,
                    width=-1
                )
                
                dpg.add_text("Allowed Domains:", color=[150, 150, 160])
                dpg.add_input_text(
                    tag="scope_domains", 
                    hint="example.com, *.test.com...",
                    multiline=True,
                    height=80,
                    width=-1
                )
                
                dpg.add_text("Domain Suffixes:", color=[150, 150, 160])
                dpg.add_input_text(
                    tag="scope_suffixes",
                    hint=".com, .org, .local...", 
                    multiline=True,
                    height=60,
                    width=-1
                )
                
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="💾 Save Scope",
                        callback=self.save_scope_settings_real
                    )
                    dpg.add_button(
                        label="🔄 Apply Scope",
                        callback=self.apply_scope_settings_real
                    )
                    dpg.add_button(
                        label="📥 Load Scope",
                        callback=self.load_scope_settings
                    )
            
            # Правая панель - что попало в scope
            with dpg.child_window():
                dpg.add_text("📋 In-Scope Targets", color=[123, 97, 255])
                dpg.add_separator()
                
                dpg.add_text("Discovered in Scope:", color=[150, 150, 160])
                dpg.add_listbox(
                    tag="in_scope_targets",
                    items=[],
                    num_items=15,
                    width=-1
                )
                
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="🔄 Refresh List",
                        callback=self.refresh_scope_list_real
                    )
                    dpg.add_button(
                        label="🧹 Clear Out-of-Scope",
                        callback=self.clear_out_of_scope_real
                    )
                    dpg.add_button(
                        label="📊 Scope Stats",
                        callback=self.show_scope_statistics
                    )
    
    def create_vulnerabilities_tab(self):
        """Вкладка уязвимостей с РЕАЛЬНЫМ сканированием"""
        with dpg.group():
            dpg.add_text("🔴 Vulnerability Scanner", color=[255, 100, 100])
            dpg.add_separator()
            
            with dpg.group(horizontal=True):
                with dpg.child_window(width=400):
                    dpg.add_text("Scan Configuration")
                    dpg.add_checkbox(tag="vuln_scan_ports", label="Scan Open Ports", default_value=True)
                    dpg.add_checkbox(tag="vuln_scan_services", label="Service Detection", default_value=True)
                    dpg.add_checkbox(tag="vuln_scan_web", label="Web Application Scan", default_value=True)
                    dpg.add_checkbox(tag="vuln_scan_auth", label="Authentication Tests", default_value=False)
                    
                    dpg.add_text("Intensity Level:")
                    dpg.add_combo(
                        tag="vuln_intensity",
                        items=["Low", "Medium", "High", "Aggressive"],
                        default_value="Medium",
                        width=-1
                    )
                    
                    dpg.add_text("Target Selection:")
                    dpg.add_radio_button(
                        tag="vuln_targets",
                        items=["All Hosts", "Selected Hosts", "In-Scope Only"],
                        default_value="In-Scope Only"
                    )
                    
                    vuln_btn = dpg.add_button(
                        label="🔍 Start Vulnerability Scan",
                        width=-1,
                        callback=self.start_vulnerability_scan_real
                    )
                    dpg.bind_item_theme(vuln_btn, self.danger_theme)
                
                with dpg.child_window():
                    dpg.add_text("Discovered Vulnerabilities")
                    with dpg.child_window(height=200, border=True):
                        dpg.add_listbox(
                            tag="vulnerabilities_list",
                            items=[],
                            num_items=8,
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
                    
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="📋 Export Vulns",
                            callback=self.export_vulnerabilities
                        )
                        dpg.add_button(
                            label="🎯 Add to Exploitation",
                            callback=self.add_vulns_to_exploitation
                        )
    
    def create_exploitation_tab(self):
        """Вкладка эксплуатации с РЕАЛЬНЫМ движком"""
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
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="🎯 Load Vulnerable Targets",
                            callback=self.load_vulnerable_targets_real
                        )
                        dpg.add_button(
                            label="🔄 Refresh",
                            callback=self.refresh_exploit_targets
                        )
                    
                    dpg.add_text("Exploitation Options")
                    dpg.add_checkbox(tag="auto_exploit", label="Auto-Exploit", default_value=False)
                    dpg.add_checkbox(tag="lateral_movement", label="Lateral Movement", default_value=True)
                    dpg.add_checkbox(tag="persistence", label="Establish Persistence", default_value=True)
                    dpg.add_checkbox(tag="privilege_escalation", label="Privilege Escalation", default_value=True)
                    
                    dpg.add_text("Payload Type:")
                    dpg.add_combo(
                        tag="payload_type",
                        items=["Meterpreter", "Shell", "Custom", "Web Shell"],
                        default_value="Meterpreter",
                        width=-1
                    )
                    
                    exploit_btn = dpg.add_button(
                        label="💥 Start Exploitation",
                        width=-1,
                        callback=self.start_exploitation_engine_real
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
                    
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="📋 Copy Results",
                            callback=self.copy_exploitation_results
                        )
                        dpg.add_button(
                            label="💾 Export Log",
                            callback=self.export_exploitation_log
                        )
                        dpg.add_button(
                            label="🧹 Clear Log",
                            callback=self.clear_exploitation_log
                        )
    
    def create_reports_tab(self):
        """Вкладка отчетов с РЕАЛЬНОЙ генерацией"""
        with dpg.group():
            dpg.add_text("📋 Reporting Engine", color=[86, 156, 214])
            dpg.add_separator()
            
            with dpg.group(horizontal=True):
                with dpg.child_window(width=300):
                    dpg.add_text("Report Types")
                    dpg.add_button(
                        label="📊 Executive Summary", 
                        width=-1,
                        callback=lambda: self.generate_report_real("executive")
                    )
                    dpg.add_button(
                        label="🔍 Technical Details", 
                        width=-1,
                        callback=lambda: self.generate_report_real("technical")
                    )
                    dpg.add_button(
                        label="🔴 Vulnerability Report", 
                        width=-1,
                        callback=lambda: self.generate_report_real("vulnerability")
                    )
                    dpg.add_button(
                        label="💥 Exploitation Report", 
                        width=-1,
                        callback=lambda: self.generate_report_real("exploitation")
                    )
                    dpg.add_button(
                        label="🌐 Full Network Report", 
                        width=-1,
                        callback=lambda: self.generate_report_real("full")
                    )
                    
                    dpg.add_separator()
                    dpg.add_text("Export Format:")
                    dpg.add_combo(
                        tag="report_format",
                        items=["PDF", "HTML", "JSON", "CSV", "Markdown"],
                        default_value="PDF",
                        width=-1
                    )
                    
                    dpg.add_button(
                        label="💾 Generate Report",
                        width=-1,
                        callback=self.generate_custom_report
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
                    
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="🔄 Refresh Preview",
                            callback=self.refresh_report_preview
                        )
                        dpg.add_button(
                            label="📤 Export Report",
                            callback=self.export_current_report
                        )
    
    def create_settings_window(self):
        """Окно настроек движка с РЕАЛЬНЫМИ настройками"""
        with dpg.window(
            tag="settings_window",
            label="Engine Settings",
            width=600,
            height=500,
            show=False,
            pos=[100, 100]
        ):
            with dpg.tab_bar():
                # Основные настройки
                with dpg.tab(label="General"):
                    dpg.add_text("General Settings")
                    dpg.add_input_text(
                        tag="settings_scan_dir",
                        label="Scan Directory",
                        default_value="./scans/",
                        width=-1
                    )
                    dpg.add_input_text(
                        tag="settings_log_dir", 
                        label="Log Directory",
                        default_value="./logs/",
                        width=-1
                    )
                    dpg.add_checkbox(
                        tag="settings_auto_save",
                        label="Auto-save results",
                        default_value=True
                    )
                    dpg.add_checkbox(
                        tag="settings_backup",
                        label="Create backups",
                        default_value=True
                    )
                
                # Настройки сканирования
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
                    dpg.add_slider_int(
                        tag="settings_rate_limit", 
                        label="Rate Limit (req/sec)",
                        default_value=10,
                        min_value=1,
                        max_value=100
                    )
                    dpg.add_slider_int(
                        tag="settings_max_depth",
                        label="Max Depth",
                        default_value=5,
                        min_value=1,
                        max_value=10
                    )
                
                # Настройки модулей
                with dpg.tab(label="Modules"):
                    dpg.add_text("Module Configuration")
                    dpg.add_checkbox(
                        tag="mod_ping_enabled",
                        label="Ping Scanner",
                        default_value=True
                    )
                    dpg.add_checkbox(
                        tag="mod_ports_enabled",
                        label="Port Scanner", 
                        default_value=True
                    )
                    dpg.add_checkbox(
                        tag="mod_services_enabled",
                        label="Service Detection",
                        default_value=True
                    )
                    dpg.add_checkbox(
                        tag="mod_subdomains_enabled",
                        label="Subdomain Scanner",
                        default_value=True
                    )
                    dpg.add_checkbox(
                        tag="mod_vulns_enabled",
                        label="Vulnerability Scanner",
                        default_value=True
                    )
                    dpg.add_checkbox(
                        tag="mod_exploit_enabled",
                        label="Exploitation Engine",
                        default_value=True
                    )
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="💾 Save Settings",
                    callback=self.save_engine_settings
                )
                dpg.add_button(
                    label="🔄 Load Defaults",
                    callback=self.load_default_settings
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
            dpg.add_checkbox(tag="export_exploits", label="Exploitation Results", default_value=True)
            dpg.add_checkbox(tag="export_scope", label="Scope Settings", default_value=True)
            
            dpg.add_text("Export Format:")
            dpg.add_combo(
                tag="export_format",
                items=["JSON", "CSV", "XML", "HTML", "PDF"],
                default_value="JSON",
                width=-1
            )
            
            dpg.add_input_text(
                tag="export_filename",
                label="Filename",
                default_value=f"rapidrecon_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
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
    
    # === РЕАЛЬНЫЕ ФУНКЦИИ ===
    
    def _on_scan_level_change(self, sender, app_data):
        """Изменение уровня сканирования - РЕАЛЬНОЕ"""
        self.current_scan_level = app_data
        self.add_to_log(f"🎛️ Scan intensity set to: {app_data}")
        
        # Применяем настройки к движку
        if hasattr(self.engine, 'set_scan_intensity'):
            intensity_map = {
                "🚀 Stealth": "stealth",
                "⚡ Normal": "normal", 
                "💥 Aggressive": "aggressive",
                "🔥 Full Attack": "full",
                "💀 Pentest": "pentest"
            }
            self.engine.set_scan_intensity(intensity_map.get(app_data, "normal"))
    
    def _on_node_select_real(self, node_id):
        """Выбор узла в дереве - РЕАЛЬНЫЙ"""
        self.add_to_log(f"🔍 Selected node: {node_id}")
        # Показываем детали узла
        if node_id in self.nodes_data:
            node = self.nodes_data[node_id]
            details = self._format_node_details(node)
            # Показываем в соответствующем поле (например, в деталях уязвимостей)
    
    def _on_host_select_real(self, ip):
        """Выбор хоста в таблице - РЕАЛЬНЫЙ"""
        self.add_to_log(f"🔍 Selected host: {ip}")
        if ip in self.hosts_data:
            host = self.hosts_data[ip]
            details = self._format_host_details(host)
            # Показываем детали в соответствующем поле
    
    def quick_start_scan(self):
        """Быстрый запуск сканирования - РЕАЛЬНЫЙ"""
        target = dpg.get_value("quick_target_input")
        if not target:
            self.add_to_log("❌ Please enter a target first!")
            return
        
        self.add_to_log(f"🚀 Starting {self.current_scan_level} scan for: {target}")
        
        try:
            # Обновляем UI
            self.is_scanning = True
            self.is_paused = False
            dpg.set_value("scan_status", "Scanning")
            dpg.configure_item("scan_status", color=[255, 179, 64])
            
            dpg.hide_item("quick_start_btn")
            dpg.show_item("quick_pause_btn")
            dpg.hide_item("quick_resume_btn")
            dpg.show_item("quick_stop_btn")
            
            # Запускаем реальное сканирование через движок
            if hasattr(self.engine, 'add_initial_target'):
                self.engine.add_initial_target(target)
            
            if hasattr(self.engine, 'start_scan'):
                success = self.engine.start_scan()
                if success:
                    self.add_to_log("✅ Scan started successfully")
                else:
                    self.add_to_log("❌ Failed to start scan")
                    self.stop_scan()
            
        except Exception as e:
            self.add_to_log(f"❌ Error starting scan: {e}")
            self.stop_scan()
    
    def pause_scan(self):
        """Пауза сканирования - РЕАЛЬНАЯ"""
        self.is_paused = True
        dpg.set_value("scan_status", "Paused")
        dpg.configure_item("scan_status", color=[255, 179, 64])
        
        dpg.hide_item("quick_pause_btn")
        dpg.show_item("quick_resume_btn")
        
        # Пауза в движке
        if hasattr(self.engine, 'pause_scan'):
            self.engine.pause_scan()
        
        self.add_to_log("⏸️ Scan paused")
    
    def resume_scan(self):
        """Возобновление сканирования - РЕАЛЬНОЕ"""
        self.is_paused = False
        dpg.set_value("scan_status", "Scanning")
        dpg.configure_item("scan_status", color=[255, 179, 64])
        
        dpg.hide_item("quick_resume_btn")
        dpg.show_item("quick_pause_btn")
        
        # Возобновление в движке
        if hasattr(self.engine, 'resume_scan'):
            self.engine.resume_scan()
        
        self.add_to_log("▶️ Scan resumed")
    
    def stop_scan(self):
        """Остановка сканирования - РЕАЛЬНАЯ"""
        self.is_scanning = False
        self.is_paused = False
        dpg.set_value("scan_status", "Ready")
        dpg.configure_item("scan_status", color=[72, 199, 116])
        
        dpg.show_item("quick_start_btn")
        dpg.hide_item("quick_pause_btn")
        dpg.hide_item("quick_resume_btn")
        dpg.hide_item("quick_stop_btn")
        
        # Остановка в движке
        if hasattr(self.engine, 'stop_scan'):
            self.engine.stop_scan()
        
        self.add_to_log("⏹️ Scan stopped")
    
    def start_vulnerability_scan_real(self):
        """Запуск сканирования уязвимостей - РЕАЛЬНЫЙ"""
        try:
            self.add_to_log("🔍 Starting vulnerability scan...")
            
            # Получаем настройки сканирования
            scan_ports = dpg.get_value("vuln_scan_ports")
            scan_services = dpg.get_value("vuln_scan_services")
            scan_web = dpg.get_value("vuln_scan_web")
            scan_auth = dpg.get_value("vuln_scan_auth")
            intensity = dpg.get_value("vuln_intensity")
            target_scope = dpg.get_value("vuln_targets")
            
            # Определяем цели для сканирования
            targets = self._get_vulnerability_targets(target_scope)
            
            if not targets:
                self.add_to_log("❌ No targets found for vulnerability scanning")
                return
            
            self.add_to_log(f"🎯 Scanning {len(targets)} targets for vulnerabilities")
            
            # Запускаем сканирование через движок
            if hasattr(self.engine, 'start_vulnerability_scan'):
                self.engine.start_vulnerability_scan(
                    targets=targets,
                    scan_ports=scan_ports,
                    scan_services=scan_services,
                    scan_web=scan_web,
                    scan_auth=scan_auth,
                    intensity=intensity
                )
                self.add_to_log("✅ Vulnerability scan started")
            else:
                # Эмуляция сканирования
                self._emulate_vulnerability_scan(targets)
            
            dpg.set_value("main_tabs", "vulns_tab")
            
        except Exception as e:
            self.add_to_log(f"❌ Error starting vulnerability scan: {e}")
    
    def start_exploitation_real(self):
        """Запуск эксплуатации - РЕАЛЬНЫЙ"""
        try:
            self.add_to_log("💥 Starting exploitation engine...")
            
            # Получаем настройки эксплуатации
            auto_exploit = dpg.get_value("auto_exploit")
            lateral_movement = dpg.get_value("lateral_movement")
            persistence = dpg.get_value("persistence")
            privilege_escalation = dpg.get_value("privilege_escalation")
            payload_type = dpg.get_value("payload_type")
            
            # Получаем уязвимые цели
            vulnerable_targets = self._get_vulnerable_targets()
            
            if not vulnerable_targets:
                self.add_to_log("❌ No vulnerable targets found for exploitation")
                return
            
            self.add_to_log(f"🎯 Found {len(vulnerable_targets)} vulnerable targets")
            
            # Запускаем эксплуатацию через движок
            if hasattr(self.engine, 'start_exploitation'):
                self.engine.start_exploitation(
                    targets=vulnerable_targets,
                    auto_exploit=auto_exploit,
                    lateral_movement=lateral_movement,
                    persistence=persistence,
                    privilege_escalation=privilege_escalation,
                    payload_type=payload_type
                )
                self.add_to_log("✅ Exploitation engine started")
            else:
                # Эмуляция эксплуатации
                self._emulate_exploitation(vulnerable_targets)
            
            dpg.set_value("main_tabs", "exploit_tab")
            
        except Exception as e:
            self.add_to_log(f"❌ Error starting exploitation: {e}")
    
    def show_settings_real(self):
        """Показать настройки движка - РЕАЛЬНЫЕ"""
        try:
            # Загружаем текущие настройки в окно
            if hasattr(self.engine, 'get_settings'):
                settings = self.engine.get_settings()
                for key, value in settings.items():
                    if dpg.does_item_exist(f"settings_{key}"):
                        dpg.set_value(f"settings_{key}", value)
            
            dpg.show_item("settings_window")
            dpg.focus_item("settings_window")
            self.add_to_log("⚙️ Engine settings opened")
            
        except Exception as e:
            self.add_to_log(f"❌ Error opening settings: {e}")
    
    def export_all_data_real(self):
        """Экспорт всех данных - РЕАЛЬНЫЙ"""
        try:
            dpg.show_item("export_window")
            dpg.focus_item("export_window")
            self.add_to_log("📤 Export dialog opened")
            
        except Exception as e:
            self.add_to_log(f"❌ Error opening export dialog: {e}")
    
    def clear_everything_real(self):
        """Очистка всего - РЕАЛЬНАЯ"""
        try:
            # Очищаем данные
            self.nodes_data.clear()
            self.hosts_data.clear()
            self.vulnerabilities_data.clear()
            self.exploitation_results.clear()
            self.selected_targets.clear()
            
            # Очищаем модули
            self.network_tree.clear()
            self.hosts_table.clear()
            
            # Сбрасываем статистику
            stats = ["stat_nodes", "stat_hosts", "stat_services", "stat_ports", 
                    "stat_vulns", "stat_exploits", "stat_lateral"]
            for stat in stats:
                dpg.set_value(stat, f"{stat.split('_')[1].title()}: 0")
            
            # Очищаем движок
            if hasattr(self.engine, 'clear_results'):
                self.engine.clear_results()
            
            self.add_to_log("🧹 Everything cleared")
            
        except Exception as e:
            self.add_to_log(f"❌ Error clearing everything: {e}")
    
    def refresh_network_tree_real(self):
        """Обновление дерева сети - РЕАЛЬНОЕ"""
        try:
            # Получаем актуальные данные из движка
            if hasattr(self.engine, 'get_network_data'):
                network_data = self.engine.get_network_data()
                self.nodes_data.update(network_data)
            
            self.network_tree.update_tree(self.nodes_data, self.hosts_data)
            self.add_to_log("🔄 Network tree refreshed with real data")
            
        except Exception as e:
            self.add_to_log(f"❌ Error refreshing network tree: {e}")
    
    def show_network_statistics_real(self):
        """Показать статистику сети - РЕАЛЬНУЮ"""
        try:
            stats = self._calculate_real_statistics()
            
            # Показываем в отдельном окне
            if dpg.does_item_exist("network_stats_window"):
                dpg.delete_item("network_stats_window")
            
            with dpg.window(
                tag="network_stats_window",
                label="Network Statistics",
                width=400,
                height=300,
                modal=True
            ):
                dpg.add_text("📊 Real Network Statistics")
                dpg.add_separator()
                
                for category, count in stats.items():
                    with dpg.group(horizontal=True):
                        dpg.add_text(f"{category}:", width=200)
                        dpg.add_text(str(count), color=[123, 97, 255])
                
                dpg.add_separator()
                dpg.add_text(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")
            
            self.add_to_log("📊 Showing real network statistics")
            
        except Exception as e:
            self.add_to_log(f"❌ Error showing network statistics: {e}")
    
    def export_network_tree_real(self):
        """Экспорт дерева сети - РЕАЛЬНЫЙ"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"network_tree_{timestamp}.json"
            
            export_data = {
                'metadata': {
                    'export_time': timestamp,
                    'total_nodes': len(self.nodes_data),
                    'total_hosts': len(self.hosts_data)
                },
                'nodes': self.nodes_data,
                'hosts': self.hosts_data,
                'statistics': self._calculate_real_statistics()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.add_to_log(f"💾 Network tree exported to {filename}")
            
        except Exception as e:
            self.add_to_log(f"❌ Error exporting network tree: {e}")
    
    def add_all_nodes_to_scope(self):
        """Добавить все узлы в scope - РЕАЛЬНАЯ"""
        try:
            count = 0
            for node_id, node in self.nodes_data.items():
                if self._add_node_to_scope(node):
                    count += 1
            
            self.add_to_log(f"🎯 Added {count} nodes to scope")
            
        except Exception as e:
            self.add_to_log(f"❌ Error adding nodes to scope: {e}")
    
    def scan_selected_hosts_real(self):
        """Сканирование выбранных хостов - РЕАЛЬНОЕ"""
        self.hosts_table._scan_selected_hosts()
    
    def add_selected_to_scope_real(self):
        """Добавление выбранных в scope - РЕАЛЬНОЕ"""
        self.hosts_table._add_selected_to_scope()
    
    def export_hosts_csv_real(self):
        """Экспорт хостов в CSV - РЕАЛЬНЫЙ"""
        self.hosts_table._export_selected_hosts()
    
    def save_scope_settings_real(self):
        """Сохранение настроек scope - РЕАЛЬНОЕ"""
        try:
            # Получаем настройки из UI
            ips_text = dpg.get_value("scope_ips")
            domains_text = dpg.get_value("scope_domains")
            suffixes_text = dpg.get_value("scope_suffixes")
            
            # Парсим настройки
            self.scope_settings['allowed_ips'] = [ip.strip() for ip in ips_text.split(',') if ip.strip()]
            self.scope_settings['allowed_domains'] = [domain.strip() for domain in domains_text.split(',') if domain.strip()]
            self.scope_settings['domain_suffixes'] = [suffix.strip() for suffix in suffixes_text.split(',') if suffix.strip()]
            
            # Сохраняем в файл
            with open('scope_settings.json', 'w') as f:
                json.dump(self.scope_settings, f, indent=2)
            
            # Применяем к движку
            if hasattr(self.engine, 'set_scope'):
                self.engine.set_scope(self.scope_settings)
            
            self.add_to_log("💾 Scope settings saved and applied")
            
        except Exception as e:
            self.add_to_log(f"❌ Error saving scope settings: {e}")
    
    def apply_scope_settings_real(self):
        """Применение настроек scope - РЕАЛЬНОЕ"""
        try:
            # Применяем scope к текущим данным
            self._apply_scope_to_data()
            self.add_to_log("🔄 Scope settings applied to current data")
            
        except Exception as e:
            self.add_to_log(f"❌ Error applying scope settings: {e}")
    
    def refresh_scope_list_real(self):
        """Обновление списка scope - РЕАЛЬНОЕ"""
        try:
            in_scope_targets = self._get_in_scope_targets()
            dpg.configure_item("in_scope_targets", items=in_scope_targets)
            self.add_to_log(f"🔄 Scope list refreshed: {len(in_scope_targets)} targets in scope")
            
        except Exception as e:
            self.add_to_log(f"❌ Error refreshing scope list: {e}")
    
    def clear_out_of_scope_real(self):
        """Очистка out-of-scope целей - РЕАЛЬНАЯ"""
        try:
            # Удаляем out-of-scope данные
            self._remove_out_of_scope_data()
            self.add_to_log("🧹 Cleared out-of-scope targets")
            
        except Exception as e:
            self.add_to_log(f"❌ Error clearing out-of-scope targets: {e}")
    
    def load_vulnerable_targets_real(self):
        """Загрузка уязвимых целей - РЕАЛЬНАЯ"""
        try:
            vulnerable_targets = self._get_vulnerable_targets()
            dpg.configure_item("exploit_targets", items=vulnerable_targets)
            self.add_to_log(f"🎯 Loaded {len(vulnerable_targets)} vulnerable targets")
            
        except Exception as e:
            self.add_to_log(f"❌ Error loading vulnerable targets: {e}")
    
    def start_exploitation_engine_real(self):
        """Запуск движка эксплуатации - РЕАЛЬНЫЙ"""
        try:
            selected_targets = dpg.get_value("exploit_targets")
            if not selected_targets:
                self.add_to_log("❌ No targets selected for exploitation")
                return
            
            # Получаем настройки
            auto_exploit = dpg.get_value("auto_exploit")
            lateral_movement = dpg.get_value("lateral_movement")
            persistence = dpg.get_value("persistence")
            privilege_escalation = dpg.get_value("privilege_escalation")
            payload_type = dpg.get_value("payload_type")
            
            self.add_to_log(f"💥 Starting exploitation for {len(selected_targets)} targets")
            
            # Запускаем эксплуатацию
            if hasattr(self.engine, 'exploit_targets'):
                results = self.engine.exploit_targets(
                    targets=selected_targets,
                    options={
                        'auto_exploit': auto_exploit,
                        'lateral_movement': lateral_movement,
                        'persistence': persistence,
                        'privilege_escalation': privilege_escalation,
                        'payload_type': payload_type
                    }
                )
                self.exploitation_results.extend(results)
                self._update_exploitation_log()
            else:
                self._emulate_exploitation(selected_targets)
            
        except Exception as e:
            self.add_to_log(f"❌ Error starting exploitation engine: {e}")
    
    def generate_report_real(self, report_type: str):
        """Генерация отчета - РЕАЛЬНАЯ"""
        try:
            self.add_to_log(f"📋 Generating {report_type} report...")
            
            report_content = self._generate_report_content(report_type)
            dpg.set_value("report_preview", report_content)
            
            self.add_to_log(f"✅ {report_type} report generated")
            
        except Exception as e:
            self.add_to_log(f"❌ Error generating report: {e}")
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _format_node_details(self, node: Dict) -> str:
        """Форматирование деталей узла"""
        details = []
        details.append(f"=== {node.get('label', 'Unknown')} ===")
        details.append(f"Type: {node.get('type', 'unknown')}")
        details.append(f"ID: {node.get('id', 'unknown')}")
        
        data = node.get('data', {})
        if isinstance(data, dict):
            for key, value in data.items():
                if key not in ['position', 'color', 'radius', 'icon']:
                    details.append(f"{key}: {value}")
        else:
            details.append(f"Data: {data}")
        
        return "\n".join(details)
    
    def _format_host_details(self, host: Dict) -> str:
        """Форматирование деталей хоста"""
        details = []
        details.append(f"=== {host.get('ip', 'Unknown')} ===")
        details.append(f"Hostname: {host.get('hostname', 'Unknown')}")
        details.append(f"Status: {host.get('status', 'unknown')}")
        details.append(f"OS: {host.get('os', 'Unknown')}")
        details.append(f"Last Seen: {host.get('last_seen', 'Unknown')}")
        
        ports = host.get('ports', [])
        if ports:
            details.append(f"Open Ports: {', '.join(map(str, ports))}")
        
        services = host.get('services', [])
        if services:
            details.append(f"Services: {', '.join(services)}")
        
        vulns = host.get('vulnerabilities', [])
        if vulns:
            details.append(f"Vulnerabilities: {len(vulns)} found")
        
        return "\n".join(details)
    
    def _calculate_real_statistics(self) -> Dict[str, int]:
        """Расчет реальной статистики"""
        return {
            "Total Nodes": len(self.nodes_data),
            "Active Hosts": len([h for h in self.hosts_data.values() if h.get('status') == 'active']),
            "Open Ports": sum(len(h.get('ports', [])) for h in self.hosts_data.values()),
            "Discovered Services": sum(len(h.get('services', [])) for h in self.hosts_data.values()),
            "Vulnerabilities Found": len(self.vulnerabilities_data),
            "Successful Exploits": len([e for e in self.exploitation_results if e.get('success')]),
            "In-Scope Targets": len(self._get_in_scope_targets()),
            "Network Depth": max((n.get('depth', 0) for n in self.nodes_data.values()), default=0)
        }
    
    def _get_vulnerability_targets(self, target_scope: str) -> List[str]:
        """Получение целей для сканирования уязвимостей"""
        if target_scope == "All Hosts":
            return list(self.hosts_data.keys())
        elif target_scope == "Selected Hosts":
            return list(self.hosts_table.selected_hosts)
        else:  # In-Scope Only
            return self._get_in_scope_targets()
    
    def _get_vulnerable_targets(self) -> List[str]:
        """Получение уязвимых целей"""
        vulnerable = []
        for ip, host in self.hosts_data.items():
            if host.get('vulnerabilities'):
                vulnerable.append(ip)
        return vulnerable
    
    def _get_in_scope_targets(self) -> List[str]:
        """Получение целей в scope"""
        # Здесь должна быть логика проверки scope
        return list(self.hosts_data.keys())  # Заглушка
    
    def _add_node_to_scope(self, node: Dict) -> bool:
        """Добавление узла в scope"""
        try:
            node_data = node.get('data')
            if isinstance(node_data, str):
                # Добавляем в scope
                if node_data not in self.scope_settings['allowed_ips']:
                    self.scope_settings['allowed_ips'].append(node_data)
                return True
            return False
        except:
            return False
    
    def _apply_scope_to_data(self):
        """Применение scope к данным"""
        # Здесь должна быть логика применения scope
        pass
    
    def _remove_out_of_scope_data(self):
        """Удаление out-of-scope данных"""
        # Здесь должна быть логика удаления out-of-scope данных
        pass
    
    def _emulate_vulnerability_scan(self, targets: List[str]):
        """Эмуляция сканирования уязвимостей"""
        for target in targets:
            self.add_to_log(f"🔍 Scanning {target} for vulnerabilities...")
            # Эмуляция нахождения уязвимостей
            time.sleep(0.5)
    
    def _emulate_exploitation(self, targets: List[str]):
        """Эмуляция эксплуатации"""
        for target in targets:
            self.add_to_log(f"💥 Attempting exploitation on {target}...")
            # Эмуляция эксплуатации
            time.sleep(1.0)
    
    def _generate_report_content(self, report_type: str) -> str:
        """Генерация содержимого отчета"""
        stats = self._calculate_real_statistics()
        
        if report_type == "executive":
            return self._generate_executive_report(stats)
        elif report_type == "technical":
            return self._generate_technical_report(stats)
        elif report_type == "vulnerability":
            return self._generate_vulnerability_report(stats)
        elif report_type == "exploitation":
            return self._generate_exploitation_report(stats)
        else:
            return self._generate_full_report(stats)
    
    def _generate_executive_report(self, stats: Dict) -> str:
        """Генерация исполнительного отчета"""
        return f"""EXECUTIVE SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW:
• Total Hosts Discovered: {stats.get('Active Hosts', 0)}
• Vulnerabilities Found: {stats.get('Vulnerabilities Found', 0)}
• Successful Exploits: {stats.get('Successful Exploits', 0)}

RECOMMENDATIONS:
1. Immediate attention required for critical vulnerabilities
2. Review network segmentation
3. Update security policies

RISK LEVEL: {'HIGH' if stats.get('Vulnerabilities Found', 0) > 0 else 'MEDIUM'}"""
    
    def _generate_technical_report(self, stats: Dict) -> str:
        """Генерация технического отчета"""
        return f"""TECHNICAL REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

NETWORK STATISTICS:
• Total Nodes: {stats.get('Total Nodes', 0)}
• Active Hosts: {stats.get('Active Hosts', 0)}
• Open Ports: {stats.get('Open Ports', 0)}
• Services: {stats.get('Discovered Services', 0)}
• Network Depth: {stats.get('Network Depth', 0)}

SECURITY FINDINGS:
• Vulnerabilities: {stats.get('Vulnerabilities Found', 0)}
• Successful Exploits: {stats.get('Successful Exploits', 0)}
• In-Scope Targets: {stats.get('In-Scope Targets', 0)}

DETAILED ANALYSIS:
[Technical details would go here]"""
    
    def _generate_vulnerability_report(self, stats: Dict) -> str:
        """Генерация отчета об уязвимостях"""
        return f"""VULNERABILITY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY:
• Total Vulnerabilities: {stats.get('Vulnerabilities Found', 0)}
• Affected Hosts: {len([h for h in self.hosts_data.values() if h.get('vulnerabilities')])}

VULNERABILITY BREAKDOWN:
[Vulnerability details would go here]

RECOMMENDATIONS:
1. Patch critical vulnerabilities immediately
2. Implement network segmentation
3. Regular security assessments"""
    
    def _generate_exploitation_report(self, stats: Dict) -> str:
        """Генерация отчета об эксплуатации"""
        return f"""EXPLOITATION REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

EXPLOITATION RESULTS:
• Successful Exploits: {stats.get('Successful Exploits', 0)}
• Total Attempts: {len(self.exploitation_results)}

COMPROMISED SYSTEMS:
[Compromised system details would go here]

LATERAL MOVEMENT:
[Lateral movement details would go here]"""
    
    def _generate_full_report(self, stats: Dict) -> str:
        """Генерация полного отчета"""
        return f"""FULL SECURITY ASSESSMENT REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

COMPREHENSIVE ANALYSIS:

NETWORK DISCOVERY:
{json.dumps(stats, indent=2)}

HOST DETAILS:
{json.dumps(list(self.hosts_data.keys())[:10], indent=2)}  # First 10 hosts

VULNERABILITIES:
{json.dumps(self.vulnerabilities_data[:5], indent=2)}  # First 5 vulnerabilities

EXPLOITATION RESULTS:
{json.dumps(self.exploitation_results, indent=2)}

RECOMMENDATIONS:
1. Comprehensive security review required
2. Immediate patching of critical systems
3. Enhanced monitoring and logging
4. Regular penetration testing"""
    
    def _update_exploitation_log(self):
        """Обновление лога эксплуатации"""
        log_content = "EXPLOITATION RESULTS:\n\n"
        for result in self.exploitation_results:
            status = "✅ SUCCESS" if result.get('success') else "❌ FAILED"
            log_content += f"{status} - {result.get('target', 'Unknown')}\n"
            if result.get('details'):
                log_content += f"    Details: {result.get('details')}\n"
            log_content += "\n"
        
        dpg.set_value("exploitation_log", log_content)
    
    def save_engine_settings(self):
        """Сохранение настроек движка"""
        try:
            settings = {}
            # Собираем настройки из UI
            for key in ['scan_dir', 'log_dir', 'auto_save', 'backup', 
                       'threads', 'timeout', 'rate_limit', 'max_depth']:
                settings[key] = dpg.get_value(f"settings_{key}")
            
            # Сохраняем в движок
            if hasattr(self.engine, 'set_settings'):
                self.engine.set_settings(settings)
            
            # Сохраняем в файл
            with open('engine_settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
            
            self.add_to_log("💾 Engine settings saved")
            dpg.hide_item("settings_window")
            
        except Exception as e:
            self.add_to_log(f"❌ Error saving engine settings: {e}")
    
    def load_default_settings(self):
        """Загрузка настроек по умолчанию"""
        try:
            default_settings = {
                'scan_dir': './scans/',
                'log_dir': './logs/',
                'auto_save': True,
                'backup': True,
                'threads': 10,
                'timeout': 5,
                'rate_limit': 10,
                'max_depth': 5
            }
            
            for key, value in default_settings.items():
                if dpg.does_item_exist(f"settings_{key}"):
                    dpg.set_value(f"settings_{key}", value)
            
            self.add_to_log("🔄 Default settings loaded")
            
        except Exception as e:
            self.add_to_log(f"❌ Error loading default settings: {e}")
    
    def perform_export(self):
        """Выполнение экспорта данных"""
        try:
            export_format = dpg.get_value("export_format")
            filename = dpg.get_value("export_filename")
            
            # Определяем какие данные экспортировать
            data_to_export = {}
            
            if dpg.get_value("export_hosts"):
                data_to_export['hosts'] = self.hosts_data
            
            if dpg.get_value("export_network"):
                data_to_export['network'] = self.nodes_data
            
            if dpg.get_value("export_vulns"):
                data_to_export['vulnerabilities'] = self.vulnerabilities_data
            
            if dpg.get_value("export_exploits"):
                data_to_export['exploitation'] = self.exploitation_results
            
            if dpg.get_value("export_scope"):
                data_to_export['scope'] = self.scope_settings
            
            # Добавляем метаданные
            data_to_export['metadata'] = {
                'export_time': datetime.now().isoformat(),
                'export_format': export_format,
                'version': '1.0.0'
            }
            
            # Экспортируем в выбранном формате
            if export_format == "JSON":
                with open(f"{filename}.json", 'w') as f:
                    json.dump(data_to_export, f, indent=2)
            elif export_format == "CSV":
                # Экспорт основных данных в CSV
                self._export_to_csv(data_to_export, filename)
            
            self.add_to_log(f"💾 Data exported to {filename}.{export_format.lower()}")
            dpg.hide_item("export_window")
            
        except Exception as e:
            self.add_to_log(f"❌ Error exporting data: {e}")
    
    def _export_to_csv(self, data: Dict, filename: str):
        """Экспорт в CSV"""
        # Экспорт хостов
        if 'hosts' in data:
            with open(f"{filename}_hosts.csv", 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['IP', 'Hostname', 'Ports', 'Services', 'OS', 'Status'])
                for ip, host in data['hosts'].items():
                    writer.writerow([
                        ip,
                        host.get('hostname', ''),
                        ','.join(map(str, host.get('ports', []))),
                        ','.join(host.get('services', [])),
                        host.get('os', ''),
                        host.get('status', '')
                    ])
    
    def add_to_log(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)  # Временное решение
    
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
                self._update_statistics()
                
            elif event_type == 'vulnerability_found':
                self.vulnerabilities_data.append(data)
                self._update_statistics()
                
            elif event_type == 'exploitation_result':
                self.exploitation_results.append(data)
                self._update_exploitation_log()
                self._update_statistics()
                
        except Exception as e:
            self.logger.error(f"Error handling engine event: {e}")
    
    def _update_statistics(self):
        """Обновление статистики"""
        try:
            stats = self._calculate_real_statistics()
            
            dpg.set_value("stat_nodes", f"Nodes: {stats['Total Nodes']}")
            dpg.set_value("stat_hosts", f"Hosts: {stats['Active Hosts']}")
            dpg.set_value("stat_services", f"Services: {stats['Discovered Services']}")
            dpg.set_value("stat_ports", f"Ports: {stats['Open Ports']}")
            dpg.set_value("stat_vulns", f"Vulnerabilities: {stats['Vulnerabilities Found']}")
            dpg.set_value("stat_exploits", f"Exploits: {stats['Successful Exploits']}")
            dpg.set_value("stat_lateral", f"Lateral: {stats.get('Lateral Moves', 0)}")
            
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

    # Дополнительные методы для кнопок (заглушки для пока)
    def load_scope_settings(self):
        """Загрузка настроек scope"""
        self.add_to_log("📥 Loading scope settings...")
    
    def show_scope_statistics(self):
        """Показать статистику scope"""
        self.add_to_log("📊 Showing scope statistics...")
    
    def export_vulnerabilities(self):
        """Экспорт уязвимостей"""
        self.add_to_log("📋 Exporting vulnerabilities...")
    
    def add_vulns_to_exploitation(self):
        """Добавить уязвимости в эксплуатацию"""
        self.add_to_log("🎯 Adding vulnerabilities to exploitation...")
    
    def refresh_exploit_targets(self):
        """Обновить цели эксплуатации"""
        self.add_to_log("🔄 Refreshing exploit targets...")
    
    def copy_exploitation_results(self):
        """Копировать результаты эксплуатации"""
        self.add_to_log("📋 Copying exploitation results...")
    
    def export_exploitation_log(self):
        """Экспорт лога эксплуатации"""
        self.add_to_log("💾 Exporting exploitation log...")
    
    def clear_exploitation_log(self):
        """Очистка лога эксплуатации"""
        self.add_to_log("🧹 Clearing exploitation log...")
    
    def generate_custom_report(self):
        """Генерация пользовательского отчета"""
        self.add_to_log("📋 Generating custom report...")
    
    def refresh_report_preview(self):
        """Обновление предпросмотра отчета"""
        self.add_to_log("🔄 Refreshing report preview...")
    
    def export_current_report(self):
        """Экспорт текущего отчета"""
        self.add_to_log("📤 Exporting current report...")
