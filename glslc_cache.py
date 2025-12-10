#!/usr/bin/env python

import pathlib
import os
import argparse
import json
import subprocess
import platform
import sys

def get_all_commands(command):
    PATH = os.environ['PATH']
    system = platform.system()
    sep = ':'
    if system == 'Windows':
        sep = ';'
    paths = PATH.split(sep)

    command_full_paths = []
    for path in paths:
        path = pathlib.Path(path)
        command_full_path = path / command
        if command_full_path.exists():
            command_full_paths.append(command_full_path)
    return command_full_paths

def load_config():
    config = None
    config_file = pathlib.Path(os.path.abspath(__file__)).resolve().parent / "config.json"
    if not config_file.exists():
        print("config file not exist!")
    else:
        with open(config_file, "r") as config_file:
            config = json.load(config_file)
    return config

def main():
    config = load_config()
    cache_dir = pathlib.Path(config['cache_dir']).absolute()
    cache_file = cache_dir / pathlib.Path.cwd().name

    glslc_paths = get_all_commands('glslc')

    glslc_calls = sys.argv
    glslc_calls[0] = glslc_paths[1]
    subprocess.run(
            glslc_calls
            )

if __name__ == '__main__':
    main()
