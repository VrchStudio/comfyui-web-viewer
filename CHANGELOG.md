# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

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