import os
from configobj import ConfigObj


def load_config(system=False):
    if system:
        path = '/etc/globus.cfg'
    else:
        path = os.path.expanduser("~/.globus.cfg")

    return ConfigObj(path)


def parse_path_param(parameter):
    section = 'cli'
    if '.' in parameter:
        section, parameter = parameter.split('.', 1)
        if section != 'cli':
            section = 'cli ' + section
    return section, parameter
