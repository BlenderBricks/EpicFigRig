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

# operators/ik_fk.py
# IK/FK snapping operators.
#
# The original code had 8 near-identical operator classes, each setting 6
# global variables before calling a shared helper. This version replaces
# that pattern with a simple IKFKBoneSet data class. Each operator defines
# its bone set once and passes it to the helper directly — no globals needed,
# and no risk of one operator's state accidentally affecting another.

import bpy
import addon_utils
from ..constants import MASTER_BONE


# ---------------------------------------------------------------------------
# BONE SET
# A plain container holding the five bone names that define one limb's
# IK/FK setup. Each operator below creates one of these and passes it to
# the snap helpers.
# ---------------------------------------------------------------------------

class IKFKBoneSet:
    """Holds the bone names needed to perform an IK/FK snap on one limb.

    Attributes:
        fk_bone   -- the main FK control bone (e.g. "RightLeg")
        fk_snap   -- the hidden snap bone that mirrors the FK bone
        ik_bone   -- the main IK control bone (e.g. "RightFootIK")
        ik_snap   -- the hidden snap bone that mirrors the IK bone
        ik_prop   -- the name of the MasterBone custom property that
                     toggles IK on/off (e.g. "RightLegIK")
    """
    def __init__(self, fk_bone, fk_snap, ik_bone, ik_snap, ik_prop):
        self.fk_bone  = fk_bone
        self.fk_snap  = fk_snap
        self.ik_bone  = ik_bone
        self.ik_snap  = ik_snap
        self.ik_prop  = ik_prop
        # The data_path string used for keyframe_insert on the custom property
        self.ik_prop_path = f'["{ik_prop}"]'


# Pre-built bone sets for each limb — defined once here, imported by operators
BONES_RIGHT_LEG = IKFKBoneSet("RightLeg",             "RightLegSnap",
                               "RightFootIK",           "RightFootIKSnap",
                               "RightLegIK")

BONES_LEFT_LEG  = IKFKBoneSet("LeftLeg",              "LeftLegSnap",
                               "LeftFootIK",            "LeftFootIKSnap",
                               "LeftLegIK")

BONES_RIGHT_ARM = IKFKBoneSet("Right Arm Socket Control", "Right Arm Snap",
                               "Right Arm IK",             "Right Arm IK Snap",
                               "RightArmIK")

BONES_LEFT_ARM  = IKFKBoneSet("Left Arm Socket Control",  "Left Arm Snap",
                               "Left Arm IK",              "Left Arm IK Snap",
                               "LeftArmIK")


# ---------------------------------------------------------------------------
# COMPATIBILITY HELPER
# bpy.ops.anim.keyframe_insert_by_name() changed its type string between
# Blender 4.x and 5.x. This wrapper tries both so the addon works on either.
# ---------------------------------------------------------------------------

def _insert_locrot_keyframe():
    """Insert a LocRot keyframe on the currently selected pose bones.
    Compatible with Blender 4.x and 5.x.
    """
    try:
        # Blender 4.x name
        bpy.ops.anim.keyframe_insert_by_name(type="BUILTIN_KSI_LocRot")
    except TypeError:
        # Blender 5.x renamed the keying set
        bpy.ops.anim.keyframe_insert_by_name(type="LocRot")


# ---------------------------------------------------------------------------
# SNAP HELPERS
# The two core functions that do the actual IK<->FK snapping work.
# Both take the armature object and a bone set — no globals required.
#
# How snapping works in brief:
#   The rig has hidden "snap bones" that sit on top of the visible ones.
#   To snap IK→FK: copy the current IK position into the snap bone,
#     turn off IK, then copy the snap bone position onto the FK bone.
#   To snap FK→IK: same idea in reverse.
#   Keyframes are inserted at the current frame so the transition is clean.
# ---------------------------------------------------------------------------

def _ensure_copy_attributes(context):
    """Enable the Copy Attributes addon if it isn't already.
    Returns True if it was already on (so we know not to disable it later).
    """
    state = addon_utils.check("space_view3d_copy_attributes")
    already_on = state != (False, False)
    if not already_on:
        addon_utils.enable("space_view3d_copy_attributes")
    return already_on


def _restore_copy_attributes(was_already_on):
    """Disable Copy Attributes again if we turned it on ourselves."""
    if not was_already_on:
        if addon_utils.check("space_view3d_copy_attributes") == (False, True):
            addon_utils.disable("space_view3d_copy_attributes")


def snap_ik_to_fk(armature, bones):
    """Snap the IK control to match the current FK pose, then switch to FK.

    Steps:
      1. Keyframe all four snap/control bones at the current frame
      2. Copy the FK bone's transform into the FK snap bone
      3. Turn off IK (slider = 0) and keyframe the property
      4. Copy the FK snap bone's transform back onto the FK bone
      5. Refresh the scene
    """
    was_on = _ensure_copy_attributes(bpy.context)

    arm_data  = armature.data
    masterbone = armature.pose.bones[MASTER_BONE]

    # Make snap bones visible temporarily so copy ops can see them
    masterbone["SnapVis"] = 1

    # Step 1 — keyframe all relevant bones at current frame
    bpy.ops.pose.select_all(action='DESELECT')
    arm_data.bones[bones.fk_bone].select  = True
    arm_data.bones[bones.fk_snap].select  = True
    arm_data.bones[bones.ik_bone].select  = True
    arm_data.bones[bones.ik_snap].select  = True
    _insert_locrot_keyframe()

    # Step 2 — copy FK bone → FK snap bone
    bpy.ops.pose.select_all(action='DESELECT')
    arm_data.bones[bones.fk_snap].select    = True
    arm_data.bones.active                   = armature.pose.bones[bones.fk_bone].bone
    bpy.ops.pose.copy_pose_vis_rot()
    bpy.ops.pose.copy_pose_vis_loc()
    _insert_locrot_keyframe()

    # Step 3 — switch to FK (IK slider off) and keyframe it
    masterbone[bones.ik_prop] = 0
    masterbone.keyframe_insert(data_path=bones.ik_prop_path)
    bpy.ops.pose.select_all(action='DESELECT')

    # Step 4 — copy FK snap bone → FK bone
    arm_data.bones[bones.fk_bone].select    = True
    arm_data.bones.active                   = armature.pose.bones[bones.fk_snap].bone
    bpy.ops.pose.copy_pose_vis_loc()
    bpy.ops.pose.copy_pose_vis_rot()
    _insert_locrot_keyframe()

    bpy.ops.pose.select_all(action='DESELECT')

    # Hide snap bones again
    masterbone["SnapVis"] = 0

    # Step 5 — nudge the frame to force a scene refresh
    scene = bpy.context.scene
    scene.frame_set(scene.frame_current - 1)
    scene.frame_set(scene.frame_current + 1)
    bpy.ops.pose.select_all(action='DESELECT')

    _restore_copy_attributes(was_on)


def snap_fk_to_ik(armature, bones):
    """Snap the FK control to match the current IK pose, then switch to IK.

    Steps:
      1. Keyframe all four snap/control bones at the current frame
      2. Copy the FK bone's transform into the FK snap bone
      3. Turn on IK (slider = 1) and keyframe the property
      4. Copy the IK snap bone's location onto the IK bone
      5. Refresh the scene
    """
    was_on = _ensure_copy_attributes(bpy.context)

    arm_data   = armature.data
    masterbone = armature.pose.bones[MASTER_BONE]

    masterbone["SnapVis"] = 1

    # Step 1 — keyframe all relevant bones
    bpy.ops.pose.select_all(action='DESELECT')
    arm_data.bones[bones.fk_bone].select  = True
    arm_data.bones[bones.fk_snap].select  = True
    arm_data.bones[bones.ik_bone].select  = True
    arm_data.bones[bones.ik_snap].select  = True
    _insert_locrot_keyframe()

    # Step 2 — copy FK bone → FK snap bone
    bpy.ops.pose.select_all(action='DESELECT')
    arm_data.bones[bones.fk_snap].select    = True
    arm_data.bones.active                   = armature.pose.bones[bones.fk_bone].bone
    bpy.ops.pose.copy_pose_vis_rot()
    bpy.ops.pose.copy_pose_vis_loc()
    _insert_locrot_keyframe()

    # Step 3 — switch to IK (IK slider on) and keyframe it
    masterbone[bones.ik_prop] = 1
    masterbone.keyframe_insert(data_path=bones.ik_prop_path)
    bpy.ops.pose.select_all(action='DESELECT')

    # Step 4 — copy IK snap bone → IK bone (location only, IK handles rotation)
    arm_data.bones[bones.ik_bone].select    = True
    arm_data.bones.active                   = armature.pose.bones[bones.ik_snap].bone
    bpy.ops.pose.copy_pose_vis_loc()
    _insert_locrot_keyframe()

    bpy.ops.pose.select_all(action='DESELECT')

    masterbone["SnapVis"] = 0

    # Step 5 — refresh
    scene = bpy.context.scene
    scene.frame_set(scene.frame_current - 1)
    scene.frame_set(scene.frame_current + 1)
    bpy.ops.pose.select_all(action='DESELECT')

    _restore_copy_attributes(was_on)


# ---------------------------------------------------------------------------
# OPERATORS
# Each operator just defines which limb it acts on, checks we're in Pose
# Mode, finds the armature, and calls the appropriate snap helper.
# The eight classes follow the same pattern so they're easy to read and
# compare side by side.
# ---------------------------------------------------------------------------

class IKtoFKRightLeg(bpy.types.Operator):
    """Snap the Right Leg IK control to the current FK pose, then switch to FK"""
    bl_label  = "Snap IK to FK"
    bl_idname = 'ik_to.fk_rleg'

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'ERROR'}, "Must be in Pose Mode")
            return {'CANCELLED'}
        snap_ik_to_fk(context.active_object, BONES_RIGHT_LEG)
        return {'FINISHED'}


class IKtoFKLeftLeg(bpy.types.Operator):
    """Snap the Left Leg IK control to the current FK pose, then switch to FK"""
    bl_label  = "Snap IK to FK"
    bl_idname = 'ik_to.fk_lleg'

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'ERROR'}, "Must be in Pose Mode")
            return {'CANCELLED'}
        snap_ik_to_fk(context.active_object, BONES_LEFT_LEG)
        return {'FINISHED'}


class IKtoFKRightArm(bpy.types.Operator):
    """Snap the Right Arm IK control to the current FK pose, then switch to FK"""
    bl_label  = "Snap IK to FK"
    bl_idname = 'ik_to.fk_rarm'

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'ERROR'}, "Must be in Pose Mode")
            return {'CANCELLED'}
        snap_ik_to_fk(context.active_object, BONES_RIGHT_ARM)
        return {'FINISHED'}


class IKtoFKLeftArm(bpy.types.Operator):
    """Snap the Left Arm IK control to the current FK pose, then switch to FK"""
    bl_label  = "Snap IK to FK"
    bl_idname = 'ik_to.fk_larm'

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'ERROR'}, "Must be in Pose Mode")
            return {'CANCELLED'}
        snap_ik_to_fk(context.active_object, BONES_LEFT_ARM)
        return {'FINISHED'}


class FKtoIKRightLeg(bpy.types.Operator):
    """Snap the Right Leg FK control to the current IK pose, then switch to IK"""
    bl_label  = "Snap FK to IK"
    bl_idname = 'fk_to.ik_rleg'

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'ERROR'}, "Must be in Pose Mode")
            return {'CANCELLED'}
        snap_fk_to_ik(context.active_object, BONES_RIGHT_LEG)
        return {'FINISHED'}


class FKtoIKLeftLeg(bpy.types.Operator):
    """Snap the Left Leg FK control to the current IK pose, then switch to IK"""
    bl_label  = "Snap FK to IK"
    bl_idname = 'fk_to.ik_lleg'

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'ERROR'}, "Must be in Pose Mode")
            return {'CANCELLED'}
        snap_fk_to_ik(context.active_object, BONES_LEFT_LEG)
        return {'FINISHED'}


class FKtoIKRightArm(bpy.types.Operator):
    """Snap the Right Arm FK control to the current IK pose, then switch to IK"""
    bl_label  = "Snap FK to IK"
    bl_idname = 'fk_to.ik_rarm'

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'ERROR'}, "Must be in Pose Mode")
            return {'CANCELLED'}
        snap_fk_to_ik(context.active_object, BONES_RIGHT_ARM)
        return {'FINISHED'}


class FKtoIKLeftArm(bpy.types.Operator):
    """Snap the Left Arm FK control to the current IK pose, then switch to IK"""
    bl_label  = "Snap FK to IK"
    bl_idname = 'fk_to.ik_larm'

    def execute(self, context):
        if context.mode != 'POSE':
            self.report({'ERROR'}, "Must be in Pose Mode")
            return {'CANCELLED'}
        snap_fk_to_ik(context.active_object, BONES_LEFT_ARM)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# REGISTRATION
# ---------------------------------------------------------------------------

classes = [
    IKtoFKRightLeg,
    IKtoFKLeftLeg,
    IKtoFKRightArm,
    IKtoFKLeftArm,
    FKtoIKRightLeg,
    FKtoIKLeftLeg,
    FKtoIKRightArm,
    FKtoIKLeftArm,
]
