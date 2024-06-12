# pyldraw

![python version](https://img.shields.io/static/v1?label=python&message=3.9%2B&color=blue&style=flat&logo=python)
![https://github.com/michaelgale/cq-kit/blob/master/LICENSE](https://img.shields.io/badge/license-MIT-blue.svg)
[![](https://img.shields.io/badge/code%20style-black-black.svg)](http://github.com/psf/black)

This repository contains a python library to work with LDraw CAD files often used for creating and modifying LEGO® models.

LDraw is an open standard used by many LEGO® compatible CAD software tools.  It is based on a hierarchy of elements describing primitive shapes up to complex LEGO models and scenes. 

> This repository supercedes my previous ldraw-py repository which is being archived.
> This implemenation is much improved and more efficient and does not include 
> unnecessary features found in ldraw-py

## Installation

The **pyldraw** package can be installed directly from the source code:

```shell
    $ git clone https://github.com/michaelgale/pyldraw.git
    $ cd pyldraw
    $ pip install .
```

## Usage

After installation, the package can imported:

```shell
    $ python
    >>> import pyldraw
    >>> ldrawpy.__version__
```

An example of the package can be seen below

```python
    from pyldraw import LdrColour

    # Create a white colour using LDraw colour code 15 for white
    mycolour = LdrColour(15)
    print(mycolour.name)
    # White
    print(mycolour.hex_code)
    # #FFFFFF
```

## Requirements

* Python 3.9+

## References

- [LDraw.org](https://www.ldraw.org) - Official maintainer of the LDraw file format specification and the LDraw official part library.
- [ldraw-vscode](https://github.com/michaelgale/ldraw-vscode) - Visual Studio Code language extension plug-in for LDraw files

### Lego CAD Tools

- [Bricklink stud.io](https://www.bricklink.com/v3/studio/download.page) new and modern design tool designed and maintained by Bricklink
- [LeoCAD](https://www.leocad.org) cross platform tool
- [MLCAD](http://mlcad.lm-software.com) for Windows
- [Bricksmith](http://bricksmith.sourceforge.net) for macOS by Allen Smith (no longer maintained)
- [LDView](http://ldview.sourceforge.net) real-time 3D viewer for LDraw models

### LPub Instructions Tools

- Original [LPub](http://lpub.binarybricks.nl) publishing tool by Kevin Clague
- [LPub3D](https://trevorsandy.github.io/lpub3d/) successor to LPub by Trevor Sandy
- [Manual](https://sites.google.com/site/workingwithlpub/lpub-4) for Legacy LPub 4 tool (last version by Kevin Clague)

## Authors

`pyldraw` was written by [Michael Gale](https://github.com/michaelgale)
