Data Directory
==============

When AUViewer is being used to visualize ad-hoc data, a data directory (including database) is _not_ required. In all other cases, a data directory is required.

The data directory is specified either as a function parameters (e.g. when used as a Python module) or as a command-line argument (when starting the web server via command line).

The data directory will contain project files, templates, config, and the database. The directory may be initially empty or pre-populated with some data. The organization of the directory is as follows, and assets will be created by AUViewer as needed if they do not already exist:

* config
    * _config.json_
* database
    * _db.sqlite_
* global_templates
    * _interface_templates.json_
    * _project_template.json_
* projects
    * \[project name\]
        * originals
        * processed
        * templates
            * _interface_templates.json_
            * _project_template.json_