# MIDI Control Nodes

### Node: `INT MIDI Control @ vrch.ai` / `FLOAT MIDI Control @ vrch.ai` (vrch.ai/control/midi)

Maps values from `VRCH_MIDI` state to Int or Float outputs.

1. **Inputs:**
   - **`midi`**: Connect the `MIDI` output from `MIDI WebSocket Channel Loader @ vrch.ai`.
   - **`lookup_mode`**: `workflow_key` or `cc_number`.
   - **`control_key`**: Canonical workflow key such as `brightness`; used only in `workflow_key` mode.
   - **`midi_channel`**: `any` or `1..16`; used only in `cc_number` mode.
   - **`cc_number`**: CC number `0..127`; used only in `cc_number` mode.
   - **`input_min` / `input_max`**: Source range, normally `0` to `127`.
   - **`output_min` / `output_max`**: Target output range.
   - **`output_invert`**: Reverse the output mapping.
   - **`output_default`**: Returned when no value is available.
   - **`output_round_to_step`**: INT node only. `0` disables rounding; values such as `32` or `64` round the mapped output up to the next step. For example, `510` becomes `512` when the step is `64`.
   - **`debug`**: Print active lookup mode and matched source.

2. **Lookup Rules:**
   - `workflow_key` mode trims `control_key` and performs exact matching against sender-owned workflow keys.
   - `cc_number` mode looks up `midi_channel + cc_number` in raw CC state.
   - The node never falls back between modes. If `lookup_mode=workflow_key`, `cc_number` is ignored. If `lookup_mode=cc_number`, `control_key` is ignored.
   - Display labels such as `Brightness` are not used as lookup aliases.

3. **Outputs:**
   - **`VALUE`**: Remapped Int or Float value.
   - **`RAW_CC`**: Raw source value as Float. When default is used, `RAW_CC` is `0.0`.

**Notes:**
- The default mode is `workflow_key`, which is the recommended user-facing setup.
- If a key is not found, enable debug to see available workflow keys.
