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

# operators/misc.py
# Master Bone and Pivot operators.
#
# ResetMasterBone  -- resets the master bone to its default position,
#                     keeping IK feet planted
# SnapMasterBone   -- snaps the master bone to the "Master Bone Snap" empty,
#                     useful for matching a new pose to a previous one
# SwitchPivotLeft  -- moves the pivot point to the left foot
# SwitchPivotRight -- moves the pivot point to the right foot
# ResetPivot       -- resets the pivot bone back to the centre

import bpy
from ..constants import (
    MASTER_BONE,
    BONE_PIVOT, BONE_PIVOT_LOCK_L, BONE_PIVOT_LOCK_R,
    BONE_CENTER_OF_MASS, BONE_BODY_CONTROL_IK,
    BONE_LEFT_FOOT_IK, BONE_RIGHT_FOOT_IK,
    BONE_MASTER_BONE_SNAP, COLLECTION_PIVOT,
)
from ..utils import get_selected_armature


# ---------------------------------------------------------------------------
# SHARED HELPERS
# ---------------------------------------------------------------------------

def _insert_locrot_keyframe():
    """Insert a LocRot keyframe on the currently selected pose bones.
    Compatible with Blender 4.x and 5.x.

    bpy.ops.anim.keyframe_insert_menu was removed in Blender 5.0.
    This wrapper tries the 4.x call first and falls back to the 5.x version.
    """
    try:
        bpy.ops.anim.keyframe_insert_menu(type='BUILTIN_KSI_LocRot')
    except TypeError:
        bpy.ops.anim.keyframe_insert_by_name(type='LocRot')


def _sync_armature_data_name(armature):
    """Keep the armature's data-block name in sync with its object name.

    When AutoRig renames the rig object (e.g. to "MyFig Rig"), the underlying
    armature data-block still has its old name. Several operators use
    bpy.data.armatures[name] to access the data, so they need these to match.
    """
    armature.data.name = armature.name


def _select_bones(armature, *bone_names):
    """Deselect all bones, then select only the named ones."""
    bpy.ops.pose.select_all(action='DESELECT')
    for name in bone_names:
        armature.pose.bones[name].select = True


def _refresh_scene():
    """Nudge the frame back and forth to force Blender to update all constraints."""
    scene = bpy.context.scene
    scene.frame_set(scene.frame_current - 1)
    scene.frame_set(scene.frame_current + 1)

def _get_bone_collections(armature):
    """collections_all was added in Blender 4.1 - fall back to collecitons in 4.0"""
    if hasattr(armature.data, 'collections_all'):
        return armature.data.collections_all
    return armature.data.collections

# ---------------------------------------------------------------------------
# RESET MASTER BONE
# Resets the master bone to its resting position while keeping the IK feet
# planted. Works by:
#   1. Saving the current hip position/rotation
#   2. Reading the world position of the "Master Bone Snap" empty
#   3. Zeroing out the pivot and center-of-mass bones
#   4. Moving the master bone to where the snap empty is
#   5. Restoring hip height so feet stay on the ground
# ---------------------------------------------------------------------------

class ResetMasterBone(bpy.types.Operator):
    """Reset the Master Bone to its default position, keeping IK feet planted"""
    bl_label  = "Reset Master Bone"
    bl_idname = 'rig.reset'

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'ERROR'}, "Make sure you are in Pose Mode")
            return {'CANCELLED'}

        armature = get_selected_armature(context)
        if armature is None:
            self.report({'ERROR'}, "No armature selected")
            return {'CANCELLED'}

        _sync_armature_data_name(armature)

        arm_data   = armature.data
        pose_bones = armature.pose.bones
        scene      = context.scene

        master_bone_snap = pose_bones[BONE_MASTER_BONE_SNAP]

        # --- Step 1: Keyframe current state at frame - 1 ---
        scene.frame_set(scene.frame_current - 1)
        _select_bones(armature, BONE_PIVOT, MASTER_BONE, BONE_BODY_CONTROL_IK,
                      BONE_LEFT_FOOT_IK, BONE_RIGHT_FOOT_IK, BONE_CENTER_OF_MASS)
        _insert_locrot_keyframe()

        # --- Step 2: Save hip state, then zero it out ---
        scene.frame_set(scene.frame_current + 1)
        _select_bones(armature, MASTER_BONE)

        hip_height = pose_bones[BONE_BODY_CONTROL_IK].location[2]
        hip_rot    = pose_bones[BONE_BODY_CONTROL_IK].rotation_quaternion[1]
        pose_bones[BONE_BODY_CONTROL_IK].location[2]            = 0
        pose_bones[BONE_BODY_CONTROL_IK].rotation_quaternion[1] = 0
        _insert_locrot_keyframe()

        # --- Step 3: Move the snap empty to the snap bone's world position ---
        matrix_final = armature.matrix_world @ master_bone_snap.matrix
        snap_empty   = bpy.data.objects[BONE_MASTER_BONE_SNAP]
        snap_empty.matrix_world = matrix_final

        # --- Step 4: Zero out pivot and center of mass ---
        pose_bones[BONE_PIVOT].rotation_euler[0] = 0
        pose_bones[BONE_PIVOT].location          = (0, 0, 0)
        _select_bones(armature, BONE_PIVOT)
        _insert_locrot_keyframe()

        _select_bones(armature, BONE_CENTER_OF_MASS)
        pose_bones[BONE_CENTER_OF_MASS].rotation_euler[2] = 0

        # Zero the IK hip forward/back offset, and compensate the IK feet
        ik_distance = pose_bones[BONE_BODY_CONTROL_IK].location[1]
        _select_bones(armature, BONE_BODY_CONTROL_IK)
        pose_bones[BONE_BODY_CONTROL_IK].location[1] = 0

        # Move both IK feet to compensate for the hip shift
        # (Original used bpy.ops.transform.translate with ~20 args — simplified here)
        _select_bones(armature, BONE_LEFT_FOOT_IK, BONE_RIGHT_FOOT_IK)
        bpy.ops.transform.translate(
            value=(0.0, ik_distance, 0.0),
            orient_type='LOCAL',
        )

        # --- Step 5: Move master bone to the snap empty's position ---
        loc = snap_empty.location
        rot = snap_empty.rotation_euler
        pose_bones[MASTER_BONE].location[0]        = loc[0]
        pose_bones[MASTER_BONE].location[2]        = loc[1]
        pose_bones[MASTER_BONE].rotation_euler[1]  = -rot[2]

        # Restore the hip height and rotation so feet stay planted
        pose_bones[BONE_BODY_CONTROL_IK].location[2]            = hip_height
        pose_bones[BONE_BODY_CONTROL_IK].rotation_quaternion[1] = hip_rot

        # --- Step 6: Keyframe final state and reset Pivot Slide ---
        _select_bones(armature, BONE_BODY_CONTROL_IK, BONE_LEFT_FOOT_IK,
                      BONE_RIGHT_FOOT_IK, MASTER_BONE, BONE_CENTER_OF_MASS,
                      BONE_PIVOT)
        _insert_locrot_keyframe()

        scene.frame_set(scene.frame_current - 1)
        pose_bones[MASTER_BONE].keyframe_insert(data_path='["Pivot Slide"]')
        scene.frame_set(scene.frame_current + 1)
        pose_bones[MASTER_BONE]["Pivot Slide"] = 0
        pose_bones[MASTER_BONE].keyframe_insert(data_path='["Pivot Slide"]')

        _refresh_scene()
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# SNAP MASTER BONE
# Snaps the master bone to the "Master Bone Snap" helper empty's position.
# Similar to Reset but doesn't zero the pivot — it just moves the master
# bone to wherever the snap empty currently is.
# ---------------------------------------------------------------------------

class SnapMasterBone(bpy.types.Operator):
    """Snap the Master Bone to the Master Bone Snap empty"""
    bl_label  = "Snap Master Bone"
    bl_idname = 'snap.masterbone'

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'ERROR'}, "Make sure you are in Pose Mode")
            return {'CANCELLED'}

        armature = get_selected_armature(context)
        if armature is None:
            self.report({'ERROR'}, "No armature selected")
            return {'CANCELLED'}

        _sync_armature_data_name(armature)

        arm_data   = armature.data
        pose_bones = armature.pose.bones
        scene      = context.scene

        master_bone_snap = pose_bones[BONE_MASTER_BONE_SNAP]

        # --- Step 1: Keyframe master bone and center of mass at frame - 1 ---
        scene.frame_set(scene.frame_current - 1)
        _select_bones(armature, MASTER_BONE, BONE_CENTER_OF_MASS)
        _insert_locrot_keyframe()

        # --- Step 2: Save and zero hip ---
        scene.frame_set(scene.frame_current + 1)
        _select_bones(armature, MASTER_BONE)

        hip_height = pose_bones[BONE_BODY_CONTROL_IK].location[2]
        hip_rot    = pose_bones[BONE_BODY_CONTROL_IK].rotation_quaternion[1]
        pose_bones[BONE_BODY_CONTROL_IK].location[2]            = 0
        pose_bones[BONE_BODY_CONTROL_IK].rotation_quaternion[1] = 0
        _insert_locrot_keyframe()

        # --- Step 3: Move snap empty to the snap bone's world position ---
        matrix_final = armature.matrix_world @ master_bone_snap.matrix
        snap_empty   = bpy.data.objects[BONE_MASTER_BONE_SNAP]
        snap_empty.matrix_world = matrix_final

        # --- Step 4: Zero center of mass rotation ---
        scene.frame_set(scene.frame_current + 1)
        _select_bones(armature, BONE_CENTER_OF_MASS)
        pose_bones[BONE_CENTER_OF_MASS].rotation_euler[2] = 0

        # --- Step 5: Move master bone to snap empty ---
        loc = snap_empty.location
        rot = snap_empty.rotation_euler
        pose_bones[MASTER_BONE].location[0]       = loc[0]
        pose_bones[MASTER_BONE].location[2]       = loc[1]
        pose_bones[MASTER_BONE].rotation_euler[1] = -rot[2]

        # Restore hip
        pose_bones[BONE_BODY_CONTROL_IK].location[2]            = hip_height
        pose_bones[BONE_BODY_CONTROL_IK].rotation_quaternion[1] = hip_rot

        # --- Step 6: Keyframe final state ---
        _select_bones(armature, MASTER_BONE, BONE_CENTER_OF_MASS)
        _insert_locrot_keyframe()

        _refresh_scene()
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# PIVOT OPERATORS
# The pivot bone lets you rotate the whole figure around a foot instead of
# the hips. These three operators move the pivot to the left foot, right
# foot, or reset it back to centre.
#
# The general steps for switching pivot to a foot are:
#   1. Keyframe the current pivot + foot position at frame - 1
#   2. Show the hidden "Pivot Controls" bone collection temporarily
#   3. Zero out the foot IK bone (so it doesn't fight the pivot)
#   4. Snap the cursor to the pivot lock bone, then snap the pivot bone there
#   5. Set the Pivot Slide property and keyframe it
#   6. Hide the pivot collection again and keyframe the new state
# ---------------------------------------------------------------------------

class SwitchPivotLeft(bpy.types.Operator):
    """Move the Pivot Bone to the Left Foot"""
    bl_label  = "Left"
    bl_idname = 'pivot.left'

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'ERROR'}, "Make sure you are in Pose Mode")
            return {'CANCELLED'}

        armature = get_selected_armature(context)
        if armature is None:
            self.report({'ERROR'}, "No armature selected")
            return {'CANCELLED'}

        _sync_armature_data_name(armature)

        arm_data   = armature.data
        pose_bones = armature.pose.bones
        scene      = context.scene

        # --- Step 1: Keyframe current state at frame - 1 ---
        scene.frame_set(scene.frame_current - 1)
        _select_bones(armature, BONE_PIVOT, BONE_LEFT_FOOT_IK)
        _insert_locrot_keyframe()
        pose_bones[MASTER_BONE].keyframe_insert(data_path='["Pivot Slide"]')

        # --- Step 2: Show pivot controls, zero IK foot ---
        scene.frame_set(scene.frame_current + 1)
        _get_bone_collections(armature)[COLLECTION_PIVOT].is_visible = True

        pose_bones[BONE_LEFT_FOOT_IK].location = (0, 0, 0)

        # --- Step 3: Snap pivot bone to the left pivot lock bone ---
        _select_bones(armature, BONE_PIVOT_LOCK_L)
        bpy.ops.view3d.snap_cursor_to_selected()
        _select_bones(armature, BONE_PIVOT)
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)

        # --- Step 4: Set Pivot Slide to 1 (left) and keyframe ---
        pose_bones[MASTER_BONE]["Pivot Slide"] = 1
        pose_bones[MASTER_BONE].keyframe_insert(data_path='["Pivot Slide"]')

        # --- Step 5: Hide pivot controls and keyframe final state ---
        _get_bone_collections(armature)[COLLECTION_PIVOT].is_visible = False
        _select_bones(armature, BONE_PIVOT, BONE_LEFT_FOOT_IK)
        _insert_locrot_keyframe()

        _refresh_scene()
        return {'FINISHED'}


class SwitchPivotRight(bpy.types.Operator):
    """Move the Pivot Bone to the Right Foot"""
    bl_label  = "Right"
    bl_idname = 'pivot.right'

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'ERROR'}, "Make sure you are in Pose Mode")
            return {'CANCELLED'}

        armature = get_selected_armature(context)
        if armature is None:
            self.report({'ERROR'}, "No armature selected")
            return {'CANCELLED'}

        _sync_armature_data_name(armature)

        arm_data   = armature.data
        pose_bones = armature.pose.bones
        scene      = context.scene

        # --- Step 1: Keyframe current state at frame - 1 ---
        scene.frame_set(scene.frame_current - 1)
        _select_bones(armature, BONE_PIVOT, BONE_RIGHT_FOOT_IK)
        _insert_locrot_keyframe()
        pose_bones[MASTER_BONE].keyframe_insert(data_path='["Pivot Slide"]')

        # --- Step 2: Show pivot controls, zero IK foot ---
        scene.frame_set(scene.frame_current + 1)
        _get_bone_collections(armature)[COLLECTION_PIVOT].is_visible = True

        pose_bones[BONE_RIGHT_FOOT_IK].location = (0, 0, 0)

        # --- Step 3: Snap pivot bone to the right pivot lock bone ---
        _select_bones(armature, BONE_PIVOT_LOCK_R)
        bpy.ops.view3d.snap_cursor_to_selected()
        _select_bones(armature, BONE_PIVOT)
        bpy.ops.view3d.snap_selected_to_cursor(use_offset=True)

        # --- Step 4: Set Pivot Slide to 0 (right) and keyframe ---
        pose_bones[MASTER_BONE]["Pivot Slide"] = 0
        pose_bones[MASTER_BONE].keyframe_insert(data_path='["Pivot Slide"]')

        # --- Step 5: Hide pivot controls and keyframe final state ---
        _get_bone_collections(armature)[COLLECTION_PIVOT].is_visible = False
        _select_bones(armature, BONE_PIVOT, BONE_RIGHT_FOOT_IK)
        _insert_locrot_keyframe()

        _refresh_scene()
        return {'FINISHED'}


class ResetPivot(bpy.types.Operator):
    """Reset the Pivot Bone back to the centre"""
    bl_label  = "Reset Pivot"
    bl_idname = 'reset.pivot'

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'ERROR'}, "Make sure you are in Pose Mode")
            return {'CANCELLED'}

        armature = get_selected_armature(context)
        if armature is None:
            self.report({'ERROR'}, "No armature selected")
            return {'CANCELLED'}

        _sync_armature_data_name(armature)

        arm_data   = armature.data
        pose_bones = armature.pose.bones
        scene      = context.scene

        # --- Step 1: Keyframe pivot and Pivot Slide at frame - 1 ---
        scene.frame_set(scene.frame_current - 1)
        _select_bones(armature, BONE_PIVOT)
        _insert_locrot_keyframe()
        pose_bones[MASTER_BONE].keyframe_insert(data_path='["Pivot Slide"]')

        # --- Step 2: Zero out pivot bone and right foot IK ---
        scene.frame_set(scene.frame_current + 1)
        pose_bones[BONE_PIVOT].location          = (0, 0, 0)
        pose_bones[BONE_PIVOT].rotation_euler[0] = 0
        pose_bones[BONE_RIGHT_FOOT_IK].location  = (0, 0, 0)

        _select_bones(armature, BONE_PIVOT, BONE_RIGHT_FOOT_IK)
        _insert_locrot_keyframe()

        # --- Step 3: Reset Pivot Slide and keyframe ---
        pose_bones[MASTER_BONE]["Pivot Slide"] = 0
        pose_bones[MASTER_BONE].keyframe_insert(data_path='["Pivot Slide"]')

        _refresh_scene()
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# REGISTRATION
# ---------------------------------------------------------------------------

classes = [
    ResetMasterBone,
    SnapMasterBone,
    SwitchPivotLeft,
    SwitchPivotRight,
    ResetPivot,
]
