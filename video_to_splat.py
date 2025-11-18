#!/usr/bin/env python3
"""
Simple Video to Gaussian Splat converter
Video in -> Gaussian Splat .ply out

Requirements:
- COLMAP installed
- CUDA-capable GPU
- Python 3.8+
"""

import os
import sys
import subprocess
import shutil
import cv2
from pathlib import Path
import argparse


def run_command(cmd, cwd=None, check=True):
    """Run a shell command and print output"""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    print(f"{'='*60}\n")

    result = subprocess.run(
        cmd,
        cwd=cwd,
        shell=isinstance(cmd, str),
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    if result.stdout:
        print(result.stdout)

    return result


def extract_frames(video_path, output_dir, fps=2):
    """Extract frames from video using OpenCV"""
    print(f"\nExtracting frames from {video_path}...")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = max(1, int(video_fps / fps))

    frame_count = 0
    saved_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            frame_path = output_dir / f"frame_{saved_count:04d}.jpg"
            cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            saved_count += 1

        frame_count += 1

    cap.release()
    print(f"Extracted {saved_count} frames to {output_dir}")

    return saved_count


def run_colmap(image_dir, workspace_dir):
    """Run COLMAP to get camera poses"""
    print("\nRunning COLMAP for camera pose estimation...")

    workspace_dir = Path(workspace_dir)
    database_path = workspace_dir / "database.db"
    sparse_dir = workspace_dir / "sparse"
    sparse_dir.mkdir(parents=True, exist_ok=True)

    # Feature extraction
    run_command([
        "colmap", "feature_extractor",
        "--database_path", str(database_path),
        "--image_path", str(image_dir),
        "--ImageReader.single_camera", "1",
        "--ImageReader.camera_model", "OPENCV",
        "--SiftExtraction.use_gpu", "1"
    ])

    # Feature matching
    run_command([
        "colmap", "exhaustive_matcher",
        "--database_path", str(database_path),
        "--SiftMatching.use_gpu", "1"
    ])

    # Sparse reconstruction
    run_command([
        "colmap", "mapper",
        "--database_path", str(database_path),
        "--image_path", str(image_dir),
        "--output_path", str(sparse_dir)
    ])

    # Convert to text format for gaussian splatting
    model_dir = sparse_dir / "0"
    if not model_dir.exists():
        raise RuntimeError("COLMAP reconstruction failed - no model generated")

    run_command([
        "colmap", "model_converter",
        "--input_path", str(model_dir),
        "--output_path", str(model_dir),
        "--output_type", "TXT"
    ])

    print(f"COLMAP reconstruction complete: {model_dir}")


def setup_gaussian_splatting():
    """Clone and setup gaussian-splatting repo if needed"""
    gs_dir = Path("gaussian-splatting")

    if not gs_dir.exists():
        print("\nCloning gaussian-splatting repository...")
        run_command([
            "git", "clone",
            "https://github.com/graphdeco-inria/gaussian-splatting.git",
            "--recursive"
        ])

        print("\nInstalling gaussian-splatting dependencies...")
        run_command(["pip", "install", "-r", "requirements.txt"], cwd=gs_dir)

        # Install submodules
        submodules_dir = gs_dir / "submodules"

        # diff-gaussian-rasterization
        diff_gauss = submodules_dir / "diff-gaussian-rasterization"
        if diff_gauss.exists():
            run_command(["pip", "install", "."], cwd=diff_gauss)

        # simple-knn
        simple_knn = submodules_dir / "simple-knn"
        if simple_knn.exists():
            run_command(["pip", "install", "."], cwd=simple_knn)
    else:
        print("\ngaussian-splatting repository already exists")

    return gs_dir


def train_gaussian_splat(gs_dir, data_dir, output_dir, iterations=7000):
    """Train gaussian splatting model"""
    print(f"\nTraining Gaussian Splatting model...")

    train_script = gs_dir / "train.py"

    if not train_script.exists():
        raise RuntimeError(f"Training script not found: {train_script}")

    # Run training
    run_command([
        "python", "train.py",
        "-s", str(data_dir),
        "-m", str(output_dir),
        "--iterations", str(iterations)
    ], cwd=gs_dir)

    # Find the output .ply file
    ply_files = list(Path(output_dir).rglob("*.ply"))

    if not ply_files:
        raise RuntimeError("No .ply file generated")

    # Return the point cloud file (typically point_cloud.ply or iteration_X.ply)
    final_ply = None
    for ply in ply_files:
        if "point_cloud" in str(ply) or f"iteration_{iterations}" in str(ply):
            final_ply = ply
            break

    if not final_ply:
        final_ply = ply_files[-1]  # Use the last one

    return final_ply


def prepare_colmap_data_for_gaussian_splatting(colmap_workspace, output_dir):
    """Prepare COLMAP output for gaussian splatting input"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy images
    images_src = Path(colmap_workspace) / "images"
    images_dst = output_dir / "images"
    if images_dst.exists():
        shutil.rmtree(images_dst)
    shutil.copytree(images_src, images_dst)

    # Copy sparse model
    sparse_src = Path(colmap_workspace) / "sparse" / "0"
    sparse_dst = output_dir / "sparse" / "0"
    sparse_dst.parent.mkdir(parents=True, exist_ok=True)
    if sparse_dst.exists():
        shutil.rmtree(sparse_dst)
    shutil.copytree(sparse_src, sparse_dst)

    print(f"Prepared data for gaussian splatting: {output_dir}")
    return output_dir


def main():
    parser = argparse.ArgumentParser(description="Convert video to Gaussian Splat")
    parser.add_argument("video", help="Path to input video file")
    parser.add_argument("-o", "--output", default="output.ply", help="Output .ply file path")
    parser.add_argument("--fps", type=int, default=2, help="Frames per second to extract (default: 2)")
    parser.add_argument("--iterations", type=int, default=7000, help="Training iterations (default: 7000)")
    parser.add_argument("--workspace", default="workspace", help="Working directory (default: workspace)")

    args = parser.parse_args()

    # Check if video exists
    if not os.path.exists(args.video):
        print(f"Error: Video file not found: {args.video}")
        sys.exit(1)

    # Check if COLMAP is installed
    try:
        subprocess.run(["colmap", "-h"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: COLMAP is not installed or not in PATH")
        print("Please install COLMAP: https://colmap.github.io/install.html")
        sys.exit(1)

    workspace = Path(args.workspace)
    workspace.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Extract frames
        images_dir = workspace / "images"
        num_frames = extract_frames(args.video, images_dir, fps=args.fps)

        if num_frames < 10:
            print("Warning: Very few frames extracted. Results may be poor.")

        # Step 2: Run COLMAP
        colmap_workspace = workspace / "colmap"
        colmap_workspace.mkdir(parents=True, exist_ok=True)

        # Copy images to colmap workspace
        colmap_images = colmap_workspace / "images"
        if colmap_images.exists():
            shutil.rmtree(colmap_images)
        shutil.copytree(images_dir, colmap_images)

        run_colmap(colmap_images, colmap_workspace)

        # Step 3: Setup Gaussian Splatting
        gs_dir = setup_gaussian_splatting()

        # Step 4: Prepare data
        gs_input_dir = workspace / "gaussian_splatting_input"
        prepare_colmap_data_for_gaussian_splatting(colmap_workspace, gs_input_dir)

        # Step 5: Train
        gs_output_dir = workspace / "gaussian_splatting_output"
        final_ply = train_gaussian_splat(gs_dir, gs_input_dir, gs_output_dir, args.iterations)

        # Step 6: Copy output
        output_path = Path(args.output)
        shutil.copy(final_ply, output_path)

        print(f"\n{'='*60}")
        print(f"SUCCESS! Gaussian Splat saved to: {output_path}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
