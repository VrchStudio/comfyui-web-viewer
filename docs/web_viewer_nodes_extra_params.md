## Web Viewer Nodes Extra Parameters

### Image Instant Viewer

| Name                    | Code                | Description                                                        | Type    | Value   | Remarks                                                                               |
|-------------------------|---------------------|--------------------------------------------------------------------|---------|---------|---------------------------------------------------------------------------------------|
| Auto Fullscreen         | autoFullscreen      | Automatically enters fullscreen mode on start.                     | Boolean | false   | When true, the viewer enters fullscreen automatically.                              |
| Skip Settings Page      | skipSettingsPage    | Bypasses the settings page to start the viewer immediately.        | Boolean | false   | Directly initiates the viewer if true.                                                |
| Image Display Option    | imageDisplayOption  | Determines how the image is scaled or fitted.                      | String  | fit     | Options: original, fit, resize, crop.                                                 |
| Image Alignment         | imageAlignment      | Sets the alignment of the image within its container.              | String  | center  | Options: top-left, top, top-right, left, center, right, bottom-left, bottom, bottom-right. |
| Background Colour       | bgColourPicker      | Sets the background color of the image container.                  | String  | #222222 | Accepts hex color codes.                                                              |
| Refresh Interval        | refreshInterval     | Interval in milliseconds for refreshing the image.                 | Number  | 200     | Controls the update frequency.                                                        |
| Fade Animation Duration | fadeAnimDuration    | Duration of fade animation in milliseconds.                        | Number  | 200     | Controls the speed of the fade effect when updating images.                           |
| Load Remote Settings    | loadRemoteSettings  | Load Remote Settings from the server side.                         | Boolean | false   | When true, the viewer loads settings from remote server.                             |
| Show Server Messages    | showServerMessages  | Display messages sent from the server side.                        | Boolean | false   | When true, the viewer displays server messages on the screen.                        |

### Image DepthMap Viewer

| Name                      | Code                  | Description                                                              | Type    | Value | Remarks                                                       |
|---------------------------|-----------------------|--------------------------------------------------------------------------|---------|-------|---------------------------------------------------------------|
| Auto Fullscreen           | autoFullscreen        | Automatically enters fullscreen mode on start.                           | Boolean | false | When true, the viewer enters fullscreen automatically.       |
| Skip Settings Page        | skipSettingsPage      | Bypasses the settings page to start the viewer immediately.              | Boolean | false | Directly initiates the viewer if true.                         |
| Enable Debug              | enableDebug           | Enables debug mode.                                                      | Boolean | false | Useful for troubleshooting and displaying debug panels.       |
| Enable Swing Anime        | enableSwingAnime      | Enables the swing animation effect.                                      | Boolean | true  | When checked, swing animation is active; otherwise, paused.      |
| Enable Mouse Track        | enableMouseTrack      | Enables mouse tracking functionality.                                    | Boolean | false | When false, mouse tracking is disabled.                        |
| Enable Head Track         | enableHeadTrack       | Enables head tracking functionality.                                     | Boolean | false | When false, head tracking is disabled.                         |
| Refresh Interval          | refreshInterval       | Interval (ms) for refreshing the image and depth map.                    | Number  | 200   | Controls update frequency.                                    |
| Video Input Rotate Angle  | videoInputRotateAngle | Sets the rotation angle for the video input.                             | Number  | 0     | Options: 0, 90, 180, 270.                                       |
| Camera Input              | cameraSelect          | Selects the camera device for video input.                               | String  | N/A   | Populated dynamically with available camera devices.          |
| Load Remote Settings      | loadRemoteSettings    | Load Remote Settings from the server side.                               | Boolean | false | When true, the viewer loads settings from remote server.      |
| Show Server Messages      | showServerMessages    | Display messages sent from the server side.                              | Boolean | false | When true, the viewer displays server messages on the screen. |

### Image Flipbook Viewer

| Name                      | Code                  | Description                                                              | Type    | Value   | Remarks                                                       |
|---------------------------|-----------------------|--------------------------------------------------------------------------|---------|---------|---------------------------------------------------------------|
| Auto Fullscreen           | autoFullscreen        | Automatically enters fullscreen mode on start.                           | Boolean | false   | When true, the viewer enters fullscreen automatically.       |
| Skip Settings Page        | skipSettingsPage      | Bypasses the settings page to start the viewer immediately.              | Boolean | false   | Directly initiates the viewer if true.                         |
| Image Display Order       | imageDisplayOrder     | Specifies the order in which images are displayed.                       | String  | sequential | Options: sequential, random.                                  |
| Image Display Option      | imageDisplayOption    | Determines how the image is scaled or fitted.                            | String  | fit     | Options: original, fit, resize, crop.                         |
| Image Alignment           | imageAlignment        | Sets the alignment of the image within its container.                    | String  | center  | Options: top-left, top, top-right, left, center, right, bottom-left, bottom, bottom-right. |
| Background Colour         | bgColourPicker        | Sets the background color of the image container.                        | String  | #222222 | Accepts hex color codes.                                      |
| Refresh Interval          | refreshInterval       | Interval (ms) for checking updated images.                               | Number  | 10000   | Controls how frequently images are refreshed.                 |
| Image Display Duration    | imageDisplayDuration  | Duration (ms) for which each image is displayed.                         | Number  | 1000    | Determines how long each image remains visible.               |
| Fade Animation Duration   | fadeAnimDuration      | Duration (ms) of the fade transition between images.                     | Number  | 300     | Controls the speed of the fade effect.                        |
| Number Of Images          | numberOfImages        | Total number of images in the flipbook sequence.                         | Number  | 4       | Specifies how many images are cycled through.                 |
| Load Remote Settings      | loadRemoteSettings    | Load Remote Settings from the server side.                               | Boolean | false   | When true, the viewer loads settings from remote server.      |
| Show Server Messages      | showServerMessages    | Display messages sent from the server side.                              | Boolean | false   | When true, the viewer displays server messages on the screen. |


### Audio Viewer

| Name                  | Code              | Description                                                             | Type    | Value   | Remarks                                                                               |
|-----------------------|-------------------|-------------------------------------------------------------------------|---------|---------|---------------------------------------------------------------------------------------|
| Auto Fullscreen       | autoFullscreen    | Automatically enters fullscreen mode on start.                          | Boolean | false   | When true, the viewer starts in fullscreen mode.                                     |
| Skip Settings Page    | skipSettingsPage  | Bypasses the settings page to start the viewer immediately.             | Boolean | false   | Directly initiates the viewer if true.                                                 |
| Enable Timed Update   | enableTimedUpdate | Enables automatic audio updates at specified intervals.                 | Boolean | false   | When true, audio is refreshed periodically based on the refresh interval.             |
| Enable Update on End  | enableUpdateOnEnd | Updates audio when the current track ends.                              | Boolean | true    | When true, attempts to load new audio upon track completion.                          |
| Enable Loop           | enableLoop        | Enables looping of audio playback.                                      | Boolean | true    | When true, audio will replay if update on end does not load new audio.                  |
| Fade In Duration      | fadeInDuration    | Duration of fade in effect in milliseconds.                             | Number  | 0       | Controls how long it takes for audio to fade in from silent to full volume.          |
| Fade Out Duration     | fadeOutDuration   | Duration of fade out effect in milliseconds.                            | Number  | 0       | Controls how long it takes for audio to fade out from full volume to silent.         |
| Crossfade Duration    | crossfadeDuration | Duration of crossfade between audio tracks in milliseconds.             | Number  | 0       | Determines smooth transition time between consecutive audio tracks.                  |
| Visualizer Type       | visualizerType    | Selects the type of audio visualizer effect.                            | String  | circles | Options: bars, circles, matrix, particles, spiral, waterball, waveform.                         |
| Load Remote Settings  | loadRemoteSettings| Load Remote Settings from the server side.                              | Boolean | false   | When true, the viewer loads settings from remote server.                             |
| Show Server Messages  | showServerMessages| Display messages sent from the server side.                             | Boolean | false   | When true, the viewer displays server messages on the screen.                        |

### Video Viewer

| Name                  | Code              | Description                                                             | Type    | Value    | Remarks                                                                               |
|-----------------------|-------------------|-------------------------------------------------------------------------|---------|----------|---------------------------------------------------------------------------------------|
| Auto Fullscreen       | autoFullscreen    | Automatically enters fullscreen mode on start.                          | Boolean | false    | When true, the viewer starts in fullscreen mode.                                     |
| Skip Settings Page    | skipSettingsPage  | Bypasses the settings page to start the viewer immediately.             | Boolean | false    | Directly initiates the viewer if true.                                                 |
| Enable Timed Update   | enableTimedUpdate | Enables automatic video updates at specified intervals.                 | Boolean | false    | When true, video is refreshed periodically based on the refresh interval.             |
| Enable Update on End  | enableUpdateOnEnd | Updates video when the current playback ends.                           | Boolean | true     | When true, attempts to load new video upon playback completion.                        |
| Enable Loop           | enableLoop        | Enables looping of video playback.                                      | Boolean | true     | When true, video will replay if update on end does not load new video.                  |
| Video Display Option  | videoDisplayOption| Determines how the video is scaled or fitted.                           | String  | original | Options: original, fit, resize, crop.                                                  |
| Video Controls        | videoControls     | Toggles the display of video control buttons.                           | Boolean | false    | When true, display video control buttons.                                           |
| Load Remote Settings  | loadRemoteSettings| Load Remote Settings from the server side.                              | Boolean | false   | When true, the viewer loads settings from remote server.                             |
| Show Server Messages  | showServerMessages| Display messages sent from the server side.                             | Boolean | false   | When true, the viewer displays server messages on the screen.                        |

### 3D Model Viewer

| Name                      | Code              | Description                                                             | Type    | Value    | Remarks                                                                           |
|---------------------------|-------------------|-------------------------------------------------------------------------|---------|----------|-----------------------------------------------------------------------------------|
| Auto Fullscreen           | autoFullscreen    | Automatically enters fullscreen mode on start.                          | Boolean | false    | When true, the viewer starts in fullscreen mode.                                |
| Skip Settings Page        | skipSettingsPage  | Bypasses the settings page to start the viewer immediately.             | Boolean | false    | When true, the viewer bypasses the settings page.                               |
| Enable Timed Update       | enableTimedUpdate | Enables automatic model updates at specified intervals.                 | Boolean | true     | When true, the model is refreshed periodically based on the refresh interval.    |
| Persist Camera Location   | persistCamera     | Saves and restores the camera position between sessions.                | Boolean | true     | When true, the current camera position is preserved between updates.             |
| Enable Rotate Animate     | enableRotateAnime | Toggles model rotation animation during display.                        | Boolean | false    | When true, the model rotates slowly for better viewing.                         |
| Background Colour         | bgColourPicker    | Sets the background color of the 3D scene.                              | String  | #222222  | Accepts a hex color value; used to set the renderer's clear color.                |
| Display Mode              | modelDisplayMode  | Determines the material display mode for the model.                     | String  | original | Options: original, normal, wireframe, depth.                                      |
| Load Remote Settings      | loadRemoteSettings| Load Remote Settings from the server side.                              | Boolean | false   | When true, the viewer loads settings from remote server.                         |
| Show Server Messages      | showServerMessages| Display messages sent from the server side.                             | Boolean | false   | When true, the viewer displays server messages on the screen.                    |