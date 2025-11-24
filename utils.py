
import json
import os

def load_param_json():
    """
    Load the param.json file

    Returns: Nested dictionaries of parameters from json file
    """
    f = open(f'{get_root_path()}/src/utilities/params.json')
    params = json.load(f)
    return params


def get_root_path():
    """
    Returns the path to the root of the repo
    """
    cwd = os.path.abspath(os.path.dirname(__file__))
    return f'{cwd}'
def get_data_path():
    """
    Returns the path to the data folder
    """
    return os.path.join(get_root_path(), 'stamped_raw')

def get_sim_path():
    """
    Returns the path to the data folder
    """
    return os.path.join(get_root_path(), 'sim_raw')