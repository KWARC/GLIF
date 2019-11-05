GLF Kernel
==========

`glf_kernel` is a kernel for [Jupyter](https://jupyter.org/) that combines functionalities of [GF](https://www.grammaticalframework.org/) and [MMT](https://uniformal.github.io/).
It is based on the [GF Kernel](https://github.com/kwarc/gf_kernel), which only supports GF.

GLF is intended as a framework for natural language understanding (NLU) experiments.
GF can be used to quickly write grammars for natural language fragments.
MMT can be used to describe a logic and the translation from GF's parse trees into that logic, which is called semantics construction.
This way, the GLF kernel can be used to quickly implement the entire pipeline from natural language strings to a logical expression.

If you want to read more about GLF, you may be interested in [this](https://kwarc.info/people/mkohlhase/submit/lfmtp-19.pdf) paper.


Prerequisites
-------------


#### Python

This package requires Python 3 (or newer) and this README assumes that this is the default python version. 
If in doubt, use `python3` instead of `python` and `python3 -m pip` instead of `pip`. 

Additionally, `setuptools` is required to install this package. 
This likely came with your Python distribution, but in case it did not use `pip install setuptools` to install it.  

#### GF

If you haven't installed GF already, get it from the official [download website](https://www.grammaticalframework.org/download/index.html).

#### MMT

You can find installation instructions for MMT [here](https://uniformal.github.io//doc/setup/).
Please note that as of now (November 2019), GLF uses some not-yet released features of MMT.
So you will have to either talk to us (probably the best idea) or try building MMT yourself from the `devel` branch of the git repository.
If you only want to use MMT for the `glf_kernel`, you don't have to install an MMT development IDE (in a way, the notebooks will be your IDE).

#### Optional: Graphviz

For graph visualization GF uses [Graphviz](http://www.graphviz.org/). Under Ubuntu etc. you can install it with
    
    sudo apt install graphviz

or under Mac OS X with [homebrew](https://brew.sh):

    brew install graphviz


Remarks for Windows Users
-------------------------

The `glf_kernel` has been succesfully installed on Windows as well.
There are two ways you can go about it, and it is not clear which one is better/easier/more likely to work:

#### Using the Windows Subsystem for Linux (WSL)

In this case you can basically follow the installation instructions for linux.
Since Jupyter simply runs a server you can use your notebooks from a browser that
is not part of the WSL.
[These](https://medium.com/@sayanghosh_49221/jupyter-notebook-in-windows-subsystem-for-linux-wsl-f075f7ec8691)
remarks on Jupyter notebooks in WSL may be helpful.

#### Installing it directly in Windows

In this case you have to add GF and Graphviz (in particular `dot`) to the PATH variable.


Installation
------------

You can either install the kernel from the source repository: 

    git clone 'insert right URL here'
    cd glf_kernel
    pip install .

or install it directly from pip:

    pip install glf-kernel

Afterwards, install the kernel module with:

    python -m glf_kernel.install
    

Usage
-----
You're now ready to go and can start a Jupyter notebook with:

    jupyter notebook

Alternatively you can also use this Kernel in Jupyter Lab

    jupyter lab

If you intend on using the visulaization capabilities of the kernel please make sure you have widgets enabled in your Jupyter Lab.

    conda install -c conda-forge nodejs
    jupyter labextension install @jupyter-widgets/jupyterlab-manager

Select the `glf_kernel` as kernel in your notebook.
The kernel supports all of the GF shell commands.
Output files produced by these commands will be placed into the current directory.

The kernel can also be used to define new grammars, which are immediately imported for usage upon defining.
If you would like to have line numbers for editing your code you can use the Juypter shortcut <kbd>Esc</kbd>+<kbd>L</kbd> to enable them. 

In addition to the GF shell commands the kernel supports the following commands:
- `show` : show the graph(s). Usage: [graph | graph generating command] | show. (e.g. parse "John loves Mary" | vt | show)
- `help` : shows the help message
- `export` : saves the specified grammar in the current diretory
- `clean` : removes all `.dot`, `.png` and `.gfo` files from the current directory

It also supports MMT specific functionalities like:

- `archive`: creates the specified archive. If it already exists this archive will be set as the working archive. If no arguments are supplied this will display the current working archive. Also also allows creation of nested archives. (e.g. `archive comma/jupyter`)
- `subdir`: used to create or switch subfolders in the current working archives source folder. It is used just like the `archive` command.
- `construct`: sends a construct request to MMT and displays the result.
- You can use the kernel to define new theories or views just like you would do with grammars. For this the kernel also supports <kbd>Tab</kbd> completion of some Unicode characters. (e.g. \rightarrow + <kbd>Tab</kbd> will give you →. \MD + <kbd>Tab</kbd>, \OD + <kbd>Tab</kbd> and \DD + <kbd>Tab</kbd> will give you module, object and declaration delimiters respectively).



