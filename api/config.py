
import yaml
from pathlib import Path

def save(new_config: dict) -> None:
    """ Updates a complete section!
    For example if {general:{ ... }} is given, 
    the complete general section is overwritten.
    """

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
        config = dict(yml)
        return config


def exists(config_path) -> bool:    
    config = load()
    levels = config_path.split(".")
    for level in levels:
        if not level in config:
            return False
        
        config = config[level]

    return True


def get(config_path, default=None):
    config = load()
    levels = config_path.split(".")
    for level in levels:
        if not level in config:
            return default
        
        config = config[level]

    return config


#
# HELPER
#
def _get_path():
    return Path.joinpath(Path.home(), ".remapy/config")
