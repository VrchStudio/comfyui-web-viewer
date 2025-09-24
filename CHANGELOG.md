# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.1.6 - 2025-09-24

### Added

- add new `VrchImageFallbackNode` node (display name: `IMAGE Fallback @ vrch.ai`)

### Updated

- update `VrchImageWebSocketFilterSettingsNode` node to add `opacity` option
- update `docs/image_nodes.md`
- update `docs/websocket_nodes.md`
- update README.md to add section of how to manually install `Music2Emotion` submodule

## 1.1.5 - 2025-09-02

### Updated

- update `VrchAudioMusic2EmotionNode` node to adjust `raw_data` output values
- update `VrchAudioEmotionVisualizerNode` node to add mood word cloud visuals
- update `VrchWebSocketServerNode` node to support server address dropdown list
- update `example_workflows/example_audio_nodes_002_audio_emotion_visualizer` workflow
- update `docs/audio_nodes.md`
- update `docs/websocket_nodes.md`

## 1.1.4 - 2025-08-27

### Added

- add new `VrchAudioEmotionVisualizerNode` node (display name: `AUDIO Emotion Visualizer @ vrch.ai`)
- add some example workflows for the newly added nodes

### Updated

- update `VrchImageWebSocketFilterSettingsNode` to adjust `brightness`, `contrast` and `saturate` range
- docs: add `AUDIO Emotion Visualizer @ vrch.ai` node section in `docs/audio_nodes.md`

## 1.1.3 - 2025-08-15

### Added

- add new `VrchImageWebSocketFilterSettingsNode` (display name: `IMAGE Filter Settings @ vrch.ai`)

### Updated

- update `VrchImageWebSocketSettingsNode` to accept optional `filters_json` input and output `IMAGE_SETTINGS_JSON`
- update front-end (`websocket_nodes.js`) to add green "Reset Filters" button for filter settings node
- update `websocket_nodes.md` documentation (new node section, legacy typo fix, settings node output & filters integration)


## 1.1.2 - 2025-08-14

### Updated

- update `Audio Recorder` node to make it more robust
- update requirements.txt to adjust dependency version 
- remove png files in `example_workflows` to reduce repo size

## 1.1.1 - 2025-08-05

### Added

- add new latent WebSocket nodes:
  - `VrchLatentWebSocketSenderNode` - send latent data over WebSocket
  - `VrchLatentWebSocketChannelLoaderNode` - receive latent data from WebSocket channel
- add new audio analysis node:
  - `VrchAudioFrequencyBandAnalyzerNode` - analyze specific frequency band volume from audio spectrum data

### Updated

- update `VrchImageWebSocketSettingsNode` to add `send_settings` parameter for manual control of settings transmission
- update `VrchWebSocketServerNode` to register `/latent` path for latent data transmission
- update `VrchMicLoaderNode` to add `enable_preview` parameter for controlling audio visualization display and improve UI layout with two-row controls design
- update websocket_nodes.md with documentation for new latent WebSocket nodes
- update audio_nodes.md with documentation for new audio frequency band analyzer node

### Fixed

- update `gradio` and `spotipy` version to fix vulnerable dependencies warning

## 1.1.0 - 2025-08-02

### Added

- add a new `VrchAudioMusic2EmotionNode` audio node for music emotion detection
- add Music2Emotion Plugin integration with smart import detection mechanism
- add comprehensive installation guide for Music2Emotion third-party plugin in README.md
- add detailed documentation for AUDIO Music to Emotion Detector node in audio_nodes.md

### Updated

- update third_party module with automatic sys.path management for git submodules
- update Music2Emotion integration to use VrchStudio/Music2Emotion fork with custom modifications
- update audio emotion detection to output 5 data types: AUDIO, RAW_DATA, MOODS, VALENCE, AROUSAL
- update mood probability display format to newline-separated with 4-decimal precision
- update all emotion detection output names to uppercase convention
- update requirements.txt with Music2Emotion dependencies (mir_eval, NumPy 2.0+ compatibility)

### Fixed

- fix import path conflicts in Music2Emotion module with relative import conversion
- fix NumPy version compatibility issues by upgrading to NumPy 2.0.2 and Numba 0.61.2
- fix graceful degradation when Music2Emotion dependencies are unavailable

## 1.0.34 - 2025-07-21

### Added

- add a new `VrchDelayNode` logic node
- add a new `VrchQRCodeNode` for generating QR codes
- add a new `VrchBPMDetectorNode` audio node
- add a new `VrchAudioVisualizerNode` audio node
- add safe unit test suite for WebSocket server functionality in `./nodes/tests/`
- add new WebSocket nodes:
  - `VrchImageWebSocketSimpleWebViewerNode` - simplified image viewer without advanced settings
  - `VrchImageWebSocketSettingsNode` - dedicated settings management node
- add `new_generation_after_pressing` parameter to Key Control nodes for automatic queue triggering

### Updated

- update `VrchDelayOSCControlNode` to have default value
- update `VrchImageWebSocketWebViewerNode` with URL output and renamed to Legacy version
- update web viewer nodes with URL output
- update Key Control nodes to add F13 - F24 as shortcut keys
- update `VrchMicLoaderNode` display name to be `AUDIO Micphone Loader @ vrch.ai`
- update `VrchImageWebSocketWebViewerNode` set `number_of_images` default value to be 1
- update `VrchImageWebSocketSimpleWebViewerNode` to include basic animation parameters
- update WebSocket server with port sharing mechanism for multi-process deployments
- update WebSocket server with smart binary message logging
- update osc_nodes.md
- update logic_nodes.md
- update web_viewer_nodes.md
- update websocket_nodes.md
- update audio_nodes.md
- update key_control_nodes.md
- refactor WebSocket server code by moving `SimpleWebSocketServer` to `./nodes/utils/websocket_server.py`
- refactor utils directory structure by moving `./utils` to `./nodes/utils`
- refactor WebSocket nodes architecture for better separation of concerns

### Fixed

- fix node sizing issue for microphone, xbox controller, QR Code and SRT player nodes
- fix WebSocket compatibility issues with websockets
- fix `VrchInstantQueueKeyControlNode` node doesn't work issue
- fix `VrchAudioRecorderNode` node incorrect init behaviour

## 1.0.33 - 2025-05-20

### Added

- add a new `VrchAudioChannelLoaderNode` node
- add a new `VrchMicLoaderNode` node
- add a new `VrchAudioConcatNode` node
- add an example workflow for WebSocket Nodes

### Updated

- update `VrchAudioWebViewerNode` to support audio transition features (fade in/out and crossfade)
- update `VrchImageWebSocketWebViewerNode` to support more server settings
- update websocket_nodes.md
- update websocet_nodes_extra_params.md
- update web_viewer_nodes.md
- update web_viewer_nodes_extra_params.md
- update audio_nodes.md
- update example workflows to match the nodes upgrade

## 1.0.32 - 2025-05-05

### Added

- add new websocket nodes, including:
  - `VrchWebSocketServerNode`
  - `VrchJsonWebSocketSenderNode`
  - `VrchJsonWebSocketChannelLoaderNode`
- add new image node `VrchImagePreviewBackgroundNewNode`
- add new gamepad node `VrchXboxControllerNode`
- add midi nodes
- add midi nodes documentation

### Updated

- rename `websocket_viewer_nodes` to be `websocket_nodes`
- rename `IMAGE Preview in Background @ vrch.ai` to be `IMAGE Preview in Background (Legacy) @ vrch.ai`
- update `VrchImageWebSocketChannelLoaderNode` with `placeholder` options and `default_image` option
- update `VrchWebSocketServerNode` to register default paths
- update `VrchGamepadLoaderNode` to improve its memory management
- update websocket_nodes.md
- update image_nodes.md
- update gamepad_nodes.md
- update gamepad nodes example workflows
- update readme.md

## 1.0.31 - 2025-04-27

### Added

- add logic nodes
- add logic_nodes.md

### Updated

- rename `workflows` to `example_workflows`
- rename css style class `comfy-big-button` to `vrch-big-button` to avoid conflict
- update gamepad workflows
- update readme.md

### Fixed

- fix the incorrect AudioUI call (Issue #10)

## 1.0.30 - 2025-04-14

### Added

- add a new Gamepad node `VrchGamepadLoaderNode`
- add gamepad_nodes.md
- add Gamepad node example workflow

## 1.0.29 - 2025-04-11

### Updated

- update websocket viewer nodes to support send settings to its client viewer
- update web viewer nodes to support save and send settings to their client viewers
- update osc control nodes to support default value
- update web_viewer_nodes.md
- update web_viewer_nodes_extra_params.md
- update websocket_viewer_nodes.md
- update websocket_viewer_nodes_extra_params.md
- update osc_control_nodes.md
- update workflows to match nodes changes

## 1.0.28 - 2025-03-29

### Updated 

- update `IMAGE Flipbook Web Viewer @ vrch.ai` to support send server messages to its web page viewer
- update web_viewer_nodes.md
- update web_viewer_nodes_extra_params.md
- update publish.yml
- fix typo in `tutorial_005_storytelling_with_text_srt_player.md`

## 1.0.27 - 2025-03-22

### Added

- add a new WebSocket Viewer node `VrchImageWebSocketChannelLoaderNode`

### Updated

- update wesocket_viewer_nodes.md

## 1.0.26 - 2025-03-18

### Updated

- update `IMAGE Flipbook Web Viewer @ vrch.ai` node to support saving settings
- update web_viewer_nodes.md

## 1.0.25 - 2025-03-17

### Added

- add a new WebSocket Viewer node `VrchImageWebSocketWebViewerNode`
- add `VrchImageWebSocketWebViewerNode` documentations

### Updated

- disable Git LFS feature as github quota is exceeded
- update README.md

## 1.0.24 - 2025-03-12

### Added

- add workflow for audio picture book (SDXL version)
  
### Updated

- update `AUDIO Recorder @ vrch.ai` node to set `look_interval` min value to 0.5
- update `IMAGE Preview in Background @ vrch.ai` node to introduce batch images display options
- update image_nodes.md
- update README.md

## 1.0.23 - 2025-03-08

### Added

- add workflow for audio picture book
- add tutorial for audio picture book

### Updated

- update `TEXT SRT Player @ vrch.ai` node to add `IS_CHANGED` check
- update README.md

## 1.0.22 - 2025-03-03

### Added

- add workflow example for `IMAGE Preview in Background @ vrch.ai` node
- add workflow example for `TEXT SRT Player @ vrch.ai` node
- add tutorial for `TEXT SRT Player @ vrch.ai` node
- add FUNDING.yml file

### Updated

- update `TEXT SRT Play @ vrch.ai` node to add interactive slider bar
- update README.md
- update text_nodes.md

## 1.0.21 - 2025-02-25

### Added

- introduce a new Text node `VrchTextSrtPlayerNode`
- add test_nodes.md

### Updated

- fix Audio Record node button disappear issue #8
- fix `VrchImageWebViewerNode` and `VrchImageFlipBookWebViewerNode` nodes IS_CHANGED() call issue
- update `VrchTextKeyControlNode` with auto switch feature
- update key_control_nodes.md

## 1.0.20 - 2025-02-17

### Added

- add a new Web Viewer node `VrchImageChannelLoaderNode`
- add a new Image node `VrchImagePreviewBackgroundNode`

### Updated

- add `Star History` section in `README.md`
- update `web_viewer_nodes.md` documentation
- update `image_nodes.md` documentation

## 1.0.19 - 2025-02-09

### Added

- add a new Web Viewer node `VrchVideoWebViewerNode`
- add `web_viewer_nodes_extra_params.md` documentation

### Updated

- adjust Audio Recorder recording behaviour
- introduce `extra_params` option for all Web Viewer nodes
- refactor Web Viewer nodes js code
- update `web_viewer_nodes.md` documentation
- update example workflows for all Web Viewer nodes

## 1.0.18 - 2025-01-29

### Added

- add a new Web Viewer node `VrchAudioWebViewerNode`
- add a new workflow for Audio Web Viewer node
- add a new tutorial for Audio web Viewer node
- separate `VrchNodeUtils` into `node_utils.py`

### Updated

- update OSC Control nodes with `DEFAUTL_ADDRESS_IP`
- update Web Viwer nodes with `DEFAULT_ADDRESS`
- update README.md
- update `web_viewer_nodes.md` documentation

## 1.0.17 - 2024-12-27

### Added

- add a new workflow for Video Web Viewer node
- add a new tutorial for Video Web Viewer node

### Updated

- update `VrchImageWebViewerNode` and `VrchImageFlipBookWebViewerNode` to have `IMAGES` as output
- update `VrchAudioRecorderNode` to introduce `new_generation_after_recording` option
- update README.md
- update `audio_nodes.md`

## 1.0.16 - 2024-12-12

### Added

- add a new Viewer Control node `VrchVideoWebViewerNode`
- add workflow for Video Web Viewer node
- add tutorial for Video Web Viewer node

### Updated

- update `web_viewer_nodes.md` documentation
- update README.md

## 1.0.15 - 2024-12-01

### Added

- add a new OSC Control node `VrchDelayOscControlNode`

### Updated

- update `VrchAnyOSCControlNode` to support IS_CHANGED() based on OSC message value change
- update `osc_control_nodes.md` documentation

## 1.0.14 - 2024-11-24

### Added

- add a new Web Viewer node `VrchImageFlipBookWebViewerNode`
- add a new example workflow

### Updated

- update `VrchWebViewerNode` to support `flipbook` mode
- update `VrchInstantQueueKeyControlNode` to support `change` queue option
- update workflow and screenshot for `VrchInstantQueueKeyControlNode`
- update `web_viewer_nodes.md` and `key_control_nodes.md` documentations
- update `README.md`

## 1.0.13 - 2024-11-12

### Updated

- update `VrchInstantQueueKeyControlNode` with two new options:
  - `enable_queue_autorun`
  - `autorun_delay`
- update `key_control_nodes.md`

## 1.0.12 - 2024-11-10

### Added

- add build-in self-signed https certs (not for production use)
- add an image example workflow for rapid 8k image generation
- add `VrchInstantQueueKeyControlNode`
- add `VrchOSCControlSettingsNode`

### Updated

- update README.md with more troubleshouting questions
- update example workflows for osc control nodes
- update `key_control_nodes.md` and `osc_control_nodes.md`

### Fixed

- fix Audio Recorder node incorrect button position and style

## 1.0.11 - 2024-10-31

### Added

- add toturial for live portrait + gamepad
- add missing python packages

### Updated

- allow accessing vrch.ai/viewer via both `http` and `https` schemes
- update README.md to add a troubleshooting section

## 1.0.10 - 2024-10-19

### Added
- add OSC Cotnrol nodes, including
  - `VrchAnyOSCControlNode`
  - `VrchFloatOSCControlNode`
  - `VrchImageSwitchOSCControlNode`
  - `VrchIntOSCControlNode`
  - `VrchSwitchOSCControlNode`
  - `VrchTextConcatOSCControlNode`
  - `VrchTextSwitchOSCControlNode`
  - `VrchXYOSCControlNode`
  - `VrchXYZOSCControlNode`
- add a new Web Viewer node `VrchImageWebViewerNode`
- add comfy-org registration configuration files (placeholder only)
- add example workflows
- add touchosc control panel file

### Updated
- update `VrchWebViewerNode` to rename `page` to be `mode`
- rework on README.md

## 1.0.9 - 2024-09-30

### Updated
- update `VrchWebViewerNode` to point to vrch.ai/viewer

## 1.0.8 - 2024-09-29

### Updated
- rework on `VrchWebViewerNode`
- update `VrchTextKeyControlNode` to have 8 text slots
- update README.md

## 1.0.7 - 2024-09-20

### Added
- add a new Key Control node `VrchTextKeyControlNode`

### Updated
- update `VrchIntKeyControlNode` node with new `min_value` and `max_value` input options
- adjust `VrchIntKeyControlNode` node range to -9999 - 9999
- change default shortcut_key to be `F2`

### Fixed
- fix the issue that when crecreating a key control node, a label remained on the screen

## 1.0.6 - 2024-09-18

### Added
- New Key Control nodes, including
  - `VrchIntKeyControlNode`
  - `VrchFloatKeyControlNode`
  - `VrchBooleanKeyControlNode`

### Updated
- update node `VrchAudioRecorderNode` shortcut keys

### Updated
- update node `VrchAudioRecorderNode` to support work on Windows

### Fixed
- fix node `VrchAudioRecorderNode` button incorrect display string issue when switching record mode

## 1.0.5 - 2024-09-03

### Updated
- update node `VrchAudioRecorderNode` to introduce shortcut feature
- update README.md

## 1.0.4 - 2024-09-02

### Added
- New `MusicGenresClassifier` in `utils/music_genres_classifier.py` for getting music genre(s)
- New CNN model `music_genre_cnn.pth` in `assets/models` for `MusicGenresClassifier`

### Updated
- rework on node `VrchAudioGenresNode` to work with the new `MusicGenresClassifier`
- update node `VrchAudioRecorderNode` with `record_mode` options:
  - `press_and_hold` mode
  - `start_and_stop` mode
- update node `VrchAudioRecorderNode` with `loop` and `loop_interval` options
- update README.md

## 1.0.3 - 2024-08-30

### Added
- New `VrchAudioRecorderNode` in `audio_nodes.py` for recording audio via a mic

### Updated
- update nodes name by using "Vrch" as prefix
- update web viewer window max width/height to be 10240
- update README.md
- change `VrchAudioSaverNode` default output format to mp3

## 1.0.2 - 2024-08-26

### Added
- New `JsonUrlLoaderNode` in `text_nodes.py` for loading JSON data from URLs
- New `ImageSaverNode` in `image_nodes.py` for saving image file
- New `AudioSaverNode` in `audio_nodes.py` for saving audio file
- New `AudioGenresNode` in `audio_nodes.py` for getting audio genres (temp node only)
- Improved error handling and debugging in audio processing

## 1.0.1 - 2024-08-25

### Added
- Initial release of ComfyUI-Web-Viewer
- Web Viewer node with customizable URL input
- Configurable window size for the Web Viewer
