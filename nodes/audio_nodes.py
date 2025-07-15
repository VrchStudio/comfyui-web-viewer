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
from ..utils.music_genres_classifier import *

ASSETS_DIR = os.path.join(Path(__file__).parent.parent, "assets")
UTILS_DIR = os.path.join(Path(__file__).parent.parent, "utils")

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
                    "default": 15,  
                    "min": 1,           
                    "max": 60,     
                    "step": 1,
                }),
                "loop": ("BOOLEAN", {"default": False}),
                "loop_interval": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.5,
                    "max": 60.0,
                    "step": 0.1,
                }),
                "new_generation_after_recording": ("BOOLEAN", {"default": False}),
                "shortcut": ("BOOLEAN", {"default": True}),
                "shortcut_key":(
                    [
                        "F1", 
                        "F2", 
                        "F3", 
                        "F4", 
                        "F5",
                        "F6", 
                        "F7", 
                        "F8", 
                        "F9", 
                        "F10", 
                        "F11", 
                        "F12",
                    ],
                    {"default": "F2"},
                ),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("AUDIO",)
    CATEGORY = CATEGORY
    FUNCTION = "process_audio"
    
    def process_audio(self, base64_data, record_mode, record_duration_max, 
                      loop, loop_interval, shortcut, shortcut_key, 
                      new_generation_after_recording):
        
        audio_data = base64.b64decode(base64_data)
        input_buffer = io.BytesIO(audio_data)

        output_buffer = io.BytesIO()
        process = (
            ffmpeg
            .input('pipe:0', format='webm')
            .output('pipe:1', format='wav')
            .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
        )
        output, _ = process.communicate(input=input_buffer.read())
        output_buffer.write(output)
        output_buffer.seek(0)

        waveform, sample_rate = torchaudio.load(output_buffer)
        
        # Check if the audio is mono (single channel)
        if waveform.shape[0] == 1:
            # Convert mono to stereo by duplicating the channel
            waveform = waveform.repeat(2, 1)
        
        audio = {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}

        return (audio,)
    
    @classmethod
    def IS_CHANGED(cls, base64_data, record_mode, record_duration_max, 
                   loop, loop_interval, shortcut, shortcut_key, 
                   new_generation_after_recording):
        
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
