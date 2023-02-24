# napari-BacSeg

[![License BSD-3](https://img.shields.io/pypi/l/napari-bacseg.svg?color=green)](https://github.com/piedrro/napari-bacseg/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-bacseg.svg?color=green)](https://pypi.org/project/napari-bacseg)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-bacseg.svg?color=green)](https://python.org)
[![tests](https://github.com/piedrro/napari-bacseg/workflows/tests/badge.svg)](https://github.com/piedrro/napari-bacseg/actions)
[![codecov](https://codecov.io/gh/piedrro/napari-bacseg/branch/main/graph/badge.svg)](https://codecov.io/gh/piedrro/napari-bacseg)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-bacseg)](https://napari-hub.org/plugins/napari-bacseg)

Bacterial segmentation and analysis platform than can inport/export files in multiple formats. Integrating many tools such as Cellpose, ColiCoords, Oufti/MicrobeTracker.

----------------------------------

This [napari] plugin was generated with [Cookiecutter] using [@napari]'s [cookiecutter-napari-plugin] template.

<!--
Don't miss the full getting started guide to set up your new package:
https://github.com/napari/cookiecutter-napari-plugin#getting-started

and review the napari docs for plugin developers:
https://napari.org/stable/plugins/index.html
-->

## Installing BacSeg

You can install `napari-bacseg` via [pip]:

    conda create –-name napari-bacseg python==3.9
    conda activate napari-bacseg
    conda install -c anaconda git
    conda update --all

    pip install napari[all]

    pip install git+https://github.com/piedrro/napari-bacseg.git

## Updating BacSeg
Once you have installed the plugin, you can update the plugin by running the following commands:

    pip install git+https://github.com/piedrro/napari-bacseg.git

## GPU Installation
 Once you have installed the plugin, you can install the GPU version of the plugin by running the following commands:

    pip uninstall torch
    conda install pytorch torchvision torchaudio pytorch-cuda=11.7 -c pytorch -c nvidia

If the latest CUDA versions don't work, try an older version like cuda 11.3:

    pip uninstall torch
    conda install pytorch torchvision torchaudio cudatoolkit=11.3 -c pytorch -c nvidia




## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [BSD-3] license,
"napari-bacseg" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[Cookiecutter]: https://github.com/audreyr/cookiecutter
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[cookiecutter-napari-plugin]: https://github.com/napari/cookiecutter-napari-plugin

[file an issue]: https://github.com/piedrro/napari-bacseg/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
