"""
VrchAudioMusic2EmotionNode – music emotion recognition using Music2Emotion.
Category: vrch.ai/audio
"""

import os, tempfile, json
import soundfile as sf
import torch
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# use the same category name used by existing audio nodes
CATEGORY = "vrch.ai/audio"

class VrchAudioMusic2EmotionNode:
    """
    Node for analyzing music emotion and mood from audio input.
    
    Inputs
    ------
    audio : AUDIO   (dict with keys `waveform` (tensor) & `sample_rate`)
    threshold : FLOAT (threshold for mood detection, default: 0.5)
    debug : BOOLEAN (enable debug logging, default: False)

    Outputs
    -------
    audio    : AUDIO  (passthrough)
    raw_data : JSON   (full model results as JSON object)
    moods    : STRING (formatted as "mood: probability" sorted high to low)
    valence  : FLOAT  (emotional valence: 1-9 scale)
    arousal  : FLOAT  (emotional arousal: 1-9 scale)
    """

    RETURN_TYPES = ("AUDIO", "JSON", "STRING", "FLOAT", "FLOAT")
    RETURN_NAMES = ("AUDIO", "RAW_DATA", "MOODS", "VALENCE", "AROUSAL")
    FUNCTION = "analyze"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def __init__(self):
        # Dynamic import with intelligent detection
        self.Music2emo = None
        self.model = None
        self.model_loaded = False
        
        try:
            # Try to import Music2emo dynamically
            from ..third_party.music2emotion.music2emo import Music2emo
            self.Music2emo = Music2emo
            
            # Try to initialize the model
            self.model = Music2emo()
            self.model_loaded = True
            print(f"[VrchAudioMusic2EmotionNode] Music2emo model loaded successfully")
            
        except ImportError as e:
            print(f"[VrchAudioMusic2EmotionNode] WARNING: Music2emotion module not found. "
                  f"This node requires the Music2emotion third-party GitHub repository to be installed. "
                  f"Please follow the installation instructions to download and set up the Music2emotion module. "
                  f"Import error: {str(e)}")
            self.model_loaded = False
            
        except Exception as e:
            print(f"[VrchAudioMusic2EmotionNode] WARNING: Failed to load Music2emo model: {str(e)}. "
                  f"Please ensure the Music2emotion dependencies are properly installed.")
            self.model_loaded = False

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "threshold": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                }),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    def _audio_to_tempfile(self, waveform, sr):
        """
        Convert tensor waveform to temporary WAV file.
        
        Args:
            waveform: Audio waveform tensor
            sr: Sample rate
            
        Returns:
            str: Path to temporary WAV file
        """
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            
            # Handle different waveform dimensions
            if waveform.dim() == 3:  # Batch dimension
                waveform = waveform[0]  # Take first batch item
            
            # Ensure waveform is 2D (channels, samples)
            if waveform.dim() == 1:
                waveform = waveform.unsqueeze(0)
            elif waveform.dim() > 2:
                waveform = waveform.squeeze()
                if waveform.dim() == 1:
                    waveform = waveform.unsqueeze(0)
            
            # Convert to numpy and transpose for soundfile (samples, channels)
            audio_np = waveform.cpu().numpy().T
            sf.write(tmp.name, audio_np, sr)
            return tmp.name
            
        except Exception as e:
            print(f"[VrchAudioMusic2EmotionNode] Error creating temp file: {str(e)}")
            raise

    def analyze(self, audio, threshold, debug):
        """
        Analyze emotional content of audio.
        
        Parameters
        ----------
        audio : dict
            Audio data containing "waveform" (tensor) and "sample_rate" (int)
        threshold : float
            Threshold for mood filtering (0.0-1.0)
        debug : bool
            Enable debug logging
        
        Returns
        -------
        tuple
            (audio_passthrough, raw_data_json, formatted_moods, valence, arousal)
        """
        if not self.model_loaded:
            error_msg = "Music2emo model not available. Please install the Music2emotion third-party module."
            raw_data = {"error": error_msg, "installation_required": True}
            return (audio, raw_data, f"Error: {error_msg}", 0.0, 0.0)
        
        try:
            # Extract audio data
            waveform = audio["waveform"]
            sample_rate = audio["sample_rate"]
            
            if debug:
                print(f"[VrchAudioMusic2EmotionNode] Debug: Processing audio with shape {waveform.shape}, sample_rate {sample_rate}")
                print(f"[VrchAudioMusic2EmotionNode] Debug: Threshold = {threshold}")
            
            # Handle tensor conversion and ensure proper dimensions
            if hasattr(waveform, 'numpy'):
                waveform_np = waveform.cpu().numpy()
            else:
                waveform_np = waveform
            
            # Handle different waveform dimensions properly
            # Expected: (samples,) for mono or (channels, samples) 
            if waveform_np.ndim == 3:  # (batch, channels, samples)
                waveform_np = waveform_np[0]  # Take first batch
                if debug:
                    print(f"[VrchAudioMusic2EmotionNode] Debug: Removed batch dimension, new shape: {waveform_np.shape}")
            
            if waveform_np.ndim == 2:  # (channels, samples)
                if waveform_np.shape[0] > 1:  # Multiple channels
                    waveform_np = waveform_np[0]  # Take first channel (mono)
                    if debug:
                        print(f"[VrchAudioMusic2EmotionNode] Debug: Converted to mono, new shape: {waveform_np.shape}")
                elif waveform_np.shape[0] == 1:  # Single channel with channel dimension
                    waveform_np = waveform_np[0]  # Remove channel dimension
                    if debug:
                        print(f"[VrchAudioMusic2EmotionNode] Debug: Removed single channel dimension, new shape: {waveform_np.shape}")
            
            # Now waveform_np should be 1D (samples,)
            if waveform_np.ndim != 1:
                raise ValueError(f"Unable to process audio with shape {waveform_np.shape}. Expected 1D array after processing.")
            
            # Create temporary WAV file
            wav_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    wav_path = temp_file.name
                
                # Write audio to temp file
                sf.write(wav_path, waveform_np, sample_rate)
                
                if debug:
                    print(f"[VrchAudioMusic2EmotionNode] Debug: Created temp file {wav_path}")
                
                # Run Music2emo prediction
                result = self.model.predict(wav_path, threshold=threshold)
                
                if debug:
                    print(f"[VrchAudioMusic2EmotionNode] Debug: Model result: {result}")
                
            finally:
                # Clean up temp file
                if wav_path and os.path.exists(wav_path):
                    try:
                        os.unlink(wav_path)
                        if debug:
                            print(f"[VrchAudioMusic2EmotionNode] Debug: Cleaned up temp file")
                    except OSError as e:
                        print(f"[VrchAudioMusic2EmotionNode] Warning: Could not remove temp file {wav_path}: {str(e)}")
            
            # Extract results with error handling
            predicted_moods = result.get("predicted_moods", [])
            mood_probs = result.get("mood_probs", {})
            valence = float(result.get("valence", 0.0))
            arousal = float(result.get("arousal", 0.0))
            
            # Format moods as "mood: probability" sorted by probability (high to low)
            if mood_probs and isinstance(mood_probs, dict):
                # Sort moods by probability in descending order
                sorted_moods = sorted(mood_probs.items(), key=lambda x: x[1], reverse=True)
                formatted_moods = []
                for mood, prob in sorted_moods:
                    if prob >= threshold:  # Only include moods above threshold
                        formatted_moods.append(f"{mood}: {prob:.4f}")
                moods_output = "\n".join(formatted_moods) if formatted_moods else "No moods detected"
                
                if debug:
                    print(f"[VrchAudioMusic2EmotionNode] Debug: Formatted moods: {moods_output}")
            else:
                # Fallback to predicted_moods list if mood_probs not available
                moods_output = ", ".join(predicted_moods) if predicted_moods else "No moods detected"
                if debug:
                    print(f"[VrchAudioMusic2EmotionNode] Debug: Using fallback mood format")
            
            # Ensure values are in expected range
            valence = max(0.0, min(9.0, valence))
            arousal = max(0.0, min(9.0, arousal))
            
            # Format mood_probs to 4 decimal places for consistency
            formatted_mood_probs = {mood: round(prob, 4) for mood, prob in mood_probs.items()} if mood_probs else {}
            
            # Create raw data JSON output
            raw_data = {
                "predicted_moods": predicted_moods,
                "mood_probs": formatted_mood_probs,
                "valence": valence,
                "arousal": arousal,
                "threshold_used": threshold,
                "analysis_success": True
            }
            
            if debug:
                print(f"[VrchAudioMusic2EmotionNode] Debug: Final outputs - Valence: {valence}, Arousal: {arousal}")
            
            return (audio, raw_data, moods_output, valence, arousal)
            
        except Exception as e:
            error_msg = f"Error during analysis: {str(e)}"
            print(f"[VrchAudioMusic2EmotionNode] {error_msg}")
            raw_data = {
                "error": error_msg,
                "analysis_success": False,
                "threshold_used": threshold
            }
            return (audio, raw_data, f"Error: {str(e)}", 0.0, 0.0)


class VrchAudioEmotionVisualizerNode:
    """
    Visualize emotion data from VrchAudioMusic2EmotionNode RAW_DATA.

    Generates two images:
    - Moods radar chart (top-k moods by probability)
    - Valence/Arousal quadrant plot
    """

    CATEGORY = CATEGORY
    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("MOODS_RADAR_IMAGE", "VALENCE_AROUSAL_IMAGE")
    FUNCTION = "visualize_emotion"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # shared
                "raw_data": ("JSON",),
                "image_width": ("INT", {"default": 512, "min": 256, "max": 2048, "step": 32}),
                "image_height": ("INT", {"default": 512, "min": 256, "max": 2048, "step": 32}),
                "background_color": ("STRING", {"default": "#111111"}),

                # radar-specific
                "radar_top_k": ("INT", {"default": 6, "min": 3, "max": 12, "step": 1}),
                "radar_normalize": ("BOOLEAN", {"default": False}),
                "radar_show_labels": ("BOOLEAN", {"default": True}),
                "radar_theme": ([
                    "custom", "pastel", "ocean", "sunset", "forest", "neon", "mono-blue", "mono-gray"
                ], {"default": "custom"}),
                "radar_fill_color": ("STRING", {"default": "#3FA9F5"}),
                "radar_outline_color": ("STRING", {"default": "#7FD1FF"}),
                "radar_grid_color": ("STRING", {"default": "#444444"}),
                "radar_label_color": ("STRING", {"default": "#CCCCCC"}),

                # valence/arousal-specific
                "va_show_background": ("BOOLEAN", {"default": False}),
                "va_background_theme": ([
                    "pastel", "ocean", "sunset", "forest", "neon", "mono-blue", "mono-gray"
                ], {"default": "pastel"}),
                "va_background_opacity": ("FLOAT", {"default": 0.15, "min": 0.0, "max": 0.5, "step": 0.01}),
                "va_grid_color": ("STRING", {"default": "#444444"}),
                "va_label_color": ("STRING", {"default": "#CCCCCC"}),
                "va_point_color": ("STRING", {"default": "#FFCC00"}),
                "va_show_value_labels": ("BOOLEAN", {"default": True}),

                # keep debug as the last option always
                "debug": ("BOOLEAN", {"default": False}),
            },
        }

    # --- Utility color helpers ---
    def hex_to_rgb(self, hex_color: str):
        try:
            s = hex_color.strip().lstrip('#')
            if len(s) == 6:
                return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))
            if len(s) == 3:
                return tuple(int(s[i]*2, 16) for i in range(3))
        except Exception:
            pass
        return (17, 17, 17)

    def _apply_radar_theme(self, theme: str):
        """Return a dict of colors for radar when theme != custom."""
        presets = {
            "pastel": {"fill": "#7FD1FF", "outline": "#3FA9F5", "grid": "#444444", "label": "#CCCCCC"},
            "ocean": {"fill": "#5FD1C9", "outline": "#2BA6B9", "grid": "#4A4F59", "label": "#BFD9E6"},
            "sunset": {"fill": "#FFB385", "outline": "#FF7F50", "grid": "#54433A", "label": "#FFD8C2"},
            "forest": {"fill": "#8CCB9B", "outline": "#5E8D6A", "grid": "#3F4A42", "label": "#CFE6D5"},
            "neon": {"fill": "#39FF14", "outline": "#00E5FF", "grid": "#404040", "label": "#EAEAEA"},
            "mono-blue": {"fill": "#6EC1FF", "outline": "#1E90FF", "grid": "#404E5A", "label": "#C8D9EA"},
            "mono-gray": {"fill": "#BDBDBD", "outline": "#E0E0E0", "grid": "#4A4A4A", "label": "#DDDDDD"},
        }
        return presets.get(theme, presets["pastel"]) if theme != "custom" else None

    def _va_theme_colors(self, theme: str):
        """Return 4 RGB tuples for quadrants background colors."""
        themes = {
            "pastel": ("#FFC9DE", "#C9E8FF", "#CFF6D6", "#FFF2B3"),
            "ocean": ("#A7D8FF", "#9EE0E8", "#A8F0D1", "#B8C9FF"),
            "sunset": ("#FFB085", "#FF9AA2", "#FFD1A6", "#FFE29A"),
            "forest": ("#CDE7BE", "#B7D7A8", "#DDE6C7", "#A9CDB5"),
            "neon": ("#FF6EFF", "#39FF14", "#00FFFF", "#FFFF00"),
            "mono-blue": ("#6EC1FF", "#6EC1FF", "#6EC1FF", "#6EC1FF"),
            "mono-gray": ("#CCCCCC", "#CCCCCC", "#CCCCCC", "#CCCCCC"),
        }
        hexes = themes.get(theme, themes["pastel"])
        return tuple(self.hex_to_rgb(h) for h in hexes)  # type: ignore

    # --- Drawing helpers ---
    def _get_font(self, size:int):
        """Get a truetype font if possible; fallback to default PIL font."""
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size=size)
        except Exception:
            try:
                return ImageFont.truetype("Arial.ttf", size=size)
            except Exception:
                return ImageFont.load_default()

    def _text_size(self, draw: ImageDraw.ImageDraw, text: str, font):
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            return font.getsize(text)

    def _text_with_outline(self, draw: ImageDraw.ImageDraw, xy, text, fill, font, outline=(0,0,0)):
        x, y = xy
        # simple 1px outline around
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            draw.text((x+dx, y+dy), text, fill=outline, font=font)
        draw.text((x, y), text, fill=fill, font=font)

    def _draw_radar_chart(self, draw: ImageDraw.ImageDraw, size, bg_rgb, 
                           moods: list, normalize: bool,
                           show_labels: bool, colors: dict, label_font, value_font, debug=False):
        w, h = size
        cx, cy = w // 2, h // 2
        radius = int(min(w, h) * 0.40)

        # Prepare values
        labels = [str(m[0]) for m in moods]
        raw_values = [float(m[1]) for m in moods]
        values = list(raw_values)
        if normalize and len(values) > 0:
            maxv = max(values)
            if maxv > 0:
                values = [v / maxv for v in values]
        n = max(1, len(values))

        grid_color = self.hex_to_rgb(colors["grid"])  # type: ignore
        label_color = self.hex_to_rgb(colors["label"])  # type: ignore
        outline_color = self.hex_to_rgb(colors["outline"])  # type: ignore
        fill_color = self.hex_to_rgb(colors["fill"])  # type: ignore

        # Draw grid: concentric polygons (or circles for simplicity)
        rings = 4
        for i in range(1, rings + 1):
            r = int(radius * i / rings)
            bbox = [cx - r, cy - r, cx + r, cy + r]
            draw.ellipse(bbox, outline=grid_color, width=1)

        # Draw spokes
        if n > 1:
            for i in range(n):
                angle = 2 * np.pi * i / n - np.pi / 2
                x = cx + int(radius * np.cos(angle))
                y = cy + int(radius * np.sin(angle))
                draw.line([(cx, cy), (x, y)], fill=grid_color, width=1)

        # Compute polygon points
        points = []
        for i, v in enumerate(values):
            v_clamped = max(0.0, min(1.0, v))
            angle = 2 * np.pi * i / max(1, n) - np.pi / 2
            r = int(v_clamped * radius)
            x = cx + int(r * np.cos(angle))
            y = cy + int(r * np.sin(angle))
            points.append((x, y))

        # Labels & numeric values
        if show_labels and n > 0:
            label_radius = radius + int(min(w, h) * 0.03)
            value_offset = int(min(w, h) * 0.02)
            for i, lab in enumerate(labels):
                angle = 2 * np.pi * i / max(1, n) - np.pi / 2
                lx = cx + int(label_radius * np.cos(angle))
                ly = cy + int(label_radius * np.sin(angle))
                text = lab.upper()
                tw, th = self._text_size(draw, text, label_font)
                self._text_with_outline(draw, (lx - tw // 2, ly - th // 2), text, label_color, label_font)

                # numeric value near vertex point (use raw probability, not normalized)
                vx, vy = points[i]
                vx += int(value_offset * np.cos(angle))
                vy += int(value_offset * np.sin(angle))
                v_text = f"{raw_values[i]:.2f}"
                v_tw, v_th = self._text_size(draw, v_text, value_font)
                self._text_with_outline(draw, (vx - v_tw // 2, vy - v_th // 2), v_text, label_color, value_font)

        return points, (outline_color, fill_color)

    def _draw_va_plot(self, base_img: Image.Image, draw: ImageDraw.ImageDraw, size,
                      bg_rgb, valence, arousal, show_bg, theme, opacity,
                      grid_color_hex, label_color_hex, point_color_hex,
                      show_value_labels, label_font, tick_font, debug=False):
        w, h = size
        # Plot margins
        margin = int(min(w, h) * 0.10)
        left, top = margin, margin
        right, bottom = w - margin, h - margin
        plot_w = right - left
        plot_h = bottom - top

        # Optional themed quadrant backgrounds
        if show_bg:
            overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            o = ImageDraw.Draw(overlay)
            q_colors = self._va_theme_colors(theme)
            alpha = int(max(0.0, min(1.0, opacity)) * 255)
            # Quadrants: 
            # Q1 (top-right), Q2 (top-left), Q3 (bottom-left), Q4 (bottom-right)
            mid_x = left + plot_w // 2
            mid_y = top + plot_h // 2
            # Top-left (Q2)
            o.rectangle([left, top, mid_x, mid_y], fill=(*q_colors[1], alpha))
            # Top-right (Q1)
            o.rectangle([mid_x, top, right, mid_y], fill=(*q_colors[0], alpha))
            # Bottom-left (Q3)
            o.rectangle([left, mid_y, mid_x, bottom], fill=(*q_colors[2], alpha))
            # Bottom-right (Q4)
            o.rectangle([mid_x, mid_y, right, bottom], fill=(*q_colors[3], alpha))
            base_img.paste(overlay, (0, 0), overlay)

        # Grid and axes
        grid_color = self.hex_to_rgb(grid_color_hex)
        label_color = self.hex_to_rgb(label_color_hex)
        # Border
        draw.rectangle([left, top, right, bottom], outline=grid_color, width=1)
        # Mid axes at 4.5
        mid_val = left + int((4.5 / 9.0) * plot_w)
        mid_aro = bottom - int((4.5 / 9.0) * plot_h)
        draw.line([(mid_val, top), (mid_val, bottom)], fill=grid_color, width=1)
        draw.line([(left, mid_aro), (right, mid_aro)], fill=grid_color, width=1)
        # Additional grid lines at 0, 3, 6, 9 (0 and 9 coincide with border)
        for t in [3.0, 6.0]:
            x = left + int((t / 9.0) * plot_w)
            y = bottom - int((t / 9.0) * plot_h)
            draw.line([(x, top), (x, bottom)], fill=grid_color, width=1)
            draw.line([(left, y), (right, y)], fill=grid_color, width=1)

        # Axis labels (ticks and titles)
        def txt(xy, t, f):
            self._text_with_outline(draw, xy, t, label_color, f)

        txt((left, bottom + 2), "0", tick_font)
        txt((left + plot_w - 10, bottom + 2), "9", tick_font)
        txt((left - 10, top), "9", tick_font)
        txt((left - 10, bottom - 10), "0", tick_font)
        # titles
        txt((left + plot_w // 2 - 30, bottom + 6), "VALENCE", label_font)
        txt((left - 60, top + plot_h // 2 - 12), "AROUSAL", label_font)

        # Plot point
        try:
            vx = float(valence)
            vy = float(arousal)
            vx = max(0.0, min(9.0, vx))
            vy = max(0.0, min(9.0, vy))
            px = left + int((vx / 9.0) * plot_w)
            py = bottom - int((vy / 9.0) * plot_h)
            pr = max(3, int(min(w, h) * 0.012))
            point_color = self.hex_to_rgb(point_color_hex)
            draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=point_color, outline=(255, 255, 255))
            if show_value_labels:
                val_text = f"V: {vx:.2f}  A: {vy:.2f}"
                tw, th = self._text_size(draw, val_text, tick_font)
                off = int(min(w, h) * 0.02)
                self._text_with_outline(draw, (px + off, py - th - off), val_text, label_color, tick_font)
        except Exception:
            # If invalid, write N/A
            self._text_with_outline(draw, (left + 6, top + 6), "N/A", label_color, tick_font)

    def visualize_emotion(self, raw_data,
                          image_width=512, image_height=512,
                          background_color="#111111",
                          radar_top_k=6, radar_normalize=False, radar_show_labels=True,
                          radar_theme="custom",
                          radar_fill_color="#3FA9F5", radar_outline_color="#7FD1FF",
                          radar_grid_color="#444444", radar_label_color="#CCCCCC",
                          va_show_background=False, va_background_theme="pastel",
                          va_background_opacity=0.15,
                          va_grid_color="#444444", va_label_color="#CCCCCC", va_point_color="#FFCC00",
                          va_show_value_labels=True,
                          debug=False):
        """Generate radar and VA images from emotion RAW_DATA."""

        # Parse raw_data (str or dict)
        mood_probs = {}
        valence = None
        arousal = None
        try:
            data = json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            if isinstance(data, dict):
                mood_probs = data.get("mood_probs", {}) or {}
                valence = data.get("valence", None)
                arousal = data.get("arousal", None)
        except Exception as e:
            if debug:
                print(f"[VrchAudioEmotionVisualizerNode] Failed to parse raw_data: {e}")

        # Prepare base images
        bg_rgb = self.hex_to_rgb(background_color)

        # Font sizes
        base = min(image_width, image_height)
        radar_label_font = self._get_font(max(12, int(base * 0.045)))
        radar_value_font = self._get_font(max(12, int(base * 0.035)))
        va_label_font = self._get_font(max(12, int(base * 0.045)))
        va_tick_font = self._get_font(max(12, int(base * 0.035)))

        # Radar image
        radar_img = Image.new('RGB', (image_width, image_height), bg_rgb)
        r_draw = ImageDraw.Draw(radar_img)

        # Resolve radar theme colors
        theme_colors = self._apply_radar_theme(radar_theme)
        radar_colors = {
            "fill": radar_fill_color,
            "outline": radar_outline_color,
            "grid": radar_grid_color,
            "label": radar_label_color,
        }
        if theme_colors:
            radar_colors = theme_colors

        # Build mood list sorted by prob desc
        moods_sorted = []
        if isinstance(mood_probs, dict) and mood_probs:
            try:
                moods_sorted = sorted(((k, float(v)) for k, v in mood_probs.items()), key=lambda x: x[1], reverse=True)
            except Exception:
                # If any value not castable to float, skip sorting by value
                moods_sorted = [(k, v) for k, v in mood_probs.items()]
        # select top-k
        moods_sel = moods_sorted[:max(1, radar_top_k)] if moods_sorted else []

        # Draw radar
        polygon_points, of_colors = self._draw_radar_chart(
            r_draw, (image_width, image_height), bg_rgb,
            moods_sel, radar_normalize, radar_show_labels, radar_colors,
            radar_label_font, radar_value_font, debug
        )
        # Composite overlay for polygon (created inside helper)
        if polygon_points and len(polygon_points) >= 3:
            # Recreate overlay with same points to composite (since draw helper cannot paste by itself)
            overlay = Image.new('RGBA', (image_width, image_height), (0, 0, 0, 0))
            o_draw = ImageDraw.Draw(overlay)
            outline_color, fill_color = of_colors
            o_draw.polygon(polygon_points, fill=(fill_color[0], fill_color[1], fill_color[2], 80))
            o_draw.line(polygon_points + [polygon_points[0]], fill=(outline_color[0], outline_color[1], outline_color[2], 200), width=2)
            radar_img.paste(overlay, (0, 0), overlay)

        # Fallback text when no mood data
        if not moods_sel:
            self._text_with_outline(r_draw, (10, 10), "No mood data".upper(), self.hex_to_rgb(radar_colors["label"]), radar_label_font)

        # VA image
        va_img = Image.new('RGB', (image_width, image_height), bg_rgb)
        v_draw = ImageDraw.Draw(va_img)
        self._draw_va_plot(
            va_img, v_draw, (image_width, image_height), bg_rgb,
            valence, arousal, va_show_background, va_background_theme, va_background_opacity,
            va_grid_color, va_label_color, va_point_color,
            va_show_value_labels, va_label_font, va_tick_font, debug
        )

        # Convert to tensors (ComfyUI IMAGE)
        radar_array = np.array(radar_img).astype(np.float32) / 255.0
        radar_tensor = torch.from_numpy(radar_array)[None,]
        va_array = np.array(va_img).astype(np.float32) / 255.0
        va_tensor = torch.from_numpy(va_array)[None,]
        return (radar_tensor, va_tensor)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Hash raw_data + key visual params for refresh
        try:
            m = __import__("hashlib").sha256()
            raw_data = kwargs.get("raw_data", "")
            if isinstance(raw_data, str):
                m.update(raw_data.encode("utf-8"))
            else:
                m.update(json.dumps(raw_data, sort_keys=True).encode("utf-8"))

            keys = [
                "image_width", "image_height", "background_color",
                "radar_top_k", "radar_normalize", "radar_show_labels", "radar_theme",
                "radar_fill_color", "radar_outline_color", "radar_grid_color", "radar_label_color",
                "va_show_background", "va_background_theme", "va_background_opacity",
                "va_grid_color", "va_label_color", "va_point_color", "va_show_value_labels",
            ]
            for k in keys:
                if k in kwargs and kwargs[k] is not None:
                    m.update(str(kwargs[k]).encode("utf-8"))
            return m.hexdigest()
        except Exception:
            return float("NaN")
