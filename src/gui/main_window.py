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
import threading
import asyncio
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
        
        # Статистика
        self.last_stats_update = 0
        self.stats_update_interval = 1.0  # секунды
        
        # Поток для мониторинга движка
        self.monitor_thread = None
        self.monitor_running = False
        
        # GUI элементы
        self.gui_initialized = False
        self.gui_elements = {}  # Словарь для хранения всех GUI элементов
        
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
            
            self.gui_initialized = True
            
            # Запуск мониторинга движка после инициализации GUI
            self.start_engine_monitor()
            
        except Exception as e:
            self.logger.error(f"Ошибка инициализации GUI: {e}")
            self.logger.error(traceback.format_exc())
            raise

    def start_engine_monitor(self):
        """Запуск мониторинга состояния движка"""
        if not self.gui_initialized:
            self.logger.warning("GUI не инициализирован, откладываем мониторинг")
            return
            
        self.monitor_running = True
        self.monitor_thread = threading.Thread(target=self._engine_monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Мониторинг движка запущен")

    def _engine_monitor_loop(self):
        """Цикл мониторинга состояния движка"""
        while self.monitor_running:
            try:
                # Проверяем состояние каждую секунду
                time.sleep(1.0)
                
                # Обновляем данные из движка
                self.update_engine_data()
                
                # Обновляем статистику
                current_time = time.time()
                if current_time - self.last_stats_update >= self.stats_update_interval:
                    self.update_statistics()
                    self.last_stats_update = current_time
                        
            except Exception as e:
                self.logger.error(f"Ошибка в мониторе движка: {e}")
    
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
                self.gui_elements['scan_status'] = dpg.add_text("Ready", tag="scan_status", color=[72, 199, 116])
            
            # Controls Panel
            self.controls_panel.create_controls_panel("sidebar")
            
            # Навигация
            with dpg.collapsing_header(label="Navigation", default_open=True):
                dpg.add_button(
                    label="Dashboard", 
                    tag="btn_dashboard",
                    width=-1,
                    callback=lambda: self.switch_tab("dashboard")
                )
                dpg.add_button(
                    label="Network Tree",
                    tag="btn_network_tree",
                    width=-1, 
                    callback=lambda: self.switch_tab("network_tree")
                )
                dpg.add_button(
                    label="Hosts Table",
                    tag="btn_hosts_table",
                    width=-1,
                    callback=lambda: self.switch_tab("hosts_table")
                )
                dpg.add_button(
                    label="Scope Manager", 
                    tag="btn_scope_manager",
                    width=-1,
                    callback=lambda: self.switch_tab("scope_manager")
                )
            
            # Статистика
            with dpg.collapsing_header(label="Statistics", default_open=True):
                dpg.add_text("Network Discovery:")
                self.gui_elements['stat_nodes'] = dpg.add_text("Nodes: 0", tag="stat_nodes")
                self.gui_elements['stat_hosts'] = dpg.add_text("Hosts: 0", tag="stat_hosts")
                self.gui_elements['stat_services'] = dpg.add_text("Services: 0", tag="stat_services")
                self.gui_elements['stat_ports'] = dpg.add_text("Ports: 0", tag="stat_ports")
                
                dpg.add_text("Security Findings:")
                self.gui_elements['stat_vulns'] = dpg.add_text("Vulnerabilities: 0", tag="stat_vulns", color=[150, 150, 160])
                self.gui_elements['stat_exploits'] = dpg.add_text("Exploits: 0", tag="stat_exploits", color=[150, 150, 160])
    
    def switch_tab(self, tab_name: str):
        """Переключение между вкладками"""
        self.current_tab = tab_name
        self.logger.info(f"Switching to tab: {tab_name}")
        
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
                    self.gui_elements['dashboard_target'] = dpg.add_input_text(
                        tag="dashboard_target",
                        hint="IP, domain or range",
                        width=-1
                    )
                    
                    dpg.add_text("Scan intensity:")
                    self.gui_elements['dashboard_intensity'] = dpg.add_combo(
                        tag="dashboard_intensity",
                        items=["Stealth", "Normal", "Aggressive", "Full"],
                        default_value="Normal",
                        width=-1
                    )
                    
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="Start Scan",
                            tag="btn_start_scan",
                            callback=self.quick_start_scan
                        )
                        dpg.add_button(
                            label="Add Target",
                            tag="btn_add_target",
                            callback=self.add_target_from_dashboard
                        )
                    
                    # Кнопка для принудительного запуска движка
                    dpg.add_button(
                        label="DEBUG: Force Engine",
                        tag="btn_force_engine",
                        callback=self.force_engine_start,
                        width=-1
                    )
                
                with dpg.child_window(width=400):
                    dpg.add_text("System Status")
                    dpg.add_separator()
                    
                    dpg.add_text("Engine: Running", color=[72, 199, 116])
                    dpg.add_text("Modules: 6/6 Ready", color=[72, 199, 116])
                    dpg.add_text("Last Scan: Never", color=[255, 179, 64])
                    self.gui_elements['stat_active_scans'] = dpg.add_text("Active Scans: 0", tag="stat_active_scans", color=[150, 150, 160])
            
            # Activity Log
            dpg.add_spacer(height=10)
            dpg.add_text("Activity Log")
            self.gui_elements['activity_log'] = dpg.add_input_text(
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
                dpg.add_button(label="Refresh", tag="btn_refresh_tree", callback=self.refresh_network_tree)
                dpg.add_button(label="Statistics", tag="btn_tree_stats", callback=self.show_network_statistics)
                dpg.add_button(label="Export", tag="btn_export_tree", callback=self.export_network_tree)
            
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
            dpg.add_button(label="Import Scope", tag="btn_import_scope", width=120)
            dpg.add_button(label="Export Scope", tag="btn_export_scope", width=120)
    
    def quick_start_scan(self):
        """Быстрый запуск сканирования"""
        try:
            target = dpg.get_value("dashboard_target")
            if not target:
                self.update_activity_log("ERROR: Please enter a target first!")
                return
            
            intensity = dpg.get_value("dashboard_intensity")
            self.update_activity_log(f"🚀 Starting {intensity} scan for: {target}")
            self.logger.info(f"🚀 QUICK START SCAN: target={target}, intensity={intensity}")
            
            # Устанавливаем профиль сканирования
            profile_map = {
                "Stealth": "stealth",
                "Normal": "normal", 
                "Aggressive": "aggressive",
                "Full": "aggressive"
            }
            profile_name = profile_map.get(intensity, "normal")
            
            if hasattr(self.engine, 'set_scan_profile'):
                success = self.engine.set_scan_profile(profile_name)
                if success:
                    self.update_activity_log(f"📊 Scan profile set to: {profile_name}")
                else:
                    self.update_activity_log(f"❌ Failed to set profile: {profile_name}")
            
            # Добавляем цель в движок
            if hasattr(self.engine, 'add_initial_target'):
                self.logger.info("✅ Adding target to engine via add_initial_target")
                try:
                    self.engine.add_initial_target(target)
                    self.update_activity_log(f"🎯 Target {target} added to engine queue")
                    
                    # Проверяем состояние очереди
                    if hasattr(self.engine, 'pending_scans'):
                        queue_size = self.engine.pending_scans.qsize()
                        self.update_activity_log(f"📋 Scan queue size: {queue_size}")
                        self.logger.info(f"Queue size after adding target: {queue_size}")
                    
                    # Проверяем обнаруженные узлы
                    if hasattr(self.engine, 'discovered_nodes'):
                        nodes_count = len(self.engine.discovered_nodes)
                        self.logger.info(f"Discovered nodes after adding target: {nodes_count}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Error in add_initial_target: {e}")
                    self.update_activity_log(f"ERROR adding target: {e}")
            else:
                self.logger.error("❌ Engine has no add_initial_target method!")
                self.update_activity_log("ERROR: Engine not properly initialized")
            
            # Обновляем состояние сканирования
            self.is_scanning = True
            self.update_scan_state()
            
            # Запускаем движок если он не запущен
            self.start_engine_if_needed()
            
        except Exception as e:
            self.logger.error(f"Error in quick_start_scan: {e}")
            self.update_activity_log(f"ERROR: {e}")
    
    def start_engine_if_needed(self):
        """Запуск движка если он не запущен"""
        try:
            # Проверяем состояние движка
            if hasattr(self.engine, 'is_running'):
                if not self.engine.is_running:
                    self.logger.info("🔄 Starting engine processing...")
                    
                    # Запускаем движок в отдельном потоке
                    engine_thread = threading.Thread(
                        target=self._run_engine_async,
                        daemon=True,
                        name="EngineProcessor"
                    )
                    engine_thread.start()
                    self.update_activity_log("🔧 Engine processing started")
                    
                    # Даем время на запуск
                    time.sleep(0.5)
                    
                    # Проверяем состояние после запуска
                    if hasattr(self.engine, 'is_running'):
                        self.logger.info(f"Engine running state after start: {self.engine.is_running}")
                    if hasattr(self.engine, 'pending_scans'):
                        queue_size = self.engine.pending_scans.qsize()
                        self.logger.info(f"Queue size after engine start: {queue_size}")
                        
                else:
                    self.update_activity_log("⚡ Engine is already running")
            else:
                self.logger.warning("⚠️ Engine doesn't have is_running attribute")
                
        except Exception as e:
            self.logger.error(f"❌ Error starting engine: {e}")
            self.update_activity_log(f"ERROR starting engine: {e}")
    
    def _run_engine_async(self):
        """Запуск асинхронного движка в отдельном потоке"""
        try:
            self.logger.info("🔄 Engine async thread started")
            
            # Создаем новый event loop для этого потока
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Запускаем обработку очереди
            self.logger.info("🏃 Starting engine process_queue...")
            result = loop.run_until_complete(self.engine.process_queue())
            self.logger.info(f"🏁 Engine process_queue completed: {result}")
            
        except Exception as e:
            self.logger.error(f"❌ Engine processing error: {e}")
            self.logger.error(traceback.format_exc())
            self.update_activity_log(f"Engine error: {e}")
    
    def force_engine_start(self):
        """Принудительный запуск движка для отладки"""
        self.logger.info("🔧 FORCE ENGINE START")
        self.update_activity_log("🔧 DEBUG: Force starting engine...")
        
        # Проверяем методы движка
        engine_methods = [method for method in dir(self.engine) if not method.startswith('_')]
        self.logger.info(f"Available engine methods: {engine_methods}")
        
        # Проверяем состояние
        if hasattr(self.engine, 'pending_scans'):
            queue_size = self.engine.pending_scans.qsize()
            self.update_activity_log(f"📋 Current queue size: {queue_size}")
        
        if hasattr(self.engine, 'discovered_nodes'):
            nodes_count = len(self.engine.discovered_nodes)
            self.update_activity_log(f"📊 Discovered nodes: {nodes_count}")
        
        # Запускаем движок
        self.start_engine_if_needed()
    
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
        try:
            if self.is_scanning:
                dpg.set_value("scan_status", "Scanning")
                dpg.configure_item("scan_status", color=[255, 179, 64])  # warning color
            else:
                dpg.set_value("scan_status", "Ready")
                dpg.configure_item("scan_status", color=[72, 199, 116])  # success color
        except Exception as e:
            self.logger.error(f"Error updating scan state: {e}")
    
    def update_activity_log(self, message: str):
        """Обновление лога активности"""
        try:
            current_log = dpg.get_value("activity_log")
            timestamp = datetime.now().strftime("%H:%M:%S")
            new_log = f"[{timestamp}] {message}\n{current_log}"
            dpg.set_value("activity_log", new_log)
        except Exception as e:
            self.logger.error(f"Error updating activity log: {e}")
    
    def refresh_network_tree(self):
        """Обновление дерева сети"""
        self.network_tree.update_tree(self.nodes_data, self.hosts_data)
        self.update_activity_log("Network tree refreshed")
    
    def show_network_statistics(self):
        """Показать статистику сети"""
        stats = self.calculate_detailed_statistics()
        
        if dpg.does_item_exist("network_stats_window"):
            dpg.delete_item("network_stats_window")
        
        with dpg.window(
            tag="network_stats_window",
            label="Network Statistics",
            width=400,
            height=300,
            modal=True
        ):
            dpg.add_text("Detailed Network Statistics")
            dpg.add_separator()
            
            for category, count in stats.items():
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{category}:")
                    dpg.add_text(str(count), color=[123, 97, 255])
        
        self.update_activity_log("Showing detailed network statistics")
    
    def calculate_detailed_statistics(self) -> Dict[str, int]:
        """Расчет детальной статистики сети"""
        try:
            # Получаем статистику из движка
            engine_stats = self.engine.get_statistics() if hasattr(self.engine, 'get_statistics') else {}
            
            # Считаем статистику из данных
            total_nodes = len(self.nodes_data)
            total_hosts = len(self.hosts_data)
            total_ports = sum(len(host.get('ports', [])) for host in self.hosts_data.values())
            total_services = sum(len(host.get('services', [])) for host in self.hosts_data.values())
            
            return {
                "Total Nodes": total_nodes,
                "Active Hosts": total_hosts,
                "Open Ports": total_ports,
                "Running Services": total_services,
                "Vulnerabilities Found": engine_stats.get('vulnerabilities_found', 0),
                "Successful Scans": engine_stats.get('successful_scans', 0),
                "Failed Scans": engine_stats.get('failed_scans', 0),
                "Pending Tasks": engine_stats.get('pending_tasks', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating statistics: {e}")
            return {"Error": "Could not calculate statistics"}
    
    def export_network_tree(self):
        """Экспорт дерева сети"""
        self.update_activity_log("Exporting network tree...")
    
    def handle_engine_event(self, event_type: str, data: Any = None):
        """Обработка событий от движка"""
        try:
            self.logger.info(f"GUI received event: {event_type}")
            
            if event_type in ['node_discovered', 'node_added', 'module_results', 'progress_update']:
                # Обновляем данные из движка
                self.update_engine_data()
                
                # Обновляем UI
                if self.current_tab == "network_tree":
                    self.network_tree.update_tree(self.nodes_data, self.hosts_data)
                elif self.current_tab == "hosts_table":
                    self.hosts_table.update_table(self.hosts_data)
                
                # Обновляем статистику
                self.update_statistics()
                
                # Логируем событие
                if event_type == 'node_discovered':
                    node_info = data.data if hasattr(data, 'data') else str(data)
                    self.update_activity_log(f"New node discovered: {node_info}")
                elif event_type == 'module_results':
                    module_name = data.get('module', 'unknown') if isinstance(data, dict) else 'unknown'
                    self.update_activity_log(f"Module completed: {module_name}")
                elif event_type == 'progress_update':
                    if isinstance(data, dict):
                        pending = data.get('pending_tasks', 0)
                        completed = data.get('completed_tasks', 0)
                        self.update_activity_log(f"Progress: {completed} completed, {pending} pending")
                
        except Exception as e:
            self.logger.error(f"Error handling engine event: {e}")
    
    def update_engine_data(self):
        """Обновление данных из движка"""
        try:
            # Получаем данные напрямую из движка
            if hasattr(self.engine, 'discovered_nodes'):
                engine_nodes = self.engine.discovered_nodes
                
                # Конвертируем в словарь для network_tree
                self.nodes_data = {}
                for i, node in enumerate(engine_nodes):
                    node_id = getattr(node, 'node_id', f"node_{i}")
                    self.nodes_data[node_id] = {
                        'id': node_id,
                        'type': getattr(node, 'type', 'unknown'),
                        'label': getattr(node, 'data', 'Unknown'),
                        'data': getattr(node, 'data', {}),
                        'timestamp': getattr(node, 'timestamp', time.time()),
                        'ports': getattr(node, 'ports', []),
                        'services': getattr(node, 'services', []),
                        'vulnerabilities': getattr(node, 'vulnerabilities', [])
                    }
            
            # Обновляем hosts_data из движка
            if hasattr(self.engine, 'hosts_data'):
                engine_hosts = self.engine.hosts_data
                if isinstance(engine_hosts, dict):
                    self.hosts_data = engine_hosts.copy()
                else:
                    # Если hosts_data это не словарь, создаем из discovered_nodes
                    self.hosts_data = {}
                    for node in getattr(self.engine, 'discovered_nodes', []):
                        if hasattr(node, 'type') and getattr(node, 'type').name in ['ACTIVE_HOST', 'IP_ADDRESS']:
                            ip = getattr(node, 'data', 'unknown')
                            self.hosts_data[ip] = {
                                'hostname': getattr(node, 'data', 'Unknown'),
                                'status': 'active',
                                'ports': getattr(node, 'ports', []),
                                'services': getattr(node, 'services', []),
                                'os': 'Unknown',
                                'last_seen': datetime.now().strftime("%H:%M:%S"),
                                'tags': ['discovered']
                            }
            
        except Exception as e:
            self.logger.error(f"Error updating engine data: {e}")
    
    def update_statistics(self):
        """Обновление статистики на боковой панели"""
        try:
            if not self.gui_initialized:
                return
                
            # Рассчитываем статистику
            total_nodes = len(self.nodes_data)
            total_hosts = len(self.hosts_data)
            total_services = sum(len(host.get('services', [])) for host in self.hosts_data.values())
            total_ports = sum(len(host.get('ports', [])) for host in self.hosts_data.values())
            
            # Получаем статистику из движка
            engine_stats = self.engine.get_statistics() if hasattr(self.engine, 'get_statistics') else {}
            total_vulns = engine_stats.get('vulnerabilities_found', 0)
            total_exploits = engine_stats.get('exploits_successful', 0)
            pending_tasks = engine_stats.get('pending_tasks', 0)
            
            # Обновляем UI
            dpg.set_value("stat_nodes", f"Nodes: {total_nodes}")
            dpg.set_value("stat_hosts", f"Hosts: {total_hosts}")
            dpg.set_value("stat_services", f"Services: {total_services}")
            dpg.set_value("stat_ports", f"Ports: {total_ports}")
            dpg.set_value("stat_vulns", f"Vulnerabilities: {total_vulns}")
            dpg.set_value("stat_exploits", f"Exploits: {total_exploits}")
            dpg.set_value("stat_active_scans", f"Active Scans: {pending_tasks}")
            
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")
    
    def run(self):
        """Запуск GUI"""
        try:
            self.logger.info("Запуск графического интерфейса...")
            
            while dpg.is_dearpygui_running():
                # Рендерим кадр
                dpg.render_dearpygui_frame()
            
            self.destroy()
            
        except Exception as e:
            self.logger.error(f"Ошибка запуска GUI: {e}")
            self.logger.error(traceback.format_exc())
    
    def destroy(self):
        """Уничтожение GUI"""
        try:
            # Останавливаем мониторинг
            self.monitor_running = False
            if self.monitor_thread and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2.0)
            
            # Уничтожаем GUI контекст
            dpg.destroy_context()
            self.logger.info("GUI уничтожен")
            
        except Exception as e:
            self.logger.error(f"Ошибка уничтожения GUI: {e}")
