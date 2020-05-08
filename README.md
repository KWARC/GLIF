GLIF Kernel
==========

`glif_kernel` is a kernel for [Jupyter](https://jupyter.org/) that combines functionalities of [GF](https://www.grammaticalframework.org/), [MMT](https://uniformal.github.io/) and [ELPI](https://github.com/LPCIC/elpi)
into a unified framework for natural-language semantics experimentation.
It is based on the [GLF Kernel](https://github.com/kaiamann/glf_kernel), which only supports GF and MMT.

**If you don't care about MMT/ELPI you can simply ignore those parts and just use the kernel for GF!!!**

Similarly, it is possible, to use the kernel only for MMT theories.


Prerequisites
-------------

Except for Python, all prerequisites are optional, i.e. if you don't install e.g. MMT, the kernel still works. You just can't use the MMT functionality in this case.

#### Python

This package requires Python 3.8 (or newer) and this README assumes that this is the default python version. 
If in doubt, use `python3` instead of `python` and `python3 -m pip` instead of `pip`. 

#### GF (optional)

If you haven't installed GF already, get it from the official [download website](https://www.grammaticalframework.org/download/index.html).
Make sure that `gf` is in your path.

##### Optional: Graphviz (for viewing parse trees)

For graph visualization GF uses [Graphviz](http://www.graphviz.org/). Under Ubuntu etc. you can install it with
    
    sudo apt install graphviz

or under Mac OS X with [homebrew](https://brew.sh):

    brew install graphviz

#### MMT (optional)

You can find installation instructions for MMT [here](https://uniformal.github.io//doc/setup/).
Please note that as of now (March 2020), GLIF uses some not-yet released features of MMT.
So you will have to either talk to us (probably the best idea) or try building MMT yourself from the `devel` branch of the git repository.
If you only want to use MMT for the `glif_kernel`, you don't have to install an MMT development IDE (in a way, the notebooks will be your IDE).

To tell `glif_kernel` where to find the MMT installation, you need to set the environment variable
`MMT_PATH` such that it points to the directory with your MMT installation,
i.e. there should be the file `$MMT_PATH/deploy/mmt.jar`.

#### ELPI (optional)

You need ELPI, which you can get from OPAM (see [this README](https://github.com/LPCIC/elpi)).
Make sure that `elpi` is in your path.
Note that people sometimes install old elpi without noticing. This results in some of the examples
not working.



Remarks for Windows Users
-------------------------

The `glif_kernel` has been succesfully installed on Windows as well.
There are two ways you can go about it and it is not clear which one is better/easier/more likely to work:

#### Using the Windows Subsystem for Linux (WSL)

In this case you can basically follow the installation instructions for linux.
Since Jupyter simply runs a server you can use your notebooks from a browser that
is not part of the WSL.
[These](https://medium.com/@sayanghosh_49221/jupyter-notebook-in-windows-subsystem-for-linux-wsl-f075f7ec8691)
remarks on Jupyter notebooks in WSL may be helpful.

#### Installing it directly in Windows

In this case you have to add GF and Graphviz (in particular `dot`) to the PATH variable.
Unfortunately, **ELPI doesn't support Windows**, so you can't use any ELPI functionality.


Installation
------------

You can either install the kernel from the source repository: 

    git clone https://github.com/KWARC/GLIF.git
    cd GLIF
    pip install .

Afterwards, install the kernel module with:

    python -m glif_kernel.install
    
If you want to use Jupyter lab, you need to install an [extra extension for syntax-highlighting](https://github.com/kaiamann/jupyterlab-gf-highlight):

    jupyter labextension install jupyterlab-gf-highlight

Usage
-----

You're now ready to go and can start a Jupyter notebook with:

    jupyter notebook

Alternatively you can also use this Kernel in Jupyter Lab

    jupyter lab

If you intend on using the visulaization capabilities of the kernel please make sure you have widgets enabled in your Jupyter Lab.

    conda install -c conda-forge nodejs
    jupyter labextension install @jupyter-widgets/jupyterlab-manager

Select `GLIF` as kernel in your notebook.
The kernel supports all of the GF shell commands.
Output files produced by these commands will be placed into the current directory.


### Introductory Notebooks

The `notebooks` folder contains many different example notebooks. `notebooks/README.md` contains
more detailed information on them.

The recommended introductory notebooks are:

* `notebooks/tutorial-gf.ipynb`: Explains how to use the kernel for GF
* `notebooks/tutorial-mmt.ipynb`: Explains how to use the kernel for MMT
* `notebooks/tutorial-glif.ipynb`: Explains how to use the kernel for implementing GLIF pipelines. You should check out the previous two notebooks first.


### Kernel Commands etc. (possibly out-dated)

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
- experimental: you can generate stubs for concrete syntaxes and semantics construction views from abstract syntax. Let's say you have defined an abstract syntax `MyGrammar`. Then you can generate a concrete syntax for e.g. English by entering `MyGrammarEng` and pressing <kbd>Tab</kbd> (stub-generation is autocompletion). Similarly, you can enter `MyGrammarSemantics` to generate a stub for the semantics-construction view. This only works, if our Python parse for GF can handle the abstract syntax (and it's still more of a prototype, so it can't handle e.g. dependent types).

What is GLIF
------------

GLIF is intended as a framework for natural language understanding (NLU) experiments.
GF can be used to quickly write grammars for natural language fragments.
MMT can be used to describe a logic and the translation from GF's parse trees into that logic, which is called semantics construction.
ELPI is used for inference.
This way, the GLIF kernel can be used to quickly implement the entire pipeline from natural language strings to a logical expression and then do inference for ambiguity resolution/theorem proving/...

If you want to read more about GLF, the framework underlying GLIF, you may be interested in [this](https://kwarc.info/people/mkohlhase/submit/lfmtp-19.pdf) paper.


