#!/usr/bin/env python3
"""
main.py - Entry point for Pixel Reveal / Particle Assembly Animation

Creates a 5-second 1080x1920 30FPS MP4 animation revealing an image through
thousands of glowing, scattered pixel particles locking into place.
"""

import argparse
import os
import sys
from pathlib import Path
import cv2

# Ensure effects module can be imported relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

try:
    from effects import ParticleRevealEngine
except ImportError:
    # If called from a different working directory
    from pixel_reveal.effects import ParticleRevealEngine


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a 5-second Pixel Reveal animation from any input image."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=None,
        help="Path to the input image (default: input/krishna.png)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Path to the output MP4 file (default: output/krishna_pixel_reveal.mp4)",
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=float,
        default=5.0,
        help="Animation duration in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Frames per second (default: 30)",
    )
    parser.add_argument(
        "--block-size",
        "-b",
        type=int,
        default=5,
        help="Base particle block size in pixels (default: 5)",
    )
    parser.add_argument(
        "--seed",
        "-s",
        type=int,
        default=42,
        help="Random seed for deterministic animation (default: 42)",
    )
    return parser.parse_args()


def resolve_paths(input_arg, output_arg):
    # Resolve input path: check relative to CWD, then relative to SCRIPT_DIR
    if input_arg:
        input_path = Path(input_arg)
        if not input_path.exists() and (SCRIPT_DIR / input_arg).exists():
            input_path = SCRIPT_DIR / input_arg
    else:
        # Default input
        default_rel = Path("input/krishna.png")
        if default_rel.exists():
            input_path = default_rel
        elif (SCRIPT_DIR / "input/krishna.png").exists():
            input_path = SCRIPT_DIR / "input/krishna.png"
        else:
            input_path = default_rel

    # Resolve output path
    if output_arg:
        output_path = Path(output_arg)
    else:
        # Default output
        output_path = Path("output/krishna_pixel_reveal.mp4")

    # Ensure parent output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return str(input_path), str(output_path)


def create_video_writer(output_path: str, fps: int, width: int = 1080, height: int = 1920):
    """
    Creates the best available video writer:
    Tries imageio with imageio-ffmpeg first for optimal libx264 compatibility,
    and falls back to OpenCV VideoWriter if needed.
    """
    use_imageio = False
    try:
        import imageio
        writer = imageio.get_writer(
            output_path,
            fps=fps,
            codec="libx264",
            pixelformat="yuv420p",
            quality=9,
            macro_block_size=None,
        )
        use_imageio = True
        return writer, use_imageio
    except Exception:
        pass

    # OpenCV VideoWriter fallback
    # Try avc1 (H.264), then mp4v
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    cv_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    if not cv_writer.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        cv_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    return cv_writer, False


def main():
    args = parse_args()
    input_path, output_path = resolve_paths(args.input, args.output)

    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    total_frames = int(round(args.duration * args.fps))
    width, height = 1080, 1920

    # Initialize effect engine
    engine = ParticleRevealEngine(
        image_path=input_path,
        canvas_width=width,
        canvas_height=height,
        block_size=args.block_size,
        total_frames=total_frames,
        fps=args.fps,
        seed=args.seed,
    )

    # Initialize video writer
    writer, is_imageio = create_video_writer(output_path, args.fps, width, height)

    try:
        for frame_idx in range(total_frames):
            print(f"Rendering frame {frame_idx + 1}/{total_frames}", flush=True)

            frame = engine.render_frame(frame_idx)

            if is_imageio:
                # imageio expects RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                writer.append_data(frame_rgb)
            else:
                writer.write(frame)
    finally:
        if is_imageio:
            writer.close()
        else:
            writer.release()

    # Success output matching exact user specification
    print(f"\nPixel reveal animation created successfully:\n{output_path}")


if __name__ == "__main__":
    main()
