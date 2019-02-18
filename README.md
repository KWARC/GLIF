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

    git clone https://github.com/kaiamann/gf_kernel
    cd gf_kernel

Install the kernel module with:

    python setup.py install
    python -m gf_kernel.install
    

Usage
-----
Note that the kernel will use the directory you open a notebook from as the source directory for GF commands. If you wish to permanently set your GF kernel source directory to a specific directory please use the configure script first:

    ./configure

In case your GF shell binary isn't located in `/usr/bin/` you can also use it to tell the kernel where to find it.
You're now ready to go and can start a Jupyter notebook with:

    jupyter notebook


Select the `gf_kernel` as kernel in your notebook.
The kernel (hopefully) supports all of the normal GF shell commands.
It can also be used to define new grammars, which are also saved and imported for usage after defining.
Viewing graphs can also be done inline in the notebook by using `view` followed by a graph generating command. 
Typing `clean` removes all `.png`, `.gfo` and `.dot` files.
Take a look at the exmaple notebook to see how it works.

This package requires Python 3.