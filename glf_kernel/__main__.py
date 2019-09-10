from ipykernel.kernelapp import IPKernelApp
from . import GLFKernel

IPKernelApp.launch_instance(kernel_class=GLFKernel)
