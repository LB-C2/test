# PlinthCAD — Lightweight 3D Layout Tool for Civil & Industrial Concrete Works

## 1. Problem Definition

Existing CAD/BIM tools (AutoCAD, Revit, Inventor, Blender) are overkill for early-stage layout of:

- Bund walls
- Concrete slabs
- Equipment plinths

This application solves only the following:

- Place, size, orient, duplicate, name, align, and dimension simple 3D concrete geometry
- Maintain constant visual clarity and correctness
- Remain lightweight, fast, and deterministic

## 2. Core Design Principles

1. **Geometry First**
   - Everything is axis-aligned or explicitly rotated
   - No free-form meshes
   - No booleans
   - No surface subdivision
2. **Always Readable**
   - Scene always lit
   - No dark views
   - No “lost edges”
   - No visible triangulation
3. **Deterministic Editing**
   - All geometry is parametric
   - Every dimension can be numerically edited
   - No destructive operations
4. **Minimal Tool Surface**
   - If a feature does not support bunds, slabs, or plinths → it does not exist

## 3. Technology Stack (Recommended)

**Runtime**

- Three.js (WebGL)
- Extremely lightweight
- Stable
- Full control over normals, materials, lighting

**Language**

- TypeScript
- Strong typing for geometry
- Deterministic state management
- Excellent Codex compatibility

**Environment**

- VS Code
- OpenAI Codex 5.2 for:
  - Geometry operators
  - UI logic
  - Dimension math
  - Scene graph mutations

**Architecture**

- Local-only
- No cloud
- No accounts
- Files saved as JSON

## 4. Object Model (Critical)

Base Class: `ConcreteObject`

```ts
interface ConcreteObject {
  id: string;
  name: string;
  type: "SLAB" | "PLINTH" | "BUND";
  position: Vector3;
  rotation: Vector3; // yaw primarily
  dimensions: {
    length: number;
    width: number;
    height: number;
  };
}
```

All geometry is derived from this model.

## 5. Supported Object Types

### 5.1 Concrete Slab

- Rectangular prism
- Adjustable:
  - Length
  - Width
  - Thickness
- Acts as reference plane for plinth alignment

### 5.2 Plinth

- Rectangular prism
- Must support:
  - Naming (e.g. P-101, P-102)
  - Duplication
  - Alignment to other plinths
  - Edge-to-edge dimensioning

### 5.3 Bund Wall

- Rectangular wall segment
- Adjustable:
  - Thickness
  - Height
  - Length
  - Orientation
- Can be chained, but remains segmented (no merging)

## 6. Required User Actions (Explicit Acceptance Criteria)

| Action | Requirement |
| --- | --- |
| Add plinth | Yes |
| Delete plinth | Yes |
| Duplicate plinth | Yes |
| Rename plinth | Yes |
| Adjust orientation | Numeric + gizmo |
| Adjust thickness | Numeric |
| Align plinths | Edge / center / face |
| Dimension between edges | Yes |
| 3D view only | Mandatory |

## 7. Dimensioning System (Key Requirement)

Dimension Type

- Edge-to-edge
- World-space accurate
- Locked to object faces (not vertices)

```ts
interface Dimension {
  fromObjectId: string;
  fromFace: "LEFT" | "RIGHT" | "FRONT" | "BACK";
  toObjectId: string;
  toFace: "LEFT" | "RIGHT" | "FRONT" | "BACK";
  value: number; // computed, read-only
}
```

Rules

- Dimensions update live when geometry changes
- Dimensions are always readable in 3D
- No paper space
- No scale ambiguity

## 8. Rendering & Visual Requirements (Non-Negotiable)

Lighting

- Permanent hemispherical light
- Permanent directional light
- No shadows required (optional soft shadow only)

```
HemisphereLight(intensity = 1.0)
DirectionalLight(intensity = 0.8)
```

Materials

- Flat concrete gray
- No textures
- No roughness maps
- No metallic response

Edge Definition

- Always visible edges
- Implement via:
  - EdgesGeometry
  - Overlay line material

Face Normals

Critical requirement:

- All rectangular faces must render as single smooth faces
- No visible triangulation

Implementation:

- Custom box geometry
- Explicit face normals
- No indexed triangle artifacts

## 9. Camera System

- Perspective camera
- Orbit controls only
- Locked Z-up
- No roll
- No perspective distortion extremes

Presets:

- Isometric
- Top
- Front
- Side

## 10. Alignment System

Supported alignment modes:

- Face-to-face
- Center-to-center
- Edge-to-edge

```
align(
  sourcePlinth,
  targetPlinth,
  mode: "LEFT" | "RIGHT" | "CENTER"
)
```

Alignment is numerical, not visual guesswork.

## 11. File Format

Native Save

```json
{
  "units": "mm",
  "objects": [],
  "dimensions": [],
  "camera": {}
}
```

Philosophy

- Human-readable
- Diff-friendly
- Scriptable
- No proprietary binary formats

## 12. Explicit Non-Goals (Important)

This application will NOT include:

- Boolean modeling
- Fillets or chamfers
- Texturing
- Photorealistic rendering
- Structural analysis
- BIM metadata
- Rebar
- Export to DWG (initially)

## 13. Success Criteria

This application is considered complete when:

1. A user can place a slab and ten plinths in under 60 seconds
2. Every plinth can be named, aligned, duplicated, and dimensioned
3. The scene is always legible, regardless of zoom or orientation
4. No triangular mesh artifacts are visible on flat faces
5. The application loads in under 1 second on a mid-range laptop

## 14. Why This Will Work

You are not building CAD.

You are building a parametric spatial calculator with a 3D viewport.

That constraint is precisely why this tool will:

- Be fast
- Be maintainable
- Be reliable
- Outperform large CAD packages for this specific task

## Next Steps

If you want, the next logical steps are:

1. UI wireframe
2. Scene graph structure
3. Exact Three.js geometry implementation
4. Codex prompt set for each subsystem
