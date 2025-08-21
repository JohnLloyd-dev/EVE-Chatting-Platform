FROM nvidia/cuda:12.1.0-devel-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    build-essential \
    cmake \
    ninja-build \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python
RUN ln -s /usr/bin/python3.11 /usr/bin/python

# Set environment variables for CUDA with explicit linker configuration
ENV CMAKE_ARGS="-DGGML_CUDA=on -DCMAKE_LIBRARY_PATH=/usr/local/cuda/lib64 -DCMAKE_INCLUDE_PATH=/usr/local/cuda/include"
ENV FORCE_CMAKE=1
ENV CUDA_HOME=/usr/local/cuda
ENV PATH=/usr/local/cuda/bin:$PATH
ENV LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64:$LD_LIBRARY_PATH
ENV LIBRARY_PATH=/usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64:$LIBRARY_PATH
ENV CPATH=/usr/local/cuda/include:$CPATH
ENV LDFLAGS="-L/usr/local/cuda/lib64 -lcuda -lcudart"
ENV CFLAGS="-I/usr/local/cuda/include"

# Ensure CUDA libraries are available for linking and create symlinks if needed
RUN ldconfig /usr/local/cuda/lib64 && \
    ln -sf /usr/local/cuda/lib64/libcuda.so.1 /usr/local/cuda/lib64/libcuda.so && \
    ln -sf /usr/local/cuda/lib64/libcudart.so.12 /usr/local/cuda/lib64/libcudart.so

# Install llama-cpp-python with CUDA support
RUN pip install --no-cache-dir llama-cpp-python[server] --force-reinstall --upgrade

# Install other Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]