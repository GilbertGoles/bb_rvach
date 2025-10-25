"""
Главное окно RapidRecon - полная версия с модулями и управлением
"""
import dearpygui.dearpygui as dpg
from typing import Dict, Any, List, Optional
import logging
import traceback
import sys
import os
import time
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
    Полный интерфейс RapidRecon с управлением и модулями
    """
    
    def __init__(self, engine, module_manager):
        self.engine = engine
        self.module_manager = module_manager
        self.logger = logging.getLogger('RapidRecon.GUI')
        
        # Модули интерфейса
        self.network_tree = NetworkTree()
        self.hosts_table = HostsTable()
        
        # Состояние
        self.is_scanning = False
        self.is_paused = False
        self.current_scan_level = "⚡ Normal"
        self.selected_targets = set()
        
        # Данные
        self.hosts_data = {}
        self.nodes_data = {}
        
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
                label="🔍 Scan for Vulnerabilities",
                width=-1,
                callback=self.scan_vulnerabilities
            )
            dpg.add_button(
                label="💥 Start Exploitation", 
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
            # 1. Вкладка дерева сети
            with dpg.tab(label="🌐 Network Tree", tag="tree_tab"):
                self.create_network_tree_tab()
            
            # 2. Вкладка таблицы хостов
            with dpg.tab(label="📊 Hosts Table", tag="table_tab"):
                self.create_hosts_table_tab()
            
            # 3. Вкладка управления scope
            with dpg.tab(label="🎯 Scope Manager", tag="scope_tab"):
                self.create_scope_manager_tab()
            
            # 4. Вкладка уязвимостей
            with dpg.tab(label="🔴 Vulnerabilities", tag="vulns_tab"):
                self.create_vulnerabilities_tab()
            
            # 5. Вкладка эксплуатации
            with dpg.tab(label="💥 Exploitation", tag="exploit_tab"):
                self.create_exploitation_tab()
            
            # 6. Вкладка lateral movement
            with dpg.tab(label="🔄 Lateral Movement", tag="lateral_tab"):
                self.create_lateral_movement_tab()
            
            # 7. Вкладка отчетов
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
            
            # Дерево сети
            self.network_tree_panel = self.network_tree.create_tree_panel("tree_tab")
            
            # Устанавливаем callback для выбора узлов
            self.network_tree.set_node_select_callback(self._on_node_select)
    
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
            self.hosts_table_panel = self.hosts_table.create_table_panel("table_tab")
            
            # Устанавливаем callback для выбора хостов
            self.hosts_table.set_host_select_callback(self._on_host_select)
    
    def create_scope_manager_tab(self):
        """Вкладка управления scope"""
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
                        callback=self.save_scope_settings
                    )
                    dpg.add_button(
                        label="🔄 Apply Scope",
                        callback=self.apply_scope_settings
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
                        callback=self.refresh_scope_list
                    )
                    dpg.add_button(
                        label="🧹 Clear Out-of-Scope",
                        callback=self.clear_out_of_scope
                    )
    
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
                    dpg.add_checkbox(tag="persistence", label="Establish Persistence", default_value=True)
                    
                    exploit_btn = dpg.add_button(
                        label="💥 Start Exploitation",
                        width=-1,
                        callback=self.start_exploitation_engine
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
                        dpg.add_button(label="📋 Copy Results")
                        dpg.add_button(label="💾 Export Log")
    
    def create_lateral_movement_tab(self):
        """Вкладка lateral movement"""
        with dpg.group():
            dpg.add_text("🔄 Lateral Movement", color=[255, 165, 0])
            dpg.add_separator()
            dpg.add_text("Lateral Movement Module - Coming Soon", color=[150, 150, 160])
            dpg.add_text("This module will enable moving through the network after initial compromise.")
    
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
    
    # === ОБРАБОТЧИКИ СОБЫТИЙ ===
    
    def _on_scan_level_change(self, sender, app_data):
        """Изменение уровня сканирования"""
        self.current_scan_level = app_data
        self.add_to_log(f"🎛️ Scan intensity set to: {app_data}")
    
    def _on_node_select(self, node_id):
        """Выбор узла в дереве"""
        self.add_to_log(f"🔍 Selected node: {node_id}")
        # Показываем детали узла в соответствующем поле
    
    def _on_host_select(self, ip):
        """Выбор хоста в таблице"""
        self.add_to_log(f"🔍 Selected host: {ip}")
        # Показываем детали хоста
    
    def quick_start_scan(self):
        """Быстрый запуск сканирования"""
        target = dpg.get_value("quick_target_input")
        if not target:
            self.add_to_log("❌ Please enter a target first!")
            return
        
        self.add_to_log(f"🚀 Starting {self.current_scan_level} scan for: {target}")
        
        # Обновляем UI
        self.is_scanning = True
        self.is_paused = False
        dpg.set_value("scan_status", "Scanning")
        dpg.configure_item("scan_status", color=[255, 179, 64])
        
        dpg.hide_item("quick_start_btn")
        dpg.show_item("quick_pause_btn")
        dpg.hide_item("quick_resume_btn")
        dpg.show_item("quick_stop_btn")
        
        # Запускаем сканирование
        if hasattr(self.engine, 'add_initial_target'):
            self.engine.add_initial_target(target)
        
        if hasattr(self.engine, 'start_scan'):
            self.engine.start_scan()
    
    def pause_scan(self):
        """Пауза сканирования"""
        self.is_paused = True
        dpg.set_value("scan_status", "Paused")
        dpg.configure_item("scan_status", color=[255, 179, 64])
        
        dpg.hide_item("quick_pause_btn")
        dpg.show_item("quick_resume_btn")
        
        self.add_to_log("⏸️ Scan paused")
    
    def resume_scan(self):
        """Возобновление сканирования"""
        self.is_paused = False
        dpg.set_value("scan_status", "Scanning")
        dpg.configure_item("scan_status", color=[255, 179, 64])
        
        dpg.hide_item("quick_resume_btn")
        dpg.show_item("quick_pause_btn")
        
        self.add_to_log("▶️ Scan resumed")
    
    def stop_scan(self):
        """Остановка сканирования"""
        self.is_scanning = False
        self.is_paused = False
        dpg.set_value("scan_status", "Ready")
        dpg.configure_item("scan_status", color=[72, 199, 116])
        
        dpg.show_item("quick_start_btn")
        dpg.hide_item("quick_pause_btn")
        dpg.hide_item("quick_resume_btn")
        dpg.hide_item("quick_stop_btn")
        
        self.add_to_log("⏹️ Scan stopped")
    
    def scan_vulnerabilities(self):
        """Сканирование уязвимостей"""
        self.add_to_log("🔍 Starting vulnerability scan...")
        dpg.set_value("main_tabs", "vulns_tab")
    
    def start_exploitation(self):
        """Запуск эксплуатации"""
        self.add_to_log("💥 Starting exploitation engine...")
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
        self.add_to_log("📊 Showing network statistics")
    
    def export_network_tree(self):
        """Экспорт дерева сети"""
        self.add_to_log("💾 Exporting network tree")
    
    def scan_selected_hosts(self):
        """Сканирование выбранных хостов"""
        self.add_to_log("🔍 Scanning selected hosts")
    
    def add_selected_to_scope(self):
        """Добавление выбранных в scope"""
        self.add_to_log("🎯 Adding selected hosts to scope")
    
    def export_hosts_csv(self):
        """Экспорт хостов в CSV"""
        self.add_to_log("💾 Exporting hosts to CSV")
    
    def save_scope_settings(self):
        """Сохранение настроек scope"""
        self.add_to_log("💾 Scope settings saved")
    
    def apply_scope_settings(self):
        """Применение настроек scope"""
        self.add_to_log("🔄 Scope settings applied")
    
    def refresh_scope_list(self):
        """Обновление списка scope"""
        self.add_to_log("🔄 Scope list refreshed")
    
    def clear_out_of_scope(self):
        """Очистка out-of-scope целей"""
        self.add_to_log("🧹 Cleared out-of-scope targets")
    
    def start_vulnerability_scan(self):
        """Запуск сканирования уязвимостей"""
        self.add_to_log("🔍 Starting vulnerability scan")
    
    def load_vulnerable_targets(self):
        """Загрузка уязвимых целей"""
        self.add_to_log("🎯 Loading vulnerable targets")
    
    def start_exploitation_engine(self):
        """Запуск движка эксплуатации"""
        self.add_to_log("💥 Starting exploitation engine")
    
    def generate_report(self):
        """Генерация отчета"""
        self.add_to_log("📋 Generating report")
    
    def show_settings(self):
        """Показать настройки"""
        self.add_to_log("⚙️ Showing engine settings")
    
    def export_all_data(self):
        """Экспорт всех данных"""
        self.add_to_log("📤 Exporting all data")
    
    def clear_everything(self):
        """Очистка всего"""
        self.nodes_data.clear()
        self.hosts_data.clear()
        self.network_tree.clear()
        self.hosts_table.clear()
        
        # Сбрасываем статистику
        stats = ["stat_nodes", "stat_hosts", "stat_services", "stat_ports", "stat_vulns", "stat_exploits", "stat_lateral"]
        for stat in stats:
            dpg.set_value(stat, f"{stat.split('_')[1].title()}: 0")
        
        self.add_to_log("🧹 Everything cleared")
    
    def add_to_log(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)  # Временное решение - выводим в консоль
    
    def handle_engine_event(self, event_type: str, data: Any = None):
        """Обработка событий от движка"""
        try:
            self.logger.info(f"GUI received event: {event_type}")
            
            if event_type in ['node_added', 'node_discovered', 'module_results']:
                # Обновляем данные
                if hasattr(self.engine, 'discovered_nodes'):
                    self.nodes_data = self.engine.discovered_nodes
                
                # Обновляем модули интерфейса
                self.network_tree.update_tree(self.nodes_data, self.hosts_data)
                self.hosts_table.update_table(self.hosts_data)
                
                # Обновляем статистику
                self._update_statistics()
                
        except Exception as e:
            self.logger.error(f"Error handling engine event: {e}")
    
    def _update_statistics(self):
        """Обновление статистики"""
        try:
            nodes_count = len(self.nodes_data)
            hosts_count = len(self.hosts_data)
            services_count = sum(1 for node in self.nodes_data.values() if node.get('type') == 'service')
            ports_count = sum(1 for node in self.nodes_data.values() if node.get('type') == 'open_ports')
            vulns_count = sum(1 for node in self.nodes_data.values() if node.get('type') == 'vulnerability')
            
            dpg.set_value("stat_nodes", f"Nodes: {nodes_count}")
            dpg.set_value("stat_hosts", f"Hosts: {hosts_count}")
            dpg.set_value("stat_services", f"Services: {services_count}")
            dpg.set_value("stat_ports", f"Ports: {ports_count}")
            dpg.set_value("stat_vulns", f"Vulnerabilities: {vulns_count}")
            
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
