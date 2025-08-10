#!/bin/bash

# Set environment variables to prevent Half precision overflow
export PYTORCH_NO_CUDA_MEMORY_CACHING=1
export CUDA_DEVICE_ORDER=PCI_BUS_ID
export TORCH_USE_CUDA_DSA=1
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
export CUDA_LAUNCH_BLOCKING=0
export TORCH_CUDNN_V8_API_ENABLED=1

# Set HuggingFace cache directory
export TRANSFORMERS_CACHE=/app/.cache/huggingface
export HF_HOME=/app/.cache/huggingface

# Create cache directory if it doesn't exist
mkdir -p /app/.cache/huggingface

echo "Starting AI Server with optimized environment variables..."
echo "GPU available: $(python3 -c 'import torch; print(torch.cuda.is_available())')"
echo "CUDA version: $(python3 -c 'import torch; print(torch.version.cuda)')"
echo "PyTorch version: $(python3 -c 'import torch; print(torch.__version__)')"

# Start the application
exec python3 main.py 