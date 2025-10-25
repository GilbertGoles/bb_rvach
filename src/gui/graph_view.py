import dearpygui.dearpygui as dpg
from typing import Dict, List, Any

class GraphView:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.node_positions = {}
        self.next_node_id = 1
    
    def setup_graph_tab(self):
        """Настройка вкладки с графом"""
        with dpg.tab(label="Карта сети"):
            with dpg.group(horizontal=True):
                dpg.add_button(label="Обновить граф", callback=self.update_graph)
                dpg.add_button(label="Очистить", callback=self.clear_graph)
            
            # Область для графа
            with dpg.child_window(height=500, tag="graph_area"):
                dpg.add_text("Граф сети будет отображаться здесь")
                # Здесь будет интерактивный граф
    
    def add_node(self, node_data: Dict[str, Any]):
        """Добавить узел в граф"""
        node_id = self.next_node_id
        self.next_node_id += 1
        
        node_type = node_data.get('type', 'unknown')
        node_label = node_data.get('data', 'Unknown')
        
        self.nodes[node_id] = {
            'id': node_id,
            'type': node_type,
            'label': node_label,
            'data': node_data,
            'color': self.get_node_color(node_type)
        }
        
        return node_id
    
    def add_edge(self, source_id: int, target_id: int):
        """Добавить связь между узлами"""
        self.edges.append({
            'source': source_id,
            'target': target_id
        })
    
    def get_node_color(self, node_type: str) -> List[float]:
        """Цвет узла в зависимости от типа"""
        colors = {
            'initial_target': [0, 255, 0],      # Зеленый
            'subdomain': [100, 149, 237],       # Синий
            'active_host': [255, 165, 0],       # Оранжевый  
            'open_ports': [255, 255, 0],        # Желтый
            'services': [148, 0, 211],          # Фиолетовый
            'vulnerability': [255, 0, 0]        # Красный
        }
        return colors.get(node_type, [128, 128, 128])  # Серый по умолчанию
    
    def update_graph(self):
        """Обновить отображение графа"""
        self.clear_graph_display()
        self.render_graph()
    
    def clear_graph_display(self):
        """Очистить отображение графа"""
        dpg.delete_item("graph_area", children_only=True)
    
    def render_graph(self):
        """Отрисовать граф в GUI"""
        if not self.nodes:
            dpg.add_text("Нет данных для отображения", parent="graph_area")
            return
        
        # Простая визуализация в виде списка с отступами
        for node_id, node in self.nodes.items():
            depth = node['data'].get('depth', 0)
            indent = "  " * depth
            
            with dpg.group(horizontal=True, parent="graph_area"):
                dpg.add_text(f"{indent}• ", color=node['color'])
                dpg.add_text(f"{node['type']}: {node['label']}")
                
                # Показываем связи
                connections = [e for e in self.edges if e['source'] == node_id]
                if connections:
                    dpg.add_text(f" → {len(connections)} связей")
    
    def clear_graph(self):
        """Полностью очистить граф"""
        self.nodes.clear()
        self.edges.clear()
        self.node_positions.clear()
        self.next_node_id = 1
        self.clear_graph_display()
