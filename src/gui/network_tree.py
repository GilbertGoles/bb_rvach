"""
Дерево сети в стиле Obsidian
"""
import dearpygui.dearpygui as dpg
from typing import Dict, Any, List, Optional, Callable
import logging
from datetime import datetime

class NetworkTree:
    """
    Древовидное представление сети в стиле Obsidian
    """
    
    def __init__(self):
        self.logger = logging.getLogger('RapidRecon.NetworkTree')
        self.nodes_data = {}
        self.hosts_data = {}
        self.selected_node = None
        self.on_node_select_callback = None
        
    def create_tree_panel(self, parent: str) -> str:
        """Создание панели дерева сети"""
        with dpg.child_window(parent=parent, border=False) as tree_panel:
            # Заголовок с статистикой
            with dpg.group(horizontal=True):
                dpg.add_text("🌐 Network Topology")
                dpg.add_text("(0)", tag="tree_stats", color=[150, 150, 160])
            
            # Поиск и фильтры
            with dpg.group(horizontal=True):
                dpg.add_input_text(
                    hint="Search nodes...",
                    width=-1,
                    callback=self._on_search
                )
            
            # Дерево сети
            with dpg.child_window(height=500, border=True):
                dpg.add_tree_node(
                    tag="network_tree_root",
                    label="Discovered Infrastructure (0)",
                    default_open=True,
                    indent=10
                )
            
            # Действия с деревом
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="🔄 Expand All",
                    width=120,
                    callback=self._expand_all
                )
                dpg.add_button(
                    label="📊 Statistics", 
                    width=120,
                    callback=self._show_statistics
                )
        
        return tree_panel
    
    def update_tree(self, nodes: Dict, hosts: Dict):
        """Обновление дерева на основе новых данных"""
        try:
            self.nodes_data = nodes
            self.hosts_data = hosts
            
            # Очищаем старое дерево
            if dpg.does_item_exist("network_tree_root"):
                dpg.delete_item("network_tree_root", children_only=True)
            
            # Обновляем статистику в заголовке
            total_nodes = len(nodes)
            dpg.set_value("tree_stats", f"({total_nodes})")
            dpg.configure_item("network_tree_root", label=f"Discovered Infrastructure ({total_nodes})")
            
            if not nodes:
                dpg.add_text("No nodes discovered yet...", parent="network_tree_root")
                return
            
            # Группируем узлы по типам
            nodes_by_type = self._group_nodes_by_type(nodes)
            
            # Создаем основные категории
            self._create_category("🎯 Initial Targets", nodes_by_type.get('initial_target', []), "targets")
            self._create_category("🌐 Subdomains", nodes_by_type.get('subdomain', []), "subdomains") 
            self._create_category("💻 Active Hosts", nodes_by_type.get('active_host', []), "hosts")
            self._create_category("🔓 Open Ports", nodes_by_type.get('open_ports', []), "ports")
            self._create_category("⚙️ Services", nodes_by_type.get('service', []), "services")
            self._create_category("🔴 Vulnerabilities", nodes_by_type.get('vulnerability', []), "vulns")
            self._create_category("💥 Exploitation", nodes_by_type.get('exploitation', []), "exploits")
            
            # Добавляем хосты из host manager
            if hosts:
                self._create_hosts_category(hosts)
                
        except Exception as e:
            self.logger.error(f"Error updating tree: {e}")
    
    def _group_nodes_by_type(self, nodes: Dict) -> Dict[str, List]:
        """Группировка узлов по типам"""
        grouped = {}
        for node_id, node in nodes.items():
            node_type = node.get('type', 'unknown')
            if node_type not in grouped:
                grouped[node_type] = []
            grouped[node_type].append(node)
        return grouped
    
    def _create_category(self, label: str, nodes: List, tag_suffix: str):
        """Создание категории узлов"""
        if not nodes:
            return
            
        with dpg.tree_node(
            label=f"{label} ({len(nodes)})", 
            parent="network_tree_root",
            tag=f"cat_{tag_suffix}"
        ):
            for node in nodes:
                self._create_node_item(node)
    
    def _create_hosts_category(self, hosts: Dict):
        """Создание категории хостов"""
        with dpg.tree_node(
            label=f"🏠 Hosts ({len(hosts)})",
            parent="network_tree_root", 
            tag="cat_hosts_manager"
        ):
            for ip, host in hosts.items():
                with dpg.tree_node(label=f"📡 {ip}"):
                    # Основная информация о хосте
                    dpg.add_text(f"Hostname: {host.get('hostname', 'Unknown')}")
                    dpg.add_text(f"Status: {host.get('status', 'unknown')}")
                    dpg.add_text(f"OS: {host.get('os', 'Unknown')}")
                    dpg.add_text(f"Last Seen: {host.get('last_seen', 'Unknown')}")
                    
                    # Порты
                    ports = host.get('ports', [])
                    if ports:
                        with dpg.tree_node(label=f"🔓 Ports ({len(ports)})"):
                            for port in ports:
                                dpg.add_text(f"Port {port}")
                    
                    # Сервисы
                    services = host.get('services', [])
                    if services:
                        with dpg.tree_node(label=f"⚙️ Services ({len(services)})"):
                            for service in services:
                                dpg.add_text(service)
                    
                    # Уязвимости
                    vulns = host.get('vulnerabilities', [])
                    if vulns:
                        with dpg.tree_node(label=f"🔴 Vulnerabilities ({len(vulns)})"):
                            for vuln in vulns:
                                dpg.add_text(vuln, color=[255, 100, 100])
                    
                    # Действия
                    with dpg.tree_node(label="🚀 Actions"):
                        dpg.add_button(
                            label="🔍 Scan Ports",
                            callback=lambda s, d, ip=ip: self._scan_host_ports(ip)
                        )
                        dpg.add_button(
                            label="🔎 Service Detection", 
                            callback=lambda s, d, ip=ip: self._detect_services(ip)
                        )
    
    def _create_node_item(self, node: Dict):
        """Создание элемента узла"""
        node_id = node.get('id', 'unknown')
        node_type = node.get('type', 'unknown')
        label = node.get('label', 'Unknown')
        
        # Иконки для разных типов узлов
        icons = {
            'initial_target': '🎯',
            'subdomain': '🌐', 
            'active_host': '💻',
            'open_ports': '🔓',
            'service': '⚙️',
            'vulnerability': '🔴',
            'exploitation': '💥'
        }
        
        icon = icons.get(node_type, '•')
        
        with dpg.tree_node(label=f"{icon} {label}", tag=f"node_{node_id}"):
            # Основная информация
            dpg.add_text(f"Type: {node_type}")
            dpg.add_text(f"ID: {node_id}")
            
            # Данные узла
            data = node.get('data', {})
            if isinstance(data, dict):
                for key, value in data.items():
                    if key not in ['position', 'color', 'radius', 'icon']:
                        dpg.add_text(f"{key}: {value}")
            else:
                dpg.add_text(f"Data: {data}")
            
            # Временные метки
            timestamp = node.get('timestamp')
            if timestamp:
                time_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
                dpg.add_text(f"Discovered: {time_str}")
            
            # Действия с узлом
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="🔍 Details",
                    callback=lambda s, d, nid=node_id: self._show_node_details(nid)
                )
                dpg.add_button(
                    label="🎯 Add to Scope",
                    callback=lambda s, d, nid=node_id: self._add_to_scope(nid)
                )
    
    def _show_node_details(self, node_id: str):
        """Показать детали узла"""
        if self.on_node_select_callback:
            self.on_node_select_callback(node_id)
    
    def _add_to_scope(self, node_id: str):
        """Добавить узел в scope"""
        self.logger.info(f"Adding node {node_id} to scope")
        # Здесь будет логика добавления в scope
    
    def _scan_host_ports(self, ip: str):
        """Сканирование портов хоста"""
        self.logger.info(f"Scanning ports for {ip}")
    
    def _detect_services(self, ip: str):
        """Обнаружение сервисов хоста"""
        self.logger.info(f"Detecting services for {ip}")
    
    def _on_search(self, sender, app_data):
        """Обработчик поиска"""
        search_text = app_data.lower()
        self._filter_tree(search_text)
    
    def _filter_tree(self, search_text: str):
        """Фильтрация дерева по тексту"""
        if not search_text:
            # Показываем все элементы
            for i in range(dpg.get_item_children("network_tree_root", 1)):
                child = dpg.get_item_children("network_tree_root", 1)[i]
                dpg.show_item(child)
            return
        
        # Скрываем/показываем элементы на основе поиска
        for i in range(dpg.get_item_children("network_tree_root", 1)):
            child = dpg.get_item_children("network_tree_root", 1)[i]
            child_label = dpg.get_item_label(child).lower()
            
            if search_text in child_label:
                dpg.show_item(child)
                # Раскрываем родительские элементы
                parent = dpg.get_item_parent(child)
                if dpg.does_item_exist(parent):
                    dpg.configure_item(parent, default_open=True)
            else:
                dpg.hide_item(child)
    
    def _expand_all(self):
        """Развернуть все узлы дерева"""
        def expand_recursive(item):
            dpg.configure_item(item, default_open=True)
            children = dpg.get_item_children(item, 1)
            for child in children:
                expand_recursive(child)
        
        expand_recursive("network_tree_root")
    
    def _show_statistics(self):
        """Показать статистику сети"""
        stats = self._calculate_statistics()
        
        # Создаем окно статистики
        if dpg.does_item_exist("stats_window"):
            dpg.delete_item("stats_window")
            
        with dpg.window(
            tag="stats_window",
            label="Network Statistics", 
            width=400,
            height=300,
            modal=True
        ):
            dpg.add_text("📊 Network Overview")
            dpg.add_separator()
            
            for category, count in stats.items():
                with dpg.group(horizontal=True):
                    dpg.add_text(f"{category}:", width=150)
                    dpg.add_text(str(count), color=[123, 97, 255])
    
    def _calculate_statistics(self) -> Dict[str, int]:
        """Расчет статистики сети"""
        stats = {
            "Total Nodes": len(self.nodes_data),
            "Initial Targets": len([n for n in self.nodes_data.values() if n.get('type') == 'initial_target']),
            "Subdomains": len([n for n in self.nodes_data.values() if n.get('type') == 'subdomain']),
            "Active Hosts": len([n for n in self.nodes_data.values() if n.get('type') == 'active_host']),
            "Open Ports": len([n for n in self.nodes_data.values() if n.get('type') == 'open_ports']),
            "Services": len([n for n in self.nodes_data.values() if n.get('type') == 'service']),
            "Vulnerabilities": len([n for n in self.nodes_data.values() if n.get('type') == 'vulnerability']),
            "Managed Hosts": len(self.hosts_data)
        }
        return stats
    
    def set_node_select_callback(self, callback: Callable):
        """Установка callback при выборе узла"""
        self.on_node_select_callback = callback
    
    def clear(self):
        """Очистка дерева"""
        self.nodes_data.clear()
        self.hosts_data.clear()
        if dpg.does_item_exist("network_tree_root"):
            dpg.delete_item("network_tree_root", children_only=True)
            dpg.add_text("No nodes discovered yet...", parent="network_tree_root")
