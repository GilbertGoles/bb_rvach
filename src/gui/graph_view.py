import dearpygui.dearpygui as dpg
from typing import Dict, List, Any, Optional
import math
import random

class GraphView:
    """
    Компонент для визуализации графа сети в RapidRecon
    Поддерживает интерактивное отображение узлов и связей
    """
    
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.node_positions = {}
        self.next_node_id = 1
        self.selected_node = None
        self.graph_scale = 1.0
        self.graph_offset = [0, 0]
        self.is_dragging = False
        self.drag_start_pos = [0, 0]
        
        # Настройка цветовой схемы
        self.setup_colors()
    
    def setup_colors(self):
        """Настройка цветовой схемы графа"""
        self.colors = {
            'background': [40, 40, 40],
            'grid': [60, 60, 60],
            'text': [220, 220, 220],
            'node_default': [128, 128, 128],
            
            # Цвета узлов по типам
            'initial_target': [0, 200, 0],        # Зеленый
            'subdomain': [100, 149, 237],         # Синий
            'ip_address': [200, 200, 100],        # Светло-желтый
            'active_host': [255, 165, 0],         # Оранжевый  
            'open_ports': [255, 255, 0],          # Желтый
            'service': [148, 0, 211],             # Фиолетовый
            'vulnerability_scan': [255, 100, 100], # Светло-красный
            'domain_scan': [100, 200, 255],       # Голубой
            'custom': [169, 169, 169]             # Темно-серый
        }
        
        # Цвета уязвимостей по severity
        self.vulnerability_colors = {
            'critical': [255, 0, 0],              # Красный
            'high': [255, 69, 0],                 # Оранжево-красный
            'medium': [255, 165, 0],              # Оранжевый
            'low': [255, 255, 0],                 # Желтый
            'info': [100, 149, 237],              # Синий
            'unknown': [255, 192, 203]            # Розовый
        }
    
    def setup_graph_tab(self):
        """Настройка вкладки с графом"""
        with dpg.tab(label="🌐 Карта сети"):
            # Панель управления графом
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="🔄 Обновить граф", 
                    callback=self.update_graph,
                    width=120
                )
                dpg.add_button(
                    label="🧹 Очистить", 
                    callback=self.clear_graph,
                    width=100
                )
                dpg.add_button(
                    label="💾 Экспорт", 
                    callback=self.export_graph,
                    width=100
                )
                dpg.add_spacer(width=20)
                dpg.add_text("Масштаб:")
                dpg.add_slider_float(
                    default_value=1.0,
                    min_value=0.1,
                    max_value=3.0,
                    callback=self.on_scale_change,
                    tag="graph_scale_slider",
                    width=100
                )
            
            # Информация о выбранном узле
            with dpg.collapsing_header(label="📋 Информация о узле", default_open=True):
                dpg.add_text("Выберите узел для просмотра деталей", tag="node_info")
            
            # Область для графа с возможностью панорамирования и масштабирования
            with dpg.child_window(
                height=500, 
                tag="graph_area",
                border=False
            ):
                # Холст для рисования графа
                with dpg.drawlist(
                    width=-1,
                    height=500,
                    tag="graph_canvas"
                ):
                    # Фон будет рисоваться динамически
                    pass
                
                # Обработчики событий для интерактивности
                with dpg.handler_registry():
                    dpg.add_mouse_click_handler(callback=self.on_canvas_click)
                    dpg.add_mouse_drag_handler(callback=self.on_canvas_drag)
                    dpg.add_mouse_wheel_handler(callback=self.on_canvas_scroll)
    
    def add_node(self, node_data: Dict[str, Any]) -> int:
        """Добавить узел в граф"""
        node_id = self.next_node_id
        self.next_node_id += 1
        
        node_type = node_data.get('type', 'unknown')
        node_label = node_data.get('data', 'Unknown')
        
        # Определяем цвет узла
        node_color = self.get_node_color(node_type, node_data)
        
        self.nodes[node_id] = {
            'id': node_id,
            'type': node_type,
            'label': node_label,
            'data': node_data,
            'color': node_color,
            'size': self.get_node_size(node_type),
            'position': self.generate_node_position(node_id)
        }
        
        return node_id
    
    def get_node_color(self, node_type: str, node_data: Dict[str, Any]) -> List[float]:
        """Цвет узла в зависимости от типа и дополнительных атрибутов"""
        
        # Специальная обработка для уязвимостей
        if node_type == 'vulnerability':
            severity = node_data.get('metadata', {}).get('severity', 'unknown')
            return self.get_vulnerability_color(severity)
        
        # Обычные узлы
        return self.colors.get(node_type, self.colors['node_default'])
    
    def get_vulnerability_color(self, severity: str) -> List[float]:
        """Цвет для уязвимости по severity"""
        return self.vulnerability_colors.get(severity.lower(), self.vulnerability_colors['unknown'])
    
    def get_node_size(self, node_type: str) -> float:
        """Размер узла в зависимости от типа"""
        sizes = {
            'initial_target': 25.0,
            'vulnerability': 20.0,
            'service': 18.0,
            'active_host': 22.0,
            'subdomain': 20.0,
            'open_ports': 19.0,
            'default': 20.0
        }
        return sizes.get(node_type, sizes['default'])
    
    def generate_node_position(self, node_id: int) -> List[float]:
        """Генерация позиции для нового узла"""
        if not self.nodes:
            # Первый узел в центре
            return [400, 250]
        
        # Распределяем узлы по кругу
        total_nodes = len(self.nodes)
        angle = (node_id * 2 * math.pi / max(total_nodes, 1)) + random.uniform(-0.1, 0.1)
        radius = 150 + (total_nodes * 5)  # Увеличиваем радиус с ростом количества узлов
        
        center_x, center_y = 400, 250
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        return [x, y]
    
    def add_edge(self, source_id: int, target_id: int):
        """Добавить связь между узлами"""
        if source_id in self.nodes and target_id in self.nodes:
            self.edges.append({
                'source': source_id,
                'target': target_id,
                'color': [150, 150, 150, 100]  # Полупрозрачный серый
            })
    
    def update_graph(self):
        """Обновить отображение графа"""
        self.render_graph()
    
    def render_graph(self):
        """Отрисовать граф на canvas"""
        dpg.delete_item("graph_canvas", children_only=True)
        
        # Рисуем фон
        self.draw_background()
        
        # Рисуем связи
        self.draw_edges()
        
        # Рисуем узлы
        self.draw_nodes()
        
        # Рисуем информацию о выбранном узле
        self.update_node_info()
    
    def draw_background(self):
        """Рисуем фон с сеткой"""
        canvas_width = dpg.get_item_width("graph_canvas")
        canvas_height = dpg.get_item_height("graph_canvas")
        
        # Фон
        dpg.draw_rectangle(
            [0, 0],
            [canvas_width, canvas_height],
            fill=self.colors['background'],
            parent="graph_canvas"
        )
        
        # Сетка (упрощенная)
        grid_size = 50 * self.graph_scale
        for x in range(0, canvas_width, int(grid_size)):
            dpg.draw_line(
                [x, 0],
                [x, canvas_height],
                color=self.colors['grid'],
                thickness=1,
                parent="graph_canvas"
            )
        
        for y in range(0, canvas_height, int(grid_size)):
            dpg.draw_line(
                [0, y],
                [canvas_width, y],
                color=self.colors['grid'],
                thickness=1,
                parent="graph_canvas"
            )
    
    def draw_edges(self):
        """Рисуем связи между узлами"""
        for edge in self.edges:
            source_node = self.nodes.get(edge['source'])
            target_node = self.nodes.get(edge['target'])
            
            if source_node and target_node:
                source_pos = self.apply_transform(source_node['position'])
                target_pos = self.apply_transform(target_node['position'])
                
                dpg.draw_line(
                    source_pos,
                    target_pos,
                    color=edge['color'],
                    thickness=2 * self.graph_scale,
                    parent="graph_canvas"
                )
    
    def draw_nodes(self):
        """Рисуем узлы графа"""
        for node_id, node in self.nodes.items():
            position = self.apply_transform(node['position'])
            size = node['size'] * self.graph_scale
            color = node['color']
            
            # Рисуем круг узла
            dpg.draw_circle(
                position,
                size,
                fill=color,
                color=[255, 255, 255, 100],
                thickness=2,
                parent="graph_canvas"
            )
            
            # Рисуем текст метки (упрощенный)
            if self.graph_scale > 0.5:  # Показываем текст только при достаточном масштабе
                label = self.get_node_label(node)
                dpg.draw_text(
                    [position[0] - len(label) * 3, position[1] + size + 5],
                    label,
                    color=self.colors['text'],
                    size=12 * self.graph_scale,
                    parent="graph_canvas"
                )
            
            # Выделение выбранного узла
            if node_id == self.selected_node:
                dpg.draw_circle(
                    position,
                    size + 3,
                    color=[255, 255, 0, 200],
                    thickness=3,
                    parent="graph_canvas"
                )
    
    def get_node_label(self, node: Dict) -> str:
        """Получить метку для узла"""
        node_type = node['type']
        label = node['label']
        
        # Сокращаем длинные метки
        if len(label) > 20:
            label = label[:17] + "..."
        
        # Добавляем иконки для типов узлов
        icons = {
            'initial_target': '🎯',
            'subdomain': '🌐',
            'active_host': '💻',
            'open_ports': '🔓',
            'service': '⚙️',
            'vulnerability': '🔴',
            'vulnerability_scan': '🔍'
        }
        
        icon = icons.get(node_type, '●')
        return f"{icon} {label}"
    
    def apply_transform(self, position: List[float]) -> List[float]:
        """Применить трансформации (масштаб и смещение) к позиции"""
        x = (position[0] + self.graph_offset[0]) * self.graph_scale
        y = (position[1] + self.graph_offset[1]) * self.graph_scale
        return [x, y]
    
    def on_scale_change(self):
        """Обработчик изменения масштаба"""
        self.graph_scale = dpg.get_value("graph_scale_slider")
        self.render_graph()
    
    def on_canvas_click(self):
        """Обработчик клика по canvas"""
        if dpg.is_mouse_button_double_clicked(dpg.mvMouseButton_Left):
            # Сброс масштаба и позиции при двойном клике
            self.graph_scale = 1.0
            self.graph_offset = [0, 0]
            dpg.set_value("graph_scale_slider", 1.0)
            self.render_graph()
    
    def on_canvas_drag(self):
        """Обработчик перетаскивания canvas"""
        if dpg.is_mouse_button_dragging(dpg.mvMouseButton_Left):
            drag_delta = dpg.get_mouse_drag_delta()
            self.graph_offset[0] += drag_delta[0] / self.graph_scale
            self.graph_offset[1] += drag_delta[1] / self.graph_scale
            dpg.reset_mouse_drag_delta()
            self.render_graph()
    
    def on_canvas_scroll(self):
        """Обработчик прокрутки колесика мыши"""
        scroll = dpg.get_mouse_wheel()
        new_scale = self.graph_scale * (1.0 + scroll * 0.1)
        new_scale = max(0.1, min(3.0, new_scale))
        
        self.graph_scale = new_scale
        dpg.set_value("graph_scale_slider", new_scale)
        self.render_graph()
    
    def update_node_info(self):
        """Обновить информацию о выбранном узле"""
        if self.selected_node and self.selected_node in self.nodes:
            node = self.nodes[self.selected_node]
            info_text = self.format_node_info(node)
            dpg.set_value("node_info", info_text)
        else:
            dpg.set_value("node_info", "Выберите узел для просмотра деталей")
    
    def format_node_info(self, node: Dict) -> str:
        """Форматировать информацию о узле"""
        info = f"""
Тип: {node['type']}
Данные: {node['label']}
Глубина: {node['data'].get('depth', 'N/A')}
Модуль: {node['data'].get('module', 'N/A')}
        """
        
        # Дополнительная информация в зависимости от типа
        metadata = node['data'].get('metadata', {})
        if metadata:
            info += "\nМетаданные:"
            for key, value in metadata.items():
                info += f"\n  {key}: {value}"
        
        if node['data'].get('ports'):
            info += f"\nПорты: {node['data']['ports']}"
        
        if node['data'].get('services'):
            info += f"\nСервисы: {len(node['data']['services'])}"
        
        if node['type'] == 'vulnerability':
            vuln_data = node['data'].get('vulnerability_data', {})
            info += f"\nУязвимость: {vuln_data.get('severity', 'unknown').upper()}"
            info += f"\nCVE: {vuln_data.get('cve', 'N/A')}"
            info += f"\nОписание: {vuln_data.get('description', 'N/A')}"
        
        return info
    
    def clear_graph_display(self):
        """Очистить отображение графа"""
        dpg.delete_item("graph_canvas", children_only=True)
    
    def clear_graph(self):
        """Полностью очистить граф"""
        self.nodes.clear()
        self.edges.clear()
        self.node_positions.clear()
        self.next_node_id = 1
        self.selected_node = None
        self.graph_scale = 1.0
        self.graph_offset = [0, 0]
        dpg.set_value("graph_scale_slider", 1.0)
        self.clear_graph_display()
        self.update_node_info()
    
    def export_graph(self):
        """Экспорт графа в файл"""
        import json
        from datetime import datetime
        
        graph_data = {
            'export_time': datetime.now().isoformat(),
            'nodes': list(self.nodes.values()),
            'edges': self.edges,
            'metadata': {
                'total_nodes': len(self.nodes),
                'total_edges': len(self.edges)
            }
        }
        
        filename = f"rapidrecon_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        
        return filename

# Пример использования
if __name__ == "__main__":
    dpg.create_context()
    
    with dpg.window(label="Graph Test", width=800, height=600):
        graph = GraphView()
        graph.setup_graph_tab()
        
        # Тестовые данные
        test_nodes = [
            {'type': 'initial_target', 'data': 'example.com', 'depth': 0},
            {'type': 'subdomain', 'data': 'api.example.com', 'depth': 1},
            {'type': 'active_host', 'data': '192.168.1.1', 'depth': 2},
            {'type': 'open_ports', 'data': '192.168.1.1', 'depth': 3, 'ports': [80, 443]},
            {'type': 'service', 'data': 'HTTP Service', 'depth': 4},
            {'type': 'vulnerability', 'data': 'CVE-2023-1234', 'depth': 5, 
             'metadata': {'severity': 'high'}}
        ]
        
        # Добавляем узлы и связи
        node_ids = []
        for node_data in test_nodes:
            node_id = graph.add_node(node_data)
            node_ids.append(node_id)
        
        for i in range(len(node_ids) - 1):
            graph.add_edge(node_ids[i], node_ids[i + 1])
        
        graph.render_graph()
    
    dpg.create_viewport(width=800, height=600, title="Graph View Test")
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
