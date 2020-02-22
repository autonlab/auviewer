# This tool will attempt to import a Python dict named template from the Python
# package you specify, convert it to JSON, and output the JSON to a file name
# of your choosing.

#Config
sources_and_destinations = [
    ['template_sources.builtin_default_project_template', '../www/js/builtin_templates/builtin_default_project_template.json'],
    ['template_sources.builtin_default_interface_templates', '../www/js/builtin_templates/builtin_default_interface_templates.json'],
    ['template_sources.builtin_default_project_template', '/zfsauton/data/public/gwelter/AUView/global_templates/global_default_project_template.json'],
    ['template_sources.builtin_default_interface_templates', '/zfsauton/data/public/gwelter/AUView/global_templates/global_default_interface_templates.json']
]

from importlib import import_module
import json

for pair in sources_and_destinations:
    pkg = import_module(pair[0])
    if isinstance(pkg.template, dict):
        with open(pair[1], "w") as t:
            t.write(json.dumps(pkg.template))