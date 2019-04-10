# -*- coding: utf-8 -*-
#
# Open Source Voting Results Reporter (ORR) - election results report generator
# Copyright (C) 2019  Chris Jerdonek
#
# This file is part of Open Source Voting Results Reporter (ORR).
#
# ORR is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

"""
Entry-point script to run ORR using Docker.
"""

import argparse
import logging
import os
from pathlib import Path
import shlex
import subprocess
from subprocess import Popen
import sys
from textwrap import dedent

import orr.scripts.scriptcommon as scriptcommon
from orr.utils import UTF8_ENCODING


_log = logging.getLogger(__name__)


DESCRIPTION = """\
Wrapper script to run orr in a Docker container.
"""

def parse_args():
    """
    Parse sys.argv and return a Namespace object.
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION,
                    formatter_class=argparse.RawDescriptionHelpFormatter)

    scriptcommon.add_common_args(parser)
    source_dir_help = dedent("""\
    the directory containing the Dockerfile to build.  Normally this should
    be the directory to the repository root of a clone of the ORR repository.
    Defaults to the current working directory (".").
    """)
    parser.add_argument('--source-dir', metavar='DIR', help=source_dir_help)
    parser.add_argument('--skip-docker-build', action='store_true',
        help='whether to skip building the Docker image.')
    parser.add_argument('--orr_args', nargs=argparse.REMAINDER,
        help='extra arguments to pass to the underlying orr command.')

    ns = parser.parse_args()

    return ns


def run_subprocess(args, check=True, **kwargs):
    command = ' '.join(shlex.quote(arg) for arg in args)
    msg = dedent(f"""\
    running command:

        $ {command}
    """)
    _log.info(msg)
    # Redirect stderr to stdout, and capture stdout.
    with Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
               encoding=UTF8_ENCODING, **kwargs) as proc:
        while True:
            line = proc.stdout.readline()
            if not line:
                # Then the subprocess is done.
                break
            # Write the output to stderr so as not to interfere with stdout.
            sys.stderr.write(line)

        # Wait for the child process to terminate.
        proc.wait()

        if check and proc.returncode:
            msg = f'subprocess ended with return code: {proc.returncode}'
            raise RuntimeError(msg)


def main():
    ns = parse_args()

    output_dir, build_time, log_level = scriptcommon.parse_common_args(ns, default_log_level=logging.INFO)

    logging.basicConfig(level=log_level)

    orr_args = ns.orr_args or []
    skip_docker_build = ns.skip_docker_build
    source_dir = ns.source_dir

    if source_dir is None:
        source_dir = os.curdir

    source_dir = Path(source_dir)
    if not (source_dir / 'Dockerfile').exists():
        resolved_path = source_dir.resolve()
        raise RuntimeError(
            f'--source-dir does not contain a file "Dockerfile": {source_dir} '
            f'(resolves to: {resolved_path})'
        )

    docker_tag = 'orr'
    container_name = 'orr_test'

    if skip_docker_build:
        _log.info('skipping building Docker image')
    else:
        _log.info(f'building Docker image: {docker_tag}')

        # Convert the path object to a string.
        args = ['docker', 'build', '-t', docker_tag, str(source_dir)]
        run_subprocess(args)

    args = ['docker', 'rm', container_name]
    # Don't pass check=True to prevent an error if the container doesn't exist.
    run_subprocess(args, check=False)

    docker_output_parent = '/tmp/orr'
    docker_output_dir_name = 'output'

    args = [
        'docker', 'run', '--name', container_name, 'orr',
        '--output-parent', docker_output_parent, '--output-subdir', docker_output_dir_name,
    ]
    args.extend(orr_args)
    run_subprocess(args)

    # Append a "." so the contents of the directory will be copied,
    # rather than the directory itself.
    src_dir = os.path.join(docker_output_parent, docker_output_dir_name, '.')
    docker_src = f'{container_name}:{src_dir}'

    # Convert the Path object to a string.
    args = ['docker', 'cp', docker_src, str(output_dir)]
    run_subprocess(args)

    output_data = scriptcommon.print_result(output_dir, build_time=build_time)

    _log.info(f'done: {docker_tag}')