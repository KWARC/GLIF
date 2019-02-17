from distutils.core import setup

with open('README.md') as f:
    readme = f.read()

setup(
    name='gf_kernel',
    version='1.0',
    packages=['gf_kernel'],
    # package_data={
    #     'gf_kernel' : ['unicode-latex-map']
    # },
    description='Simple example kernel for GF',
    long_description=readme,
    author='Kai Amann',
    author_email='kai.amann@fau.de',
    url='https://github.com/UniFormal/gf_kernel',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ]
    
)
