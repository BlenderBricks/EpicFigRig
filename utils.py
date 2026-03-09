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

# utils.py
# Shared helper functions used across the addon.
# Anything that would otherwise be copy-pasted into multiple operators lives here.

import bpy


# ---------------------------------------------------------------------------
# ARMATURE HELPER
# ---------------------------------------------------------------------------

def get_selected_armature(context):
    """Return the first selected armature object, or None if none is selected.

    Replaces the repeated pattern in the original code:
        global selected_armature
        for obj in bpy.context.selected_objects:
            if obj.type == 'ARMATURE':
                selected_armature = obj.name

    Instead of returning just a name string (and relying on a global),
    this returns the actual object. You can still get the name via .name
    if you need it.

    Usage:
        armature = get_selected_armature(context)
        if armature is None:
            self.report({'ERROR'}, "No armature selected")
            return {'CANCELLED'}
    """
    for obj in context.selected_objects:
        if obj.type == 'ARMATURE':
            return obj
    return None


# ---------------------------------------------------------------------------
# DRIVER HELPER
# ---------------------------------------------------------------------------

def create_visibility_driver(obj_name, armature_name, prop_path, bonus_path=None,
                              expression="hide"):
    """Add hide_viewport and hide_render drivers to an object, driven by an
    armature custom property.

    This is a cleaned-up version of the driverCreate() function that was
    previously defined inside AutoRig.execute() — moving it here means it
    can be used anywhere in the addon without being re-created each time.

    Arguments:
        obj_name      -- name of the object to add drivers to
        armature_name -- name of the armature that owns the driving property
        prop_path     -- data path of the primary driver variable, e.g. '["SmearsTest"]'
        bonus_path    -- optional second variable path (used for smear objects
                         that depend on two properties at once)
        expression    -- the driver expression string (default: "hide")
        x, y          -- first keyframe point coordinates (default: 0, 0)
        xx, yy        -- second keyframe point coordinates (default: 1, 1)
    """
    obj       = bpy.data.objects[obj_name]
    armature  = bpy.data.armatures[armature_name]

    for driver_path in ("hide_viewport", "hide_render"):
        fcurve = obj.driver_add(driver_path)
        driver = fcurve.driver

        # Primary variable
        var            = driver.variables.new()
        var.type       = 'SINGLE_PROP'
        var.name       = "hide"
        target         = var.targets[0]
        target.id_type = 'ARMATURE'
        target.id      = armature
        target.data_path = prop_path

        # Optional second variable (used for smear objects)
        if bonus_path is not None:
            var2            = driver.variables.new()
            var2.type       = 'SINGLE_PROP'
            var2.name       = "hide2"
            target2         = var2.targets[0]
            target2.id_type = 'ARMATURE'
            target2.id      = armature
            target2.data_path = bonus_path

        driver.expression = expression
