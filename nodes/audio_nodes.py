import hashlib
import os
import io
import base64
import ffmpeg
from pathlib import Path
import torchaudio
import folder_paths
from ..utils.music_genres_classifier import *

ASSETS_DIR = os.path.join(Path(__file__).parent.parent, "assets")
UTILS_DIR = os.path.join(Path(__file__).parent.parent, "utils")

CATEGORY = "vrch.ai/audio"

class VrchAudioSaverNode:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()

    @classmethod
    def INPUT_TYPES(s):
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
    def INPUT_TYPES(s):
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
                    "min": 0.1,           
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
    def IS_CHANGED(s, base64_data, record_mode, record_duration_max, 
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
    def INPUT_TYPES(s):
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
            for genre, probability in predicted_probabilities.items():
                result += f"{genre}: {probability:.4f}\n"
        else:
            result = "Error: Unable to process the audio input."

        return (audio, result,)
    