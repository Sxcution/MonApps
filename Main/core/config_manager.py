import os
import json

class ConfigManager:
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

    @staticmethod
    def load():
        if os.path.exists(ConfigManager.CONFIG_FILE):
            try:
                with open(ConfigManager.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "dark_mode": True, 
            "startup": False,
            "external_autokey": True,
            "external_android": True
        }

    @staticmethod
    def save(config):
        try:
            with open(ConfigManager.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
