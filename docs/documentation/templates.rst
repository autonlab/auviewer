Project Templates
=================

Template files can be global or project-specific. Here is an example which can be used to generate your own template files.

The "_default" series will apply to all series (unless any settings are overridden by specific series settings).

Series-specific settings can be applied by using the series name, as in "/data/numerics/AR1-D:value" in the example below.

A virtual series comprised of a group of real series can be specified as in "Non-Invasive BP (NBP-X)" in the example below.

.. code-block:: JSON

    {
            "series": {
                    "_default": {
                            "graphHeight": "120px",
                            "drawLine": false,
                            "drawDots": true,
                            "lineColor": "#171717",
                            "dotColor": "#171717",
                            "gridColor": "rgb(232,122,128)",
                            "exceedanceThresholdDemarcation": "rgb(220,0,0)",
                            "ownPatternColor": "rgba(247, 164, 56, 0.77)",
                            "otherPatternColor": "rgba(245, 212, 171, 0.53)",
                            "ownCurrentWorkflowPatternColor": "rgba(0, 189, 29, 0.77)",
                            "otherCurrentWorkflowPatternColor": "rgba(83, 255, 101, 0.53)",
                            "ownAnnotationColor": "rgba(24,186,186,0.77)",
                            "ownAnnotationLabelColor": "#fff",
                            "otherAnnotationColor": "rgba(31,221,221,0.53)",
                            "otherAnnotationLabelColor": "#fff",
                            "show": false
                    },
                    "/data/numerics/AR1-D:value": { "range": [0, 150] },
                    "Non-Invasive BP (NBP-X)": {
                            "members": [
                                    "/data/numerics/NBP-S:value",
                                    "/data/numerics/NBP-M:value",
                                    "/data/numerics/NBP-D:value"
                            ],
                            "range": [0, 150],
                            "show": true
                    }
            }
    }
