# Video to Gaussian Splat

Simple, reliable tool to convert videos into Gaussian Splat .ply files.

**Video in → Gaussian Splat .ply out**

## Requirements

- Linux (Ubuntu/Debian recommended)
- NVIDIA GPU with CUDA (tested on RTX 3070)
- Python 3.8+
- COLMAP
- 8GB+ GPU VRAM recommended

## Quick Start

### 1. Install Dependencies

```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Install Python dependencies
- Install COLMAP (if not present)
- Verify CUDA setup

**Note:** If automatic COLMAP installation fails, install manually:
- Ubuntu: `sudo apt install colmap`
- Or build from source: https://colmap.github.io/install.html

### 2. Process Your Video

```bash
python video_to_splat.py your_video.mp4
```

That's it! The script will:
1. Extract frames from your video
2. Run COLMAP to estimate camera poses
3. Clone and setup Gaussian Splatting (first run only)
4. Train the Gaussian Splat model
5. Output `output.ply`

## Usage Options

```bash
# Basic usage
python video_to_splat.py video.mp4

# Custom output path
python video_to_splat.py video.mp4 -o my_splat.ply

# Extract more frames for better quality (slower)
python video_to_splat.py video.mp4 --fps 5

# More training iterations for better quality (slower)
python video_to_splat.py video.mp4 --iterations 15000

# Custom workspace directory
python video_to_splat.py video.mp4 --workspace my_workspace
```

## Tips for Best Results

1. **Video Quality:** Use clear, well-lit videos
2. **Camera Movement:** Smooth, circular motion around the subject works best
3. **Subject:** Static objects are easier than moving ones
4. **Duration:** 10-30 seconds is usually enough
5. **Frame Rate:** Start with default (2 fps), increase if needed
6. **Iterations:** 7000 is good for testing, 15000-30000 for final results

## Viewing Your Gaussian Splat

You can view the generated .ply file using:
- https://antimatter15.com/splat/ (web viewer)
- https://github.com/antimatter15/splat (desktop viewer)
- SuperSplat: https://playcanvas.com/supersplat/editor

## Troubleshooting

**COLMAP fails:**
- Make sure your video has enough texture/features
- Try a shorter video clip
- Ensure good camera movement (not too fast)

**Out of memory:**
- Reduce --fps to extract fewer frames
- Use a shorter video
- Reduce --iterations

**Poor quality results:**
- Increase --fps for more frames
- Increase --iterations for more training
- Ensure good video quality and camera movement

**CUDA errors:**
- Verify CUDA installation: `nvcc --version`
- Check PyTorch CUDA: `python -c "import torch; print(torch.cuda.is_available())"`
- May need to reinstall PyTorch with CUDA: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118`

## How It Works

1. **Frame Extraction:** OpenCV extracts frames from video
2. **COLMAP:** Estimates camera poses using structure-from-motion
3. **Gaussian Splatting:** Uses the original Inria implementation to train
4. **Output:** Generates .ply point cloud file

## License

This tool uses:
- [COLMAP](https://colmap.github.io/) - BSD License
- [Gaussian Splatting](https://github.com/graphdeco-inria/gaussian-splatting) - Inria License

Check their respective licenses for usage terms.
