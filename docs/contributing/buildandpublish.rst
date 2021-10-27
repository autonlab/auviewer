Building & Publishing
=====================

Build from source & install locally
```````````````````````````````````
::

    cd tools
    ./rebuild

Clean up source builds
``````````````````````
::

    cd tools
    ./clean

Generate Sphinx documentation
`````````````````````````````
::

    cd tools
    ./mkdocs

Build from source and publish Linux (wheels and source)
```````````````````````````````````````````````````````
::

    cd tools
    ./publish_linux

*Note: Requires Docker in order to build with manywheel*

Build from source and publish Mac wheel
```````````````````````````````````````
::

    cd tools
    ./publish_mac
