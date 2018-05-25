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
Includes custom filters and context functions.
"""

import logging
from pathlib import Path

import babel.dates
import dateutil.parser
from jinja2 import contextfilter, contextfunction, Environment


_log = logging.getLogger(__name__)


# TODO: move this function to a different module.
def process_template(env:Environment, template_name:str, rel_output_path:Path,
    context:dict=None, test_mode:bool=False):
    """
    Creates the specified output file using the named template,
    where `data` provides the template context. The template
    and included templates will be located within the template
    search path, already setup via configuration data.

    Args:
      env: the Jinja2 Environment object to use.
      template_name: template to expand.
      rel_output_path: the output path (relative to the output directory
        configured in the Jinja2 Environment object), or else '-'.
      context: optional context data.
    """
    if context is None:
        context = {}

    if test_mode:
        print(
            f'Will process_template {template_name} to create {output_path})')
        return

    options = env.globals['options']
    output_dir = options.output_dir
    output_path = output_dir / rel_output_path

    _log.debug(f'process_template: {template_name} -> {output_path}')

    template = env.get_template(template_name)

    # PDF output renders using html, create a .pdf.html file
    if output_path.suffix == '.pdf':
        pdf_path = output_path
        output_path += '.html'
    else:
        pdf_path = ''

    output_dir = output_path.parent
    if not output_dir.exists():
        output_dir.mkdir()

    output_text = template.render(context)
    output_path.write_text(output_text)
    _log.info(f'Created {output_path} from template {template_name}')

    if pdf_path:
        # Convert the html file to pdf_path
        #[TODO]
        return


def format_date(value,format_str:str='medium'):
    """
    Template Filter: Converts a date value (str or datetime) into
    the internationalized representation. A format parameter
    can be supplied, either the standard short, medium, long, or
    full (default is medium), or a pattern in the Locale Data
    Markup Language specification.
    """
    if isinstance(value,str):
        value = dateutil.parser.parse(value)

    return(babel.dates.format_date(value,format_str))


@contextfilter
def translate(context, label):
    """
    Return the translation using the currently set language.
    """
    options = context['options']
    lang = options.lang

    all_trans = context['translations']
    translations = all_trans[label]
    translated = translations[lang]

    return translated


@contextfunction
def subtemplate(context, template_name, file_name):
    """
    Render a template.
    """
    env = context.environment

    process_template(env, template_name=template_name, rel_output_path=file_name,
        context=context)