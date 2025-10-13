import hashlib
import os
import io
import base64
import json
import ffmpeg
from pathlib import Path
import torch
import torchaudio
import folder_paths # type: ignore
from .utils.music_genres_classifier import *
import time
import numpy as np
from collections import deque
from scipy.signal import find_peaks
from PIL import Image, ImageDraw
import colorsys

ASSETS_DIR = os.path.join(Path(__file__).parent.parent, "assets")
UTILS_DIR = os.path.join(Path(__file__).parent, "utils")

CATEGORY = "vrch.ai/audio"

class VrchAudioSaverNode:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "filename": ("STRING", {"default": "web_viewer_audio"}),
                "path": ("STRING", {"default": "web_viewer"}),
                "extension": (["flac", "wav", "mp3"], {"default": "mp3"}),
                "enable_preview": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "save_audio"
    OUTPUT_NODE = True
    CATEGORY = CATEGORY

    def save_audio(self, audio, filename, path, extension, enable_preview=False):
        full_output_folder = os.path.join(self.output_dir, path)
        os.makedirs(full_output_folder, exist_ok=True)

        results = []
        for i, waveform in enumerate(audio["waveform"]):
            file_name = f"{filename}_{i:02d}.{extension}" if len(audio["waveform"]) > 1 else f"{filename}.{extension}"
            full_path = os.path.join(full_output_folder, file_name)

            # Ensure waveform is 2D
            if waveform.dim() == 1:
                waveform = waveform.unsqueeze(0)
            elif waveform.dim() > 2:
                waveform = waveform.view(waveform.size(0), -1)

            # Save audio using BytesIO
            buff = io.BytesIO()
            torchaudio.save(buff, waveform, audio["sample_rate"], format=extension.upper())
            buff.seek(0)

            # Write BytesIO content to file
            with open(full_path, 'wb') as f:
                f.write(buff.getvalue())

            results.append({
                "filename": file_name,
                "subfolder": path,
                "type": "output"
            })

        if enable_preview:
            return {"ui": {"audio": results}}
        else:
            return {}
        
class VrchAudioRecorderNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "base64_data": ("STRING", {"multiline": False}),
                "record_mode": (["press_and_hold", "start_and_stop"],{"default":"press_and_hold",}),
                "record_duration_max": ("INT", {
                    "default": 15, "min": 1, "max": 60, "step": 1,
                }),
                "loop": ("BOOLEAN", {"default": False}),
                "loop_interval": ("FLOAT", {
                    "default": 1.0, "min": 0.5, "max": 60.0, "step": 0.1,
                }),
                "new_generation_after_recording": ("BOOLEAN", {"default": False}),
                "shortcut": ("BOOLEAN", {"default": True}),
                "shortcut_key":(
                    [
                        "F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12",
                        "F13","F14","F15","F16","F17","F18","F19","F20","F21","F22","F23","F24",
                    ],
                    {"default": "F2"},
                ),
                "device_id": ("STRING", {"default": ""}),
                "device_name": ("STRING", {"default": ""}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("AUDIO",)
    CATEGORY = CATEGORY
    FUNCTION = "process_audio"
    
    def process_audio(self, base64_data, record_mode, record_duration_max, 
                      loop, loop_interval, shortcut, shortcut_key, 
                      new_generation_after_recording, device_id="", device_name="", debug=False):
        
        def _silent_audio(duration_sec: float = 0.5, sample_rate: int = 44100):
            """Return a short silent stereo audio as a safe fallback."""
            num_samples = max(int(sample_rate * duration_sec), 1)
            waveform = torch.zeros(2, num_samples)
            return {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}

        # Validate base64 content early to avoid decoder/ffmpeg crashes
        if not base64_data or not isinstance(base64_data, str) or not base64_data.strip():
            return (_silent_audio(),)

        try:
            audio_data = base64.b64decode(base64_data)
        except Exception:
            # Bad/partial base64 -> return silence
            return (_silent_audio(),)

        if not audio_data:
            return (_silent_audio(),)

        input_buffer = io.BytesIO(audio_data)

        # Decode webm -> wav via ffmpeg with error handling
        try:
            output_buffer = io.BytesIO()
            process = (
                ffmpeg
                .input('pipe:0', format='webm')
                .output('pipe:1', format='wav')
                .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
            )
            output, _ = process.communicate(input=input_buffer.read())
            if not output:
                return (_silent_audio(),)
            output_buffer.write(output)
            output_buffer.seek(0)
        except Exception:
            return (_silent_audio(),)

        # Load wav bytes with torchaudio
        try:
            waveform, sample_rate = torchaudio.load(output_buffer)
        except Exception:
            return (_silent_audio(),)
        
        # Ensure stereo output for downstream consistency
        if waveform.shape[0] == 1:
            waveform = waveform.repeat(2, 1)
        
        audio = {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}

        return (audio,)
    
    @classmethod
    def IS_CHANGED(cls, base64_data, record_mode, record_duration_max, 
                   loop, loop_interval, shortcut, shortcut_key, 
                   new_generation_after_recording, device_id="", device_name="", debug=False):
        
        # Create a new SHA-256 hash object
        m = hashlib.sha256()
        
        # Update the hash object with the encoded base64 data
        m.update(base64_data.encode())
        
        # Return the hexadecimal digest of the hash
        return m.hexdigest()

class VrchAudioGenresNode:
    
    def __init__(self):
        self.genres_file = os.path.join(UTILS_DIR, "genres.json")
        self.model_file = os.path.join(ASSETS_DIR, "models", "music_genre_cnn.pth")
        
        # Initialize classifier and load model and genres
        self.classfier = MusicGenresClassifier(num_genres=10)  # Ensure num_genres matches your use case
        self.classfier.load_genres(self.genres_file)
        self.model = self.classfier.load_model(self.model_file)  # Load the model here

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": { 
                "audio": ("AUDIO", ),
                "threshold": ("FLOAT", {
                    "default": 0.01,
                    "min": 0.0,           
                    "max": 1.0,     
                    "step": 0.01,
                }), 
            },
        }
    
    RETURN_TYPES = ("AUDIO", "STRING",)
    RETURN_NAMES = ("audio", "genres",)
    OUTPUT_NODE = True
    FUNCTION = "analysis"
    CATEGORY = CATEGORY

    def analysis(self, audio, threshold=0.015):  # Add threshold parameter with default value
        waveform = audio["waveform"]
        
        # Check and adjust waveform dimensions
        if waveform.dim() == 3:  # If batch of single channel audio
            # Expected shape is (batch_size, channels, time)
            waveform = waveform[:, 0, :]  # Use only the first channel if stereo
        
        if waveform.dim() == 2:  # If waveform is now [batch_size, time]
            waveform = waveform.unsqueeze(1)  # Convert to [batch_size, 1, time] to add channel dimension
        elif waveform.dim() != 3:
            raise ValueError(f"Expected 2D or 3D waveform tensor, but got {waveform.dim()}D tensor")
        
        predicted_probabilities = self.classfier.predict(
            model=self.model,
            waveform=waveform,
            threshold=threshold
        )
        
        result = ""
        if predicted_probabilities:
            for genre, probability in predicted_probabilities.items(): # type: ignore
                result += f"{genre}: {probability:.4f}\n"
        else:
            result = "Error: Unable to process the audio input."

        return (audio, result,)

class VrchMicLoaderNode:
    """
    Node for capturing and processing microphone input in real-time.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "device_id": ("STRING", {"default": ""}),
                "name": ("STRING", {"default": ""}),
                "sensitivity": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
                "frame_size": (["256", "512", "1024"], {"default": "512"}),
                "sample_rate": (["16000", "24000", "48000"], {"default": "48000"}),
                "low_freq_max": ("INT", {"default": 200, "min": 50, "max": 1000, "step": 50}),
                "mid_freq_max": ("INT", {"default": 5000, "min": 1000, "max": 10000, "step": 100}),
                "enable_preview": ("BOOLEAN", {"default": True}),
                "debug": ("BOOLEAN", {"default": False}),
                "raw_data": ("STRING", {"default": "", "multiline": True, "dynamicPrompts": False}),
            },
        }
    
    RETURN_TYPES = (
        "JSON",     # RAW_DATA
        "FLOAT",    # WAVEFORM
        "FLOAT",    # SPECTRUM
        "FLOAT",    # VOLUME
        "FLOAT",    # LOW_FREQ_VOLUME
        "FLOAT",    # MID_FREQ_VOLUME
        "FLOAT",    # HIGH_FREQ_VOLUME
        "BOOLEAN",  # IS_ACTIVE
    )
    
    OUTPUT_IS_LIST = (
        False,      # RAW_DATA
        True,       # WAVEFORM
        True,       # SPECTRUM
        False,      # VOLUME
        False,      # LOW_FREQ_VOLUME
        False,      # MID_FREQ_VOLUME
        False,      # HIGH_FREQ_VOLUME
        False,      # IS_ACTIVE
    )
    
    RETURN_NAMES = (
        "RAW_DATA",
        "WAVEFORM",
        "SPECTRUM",
        "VOLUME",
        "LOW_FREQ_VOLUME",
        "MID_FREQ_VOLUME",
        "HIGH_FREQ_VOLUME",
        "IS_ACTIVE",
    )
    
    CATEGORY = CATEGORY
    FUNCTION = "load_microphone"
    
    def analyze_frequency_bands(self, spectrum, sample_rate, low_freq_max, mid_freq_max):
        """
        Analyze spectrum data to extract low/mid/high frequency volume values.
        
        Args:
            spectrum: FFT spectrum data (list or array)
            sample_rate: Audio sample rate in Hz
            low_freq_max: Maximum frequency for low band (Hz)
            mid_freq_max: Maximum frequency for mid band (Hz)
            
        Returns:
            list: [low_volume, mid_volume, high_volume]
        """
        try:
            if not spectrum or len(spectrum) == 0:
                return [0.0, 0.0, 0.0]
            
            # Convert to float list if needed
            if not isinstance(spectrum, list):
                spectrum = list(spectrum)
            
            # Calculate frequency resolution
            nyquist = sample_rate / 2
            freq_bins = len(spectrum)
            freq_per_bin = nyquist / freq_bins
            
            # Calculate frequency band boundaries in bins
            low_end = max(1, int(low_freq_max / freq_per_bin))
            mid_end = max(low_end + 1, int(mid_freq_max / freq_per_bin))
            
            # Ensure boundaries don't exceed spectrum length
            low_end = min(low_end, freq_bins)
            mid_end = min(mid_end, freq_bins)
            
            # Calculate average volume for each frequency band
            low_volume = sum(spectrum[:low_end]) / low_end if low_end > 0 else 0.0
            mid_volume = sum(spectrum[low_end:mid_end]) / (mid_end - low_end) if mid_end > low_end else 0.0
            high_volume = sum(spectrum[mid_end:]) / (freq_bins - mid_end) if freq_bins > mid_end else 0.0
            
            return [float(low_volume), float(mid_volume), float(high_volume)]
            
        except Exception as e:
            print(f"[VrchMicLoaderNode] Error analyzing frequency bands: {str(e)}")
            return [0.0, 0.0, 0.0]
    
    def load_microphone(self, 
                        device_id: str, 
                        name: str, 
                        sensitivity: float = 0.5,
                        frame_size: str = "512",
                        sample_rate: str = "48000",
                        low_freq_max: int = 200,
                        mid_freq_max: int = 5000,
                        enable_preview: bool = True,
                        debug: bool = False, 
                        raw_data: str = ""):
        """
        Load and process microphone data with frequency band analysis.
        """
        try:
            # Initialize default values
            waveform = [0.0] * 128
            spectrum = [0.0] * 128
            volume = 0.0
            low_freq_volume = 0.0
            mid_freq_volume = 0.0
            high_freq_volume = 0.0
            is_active = False
            
            # Create base result data structure
            mic_data = {
                "device_id": device_id,
                "name": name
            }
            
            # Parse raw_data if available
            if raw_data:
                try:
                    parsed_data = json.loads(raw_data)
                    
                    # Merge parsed data into mic_data
                    mic_data.update(parsed_data)
                    
                    # Get pre-calculated waveform from JS
                    if "waveform" in parsed_data and isinstance(parsed_data["waveform"], list):
                        waveform = parsed_data["waveform"]
                        
                    # Get pre-calculated spectrum from JS
                    if "spectrum" in parsed_data and isinstance(parsed_data["spectrum"], list):
                        spectrum = parsed_data["spectrum"]
                    
                    # Get volume level
                    if "volume" in parsed_data:
                        volume = float(parsed_data["volume"])
                    
                    # Get activity state
                    if "is_active" in parsed_data:
                        is_active = bool(parsed_data["is_active"])
                    
                except json.JSONDecodeError:
                    if debug:
                        print("[VrchMicLoaderNode] Failed to parse microphone data as JSON")
                except Exception as e:
                    if debug:
                        print(f"[VrchMicLoaderNode] Error processing microphone data: {str(e)}")
            
            # Perform frequency analysis if spectrum data is available
            if spectrum:
                freq_volumes = self.analyze_frequency_bands(
                    spectrum, 
                    int(sample_rate), 
                    low_freq_max, 
                    mid_freq_max
                )
                low_freq_volume = freq_volumes[0]
                mid_freq_volume = freq_volumes[1]
                high_freq_volume = freq_volumes[2]
                
                # Add frequency analysis results to mic_data
                mic_data.update({
                    "low_freq_volume": low_freq_volume,
                    "mid_freq_volume": mid_freq_volume,
                    "high_freq_volume": high_freq_volume,
                    "low_freq_max": low_freq_max,
                    "mid_freq_max": mid_freq_max
                })
                        
            if debug:
                print(f"[VrchMicLoaderNode] Device ID: {device_id}, Name: {name}")
                print(f"[VrchMicLoaderNode] Volume: {volume}, Active: {is_active}")
                print(f"[VrchMicLoaderNode] Waveform length: {len(waveform)}")
                print(f"[VrchMicLoaderNode] Spectrum length: {len(spectrum)}")
                print(f"[VrchMicLoaderNode] Frequency volumes - Low: {low_freq_volume:.4f}, Mid: {mid_freq_volume:.4f}, High: {high_freq_volume:.4f}")
            
            # Return processed data
            return (
                json.dumps(mic_data),   # RAW_DATA - complete mic data as JSON
                waveform,               # WAVEFORM
                spectrum,               # SPECTRUM
                volume,                 # VOLUME
                low_freq_volume,        # LOW_FREQ_VOLUME
                mid_freq_volume,        # MID_FREQ_VOLUME
                high_freq_volume,       # HIGH_FREQ_VOLUME
                is_active,              # IS_ACTIVE
            )
            
        except Exception as e:
            print(f"[VrchMicLoaderNode] Error loading microphone data: {str(e)}")
            # Return default values
            default_mic_data = {
                "device_id": device_id,
                "name": name,
                "error": str(e)
            }
            return (
                json.dumps(default_mic_data),  # RAW_DATA
                [0.0] * 128,                   # WAVEFORM
                [0.0] * 128,                   # SPECTRUM
                0.0,                           # VOLUME
                0.0,                           # LOW_FREQ_VOLUME
                0.0,                           # MID_FREQ_VOLUME
                0.0,                           # HIGH_FREQ_VOLUME
                False,                         # IS_ACTIVE
            )
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        raw_data = kwargs.get("raw_data", "")
        debug = kwargs.get("debug", False)
        if not raw_data:
            if debug:
                print("[VrchMicLoaderNode] No raw_data provided to IS_CHANGED.")
            return False
        
        m = hashlib.sha256()
        m.update(raw_data.encode("utf-8"))
        return m.hexdigest()

class VrchAudioFrequencyBandAnalyzerNode:
    """
    Node for analyzing specific frequency band volume from audio raw data.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "raw_data": ("JSON",),
                "freq_min": ("INT", {"default": 200, "min": 20, "max": 20000, "step": 10}),
                "freq_max": ("INT", {"default": 500, "min": 20, "max": 20000, "step": 10}),
                "sample_rate": (["16000", "24000", "48000"], {"default": "48000"}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("JSON", "FLOAT")
    RETURN_NAMES = ("ANALYSIS_DATA", "BAND_VOLUME")
    FUNCTION = "analyze_frequency_band"
    CATEGORY = CATEGORY
    
    def analyze_frequency_band(self, raw_data, freq_min, freq_max, sample_rate="48000", debug=False):
        """
        Analyze the volume of a specific frequency band from audio raw data.
        
        Args:
            raw_data: JSON string containing spectrum data
            freq_min: Minimum frequency of the band (Hz)
            freq_max: Maximum frequency of the band (Hz)
            sample_rate: Audio sample rate
            debug: Enable debug output
            
        Returns:
            tuple: (band_volume, analysis_data)
        """
        try:
            # Initialize default values
            band_volume = 0.0
            spectrum = []
            
            # Parse raw_data if available
            if raw_data:
                try:
                    # Handle JSON input - raw_data is already parsed if it's JSON type
                    if isinstance(raw_data, str):
                        parsed_data = json.loads(raw_data)
                    else:
                        parsed_data = raw_data
                    
                    # Get spectrum data
                    if "spectrum" in parsed_data and isinstance(parsed_data["spectrum"], list):
                        spectrum = parsed_data["spectrum"]
                    
                except (json.JSONDecodeError, TypeError):
                    if debug:
                        print("[VrchAudioFrequencyBandAnalyzerNode] Failed to parse raw_data as JSON")
                except Exception as e:
                    if debug:
                        print(f"[VrchAudioFrequencyBandAnalyzerNode] Error processing raw_data: {str(e)}")
            
            # Calculate frequency band volume if spectrum data is available
            if spectrum:
                band_volume = self.calculate_band_volume(
                    spectrum, 
                    int(sample_rate), 
                    freq_min, 
                    freq_max
                )
            
            # Create analysis data
            analysis_data = {
                "band_volume": band_volume,
                "freq_min": freq_min,
                "freq_max": freq_max,
                "sample_rate": int(sample_rate),
                "spectrum_length": len(spectrum),
                "has_spectrum_data": len(spectrum) > 0
            }
            
            if debug:
                print(f"[VrchAudioFrequencyBandAnalyzerNode] Frequency band {freq_min}-{freq_max}Hz volume: {band_volume:.4f}")
                print(f"[VrchAudioFrequencyBandAnalyzerNode] Spectrum length: {len(spectrum)}")
            
            return (analysis_data, band_volume)
            
        except Exception as e:
            if debug:
                print(f"[VrchAudioFrequencyBandAnalyzerNode] Error: {str(e)}")
            
            # Return default values on error
            error_data = {
                "band_volume": 0.0,
                "freq_min": freq_min,
                "freq_max": freq_max,
                "sample_rate": int(sample_rate),
                "error": str(e)
            }
            return (error_data, 0.0)
    
    def calculate_band_volume(self, spectrum, sample_rate, freq_min, freq_max):
        """
        Calculate the average volume for a specific frequency band.
        
        Args:
            spectrum: FFT spectrum data (list)
            sample_rate: Audio sample rate in Hz
            freq_min: Minimum frequency of the band (Hz)
            freq_max: Maximum frequency of the band (Hz)
            
        Returns:
            float: Average volume in the specified frequency band
        """
        try:
            if not spectrum or len(spectrum) == 0:
                return 0.0
            
            # Ensure freq_min <= freq_max
            if freq_min > freq_max:
                freq_min, freq_max = freq_max, freq_min
            
            # Calculate frequency resolution
            nyquist = sample_rate / 2
            freq_bins = len(spectrum)
            freq_per_bin = nyquist / freq_bins
            
            # Calculate frequency band boundaries in bins
            bin_min = max(0, int(freq_min / freq_per_bin))
            bin_max = min(freq_bins - 1, int(freq_max / freq_per_bin))
            
            # Ensure we have a valid range
            if bin_min >= bin_max:
                return 0.0
            
            # Calculate average volume for the frequency band
            band_spectrum = spectrum[bin_min:bin_max + 1]
            band_volume = sum(band_spectrum) / len(band_spectrum) if band_spectrum else 0.0
            
            return float(band_volume)
            
        except Exception as e:
            print(f"[VrchAudioFrequencyBandAnalyzerNode] Error calculating band volume: {str(e)}")
            return 0.0
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        raw_data = kwargs.get("raw_data", "")
        if not raw_data:
            return False
        
        m = hashlib.sha256()
        # Handle JSON input properly
        if isinstance(raw_data, str):
            m.update(raw_data.encode("utf-8"))
        else:
            # Convert JSON to string for hashing
            m.update(json.dumps(raw_data, sort_keys=True).encode("utf-8"))
        return m.hexdigest()

class VrchAudioConcatNode:
    """
    Node for concatenating two audio inputs into a single audio output.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio1": ("AUDIO",),
                "audio2": ("AUDIO",),
                "crossfade_duration_ms": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 10000,
                    "step": 100,
                }),
            },
        }
    
    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("AUDIO",)
    FUNCTION = "concatenate_audio"
    CATEGORY = CATEGORY
    
    def concatenate_audio(self, audio1, audio2, crossfade_duration_ms=0):
        """
        Concatenate two audio inputs with optional crossfade.
        
        Args:
            audio1: First audio input
            audio2: Second audio input
            crossfade_duration_ms: Duration of crossfade in milliseconds (0 means no crossfade)
            
        Returns:
            Concatenated audio
        """
        # Extract waveforms and sample rates
        waveform1 = audio1["waveform"]
        waveform2 = audio2["waveform"]
        sample_rate1 = audio1["sample_rate"]
        sample_rate2 = audio2["sample_rate"]
        
        # Check if sample rates match
        if sample_rate1 != sample_rate2:
            # Resample audio2 to match audio1's sample rate
            if len(waveform2.shape) == 3:  # Batch of waveforms
                resampled_waveforms = []
                for wav in waveform2:
                    resampler = torchaudio.transforms.Resample(sample_rate2, sample_rate1)
                    resampled_waveforms.append(resampler(wav))
                waveform2 = torch.stack(resampled_waveforms)
            else:
                resampler = torchaudio.transforms.Resample(sample_rate2, sample_rate1)
                waveform2 = resampler(waveform2)
            sample_rate = sample_rate1
        else:
            sample_rate = sample_rate1
        
        # Handle batched waveforms
        if len(waveform1.shape) == 3 and len(waveform2.shape) == 3:
            # Batch size might be different, we'll concatenate each waveform in the batch
            batch_size1 = waveform1.shape[0]
            batch_size2 = waveform2.shape[0]
            
            # Use the first waveform from each batch for demonstration
            # More sophisticated batch handling could be implemented if needed
            waveform1 = waveform1[0]
            waveform2 = waveform2[0]
        elif len(waveform1.shape) == 3:
            waveform1 = waveform1[0]
        elif len(waveform2.shape) == 3:
            waveform2 = waveform2[0]
        
        # Ensure both waveforms have the same number of channels
        num_channels1 = waveform1.shape[0]
        num_channels2 = waveform2.shape[0]
        
        if num_channels1 > num_channels2:
            # Duplicate channels to match waveform1
            waveform2 = waveform2.repeat(num_channels1 // num_channels2, 1)
        elif num_channels1 < num_channels2:
            # Duplicate channels to match waveform2
            waveform1 = waveform1.repeat(num_channels2 // num_channels1, 1)
        
        # Apply crossfade if duration > 0
        if crossfade_duration_ms > 0:
            # Convert milliseconds to seconds for sample rate calculation
            crossfade_seconds = crossfade_duration_ms / 1000.0
            crossfade_samples = int(crossfade_seconds * sample_rate)
            
            # Ensure crossfade_samples isn't larger than either audio
            crossfade_samples = min(crossfade_samples, waveform1.shape[1], waveform2.shape[1])
            
            if crossfade_samples > 0:
                # Create fade out and fade in curves
                fade_out = torch.linspace(1, 0, crossfade_samples)
                fade_in = torch.linspace(0, 1, crossfade_samples)
                
                # Apply fade out to the end of waveform1
                for c in range(waveform1.shape[0]):
                    waveform1[c, -crossfade_samples:] *= fade_out
                
                # Apply fade in to the beginning of waveform2
                for c in range(waveform2.shape[0]):
                    waveform2[c, :crossfade_samples] *= fade_in
                
                # Concatenate with overlap
                result = torch.zeros(waveform1.shape[0], waveform1.shape[1] + waveform2.shape[1] - crossfade_samples, 
                                  device=waveform1.device, dtype=waveform1.dtype)
                result[:, :waveform1.shape[1]] += waveform1
                result[:, waveform1.shape[1]-crossfade_samples:] += waveform2
            else:
                # Simple concatenation without crossfade
                result = torch.cat([waveform1, waveform2], dim=1)
        else:
            # Simple concatenation without crossfade
            result = torch.cat([waveform1, waveform2], dim=1)
        
        # Return the concatenated audio
        return ({"waveform": result.unsqueeze(0), "sample_rate": sample_rate},)

class VrchBPMDetectorNode:
    """
    Node for detecting BPM (beats per minute) from audio waveform and spectrum data.
    """
    
    def __init__(self):
        # Initialize buffers for temporal analysis
        self.waveform_buffer = deque(maxlen=500)  # Reduced buffer size for better performance
        self.spectrum_buffer = deque(maxlen=500)
        self.beat_times = deque(maxlen=30)  # Increased for better BPM calculation
        self.last_update_time = 0
        self.bpm_history = deque(maxlen=8)  # Increased for better smoothing
        self.debug_counter = 0
        
        # Persistent BPM state variables
        self.current_bpm = 0.0
        self.current_confidence = 0.0
        self.last_valid_bpm_time = 0
        
    def clean_old_beats(self, current_time, max_age=10.0):
        """
        Remove beat times older than max_age seconds.
        
        Args:
            current_time: Current timestamp
            max_age: Maximum age in seconds to keep beats
        """
        cutoff_time = current_time - max_age
        while self.beat_times and self.beat_times[0] < cutoff_time:
            self.beat_times.popleft()
            
    def clean_old_bpm_history(self, current_time, max_age=30.0):
        """
        Clean old BPM history entries that are too old.
        
        Args:
            current_time: Current timestamp
            max_age: Maximum age in seconds to keep BPM history
        """
        # For now, we rely on the deque maxlen to limit size
        # In the future, we could implement time-based cleanup here
        pass
    
    def get_adaptive_min_interval(self):
        """
        Calculate adaptive minimum interval between beats based on recent BPM history.
        
        Returns:
            float: Minimum interval in seconds
        """
        if len(self.bpm_history) > 0:
            avg_bpm = np.mean(list(self.bpm_history))
            if avg_bpm > 0:
                # Allow slightly faster than detected BPM (up to 20% faster)
                return max(0.15, 60.0 / (avg_bpm * 1.2))
        
        # Default minimum interval (300 BPM max)
        return 0.2
        
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "raw_data": ("JSON",),
                "sample_rate": (["16000", "24000", "48000"], {"default": "48000"}),
                "analysis_window": ("FLOAT", {"default": 4.0, "min": 1.0, "max": 10.0, "step": 0.1}),
                "update_interval": ("FLOAT", {"default": 0.2, "min": 0.1, "max": 2.0, "step": 0.1}),
                "confidence_threshold": ("FLOAT", {"default": 0.3, "min": 0.0, "max": 1.0, "step": 0.01}),
                "bpm_range_min": ("INT", {"default": 60, "min": 30, "max": 200, "step": 1}),
                "bpm_range_max": ("INT", {"default": 200, "min": 60, "max": 300, "step": 1}),
                "debug": ("BOOLEAN", {"default": False}),
            },
        }
    
    RETURN_TYPES = (
        "JSON",     # BPM_DATA
        "FLOAT",    # BPM_VALUE
        "FLOAT",    # BPM_CONFIDENCE
        "BOOLEAN",  # BEAT_DETECTED
        "FLOAT",    # RHYTHM_STRENGTH
    )
    
    RETURN_NAMES = (
        "BPM_DATA",
        "BPM_VALUE",
        "BPM_CONFIDENCE",
        "BEAT_DETECTED",
        "RHYTHM_STRENGTH",
    )
    
    CATEGORY = CATEGORY
    FUNCTION = "detect_bpm"
    
    def detect_beat(self, waveform, spectrum, sample_rate, debug=False):
        """
        Detect if a beat occurs in the current frame.
        
        Args:
            waveform: Current waveform data
            spectrum: Current spectrum data
            sample_rate: Audio sample rate
            debug: Whether to print debug information
            
        Returns:
            tuple: (beat_detected, beat_strength)
        """
        try:
            if not waveform or not spectrum:
                return False, 0.0
                
            # Convert to numpy arrays for analysis
            waveform_np = np.array(waveform) if isinstance(waveform, list) else waveform
            spectrum_np = np.array(spectrum) if isinstance(spectrum, list) else spectrum
            
            # Validate input arrays
            if len(waveform_np) == 0 or len(spectrum_np) == 0:
                return False, 0.0
            
            # Focus on low-frequency content for beat detection (20-250 Hz)
            freq_per_bin = (sample_rate / 2) / len(spectrum_np)
            low_freq_end = min(int(250 / freq_per_bin), len(spectrum_np))
            # Ensure we have at least 10 bins for low frequency analysis
            low_freq_end = max(low_freq_end, min(10, len(spectrum_np)))
            beat_spectrum = spectrum_np[:low_freq_end]
            
            # Calculate energy in beat-relevant frequencies
            beat_energy = np.sum(np.abs(beat_spectrum))  # Use absolute values for energy
            
            # Initialize debug counter if not exists
            if not hasattr(self, 'debug_counter'):
                self.debug_counter = 0
            
            # Simple onset detection using energy increase
            if len(self.spectrum_buffer) > 0:
                prev_spectrum = np.array(self.spectrum_buffer[-1])
                if len(prev_spectrum) >= low_freq_end:
                    prev_beat_energy = np.sum(np.abs(prev_spectrum[:low_freq_end]))
                    energy_increase = beat_energy - prev_beat_energy
                    
                    # Debug: Print energy analysis (controlled by debug parameter)
                    if debug:
                        self.debug_counter += 1
                        if self.debug_counter % 10 == 0:
                            total_energy = np.sum(np.abs(spectrum_np))
                            max_spectrum_val = np.max(spectrum_np)
                            mean_spectrum_val = np.mean(spectrum_np)
                            print(f"[DEBUG] Beat Energy: {beat_energy:.6f}, Prev: {prev_beat_energy:.6f}")
                            print(f"[DEBUG] Energy Increase: {energy_increase:.6f}")
                            print(f"[DEBUG] Total Spectrum Energy: {total_energy:.6f}")
                            print(f"[DEBUG] Max Spectrum: {max_spectrum_val:.6f}, Mean: {mean_spectrum_val:.6f}")
                            print(f"[DEBUG] Low freq bins: {low_freq_end}/{len(spectrum_np)}")
                    
                    # Check if we have enough variation in the spectrum
                    spectrum_variation = np.std(spectrum_np)
                    
                    # Normalize by previous energy to get relative increase
                    if prev_beat_energy > 0:
                        energy_ratio = energy_increase / prev_beat_energy
                        
                        # Calculate RMS energy variation
                        current_rms = np.sqrt(np.mean(waveform_np**2))
                        
                        # Check if we have previous waveform for RMS comparison
                        rms_based_beat = False
                        rms_ratio = 0.0
                        if len(self.waveform_buffer) > 0:
                            prev_waveform = np.array(self.waveform_buffer[-1])
                            if len(prev_waveform) > 0:
                                prev_rms = np.sqrt(np.mean(prev_waveform**2))
                                if prev_rms > 0:
                                    rms_ratio = (current_rms - prev_rms) / prev_rms
                                    rms_based_beat = abs(rms_ratio) > 0.15  # Lower threshold for RMS change
                        
                        # Alternative detection: Use spectral flux for onset detection
                        spectral_flux = 0.0
                        if len(self.spectrum_buffer) >= 2:
                            prev2_spectrum = np.array(self.spectrum_buffer[-2]) if len(self.spectrum_buffer) >= 2 else prev_spectrum
                            if len(prev2_spectrum) >= low_freq_end:
                                # Calculate spectral flux (positive differences)
                                flux_diff = beat_spectrum - prev2_spectrum[:low_freq_end]
                                spectral_flux = np.sum(np.maximum(flux_diff, 0))
                        
                        # Improved beat detection logic with multiple criteria
                        energy_threshold = 0.03  # Lowered threshold
                        absolute_energy_threshold = 0.015  # Lowered threshold
                        flux_threshold = 0.1  # Spectral flux threshold
                        
                        # Multiple detection criteria
                        energy_beat = energy_ratio > energy_threshold and beat_energy > absolute_energy_threshold
                        flux_beat = spectral_flux > flux_threshold
                        variation_beat = spectrum_variation > 0.1 and current_rms > 0.05  # Minimum activity
                        
                        beat_detected = energy_beat or rms_based_beat or flux_beat or variation_beat
                        
                        # Calculate strength based on multiple factors
                        energy_strength = min(1.0, max(0.0, energy_ratio * 6))
                        rms_strength = min(1.0, abs(rms_ratio) * 3) if rms_based_beat else 0.0
                        flux_strength = min(1.0, spectral_flux * 2) if flux_beat else 0.0
                        variation_strength = min(1.0, spectrum_variation * 2) if variation_beat else 0.0
                        
                        beat_strength = max(energy_strength, rms_strength, flux_strength, variation_strength)
                        
                        # Debug: Print beat detection details
                        if debug and self.debug_counter % 10 == 0:
                            print(f"[DEBUG] Energy Ratio: {energy_ratio:.6f}, RMS: {current_rms:.6f}")
                            print(f"[DEBUG] RMS Ratio: {rms_ratio:.6f}, Spectral Flux: {spectral_flux:.6f}")
                            print(f"[DEBUG] Spectrum Variation: {spectrum_variation:.6f}")
                            print(f"[DEBUG] Beat Detected: {beat_detected} (energy: {energy_beat}, rms: {rms_based_beat}, flux: {flux_beat}, variation: {variation_beat})")
                            print(f"[DEBUG] Beat Strength: {beat_strength:.6f}")
                            
                        return beat_detected, beat_strength
                    else:
                        # If previous energy is 0, use alternative detection methods
                        current_rms = np.sqrt(np.mean(waveform_np**2))
                        spectrum_variation = np.std(spectrum_np)
                        
                        # Detect based on absolute thresholds
                        if beat_energy > 0.02 or current_rms > 0.05 or spectrum_variation > 0.1:
                            if debug and self.debug_counter % 10 == 0:
                                print(f"[DEBUG] Previous energy was 0, using alternative detection")
                                print(f"[DEBUG] Current energy: {beat_energy:.6f}, RMS: {current_rms:.6f}, Variation: {spectrum_variation:.6f}")
                            
                            strength = max(
                                min(1.0, beat_energy * 25),
                                min(1.0, current_rms * 10),
                                min(1.0, spectrum_variation * 5)
                            )
                            return True, strength
            
            # If no previous spectrum, check for significant activity in current frame
            current_rms = np.sqrt(np.mean(waveform_np**2))
            spectrum_variation = np.std(spectrum_np)
            
            if beat_energy > 0.03 or current_rms > 0.05 or spectrum_variation > 0.1:
                strength = max(
                    min(1.0, beat_energy * 20),
                    min(1.0, current_rms * 8),
                    min(1.0, spectrum_variation * 4)
                )
                return True, strength
            
            return False, 0.0
            
        except Exception as e:
            if debug:
                print(f"[ERROR] detect_beat error: {str(e)}")
            return False, 0.0
    
    def calculate_bpm(self, beat_times):
        """
        Calculate BPM from beat timestamps.
        
        Args:
            beat_times: List of beat timestamps
            
        Returns:
            tuple: (bpm_value, confidence)
        """
        try:
            if len(beat_times) < 2:  # Need at least 2 beats for one interval
                return 0.0, 0.0
                
            # Calculate intervals between beats
            intervals = []
            for i in range(1, len(beat_times)):
                interval = beat_times[i] - beat_times[i-1]
                # Filter intervals to reasonable BPM range (24-300 BPM)
                if 0.2 < interval < 2.5:  # 24-300 BPM range
                    intervals.append(interval)
            
            if len(intervals) < 1:
                return 0.0, 0.0
            
            # Remove outliers using median filtering for more robust estimation
            if len(intervals) >= 3:
                median_interval = np.median(intervals)
                # Keep intervals within 30% of median
                filtered_intervals = [
                    interval for interval in intervals 
                    if abs(interval - median_interval) < 0.3 * median_interval
                ]
                if len(filtered_intervals) >= 2:
                    intervals = filtered_intervals
            
            # Calculate BPM from average interval
            avg_interval = np.mean(intervals)
            bpm = 60.0 / avg_interval
            
            # Calculate confidence based on interval consistency
            if len(intervals) > 1:
                interval_std = np.std(intervals)
                # Confidence decreases with higher standard deviation
                confidence = max(0.0, 1.0 - (interval_std / avg_interval))
                
                # Boost confidence for more intervals
                interval_count_boost = min(1.0, len(intervals) / 5.0)
                confidence = confidence * 0.7 + interval_count_boost * 0.3
            else:
                confidence = 0.1  # Low confidence with only one interval
            
            return float(bpm), float(confidence)
            
        except Exception as e:
            return 0.0, 0.0
    
    def detect_bpm(self, 
                   raw_data, 
                   sample_rate="48000", 
                   analysis_window=3.0,
                   update_interval=0.5,
                   confidence_threshold=0.3,
                   bpm_range_min=60,
                   bpm_range_max=200,
                   debug=False):
        """
        Detect BPM from audio raw data containing waveform and spectrum.
        """
        try:
            current_time = time.time()
            
            # Initialize with previous values to maintain stability
            bpm_value = self.current_bpm
            bpm_confidence = self.current_confidence
            beat_detected = False
            rhythm_strength = 0.0
            waveform = []
            spectrum = []
            
            # Extract waveform and spectrum from raw_data
            if raw_data:
                try:
                    # Parse raw_data if it's a JSON string
                    if isinstance(raw_data, str):
                        parsed_data = json.loads(raw_data)
                    else:
                        parsed_data = raw_data
                    
                    # Extract waveform and spectrum data
                    if "waveform" in parsed_data and isinstance(parsed_data["waveform"], list):
                        waveform = parsed_data["waveform"]
                    if "spectrum" in parsed_data and isinstance(parsed_data["spectrum"], list):
                        spectrum = parsed_data["spectrum"]
                        
                    if debug:
                        print(f"[VrchBPMDetectorNode] Extracted waveform length: {len(waveform)}")
                        print(f"[VrchBPMDetectorNode] Extracted spectrum length: {len(spectrum)}")
                        
                        # Debug: Print data ranges
                        if waveform:
                            waveform_np = np.array(waveform)
                            print(f"[VrchBPMDetectorNode] Waveform range: [{np.min(waveform_np):.6f}, {np.max(waveform_np):.6f}]")
                            print(f"[VrchBPMDetectorNode] Waveform RMS: {np.sqrt(np.mean(waveform_np**2)):.6f}")
                        
                        if spectrum:
                            spectrum_np = np.array(spectrum)
                            print(f"[VrchBPMDetectorNode] Spectrum range: [{np.min(spectrum_np):.6f}, {np.max(spectrum_np):.6f}]")
                            print(f"[VrchBPMDetectorNode] Spectrum sum: {np.sum(spectrum_np):.6f}")
                            
                            # Show non-zero spectrum values
                            non_zero_count = np.count_nonzero(spectrum_np)
                            print(f"[VrchBPMDetectorNode] Non-zero spectrum bins: {non_zero_count}/{len(spectrum_np)}")
                        
                except (json.JSONDecodeError, TypeError) as e:
                    if debug:
                        print(f"[VrchBPMDetectorNode] Error parsing raw_data: {str(e)}")
                    waveform = []
                    spectrum = []
            
            # Add current data to buffers
            self.waveform_buffer.append(waveform)
            self.spectrum_buffer.append(spectrum)
            
            # Clean old beat times
            self.clean_old_beats(current_time)
            
            # Detect beat in current frame using primary method
            beat_detected, beat_strength = self.detect_beat(
                waveform, spectrum, int(sample_rate), debug=debug
            )
            
            # Record beat time if detected, but check for minimum interval
            if beat_detected:
                # Get adaptive minimum interval
                min_interval = self.get_adaptive_min_interval()
                
                # Check if enough time has passed since last beat
                if not self.beat_times or (current_time - self.beat_times[-1]) >= min_interval:
                    self.beat_times.append(current_time)
                    if debug:
                        print(f"[VrchBPMDetectorNode] Beat recorded at time: {current_time:.3f}")
                        print(f"[VrchBPMDetectorNode] Total beats recorded: {len(self.beat_times)}")
                else:
                    # Too soon since last beat - reduce strength but don't completely ignore
                    beat_strength *= 0.3
                    if debug:
                        print(f"[VrchBPMDetectorNode] Beat too soon, reduced strength: {current_time:.3f}")
                        print(f"[VrchBPMDetectorNode] Min interval: {min_interval:.3f}s")
                
            # Update BPM calculation periodically
            if current_time - self.last_update_time >= update_interval:
                self.last_update_time = current_time
                
                # Calculate BPM from recent beats
                recent_beats = [t for t in self.beat_times if current_time - t <= analysis_window]
                if len(recent_beats) >= 2:  # Need at least 2 beats for BPM calculation
                    calculated_bpm, calculated_confidence = self.calculate_bpm(recent_beats)
                    
                    # Filter BPM to valid range
                    if bpm_range_min <= calculated_bpm <= bpm_range_max:
                        # Apply confidence threshold with adaptive scaling
                        min_confidence = max(0.15, confidence_threshold * 0.5)
                        if calculated_confidence >= min_confidence:
                            self.bpm_history.append(calculated_bpm)
                            
                            # Smooth BPM using recent history with weighted average
                            if len(self.bpm_history) > 1:
                                weights = np.exp(np.linspace(-1, 0, len(self.bpm_history)))
                                weights /= np.sum(weights)
                                bpm_value = np.average(list(self.bpm_history), weights=weights)
                                bpm_confidence = calculated_confidence
                            else:
                                bpm_value = calculated_bpm
                                bpm_confidence = calculated_confidence
                        else:
                            # Keep calculated value but with reduced confidence
                            bpm_value = calculated_bpm
                            bpm_confidence = calculated_confidence * 0.5
                    else:
                        # Out of range - use history if available
                        if len(self.bpm_history) > 0:
                            bpm_value = np.mean(list(self.bpm_history))
                            bpm_confidence = 0.1  # Low confidence
                        # Don't set to 0 if we have no history - keep previous value
                elif len(self.bpm_history) > 0:
                    # Not enough recent beats but we have history - use smoothed history
                    bpm_value = np.mean(list(self.bpm_history))
                    bpm_confidence = max(0.1, bpm_confidence * 0.9)  # Gradually reduce confidence
            else:
                # Not time to update yet - keep previous values if we have history
                if len(self.bpm_history) > 0 and bpm_value == 0.0:
                    bpm_value = np.mean(list(self.bpm_history))
                    bpm_confidence = max(0.1, bpm_confidence * 0.95)  # Slowly decay confidence
            
            # Calculate rhythm strength based on beat consistency
            if len(self.beat_times) >= 2:
                recent_beats = [t for t in self.beat_times if current_time - t <= analysis_window]
                if len(recent_beats) >= 3:
                    intervals = [recent_beats[i] - recent_beats[i-1] for i in range(1, len(recent_beats))]
                    if intervals:
                        rhythm_strength = max(0.0, 1.0 - (np.std(intervals) / np.mean(intervals)))
            
            # Enhance rhythm strength with current beat
            if beat_detected:
                rhythm_strength = max(rhythm_strength, beat_strength)
            
            if debug:
                print(f"[VrchBPMDetectorNode] BPM: {bpm_value:.1f}, Confidence: {bpm_confidence:.3f}")
                print(f"[VrchBPMDetectorNode] Beat detected: {beat_detected}, Strength: {beat_strength:.3f}")
                print(f"[VrchBPMDetectorNode] Rhythm strength: {rhythm_strength:.3f}")
                print(f"[VrchBPMDetectorNode] Recent beats: {len([t for t in self.beat_times if current_time - t <= analysis_window])}")
            
            # Update persistent BPM state
            if bpm_value > 0:
                self.current_bpm = bpm_value
                self.current_confidence = bpm_confidence
                self.last_valid_bpm_time = current_time
            else:
                # If no valid BPM but we have a recent valid one, use it with decaying confidence
                if current_time - self.last_valid_bpm_time < 10.0:  # Keep for 10 seconds
                    decay_factor = 1.0 - (current_time - self.last_valid_bpm_time) / 10.0
                    bpm_value = self.current_bpm
                    bpm_confidence = self.current_confidence * decay_factor
            
            # Create comprehensive BPM data
            bpm_data = {
                "bpm_value": float(bpm_value),
                "bpm_confidence": float(bpm_confidence),
                "beat_detected": bool(beat_detected),
                "rhythm_strength": float(rhythm_strength),
                "analysis_window": analysis_window,
                "update_interval": update_interval,
                "confidence_threshold": confidence_threshold,
                "bpm_range": [bpm_range_min, bpm_range_max],
                "beat_count": len(self.beat_times),
                "timestamp": current_time
            }
            
            return (
                json.dumps(bpm_data),
                float(bpm_value),
                float(bpm_confidence),
                bool(beat_detected),
                float(rhythm_strength),
            )
            
        except Exception as e:
            if debug:
                print(f"[VrchBPMDetectorNode] Error detecting BPM: {str(e)}")
            
            # Return default values on error
            error_data = {
                "bpm_value": 0.0,
                "bpm_confidence": 0.0,
                "beat_detected": False,
                "rhythm_strength": 0.0,
                "error": str(e)
            }
            return (
                json.dumps(error_data),
                0.0,
                0.0,
                False,
                0.0,
            )
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always update for real-time BPM detection
        return float("NaN")

class VrchAudioVisualizerNode:
    """
    Node for generating visualization images from audio waveform and spectrum data.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "raw_data": ("JSON",),
                "image_width": ("INT", {"default": 512, "min": 256, "max": 2048, "step": 32}),
                "image_height": ("INT", {"default": 256, "min": 128, "max": 1024, "step": 32}),
                "color_scheme": (["colorful", "monochrome", "neon", "plasma"], {"default": "colorful"}),
                "background_color": ("STRING", {"default": "#111111"}),
                "waveform_color": ("STRING", {"default": "#CCCCCC"}),
                "waveform_amplification": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.1}),
                "line_width": ("INT", {"default": 2, "min": 1, "max": 10}),
                "debug": ("BOOLEAN", {"default": False}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "IMAGE")
    RETURN_NAMES = ("WAVEFORM_IMAGE", "SPECTRUM_IMAGE")
    FUNCTION = "generate_visualization"
    CATEGORY = CATEGORY
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        try:
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 6:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            elif len(hex_color) == 3:
                return tuple(int(hex_color[i]*2, 16) for i in range(3))
            else:
                return (17, 17, 17)  # Default dark gray
        except ValueError:
            return (17, 17, 17)  # Default dark gray
    
    def get_spectrum_color(self, index, total_bars, color_scheme):
        """Get color for spectrum bar based on color scheme."""
        if color_scheme == "colorful":
            # Rainbow colors from red to green
            hue = index / max(1, total_bars) * 120  # 0-120 degrees
            # Convert HSV to RGB
            r, g, b = colorsys.hsv_to_rgb(hue/360, 1.0, 1.0)
            return (int(r * 255), int(g * 255), int(b * 255))
        elif color_scheme == "neon":
            # Neon colors
            if index < total_bars * 0.3:
                return (255, 0, 255)  # Magenta
            elif index < total_bars * 0.6:
                return (0, 255, 255)  # Cyan
            else:
                return (255, 255, 0)  # Yellow
        elif color_scheme == "plasma":
            # Plasma-like colors
            ratio = index / max(1, total_bars)
            r = int(255 * (0.5 + 0.5 * ratio))
            g = int(255 * (0.2 + 0.3 * ratio))
            b = int(255 * (0.8 - 0.3 * ratio))
            return (r, g, b)
        else:  # monochrome
            intensity = 128 + int(127 * (index / max(1, total_bars)))
            return (intensity, intensity, intensity)
    
    def draw_waveform(self, draw, waveform, canvas_width, canvas_height, 
                     waveform_color, line_width, amplification=1.0, debug=False):
        """Draw waveform on the canvas."""
        try:
            if not waveform or len(waveform) == 0:
                return
            
            # Convert waveform data to numpy array
            waveform_np = np.array(waveform)
            
            if debug:
                print(f"[VrchAudioVisualizerNode] Drawing waveform with {len(waveform)} points")
                print(f"[VrchAudioVisualizerNode] Waveform range: [{np.min(waveform_np):.3f}, {np.max(waveform_np):.3f}]")
                print(f"[VrchAudioVisualizerNode] Amplification factor: {amplification}")
            
            # Draw center line
            center_y = canvas_height // 2
            draw.line([(0, center_y), (canvas_width, center_y)], 
                     fill=(64, 64, 64), width=1)
            
            # Calculate step size for waveform
            step_size = canvas_width / len(waveform)
            
            # Draw waveform
            points = []
            for i, value in enumerate(waveform):
                x = int(i * step_size)
                # Apply amplification and clamp value to [-1, 1]
                amplified_value = value * amplification
                clamped_value = max(-1.0, min(1.0, amplified_value))
                y = center_y - int(clamped_value * (canvas_height // 2 - 10))
                points.append((x, y))
            
            # Draw the waveform line
            if len(points) > 1:
                draw.line(points, fill=waveform_color, width=line_width)
                
        except Exception as e:
            if debug:
                print(f"[VrchAudioVisualizerNode] Error drawing waveform: {str(e)}")
    
    def draw_spectrum(self, draw, spectrum, canvas_width, canvas_height, 
                     color_scheme, debug=False):
        """Draw frequency spectrum on the canvas."""
        try:
            if not spectrum or len(spectrum) == 0:
                return
            
            # Convert spectrum data to numpy array
            spectrum_np = np.array(spectrum)
            
            if debug:
                print(f"[VrchAudioVisualizerNode] Drawing spectrum with {len(spectrum)} bars")
                print(f"[VrchAudioVisualizerNode] Spectrum range: [{np.min(spectrum_np):.3f}, {np.max(spectrum_np):.3f}]")
            
            # Calculate bar width
            bar_count = min(128, len(spectrum))
            bar_width = max(1, canvas_width // bar_count)
            
            # Draw spectrum bars
            for i in range(bar_count):
                # Get spectrum value (0.0 to 1.0)
                data_index = int(i * len(spectrum) / bar_count)
                value = max(0.0, min(1.0, spectrum[data_index]))
                
                # Calculate bar dimensions
                bar_height = int(value * (canvas_height - 4))  # Leave some margin
                x = i * bar_width
                y = canvas_height - bar_height
                
                # Get color for this bar
                bar_color = self.get_spectrum_color(i, bar_count, color_scheme)
                
                # Draw the bar
                if bar_height > 0:
                    draw.rectangle([x, y, x + bar_width - 1, canvas_height - 1], 
                                 fill=bar_color)
                
        except Exception as e:
            if debug:
                print(f"[VrchAudioVisualizerNode] Error drawing spectrum: {str(e)}")
    
    def generate_visualization(self, raw_data, image_width=512, image_height=256,
                              color_scheme="colorful", background_color="#111111", 
                              waveform_color="#CCCCCC", waveform_amplification=1.0,
                              line_width=2, debug=False):
        """
        Generate visualization images from audio raw data.
        """
        try:
            # Initialize default values
            waveform = [0.0] * 128
            spectrum = [0.0] * 128
            
            # Extract waveform and spectrum from raw_data
            if raw_data:
                try:
                    # Parse raw_data if it's a JSON string
                    if isinstance(raw_data, str):
                        parsed_data = json.loads(raw_data)
                    else:
                        parsed_data = raw_data
                    
                    # Extract waveform and spectrum data
                    if "waveform" in parsed_data and isinstance(parsed_data["waveform"], list):
                        waveform = parsed_data["waveform"]
                    if "spectrum" in parsed_data and isinstance(parsed_data["spectrum"], list):
                        spectrum = parsed_data["spectrum"]
                        
                    if debug:
                        print(f"[VrchAudioVisualizerNode] Extracted waveform length: {len(waveform)}")
                        print(f"[VrchAudioVisualizerNode] Extracted spectrum length: {len(spectrum)}")
                        
                except (json.JSONDecodeError, TypeError) as e:
                    if debug:
                        print(f"[VrchAudioVisualizerNode] Error parsing raw_data: {str(e)}")
                    # Use default values
            
            # Convert color strings to RGB tuples
            bg_color = self.hex_to_rgb(background_color)
            wave_color = self.hex_to_rgb(waveform_color)
            
            # Generate waveform image
            waveform_image = Image.new('RGB', (image_width, image_height))
            waveform_image.paste(bg_color, (0, 0, image_width, image_height))
            waveform_draw = ImageDraw.Draw(waveform_image)
            self.draw_waveform(waveform_draw, waveform, image_width, image_height, 
                             wave_color, line_width, waveform_amplification, debug)
            
            # Generate spectrum image
            spectrum_image = Image.new('RGB', (image_width, image_height))
            spectrum_image.paste(bg_color, (0, 0, image_width, image_height))
            spectrum_draw = ImageDraw.Draw(spectrum_image)
            self.draw_spectrum(spectrum_draw, spectrum, image_width, image_height, 
                             color_scheme, debug)
            
            # Convert PIL images to ComfyUI IMAGE format (tensors)
            waveform_array = np.array(waveform_image).astype(np.float32) / 255.0
            waveform_tensor = torch.from_numpy(waveform_array)[None,]  # Add batch dimension
            
            spectrum_array = np.array(spectrum_image).astype(np.float32) / 255.0
            spectrum_tensor = torch.from_numpy(spectrum_array)[None,]  # Add batch dimension
            
            if debug:
                print(f"[VrchAudioVisualizerNode] Generated waveform tensor shape: {waveform_tensor.shape}")
                print(f"[VrchAudioVisualizerNode] Generated spectrum tensor shape: {spectrum_tensor.shape}")
                print(f"[VrchAudioVisualizerNode] Tensors range: [{waveform_tensor.min():.3f}, {waveform_tensor.max():.3f}]")
            
            return (waveform_tensor, spectrum_tensor)
            
        except Exception as e:
            if debug:
                print(f"[VrchAudioVisualizerNode] Error generating visualization: {str(e)}")
            
            # Return black images as fallback
            black_image = np.zeros((image_height, image_width, 3), dtype=np.float32)
            black_tensor = torch.from_numpy(black_image)[None,]
            return (black_tensor, black_tensor)
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Always update for real-time visualization."""
        raw_data = kwargs.get("raw_data", "")
        if not raw_data:
            return False
        
        # Create hash from raw_data to detect changes
        m = hashlib.sha256()
        if isinstance(raw_data, str):
            m.update(raw_data.encode("utf-8"))
        else:
            m.update(str(raw_data).encode("utf-8"))
        
        return m.hexdigest()
