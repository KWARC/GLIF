# Example Notebooks

This folder contains a number of example GLIF notebooks.

### Tutorials
We have a number of tutorial notebooks,
which explain how to use the GLIF kernel.
Note that they do not explain how to use GLIF.

* `tutorial-gf.ipynb`: Requires *GF*. Explains how to use the GLIF kernel for GF development and testing.
* `tutorial-mmt.ipynb`: Requires *MMT*. Explains how to use the GLIF kernel for MMT development.
* `tutorial-glif.ipynb`: Requires *GF* and *MMT*.
    Explains how to use the GLIF kernel for semantics construction.
    It is recommended to first look at `tutorial-gf.ipynb` and `tutorial-mmt.ipynb`.

### Other Examples
Brief descriptions of the other examples:

* `dimensional-analysis-ki-2020.ipynb`: Requires *GF*, *MMT*, *ELPI*.
    It translates statements of physical properties in a CNL
    into logical expressions.
    Custom ELPI code performs a dimensional analysis to reduce the number
    of readings. For example *5 mN* has to mean *5 meter Newton* when
    talking about energy. When talking about forces, it must mean *5 milli Newton*.
    It served as a running example in [this paper](http://kwarc.info/kohlhase/submit/cicm20-glif.pdf),
    which is submitted to CICM 2020.
* `fake-lambda-test.ipynb`: Requires *GF*, *MMT*.
    Explores how variables in mathematical discourse can be bound during the semantics construction.
* `glforthel-empty-set.ipynb`: Requires *GF*, *MMT*.
    Demo of the GlForTheL project. The GlForThel project
    attempts to re-implement the ForTheL language (system of automated deduction) in GLIF,
    to learn more about the challenges GLIF has to overcome for implementing controlled
    mathematical languages.
* `sample-gf-homework.ipynb`: Requires *GF*.
    Example homework assignment used in a course on logic-based natural language processing.
    It asks the students to develop a grammar in GF.
* `sample-gf-mmt-homework.ipynb`: Requires *GF* and *MMT*.
    Example homework assignment used in a course on logic-based natural language processing.
    It asks students to develop a simple grammar and semantics construction.



### Examples from Papers
If you came here after reading a specific paper,
you can find the necessary information here.


#### The GLIF System: A Framework for Inference-Based Natural-Language Understanding (submitted to KI 2020)

* `dimensional-analysis-ki-2020.ipynb`: Requires *GF*, *MMT*, *ELPI*.
    This notebook contains the running example.
* `glforthel-empty-set.ipynb`: Requires *GF*, *MMT*.
    This notebook demos a project to use GLIF for controlled mathematical language.
    It was developed before we added the inference component (ELPI) to GLIF.

#### Prototyping Controlled Mathematical Languages in Jupyter Notebooks (ICMS 2020)
That paper introduces GLF, the predecessor of GLIF.
Since the GLIF kernel subsumes the deprecated GLF kernel (and is indeed based on it),
all examples have been migrated to GLIF.

* The introductory tutorials `tutorial-gf.ipynb`, `tutorial-mmt.ipynb`, `tutorial-glif.ipynb` should
    provide a nice overview of the Jupyter kernel's features.
* `glforthel-empty-set.ipynb`: Requires *GF*, *MMT*.
    Demos GlForTheL.
* `fake-lambda-test.ipynb`: Requires *GF*, *MMT*.
    Demos the fake lambdas needed in GlForTheL.
    This is a nice example how a Jupyter notebook was used to
    prototype one particular mechanism (the use of fake lambdas)
    before using them in a larger project.
    Of course, the notebook has been cleaned up a bit and explanatory mark-down
    cells have been added.
