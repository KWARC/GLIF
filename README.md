GF Kernel
===========

`glf_kernel` is a [GF](https://www.grammaticalframework.org/) kernel for [Jupyter](https://jupyter.org/), which is extended by functionalities provided by [MMT](https://uniformal.github.io/).

Prerequisites
-------------

This package requires Python 3 (or newer) and this README assumes that this is the default python version. 
If in doubt, use `python3` instead of `python` and `python3 -m pip` instead of `pip`. 

If you haven't installed GF already, get it from the official [download website](https://www.grammaticalframework.org/download/index.html).

For graph visualization GF uses [graphviz](http://www.graphviz.org/), so please make sure you have it installed:
    
    sudo apt install graphviz

or under Mac OS X with [homebrew](https://brew.sh):

    brew install graphviz

Additionally, `setuptools` is required to install this package. 
This likely came with your Python distribution, but in case it did not use `pip install setuptools` to install it.  

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
- You can use the kernel to define new theories or views just like you would do with grammars. For this the kernel also supports <kbd>Tab<kbd> completion of some Unicode characters. (e.g. \rightarrow + <kbd>Tab<kbd> will give you →. \MD + <kbd>Tab<kbd>, \OD + <kbd>Tab<kbd> and \DD + <kbd>Tab<kbd> will give you module, object and declaration delimiters respectively).



