#
# Open Source Voting Results Reporter (ORR) - election results report generator
# Copyright (C) 2018  Carl Hage
# Copyright (C) 2018  Chris Jerdonek
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
Contains functions to help configure ORR.
"""

from pathlib import Path

import jinja2
from jinja2 import Environment, FileSystemLoader
from jinja2.utils import Namespace

import orr.templating as templating


def create_jinja_env(output_dir, template_dirs=None):
    """
    Create and return the Jinja2 Environment object.

    Args:
      output_dir: a path-like object.
    """
    if template_dirs is None:
        template_dirs = []

    env = Environment(
        loader=FileSystemLoader(template_dirs),
        autoescape=jinja2.select_autoescape(['html', 'xml']),
        # Enable the expression-statement extension:
        # http://jinja.pocoo.org/docs/2.10/templates/#expression-statement
        extensions=['jinja2.ext.do'],
    )

    # Using a Namespace object lets us change the context inside a
    # template, e.g. by calling "{% set options.lang = lang %}" from
    # within a with block.  Doing this lets us access the option values
    # from within a custom filter, without having to pass the option
    # values explicitly.
    options = Namespace()
    # Jinja requires you to set using index rather than attribute notation.
    options['output_dir'] = Path(output_dir)

    env.globals.update(options=options,
        create_pdf=templating.create_pdf,
        create_tsv_files=templating.create_tsv_files,
        create_xlsx=templating.create_xlsx,
        subtemplate=templating.subtemplate
    )

    filters = dict(
        output_file_uri=templating.output_file_uri,
        format_date=templating.format_date,
        format_date_medium=templating.format_date_medium,
        translate=templating.translate
    )
    tests = {}

    env.filters.update(filters)
    env.tests.update(tests)

    return env
