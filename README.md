GF Kernel
===========

`gf_kernel` is a [GF](https://www.grammaticalframework.org/) kernel for [Jupyter](https://jupyter.org/).

Prerequisites
-------------
If you haven't installed GF already, get it from the official [download website](https://www.grammaticalframework.org/download/index.html).


For graph visualization GF uses [graphviz](http://www.graphviz.org/), so please make sure you have it installed.
    
    sudo apt install graphviz

Installation
------------
Install all necessary packages:

    pip install -r requirements.txt

Clone the kernel:

    git clone https://github.com/kwarc/gf_kernel
    cd gf_kernel

Install the kernel module with:

    python setup.py install
    python -m gf_kernel.install
    

Usage
-----
You're now ready to go and can start a Jupyter notebook with:

    jupyter notebook

Select the `gf_kernel` as kernel in your notebook.
The kernel supports all of the GF shell commands.
Output files produced by these commands will be placed into the current directory.

The kernel can also be used to define new grammars, which are immediately imported for usage upon defining.
If you would like to have line numbers for editing your code you can use the Juypter shortcut <kbd>Esc</kbd>+<kbd>L</kbd> to enable them. 

In addition to the GF shell commands the kernel supports the following commands:
- `view` : show the graph(s) generated by the specified GF shell command
- `help` : shows the help message
- `export` : saves the specified grammar in the current diretory
- `clean` : removes all `.dot`, `.png` and `.gfo` files from the current directory

Please refer to the tutorial notebook to see how exactly they are used.

This package requires Python 3.
