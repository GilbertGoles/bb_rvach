"""
Главное окно RapidRecon на Dear PyGui
"""
import dearpygui.dearpygui as dpg
from typing import Callable

class MainWindow:
    def __init__(self, engine):
        self.engine = engine
        self.setup_gui()
    
    def setup_gui(self):
        """Настройка основного интерфейса"""
        dpg.create_context()
        
        with dpg.window(tag="Primary Window"):
            # Панель управления
            with dpg.group(horizontal=True):
                dpg.add_input_text(tag="target_input", hint="Введите домен или IP")
                dpg.add_button(label="Сканировать", callback=self.start_scan)
                dpg.add_button(label="Стоп", callback=self.stop_scan)
            
            # Настройки скорости
            with dpg.collapsing_header(label="Настройки скорости"):
                dpg.add_slider_int(
                    label="Пакетов/секунду",
                    default_value=10, min_value=1, max_value=100,
                    tag="rate_limit"
                )
                dpg.add_combo(
                    label="Профиль",
                    items=["Стелс", "Нормальный", "Агрессивный", "Безумный"],
                    default_value="Нормальный",
                    tag="speed_profile"
                )
            
            # Область вывода результатов
            with dpg.child_window(height=300):
                dpg.add_text("Результаты сканирования:")
                dpg.add_text("", tag="results_output")
    
    def start_scan(self):
        """Запуск сканирования"""
        target = dpg.get_value("target_input")
        if target:
            self.engine.add_initial_target(target)
            dpg.set_value("results_output", f"Начато сканирование: {target}")
    
    def stop_scan(self):
        """Остановка сканирования"""
        dpg.set_value("results_output", "Сканирование остановлено")
    
    def show(self):
        """Показать окно"""
        dpg.create_viewport(title='RapidRecon', width=1200, height=800)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("Primary Window", True)
        dpg.start_dearpygui()
    
    def destroy(self):
        """Очистка"""
        dpg.destroy_context()
