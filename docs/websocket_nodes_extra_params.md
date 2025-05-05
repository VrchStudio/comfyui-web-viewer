### Image WebSocket Viewer

| Name                    | Code                | Description                                                        | Type    | Value   | Remarks                                                                               |
|-------------------------|---------------------|--------------------------------------------------------------------|---------|---------|---------------------------------------------------------------------------------------|
| Auto Fullscreen         | autoFullscreen      | Automatically enters fullscreen mode on start.                     | Boolean | false   | When true, the viewer enters fullscreen automatically.                              |
| Skip Settings Page      | skipSettingsPage    | Bypasses the settings page to start the viewer immediately.        | Boolean | false   | Directly initiates the viewer if true.                                                |
| Image Display Option    | imageDisplayOption  | Determines how the image is scaled or fitted.                      | String  | fit     | Options: original, fit, resize, crop.                                                 |
| Image Alignment         | imageAlignment      | Sets the alignment of the image within its container.              | String  | center  | Options: top-left, top, top-right, left, center, right, bottom-left, bottom, bottom-right. |
| Background Colour       | bgColourPicker      | Sets the background color of the image container.                  | String  | #222222 | Accepts hex color codes.                                                              |
| Image Display Duration  | imageDisplayDuration| Duration (ms) for which each image is displayed.                   | Number  | 1000    | Determines how long each image remains visible.                                      |
| Fade Animation Duration | fadeAnimDuration    | Duration (ms) of the fade transition between images.               | Number  | 200     | Controls the speed of the fade effect.                                               |
| Number Of Images        | numberOfImages      | Total number of images in the image cache sequence.                | Number  | 4       | Specifies how many images are cached and cycled through.                             |
| Load Remote Settings    | loadRemoteSettings  | Load Remote Settings from the server side.                         | Boolean | false   | When true, the viewer loads settings from remote server.                             |
| Show Server Messages    | showServerMessages  | Display messages sent from the server side.                        | Boolean | false   | When true, the viewer displays server messages on the screen.                        |
