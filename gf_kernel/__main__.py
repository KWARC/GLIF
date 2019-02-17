from ipykernel.kernelapp import IPKernelApp
from . import GFKernel

IPKernelApp.launch_instance(kernel_class=GFKernel)
