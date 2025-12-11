#!/usr/bin/env python

import pathlib
import os
import argparse
import json
import subprocess
import platform
import sys
import hashlib
import shutil

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
    res = subprocess.run(cmds, capture_output=True, encoding='utf-8')
    deps_out = res.stdout
    deps_lines = deps_out.splitlines()
    deps = {}
    for dep_line in deps_lines:
        files = dep_line.split(' ')
        output = files[0].removesuffix(':')
        if '-c' not in cmds and '-S' not in cmds:
            output = 'a.spv'
        inputs = files[1:]
        deps[output] = inputs
    return deps

def hash_file(path):
    digest = 0
    with open(path, "rb") as f:
        digest = hashlib.file_digest(f, "sha256")
    return digest.hexdigest()
def hash_file_to_bytes(path):
    digest = 0
    with open(path, "rb") as f:
        digest = hashlib.file_digest(f, "sha256")
    return digest.digest()

def main():
    config = load_config()
    cache_dir = pathlib.Path(config['cache_dir']).absolute()
    cache_file = cache_dir / pathlib.Path.cwd().name
    
    if not cache_file.exists():
        with cache_file.open('w') as file:
            json.dump({}, file)

    glslc_paths = get_all_commands('glslc')

    glslc_calls = [str(glslc_paths[1])]
    glslc_calls.extend(sys.argv[1:])

    deps = glsl_generate_deps(glslc_calls.copy())

    input_files = []
    inputs_hash = hashlib.sha256()
    for output_file in deps:
        this_input_files = deps[output_file]
        input_files.extend(this_input_files)
    for input_file in input_files:
        inputs_hash.update(hash_file_to_bytes(input_file))
    inputs_hash = inputs_hash.hexdigest()

    cache = None
    key = " ".join(glslc_calls)
    with cache_file.open() as file:
        cache = json.load(file)
        if key in cache:
            if inputs_hash in cache[key]:
                output_hashs = cache[key][inputs_hash]
                for output_file in output_hashs:
                    output_file_cache = cache_dir / output_hashs[output_file]
                    shutil.copy(output_file_cache, output_file)
                print('cache hit')
                return

    print('run', glslc_calls)
    res = subprocess.run(
            glslc_calls
            )

    if res.returncode == 0:
        output_hashs = {}
        for output_file in deps:
            output_hash = hash_file(output_file)
            output_hashs[output_file] = output_hash
            output_file_cache = cache_dir / output_hash
            output_file = pathlib.Path(output_file)
            shutil.copy(output_file, output_file_cache)

        with cache_file.open('w') as file:
            print('cache result')
            if not key in cache:
                cache[key] = {}
            cache[key][inputs_hash] = output_hashs
            json.dump(cache, file, indent=4)

if __name__ == '__main__':
    main()
