"""
VrchAudioMusic2EmotionNode – music emotion recognition using Music2Emotion.
Category: vrch.ai/audio
"""

import os, tempfile, json
import soundfile as sf
import torch

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
