import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

class ConfigManager:
    def __init__(self, config_file: Optional[str] = None):
        # Настройка логирования
        self.logger = self._setup_logging()
        
        # Основные конфиги
        if config_file:
            self.config_path = Path(config_file)
        else:
            self.config_path = Path("config.json")
        
        # Профили сканирования
        self.profiles_path = Path("configs/scan_profiles.json")
        self.active_profile = "normal"
        self.profiles = self.load_profiles()
        
        # Конфигурация модулей
        self.modules_config_path = Path("configs/modules_config.json")
        self.modules_config = self.load_modules_config()
        
        # Кэш для конфигов
        self._config_cache = None
        self._cache_timestamp = None
        self.cache_timeout = 30  # секунд
        
        self.logger.info(f"ConfigManager инициализирован, активный профиль: {self.active_profile}")

    def _setup_logging(self) -> logging.Logger:
        """Настройка логирования для ConfigManager"""
        logger = logging.getLogger('ConfigManager')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def load_config(self) -> Dict[str, Any]:
        """Загрузка основного конфига приложения с кэшированием"""
        # Проверка кэша
        current_time = datetime.now().timestamp()
        if (self._config_cache and self._cache_timestamp and 
            (current_time - self._cache_timestamp) < self.cache_timeout):
            return self._config_cache
        
        default_config = {
            "app": {
                "version": "1.0.0",
                "debug": True,
                "update_interval": 0.5,
                "max_workers": 10,
                "request_timeout": 10
            },
            "logging": {
                "level": "INFO",
                "file": "rapidrecon.log",
                "max_size_mb": 10,
                "backup_count": 5
            },
            "engine": {
                "max_depth": 5,
                "max_concurrent_tasks": 5,
                "rate_limit": 10,
                "timeout_multiplier": 1.5,
                "retry_attempts": 3
            },
            "modules": {
                "directory": "src/modules",
                "auto_discover": True,
                "auto_load": True,
                "builtin_modules": [
                    "ping_scanner",
                    "port_scanner", 
                    "service_detector",
                    "subdomain_scanner",
                    "vulnerability_scanner",
                    "exploitation"
                ]
            },
            "security": {
                "user_agent": "RapidRecon/1.0",
                "follow_redirects": True,
                "max_redirects": 5,
                "verify_ssl": False
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Мердж с дефолтными значениями
                merged_config = self._deep_merge(default_config, loaded_config)
                self._config_cache = merged_config
                self._cache_timestamp = datetime.now().timestamp()
                
                self.logger.info(f"Конфиг загружен из {self.config_path}")
                return merged_config
                
            except Exception as e:
                self.logger.error(f"Ошибка загрузки конфига {self.config_path}: {e}")
        
        # Создаем дефолтный конфиг если файла нет
        self.save_config(default_config)
        self._config_cache = default_config
        self._cache_timestamp = datetime.now().timestamp()
        
        return default_config

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Рекурсивное слияние словарей"""
        result = base.copy()
        
        for key, value in update.items():
            if (key in result and isinstance(result[key], dict) 
                and isinstance(value, dict)):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
                
        return result

    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """Сохранение основного конфига"""
        try:
            if config is None:
                config = self.load_config()
            
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Обновляем кэш
            self._config_cache = config
            self._cache_timestamp = datetime.now().timestamp()
            
            self.logger.info(f"Конфиг сохранен в {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения конфига: {e}")
            return False

    def load_profiles(self) -> Dict[str, Any]:
        """Загрузка профилей сканирования"""
        default_profiles = {
            "stealth": {
                "rate_limit": 2,
                "timeout": 3.0,
                "max_depth": 3,
                "modules": ["ping_scanner", "port_scanner"],
                "ports": [80, 443],
                "skip_aggressive": True,
                "description": "Стелс-сканирование для минимальной заметности"
            },
            "normal": {
                "rate_limit": 10,
                "timeout": 2.0,
                "max_depth": 5,
                "modules": ["ping_scanner", "port_scanner", "service_detector"],
                "ports": [21, 22, 23, 25, 53, 80, 110, 443, 993, 995, 8080],
                "skip_aggressive": False,
                "description": "Стандартное сбалансированное сканирование"
            },
            "aggressive": {
                "rate_limit": 50,
                "timeout": 1.0,
                "max_depth": 8,
                "modules": ["ping_scanner", "port_scanner", "service_detector", "subdomain_scanner"],
                "ports": "full",
                "skip_aggressive": False,
                "description": "Агрессивное сканирование с максимальным охватом"
            },
            "web_only": {
                "rate_limit": 5,
                "timeout": 2.0,
                "max_depth": 3,
                "modules": ["port_scanner", "service_detector"],
                "ports": [80, 443, 8080, 8443],
                "skip_aggressive": True,
                "description": "Сканирование только веб-сервисов"
            }
        }
        
        if self.profiles_path.exists():
            try:
                with open(self.profiles_path, 'r', encoding='utf-8') as f:
                    loaded_profiles = json.load(f)
                
                # Объединяем с дефолтными профилями
                merged_profiles = default_profiles.copy()
                merged_profiles.update(loaded_profiles)
                
                self.logger.info(f"Профили загружены из {self.profiles_path}")
                return merged_profiles
                
            except Exception as e:
                self.logger.error(f"Ошибка загрузки профилей {self.profiles_path}: {e}")
        
        # Создаем дефолтные профили если файла нет
        self.save_profiles(default_profiles)
        return default_profiles

    def save_profiles(self, profiles: Dict[str, Any] = None) -> bool:
        """Сохранение профилей сканирования"""
        try:
            if profiles is None:
                profiles = self.profiles
            
            self.profiles_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.profiles_path, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Профили сохранены в {self.profiles_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения профилей: {e}")
            return False

    def load_modules_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации модулей"""
        default_modules_config = {
            "ping_scanner": {
                "rate_limit": 10,
                "timeout": 2.0,
                "enabled": True,
                "packet_count": 2,
                "use_icmp": True
            },
            "port_scanner": {
                "rate_limit": 10,
                "timeout": 1.0,
                "ports": [21, 22, 80, 443, 8080],
                "enabled": True,
                "scan_method": "syn",  # syn, connect, udp
                "max_port_workers": 50
            },
            "service_detector": {
                "rate_limit": 5,
                "timeout": 3.0,
                "enabled": True,
                "banner_grab": True,
                "service_timeout": 5.0
            },
            "subdomain_scanner": {
                "rate_limit": 3,
                "wordlist": "common_subdomains.txt",
                "enabled": True,
                "use_brute_force": False,
                "recursive": False
            },
            "vulnerability_scanner": {
                "rate_limit": 2,
                "check_cves": True,
                "enabled": True,
                "cve_db_path": "data/cve_db.json",
                "scan_level": "normal"  # light, normal, full
            },
            "exploitation": {
                "rate_limit": 1,
                "enabled": True,
                "auto_exploit": False,
                "exploit_db_path": "data/exploits",
                "safe_mode": True
            }
        }
        
        if self.modules_config_path.exists():
            try:
                with open(self.modules_config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Мердж с дефолтными значениями
                merged_config = self._deep_merge(default_modules_config, loaded_config)
                self.logger.info(f"Конфиг модулей загружен из {self.modules_config_path}")
                return merged_config
                
            except Exception as e:
                self.logger.error(f"Ошибка загрузки конфига модулей {self.modules_config_path}: {e}")
        
        # Создаем дефолтную конфигурацию модулей если файла нет
        self.save_module_configs(default_modules_config)
        return default_modules_config

    def save_module_configs(self, modules_config: Dict[str, Any] = None) -> bool:
        """Сохранение конфигурации модулей"""
        try:
            if modules_config is None:
                modules_config = self.modules_config
            
            self.modules_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.modules_config_path, 'w', encoding='utf-8') as f:
                json.dump(modules_config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Конфиг модулей сохранен в {self.modules_config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка сохранения конфига модулей: {e}")
            return False

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Получить конфигурацию для конкретного модуля"""
        config = self.modules_config.get(module_name, {})
        # Добавляем общие настройки из активного профиля
        profile_config = self.get_active_config()
        config.update({
            'rate_limit': profile_config.get('rate_limit', 10),
            'timeout': profile_config.get('timeout', 2.0)
        })
        return config

    def update_module_config(self, module_name: str, config: Dict[str, Any]) -> bool:
        """Обновить конфигурацию модуля"""
        self.modules_config[module_name] = config
        return self.save_module_configs()

    def get_active_config(self) -> Dict[str, Any]:
        """Получить активную конфигурацию профиля"""
        return self.profiles.get(self.active_profile, self.profiles["normal"])

    def set_profile(self, profile_name: str) -> bool:
        """Установить активный профиль"""
        if profile_name in self.profiles:
            old_profile = self.active_profile
            self.active_profile = profile_name
            self.logger.info(f"Профиль изменен: {old_profile} -> {profile_name}")
            return True
        
        self.logger.warning(f"Попытка установить несуществующий профиль: {profile_name}")
        return False

    def get_available_profiles(self) -> List[str]:
        """Получить список доступных профилей"""
        return list(self.profiles.keys())

    def get_profile_info(self, profile_name: str) -> Dict[str, Any]:
        """Получить информацию о профиле"""
        profile = self.profiles.get(profile_name, {})
        return {
            "name": profile_name,
            "description": profile.get("description", "Нет описания"),
            "modules": profile.get("modules", []),
            "rate_limit": profile.get("rate_limit", 10),
            "max_depth": profile.get("max_depth", 5)
        }

    def create_custom_profile(self, profile_name: str, config: Dict[str, Any]) -> bool:
        """Создать кастомный профиль"""
        if profile_name in self.profiles:
            self.logger.warning(f"Профиль {profile_name} уже существует")
            return False
        
        self.profiles[profile_name] = config
        return self.save_profiles()

    def delete_profile(self, profile_name: str) -> bool:
        """Удалить профиль"""
        if profile_name in ["stealth", "normal", "aggressive"]:
            self.logger.warning(f"Нельзя удалить системный профиль: {profile_name}")
            return False
        
        if profile_name in self.profiles:
            del self.profiles[profile_name]
            
            # Если удаляемый профиль был активным, переключаемся на normal
            if self.active_profile == profile_name:
                self.active_profile = "normal"
                self.logger.info(f"Активный профиль переключен на 'normal'")
                
            return self.save_profiles()
        
        return False

    def get_engine_config(self) -> Dict[str, Any]:
        """Получить конфигурацию движка"""
        config = self.load_config()
        return config.get('engine', {})

    def get_app_config(self) -> Dict[str, Any]:
        """Получить конфигурацию приложения"""
        config = self.load_config()
        return config.get('app', {})

    def get_modules_config(self) -> Dict[str, Any]:
        """Получить общую конфигурацию модулей"""
        config = self.load_config()
        return config.get('modules', {})

    def get_security_config(self) -> Dict[str, Any]:
        """Получить конфигурацию безопасности"""
        config = self.load_config()
        return config.get('security', {})

    def validate_config(self) -> Dict[str, List[str]]:
        """Валидация всех конфигов"""
        errors = {}
        
        # Валидация основного конфига
        app_config = self.get_app_config()
        if app_config.get('max_workers', 0) <= 0:
            errors.setdefault('app', []).append("max_workers должен быть положительным числом")
        
        # Валидация профилей
        for profile_name, profile in self.profiles.items():
            if profile.get('rate_limit', 0) < 0:
                errors.setdefault(f'profile_{profile_name}', []).append(
                    "rate_limit не может быть отрицательным"
                )
        
        # Валидация конфигов модулей
        for module_name, module_config in self.modules_config.items():
            if not module_config.get('enabled', True):
                continue
                
            if module_config.get('rate_limit', 0) < 0:
                errors.setdefault(f'module_{module_name}', []).append(
                    "rate_limit не может быть отрицательным"
                )
        
        if not errors:
            self.logger.info("Валидация конфигов прошла успешно")
        else:
            self.logger.warning(f"Найдены ошибки в конфигах: {errors}")
            
        return errors

    def reset_to_defaults(self, config_type: str = "all") -> bool:
        """Сброс конфигов к значениям по умолчанию"""
        try:
            if config_type in ["all", "main"]:
                default_config = self.load_config()  # Это создаст дефолтный конфиг
                self.save_config(default_config)
            
            if config_type in ["all", "profiles"]:
                default_profiles = self.load_profiles()  # Это создаст дефолтные профили
                self.save_profiles(default_profiles)
                self.profiles = default_profiles
            
            if config_type in ["all", "modules"]:
                default_modules = self.load_modules_config()  # Это создаст дефолтные модули
                self.save_module_configs(default_modules)
                self.modules_config = default_modules
            
            self.logger.info(f"Конфиги сброшены к значениям по умолчанию: {config_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка сброса конфигов: {e}")
            return False

    def export_config(self, export_path: str) -> bool:
        """Экспорт всех конфигов в указанную директорию"""
        try:
            export_dir = Path(export_path)
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Экспорт основного конфига
            main_config = self.load_config()
            with open(export_dir / "config.json", 'w', encoding='utf-8') as f:
                json.dump(main_config, f, indent=2, ensure_ascii=False)
            
            # Экспорт профилей
            with open(export_dir / "scan_profiles.json", 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, indent=2, ensure_ascii=False)
            
            # Экспорт конфигов модулей
            with open(export_dir / "modules_config.json", 'w', encoding='utf-8') as f:
                json.dump(self.modules_config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Конфиги экспортированы в {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Ошибка экспорта конфигов: {e}")
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """Получить сводку по всем конфигам"""
        active_profile = self.get_active_config()
        
        return {
            "active_profile": self.active_profile,
            "available_profiles": self.get_available_profiles(),
            "active_modules": active_profile.get("modules", []),
            "engine_settings": self.get_engine_config(),
            "app_settings": {
                "debug": self.get_app_config().get("debug", False),
                "max_workers": self.get_app_config().get("max_workers", 10)
            },
            "enabled_modules": [
                name for name, config in self.modules_config.items() 
                if config.get("enabled", True)
            ]
        }
