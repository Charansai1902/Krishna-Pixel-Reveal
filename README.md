# ✨ Krishna Pixel Reveal Animation

A Python-based **pixel particle reveal animation** that reconstructs digital artwork using randomized colored particles, smooth transitions, and progressive image assembly.

The project transforms a static image into a cinematic **5-second pixel reconstruction animation**, where thousands of particles gradually assemble to reveal the final artwork.

## 🎬 Animation Concept

The animation follows a progressive reconstruction sequence:

**Black Screen → Scattered Pixels → Particle Formation → Pixelated Artwork → Full Image Reveal**

Each particle takes its color directly from the original image and gradually moves toward its correct position, creating the effect of an image being digitally reconstructed.

## ✨ Features

- 🎨 Source-image-based particle colors
- 🧩 Randomized pixel reconstruction
- ✨ Glowing particle effects
- 🎞️ Smooth ease-out particle movement
- 🔲 Pixel-art intermediate stages
- 🖼️ Exact original-image final reveal
- 📱 1080 × 1920 vertical video output
- 🎥 30 FPS MP4 rendering
- ⏱️ 5-second animation
- 🎲 Deterministic particle generation
- ⚡ Built entirely with Python

## 🛠️ Technologies Used

- Python 3
- OpenCV
- NumPy
- Pillow
- ImageIO
- ImageIO-FFmpeg

## 📂 Project Structure

```text
Krishna-Pixel-Reveal/
│
├── input/
│   └── source image
│
├── output/
│   └── krishna_pixel_reveal.mp4
│
├── main.py
├── .gitignore
└── README.md
```

## ⚙️ How It Works

The program first loads the source artwork and preserves its original aspect ratio.

It then divides the visible image into thousands of small pixel blocks. Each block stores information such as:

- Original position
- Source color
- Starting position
- Activation frame
- Particle size
- Movement timing

The particles initially appear at randomized positions and gradually move toward their correct coordinates using smooth easing.

As the animation progresses, more particles lock into place until the complete source image is reconstructed.

## 🎞️ Animation Timeline

| Time | Stage |
|------|------|
| 0.0 – 0.7s | Sparse particles appear |
| 0.7 – 2.0s | Pixel clusters begin forming |
| 2.0 – 3.5s | Rapid image reconstruction |
| 3.5 – 4.5s | Fine details resolve |
| 4.5 – 5.0s | Complete artwork reveal |

## 🚀 Run Locally

Clone the repository:

```bash
git clone https://github.com/Charansai1902/Krishna-Pixel-Reveal.git
```

Enter the project:

```bash
cd Krishna-Pixel-Reveal
```

Install dependencies:

```bash
pip3 install opencv-python numpy pillow imageio imageio-ffmpeg
```

Run the animation:

```bash
python3 main.py
```

The generated video will be available at:

```text
output/krishna_pixel_reveal.mp4
```

## 🎥 Output Specifications

```text
Resolution : 1080 × 1920
Aspect     : 9:16
Frame Rate : 30 FPS
Duration   : 5 seconds
Format     : MP4
```

Designed for vertical content such as **Instagram Reels, YouTube Shorts, and other short-form visual content**.

## 💡 Technical Idea

Instead of applying a traditional opacity or dissolve transition, this project treats the image as a collection of independently animated pixel particles.

Each particle ultimately converges on its corresponding source-image coordinate, producing a computational **digital reconstruction effect**.

## 👨‍💻 Author

**Charan Sai Masagani**

Built as a creative Python computer-graphics experiment combining image processing, particle animation, and procedural visual effects.

---

⭐ If you like the project, consider starring the repository.
