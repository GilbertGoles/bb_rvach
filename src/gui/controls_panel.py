"""
Controls Panel - максимально продвинутая панель управления сканированием
"""
import dearpygui.dearpygui as dpg
from typing import Dict, Any, List, Optional, Callable
import logging
import time
import json
from datetime import datetime, timedelta
import threading
from enum import Enum

class ScanIntensity(Enum):
    """Уровни интенсивности сканирования"""
    STEALTH = "stealth"
    NORMAL = "normal" 
    AGGRESSIVE = "aggressive"
    FULL_ATTACK = "full"
    PENTEST = "pentest"

class ScanPhase(Enum):
    """Фазы сканирования"""
    RECON = "reconnaissance"
    DISCOVERY = "discovery"
    VULN_SCAN = "vulnerability_scan"
    EXPLOITATION = "exploitation"
    POST_EXPLOIT = "post_exploitation"

class ControlsPanel:
    """
    Продвинутая панель управления сканированием с учетом всех нюансов
    """
    
    def __init__(self, engine=None):
        self.logger = logging.getLogger('RapidRecon.ControlsPanel')
        self.engine = engine
        
        # Состояние сканирования
        self.scan_state = {
            'is_scanning': False,
            'is_paused': False,
            'current_phase': None,
            'start_time': None,
            'estimated_completion': None,
            'progress': 0.0,
            'current_target': None,
            'threads_active': 0
        }
        
        # Конфигурация сканирования
        self.scan_config = {
            'intensity': ScanIntensity.NORMAL,
            'phases_enabled': {
                'recon': True,
                'discovery': True, 
                'vuln_scan': False,
                'exploitation': False,
                'post_exploit': False
            },
            'advanced_options': {
                'stealth_mode': True,
                'randomize_scan': True,
                'obfuscate_traffic': False,
                'use_proxies': False,
                'rate_limit': 10,
                'max_threads': 5,
                'timeout': 5,
                'retry_count': 2
            },
            'custom_ports': [80, 443, 22, 21, 25, 53, 110, 143, 993, 995, 8080, 8443],
            'user_agents': [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            ]
        }
        
        # Мониторинг ресурсов
        self.resource_monitor = {
            'cpu_usage': 0,
            'memory_usage': 0,
            'network_usage': 0,
            'requests_per_second': 0,
            'active_connections': 0
        }
        
        # Callbacks
        self.on_scan_start = None
        self.on_scan_pause = None
        self.on_scan_resume = None
        self.on_scan_stop = None
        self.on_config_change = None
        
        # Таймеры и потоки
        self.update_timer = None
        self.resource_monitor_thread = None
        self.monitoring_active = False
        
    def create_controls_panel(self, parent: str) -> str:
        """Создание продвинутой панели управления"""
        with dpg.child_window(parent=parent, border=False) as controls_panel:
            # Быстрый запуск
            with dpg.collapsing_header(label="⚡ Quick Launch", default_open=True):
                self._create_quick_launch_section()
            
            # Управление сканированием
            with dpg.collapsing_header(label="🎯 Scan Control", default_open=True):
                self._create_scan_control_section()
            
            # Конфигурация сканирования
            with dpg.collapsing_header(label="🔧 Scan Configuration", default_open=False):
                self._create_scan_config_section()
            
            # Мониторинг в реальном времени
            with dpg.collapsing_header(label="📊 Live Monitoring", default_open=False):
                self._create_monitoring_section()
            
            # Расширенные настройки
            with dpg.collapsing_header(label="⚙️ Advanced Settings", default_open=False):
                self._create_advanced_section()
        
        return controls_panel
    
    def _create_quick_launch_section(self):
        """Секция быстрого запуска"""
        with dpg.group():
            dpg.add_text("Primary Target:", color=[150, 150, 160])
            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    tag="quick_target",
                    hint="example.com / 192.168.1.1",
                    width=180
                )
                dpg.add_button(
                    label="🎯",
                    callback=self._quick_add_target,
                    width=30
                )
            
            dpg.add_text("Scan Intensity:", color=[150, 150, 160])
            dpg.add_combo(
                tag="quick_intensity",
                items=["🚀 Stealth", "⚡ Normal", "💥 Aggressive", "🔥 Full Attack", "💀 Pentest"],
                default_value="⚡ Normal",
                width=-1,
                callback=self._on_intensity_change
            )
            
            # Быстрые цели
            dpg.add_text("Quick Targets:", color=[150, 150, 160])
            with dpg.group(horizontal=True, wrap=True):
                quick_targets = [
                    ("🌐 Domain", "example.com"),
                    ("🏠 Local", "192.168.1.1"),
                    ("🔍 Test", "scanme.nmap.org"),
                    ("📱 Mobile", "mobile.example.com")
                ]
                
                for label, target in quick_targets:
                    dpg.add_button(
                        label=label,
                        callback=lambda s, d, t=target: self._set_quick_target(t),
                        width=70
                    )
    
    def _create_scan_control_section(self):
        """Секция управления сканированием"""
        with dpg.group():
            # Основные кнопки управления
            with dpg.group(horizontal=True):
                self.start_btn = dpg.add_button(
                    label="🚀 Start Scan",
                    tag="start_btn",
                    width=100,
                    callback=self.start_scan
                )
                self.pause_btn = dpg.add_button(
                    label="⏸️ Pause", 
                    tag="pause_btn",
                    width=80,
                    callback=self.pause_scan,
                    show=False
                )
            
            with dpg.group(horizontal=True):
                self.resume_btn = dpg.add_button(
                    label="▶️ Resume",
                    tag="resume_btn",
                    width=80,
                    callback=self.resume_scan,
                    show=False
                )
                self.stop_btn = dpg.add_button(
                    label="⏹️ Stop",
                    tag="stop_btn",
                    width=80,
                    callback=self.stop_scan,
                    show=False
                )
            
            # Прогресс сканирования
            dpg.add_text("Scan Progress:", color=[150, 150, 160])
            with dpg.group(horizontal=True):
                dpg.add_progress_bar(
                    tag="scan_progress",
                    default_value=0.0,
                    width=150
                )
                dpg.add_text("0%", tag="progress_text")
            
            # Текущий статус
            dpg.add_text("Status: Ready", tag="status_text", color=[72, 199, 116])
            
            # Таймер сканирования
            with dpg.group(horizontal=True):
                dpg.add_text("Elapsed:", color=[150, 150, 160])
                dpg.add_text("00:00:00", tag="elapsed_time")
                dpg.add_text("ETA:", color=[150, 150, 160])
                dpg.add_text("--:--:--", tag="eta_time")
    
    def _create_scan_config_section(self):
        """Секция конфигурации сканирования"""
        with dpg.group():
            # Фазы сканирования
            dpg.add_text("Scan Phases:", color=[150, 150, 160])
            dpg.add_checkbox(
                tag="phase_recon",
                label="🔍 Reconnaissance",
                default_value=True,
                callback=self._on_phase_change
            )
            dpg.add_checkbox(
                tag="phase_discovery", 
                label="🌐 Host Discovery",
                default_value=True,
                callback=self._on_phase_change
            )
            dpg.add_checkbox(
                tag="phase_vuln",
                label="🔴 Vulnerability Scan", 
                default_value=False,
                callback=self._on_phase_change
            )
            dpg.add_checkbox(
                tag="phase_exploit",
                label="💥 Exploitation",
                default_value=False,
                callback=self._on_phase_change
            )
            
            # Настройки производительности
            dpg.add_text("Performance:", color=[150, 150, 160])
            dpg.add_slider_int(
                tag="config_threads",
                label="Max Threads",
                default_value=5,
                min_value=1,
                max_value=50,
                callback=self._on_config_change
            )
            dpg.add_slider_int(
                tag="config_rate_limit",
                label="Rate Limit (req/sec)",
                default_value=10,
                min_value=1, 
                max_value=100,
                callback=self._on_config_change
            )
            dpg.add_slider_int(
                tag="config_timeout",
                label="Timeout (seconds)",
                default_value=5,
                min_value=1,
                max_value=30,
                callback=self._on_config_change
            )
    
    def _create_monitoring_section(self):
        """Секция мониторинга в реальном времени"""
        with dpg.group():
            # Использование ресурсов
            dpg.add_text("Resource Usage:", color=[150, 150, 160])
            
            with dpg.group(horizontal=True):
                with dpg.child_window(width=120):
                    dpg.add_text("CPU:", color=[150, 150, 160])
                    dpg.add_text("0%", tag="cpu_usage", color=[86, 156, 214])
                    
                    dpg.add_text("Memory:", color=[150, 150, 160])
                    dpg.add_text("0 MB", tag="memory_usage", color=[123, 97, 255])
                
                with dpg.child_window(width=120):
                    dpg.add_text("Network:", color=[150, 150, 160])
                    dpg.add_text("0 KB/s", tag="network_usage", color=[72, 199, 116])
                    
                    dpg.add_text("Requests:", color=[150, 150, 160])
                    dpg.add_text("0/sec", tag="requests_sec", color=[255, 179, 64])
            
            # Активность в реальном времени
            dpg.add_text("Current Activity:", color=[150, 150, 160])
            dpg.add_text("Idle", tag="current_activity", color=[150, 150, 160])
            
            # Графики использования (заглушки)
            dpg.add_button(
                label="📈 Show Resource Graphs",
                callback=self._show_resource_graphs,
                width=-1
            )
    
    def _create_advanced_section(self):
        """Секция расширенных настроек"""
        with dpg.tab_bar():
            # Вкладка stealth
            with dpg.tab(label="🕵️ Stealth"):
                self._create_stealth_tab()
            
            # Вкладка сети
            with dpg.tab(label="🌐 Network"):
                self._create_network_tab()
            
            # Вкладка кастомизации
            with dpg.tab(label="🔧 Customization"):
                self._create_customization_tab()
    
    def _create_stealth_tab(self):
        """Вкладка stealth настроек"""
        with dpg.group():
            dpg.add_checkbox(
                tag="stealth_mode",
                label="Enable Stealth Mode",
                default_value=True,
                callback=self._on_config_change
            )
            dpg.add_checkbox(
                tag="randomize_scan",
                label="Randomize Scan Order", 
                default_value=True,
                callback=self._on_config_change
            )
            dpg.add_checkbox(
                tag="obfuscate_traffic",
                label="Obfuscate Traffic",
                default_value=False,
                callback=self._on_config_change
            )
            dpg.add_checkbox(
                tag="use_proxies",
                label="Use Proxy Chain",
                default_value=False,
                callback=self._on_config_change
            )
            
            dpg.add_text("Scan Delay (ms):", color=[150, 150, 160])
            dpg.add_slider_int(
                tag="scan_delay",
                label="Delay Between Requests",
                default_value=100,
                min_value=0,
                max_value=5000,
                callback=self._on_config_change
            )
    
    def _create_network_tab(self):
        """Вкладка сетевых настроек"""
        with dpg.group():
            dpg.add_text("Port Configuration:", color=[150, 150, 160])
            dpg.add_input_text(
                tag="custom_ports",
                hint="80,443,22,21,25,53...",
                multiline=True,
                height=60,
                width=-1,
                callback=self._on_ports_change
            )
            
            dpg.add_text("User Agents:", color=[150, 150, 160])
            dpg.add_combo(
                tag="user_agent",
                items=self.scan_config['user_agents'],
                default_value=self.scan_config['user_agents'][0],
                width=-1,
                callback=self._on_config_change
            )
            
            dpg.add_text("DNS Servers:", color=[150, 150, 160])
            dpg.add_input_text(
                tag="dns_servers",
                default_value="8.8.8.8,1.1.1.1",
                width=-1,
                callback=self._on_config_change
            )
    
    def _create_customization_tab(self):
        """Вкладка кастомизации"""
        with dpg.group():
            dpg.add_text("Custom Scripts:", color=[150, 150, 160])
            dpg.add_input_text(
                tag="pre_scan_script",
                hint="Pre-scan script path...",
                width=-1
            )
            dpg.add_input_text(
                tag="post_scan_script", 
                hint="Post-scan script path...",
                width=-1
            )
            
            dpg.add_text("Output Format:", color=[150, 150, 160])
            dpg.add_combo(
                tag="output_format",
                items=["JSON", "XML", "CSV", "HTML", "PDF"],
                default_value="JSON",
                width=-1
            )
            
            dpg.add_checkbox(
                tag="auto_save",
                label="Auto-save Results",
                default_value=True
            )
            dpg.add_checkbox(
                tag="backup_results",
                label="Create Backups",
                default_value=True
            )
    
    def _quick_add_target(self):
        """Быстрое добавление цели"""
        target = dpg.get_value("quick_target")
        if target:
            self._set_quick_target(target)
    
    def _set_quick_target(self, target: str):
        """Установка цели в quick input"""
        dpg.set_value("quick_target", target)
        self.add_to_log(f"🎯 Target set: {target}")
    
    def _on_intensity_change(self, sender, app_data):
        """Обработчик изменения интенсивности"""
        intensity_map = {
            "🚀 Stealth": ScanIntensity.STEALTH,
            "⚡ Normal": ScanIntensity.NORMAL,
            "💥 Aggressive": ScanIntensity.AGGRESSIVE, 
            "🔥 Full Attack": ScanIntensity.FULL_ATTACK,
            "💀 Pentest": ScanIntensity.PENTEST
        }
        
        self.scan_config['intensity'] = intensity_map.get(app_data, ScanIntensity.NORMAL)
        self._apply_intensity_preset()
        self.add_to_log(f"🎛️ Scan intensity: {app_data}")
    
    def _apply_intensity_preset(self):
        """Применение пресетов интенсивности"""
        intensity = self.scan_config['intensity']
        
        presets = {
            ScanIntensity.STEALTH: {'threads': 2, 'rate_limit': 2, 'timeout': 10},
            ScanIntensity.NORMAL: {'threads': 5, 'rate_limit': 10, 'timeout': 5},
            ScanIntensity.AGGRESSIVE: {'threads': 15, 'rate_limit': 25, 'timeout': 3},
            ScanIntensity.FULL_ATTACK: {'threads': 30, 'rate_limit': 50, 'timeout': 2},
            ScanIntensity.PENTEST: {'threads': 50, 'rate_limit': 100, 'timeout': 1}
        }
        
        preset = presets.get(intensity, presets[ScanIntensity.NORMAL])
        self.scan_config['advanced_options'].update(preset)
        
        # Обновляем UI
        dpg.set_value("config_threads", preset['threads'])
        dpg.set_value("config_rate_limit", preset['rate_limit']) 
        dpg.set_value("config_timeout", preset['timeout'])
    
    def _on_phase_change(self, sender, app_data):
        """Обработчик изменения фаз сканирования"""
        phase_map = {
            'phase_recon': 'recon',
            'phase_discovery': 'discovery',
            'phase_vuln': 'vuln_scan', 
            'phase_exploit': 'exploitation'
        }
        
        phase = phase_map.get(sender)
        if phase:
            self.scan_config['phases_enabled'][phase] = app_data
            self.add_to_log(f"🔧 {phase} phase: {'enabled' if app_data else 'disabled'}")
    
    def _on_config_change(self, sender, app_data):
        """Обработчик изменения конфигурации"""
        config_map = {
            'config_threads': 'max_threads',
            'config_rate_limit': 'rate_limit',
            'config_timeout': 'timeout',
            'stealth_mode': 'stealth_mode',
            'randomize_scan': 'randomize_scan',
            'obfuscate_traffic': 'obfuscate_traffic',
            'use_proxies': 'use_proxies'
        }
        
        config_key = config_map.get(sender)
        if config_key:
            self.scan_config['advanced_options'][config_key] = app_data
    
    def _on_ports_change(self, sender, app_data):
        """Обработчик изменения портов"""
        try:
            ports = [int(port.strip()) for port in app_data.split(',') if port.strip()]
            self.scan_config['custom_ports'] = ports
            self.add_to_log(f"🔧 Custom ports updated: {len(ports)} ports")
        except ValueError as e:
            self.add_to_log(f"❌ Invalid port format: {e}")
    
    def _show_resource_graphs(self):
        """Показать графики использования ресурсов"""
        # Заглушка для графиков
        self.add_to_log("📈 Resource graphs - to be implemented")
    
    def start_scan(self, target: str = None, intensity: str = None):
        """Запуск сканирования"""
        try:
            if not target:
                target = dpg.get_value("quick_target")
            
            if not target:
                self.add_to_log("❌ Please enter a target first!")
                return False
            
            if intensity:
                self.scan_config['intensity'] = intensity
            
            # Обновляем состояние
            self.scan_state.update({
                'is_scanning': True,
                'is_paused': False,
                'start_time': datetime.now(),
                'current_phase': ScanPhase.RECON,
                'current_target': target,
                'progress': 0.0
            })
            
            # Обновляем UI
            self._update_control_buttons()
            dpg.set_value("status_text", "Status: Scanning")
            dpg.configure_item("status_text", color=[255, 179, 64])
            dpg.set_value("current_activity", f"Reconnaissance: {target}")
            
            # Запускаем мониторинг ресурсов
            self._start_resource_monitoring()
            
            # Запускаем таймер
            self._start_scan_timer()
            
            # Вызываем callback
            if self.on_scan_start:
                self.on_scan_start(target, self.scan_config)
            
            self.add_to_log(f"🚀 Scan started for: {target}")
            self.add_to_log(f"🎯 Intensity: {self.scan_config['intensity'].value}")
            
            return True
            
        except Exception as e:
            self.add_to_log(f"❌ Error starting scan: {e}")
            return False
    
    def pause_scan(self):
        """Пауза сканирования"""
        try:
            self.scan_state.update({
                'is_scanning': True,
                'is_paused': True
            })
            
            self._update_control_buttons()
            dpg.set_value("status_text", "Status: Paused")
            dpg.configure_item("status_text", color=[255, 179, 64])
            
            # Приостанавливаем мониторинг
            self._pause_resource_monitoring()
            
            if self.on_scan_pause:
                self.on_scan_pause()
            
            self.add_to_log("⏸️ Scan paused")
            
        except Exception as e:
            self.add_to_log(f"❌ Error pausing scan: {e}")
    
    def resume_scan(self):
        """Возобновление сканирования"""
        try:
            self.scan_state.update({
                'is_scanning': True,
                'is_paused': False
            })
            
            self._update_control_buttons()
            dpg.set_value("status_text", "Status: Scanning")
            dpg.configure_item("status_text", color=[255, 179, 64])
            
            # Возобновляем мониторинг
            self._resume_resource_monitoring()
            
            if self.on_scan_resume:
                self.on_scan_resume()
            
            self.add_to_log("▶️ Scan resumed")
            
        except Exception as e:
            self.add_to_log(f"❌ Error resuming scan: {e}")
    
    def stop_scan(self):
        """Остановка сканирования"""
        try:
            self.scan_state.update({
                'is_scanning': False,
                'is_paused': False,
                'current_phase': None,
                'progress': 0.0
            })
            
            self._update_control_buttons()
            dpg.set_value("status_text", "Status: Ready")
            dpg.configure_item("status_text", color=[72, 199, 116])
            dpg.set_value("current_activity", "Idle")
            
            # Останавливаем мониторинг и таймер
            self._stop_resource_monitoring()
            self._stop_scan_timer()
            
            # Сбрасываем прогресс
            dpg.set_value("scan_progress", 0.0)
            dpg.set_value("progress_text", "0%")
            dpg.set_value("elapsed_time", "00:00:00")
            dpg.set_value("eta_time", "--:--:--")
            
            if self.on_scan_stop:
                self.on_scan_stop()
            
            self.add_to_log("⏹️ Scan stopped")
            
        except Exception as e:
            self.add_to_log(f"❌ Error stopping scan: {e}")
    
    def _update_control_buttons(self):
        """Обновление состояния кнопок управления"""
        state = self.scan_state
        
        dpg.configure_item("start_btn", show=not state['is_scanning'])
        dpg.configure_item("pause_btn", show=state['is_scanning'] and not state['is_paused'])
        dpg.configure_item("resume_btn", show=state['is_scanning'] and state['is_paused'])
        dpg.configure_item("stop_btn", show=state['is_scanning'])
    
    def _start_resource_monitoring(self):
        """Запуск мониторинга ресурсов"""
        self.monitoring_active = True
        self.resource_monitor_thread = threading.Thread(
            target=self._resource_monitor_worker,
            daemon=True
        )
        self.resource_monitor_thread.start()
    
    def _pause_resource_monitoring(self):
        """Приостановка мониторинга ресурсов"""
        self.monitoring_active = False
    
    def _resume_resource_monitoring(self):
        """Возобновление мониторинга ресурсов"""
        self.monitoring_active = True
    
    def _stop_resource_monitoring(self):
        """Остановка мониторинга ресурсов"""
        self.monitoring_active = False
        if self.resource_monitor_thread and self.resource_monitor_thread.is_alive():
            self.resource_monitor_thread.join(timeout=1.0)
    
    def _resource_monitor_worker(self):
        """Воркер мониторинга ресурсов"""
        while self.monitoring_active:
            try:
                # Эмуляция данных мониторинга
                import psutil
                import random
                
                self.resource_monitor.update({
                    'cpu_usage': psutil.cpu_percent(),
                    'memory_usage': psutil.virtual_memory().percent,
                    'network_usage': random.randint(10, 1000),  # KB/s
                    'requests_per_second': random.randint(0, 50),
                    'active_connections': random.randint(0, 20)
                })
                
                # Обновляем UI в главном потоке
                dpg.set_value("cpu_usage", f"{self.resource_monitor['cpu_usage']:.1f}%")
                dpg.set_value("memory_usage", f"{self.resource_monitor['memory_usage']:.1f}%")
                dpg.set_value("network_usage", f"{self.resource_monitor['network_usage']} KB/s")
                dpg.set_value("requests_sec", f"{self.resource_monitor['requests_per_second']}/sec")
                
                time.sleep(1)  # Обновляем каждую секунду
                
            except Exception as e:
                self.logger.error(f"Resource monitor error: {e}")
                time.sleep(5)
    
    def _start_scan_timer(self):
        """Запуск таймера сканирования"""
        self.update_timer = threading.Timer(1.0, self._update_scan_timer)
        self.update_timer.start()
    
    def _stop_scan_timer(self):
        """Остановка таймера сканирования"""
        if self.update_timer:
            self.update_timer.cancel()
    
    def _update_scan_timer(self):
        """Обновление таймера сканирования"""
        if self.scan_state['is_scanning'] and not self.scan_state['is_paused']:
            elapsed = datetime.now() - self.scan_state['start_time']
            elapsed_str = str(elapsed).split('.')[0]  # Убираем микросекунды
            
            # Эмуляция прогресса
            if self.scan_state['progress'] < 1.0:
                self.scan_state['progress'] += 0.01
                progress_percent = int(self.scan_state['progress'] * 100)
                
                dpg.set_value("scan_progress", self.scan_state['progress'])
                dpg.set_value("progress_text", f"{progress_percent}%")
                dpg.set_value("elapsed_time", elapsed_str)
                
                # Расчет ETA
                if progress_percent > 0:
                    total_time = elapsed.total_seconds() / (progress_percent / 100)
                    eta = self.scan_state['start_time'] + timedelta(seconds=total_time)
                    eta_str = eta.strftime("%H:%M:%S")
                    dpg.set_value("eta_time", eta_str)
            
            # Перезапускаем таймер
            self._start_scan_timer()
    
    def update_scan_progress(self, progress: float, phase: ScanPhase = None, activity: str = None):
        """Обновление прогресса сканирования"""
        self.scan_state['progress'] = progress
        
        if phase:
            self.scan_state['current_phase'] = phase
        
        if activity:
            dpg.set_value("current_activity", activity)
        
        progress_percent = int(progress * 100)
        dpg.set_value("scan_progress", progress)
        dpg.set_value("progress_text", f"{progress_percent}%")
    
    def get_scan_state(self) -> Dict[str, Any]:
        """Получение состояния сканирования"""
        state = self.scan_state.copy()
        
        # Добавляем информацию о статусе для UI
        if state['is_scanning']:
            if state['is_paused']:
                state.update({
                    'status': 'Paused',
                    'color': [255, 179, 64]
                })
            else:
                state.update({
                    'status': 'Scanning', 
                    'color': [255, 179, 64]
                })
        else:
            state.update({
                'status': 'Ready',
                'color': [72, 199, 116]
            })
        
        return state
    
    def get_scan_config(self) -> Dict[str, Any]:
        """Получение конфигурации сканирования"""
        return self.scan_config.copy()
    
    def set_engine(self, engine):
        """Установка движка сканирования"""
        self.engine = engine
    
    def set_callbacks(self, start_callback: Callable = None, pause_callback: Callable = None,
                     resume_callback: Callable = None, stop_callback: Callable = None,
                     config_callback: Callable = None):
        """Установка callback функций"""
        self.on_scan_start = start_callback
        self.on_scan_pause = pause_callback
        self.on_scan_resume = resume_callback
        self.on_scan_stop = stop_callback
        self.on_config_change = config_callback
    
    def add_to_log(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)
    
    def save_config(self, filename: str = "scan_config.json"):
        """Сохранение конфигурации в файл"""
        try:
            config_data = {
                'scan_config': self.scan_config,
                'metadata': {
                    'saved_at': datetime.now().isoformat(),
                    'version': '1.0'
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.add_to_log(f"💾 Config saved to {filename}")
            
        except Exception as e:
            self.add_to_log(f"❌ Error saving config: {e}")
    
    def load_config(self, filename: str = "scan_config.json"):
        """Загрузка конфигурации из файла"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.scan_config.update(data.get('scan_config', {}))
            self._update_ui_from_config()
            
            self.add_to_log(f"📥 Config loaded from {filename}")
            
        except Exception as e:
            self.add_to_log(f"❌ Error loading config: {e}")
    
    def _update_ui_from_config(self):
        """Обновление UI из конфигурации"""
        # Обновляем интенсивность
        intensity_map = {
            ScanIntensity.STEALTH: "🚀 Stealth",
            ScanIntensity.NORMAL: "⚡ Normal", 
            ScanIntensity.AGGRESSIVE: "💥 Aggressive",
            ScanIntensity.FULL_ATTACK: "🔥 Full Attack",
            ScanIntensity.PENTEST: "💀 Pentest"
        }
        
        dpg.set_value("quick_intensity", intensity_map.get(
            self.scan_config['intensity'], "⚡ Normal"
        ))
        
        # Обновляем фазы
        phases = self.scan_config['phases_enabled']
        dpg.set_value("phase_recon", phases.get('recon', True))
        dpg.set_value("phase_discovery", phases.get('discovery', True))
        dpg.set_value("phase_vuln", phases.get('vuln_scan', False))
        dpg.set_value("phase_exploit", phases.get('exploitation', False))
        
        # Обновляем настройки производительности
        options = self.scan_config['advanced_options']
        dpg.set_value("config_threads", options.get('max_threads', 5))
        dpg.set_value("config_rate_limit", options.get('rate_limit', 10))
        dpg.set_value("config_timeout", options.get('timeout', 5))
        
        # Обновляем stealth настройки
        dpg.set_value("stealth_mode", options.get('stealth_mode', True))
        dpg.set_value("randomize_scan", options.get('randomize_scan', True))
        dpg.set_value("obfuscate_traffic", options.get('obfuscate_traffic', False))
        dpg.set_value("use_proxies", options.get('use_proxies', False))
