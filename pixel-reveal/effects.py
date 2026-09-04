"""
effects.py - High-Performance Particle Assembly & Reveal Animation Engine

Creates a 5-second 1080x1920 30FPS MP4 animation revealing an image through
thousands of glowing, scattered pixel particles locking into place.
"""

import cv2
import numpy as np


class ParticleRevealEngine:
    def __init__(
        self,
        image_path: str,
        canvas_width: int = 1080,
        canvas_height: int = 1920,
        block_size: int = 5,
        total_frames: int = 150,
        fps: int = 30,
        seed: int = 42,
    ):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.block_size = block_size
        self.total_frames = total_frames
        self.fps = fps
        self.seed = seed

        # Ensure 100% deterministic randomness
        np.random.seed(self.seed)

        # 1. Load image, preserve aspect ratio, center on canvas
        self._load_and_prepare_canvas(image_path)

        # 2. Deconstruct image into pixel blocks and assign particle dynamics
        self._create_particles()

        # 3. Progressive locked canvas cache for maximum rendering speed
        self.locked_canvas = np.zeros(
            (self.canvas_height, self.canvas_width, 3), dtype=np.uint8
        )
        self.last_locked_frame = -1

    def _load_and_prepare_canvas(self, image_path: str):
        """Loads source image, preserves aspect ratio, centers on 1080x1920 black canvas."""
        img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise FileNotFoundError(f"Could not load input image from: {image_path}")

        # Handle alpha channel if present
        has_alpha = img.ndim == 3 and img.shape[2] == 4
        if has_alpha:
            bgr = img[:, :, :3]
            alpha = img[:, :, 3]
        else:
            bgr = img if img.ndim == 3 else cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            alpha = np.full((bgr.shape[0], bgr.shape[1]), 255, dtype=np.uint8)

        orig_h, orig_w = bgr.shape[:2]

        # Calculate scale to fit inside 1080x1920 with balanced aesthetic margins
        max_target_w = int(self.canvas_width * 0.94)
        max_target_h = int(self.canvas_height * 0.90)

        scale = min(max_target_w / orig_w, max_target_h / orig_h)
        target_w = int(round(orig_w * scale))
        target_h = int(round(orig_h * scale))

        # Lanczos-4 interpolation for pristine image quality
        scaled_bgr = cv2.resize(
            bgr, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4
        )
        scaled_alpha = cv2.resize(
            alpha, (target_w, target_h), interpolation=cv2.INTER_NEAREST
        )

        # Center on canvas
        self.offset_x = (self.canvas_width - target_w) // 2
        self.offset_y = (self.canvas_height - target_h) // 2
        self.image_w = target_w
        self.image_h = target_h

        # The pristine 100% clean canvas (held from 4.5s to 5.0s)
        self.clean_canvas = np.zeros(
            (self.canvas_height, self.canvas_width, 3), dtype=np.uint8
        )

        # Alpha-aware placement
        alpha_mask = scaled_alpha > 20
        self.clean_canvas[
            self.offset_y : self.offset_y + target_h,
            self.offset_x : self.offset_x + target_w,
        ] = scaled_bgr

        self.scaled_bgr = scaled_bgr
        self.alpha_mask = alpha_mask

    def _create_particles(self):
        """Divides image into blocks and computes organic continuous cluster timeline."""
        bs = self.block_size
        blocks_x = (self.image_w + bs - 1) // bs
        blocks_y = (self.image_h + bs - 1) // bs

        dest_x_list = []
        dest_y_list = []
        color_list = []
        orig_w_list = []
        orig_h_list = []
        img_rel_x = []
        img_rel_y = []

        for by in range(blocks_y):
            y0 = by * bs
            y1 = min(y0 + bs, self.image_h)
            h = y1 - y0
            for bx in range(blocks_x):
                x0 = bx * bs
                x1 = min(x0 + bs, self.image_w)
                w = x1 - x0

                block_alpha = self.alpha_mask[y0:y1, x0:x1]
                if not np.any(block_alpha):
                    continue

                block_bgr = self.scaled_bgr[y0:y1, x0:x1]
                mean_col = block_bgr.mean(axis=(0, 1)).astype(np.uint8)

                # Skip completely black empty pixels
                if int(mean_col[0]) + int(mean_col[1]) + int(mean_col[2]) < 4:
                    continue

                canvas_x = self.offset_x + x0
                canvas_y = self.offset_y + y0

                dest_x_list.append(canvas_x)
                dest_y_list.append(canvas_y)
                color_list.append(mean_col)
                orig_w_list.append(w)
                orig_h_list.append(h)
                img_rel_x.append(x0 + w // 2)
                img_rel_y.append(y0 + h // 2)

        N = len(dest_x_list)
        self.num_particles = N

        self.dest_x = np.array(dest_x_list, dtype=np.int32)
        self.dest_y = np.array(dest_y_list, dtype=np.int32)
        self.colors = np.array(color_list, dtype=np.uint8)
        self.block_w = np.array(orig_w_list, dtype=np.int32)
        self.block_h = np.array(orig_h_list, dtype=np.int32)

        # Multi-scale Organic Noise Field for continuous organic cluster formation
        # Free from geometric Voronoi facets or straight line boundaries
        gh = max(16, self.image_h // 20)
        gw = max(16, self.image_w // 20)
        coarse_noise = np.random.uniform(0.0, 1.0, (gh, gw)).astype(np.float32)
        coarse_field = cv2.GaussianBlur(coarse_noise, (11, 11), 0)
        coarse_field = cv2.resize(coarse_field, (self.image_w, self.image_h))

        fh = max(32, self.image_h // 8)
        fw = max(32, self.image_w // 8)
        fine_noise = np.random.uniform(0.0, 1.0, (fh, fw)).astype(np.float32)
        fine_field = cv2.GaussianBlur(fine_noise, (9, 9), 0)
        fine_field = cv2.resize(fine_field, (self.image_w, self.image_h))

        # Sample noise field at particle locations
        rx = np.clip(np.array(img_rel_x), 0, self.image_w - 1)
        ry = np.clip(np.array(img_rel_y), 0, self.image_h - 1)
        c_val = coarse_field[ry, rx]
        f_val = fine_field[ry, rx]
        pixel_jitter = np.random.uniform(0.0, 1.0, N).astype(np.float32)

        # Organic activation score: 50% macro clusters, 30% micro clusters, 20% independent pixel jitter
        activation_score = 0.50 * c_val + 0.30 * f_val + 0.20 * pixel_jitter

        # Uniform percentile ranking in [0, 1]
        ranks = np.argsort(np.argsort(activation_score)) / float(N)

        # Map ranks precisely to the 5-phase timeline:
        # 0.0 - 0.7s (f0 - f21): ~1.8% tiny sparks randomly appearing across image
        # 0.7 - 2.0s (f21 - f60): ~25% active in organic soft clusters
        # 2.0 - 3.5s (f60 - f105): ~80% - 85% rapid assembly surge
        # 3.5 - 4.5s (f105 - f135): 100% locked, fine detail resolution and transition
        # 4.5 - 5.0s (f135 - f150): 100% pristine clean source image held steady
        act_frames = np.piecewise(
            ranks,
            [
                ranks < 0.018,
                (ranks >= 0.018) & (ranks < 0.25),
                (ranks >= 0.25) & (ranks < 0.82),
                ranks >= 0.82,
            ],
            [
                lambda r: (r / 0.018) * 20.0,
                lambda r: 20.0 + ((r - 0.018) / (0.25 - 0.018)) * (58.0 - 20.0),
                lambda r: 58.0 + ((r - 0.25) / (0.82 - 0.25)) * (98.0 - 58.0),
                lambda r: 98.0 + ((r - 0.82) / (1.00 - 0.82)) * (115.0 - 98.0),
            ],
        )

        self.act_frame = np.clip(
            act_frames + np.random.normal(0, 0.8, N), 0.0, 118.0
        ).astype(np.float32)

        # Flight duration: 15 to 24 frames (~0.5 - 0.8s)
        self.flight_dur = np.random.randint(15, 25, N).astype(np.float32)
        self.lock_frame = self.act_frame + self.flight_dur

        # Organic initial scatter offsets
        angles = np.random.uniform(0, 2 * np.pi, N)
        tier = np.random.choice([0, 1, 2], size=N, p=[0.50, 0.35, 0.15])
        radii = np.zeros(N, dtype=np.float32)
        radii[tier == 0] = np.random.uniform(20.0, 80.0, np.sum(tier == 0))
        radii[tier == 1] = np.random.uniform(80.0, 240.0, np.sum(tier == 1))
        radii[tier == 2] = np.random.uniform(240.0, 480.0, np.sum(tier == 2))

        self.start_x = (self.dest_x + radii * np.cos(angles)).astype(np.float32)
        self.start_y = (self.dest_y + radii * np.sin(angles)).astype(np.float32)

        # Transverse curvature curl wave
        curl_sign = np.random.choice([-1.0, 1.0], size=N)
        self.curl_amp = (
            np.random.uniform(10.0, 28.0, N) * curl_sign
        ).astype(np.float32)
        self.curl_nx = -np.sin(angles).astype(np.float32)
        self.curl_ny = np.cos(angles).astype(np.float32)

        self.flicker_phase = np.random.uniform(0, 2 * np.pi, N).astype(np.float32)
        self.size_scale = np.random.uniform(0.85, 1.25, N).astype(np.float32)

    def render_frame(self, frame_idx: int) -> np.ndarray:
        """
        Renders a single frame according to the animation timeline.
        Returns 1080x1920 BGR image.
        """
        # Phase 5: 4.5 – 5.0 sec (Frames 135 to 150)
        # Completely clean original image held steady
        if frame_idx >= 135:
            return self.clean_canvas.copy()

        # Update locked particles cache
        new_locked_mask = (self.lock_frame <= frame_idx) & (
            self.lock_frame > self.last_locked_frame
        )
        if np.any(new_locked_mask):
            lx = self.dest_x[new_locked_mask]
            ly = self.dest_y[new_locked_mask]
            lw = self.block_w[new_locked_mask]
            lh = self.block_h[new_locked_mask]
            lc = self.colors[new_locked_mask]

            for i in range(len(lx)):
                x, y, w, h = lx[i], ly[i], lw[i], lh[i]
                col = (int(lc[i, 0]), int(lc[i, 1]), int(lc[i, 2]))
                cv2.rectangle(
                    self.locked_canvas, (x, y), (x + w, y + h), col, -1
                )
            self.last_locked_frame = frame_idx

        # Start frame canvas with already locked particles
        frame_canvas = self.locked_canvas.copy()

        # Identify flying particles
        flying_mask = (self.act_frame <= frame_idx) & (self.lock_frame > frame_idx)
        flying_count = np.sum(flying_mask)

        if flying_count > 0:
            f_act = self.act_frame[flying_mask]
            f_dur = self.flight_dur[flying_mask]
            sx = self.start_x[flying_mask]
            sy = self.start_y[flying_mask]
            dx = self.dest_x[flying_mask].astype(np.float32)
            dy = self.dest_y[flying_mask].astype(np.float32)
            bw = self.block_w[flying_mask]
            bh = self.block_h[flying_mask]
            cols = self.colors[flying_mask].astype(np.float32)
            curl_amp = self.curl_amp[flying_mask]
            curl_nx = self.curl_nx[flying_mask]
            curl_ny = self.curl_ny[flying_mask]
            flicker_phase = self.flicker_phase[flying_mask]
            size_scale = self.size_scale[flying_mask]

            # Progress tau in [0, 1]
            tau = np.clip((frame_idx - f_act) / f_dur, 0.0, 1.0)

            # Smooth ease-out interpolation: t = 1 - (1 - tau)**3
            ease = 1.0 - (1.0 - tau) ** 3
            decay = 1.0 - ease

            # Organic curved flight path
            curl_wave = np.sin(np.pi * tau) * curl_amp
            cur_x = (dx + (sx - dx) * decay + curl_nx * curl_wave).astype(np.int32)
            cur_y = (dy + (sy - dy) * decay + curl_ny * curl_wave).astype(np.int32)

            # Trailing position (for subtle motion trail)
            tau_trail = np.maximum(0.0, tau - 0.22)
            ease_trail = 1.0 - (1.0 - tau_trail) ** 3
            decay_trail = 1.0 - ease_trail
            curl_trail = np.sin(np.pi * tau_trail) * curl_amp
            trail_x = (
                dx + (sx - dx) * decay_trail + curl_nx * curl_trail
            ).astype(np.int32)
            trail_y = (
                dy + (sy - dy) * decay_trail + curl_ny * curl_trail
            ).astype(np.int32)

            # Electrical brightness flicker
            flicker = 1.0 + 0.28 * np.sin(frame_idx * 1.35 + flicker_phase)
            cur_cols = np.clip(cols * flicker[:, None], 0, 255).astype(np.uint8)
            trail_cols = (cur_cols * 0.45).astype(np.uint8)

            # Block size variation during flight
            flight_scale = size_scale * (0.8 + 0.3 * np.sin(np.pi * tau))
            cur_w = np.maximum(2, np.round(bw * flight_scale)).astype(np.int32)
            cur_h = np.maximum(2, np.round(bh * flight_scale)).astype(np.int32)

            cw, ch = self.canvas_width, self.canvas_height

            # Draw subtle glowing trails for fast moving particles
            fast_movers = decay > 0.15
            for i in range(flying_count):
                if not fast_movers[i]:
                    continue
                tx = trail_x[i]
                ty = trail_y[i]
                if 0 <= tx < cw - 2 and 0 <= ty < ch - 2:
                    t_col = (
                        int(trail_cols[i, 0]),
                        int(trail_cols[i, 1]),
                        int(trail_cols[i, 2]),
                    )
                    cv2.rectangle(
                        frame_canvas, (tx, ty), (tx + 2, ty + 2), t_col, -1
                    )

            # Draw current flying particle blocks
            for i in range(flying_count):
                x = cur_x[i]
                y = cur_y[i]
                w = cur_w[i]
                h = cur_h[i]

                if x + w <= 0 or x >= cw or y + h <= 0 or y >= ch:
                    continue

                col = (int(cur_cols[i, 0]), int(cur_cols[i, 1]), int(cur_cols[i, 2]))
                cv2.rectangle(
                    frame_canvas,
                    (max(0, x), max(0, y)),
                    (min(cw - 1, x + w), min(ch - 1, y + h)),
                    col,
                    -1,
                )

        # Gaussian Bloom / Glow pass
        if frame_idx < 25:
            glow_intensity = 0.55  # Tiny glowing sparks stand out in the dark
        elif frame_idx < 90:
            glow_intensity = 0.38  # Vibrant colored clusters
        else:
            glow_intensity = 0.20  # Controlled fine refinement

        small = cv2.resize(frame_canvas, (270, 480), interpolation=cv2.INTER_LINEAR)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        _, bright_mask = cv2.threshold(gray, 110, 255, cv2.THRESH_BINARY)
        bright_area = cv2.bitwise_and(small, small, mask=bright_mask)
        blur = cv2.GaussianBlur(bright_area, (19, 19), 0)
        glow = cv2.resize(
            blur, (self.canvas_width, self.canvas_height), interpolation=cv2.INTER_LINEAR
        )
        frame_canvas = cv2.addWeighted(frame_canvas, 1.0, glow, glow_intensity, 0)

        # Phase 4: 3.5 – 4.5 sec (Frames 105 to 135)
        # Seamlessly transition from particle pixel-art grid to pristine original image
        if frame_idx >= 105:
            progress = (frame_idx - 105) / (135 - 105)
            progress = np.clip(progress, 0.0, 1.0)
            # Smoothstep ease-in-out
            smooth_blend = progress * progress * (3.0 - 2.0 * progress)

            frame_canvas = cv2.addWeighted(
                frame_canvas, 1.0 - smooth_blend, self.clean_canvas, smooth_blend, 0
            )

        return frame_canvas
