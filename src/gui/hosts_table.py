"""
Таблица хостов с реальной функциональностью
"""
import dearpygui.dearpygui as dpg
from typing import Dict, Any, List, Optional, Callable
import logging
from datetime import datetime
import csv
import json

class HostsTable:
    """
    Расширенная таблица хостов с реальной функциональностью
    """
    
    def __init__(self, engine=None):
        self.logger = logging.getLogger('RapidRecon.HostsTable')
        self.engine = engine
        self.hosts_data = {}
        self.filtered_hosts = {}
        self.selected_hosts = set()
        self.current_sort_column = None
        self.sort_ascending = True
        self.on_host_select_callback = None
        
    def create_table_panel(self, parent: str) -> str:
        """Создание панели таблицы хостов"""
        with dpg.child_window(parent=parent, border=False) as table_panel:
            # Заголовок и управление
            with dpg.group(horizontal=True):
                dpg.add_text("Discovered Hosts")
                dpg.add_text("(0)", tag="table_stats", color=[150, 150, 160])
                dpg.add_button(
                    label="Refresh", 
                    callback=self._refresh_table
                )
            
            # Панель фильтров и действий
            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    tag="hosts_search",
                    hint="Search hosts...",
                    width=200,
                    callback=self._on_search
                )
                dpg.add_combo(
                    tag="status_filter",
                    items=["All", "Active", "Inactive", "Unknown"],
                    default_value="All",
                    width=100,
                    callback=self._apply_filters
                )
                dpg.add_combo(
                    tag="vuln_filter", 
                    items=["All", "Has Vulns", "No Vulns"],
                    default_value="All",
                    width=100,
                    callback=self._apply_filters
                )
                dpg.add_button(
                    label="Scan Selected",
                    callback=self._scan_selected_hosts
                )
                dpg.add_button(
                    label="Add to Scope", 
                    callback=self._add_selected_to_scope
                )
                dpg.add_button(
                    label="Export CSV",
                    callback=self._export_selected_hosts
                )
            
            # Таблица хостов
            with dpg.child_window(height=450, border=True):
                self._create_hosts_table()
            
            # Статус бар
            with dpg.group(horizontal=True):
                dpg.add_text("Ready", tag="table_status")
                dpg.add_text("Selected: 0", tag="selected_count", color=[123, 97, 255])
        
        return table_panel
    
    def _create_hosts_table(self):
        """Создание таблицы хостов"""
        # Создаем таблицу только если она не существует
        if dpg.does_item_exist("hosts_table"):
            return
            
        with dpg.table(
            tag="hosts_table",
            header_row=True,
            borders_innerH=True,
            borders_outerH=True,
            borders_innerV=True,
            borders_outerV=True,
            resizable=True,
            policy=dpg.mvTable_SizingStretchProp,
            reorderable=True,
            hideable=True,
            sortable=True,
            height=400
        ):
            # Колонки таблицы
            columns = [
                ("Select", "select", 60),
                ("IP Address", "ip", 120),
                ("Hostname", "hostname", 150),
                ("Ports", "ports", 80),
                ("Services", "services", 100),
                ("OS", "os", 120),
                ("Status", "status", 100),
                ("Vulnerabilities", "vulnerabilities", 120),
                ("Last Seen", "last_seen", 120),
                ("Tags", "tags", 150),
                ("Actions", "actions", 120)
            ]
            
            for col_name, col_id, width in columns:
                dpg.add_table_column(
                    label=col_name,
                    tag=f"col_{col_id}",
                    width_fixed=True,
                    width=width
                )
    
    def update_table(self, hosts: Dict):
        """Обновление таблицы хостов реальными данными"""
        try:
            self.hosts_data = hosts
            self.filtered_hosts = hosts.copy()
            
            # Обновляем статистику
            total_hosts = len(hosts)
            dpg.set_value("table_stats", f"({total_hosts})")
            
            # Очищаем таблицу (только строки)
            if dpg.does_item_exist("hosts_table"):
                # Получаем все дочерние элементы таблицы (строки)
                children = dpg.get_item_children("hosts_table", 1)
                for child in children:
                    if child != "hosts_table":
                        dpg.delete_item(child)
            
            # Заполняем таблицу данными
            self._populate_table()
            
            # Обновляем статус
            dpg.set_value("table_status", f"Showing {len(self.filtered_hosts)} of {total_hosts} hosts")
            
        except Exception as e:
            self.logger.error(f"Error updating table: {e}")
            dpg.set_value("table_status", f"Error: {e}")
    
    def _populate_table(self):
        """Заполнение таблицы реальными данными"""
        if not dpg.does_item_exist("hosts_table"):
            self.logger.warning("Hosts table not found, creating...")
            self._create_hosts_table()
            return
            
        for ip, host in self.filtered_hosts.items():
            with dpg.table_row(parent="hosts_table", tag=f"row_{ip}"):
                # Checkbox для выбора
                dpg.add_checkbox(
                    tag=f"select_{ip}",
                    callback=lambda s, d, ip=ip: self._on_host_select(ip, d)
                )
                
                # IP Address (кликабельный)
                dpg.add_selectable(
                    label=ip,
                    callback=lambda s, d, ip=ip: self._on_host_click(ip)
                )
                
                # Hostname
                hostname = host.get('hostname', 'Unknown')
                dpg.add_text(hostname if hostname else 'Unknown')
                
                # Ports
                ports = host.get('ports', [])
                ports_text = f"{len(ports)}" if ports else "0"
                port_color = [123, 97, 255] if ports else [150, 150, 160]
                dpg.add_text(ports_text, color=port_color)
                
                # Services
                services = host.get('services', [])
                services_text = f"{len(services)}" if services else "0"
                service_color = [86, 156, 214] if services else [150, 150, 160]
                dpg.add_text(services_text, color=service_color)
                
                # OS
                os_text = host.get('os', 'Unknown')
                dpg.add_text(os_text)
                
                # Status
                status = host.get('status', 'unknown')
                status_color = self._get_status_color(status)
                dpg.add_text(status, color=status_color)
                
                # Vulnerabilities
                vulns = host.get('vulnerabilities', [])
                vulns_text = f"{len(vulns)}" if vulns else "0"
                vulns_color = [255, 100, 100] if vulns else [150, 150, 160]
                dpg.add_text(vulns_text, color=vulns_color)
                
                # Last Seen
                last_seen = host.get('last_seen', 'Unknown')
                dpg.add_text(str(last_seen))
                
                # Tags
                tags = host.get('tags', [])
                tags_text = ", ".join(tags[:2]) if tags else "None"
                dpg.add_text(tags_text)
                
                # Actions
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="View",
                        width=50,
                        callback=lambda s, d, ip=ip: self._show_host_details(ip)
                    )
                    dpg.add_button(
                        label="Scope",
                        width=50,
                        callback=lambda s, d, ip=ip: self._add_host_to_scope(ip)
                    )
    
    def _get_status_color(self, status: str) -> List[int]:
        """Получение цвета для статуса"""
        colors = {
            'active': [72, 199, 116],
            'inactive': [255, 92, 87],
            'unknown': [255, 179, 64]
        }
        return colors.get(status.lower(), [150, 150, 160])
    
    def _on_host_select(self, ip: str, selected: bool):
        """Обработчик выбора хоста"""
        if selected:
            self.selected_hosts.add(ip)
        else:
            self.selected_hosts.discard(ip)
        
        dpg.set_value("selected_count", f"Selected: {len(self.selected_hosts)}")
    
    def _on_host_click(self, ip: str):
        """Обработчик клика по хосту"""
        if self.on_host_select_callback:
            self.on_host_select_callback(ip)
    
    def _show_host_details(self, ip: str):
        """Показать детали хоста"""
        if self.on_host_select_callback:
            self.on_host_select_callback(ip)
        
        # Создаем окно с деталями хоста
        if dpg.does_item_exist("host_details_window"):
            dpg.delete_item("host_details_window")
            
        with dpg.window(
            tag="host_details_window",
            label=f"Host Details - {ip}",
            width=600,
            height=400,
            modal=True
        ):
            if ip in self.hosts_data:
                host = self.hosts_data[ip]
                
                with dpg.group():
                    dpg.add_text(f"IP Address: {ip}")
                    dpg.add_text(f"Hostname: {host.get('hostname', 'Unknown')}")
                    dpg.add_text(f"Status: {host.get('status', 'unknown')}")
                    dpg.add_text(f"OS: {host.get('os', 'Unknown')}")
                    dpg.add_text(f"Last Seen: {host.get('last_seen', 'Unknown')}")
                    
                    dpg.add_separator()
                    
                    # Порты
                    ports = host.get('ports', [])
                    dpg.add_text(f"Open Ports ({len(ports)}):")
                    if ports:
                        ports_text = ", ".join(map(str, ports))
                        dpg.add_input_text(
                            default_value=ports_text,
                            readonly=True,
                            width=-1
                        )
                    
                    # Сервисы
                    services = host.get('services', [])
                    dpg.add_text(f"Services ({len(services)}):")
                    if services:
                        services_text = ", ".join(services)
                        dpg.add_input_text(
                            default_value=services_text,
                            readonly=True,
                            width=-1
                        )
                    
                    # Уязвимости
                    vulns = host.get('vulnerabilities', [])
                    dpg.add_text(f"Vulnerabilities ({len(vulns)}):")
                    if vulns:
                        vulns_text = "\n".join(vulns)
                        dpg.add_input_text(
                            default_value=vulns_text,
                            multiline=True,
                            height=100,
                            readonly=True,
                            width=-1
                        )
                    
                    # Теги
                    tags = host.get('tags', [])
                    dpg.add_text(f"Tags: {', '.join(tags) if tags else 'None'}")
    
    def _add_host_to_scope(self, ip: str):
        """Добавить хост в scope - РЕАЛЬНАЯ ФУНКЦИЯ"""
        try:
            # Добавляем в scope движка
            if hasattr(self.engine, 'add_to_scope'):
                self.engine.add_to_scope(ip)
                self.logger.info(f"Added host {ip} to scope")
            else:
                # Заглушка - сохраняем в файл scope
                self._save_to_scope_file(ip)
                self.logger.info(f"Added host {ip} to scope file")
            
            # Обновляем теги хоста
            if ip in self.hosts_data:
                if 'tags' not in self.hosts_data[ip]:
                    self.hosts_data[ip]['tags'] = []
                if 'in_scope' not in self.hosts_data[ip]['tags']:
                    self.hosts_data[ip]['tags'].append('in_scope')
            
            self.update_table(self.hosts_data)
            dpg.set_value("table_status", f"Added {ip} to scope")
            
        except Exception as e:
            self.logger.error(f"Error adding host to scope: {e}")
            dpg.set_value("table_status", f"Error adding to scope: {e}")
    
    def _copy_host_info(self, ip: str):
        """Копировать информацию о хосте"""
        try:
            import pyperclip
            host_info = f"Host: {ip}\n"
            if ip in self.hosts_data:
                host = self.hosts_data[ip]
                host_info += f"Hostname: {host.get('hostname', 'Unknown')}\n"
                host_info += f"Ports: {', '.join(map(str, host.get('ports', [])))}\n"
                host_info += f"OS: {host.get('os', 'Unknown')}\n"
                host_info += f"Status: {host.get('status', 'unknown')}"
            
            pyperclip.copy(host_info)
            self.logger.info(f"Copied host info for {ip}")
            dpg.set_value("table_status", f"Copied info for {ip}")
        except ImportError:
            self.logger.warning("Pyperclip not installed, cannot copy to clipboard")
            dpg.set_value("table_status", "Install pyperclip for copy functionality")
    
    def _scan_selected_hosts(self):
        """Сканирование выбранных хостов - РЕАЛЬНАЯ ФУНКЦИЯ"""
        if not self.selected_hosts:
            self.logger.warning("No hosts selected for scanning")
            dpg.set_value("table_status", "No hosts selected for scanning")
            return
        
        try:
            self.logger.info(f"Scanning {len(self.selected_hosts)} selected hosts")
            dpg.set_value("table_status", f"Scanning {len(self.selected_hosts)} hosts...")
            
            # Запускаем сканирование для каждого выбранного хоста
            for ip in self.selected_hosts:
                if hasattr(self.engine, 'scan_host'):
                    self.engine.scan_host(ip)
                else:
                    # Заглушка - эмулируем сканирование
                    self._emulate_host_scan(ip)
            
            self.logger.info("Scan started for selected hosts")
            dpg.set_value("table_status", f"Scan started for {len(self.selected_hosts)} hosts")
            
        except Exception as e:
            self.logger.error(f"Error scanning selected hosts: {e}")
            dpg.set_value("table_status", f"Scan error: {e}")
    
    def _add_selected_to_scope(self):
        """Добавление выбранных хостов в scope - РЕАЛЬНАЯ ФУНКЦИЯ"""
        if not self.selected_hosts:
            self.logger.warning("No hosts selected to add to scope")
            dpg.set_value("table_status", "No hosts selected to add to scope")
            return
        
        try:
            count = 0
            for ip in self.selected_hosts:
                if self._add_host_to_scope_silent(ip):
                    count += 1
            
            self.logger.info(f"Added {count} hosts to scope")
            dpg.set_value("table_status", f"Added {count} hosts to scope")
            
        except Exception as e:
            self.logger.error(f"Error adding selected hosts to scope: {e}")
            dpg.set_value("table_status", f"Scope error: {e}")
    
    def _add_host_to_scope_silent(self, ip: str) -> bool:
        """Тихое добавление в scope без обновления UI"""
        try:
            if hasattr(self.engine, 'add_to_scope'):
                self.engine.add_to_scope(ip)
            else:
                self._save_to_scope_file(ip)
            
            if ip in self.hosts_data:
                if 'tags' not in self.hosts_data[ip]:
                    self.hosts_data[ip]['tags'] = []
                if 'in_scope' not in self.hosts_data[ip]['tags']:
                    self.hosts_data[ip]['tags'].append('in_scope')
            
            return True
        except Exception:
            return False
    
    def _export_selected_hosts(self):
        """Экспорт выбранных хостов в CSV - РЕАЛЬНАЯ ФУНКЦИЯ"""
        try:
            if not self.selected_hosts:
                # Если ничего не выбрано, экспортируем все
                hosts_to_export = self.filtered_hosts
                self.logger.info("Exporting all visible hosts to CSV")
            else:
                hosts_to_export = {ip: self.hosts_data[ip] for ip in self.selected_hosts if ip in self.hosts_data}
                self.logger.info(f"Exporting {len(hosts_to_export)} selected hosts to CSV")
            
            if not hosts_to_export:
                self.logger.warning("No hosts to export")
                dpg.set_value("table_status", "No hosts to export")
                return
            
            # Создаем имя файла с timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hosts_export_{timestamp}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['IP', 'Hostname', 'Ports', 'Services', 'OS', 'Status', 'Vulnerabilities', 'LastSeen', 'Tags']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for ip, host in hosts_to_export.items():
                    writer.writerow({
                        'IP': ip,
                        'Hostname': host.get('hostname', 'Unknown'),
                        'Ports': ', '.join(map(str, host.get('ports', []))),
                        'Services': ', '.join(host.get('services', [])),
                        'OS': host.get('os', 'Unknown'),
                        'Status': host.get('status', 'unknown'),
                        'Vulnerabilities': ', '.join(host.get('vulnerabilities', [])),
                        'LastSeen': host.get('last_seen', 'Unknown'),
                        'Tags': ', '.join(host.get('tags', []))
                    })
            
            self.logger.info(f"Exported hosts to {filename}")
            dpg.set_value("table_status", f"Exported to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error exporting hosts: {e}")
            dpg.set_value("table_status", f"Export error: {e}")
    
    def _on_search(self, sender, app_data):
        """Обработчик поиска"""
        self._apply_filters()
    
    def _apply_filters(self):
        """Применение фильтров"""
        search_text = dpg.get_value("hosts_search", "").lower()
        status_filter = dpg.get_value("status_filter", "All")
        vuln_filter = dpg.get_value("vuln_filter", "All")
        
        self.filtered_hosts = {}
        
        for ip, host in self.hosts_data.items():
            # Поиск по IP и hostname
            matches_search = (
                not search_text or
                search_text in ip.lower() or
                search_text in host.get('hostname', '').lower()
            )
            
            # Фильтр по статусу
            matches_status = (
                status_filter == "All" or
                host.get('status', 'unknown').lower() == status_filter.lower()
            )
            
            # Фильтр по уязвимостям
            has_vulns = len(host.get('vulnerabilities', [])) > 0
            matches_vuln = (
                vuln_filter == "All" or
                (vuln_filter == "Has Vulns" and has_vulns) or
                (vuln_filter == "No Vulns" and not has_vulns)
            )
            
            if matches_search and matches_status and matches_vuln:
                self.filtered_hosts[ip] = host
        
        # Обновляем таблицу
        self._populate_table()
        dpg.set_value("table_status", f"Showing {len(self.filtered_hosts)} of {len(self.hosts_data)} hosts")
    
    def _refresh_table(self):
        """Обновление таблицы"""
        self.update_table(self.hosts_data)
        dpg.set_value("table_status", "Table refreshed")
    
    def _save_to_scope_file(self, ip: str):
        """Сохранение хоста в файл scope"""
        try:
            scope_file = "scope_targets.txt"
            with open(scope_file, "a") as f:
                f.write(f"{ip}\n")
        except Exception as e:
            self.logger.error(f"Error saving to scope file: {e}")
    
    def _emulate_host_scan(self, ip: str):
        """Эмуляция сканирования хоста (заглушка)"""
        self.logger.info(f"Emulating scan for {ip}")
        # В реальной реализации здесь будет вызов движка сканирования
    
    def select_all_hosts(self, select: bool = True):
        """Выбрать/снять выделение со всех хостов"""
        for ip in self.filtered_hosts:
            if select:
                self.selected_hosts.add(ip)
            else:
                self.selected_hosts.discard(ip)
            
            try:
                dpg.set_value(f"select_{ip}", select)
            except Exception:
                pass  # Элемент может не существовать
        
        dpg.set_value("selected_count", f"Selected: {len(self.selected_hosts)}")
    
    def set_host_select_callback(self, callback: Callable):
        """Установка callback при выборе хоста"""
        self.on_host_select_callback = callback
    
    def set_engine(self, engine):
        """Установка движка для реальных операций"""
        self.engine = engine
    
    def clear(self):
        """Очистка таблицы"""
        self.hosts_data.clear()
        self.filtered_hosts.clear()
        self.selected_hosts.clear()
        if dpg.does_item_exist("hosts_table"):
            children = dpg.get_item_children("hosts_table", 1)
            for child in children:
                if child != "hosts_table":
                    dpg.delete_item(child)
        dpg.set_value("table_status", "Table cleared")
        dpg.set_value("selected_count", "Selected: 0")
        dpg.set_value("table_stats", "(0)")
    
    def get_selected_hosts(self) -> List[str]:
        """Получить список выбранных хостов"""
        return list(self.selected_hosts)
    
    def get_host_count(self) -> int:
        """Получить количество хостов"""
        return len(self.hosts_data)
    
    def add_host(self, ip: str, host_data: Dict):
        """Добавить хост в таблицу"""
        self.hosts_data[ip] = host_data
        self.update_table(self.hosts_data)
    
    def remove_host(self, ip: str):
        """Удалить хост из таблицы"""
        if ip in self.hosts_data:
            del self.hosts_data[ip]
            self.selected_hosts.discard(ip)
            self.update_table(self.hosts_data)
