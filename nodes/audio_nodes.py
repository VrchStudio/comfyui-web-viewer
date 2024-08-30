import subprocess
import tempfile
import time
import traceback
import json
import os
import io
import base64
import torch
import torch.nn as nn
import torchaudio
import torch.nn.functional as F
import torchaudio.transforms as T
import folder_paths

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
    CATEGORY = "vrch.io/audio"

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
                "record_duration": ("INT", {
                    "default": 10,  
                    "min": 1,           
                    "max": 120,     
                    "step": 1,      
                    "display": "number"
                }),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("AUDIO",)
    CATEGORY = "vrch.io/audio"
    FUNCTION = "process_audio"
    
    def process_audio(self, base64_data, record_duration):
        
        audio_data = base64.b64decode(base64_data)
        buffer = io.BytesIO(audio_data)
        waveform, sample_rate = torchaudio.load(buffer)
        
        # Check if the audio is mono (single channel)
        if waveform.shape[0] == 1:
            # Convert mono to stereo by duplicating the channel
            waveform = waveform.repeat(2, 1)
        
        audio = {"waveform": waveform.unsqueeze(0), "sample_rate": sample_rate}

        return (audio,)

class VrchAudioGenresNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "audio_file": ("STRING", {"default": "input.mp3"})
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_genres"
    CATEGORY = "vrch.io/audio"

    def get_genres(self, audio_file):
        # Implement genre detection logic here
        genres = "pop, rock, electronic"  # Placeholder
        print(f"Detected genres: {genres}")
        return (genres,)
    
class MusicGenreCNN(nn.Module):
    
    def __init__(self, num_genres, input_length=1291, n_mfcc=13):
        super(MusicGenreCNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        
        # 通过一个示例输入来计算卷积输出的尺寸
        example_input = torch.zeros(1, 1, input_length, n_mfcc)  # [batch_size, channels, height, width]
        conv_output = self._forward_conv(example_input)
        conv_output_size = conv_output.view(1, -1).size(1)  # 展平后得到的尺寸

        self.fc1 = nn.Linear(conv_output_size, 128)
        self.fc2 = nn.Linear(128, num_genres)
        self.dropout = nn.Dropout(0.5)

    def _forward_conv(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        return x

    def forward(self, x):
        print(f"Input shape before processing: {x.shape}")
        
        # Ensure that the input tensor has the correct shape
        if x.dim() == 3:  # Case when input is [batch_size, n_mfcc, time]
            x = x.unsqueeze(1)  # Make it [batch_size, 1, n_mfcc, time]
        elif x.dim() != 4 or x.shape[1] != 1:  # Unexpected shape
            raise ValueError(f"Unexpected input shape: {x.shape}")

        print(f"Input shape after possible unsqueeze: {x.shape}")

        x = self._forward_conv(x)
        x = x.view(x.size(0), -1)  # Flatten
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x
    
    # def forward(self, x):
    #     x = x.unsqueeze(1)  # Add channel dimension [batch, 1, input_length, n_mfcc]
    #     print(f"Input shape after possible unsqueeze: {x.shape}")
    #     x = self._forward_conv(x)
    #     x = x.view(x.size(0), -1)  # Flatten
    #     x = F.relu(self.fc1(x))
    #     x = self.dropout(x)
    #     x = self.fc2(x)
    #     return x

class VrchAudioGenresNode:
    
    def __init__(self):
        self.model_dir = os.path.join(folder_paths.models_dir, "audio_genres")
        self.genres_file = os.path.join(self.model_dir, "genres.json")
        self.model_file = os.path.join(self.model_dir, "music_genres_classifier_cnn.pth")
        
        self.genres = self.load_genres()
        self.model = self.load_model()
        
    def load_genres(self):
        with open(self.genres_file, 'r') as f:
            return json.load(f)
        
    def load_model(self):
        
        # Check if CUDA is available; if not, map to CPU
        map_location = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        model = MusicGenreCNN(num_genres=len(self.genres))
        model.load_state_dict(torch.load(self.model_file, map_location=map_location))
        model.eval()
        
        return model
    
    def process_waveform(self, waveform, sample_rate, target_sample_rate=44100, num_channels=1):
        # Resample the waveform to the target sample rate
        if sample_rate != target_sample_rate:
            resample_transform = T.Resample(orig_freq=sample_rate, new_freq=target_sample_rate)
            waveform = resample_transform(waveform)
        
        # Convert to mono if num_channels is 1
        if waveform.shape[0] > 1 and num_channels == 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        elif waveform.shape[0] == 1 and num_channels > 1:
            waveform = waveform.repeat(num_channels, 1)

        # Adjust the sample width (bit depth)
        # Note: PyTorch generally works with 32-bit floats, so setting sample width directly is non-trivial.
        # You might want to normalize the audio or convert to a different data type if needed.
        # For simplicity, we'll assume you're working with normalized 32-bit floats.
        return waveform, target_sample_rate
        
    def extract_features(self, waveform=None, file_path=None, duration=None, target_length=1291, n_mfcc=13):
        try:
            # Load the audio file if waveform is not provided
            if waveform is None and file_path is not None:
                waveform, sr = torchaudio.load(file_path)
            elif waveform is not None:
                sr = 44100  # Assume a sample rate of 16000 Hz (adjust if necessary)
                # waveform, sr = self.process_waveform(waveform=waveform, sample_rate=sr)
            
            if waveform is None:
                raise ValueError("Either waveform or file_path must be provided")

            if duration is not None:
                max_samples = int(sr * duration)
                waveform = waveform[:, :max_samples]  # Truncate the audio to 'duration' seconds
            
            # Extract MFCC features
            mfcc = torchaudio.transforms.MFCC(
                sample_rate=sr,
                n_mfcc=n_mfcc,
                melkwargs={'n_mels': 64, 'n_fft': 2048}
            )(waveform)
            
            # Reshape MFCC to have [time, n_mfcc]
            # mfcc = mfcc.squeeze(0).transpose(0, 1)
            
            # Ensure mfcc has the correct shape
            mfcc = mfcc.squeeze()  # Remove any extra dimensions

            print(f"========mfcc.dim()={mfcc.dim()}, shape={mfcc.shape}")

            if mfcc.dim() == 2:  # Case when mfcc is [n_mfcc, time]
                mfcc = mfcc.unsqueeze(0).unsqueeze(0)  # Make it [1, 1, n_mfcc, time]
            elif mfcc.dim() == 3:  # Case when mfcc is [batch_size, n_mfcc, time]
                mfcc = mfcc.unsqueeze(1)  # Make it [batch_size, 1, n_mfcc, time]
            
            print(f"========Final mfcc.dim()={mfcc.dim()}, shape={mfcc.shape}")

            if target_length is not None:
                if mfcc.shape[-1] < target_length:
                    mfcc = F.pad(mfcc, (0, target_length - mfcc.shape[-1]))  # Pad time dimension
                else:
                    mfcc = mfcc[:, :, :, :target_length]  # Crop time dimension
                
            return mfcc  # The output should be [batch_size, channels, n_mfcc, target_length]
        
            # if target_length is not None:
            #     if mfcc.shape[0] < target_length:
            #         mfcc = F.pad(mfcc, (0, 0, 0, target_length - mfcc.shape[0]))  # Pad to 'target_length'
            #     else:
            #         mfcc = mfcc[:target_length, :]  # Crop to 'target_length'
            
            return mfcc  # Ensure the output is [target_length, n_mfcc]
        except Exception as e:
            print(f"Error processing waveform or file {file_path}: {str(e)}")
            traceback.print_exc()
            return None
    
    def predict(self, audio, enable_debug=False):
        
        if enable_debug:
            start_time = time.time()
            print("Starting audio prediction...")
            
        wavform = audio["waveform"]

        target_length = 1291  # Ensure this matches the value used during training
        n_mfcc = 13  # Ensure this matches the value used during training
        
        features = self.extract_features(
            waveform=wavform,
            # file_path=wav_file, 
            target_length=target_length, 
            n_mfcc=n_mfcc)
        
        if features is None:
            return "Error: Unable to extract features from the audio file."
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(device)
        
        # features = features.unsqueeze(0).to(device)
        features = features.to(device)
        
        with torch.no_grad():
            outputs = self.model(features)
            probabilities = torch.softmax(outputs, dim=1).cpu().numpy().flatten()
        
        predicted_probabilities = {genre: prob for genre, prob in zip(self.genres, probabilities)}

        # Sort the predicted probabilities in descending order
        sorted_predicted_probabilities = dict(sorted(predicted_probabilities.items(), key=lambda item: item[1], reverse=True))

        if enable_debug:
            end_time = time.time()
            print(f"Prediction completed. Time taken: {end_time - start_time:.2f} seconds")

        return sorted_predicted_probabilities
    
        
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": { 
                "audio": ("AUDIO", ),
            }
        }
    
    RETURN_TYPES = ("AUDIO", "STRING",)
    RETURN_NAMES = ("audio", "genres",)
    OUTPUT_NODE = True
    FUNCTION = "analysis"
    CATEGORY = "vrch.io/audio"

    def analysis(self, audio):
        predicted_probabilities = self.predict(audio)
        result = ""
        for genre, probability in predicted_probabilities.items():
            result += f"{genre}: {probability:.4f}\n"
        return {"result": (audio, result,)}