"""
VrchAudioMusic2EmotionNode – music emotion recognition using Music2Emotion.
Category: vrch.ai/audio
"""

import os, tempfile, json, random
from collections import OrderedDict
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
            
            # Apply threshold filter to mood_probs and predicted_moods for raw_data
            filtered_mood_probs = {}
            if mood_probs and isinstance(mood_probs, dict):
                try:
                    filtered_mood_probs = {
                        str(mood): float(prob) for mood, prob in mood_probs.items() if float(prob) >= float(threshold)
                    }
                except Exception:
                    # If any casting fails, skip that entry
                    filtered_mood_probs = {}

            # Round to 4 decimals and sort by probability desc for consistency
            if filtered_mood_probs:
                sorted_pairs = sorted(filtered_mood_probs.items(), key=lambda x: x[1], reverse=True)
                formatted_mood_probs = OrderedDict((m, round(float(p), 4)) for m, p in sorted_pairs)
            else:
                formatted_mood_probs = {}

            # Build moods list sorted by probability desc for raw_data
            if filtered_mood_probs:
                predicted_moods_sorted = [m for m, _ in sorted(filtered_mood_probs.items(), key=lambda x: x[1], reverse=True)]
            else:
                # Fallback: keep original order when backend provides no probs
                predicted_moods_sorted = predicted_moods or []

            # Create raw data JSON output
            raw_data = {
                # Only return threshold-filtered fields (sorted high->low)
                "predicted_moods": predicted_moods_sorted,
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

    Generates three images:
    - Moods radar chart (top-k moods by probability)
    - Moods word cloud (top-k moods by probability)
    - Valence/Arousal quadrant plot
    """

    CATEGORY = CATEGORY
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("MOODS_RADAR_IMAGE", "MOODS_WORDCLOUD_IMAGE", "VALENCE_AROUSAL_IMAGE")
    FUNCTION = "visualize_emotion"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # shared
                "raw_data": ("JSON",),
                "image_width": ("INT", {"default": 640, "min": 256, "max": 2048, "step": 32}),
                "image_height": ("INT", {"default": 480, "min": 256, "max": 2048, "step": 32}),
                "background_color": ("STRING", {"default": "#111111"}),
                "font_color": ("STRING", {"default": "#EFEFEF"}),
                "font_size": ([
                    "extra small", "small", "medium", "large", "extra large"
                ], {"default": "medium"}),

                # radar settings (theme first)
                "radar_theme": ([
                    "pastel", "ocean", "sunset", "forest", "neon", "mono-blue", "mono-gray"
                ], {"default": "pastel"}),
                "radar_top_k": ("INT", {"default": 6, "min": 3, "max": 12, "step": 1}),
                "radar_normalize": ("BOOLEAN", {"default": False}),
                "radar_show_labels": ("BOOLEAN", {"default": True}),
                "radar_show_values": ("BOOLEAN", {"default": True}),

                # wordcloud settings (theme first)
                "wordcloud_theme": ([
                    "pastel", "ocean", "sunset", "forest", "neon", "mono-blue", "mono-gray"
                ], {"default": "pastel"}),
                # layout option placed right after theme for better UX
                "wordcloud_layout": ([
                    "center_spiral", "archimedean_spiral_desc", "concentric_rings", "sequential_flow"
                ], {"default": "sequential_flow"}),
                "wordcloud_top_k": ("INT", {"default": 12, "min": 3, "max": 64, "step": 1}),
                "wordcloud_use_opacity": ("BOOLEAN", {"default": True}),
                # size scaling intensity (probability -> font size mapping)
                "wordcloud_size_scale": (["low", "medium", "high"], {"default": "high"}),

                # valence/arousal settings (theme first)
                "va_theme": ([
                    "no_background", "pastel", "ocean", "sunset", "forest", "neon", "mono-blue", "mono-gray"
                ], {"default": "no_background"}),
                "va_show_minor_gridlines": ("BOOLEAN", {"default": True}),
                "va_show_mood_labels": ("BOOLEAN", {"default": False}),
                "va_show_axis_labels": ("BOOLEAN", {"default": True}),
                "va_show_value_labels": ("BOOLEAN", {"default": True}),
                "va_point_color": ("STRING", {"default": "#FFCC00"}),

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
        """Return a dict of colors for radar."""
        presets = {
            "pastel": {"fill": "#7FD1FF", "outline": "#3FA9F5", "grid": "#444444"},
            "ocean": {"fill": "#5FD1C9", "outline": "#2BA6B9", "grid": "#4A4F59"},
            "sunset": {"fill": "#FFB385", "outline": "#FF7F50", "grid": "#54433A"},
            "forest": {"fill": "#8CCB9B", "outline": "#5E8D6A", "grid": "#3F4A42"},
            "neon": {"fill": "#39FF14", "outline": "#00E5FF", "grid": "#404040"},
            "mono-blue": {"fill": "#6EC1FF", "outline": "#1E90FF", "grid": "#404E5A"},
            "mono-gray": {"fill": "#BDBDBD", "outline": "#E0E0E0", "grid": "#4A4A4A"},
        }
        return presets.get(theme, presets["pastel"])  # default to pastel

    def _apply_wordcloud_theme(self, theme: str):
        """Return a palette (list of hex colors) for wordcloud words."""
        palettes = {
            "pastel": ["#7FD1FF", "#F7A6B8", "#8CCB9B", "#FFD38C", "#C6A8FF"],
            "ocean": ["#2BA6B9", "#5FD1C9", "#1E90FF", "#6EC1FF", "#00CED1"],
            "sunset": ["#FF7F50", "#FFB385", "#FFD38C", "#FF6F91", "#FFA07A"],
            "forest": ["#5E8D6A", "#8CCB9B", "#A3D9A5", "#6B8E23", "#3CB371"],
            "neon": ["#39FF14", "#00E5FF", "#FF00FF", "#FFFF00", "#00FF7F"],
            "mono-blue": ["#1E90FF", "#6EC1FF", "#A7D8FF", "#3FA9F5", "#0F6ABF"],
            "mono-gray": ["#B0B0B0", "#D0D0D0", "#9AA0A6", "#ECECEC", "#7A7A7A"],
        }
        return palettes.get(theme, palettes["pastel"])

    def _va_theme_config(self, theme: str):
        """Return VA theme config: (quadrant_colors or None, grid_hex)."""
        if theme == "no_background":
            return None, "#444444"
        quadrant_hex = {
            "pastel": ("#FFC9DE", "#C9E8FF", "#CFF6D6", "#FFF2B3"),
            "ocean": ("#A7D8FF", "#9EE0E8", "#A8F0D1", "#B8C9FF"),
            "sunset": ("#FFB085", "#FF9AA2", "#FFD1A6", "#FFE29A"),
            "forest": ("#CDE7BE", "#B7D7A8", "#DDE6C7", "#A9CDB5"),
            "neon": ("#FF6EFF", "#39FF14", "#00FFFF", "#FFFF00"),
            "mono-blue": ("#6EC1FF", "#6EC1FF", "#6EC1FF", "#6EC1FF"),
            "mono-gray": ("#CCCCCC", "#CCCCCC", "#CCCCCC", "#CCCCCC"),
        }.get(theme, ("#FFC9DE", "#C9E8FF", "#CFF6D6", "#FFF2B3"))
        return tuple(self.hex_to_rgb(h) for h in quadrant_hex), "#444444"

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
                           show_labels: bool, show_values: bool,
                           colors: dict, label_font, value_font, font_color_rgb, debug=False):
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
        label_color = font_color_rgb
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

        # Labels & numeric values with smart placement (independently controlled)
        if n > 0 and (show_labels or show_values):
            base_unit = min(w, h)
            outside_offset = int(base_unit * 0.06)
            inside_offset = int(base_unit * 0.04)
            value_offset_out = int(base_unit * 0.02)
            value_offset_in = int(base_unit * 0.02)
            for i, lab in enumerate(labels):
                angle = 2 * np.pi * i / max(1, n) - np.pi / 2
                if show_labels:
                    # Try to place label outside the circle if it fits entirely within the image bounds
                    text = lab.upper()
                    tw, th = self._text_size(draw, text, label_font)
                    # Candidate outside position
                    lx_out = cx + int((radius + outside_offset) * np.cos(angle))
                    ly_out = cy + int((radius + outside_offset) * np.sin(angle))
                    # Compute top-left of text box for outside
                    x_out = lx_out - tw // 2
                    y_out = ly_out - th // 2
                    fits_outside = (x_out >= 2 and y_out >= 2 and x_out + tw <= w - 2 and y_out + th <= h - 2)
                    if fits_outside:
                        self._text_with_outline(draw, (x_out, y_out), text, label_color, label_font)
                    else:
                        # Fallback: place slightly inside the circle
                        lx_in = cx + int((radius - inside_offset) * np.cos(angle))
                        ly_in = cy + int((radius - inside_offset) * np.sin(angle))
                        x_in = lx_in - tw // 2
                        y_in = ly_in - th // 2
                        self._text_with_outline(draw, (x_in, y_in), text, label_color, label_font)

                if show_values:
                    # numeric value near vertex point (use raw probability, not normalized)
                    vx, vy = points[i]
                    if normalize:
                        # move value slightly inward to avoid overlap with labels at outer side
                        vx += int(-value_offset_in * np.cos(angle))
                        vy += int(-value_offset_in * np.sin(angle))
                    else:
                        # move slightly outward
                        vx += int(value_offset_out * np.cos(angle))
                        vy += int(value_offset_out * np.sin(angle))
                    v_text = f"{raw_values[i]:.2f}"
                    v_tw, v_th = self._text_size(draw, v_text, value_font)
                    # Clamp to image bounds
                    vx_clamped = max(2 + v_tw // 2, min(w - 2 - v_tw // 2, vx))
                    vy_clamped = max(2 + v_th // 2, min(h - 2 - v_th // 2, vy))
                    self._text_with_outline(draw, (vx_clamped - v_tw // 2, vy_clamped - v_th // 2), v_text, label_color, value_font)

        return points, (outline_color, fill_color)

    def _draw_va_plot(self, base_img: Image.Image, draw: ImageDraw.ImageDraw, size,
                      bg_rgb, valence, arousal,
                      show_minor_gridlines, show_axis_labels, show_value_labels,
                      show_mood_labels,
                      va_theme: str, point_color_hex: str,
                      label_font, tick_font, font_color_rgb, debug=False):
        w, h = size
        # Plot margins
        margin = int(min(w, h) * 0.10)
        avail_left, avail_top = margin, margin
        avail_right, avail_bottom = w - margin, h - margin
        avail_w = avail_right - avail_left
        avail_h = avail_bottom - avail_top
        # Keep square plot inside available rectangle
        plot_size = min(avail_w, avail_h)
        # center square
        left = avail_left + (avail_w - plot_size) // 2
        top = avail_top + (avail_h - plot_size) // 2
        right = left + plot_size
        bottom = top + plot_size
        plot_w = plot_size
        plot_h = plot_size
        # Remaining spaces outside the square (relative to entire image)
        extra_left_img = left
        extra_right_img = w - right
        extra_top_img = top
        extra_bottom_img = h - bottom

        # Optional themed quadrant backgrounds from theme
        q_colors_and_grid = self._va_theme_config(va_theme)
        q_colors, grid_hex = q_colors_and_grid if isinstance(q_colors_and_grid, tuple) else (None, "#444444")
        if q_colors is not None:
            overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            o = ImageDraw.Draw(overlay)
            alpha = 40  # light transparency for subtle background
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
        grid_color = self.hex_to_rgb(grid_hex)
        label_color = font_color_rgb
        # Border (hidden when minor gridlines are off)
        # Only draw the outer border if we are showing gridlines; otherwise just axes
        # This keeps the view clean when gridlines are disabled
        # (matches requirement: only show X/Y axes when gridlines are hidden)
        # Note: border uses same grid_color for visual consistency
        if show_minor_gridlines:
            draw.rectangle([left, top, right, bottom], outline=grid_color, width=1)
        # Mid axes at 4.5 with bidirectional arrows
        mid_val = left + int((4.5 / 9.0) * plot_w)
        mid_aro = bottom - int((4.5 / 9.0) * plot_h)
        # X axis + arrows (extend further outside square)
        arrow_out = max(8, int(plot_w * 0.03))
        # extend line beyond square into image bounds
        x_line_left = max(0, left - arrow_out)
        x_line_right = min(w - 1, right + arrow_out)
        draw.line([(x_line_left, mid_aro), (x_line_right, mid_aro)], fill=grid_color, width=2)
        # Right arrow (tip outside)
        draw.polygon([(right + arrow_out, mid_aro), (right - 8, mid_aro - 6), (right - 8, mid_aro + 6)], fill=grid_color)
        # Left arrow (tip outside)
        draw.polygon([(left - arrow_out, mid_aro), (left + 8, mid_aro - 6), (left + 8, mid_aro + 6)], fill=grid_color)
        # Y axis + arrows (extend further outside square)
        y_line_top = max(0, top - arrow_out)
        y_line_bottom = min(h - 1, bottom + arrow_out)
        draw.line([(mid_val, y_line_bottom), (mid_val, y_line_top)], fill=grid_color, width=2)
        # Top arrow (tip outside)
        draw.polygon([(mid_val, top - arrow_out), (mid_val - 6, top + 8), (mid_val + 6, top + 8)], fill=grid_color)
        # Bottom arrow (tip outside)
        draw.polygon([(mid_val, bottom + arrow_out), (mid_val - 6, bottom - 8), (mid_val + 6, bottom - 8)], fill=grid_color)
        # Sub grid lines at every integer from 1..8
        if show_minor_gridlines:
            # Draw at every 0.5 from 0.5 to 8.5
            steps = [i * 0.5 for i in range(1, 18)]
            for t in steps:
                x = left + int((t / 9.0) * plot_w)
                y = bottom - int((t / 9.0) * plot_h)
                draw.line([(x, top), (x, bottom)], fill=grid_color, width=1)
                draw.line([(left, y), (right, y)], fill=grid_color, width=1)

        # Axis semantic labels
        if show_axis_labels:
            def txt(xy, t, f):
                self._text_with_outline(draw, xy, t, label_color, f)
            margin_lbl = 8
            # Baseline for X-axis labels below the axis (same as Neutral)
            base_y = mid_aro + 6
            # Extremes Negative/Positive positioned below X-axis; prefer outside horizontally
            n_text = "Negative"; n_tw, n_th = self._text_size(draw, n_text, tick_font)
            p_text = "Positive"; p_tw, p_th = self._text_size(draw, p_text, tick_font)
            if extra_left_img >= n_tw + margin_lbl:
                txt((left - n_tw - margin_lbl, base_y), n_text, tick_font)
            else:
                txt((left + 4, base_y), n_text, tick_font)
            if extra_right_img >= p_tw + margin_lbl:
                txt((right + margin_lbl, base_y), p_text, tick_font)
            else:
                txt((right - p_tw - 4, base_y), p_text, tick_font)
            # Arousal extremes (High always inside near top edge; Low near bottom edge)
            h_text = "High"; h_tw, h_th = self._text_size(draw, h_text, tick_font)
            l_text = "Low";  l_tw, l_th = self._text_size(draw, l_text, tick_font)
            y_high = top + 6
            txt((mid_val + 6, y_high), h_text, tick_font)
            if extra_bottom_img >= l_th + margin_lbl:
                y_low = bottom + margin_lbl
            else:
                y_low = bottom + 2
            txt((mid_val + 6, y_low), l_text, tick_font)
            # Origin label (Neutral)
            on_text = "(Neutral)"; on_tw, on_th = self._text_size(draw, on_text, tick_font)
            txt((mid_val - on_tw // 2, base_y), on_text, tick_font)
            # Axis names: VALENCE above axis; place outside horizontally if possible
            v_text = "VALENCE"; v_tw, v_th = self._text_size(draw, v_text, label_font)
            v_y = mid_aro - v_th - 6
            if extra_right_img >= v_tw + margin_lbl:
                txt((right + margin_lbl, v_y), v_text, label_font)
            elif extra_left_img >= v_tw + margin_lbl:
                txt((left - v_tw - margin_lbl, v_y), v_text, label_font)
            else:
                txt((right - v_tw - 14, v_y), v_text, label_font)
            # AROUSAL placement relative to 'High': prefer above top border; otherwise below High
            a_text = "AROUSAL"; a_tw, a_th = self._text_size(draw, a_text, label_font)
            if extra_top_img >= a_th + (margin_lbl + 4):
                # move a few pixels further up by default for clearer separation
                a_y = top - a_th - (margin_lbl + 4)
            else:
                a_y = y_high + h_th + margin_lbl
            txt((mid_val - a_tw // 2, a_y), a_text, label_font)

        # Mood labels ring overlay (above grid and axes)
        if show_mood_labels:
            cx = left + plot_w // 2
            cy = top + plot_h // 2
            square_radius = plot_w // 2
            ring_r = int(square_radius * 0.82)
            # Draw translucent black-filled ring with semi-transparent outline
            overlay = Image.new('RGBA', (size[0], size[1]), (0, 0, 0, 0))
            od = ImageDraw.Draw(overlay)
            # Ring fill
            od.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], fill=(0, 0, 0, 24))
            # Ring outline
            od.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], outline=(grid_color[0], grid_color[1], grid_color[2], 80), width=1)
            base_img.paste(overlay, (0, 0), overlay)

            # Define 12 labels with fixed angles
            labels_angles = [
                (15, "HAPPY"), (45, "DELIGHTED"), (75, "EXCITED"),
                (105, "TENSE"), (135, "ANGRY"), (165, "FRUSTRATED"),
                (195, "DEPRESSED"), (225, "BORED"), (255, "TIRED"),
                (285, "CALM"), (315, "RELAXED"), (345, "CONTENT"),
            ]
            # Offsets
            outer_offset = 0  # per request: 0% outer offset
            inner_offset = int(plot_w * 0.02)
            for deg, word in labels_angles:
                ang = np.deg2rad(deg)
                # Preferred outer position relative to plot square (not entire image)
                rx_out = cx + int((ring_r + outer_offset) * np.cos(ang))
                # Use image coordinate system: y axis grows downward, so invert sin to make 90° point up
                ry_out = cy - int((ring_r + outer_offset) * np.sin(ang))
                text = word
                tw, th = self._text_size(draw, text, tick_font)
                x_out = rx_out - tw // 2
                y_out = ry_out - th // 2
                # Check against square bounds
                fits = (x_out >= left + 2 and y_out >= top + 2 and x_out + tw <= right - 2 and y_out + th <= bottom - 2)
                if fits:
                    # draw semi-transparent text via overlay with outline
                    txt_overlay = Image.new('RGBA', (size[0], size[1]), (0, 0, 0, 0))
                    td = ImageDraw.Draw(txt_overlay)
                    # outline (slightly stronger alpha)
                    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                        td.text((x_out+dx, y_out+dy), text, fill=(0,0,0,200), font=tick_font)
                    # fill semi-transparent
                    td.text((x_out, y_out), text, fill=(label_color[0], label_color[1], label_color[2], 160), font=tick_font)
                    base_img.paste(txt_overlay, (0, 0), txt_overlay)
                else:
                    # Fallback inner position (slightly inside ring)
                    rx_in = cx + int((ring_r - inner_offset) * np.cos(ang))
                    ry_in = cy - int((ring_r - inner_offset) * np.sin(ang))
                    x_in = rx_in - tw // 2
                    y_in = ry_in - th // 2
                    # Clamp to square bounds
                    x_in = max(left + 2, min(right - 2 - tw, x_in))
                    y_in = max(top + 2, min(bottom - 2 - th, y_in))
                    txt_overlay = Image.new('RGBA', (size[0], size[1]), (0, 0, 0, 0))
                    td = ImageDraw.Draw(txt_overlay)
                    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                        td.text((x_in+dx, y_in+dy), text, fill=(0,0,0,200), font=tick_font)
                    td.text((x_in, y_in), text, fill=(label_color[0], label_color[1], label_color[2], 160), font=tick_font)
                    base_img.paste(txt_overlay, (0, 0), txt_overlay)

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
                val_text = f"V:{vx:.2f} A:{vy:.2f}"
                tw, th = self._text_size(draw, val_text, tick_font)
                off = int(min(w, h) * 0.02)
                tx = px + off
                ty = py - th - off
                # draw semi-transparent black rect as background (padding)
                pad_x, pad_y = 4, 2
                bg_overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
                bd = ImageDraw.Draw(bg_overlay)
                bd.rectangle([tx - pad_x, ty - pad_y, tx + tw + pad_x, ty + th + pad_y], fill=(0,0,0,160))
                base_img.paste(bg_overlay, (0, 0), bg_overlay)
                # then draw opaque text for readability
                self._text_with_outline(draw, (tx, ty), val_text, label_color, tick_font)
        except Exception:
            # If invalid, write N/A
            self._text_with_outline(draw, (left + 6, top + 6), "N/A", label_color, tick_font)

    def visualize_emotion(self, raw_data,
                          image_width=640, image_height=480,
                          background_color="#111111", font_color="#EFEFEF", font_size="medium",
                          radar_top_k=6, radar_normalize=False, radar_show_labels=True, radar_show_values=True,
                          radar_theme="pastel",
                          wordcloud_theme="pastel", wordcloud_top_k=12, wordcloud_use_opacity=True, wordcloud_layout="center_spiral", wordcloud_size_scale="medium",
                          va_show_minor_gridlines=True, va_show_mood_labels=False, va_show_axis_labels=True, va_show_value_labels=True,
                          va_point_color="#FFCC00", va_theme="no_background",
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

        # Prepare base images and fonts
        bg_rgb = self.hex_to_rgb(background_color)
        # Map font size keyword to pixel size
        size_map = {
            "extra small": 14,
            "small": 18,
            "medium": 22,
            "large": 28,
            "extra large": 34,
        }
        fs = size_map.get(str(font_size).lower(), 22)
        radar_label_font = self._get_font(int(fs))
        radar_value_font = self._get_font(max(10, int(fs * 0.9)))
        va_label_font = self._get_font(int(fs))
        va_tick_font = self._get_font(max(10, int(fs * 0.9)))
        font_color_rgb = self.hex_to_rgb(font_color)

        # Radar image
        radar_img = Image.new('RGB', (image_width, image_height), bg_rgb)
        r_draw = ImageDraw.Draw(radar_img)

        # Resolve radar theme colors (managed by theme)
        radar_colors = self._apply_radar_theme(radar_theme)

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
            moods_sel, radar_normalize, radar_show_labels, radar_show_values, radar_colors,
            radar_label_font, radar_value_font, font_color_rgb, debug
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
            self._text_with_outline(r_draw, (10, 10), "NO MOOD DATA", font_color_rgb, radar_label_font)

        # Wordcloud image
        wc_img = Image.new('RGB', (image_width, image_height), bg_rgb)
        wc_draw = ImageDraw.Draw(wc_img)
        # Build sorted moods for wordcloud
        moods_wc_sorted = []
        if isinstance(mood_probs, dict) and mood_probs:
            try:
                moods_wc_sorted = sorted(((k, float(v)) for k, v in mood_probs.items()), key=lambda x: x[1], reverse=True)
            except Exception:
                moods_wc_sorted = [(k, v) for k, v in mood_probs.items()]
        moods_wc_sel = moods_wc_sorted[:max(1, int(wordcloud_top_k))] if moods_wc_sorted else []

        # Draw wordcloud
        self._draw_wordcloud(
            wc_img, wc_draw, (image_width, image_height), bg_rgb,
            moods_wc_sel, self._apply_wordcloud_theme(wordcloud_theme),
            radar_label_font, fs, font_color_rgb, wordcloud_use_opacity, wordcloud_layout, wordcloud_size_scale, debug
        )

        # VA image
        va_img = Image.new('RGB', (image_width, image_height), bg_rgb)
        v_draw = ImageDraw.Draw(va_img)
        self._draw_va_plot(
            va_img, v_draw, (image_width, image_height), bg_rgb,
            valence, arousal,
            va_show_minor_gridlines, va_show_axis_labels, va_show_value_labels,
            va_show_mood_labels,
            va_theme, va_point_color,
            va_label_font, va_tick_font, font_color_rgb, debug
        )

        # Convert to tensors (ComfyUI IMAGE)
        radar_array = np.array(radar_img).astype(np.float32) / 255.0
        radar_tensor = torch.from_numpy(radar_array)[None,]
        wc_array = np.array(wc_img).astype(np.float32) / 255.0
        wc_tensor = torch.from_numpy(wc_array)[None,]
        va_array = np.array(va_img).astype(np.float32) / 255.0
        va_tensor = torch.from_numpy(va_array)[None,]
        return (radar_tensor, wc_tensor, va_tensor)

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
                "image_width", "image_height", "background_color", "font_color", "font_size",
                "radar_theme", "radar_top_k", "radar_normalize", "radar_show_labels", "radar_show_values",
                "wordcloud_theme", "wordcloud_layout", "wordcloud_top_k", "wordcloud_use_opacity", "wordcloud_size_scale",
                "va_theme", "va_show_minor_gridlines", "va_show_mood_labels", "va_show_axis_labels", "va_show_value_labels", "va_point_color",
            ]
            for k in keys:
                if k in kwargs and kwargs[k] is not None:
                    m.update(str(kwargs[k]).encode("utf-8"))
            return m.hexdigest()
        except Exception:
            return float("NaN")

    def _draw_wordcloud(self, base_img: Image.Image, draw: ImageDraw.ImageDraw, size, bg_rgb,
                        moods: list, palette_hex: list,
                        base_font, base_font_px: int, fallback_color_rgb,
                        use_opacity: bool, layout: str, size_scale: str,
                        debug=False):
        """
        Draw a simple word cloud from (mood, prob) list.

        - Uses row-based flow layout with slight jitter.
        - Font size scales linearly with probability.
        - Colors cycle through a themed palette.
        """
        w, h = size
        # Fallback when no data
        if not moods:
            self._text_with_outline(draw, (10, 10), "NO MOOD DATA", fallback_color_rgb, base_font)
            return

        # Normalize probabilities for sizing
        probs = [float(v) for _, v in moods]
        p_min, p_max = (min(probs), max(probs)) if probs else (0.0, 1.0)
        if p_max == p_min:
            p_min = 0.0
        # Size bounds derived from UI font size choice and scale level
        # Keep minimum at or above base size; increase maximum across levels
        scale_level = str(size_scale).lower()
        if scale_level == "low":
            lo, hi = 1.00, 2.6
        elif scale_level == "high":
            lo, hi = 1.00, 4.0
        else:  # medium
            lo, hi = 1.00, 3.2
        sz_min = max(12, int(base_font_px * lo))
        sz_max = max(sz_min + 2, int(base_font_px * hi))

        def scale_sz(p: float):
            t = 0.0 if p_max == p_min else (p - p_min) / (p_max - p_min)
            return int(sz_min + t * (sz_max - sz_min))

        # Prepare measured words with chosen colors and fonts
        palette_rgb = [self.hex_to_rgb(c) for c in (palette_hex or [])]
        if not palette_rgb:
            palette_rgb = [fallback_color_rgb]

        measured = []
        for idx, (word, p) in enumerate(moods):
            sz = scale_sz(float(p))
            font = self._get_font(sz)
            tw, th = self._text_size(draw, str(word), font)
            color = palette_rgb[idx % len(palette_rgb)]
            measured.append((str(word), font, tw, th, color, float(p)))

        # Helper: draw word with alpha and outline into overlay
        def draw_item(od, x, y, item, t_norm):
            word, font, tw, th, color, p = item
            alpha = int(210 if not use_opacity else (80 + t_norm * 160))
            oa = min(255, alpha + 40)
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                od.text((x+dx, y+dy), word, fill=(0,0,0,oa), font=font)
            od.text((x, y), word, fill=(color[0], color[1], color[2], alpha), font=font)

        # Helper: collision check (l,t,r,b) vs placed rects with padding
        def collide(rect, placed, pad=3):
            l, t, r, b = rect
            l -= pad; t -= pad; r += pad; b += pad
            for L,T,R,B in placed:
                if not (r < L or l > R or b < T or t > B):
                    return True
            return False

        cx, cy = w // 2, h // 2
        overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        placed = []  # list of (l,t,r,b)
        spacing = 8

        # Normalize probs per item for drawing alpha
        def tnorm(p):
            return 0.0 if p_max == p_min else max(0.0, min(1.0, (p - p_min) / (p_max - p_min)))

        if layout == "sequential_flow":
            # Simple line flow centered, minimal overlap by construction
            margin_x = int(w * 0.05)
            margin_y = int(h * 0.06)
            max_line_w = w - margin_x * 2
            lines = []
            line_items = []
            line_w = 0
            line_h = 0
            for item in measured:
                _, _, tw, th, _, _ = item
                need = tw if not line_items else (tw + spacing)
                if line_w + need > max_line_w:
                    if line_items:
                        lines.append((line_items, line_w, line_h))
                    line_items = [item]
                    line_w = tw
                    line_h = th
                else:
                    if line_items:
                        line_w += spacing
                    line_w += tw
                    line_h = max(line_h, th)
                    line_items.append(item)
            if line_items:
                lines.append((line_items, line_w, line_h))

            total_h = sum(lh for _, _, lh in lines) + (len(lines) - 1) * (spacing // 2)
            y = max(margin_y, (h - total_h) // 2)
            for items, lw, lh in lines:
                x = (w - lw) // 2
                for item in items:
                    word, font, tw, th, color, p = item
                    tx = x
                    ty = y + (lh - th) // 2
                    draw_item(od, tx, ty, item, tnorm(p))
                    placed.append((tx, ty, tx + tw, ty + th))
                    x += tw + spacing
                y += lh + (spacing // 2)

        elif layout == "archimedean_spiral_desc":
            # Place from center along a growing spiral, avoiding overlaps
            a = 0.0
            b = min(w, h) * 0.015
            theta_step = 0.35
            max_steps = 1200
            for idx, item in enumerate(measured):
                word, font, tw, th, color, p = item
                placed_ok = False
                theta = 0.0
                for step in range(max_steps):
                    r = a + b * theta
                    x = int(cx + r * np.cos(theta)) - tw // 2
                    y = int(cy + r * np.sin(theta)) - th // 2
                    x = max(2, min(w - tw - 2, x))
                    y = max(2, min(h - th - 2, y))
                    rect = (x, y, x + tw, y + th)
                    if not collide(rect, placed, pad=3):
                        draw_item(od, x, y, item, tnorm(p))
                        placed.append(rect)
                        placed_ok = True
                        break
                    theta += theta_step
                if not placed_ok:
                    # Fallback near bottom-right corner
                    x = min(w - tw - 2, max(2, w - tw - 10))
                    y = min(h - th - 2, max(2, h - th - 10))
                    draw_item(od, x, y, item, tnorm(p))
                    placed.append((x, y, x + tw, y + th))

        elif layout == "concentric_rings":
            # Top-1 at center, others distributed on rings by capacity
            if measured:
                item0 = measured[0]
                word, font, tw, th, color, p = item0
                x0 = cx - tw // 2
                y0 = cy - th // 2
                draw_item(od, x0, y0, item0, tnorm(p))
                placed.append((x0, y0, x0 + tw, y0 + th))
                rest = measured[1:]
            else:
                rest = []

            min_r = int(min(w, h) * 0.14)
            ring_step = int(min(w, h) * 0.14)
            idx = 0
            ring_idx = 0
            while idx < len(rest) and ring_idx < 6:
                R = min_r + ring_idx * ring_step
                # Estimate capacity from circumference
                slice_items = rest[idx:]
                if not slice_items:
                    break
                avg_w = max(1, int(sum(it[2] for it in slice_items[:6]) / min(6, len(slice_items))))
                capacity = max(3, int((2 * np.pi * R) / (avg_w + spacing)))
                ring_items = rest[idx: idx + capacity]
                n = len(ring_items)
                if n == 0:
                    break
                angle_step = 2 * np.pi / n
                for i in range(n):
                    item = ring_items[i]
                    ang = i * angle_step
                    # Try small angular adjustments to avoid overlaps
                    attempts = 24
                    for atry in range(attempts):
                        a_off = ((atry // 2) * 0.06) * ((-1) ** atry)
                        ang_try = ang + a_off
                        x = cx + int(R * np.cos(ang_try)) - item[2] // 2
                        y = cy + int(R * np.sin(ang_try)) - item[3] // 2
                        x = max(2, min(w - item[2] - 2, x))
                        y = max(2, min(h - item[3] - 2, y))
                        rect = (x, y, x + item[2], y + item[3])
                        if not collide(rect, placed, pad=3):
                            draw_item(od, x, y, item, tnorm(item[5]))
                            placed.append(rect)
                            break
                idx += n
                ring_idx += 1

        else:  # center_spiral (default)
            # Place center word then others along golden-angle spiral with overlap avoidance
            if measured:
                item0 = measured[0]
                word, font, tw, th, color, p = item0
                x0 = cx - tw // 2
                y0 = cy - th // 2
                draw_item(od, x0, y0, item0, tnorm(p))
                placed.append((x0, y0, x0 + tw, y0 + th))

            max_r = int(min(w, h) * 0.42)
            min_r = int(min(w, h) * 0.08)
            golden_angle = np.deg2rad(137.508)
            for i, item in enumerate(measured[1:], start=1):
                p = item[5]
                t = tnorm(p)
                r_base = int(min_r + (1.0 - t) * (max_r - min_r))
                placed_ok = False
                # Try multiple angle and radius offsets
                for k in range(180):
                    ang = i * golden_angle + k * 0.12 * ((-1) ** k)
                    r = r_base + (k // 12) * 6
                    x = cx + int(r * np.cos(ang)) - item[2] // 2
                    y = cy + int(r * np.sin(ang)) - item[3] // 2
                    x = max(2, min(w - item[2] - 2, x))
                    y = max(2, min(h - item[3] - 2, y))
                    rect = (x, y, x + item[2], y + item[3])
                    if not collide(rect, placed, pad=3):
                        draw_item(od, x, y, item, t)
                        placed.append(rect)
                        placed_ok = True
                        break
                if not placed_ok:
                    # Last resort near edges
                    x = random.randint(2, max(2, w - item[2] - 2))
                    y = random.randint(2, max(2, h - item[3] - 2))
                    draw_item(od, x, y, item, t)
                    placed.append((x, y, x + item[2], y + item[3]))

        base_img.paste(overlay, (0, 0), overlay)
