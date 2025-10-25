"""
Главный файл RapidRecon
"""
import asyncio
import threading
from core.engine import PropagationEngine
from gui.main_window import MainWindow

class RapidRecon:
    def __init__(self):
        self.engine = PropagationEngine()
        self.gui = MainWindow(self.engine)
    
    def run(self):
        """Запуск приложения"""
        print("🚀 RapidRecon запускается...")
        
        # В будущем здесь будет асинхронный запуск движка
        # Пока просто запускаем GUI
        self.gui.show()

if __name__ == "__main__":
    app = RapidRecon()
    app.run()
