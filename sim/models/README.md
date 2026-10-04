# Vendored simulation models

These are the exact models the original SkyScan simulator used, copied here so the repo is self-contained.

| model | origin |
|---|---|
| `iris_with_gimbal` | stock `ardupilot_gazebo` model, unchanged |
| `iris_with_standoffs` | the AeroTHON-modified model (adds the belly `down_camera` and a 360° lidar) from `aerothon-drone-sim/model-mods`, unchanged |
| `gimbal_small_3d` | the AeroTHON-modified gimbal from `aerothon-drone-sim/model-mods`; **only change:** front camera `update_rate` 1 Hz -> 5 Hz so the alignment loop gets usable frames |

The Gazebo resource path puts this directory first (`SDF_PATH` and `GZ_SIM_RESOURCE_PATH`), so these win over the stock copies.
