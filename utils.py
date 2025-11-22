
import os

def get_root_path():
    """
    Returns the path to the root of the repo
    """
    cwd = os.path.abspath(os.path.dirname(__file__))
    return f'{cwd}/../..'