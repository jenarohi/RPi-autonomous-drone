# Vendored gzweb (Gazebo web client)

Loaded lazily by the "GAZEBO 3D" tab (`/static/gazebo3d.js`). No CDN, no network needed on the robotics box.

| file | what | version |
|---|---|---|
| `gzweb.js` | Gazebo's official web client (UMD) | gzweb 3.0.2 (Apache-2.0) |
| `three.min.js` | three.js | r141 (MIT) |
| `eventemitter2.js` `jszip.min.js` `rxjs.umd.min.js` `protobuf.min.js` `three-nebula.js` | gzweb runtime dependencies (browser builds from npm) | eventemitter2 6.4.9, jszip 3.10.1, rxjs 7.8.1, protobufjs 6.11.4, three-nebula 10.0.3 |
| `fxp.min.js` | fast-xml-parser 4.5.0, bundled with esbuild into the global `fxp` (npm ships no browser build) | 4.5.0 (MIT) |
| `globals.js` | maps the above onto the global names the gzweb bundle looks for | - |

It talks to the `gz launch` websocket server (`sim/websocket.gzlaunch`, port 9090), which the server starts with the sim.

`globals.js` also patches one gap: the protocol bundle served by `gz launch` leaves out the top-level enums
`PixelFormatType` and `SphericalCoordinatesType`, which makes gzweb throw "no such Type or Enum" when the scene
arrives. The shim adds them to the protobuf root before gzweb starts.
