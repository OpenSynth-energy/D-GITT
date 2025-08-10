# D-GITT Project

The following repository contains the technical documentation and tutorials for the D-GITT Project.

The Documentation folder contains a set of Jupyter Notebooks which the users of the dataset can use to get familiar with the basic PowSyBl actions. These tutorials aim to provide some foundations in order to manage the files of the RTE7k dataset available in the [OpenSynth Hugging Face repo](https://huggingface.co/datasets/OpenSynth/). After going through these notebooks, the user should be able to import and export grid models in the supported formats, be able to understand the detailed voltage level topology of the PowSyBl models, modify these models, extract time series profiles for the equipments of the model and running power flows.

## Tutorials structure

The tutorials are supposed to be followed with the following structure. You can see its completion status in parenthesis, as this is an on-going project at the moment. Clicking the Binder icon will open an executable notebook in your browser without needing to install anything in your computer.

1. Data description
    a. Introduction (complete)
    b. ID Inconsistency over time (complete)
    c. Operational limits (TO-DO)
    d. Shunt blocks (TO-DO)
    e. Other elements references (TO-DO)

2. Data format conversion
    a. From XIIDM to other formats and viceversa (complete)

3. Data modification
    a. Modify static data and parameters of the elements (WIP)
    b. Add injection time series (TO-DO)

4. Voltage level topology
    a. Bus-breaker and node-breaker topologies (WIP)

5. Execution analysis
    a. Launching a powerflow (TO-DO)
    b. Secutity-constrained analysis (TO-DO)


## How to run locally the notebooks?

If the user wants to run locally a notebook, it must first install two modules in a Python environment. **IMPORTANT:** PyPowSyBl is not supported in the lastest version of Python 3.13, **Python version 3.12 is recommended**, although it is supported from version 3.8.

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

The users should download the folder where the notebook is located in order to have access to all the necessary files to visualize and run all the pieces of code.
