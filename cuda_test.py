import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA is available: {torch.cuda.is_available()}")
print(f"CUDA version used by PyTorch: {torch.version.cuda}")
print(f"Number of GPUs detected: {torch.cuda.device_count()}")
print(f"Current GPU name: {torch.cuda.get_device_name(0)}")

# Exit the interpreter
exit()
