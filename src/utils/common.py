import yaml
import os


def read_config(config_path="config/config.yaml"):
    """
    It reads the YAML file and returns it as a dictionary.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    full_path = os.path.join(base_dir, config_path)

    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Couldn't find Config file: {full_path}")

    with open(full_path, 'r') as f:
        config = yaml.safe_load(f)
    return config