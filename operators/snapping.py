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

# operators/snapping.py
# Accessory snapping operators.
#
# These operators attach a loose mesh object (e.g. a sword, hat, or torch)
# to a specific bone on the rig using a Copy Transforms constraint. The snap
# is keyframed so the object appears to be picked up or put down at a specific
# frame — before the snap frame it has no constraint, after it follows the bone.
#
# SnapRight -- snaps to the Right Hand Snap Bone
# SnapLeft  -- snaps to the Left Hand Snap Bone
# SnapHead  -- snaps to the Head Accessory bone

import bpy
from ..constants import BONE_RIGHT_HAND_SNAP, BONE_LEFT_HAND_SNAP, BONE_HEAD_ACCESSORY
from ..utils import get_selected_armature


# ---------------------------------------------------------------------------
# COMPATIBILITY HELPER
# ---------------------------------------------------------------------------

def _insert_visual_locrot_keyframe():
    """Insert a Visual LocRot keyframe on the active object.
    Compatible with Blender 4.x and 5.x.

    'Visual' keyframes bake the constraint's final world-space result into
    the keyframe, rather than the local bone values. This is what makes the
    object appear to stay in place the frame before the constraint kicks in.
    """
    try:
        bpy.ops.anim.keyframe_insert_menu(type='BUILTIN_KSI_VisualLocRot')
    except TypeError:
        bpy.ops.anim.keyframe_insert_by_name(type='VisualLocRot')


# ---------------------------------------------------------------------------
# SHARED SNAP HELPER
# All three snap operators do exactly the same thing — the only difference
# is which bone they snap to. This function handles all of it.
# ---------------------------------------------------------------------------

def _snap_accessory_to_bone(context, snap_bone_name):
    """Attach the selected mesh object to the given bone on the selected armature.

    What this does step by step:
      1. Find which of the two selected objects is the armature and which
         is the mesh accessory
      2. Keyframe the accessory's current location/rotation/scale at frame - 1
         so it has a "before" position
      3. Add a Copy Transforms constraint targeting the snap bone
      4. Keyframe the constraint influence: 0 at frame - 1, 1 at frame current
         (this creates the animated snap-on effect)
      5. Bake the final visual position as a keyframe so the transition is clean

    Arguments:
        context        -- the Blender context passed in from the operator
        snap_bone_name -- the name of the bone to snap the accessory to
    """
    cur_frame = context.scene.frame_current

    # --- Identify the armature and the mesh from the two selected objects ---
    armature     = None
    mesh_obj     = None
    for obj in context.selected_objects:
        if obj.type == 'ARMATURE':
            armature = obj
        elif obj.type == 'MESH':
            mesh_obj = obj

    if armature is None or mesh_obj is None:
        return False   # caller will report the error

    # --- Deselect everything cleanly ---
    for obj in context.selected_objects:
        obj.select_set(False)

    # --- Set the mesh as the active object ---
    # Bug fix: original used bpy.context.window.scene.objects[0] which grabs
    # the first object in the scene regardless of selection. We already have
    # the correct mesh object, so we just use it directly.
    mesh_obj.select_set(True)
    context.view_layer.objects.active = mesh_obj

    # --- Keyframe the accessory's current transform at frame - 1 ---
    # This is the "before" position — where the object was before being snapped
    kf = mesh_obj.keyframe_insert
    kf(data_path='location',       frame=cur_frame - 1)
    kf(data_path='rotation_euler', frame=cur_frame - 1)
    kf(data_path='scale',          frame=cur_frame - 1)

    # --- Add and configure the Copy Transforms constraint ---
    mesh_obj.constraints.new('COPY_TRANSFORMS')
    copy_transform            = mesh_obj.constraints['Copy Transforms']
    copy_transform.target     = armature
    copy_transform.subtarget  = snap_bone_name

    # --- Keyframe constraint influence: off before snap, on at snap frame ---
    copy_transform.influence = 0
    copy_transform.keyframe_insert(data_path="influence", frame=cur_frame - 1)
    copy_transform.influence = 1
    copy_transform.keyframe_insert(data_path="influence", frame=cur_frame)

    # --- Bake the visual (world-space) position at the snap frame ---
    # This inserts a keyframe that captures where the object actually ends up
    # after the constraint is applied, making the transition clean
    kf(data_path='location',       frame=cur_frame - 1)
    kf(data_path='rotation_euler', frame=cur_frame - 1)
    kf(data_path='scale',          frame=cur_frame - 1)
    _insert_visual_locrot_keyframe()

    # Turn the constraint back off at the snap frame so it stays at the snapped
    # position without being permanently constrained
    copy_transform.influence = 0
    copy_transform.keyframe_insert(data_path="influence", frame=cur_frame)

    # Refresh scene
    context.scene.frame_set(cur_frame - 1)
    context.scene.frame_set(cur_frame + 1)

    return True


# ---------------------------------------------------------------------------
# OPERATORS
# ---------------------------------------------------------------------------

class SnapRight(bpy.types.Operator):
    """Snap the selected accessory to the Right Hand"""
    bl_label  = "Right Hand"
    bl_idname = 'snap_right.add'

    def execute(self, context):
        if len(context.selected_objects) != 2:
            self.report({'ERROR'}, "Select both the armature and the accessory object")
            return {'CANCELLED'}

        success = _snap_accessory_to_bone(context, BONE_RIGHT_HAND_SNAP)
        if not success:
            self.report({'ERROR'}, "Could not find both an armature and a mesh in your selection")
            return {'CANCELLED'}

        return {'FINISHED'}


class SnapLeft(bpy.types.Operator):
    """Snap the selected accessory to the Left Hand"""
    bl_label  = "Left Hand"
    bl_idname = 'snap_left.add'

    def execute(self, context):
        if len(context.selected_objects) != 2:
            self.report({'ERROR'}, "Select both the armature and the accessory object")
            return {'CANCELLED'}

        success = _snap_accessory_to_bone(context, BONE_LEFT_HAND_SNAP)
        if not success:
            self.report({'ERROR'}, "Could not find both an armature and a mesh in your selection")
            return {'CANCELLED'}

        return {'FINISHED'}


class SnapHead(bpy.types.Operator):
    """Snap the selected accessory to the Head"""
    bl_label  = "Head"
    bl_idname = 'snap_head.add'

    def execute(self, context):
        if len(context.selected_objects) != 2:
            self.report({'ERROR'}, "Select both the armature and the accessory object")
            return {'CANCELLED'}

        success = _snap_accessory_to_bone(context, BONE_HEAD_ACCESSORY)
        if not success:
            self.report({'ERROR'}, "Could not find both an armature and a mesh in your selection")
            return {'CANCELLED'}

        return {'FINISHED'}


# ---------------------------------------------------------------------------
# REGISTRATION
# ---------------------------------------------------------------------------

classes = [
    SnapRight,
    SnapLeft,
    SnapHead,
]
