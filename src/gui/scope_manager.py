"""
Scope Manager для Bug Bounty - умное управление областью сканирования
"""
import dearpygui.dearpygui as dpg
from typing import Dict, Any, List, Optional, Set, Callable
import logging
import json
import re
from datetime import datetime
import ipaddress

class ScopeManager:
    """
    Менеджер scope для Bug Bounty с защитой от выхода за пределы
    """
    
    def __init__(self):
        self.logger = logging.getLogger('RapidRecon.ScopeManager')
        self.scope_data = {
            'allowed_ips': set(),
            'allowed_domains': set(),
            'domain_suffixes': set(),
            'wildcard_domains': set(),
            'excluded_ips': set(),
            'excluded_domains': set(),
            'scope_name': 'Bug Bounty Scope',
            'program_url': '',
            'platform': 'Other'
        }
        self.in_scope_targets = set()
        self.out_of_scope_targets = set()
        self.scope_violations = []
        self.on_scope_change_callback = None
        
        # Платформы Bug Bounty
        self.bounty_platforms = [
            "HackerOne", "Bugcrowd", "Intigriti", "YesWeHack", 
            "Open Bug Bounty", "Other"
        ]
        
        # Популярные доменные суффиксы для подсказок
        self.common_suffixes = [".com", ".org", ".net", ".io", ".dev", ".app", ".cloud"]
    
    def create_scope_panel(self, parent: str) -> str:
        """Создание панели управления scope"""
        with dpg.child_window(parent=parent, border=False) as scope_panel:
            # Заголовок и быстрые действия
            with dpg.group(horizontal=True):
                dpg.add_text("🎯 Bug Bounty Scope")
                dpg.add_button(
                    label="💾 Save Scope",
                    callback=self.save_scope_settings
                )
                dpg.add_button(
                    label="📥 Load Scope",
                    callback=self.load_scope_settings
                )
            
            dpg.add_separator()
            
            # Основная конфигурация scope
            with dpg.tab_bar():
                # Вкладка быстрой настройки
                with dpg.tab(label="⚡ Quick Setup"):
                    self._create_quick_setup_tab()
                
                # Вкладка расширенной настройки
                with dpg.tab(label="🔧 Advanced"):
                    self._create_advanced_tab()
                
                # Вкладка импорта
                with dpg.tab(label="📥 Import"):
                    self._create_import_tab()
            
            # Статистика scope
            self._create_scope_statistics()
            
            # Список нарушений scope
            self._create_violations_list()
        
        return scope_panel
    
    def _create_quick_setup_tab(self):
        """Вкладка быстрой настройки scope"""
        with dpg.group():
            dpg.add_text("Program Information", color=[150, 150, 160])
            
            # Информация о программе
            dpg.add_input_text(
                tag="scope_name",
                label="Scope Name",
                default_value="Bug Bounty Scope",
                width=-1
            )
            
            dpg.add_input_text(
                tag="program_url", 
                label="Program URL",
                hint="https://hackerone.com/...",
                width=-1
            )
            
            dpg.add_combo(
                tag="bounty_platform",
                label="Platform",
                items=self.bounty_platforms,
                default_value="Other",
                width=-1
            )
            
            dpg.add_separator()
            dpg.add_text("Scope Definition", color=[150, 150, 160])
            
            # Быстрый ввод scope
            dpg.add_text("Allowed Domains:", color=[150, 150, 160])
            dpg.add_input_text(
                tag="quick_domains",
                hint="example.com, *.test.com, app.*.com...",
                multiline=True,
                height=80,
                width=-1
            )
            
            dpg.add_text("Allowed IP Ranges:", color=[150, 150, 160])
            dpg.add_input_text(
                tag="quick_ips",
                hint="192.168.1.0/24, 10.0.0.0/8, 203.0.113.1...",
                multiline=True,
                height=60,
                width=-1
            )
            
            dpg.add_text("Domain Suffixes (Auto-add):", color=[150, 150, 160])
            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    tag="domain_suffix",
                    hint=".com",
                    width=100
                )
                dpg.add_button(
                    label="Add Suffix",
                    callback=self._add_domain_suffix
                )
            
            # Предустановленные суффиксы
            dpg.add_text("Quick Suffixes:", color=[150, 150, 160])
            with dpg.group(horizontal=True):
                for suffix in self.common_suffixes:
                    dpg.add_button(
                        label=suffix,
                        width=60,
                        callback=lambda s, d, suf=suffix: self._quick_add_suffix(suf)
                    )
            
            dpg.add_button(
                label="🔄 Parse and Apply Scope",
                width=-1,
                callback=self.parse_and_apply_scope
            )
    
    def _create_advanced_tab(self):
        """Вкладка расширенной настройки scope"""
        with dpg.group():
            dpg.add_text("Advanced Scope Configuration", color=[150, 150, 160])
            
            with dpg.group(horizontal=True):
                # Разрешенные цели
                with dpg.child_window(width=300):
                    dpg.add_text("Allowed Targets")
                    dpg.add_input_text(
                        tag="allowed_domains",
                        hint="Domains and wildcards...",
                        multiline=True,
                        height=120,
                        width=-1
                    )
                    dpg.add_input_text(
                        tag="allowed_ips",
                        hint="IPs and ranges...",
                        multiline=True,
                        height=80,
                        width=-1
                    )
                
                # Исключенные цели
                with dpg.child_window(width=300):
                    dpg.add_text("Excluded Targets")
                    dpg.add_input_text(
                        tag="excluded_domains",
                        hint="Out-of-scope domains...",
                        multiline=True,
                        height=120,
                        width=-1
                    )
                    dpg.add_input_text(
                        tag="excluded_ips",
                        hint="Out-of-scope IPs...",
                        multiline=True,
                        height=80,
                        width=-1
                    )
            
            # Опции scope
            dpg.add_text("Scope Options:", color=[150, 150, 160])
            dpg.add_checkbox(
                tag="auto_detect_suffixes",
                label="Auto-detect domain suffixes",
                default_value=True
            )
            dpg.add_checkbox(
                tag="strict_mode", 
                label="Strict mode (block out-of-scope)",
                default_value=True
            )
            dpg.add_checkbox(
                tag="log_violations",
                label="Log scope violations",
                default_value=True
            )
    
    def _create_import_tab(self):
        """Вкладка импорта scope"""
        with dpg.group():
            dpg.add_text("Import Scope Configuration", color=[150, 150, 160])
            
            dpg.add_text("Import from Text:", color=[150, 150, 160])
            dpg.add_input_text(
                tag="import_text",
                hint="Paste scope from bug bounty platform...",
                multiline=True,
                height=150,
                width=-1
            )
            
            dpg.add_button(
                label="📥 Import from Text",
                width=-1,
                callback=self.import_from_text
            )
            
            dpg.add_separator()
            dpg.add_text("Import from File:", color=[150, 150, 160])
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="📁 Load JSON",
                    callback=self.load_scope_json
                )
                dpg.add_button(
                    label="💾 Save JSON",
                    callback=self.save_scope_json
                )
                dpg.add_button(
                    label="🔄 Load Defaults",
                    callback=self.load_default_scope
                )
    
    def _create_scope_statistics(self):
        """Создание панели статистики scope"""
        with dpg.group():
            dpg.add_separator()
            dpg.add_text("📊 Scope Statistics", color=[123, 97, 255])
            
            with dpg.group(horizontal=True):
                with dpg.child_window(width=200):
                    dpg.add_text("In Scope:", color=[150, 150, 160])
                    dpg.add_text("Domains: 0", tag="stat_scope_domains")
                    dpg.add_text("IP Ranges: 0", tag="stat_scope_ips")
                    dpg.add_text("Suffixes: 0", tag="stat_scope_suffixes")
                
                with dpg.child_window(width=200):
                    dpg.add_text("Discovered:", color=[150, 150, 160])
                    dpg.add_text("In Scope: 0", tag="stat_in_scope")
                    dpg.add_text("Out of Scope: 0", tag="stat_out_scope")
                    dpg.add_text("Violations: 0", tag="stat_violations")
            
            dpg.add_button(
                label="🔄 Update Statistics",
                callback=self.update_statistics
            )
    
    def _create_violations_list(self):
        """Создание списка нарушений scope"""
        with dpg.group():
            dpg.add_separator()
            dpg.add_text("🚨 Scope Violations", color=[255, 100, 100])
            
            dpg.add_listbox(
                tag="violations_list",
                items=[],
                num_items=6,
                width=-1
            )
            
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="🧹 Clear Violations",
                    callback=self.clear_violations
                )
                dpg.add_button(
                    label="📋 Export Violations",
                    callback=self.export_violations
                )
    
    def _add_domain_suffix(self):
        """Добавление доменного суффикса"""
        suffix = dpg.get_value("domain_suffix")
        if suffix and suffix not in self.scope_data['domain_suffixes']:
            self.scope_data['domain_suffixes'].add(suffix)
            self.update_statistics()
            self.add_to_log(f"✅ Added domain suffix: {suffix}")
    
    def _quick_add_suffix(self, suffix: str):
        """Быстрое добавление суффикса"""
        if suffix not in self.scope_data['domain_suffixes']:
            self.scope_data['domain_suffixes'].add(suffix)
            self.update_statistics()
            self.add_to_log(f"✅ Added domain suffix: {suffix}")
    
    def parse_and_apply_scope(self):
        """Парсинг и применение scope из быстрого ввода"""
        try:
            # Парсим домены
            domains_text = dpg.get_value("quick_domains")
            if domains_text:
                domains = self._parse_domains(domains_text)
                self.scope_data['allowed_domains'].update(domains['domains'])
                self.scope_data['wildcard_domains'].update(domains['wildcards'])
            
            # Парсим IP
            ips_text = dpg.get_value("quick_ips")
            if ips_text:
                ips = self._parse_ips(ips_text)
                self.scope_data['allowed_ips'].update(ips)
            
            # Обновляем остальные настройки
            self.scope_data['scope_name'] = dpg.get_value("scope_name")
            self.scope_data['program_url'] = dpg.get_value("program_url")
            
            # Авто-определение суффиксов
            if dpg.get_value("auto_detect_suffixes"):
                self._auto_detect_suffixes()
            
            self.update_statistics()
            self._update_ui_from_scope()
            self.add_to_log("✅ Scope parsed and applied successfully")
            
        except Exception as e:
            self.add_to_log(f"❌ Error parsing scope: {e}")
    
    def _parse_domains(self, text: str) -> Dict[str, Set]:
        """Парсинг доменов из текста"""
        domains = set()
        wildcards = set()
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Обработка wildcard доменов
            if '*' in line:
                wildcards.add(line.lower())
            else:
                domains.add(line.lower())
                
                # Автоматически добавляем суффикс
                if '.' in line:
                    suffix = '.' + line.split('.')[-1]
                    if suffix not in self.common_suffixes:
                        self.common_suffixes.append(suffix)
        
        return {'domains': domains, 'wildcards': wildcards}
    
    def _parse_ips(self, text: str) -> Set:
        """Парсинг IP и диапазонов из текста"""
        ips = set()
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                # Проверяем, является ли IP или диапазоном
                if '/' in line:
                    # CIDR диапазон
                    ipaddress.IPv4Network(line, strict=False)
                    ips.add(line)
                else:
                    # Одиночный IP
                    ipaddress.IPv4Address(line)
                    ips.add(line)
            except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
                self.add_to_log(f"⚠️ Invalid IP format: {line}")
        
        return ips
    
    def _auto_detect_suffixes(self):
        """Автоматическое определение доменных суффиксов"""
        suffixes = set()
        
        for domain in self.scope_data['allowed_domains']:
            if '.' in domain:
                parts = domain.split('.')
                if len(parts) >= 2:
                    suffix = '.' + '.'.join(parts[-2:])  # Берем два последних уровня
                    suffixes.add(suffix)
        
        self.scope_data['domain_suffixes'].update(suffixes)
    
    def is_in_scope(self, target: str) -> bool:
        """
        Проверка, находится ли цель в scope
        
        Args:
            target: Цель для проверки (домен или IP)
            
        Returns:
            True если цель в scope, False если нет
        """
        # Проверка IP
        if self._is_ip(target):
            return self._is_ip_in_scope(target)
        
        # Проверка домена
        return self._is_domain_in_scope(target.lower())
    
    def _is_ip(self, target: str) -> bool:
        """Проверка, является ли цель IP адресом"""
        try:
            ipaddress.IPv4Address(target)
            return True
        except ipaddress.AddressValueError:
            return False
    
    def _is_ip_in_scope(self, ip: str) -> bool:
        """Проверка IP на вхождение в scope"""
        # Проверка исключений
        if ip in self.scope_data['excluded_ips']:
            return False
        
        # Проверка разрешенных IP
        for allowed_ip in self.scope_data['allowed_ips']:
            if '/' in allowed_ip:
                # CIDR диапазон
                if ipaddress.IPv4Address(ip) in ipaddress.IPv4Network(allowed_ip, strict=False):
                    return True
            else:
                # Одиночный IP
                if ip == allowed_ip:
                    return True
        
        return False
    
    def _is_domain_in_scope(self, domain: str) -> bool:
        """Проверка домена на вхождение в scope"""
        # Проверка исключений
        if domain in self.scope_data['excluded_domains']:
            return False
        
        # Проверка точных совпадений
        if domain in self.scope_data['allowed_domains']:
            return True
        
        # Проверка wildcard доменов
        for wildcard in self.scope_data['wildcard_domains']:
            if self._matches_wildcard(domain, wildcard):
                return True
        
        # Проверка по суффиксам
        for suffix in self.scope_data['domain_suffixes']:
            if domain.endswith(suffix):
                return True
        
        return False
    
    def _matches_wildcard(self, domain: str, wildcard: str) -> bool:
        """Проверка соответствия домена wildcard шаблону"""
        # Простая реализация wildcard matching
        if wildcard.startswith('*.'):
            # *.example.com
            suffix = wildcard[2:]
            return domain.endswith(suffix) or domain == suffix[1:]
        elif wildcard.endswith('.*'):
            # example.*
            prefix = wildcard[:-2]
            return domain.startswith(prefix)
        elif '*' in wildcard:
            # Более сложные шаблоны (app.*.example.com)
            pattern = wildcard.replace('.', '\\.').replace('*', '.*')
            return bool(re.match(pattern, domain))
        
        return False
    
    def add_to_scope(self, target: str) -> bool:
        """
        Добавление цели в scope
        
        Args:
            target: Цель для добавления
            
        Returns:
            True если успешно добавлено
        """
        try:
            if self._is_ip(target):
                self.scope_data['allowed_ips'].add(target)
            else:
                self.scope_data['allowed_domains'].add(target.lower())
            
            self.update_statistics()
            return True
            
        except Exception as e:
            self.add_to_log(f"❌ Error adding to scope: {e}")
            return False
    
    def remove_from_scope(self, target: str) -> bool:
        """
        Удаление цели из scope
        
        Args:
            target: Цель для удаления
            
        Returns:
            True если успешно удалено
        """
        if target in self.scope_data['allowed_ips']:
            self.scope_data['allowed_ips'].remove(target)
        elif target.lower() in self.scope_data['allowed_domains']:
            self.scope_data['allowed_domains'].remove(target.lower())
        else:
            return False
        
        self.update_statistics()
        return True
    
    def log_violation(self, target: str, source: str = "unknown"):
        """Логирование нарушения scope"""
        violation = {
            'target': target,
            'source': source,
            'timestamp': datetime.now().isoformat(),
            'type': 'ip' if self._is_ip(target) else 'domain'
        }
        
        self.scope_violations.append(violation)
        
        # Обновляем UI
        violations_list = [f"{v['target']} ({v['source']})" for v in self.scope_violations[-10:]]
        dpg.configure_item("violations_list", items=violations_list)
        
        self.update_statistics()
        
        if dpg.get_value("log_violations"):
            self.add_to_log(f"🚨 Scope violation: {target} from {source}")
    
    def save_scope_settings(self):
        """Сохранение настроек scope"""
        try:
            # Собираем данные из UI
            self._update_scope_from_ui()
            
            # Сохраняем в файл
            filename = f"scope_{self.scope_data['scope_name'].replace(' ', '_')}.json"
            with open(filename, 'w') as f:
                json.dump({
                    'scope_data': {
                        'allowed_ips': list(self.scope_data['allowed_ips']),
                        'allowed_domains': list(self.scope_data['allowed_domains']),
                        'domain_suffixes': list(self.scope_data['domain_suffixes']),
                        'wildcard_domains': list(self.scope_data['wildcard_domains']),
                        'excluded_ips': list(self.scope_data['excluded_ips']),
                        'excluded_domains': list(self.scope_data['excluded_domains']),
                        'scope_name': self.scope_data['scope_name'],
                        'program_url': self.scope_data['program_url'],
                        'platform': self.scope_data['platform']
                    },
                    'metadata': {
                        'export_time': datetime.now().isoformat(),
                        'version': '1.0'
                    }
                }, f, indent=2)
            
            self.add_to_log(f"💾 Scope saved to {filename}")
            
        except Exception as e:
            self.add_to_log(f"❌ Error saving scope: {e}")
    
    def load_scope_settings(self):
        """Загрузка настроек scope"""
        try:
            filename = f"scope_{self.scope_data['scope_name'].replace(' ', '_')}.json"
            with open(filename, 'r') as f:
                data = json.load(f)
            
            scope_data = data['scope_data']
            self.scope_data['allowed_ips'] = set(scope_data.get('allowed_ips', []))
            self.scope_data['allowed_domains'] = set(scope_data.get('allowed_domains', []))
            self.scope_data['domain_suffixes'] = set(scope_data.get('domain_suffixes', []))
            self.scope_data['wildcard_domains'] = set(scope_data.get('wildcard_domains', []))
            self.scope_data['excluded_ips'] = set(scope_data.get('excluded_ips', []))
            self.scope_data['excluded_domains'] = set(scope_data.get('excluded_domains', []))
            self.scope_data['scope_name'] = scope_data.get('scope_name', 'Bug Bounty Scope')
            self.scope_data['program_url'] = scope_data.get('program_url', '')
            self.scope_data['platform'] = scope_data.get('platform', 'Other')
            
            self._update_ui_from_scope()
            self.update_statistics()
            self.add_to_log(f"📥 Scope loaded from {filename}")
            
        except Exception as e:
            self.add_to_log(f"❌ Error loading scope: {e}")
    
    def import_from_text(self):
        """Импорт scope из текста"""
        try:
            text = dpg.get_value("import_text")
            if not text:
                return
            
            # Простой парсинг common scope formats
            domains = set()
            ips = set()
            
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Пропускаем комментарии и заголовки
                if line.startswith('#') or line.startswith('//') or ':' in line and len(line) < 50:
                    continue
                
                # Парсим домены и IP
                if self._is_ip(line):
                    ips.add(line)
                else:
                    domains.add(line.lower())
            
            self.scope_data['allowed_domains'].update(domains)
            self.scope_data['allowed_ips'].update(ips)
            
            self._update_ui_from_scope()
            self.update_statistics()
            self.add_to_log(f"✅ Imported {len(domains)} domains and {len(ips)} IPs")
            
        except Exception as e:
            self.add_to_log(f"❌ Error importing scope: {e}")
    
    def load_scope_json(self):
        """Загрузка scope из JSON файла"""
        # Заглушка для загрузки из файла
        self.add_to_log("📁 Load JSON functionality - to be implemented")
    
    def save_scope_json(self):
        """Сохранение scope в JSON файл"""
        self.save_scope_settings()
    
    def load_default_scope(self):
        """Загрузка scope по умолчанию"""
        self.scope_data = {
            'allowed_ips': set(),
            'allowed_domains': set(['example.com', 'test.com']),
            'domain_suffixes': set(['.com', '.org']),
            'wildcard_domains': set(['*.example.com']),
            'excluded_ips': set(),
            'excluded_domains': set(),
            'scope_name': 'Default Bug Bounty Scope',
            'program_url': '',
            'platform': 'Other'
        }
        
        self._update_ui_from_scope()
        self.update_statistics()
        self.add_to_log("🔄 Loaded default scope")
    
    def _update_scope_from_ui(self):
        """Обновление scope данных из UI"""
        # Обновляем из advanced вкладки
        domains_text = dpg.get_value("allowed_domains")
        if domains_text:
            parsed = self._parse_domains(domains_text)
            self.scope_data['allowed_domains'] = parsed['domains']
            self.scope_data['wildcard_domains'] = parsed['wildcards']
        
        ips_text = dpg.get_value("allowed_ips")
        if ips_text:
            self.scope_data['allowed_ips'] = self._parse_ips(ips_text)
    
    def _update_ui_from_scope(self):
        """Обновление UI из scope данных"""
        # Обновляем quick setup
        dpg.set_value("scope_name", self.scope_data['scope_name'])
        dpg.set_value("program_url", self.scope_data['program_url'])
        
        # Обновляем advanced вкладку
        domains_text = '\n'.join(sorted(self.scope_data['allowed_domains'] | self.scope_data['wildcard_domains']))
        dpg.set_value("allowed_domains", domains_text)
        
        ips_text = '\n'.join(sorted(self.scope_data['allowed_ips']))
        dpg.set_value("allowed_ips", ips_text)
    
    def update_statistics(self):
        """Обновление статистики scope"""
        dpg.set_value("stat_scope_domains", f"Domains: {len(self.scope_data['allowed_domains'])}")
        dpg.set_value("stat_scope_ips", f"IP Ranges: {len(self.scope_data['allowed_ips'])}")
        dpg.set_value("stat_scope_suffixes", f"Suffixes: {len(self.scope_data['domain_suffixes'])}")
        dpg.set_value("stat_in_scope", f"In Scope: {len(self.in_scope_targets)}")
        dpg.set_value("stat_out_scope", f"Out of Scope: {len(self.out_of_scope_targets)}")
        dpg.set_value("stat_violations", f"Violations: {len(self.scope_violations)}")
    
    def clear_violations(self):
        """Очистка нарушений scope"""
        self.scope_violations.clear()
        dpg.configure_item("violations_list", items=[])
        self.update_statistics()
        self.add_to_log("🧹 Scope violations cleared")
    
    def export_violations(self):
        """Экспорт нарушений scope"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scope_violations_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(self.scope_violations, f, indent=2)
            
            self.add_to_log(f"📋 Scope violations exported to {filename}")
            
        except Exception as e:
            self.add_to_log(f"❌ Error exporting violations: {e}")
    
    def add_to_log(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)
    
    def set_scope_change_callback(self, callback: Callable):
        """Установка callback при изменении scope"""
        self.on_scope_change_callback = callback
    
    def clear(self):
        """Очистка scope"""
        self.scope_data = {
            'allowed_ips': set(),
            'allowed_domains': set(),
            'domain_suffixes': set(),
            'wildcard_domains': set(),
            'excluded_ips': set(),
            'excluded_domains': set(),
            'scope_name': 'Bug Bounty Scope',
            'program_url': '',
            'platform': 'Other'
        }
        self.in_scope_targets.clear()
        self.out_of_scope_targets.clear()
        self.scope_violations.clear()
        
        self._update_ui_from_scope()
        self.update_statistics()
        self.add_to_log("🧹 Scope cleared")
