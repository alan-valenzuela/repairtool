import yaml
import pickle


def read_config(filename='config.yaml'):
    """Read YAML configuration and log it."""
    with open(filename, 'r') as stream:
        Config = yaml.safe_load(stream)
    return Config


def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def load_object(filename):
    with open(filename, 'rb') as input:
        return pickle.load(input)
