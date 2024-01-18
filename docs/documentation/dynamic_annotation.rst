Dynamic Annotation
==================

Why does this exist?
--------------------
A user-defined annotation form, so domain experts/analysts can easily define custom annotation forms

How can I use this?
--------------------
At the global viewer level, there are two json files, `project_config.json` and `interface_templates.json`, where analysts can define project specific configuration.
In general, these configurations are pulled into the global state manager on-auviewer-load, so we here add the functionality to define a project-specific annotation form as a field in the `project_template.json`.

An example:

.. code-block:: json

    "_default": {
        "fields": [
            {
                "id": "confidence",
                "label": "Confidence",
                "type": "categorical",
                "classes": ["-3", "-2", "-1", "0", "1", "2", "3"],
                "selection_type": "radio"
            },
            {
                "id": "notes",
                "label": "Notes",
                "type": "text" 
            }
        ]
    }

In this example we see the default annotation form fields defined in json format (the annotation form you're used to seeing). Below, we see a more involved example demonstrating the possible field types and specifications one can add:

.. code-block:: json


    "custom_form": {
        "fields": [
        {
            "id": "pvc_presence",
            "label": "PVC Presence",
            "type": "categorical",
            "classes": ["None", "One PVC", "Multiple PVCs"],
            "selection_type": "button"
        },
        {
            "id": "pac_presence",
            "label": "PAC Presence",
            "type": "categorical",
            "classes": ["None", "One PAC", "Multiple PACs"],
            "selection_type": "button"
        },
        {
            "id": "worth_review",
            "label": "Worth revisiting",
            "type": "text"
        },
        {
            "id": "rhythm_label",
            "label": "Rhythm",
            "type": "categorical",
            "classes": ["Atrial Fibrillation", "Sinus", "Other", "Noise"],
            "selection_type": "button"
        }
        ]
    }

Once you define such a field in the `project_template.json` for that particular project (within the `templates` directory of every defined project in the `projects` folder), you may restart the viewer to see that form rendered for every annotation assignment reflects your defined form.


Implementation
----------------------------------------------
We implemented this mostly with Vue.js, with some code interacting directly with the global state manager in an identical way to the prior javascript state management.

Every form field (the json objects internal to the above `fields` array) are expected to match this format, as found in ``auviewer/static/www/js/src/main.ts``:

.. code-block:: typescript

    export interface AnnotationField 
        {
            id: string,
            label: string,
            type: AnnotationFieldType,
            default?: string,
            required?: boolean,
            classes?: Array<string>,
            class_ids?: Array<string>,
            selection_type?: AnnotationSelectionType
        }


An explanation:
 * *id*: identifier for the attribute being captured, will be the column identifier in the extracted annotations csv
 * *label*: user-readable name to title the field in the annotation form
 * *type*: one of ``categorical`` (for selecting one of multiple pre-defined options as defined by the *classes* attribute) or ``text``

