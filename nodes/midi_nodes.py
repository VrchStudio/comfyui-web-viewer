import hashlib  
import json  
  
CATEGORY = "vrch.ai/control/midi"  
  
class VrchMidiDeviceLoaderNode:  
    @classmethod  
    def INPUT_TYPES(s):  
        return {  
            "required": {  
                "device_id": ("STRING", {"default": ""}),  
                "name": ("STRING", {"default": ""}),  
                "debug": ("BOOLEAN", {"default": False}),  
                "raw_data": ("STRING", {"default": "", "multiline": True, "dynamicPrompts": False}),  
            },  
        }  
        
    RETURN_TYPES = (  
        "JSON",      # RAW_DATA  
        "INT",       # INT_CC_VALUES  
        "FLOAT",     # FLOAT_CC_VALUES  
        "BOOL",      # BOOLEAN_NOTE_VALUES  
        "INT",       # INT_NOTE_VALUES
    )  
      
    RETURN_NAMES = (  
        "RAW_DATA",  
        "INT_CC_VALUES",  
        "FLOAT_CC_VALUES",  
        "BOOLEAN_NOTE_VALUES",  
        "INT_NOTE_VALUES",  
    )  
      
    CATEGORY = CATEGORY  
    FUNCTION = "load_midi_device"  
  
    def load_midi_device(self,   
                      device_id: str,   
                      name: str,
                      debug: bool=False,  
                      raw_data: str=""):  
        """  
        Load MIDI device data and return it as JSON.  
        """  
        try:  
            # Parse raw_data as JSON  
            midi_data = {  
                "device_id": device_id,  
                "name": name,  
                "raw_data": raw_data,  
            }  
              
            # Initialize default values  
            int_cc_values = [0] * 128      # Controller int values (0-127)
            float_cc_values = [0.0] * 128  # Controller float values (0.0-1.0)
            boolean_note_values = [False] * 128   # Note on/off status  
            int_note_values = [0] * 128   # Note values (0-127)
              
            # Try to parse MIDI data  
            if raw_data:  
                try:  
                    parsed_data = json.loads(raw_data)  
                      
                    # Extract CC controller data  
                    if "cc" in parsed_data and isinstance(parsed_data["cc"], list):  
                        for cc in parsed_data["cc"]:  
                            if "number" in cc and "value" in cc:  
                                cc_num = int(cc["number"])  
                                cc_value = int(cc["value"])
                                if 0 <= cc_num < 128:  
                                    int_cc_values[cc_num] = cc_value  # Store raw int value (0-127)
                                    float_cc_values[cc_num] = float(cc_value) / 127.0  # Normalize to 0-1  
                      
                    # Extract note data  
                    if "notes" in parsed_data and isinstance(parsed_data["notes"], list):  
                        for note in parsed_data["notes"]:  
                            if "number" in note and "velocity" in note and "status" in note:  
                                note_num = int(note["number"])  
                                if 0 <= note_num < 128:  
                                    int_note_values[note_num] = int(note["velocity"])  
                                    boolean_note_values[note_num] = note["status"] == "noteOn"  
                      
                except json.JSONDecodeError:  
                    if debug:  
                        print("[VrchMidiDeviceLoaderNode] Failed to parse MIDI data as JSON")  
                except Exception as e:  
                    if debug:  
                        print(f"[VrchMidiDeviceLoaderNode] Error processing MIDI data: {str(e)}")  
  
            if debug:  
                print(f"[VrchMidiDeviceLoaderNode] MIDI data:", json.dumps(midi_data, indent=2, ensure_ascii=False))  
                print(f"[VrchMidiDeviceLoaderNode] INT_CC_VALUES sample: {int_cc_values[:5]}...")  
                print(f"[VrchMidiDeviceLoaderNode] FLOAT_CC_VALUES sample: {float_cc_values[:5]}...")  
                print(f"[VrchMidiDeviceLoaderNode] BOOLEAN_NOTE_VALUES sample: {boolean_note_values[:5]}...")  
                print(f"[VrchMidiDeviceLoaderNode] INT_NOTE_VALUES sample: {int_note_values[:5]}...")  
                  
            return (  
                midi_data,  
                int_cc_values,  
                float_cc_values,  
                boolean_note_values,  
                int_note_values,  
            )  
              
        except Exception as e:  
            print(f"[VrchMidiDeviceLoaderNode] Error loading MIDI data: {str(e)}")  
            # Return default values  
            return (  
                {},              # RAW_DATA  
                [0] * 128,       # INT_CC_VALUES  
                [0.0] * 128,     # FLOAT_CC_VALUES  
                [False] * 128,   # BOOLEAN_NOTE_VALUES  
                [0] * 128,       # INT_NOTE_VALUES
            )  
      
    @classmethod  
    def IS_CHANGED(cls, **kwargs):  
        raw_data = kwargs.get("raw_data", "")  
        debug = kwargs.get("debug", False)  
        if not raw_data:  
            if debug:  
                print("[VrchMidiDeviceLoaderNode] No raw_data provided to IS_CHANGED.")  
            return False  
          
        m = hashlib.sha256()  
        m.update(raw_data.encode("utf-8"))  
        return m.hexdigest()