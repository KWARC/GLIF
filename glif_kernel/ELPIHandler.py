import os
import subprocess
from distutils.spawn import find_executable


# Basically a unique string that will never show up in the output (hopefully)
COMMAND_SEPARATOR = "COMMAND_SEPARATOR===??!<>239'_"
