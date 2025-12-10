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

def glsl_generate_deps(cmds):
    cmds.append('-M')
    res = subprocess.run(cmds, capture_out=True, encoding='utf-8')
    deps_out = res.stdout
    deps_lines = deps_out.splitlines()
    deps = {}
    for dep_line in deps_lines:
        files = dep_line.split(' ')
        output = files[0].removesuffix(':')
        inputs = files[1:]
        deps[output] = inputs
    return deps

def main():
    config = load_config()
    cache_dir = pathlib.Path(config['cache_dir']).absolute()
    cache_file = cache_dir / pathlib.Path.cwd().name
    
    if not cache_file.exists():
        cache_file.touch()

    glslc_paths = get_all_commands('glslc')

    glslc_calls = sys.argv
    glslc_calls[0] = glslc_paths[1]

    deps = glsl_generate_deps(glslc_calls)

    input_files = []
    input_hashs = {}
    for output_file in deps:
        this_input_files = deps[output_file]
        input_files.merge(this_input_files)

    input_hash = hash(input_hashs)

    with cache_file.open() as cache_file:
        cache = json.load(cache_file)
        key = "".join(glslc_calls)
        if key in cache:
            cache = cache[key]
            if input_hash in cache:
                output_hashs = cache[input_hash]
                for output_file in output_hashs:
                    output_file_cache = cache_dir / output_hashs[output_file]
                    copy_file(outpu_file_cache, output)
                return

    subprocess.run(
            glslc_calls
            )

    output_hashs = {}
    for output_file in deps:
        output_hash = hash_file(output_file)
        output_hashs[output_file] = output_hash
        output_file_cache = cache_dir / output_hash
        copy_file(output_file, output_file_cache)

    with cache_file.open('rw') as cache_file:
        cache = json.load(cache_file)
        key = "".join(glslc_calls)
        if not key in cache:
            cache[key] = {}
        cache = cache[key]
        cache[input_hash] = output_hashs

if __name__ == '__main__':
    main()
