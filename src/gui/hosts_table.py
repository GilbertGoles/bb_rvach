"""
Таблица хостов с расширенными функциями
"""
import dearpygui.dearpygui as dpg
from typing import Dict, Any, List, Optional, Callable
import logging
from datetime import datetime

class HostsTable:
    """
    Расширенная таблица хостов с сортировкой и фильтрацией
    """
    
    def __init__(self):
        self.logger = logging.getLogger('RapidRecon.HostsTable')
        self.hosts_data = {}
        self.filtered_hosts = {}
        self.current_sort_column = None
        self.sort_ascending = True
        self.on_host_select_callback = None
        
    def create_table_panel(self, parent: str) -> str:
        """Создание панели таблицы хостов"""
        with dpg.child_window(parent=parent, border=False) as table_panel:
            # Заголовок и управление
            with dpg.group(horizontal=True):
                dpg.add_text("📊 Discovered Hosts")
                dpg.add_text("(0)", tag="table_stats", color=[150, 150, 160])
                dpg.add_button(
                    label="🔄 Refresh", 
                    callback=self._refresh_table
                )
            
            # Панель фильтров
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
            
            # Таблица хостов
            with dpg.child_window(height=500, border=True):
                self._create_hosts_table()
            
            # Статус бар
            with dpg.group(horizontal=True):
                dpg.add_text("Ready", tag="table_status")
        
        return table_panel
    
    def _create_hosts_table(self):
        """Создание таблицы хостов"""
        with dpg.table(
            tag="hosts_table",
            header_row=True,
            borders_innerH=True,
            borders_outerH=True,
            borders_innerV=True,
            borders_outerV=True,
            resizable=True,
            policy=dpg.mvTable_SizingStretchProp,
            row_background=True,
            reorderable=True,
            hideable=True,
            sortable=True,
            context_menu_in_body=True,
            height=450
        ):
            # Колонки таблицы
            columns = [
                ("IP Address", "ip", 120),
                ("Hostname", "hostname", 150),
                ("Ports", "ports", 80),
                ("Services", "services", 100),
                ("OS", "os", 120),
                ("Status", "status", 100),
                ("Vulnerabilities", "vulnerabilities", 120),
                ("Last Seen", "last_seen", 120),
                ("Tags", "tags", 150),
                ("Actions", "actions", 100)
            ]
            
            for col_name, col_id, width in columns:
                with dpg.table_column(
                    label=col_name,
                    tag=f"col_{col_id}",
                    width_fixed=True,
                    width=width
                ):
                    # Добавляем обработчик сортировки для заголовков
                    if col_id not in ['actions']:
                        dpg.add_text(col_name)
            
            # Контекстное меню для таблицы
            with dpg.popup(dpg.last_item(), tag="table_context_menu", mousebutton=dpg.mvMouseButton_Right):
                dpg.add_menu_item(label="🔍 Scan Selected", callback=self._scan_selected_hosts)
                dpg.add_menu_item(label="🔎 Detect Services", callback=self._detect_selected_services)
                dpg.add_menu_item(label="🎯 Add to Scope", callback=self._add_selected_to_scope)
                dpg.add_separator()
                dpg.add_menu_item(label="💾 Export Selected", callback=self._export_selected_hosts)
                dpg.add_menu_item(label="📋 Copy IPs", callback=self._copy_selected_ips)
    
    def update_table(self, hosts: Dict):
        """Обновление таблицы хостов"""
        try:
            self.hosts_data = hosts
            self.filtered_hosts = hosts.copy()
            
            # Обновляем статистику
            total_hosts = len(hosts)
            dpg.set_value("table_stats", f"({total_hosts})")
            
            # Очищаем таблицу (кроме заголовков)
            if dpg.does_item_exist("hosts_table"):
                dpg.delete_item("hosts_table", children_only=True)
                self._create_hosts_table()
            
            # Заполняем таблицу данными
            self._populate_table()
            
            # Обновляем статус
            dpg.set_value("table_status", f"Showing {len(self.filtered_hosts)} of {total_hosts} hosts")
            
        except Exception as e:
            self.logger.error(f"Error updating table: {e}")
            dpg.set_value("table_status", f"Error: {e}")
    
    def _populate_table(self):
        """Заполнение таблицы данными"""
        for ip, host in self.filtered_hosts.items():
            with dpg.table_row(parent="hosts_table"):
                # IP Address (кликабельный)
                dpg.add_selectable(
                    label=ip,
                    callback=lambda s, d, ip=ip: self._on_host_select(ip)
                )
                
                # Hostname
                dpg.add_text(host.get('hostname', 'Unknown'))
                
                # Ports
                ports = host.get('ports', [])
                ports_text = f"{len(ports)}" if ports else "0"
                dpg.add_text(ports_text)
                
                # Services
                services = host.get('services', [])
                services_text = f"{len(services)}" if services else "0"
                dpg.add_text(services_text)
                
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
                dpg.add_text(last_seen)
                
                # Tags
                tags = host.get('tags', [])
                tags_text = ", ".join(tags[:3])  # Показываем первые 3 тега
                dpg.add_text(tags_text)
                
                # Actions
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="🔍",
                        callback=lambda s, d, ip=ip: self._show_host_details(ip)
                    )
                    dpg.add_button(
                        label="🎯",
                        callback=lambda s, d, ip=ip: self._add_host_to_scope(ip)
                    )
    
    def _get_status_color(self, status: str) -> List[int]:
        """Получение цвета для статуса"""
        colors = {
            'active': [72, 199, 116],
            'inactive': [255, 92, 87],
            'unknown': [255, 179, 64]
        }
        return colors.get(status, [150, 150, 160])
    
    def _on_host_select(self, ip: str):
        """Обработчик выбора хоста"""
        if self.on_host_select_callback:
            self.on_host_select_callback(ip)
    
    def _show_host_details(self, ip: str):
        """Показать детали хоста"""
        self.logger.info(f"Showing details for host: {ip}")
        if self.on_host_select_callback:
            self.on_host_select_callback(ip)
    
    def _add_host_to_scope(self, ip: str):
        """Добавить хост в scope"""
        self.logger.info(f"Adding host {ip} to scope")
    
    def _on_search(self, sender, app_data):
        """Обработчик поиска"""
        self._apply_filters()
    
    def _apply_filters(self):
        """Применение фильтров"""
        search_text = dpg.get_value("hosts_search").lower()
        status_filter = dpg.get_value("status_filter")
        vuln_filter = dpg.get_value("vuln_filter")
        
        self.filtered_hosts = {}
        
        for ip, host in self.hosts_data.items():
            # Поиск по IP и hostname
            matches_search = (
                search_text in ip.lower() or
                search_text in host.get('hostname', '').lower()
            )
            
            # Фильтр по статусу
            matches_status = (
                status_filter == "All" or
                host.get('status', 'unknown') == status_filter.lower()
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
    
    def _scan_selected_hosts(self):
        """Сканирование выбранных хостов"""
        self.logger.info("Scanning selected hosts")
    
    def _detect_selected_services(self):
        """Обнаружение сервисов выбранных хостов"""
        self.logger.info("Detecting services for selected hosts")
    
    def _add_selected_to_scope(self):
        """Добавление выбранных хостов в scope"""
        self.logger.info("Adding selected hosts to scope")
    
    def _export_selected_hosts(self):
        """Экспорт выбранных хостов"""
        self.logger.info("Exporting selected hosts")
    
    def _copy_selected_ips(self):
        """Копирование IP выбранных хостов"""
        self.logger.info("Copying selected IPs")
    
    def set_host_select_callback(self, callback: Callable):
        """Установка callback при выборе хоста"""
        self.on_host_select_callback = callback
    
    def clear(self):
        """Очистка таблицы"""
        self.hosts_data.clear()
        self.filtered_hosts.clear()
        if dpg.does_item_exist("hosts_table"):
            dpg.delete_item("hosts_table", children_only=True)
            self._create_hosts_table()
        dpg.set_value("table_status", "Table cleared")
