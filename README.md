# D-GITT Project

The following repository contains the technical documentation and tutorials for the D-GITT Project.

The Documentation folder contains a set of Jupyter Notebooks which the users of the dataset can use to get familiar with the basic PowSyBl actions. These tutorials aim to provide some foundations in order to manage the files of the RTE7k dataset available in [Link text](https://huggingface.co/datasets/rte-france/RTE7000). After going through these notebooks, the user should be able to import and export grid models in the supported formats, be able to understand the detailed voltage level topology of the PowSyBl models, modify these models, extract time series profiles for the equipments of the model and running power flows.

## How to run the notebooks?

In order to run a notebook, the user must first install two modules in a Python environment. **IMPORTANT:** PyPowSyBl is not supported in the lastest version of Python 3.13, **Python version 3.12 is recommended**, although it is supported from version 3.8.

```bash
pip install jupyter

```

```bash
pip install pypowsybl
```

Once installed, one may open a jupyter notebook by opening the jupyter lab and navigating through the folders in its user interface

```bash
jupyter lab
```

or by executing the following command:

```bash

jupyter notebook name_of_the_notebook.ipynb

```

You should download the folder where the notebook is located in order to have access to all the necessary files to visualize and run all the pieces of code.
