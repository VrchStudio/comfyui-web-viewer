# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

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