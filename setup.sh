#!/bin/bash

set -e

echo "=================================="
echo "Setting up Video to Gaussian Splat"
echo "=================================="

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Warning: This setup script is designed for Linux"
    echo "For other platforms, please install COLMAP manually"
    echo "Visit: https://colmap.github.io/install.html"
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Check if COLMAP is installed
echo ""
echo "Checking for COLMAP..."
if command -v colmap &> /dev/null; then
    echo "COLMAP is already installed"
    colmap -h | head -n 1
else
    echo "COLMAP not found. Installing COLMAP..."

    # Install COLMAP dependencies
    sudo apt-get update
    sudo apt-get install -y \
        git \
        cmake \
        build-essential \
        libboost-program-options-dev \
        libboost-filesystem-dev \
        libboost-graph-dev \
        libboost-system-dev \
        libboost-test-dev \
        libeigen3-dev \
        libsuitesparse-dev \
        libfreeimage-dev \
        libmetis-dev \
        libgoogle-glog-dev \
        libgflags-dev \
        libglew-dev \
        qtbase5-dev \
        libqt5opengl5-dev \
        libcgal-dev \
        libceres-dev

    # Clone and build COLMAP
    cd /tmp
    git clone https://github.com/colmap/colmap.git
    cd colmap
    mkdir build
    cd build
    cmake .. -DCMAKE_CUDA_ARCHITECTURES=86  # For RTX 3070
    make -j$(nproc)
    sudo make install

    echo "COLMAP installed successfully"
fi

# Check CUDA
echo ""
echo "Checking CUDA..."
if command -v nvcc &> /dev/null; then
    nvcc --version
    echo "CUDA found"
else
    echo "Warning: CUDA not found. You need CUDA for GPU acceleration."
    echo "Please install CUDA toolkit from: https://developer.nvidia.com/cuda-downloads"
fi

# Check PyTorch CUDA
echo ""
echo "Checking PyTorch CUDA support..."
python3 -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')" || echo "PyTorch not installed yet"

echo ""
echo "=================================="
echo "Setup complete!"
echo "=================================="
echo ""
echo "To process a video, run:"
echo "  python video_to_splat.py your_video.mp4"
echo ""
