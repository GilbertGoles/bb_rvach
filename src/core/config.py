import json
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    def __init__(self):
        self.config_path = Path("configs/scan_profiles.json")
        self.active_profile = "normal"
        self.profiles = self.load_profiles()
    
    def load_profiles(self) -> Dict[str, Any]:
        """Загрузка профилей сканирования"""
        default_profiles = {
            "stealth": {
                "rate_limit": 2,
                "timeout": 3.0,
                "max_depth": 3,
                "modules": ["ping_scanner", "port_scanner"],
                "ports": [80, 443],
                "skip_aggressive": True
            },
            "normal": {
                "rate_limit": 10,
                "timeout": 2.0,
                "max_depth": 5,
                "modules": ["ping_scanner", "port_scanner", "service_detector"],
                "ports": [21, 22, 23, 25, 53, 80, 110, 443, 993, 995, 8080],
                "skip_aggressive": False
            },
            "aggressive": {
                "rate_limit": 50,
                "timeout": 1.0,
                "max_depth": 8,
                "modules": ["ping_scanner", "port_scanner", "service_detector"],
                "ports": "full",  # Все порты из модуля
                "skip_aggressive": False
            }
        }
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return default_profiles
    
    def get_active_config(self) -> Dict[str, Any]:
        """Получить активную конфигурацию"""
        return self.profiles.get(self.active_profile, self.profiles["normal"])
    
    def set_profile(self, profile_name: str):
        """Установить активный профиль"""
        if profile_name in self.profiles:
            self.active_profile = profile_name
            return True
        return False
