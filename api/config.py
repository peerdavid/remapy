
import yaml
from pathlib import Path


def save(new_config: dict) -> None:
    path = _get_path()

    # Update keys and keep all old keys
    config = load()
    config.update(new_config)
    
    with open(path, 'w') as f:
        content = yaml.dump(config)
        f.write(content)
    
    return config


def load() -> dict:
    path = _get_path()
    if not Path.exists(path):
        return {}

    with open(path, "r") as f:
        content = f.read()
        yml = yaml.load(content, Loader=yaml.FullLoader)
        return dict(yml)


def exists(config_path) -> bool:    
    config = load()
    levels = config_path.split(".")
    for level in levels:
        if not level in config:
            return False
        
        config = config[level]

    return True


def get(config_path):
    config = load()
    levels = config_path.split(".")
    for level in levels:
        if not level in config:
            return None
        
        config = config[level]

    return config


#
# HELPER
#
def _get_path() -> Path:
    return Path.joinpath(Path.home(), ".remapy")
