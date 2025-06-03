# 3D Viewer Example

This repository provides a basic HTML page that uses the
[`model-viewer`](https://github.com/google/model-viewer) web component to
render 3D models.

The page loads a GLB/GLTF file and offers a USDZ fallback for iOS devices.

## Usage

1. Place your `model.glb` (or `.gltf`) and optional `model.usdz` file next to
   `index.html`.
2. Open `index.html` in a web browser. Compatible browsers will display the
   model, and iOS devices will automatically use the USDZ file for AR Quick
   Look.

Feel free to replace the file paths in `index.html` with your own models.
