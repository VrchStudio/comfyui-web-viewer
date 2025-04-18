import json
import os
import socket

class VrchNodeUtils:
    
    @staticmethod
    def get_default_ip_address(fallback_ip="127.0.0.1"):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return fallback_ip

    @staticmethod
    def remap(value, in_min=0.0, in_max=1.0, out_min=0.0, out_max=1.0):
        """
        Remap a scalar value from the range [in_min, in_max] to [out_min, out_max].
        """
        if in_max == in_min:
            return out_min
        # Clamp the value within the input range
        value = max(min(value, in_max), in_min)
        # Perform the remapping
        return out_min + ((value - in_min) / (in_max - in_min)) * (out_max - out_min)

    @staticmethod
    def remap_invert(value, in_min=0.0, in_max=1.0, out_min=0.0, out_max=1.0):
        """
        Invert and remap a scalar value from the range [in_min, in_max] to [out_min, out_max].
        """
        if in_max == in_min:
            return out_max
        # Clamp the value within the input range
        value = max(min(value, in_max), in_min)
        # Perform the inverted remapping
        return out_max - ((value - in_min) / (in_max - in_min)) * (out_max - out_min)

    @staticmethod
    def select_remap_func(invert: bool):
        return VrchNodeUtils.remap_invert if invert else VrchNodeUtils.remap

    @staticmethod
    def save_channel_settings(output_path, channel, settings_dict):
        """
        Save settings for a channel to a JSON file.
        
        Args:
            output_path (str): Directory path to save the settings file
            channel (str): Channel identifier
            settings_dict (dict): Dictionary containing the settings
        """
        settings_filename = f"channel_{channel}_settings.json"
        settings_path = os.path.join(output_path, settings_filename)
        with open(settings_path, "w") as f:
            json.dump(settings_dict, f)