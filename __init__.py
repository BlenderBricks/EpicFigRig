# Copyright (C) 2020-2026 The EpicFigRig Team
# https://github.com/BlenderBricks/EpicFigRig
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# __init__.py
# The entry point for the EpicFigRig addon.
#
# Blender looks for this file first when loading an addon folder.
# Its only jobs are:
#   1. Declare bl_info so Blender knows the addon's name, version, etc.
#   2. Import all classes from the other modules
#   3. Register and unregister them with Blender
#   4. Register and unregister the scene properties the addon needs
#
# All actual logic lives in the other files — keeping this one short makes
# it easy to see the full shape of the addon at a glance.

import bpy
from bpy.props import IntProperty, BoolProperty

from .panels    import classes as panel_classes
from .operators import classes as operator_classes


bl_info = {
    "name":        "The EpicFigRig 2.0",
    "author":      "Reecey Bricks :), JabLab, IX Productions, Citrine's Animations, Jambo, "
                   "Owenator Productions and Golden Ninja Ben",
    "version":     (2, 0, 0),
    "blender":     (4, 0, 0),
    "location":    "View3D > Sidebar > EpicFigRig",
    "description": "An Epic Minifigure Rig",
    "wiki_url":    "https://github.com/BlenderBricks/EpicFigRig/tree/jablab-releases",
    "category":    "Animation",
}


# All classes that need to be registered with Blender, in order.
# Panels must come before operators in case any operator references a panel.
_ALL_CLASSES = panel_classes + operator_classes


def register():
    # Register all panel and operator classes
    for cls in _ALL_CLASSES:
        bpy.utils.register_class(cls)

    # Scene properties
    # EpicRigTabs controls which tab is visible in the panel (0=Main, 1=Advanced)
    # Bug fix: the original registered this inside operator execute() calls,
    # which re-registered the type at runtime. It belongs here, registered once.
    bpy.types.Scene.EpicRigTabs = IntProperty(
        name        = "Epic Rig Tabs",
        default     = 0,
        min         = 0,
        max         = 1,
    )

    # normalize_mini normalises object transforms when rigging
    bpy.types.Scene.normalize_mini = BoolProperty(
        name        = "Normalize Minifigure",
        description = "Normalize object transforms when rigging",
        default     = False,
    )


def unregister():
    # Unregister in reverse order to avoid dependency issues
    for cls in reversed(_ALL_CLASSES):
        bpy.utils.unregister_class(cls)

    # Clean up scene properties
    del bpy.types.Scene.EpicRigTabs
    del bpy.types.Scene.normalize_mini


if __name__ == "__main__":
    register()
