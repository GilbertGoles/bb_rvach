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
        self.current_tab = "dashboard"
        
        # Данные
        self.hosts_data = {}
        self.nodes_data = {}
        
        # Инициализация GUI
        self.initialize_gui()
        
        self.logger.info("Графический интерфейс инициализирован")
    
    def initialize_gui(self):
        """Инициализация GUI"""
        try:
            dpg.create_context()
            
            # Создание темы
            self.obsidian_theme = ObsidianTheme.setup_theme()
            
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
            
            # Настройка и показ GUI
            dpg.bind_theme(self.obsidian_theme)
            dpg.setup_dearpygui()
            dpg.show_viewport()
            dpg.set_primary_window("main_window", True)
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации GUI: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def create_main_window(self):
        """Создание главного окна"""
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
            # Основной контейнер
            with dpg.group(horizontal=True, width=-1, height=-1):
                # Боковая панель
                with dpg.child_window(tag="sidebar", width=280, border=False):
                    self.create_sidebar()
                
                # Область контента
                with dpg.child_window(tag="content_area", width=-1, border=False):
                    self.create_dashboard_tab()
    
    def create_sidebar(self):
        """Создание боковой панели"""
        with dpg.group(parent="sidebar"):
            dpg.add_spacer(height=10)
            dpg.add_text("RapidRecon", color=[123, 97, 255])
            dpg.add_text("Security Scanner", color=[150, 150, 160])
            dpg.add_separator()
            
            # Статус
            with dpg.group(horizontal=True):
                dpg.add_text("Status:")
                dpg.add_text("Ready", tag="scan_status", color=[72, 199, 116])
            
            # Controls Panel
            self.controls_panel.create_controls_panel("sidebar")
            
            # Навигация
            with dpg.collapsing_header(label="Navigation", default_open=True):
                dpg.add_button(
                    label="Dashboard", 
                    width=-1,
                    callback=lambda: self.switch_tab("dashboard")
                )
                dpg.add_button(
                    label="Network Tree",
                    width=-1, 
                    callback=lambda: self.switch_tab("network_tree")
                )
                dpg.add_button(
                    label="Hosts Table",
                    width=-1,
                    callback=lambda: self.switch_tab("hosts_table")
                )
                dpg.add_button(
                    label="Scope Manager", 
                    width=-1,
                    callback=lambda: self.switch_tab("scope_manager")
                )
            
            # Статистика
            with dpg.collapsing_header(label="Statistics", default_open=True):
                dpg.add_text("Network Discovery:")
                dpg.add_text("Nodes: 0", tag="stat_nodes")
                dpg.add_text("Hosts: 0", tag="stat_hosts")
                dpg.add_text("Services: 0", tag="stat_services")
                
                dpg.add_text("Security Findings:")
                dpg.add_text("Vulnerabilities: 0", tag="stat_vulns", color=[150, 150, 160])
                dpg.add_text("Exploits: 0", tag="stat_exploits", color=[150, 150, 160])
    
    def switch_tab(self, tab_name: str):
        """Переключение между вкладками"""
        self.current_tab = tab_name
        
        # Очищаем область контента
        if dpg.does_item_exist("content_area"):
            dpg.delete_item("content_area", children_only=True)
        
        # Создаем новую вкладку
        if tab_name == "dashboard":
            self.create_dashboard_tab()
        elif tab_name == "network_tree":
            self.create_network_tree_tab()
        elif tab_name == "hosts_table":
            self.create_hosts_table_tab()
        elif tab_name == "scope_manager":
            self.create_scope_manager_tab()
    
    def create_dashboard_tab(self):
        """Создание вкладки Dashboard"""
        with dpg.group(parent="content_area"):
            dpg.add_text("Dashboard - RapidRecon Scanner", color=[123, 97, 255])
            dpg.add_separator()
            
            # Quick Start
            with dpg.group(horizontal=True):
                with dpg.child_window(width=400):
                    dpg.add_text("Quick Start")
                    dpg.add_separator()
                    
                    dpg.add_text("Enter target:")
                    dpg.add_input_text(
                        tag="dashboard_target",
                        hint="IP, domain or range",
                        width=-1
                    )
                    
                    dpg.add_text("Scan intensity:")
                    dpg.add_combo(
                        tag="dashboard_intensity",
                        items=["Stealth", "Normal", "Aggressive", "Full"],
                        default_value="Normal",
                        width=-1
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
                    dpg.add_text("System Status")
                    dpg.add_separator()
                    
                    dpg.add_text("Engine: Running", color=[72, 199, 116])
                    dpg.add_text("Modules: 6/6 Ready", color=[72, 199, 116])
                    dpg.add_text("Last Scan: Never", color=[255, 179, 64])
                    dpg.add_text("Active Scans: 0", color=[150, 150, 160])
            
            # Activity Log
            dpg.add_spacer(height=10)
            dpg.add_text("Activity Log")
            dpg.add_input_text(
                tag="activity_log",
                multiline=True,
                height=200,
                readonly=True,
                width=-1,
                default_value="[00:00:00] System initialized\n[00:00:00] Ready for scanning\n\nEnter target and click 'Start Scan' to begin reconnaissance."
            )
    
    def create_network_tree_tab(self):
        """Создание вкладки Network Tree"""
        with dpg.group(parent="content_area"):
            dpg.add_text("Network Topology", color=[123, 97, 255])
            dpg.add_separator()
            
            # Controls
            with dpg.group(horizontal=True):
                dpg.add_button(label="Refresh", callback=self.refresh_network_tree)
                dpg.add_button(label="Statistics", callback=self.show_network_statistics)
                dpg.add_button(label="Export", callback=self.export_network_tree)
            
            # Tree
            self.network_tree.create_tree_panel("content_area")
            self.network_tree.update_tree(self.nodes_data, self.hosts_data)
    
    def create_hosts_table_tab(self):
        """Создание вкладки Hosts Table"""
        with dpg.group(parent="content_area"):
            dpg.add_text("Discovered Hosts", color=[123, 97, 255])
            dpg.add_separator()
            
            # Table
            self.hosts_table.create_table_panel("content_area")
            self.hosts_table.update_table(self.hosts_data)
    
    def create_scope_manager_tab(self):
        """Создание вкладки Scope Manager"""
        with dpg.group(parent="content_area"):
            dpg.add_text("Scope Manager", color=[123, 97, 255])
            dpg.add_separator()
            dpg.add_text("Scope management interface")
            dpg.add_text("Add targets to scope for focused scanning")
            dpg.add_button(label="Import Scope", width=120)
            dpg.add_button(label="Export Scope", width=120)
    
    def quick_start_scan(self):
        """Быстрый запуск сканирования"""
        target = dpg.get_value("dashboard_target")
        if not target:
            self.update_activity_log("ERROR: Please enter a target first!")
            return
        
        intensity = dpg.get_value("dashboard_intensity")
        self.update_activity_log(f"Starting {intensity} scan for: {target}")
        
        # ИНТЕГРАЦИЯ С ДВИЖКОМ - запускаем настоящее сканирование
        if hasattr(self.engine, 'add_initial_target'):
            self.engine.add_initial_target(target)
            self.update_activity_log(f"Target {target} added to engine queue")
        
        # Запускаем через ControlsPanel
        self.controls_panel.start_scan(target, intensity)
        self.update_scan_state()
        
        # Запускаем обработку очереди в движке
        self.start_engine_processing()
    
    def start_engine_processing(self):
        """Запуск обработки очереди в движке"""
        import asyncio
        import threading
        
        def run_engine():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.engine.process_queue())
            except Exception as e:
                self.logger.error(f"Engine processing error: {e}")
        
        # Запускаем движок в отдельном потоке
        engine_thread = threading.Thread(target=run_engine, daemon=True)
        engine_thread.start()
        self.update_activity_log("Engine processing started in background")
    
    def add_target_from_dashboard(self):
        """Добавление цели из dashboard"""
        target = dpg.get_value("dashboard_target")
        if target:
            self.update_activity_log(f"Added target to scope: {target}")
            if hasattr(self.engine, 'add_to_scope'):
                self.engine.add_to_scope(target)
        else:
            self.update_activity_log("ERROR: Please enter a target first!")
    
    def update_scan_state(self):
        """Обновление состояния сканирования"""
        state = self.controls_panel.get_scan_state()
        dpg.set_value("scan_status", state['status'])
        dpg.configure_item("scan_status", color=state['color'])
    
    def update_activity_log(self, message: str):
        """Обновление лога активности"""
        current_log = dpg.get_value("activity_log")
        timestamp = datetime.now().strftime("%H:%M:%S")
        new_log = f"[{timestamp}] {message}\n{current_log}"
        dpg.set_value("activity_log", new_log)
    
    def refresh_network_tree(self):
        """Обновление дерева сети"""
        self.network_tree.update_tree(self.nodes_data, self.hosts_data)
        self.update_activity_log("Network tree refreshed")
    
    def show_network_statistics(self):
        """Показать статистику сети"""
        self.update_activity_log("Showing network statistics")
    
    def export_network_tree(self):
        """Экспорт дерева сети"""
        self.update_activity_log("Exporting network tree...")
    
    def handle_engine_event(self, event_type: str, data: Any = None):
        """Обработка событий от движка - КЛЮЧЕВАЯ ФУНКЦИЯ"""
        try:
            self.logger.info(f"GUI received event: {event_type}")
            
            if event_type in ['node_discovered', 'node_added', 'module_results']:
                # Обновляем данные из движка
                if hasattr(self.engine, 'discovered_nodes'):
                    self.nodes_data = self.engine.discovered_nodes.copy()
                
                if hasattr(self.engine, 'hosts_data'):
                    self.hosts_data = self.engine.hosts_data.copy()
                
                # Обновляем UI
                if self.current_tab == "network_tree":
                    self.network_tree.update_tree(self.nodes_data, self.hosts_data)
                elif self.current_tab == "hosts_table":
                    self.hosts_table.update_table(self.hosts_data)
                
                # Обновляем статистику
                self.update_statistics()
                
                # Логируем событие
                if event_type == 'node_discovered':
                    self.update_activity_log(f"New node discovered: {data.data if hasattr(data, 'data') else data}")
                elif event_type == 'module_results':
                    self.update_activity_log(f"Module completed: {data.get('module', 'unknown')}")
                
        except Exception as e:
            self.logger.error(f"Error handling engine event: {e}")
    
    def update_statistics(self):
        """Обновление статистики"""
        try:
            total_nodes = len(self.nodes_data)
            total_hosts = len(self.hosts_data)
            total_services = sum(len(h.get('services', [])) for h in self.hosts_data.values())
            
            dpg.set_value("stat_nodes", f"Nodes: {total_nodes}")
            dpg.set_value("stat_hosts", f"Hosts: {total_hosts}")
            dpg.set_value("stat_services", f"Services: {total_services}")
            
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")
    
    def run(self):
        """Запуск GUI"""
        try:
            self.logger.info("Запуск графического интерфейса...")
            
            while dpg.is_dearpygui_running():
                # Постоянно проверяем обновления от движка
                self.check_engine_updates()
                dpg.render_dearpygui_frame()
            
            self.destroy()
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска GUI: {e}")
    
    def check_engine_updates(self):
        """Проверка обновлений от движка"""
        try:
            # Проверяем наличие новых данных в движке
            if hasattr(self.engine, 'discovered_nodes'):
                new_nodes = self.engine.discovered_nodes
                if new_nodes != self.nodes_data:
                    self.nodes_data = new_nodes.copy()
                    self.handle_engine_event('node_discovered')
            
            if hasattr(self.engine, 'hosts_data'):
                new_hosts = self.engine.hosts_data
                if new_hosts != self.hosts_data:
                    self.hosts_data = new_hosts.copy()
                    self.handle_engine_event('node_discovered')
                    
        except Exception as e:
            self.logger.error(f"Error checking engine updates: {e}")
    
    def destroy(self):
        """Уничтожение GUI"""
        try:
            dpg.destroy_context()
        except Exception as e:
            self.logger.error(f"Ошибка уничтожения GUI: {e}")
