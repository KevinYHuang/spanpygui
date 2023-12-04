import toml
import os

_config_path = os.path.join(os.path.dirname(__file__), '../config.toml')
    
def reload(path=None):
    # To use in an interractive environment to relead config object when file is changed.
    global _CONFIG, _config_path
    _config_path = path if path else _config_path
    _CONFIG = toml.load(_config_path)

    def convert_to_absolute_paths(data):
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = convert_to_absolute_paths(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                data[i] = convert_to_absolute_paths(item)
        elif isinstance(data, str):
            if os.path.isabs(data):
                return data
            else:
                return os.path.join(os.path.dirname(_config_path), data)
        return data

    if 'files' in _CONFIG:
        convert_to_absolute_paths(_CONFIG['files'])



def config(*keys, **kwargs):
    obj = _CONFIG
    try:
        for key in keys:
            obj = obj[key]
        return obj
    except KeyError:
        if 'default' in kwargs:
            return kwargs['default'] 
        raise

reload()