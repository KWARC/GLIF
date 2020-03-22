import setuptools

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    name='glif_kernel',
    version='1.0.0',
    packages=['glif_kernel'],
    package_data={
        'glif_kernel' : ['messages.json', 'unicode-latex-map']
    },
    install_requires = [
        'ipykernel>=5.1.0',
        'ipython>=7.2.0',
        'ipywidgets>=7.4.2',
        'jupyter>=1.0.0',
        'jupyter-client>=5.2.4',
    ],
    description='Simple example kernel for GLF',
    long_description=long_description,
    long_description_content_type='text/markdown',
    include_package_data=True,
    author='Kai Amann',
    author_email='kai.amann@fau.de',
    url='https://github.com/UniFormal/glif_kernel',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
    ]
    
)
