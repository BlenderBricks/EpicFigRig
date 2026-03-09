# EpicFigRig 2.0

A Blender addon for automatically rigging Mecabricks LEGO minifigure exports.

EpicFigRig identifies each brick part by its Mecabricks part ID and parents it to the correct bone on a pre-built armature — including special handling for capes, skirts, child figures, and accessories.

---

## Features

- One-click auto-rigging for standard Mecabricks minifigure exports
- IK/FK switching for arms and legs with snapping
- Smear mesh support for arms and legs
- Cape and skirt rigging with secondary motion bones
- Child figure detection (shorter leg rig variant)
- Pivot bone switching (rotate from left foot, right foot, or centre)
- Prop bone rigging for accessories held in either hand
- Accessory snap operators for attaching loose objects to hands or head
- Master bone reset and snap utilities
- Lepin hand Boolean support
- Blender 4.0 and 5.0 compatible

---

## Requirements

- Blender 4.0 or later (including 5.0)
- A Mecabricks minifigure export (standard part IDs required)

---

## Installation

1. Download the latest release zip from the [Releases](../../releases) page
2. In Blender go to **Edit → Preferences → Add-ons → Install**
3. Select the downloaded zip file
4. Enable **The EpicFigRig** in the addon list

The addon will appear in the **EpicFigRig** tab in the 3D viewport sidebar (press **N** to open it).

---

## Usage

### Rigging a Minifigure

1. Import your Mecabricks export into Blender
2. Select all the minifigure mesh objects
3. Open the EpicFigRig sidebar tab
4. Click **Rig Selected Minifigure**

The addon will identify each part, append the armature, and parent everything automatically.

### Prop Rigging

To attach a held object (sword, torch, etc.) to a prop bone:

1. Select the prop mesh and the rig
2. Click **Prop A** (right hand by default) or **Prop B** (left hand by default)

### Accessory Snapping

To snap a loose prop to the rig at a specific frame (animated pick-up/put-down):

1. Select the prop mesh and the rig
2. In the Snapping section, click **Right Hand**, **Left Hand**, or **Head**

---

## Supported Brick IDs

EpicFigRig recognises standard Mecabricks part IDs for:

- Legs, arms, torso, and head (including all standard variants)
- Hats, hair, helmets, visors, and head accessories
- Capes and skirts (full secondary rig)
- Child figure legs
- Dress bricks
- Hands (auto-detects nearest hand bone)

If a brick is not recognised, use **Additional Objects** to parent it to the nearest bone automatically.

To add support for a new brick ID, see the [Developer Reference](EpicFigRig_Developer_Reference.pdf).

---

## Credits

Created by **Reecey Bricks**, **JabLab**, **IX Productions**, **Citrine's Animations**, **Jambo**, **Owenator Productions**, and **Golden Ninja Ben**.

---

## Contributing

Bug reports and pull requests are welcome. Before contributing please read the [Developer Reference](EpicFigRig_Developer_Reference.pdf) which documents the package structure, design decisions, and instructions for adding new bricks and operators.

---

## License

This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details.
