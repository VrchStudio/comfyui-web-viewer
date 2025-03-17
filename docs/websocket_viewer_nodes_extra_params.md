### Image WebSocket Viewer

| Name                    | Code                | Description                                                        | Type    | Value   | Remarks                                                                               |
|-------------------------|---------------------|--------------------------------------------------------------------|---------|---------|---------------------------------------------------------------------------------------|
| Auto Fullscreen         | autoFullscreen      | Automatically enters fullscreen mode on start.                   | Boolean | false   | When true, the viewer enters fullscreen automatically.                              |
| Skip Settings Page      | skipSettingsPage    | Bypasses the settings page to start the viewer immediately.        | Boolean | false   | Directly initiates the viewer if true.                                                |
| Image Display Option    | imageDisplayOption  | Determines how the image is scaled or fitted.                      | String  | fit     | Options: original, fit, resize, crop.                                                 |
| Image Alignment         | imageAlignment      | Sets the alignment of the image within its container.              | String  | center  | Options: top-left, top, top-right, left, center, right, bottom-left, bottom, bottom-right. |
| Background Colour       | bgColourPicker      | Sets the background color of the image container.                  | String  | #222222 | Accepts hex color codes.                                                              |
| Fade Animation Duration | fadeAnimDuration    | Duration of fade animation in milliseconds.                        | Number  | 200     | Controls the speed of the fade effect when updating images.                           |
