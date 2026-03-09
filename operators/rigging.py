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

# operators/rigging.py
# The core rigging operators.
#
# AutoRig   -- identifies all selected Mecabricks parts by brick ID, appends
#              the EpicFigRig .blend file, and parents each part to the correct
#              bone. Also handles capes, skirts and Lepin hands.
# PropRigA  -- parents selected objects to Prop Bone A (default right hand)
# PropRigB  -- parents selected objects to Prop Bone B (default left hand)
# ProxRig   -- proximity-based fallback: parents unrecognised parts to the
#              nearest allowed bone

import os
import bpy
import addon_utils
import mathutils

from ..constants import (
    MASTER_BONE,
    BONE_TORSO, BONE_TORSO_ROCK, BONE_HEAD, BONE_HEAD_ACCESSORY,
    BONE_LEFT_ARM, BONE_RIGHT_ARM, BONE_LEFT_LEG_INVERT, BONE_RIGHT_LEG_INVERT,
    BONE_LEFT_HAND, BONE_RIGHT_HAND,
    BONE_LEFT_FOOT_IK, BONE_RIGHT_FOOT_IK,
    BONE_PROP_A_TRANSFORM, BONE_PROP_B_TRANSFORM,
    BRICK_LEG_LEFT, BRICK_LEG_RIGHT,
    BRICK_CHILD_LEG, BRICK_CHILD_LEG_SINGLE,
    BRICK_TORSO, BRICK_TORSO_GEAR,
    BRICK_ARM_LEFT, BRICK_ARM_RIGHT,
    BRICK_HAND,
    BRICK_HEAD, BRICK_HEAD_ACCESSORY,
    BRICK_HEAD_CLOTHING, BRICK_HEAD_VISORS,
    BRICK_DRESS, BRICK_DRESS_REGULAR,
    BRICK_CAPE, BRICK_SKIRT,
)
from ..utils import get_selected_armature, create_visibility_driver

# Path to the addon folder — used to locate the .blend files to append
_ADDON_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


# ---------------------------------------------------------------------------
# APPEND HELPERS
# These load the rig, cape rig, and skirt rig from the addon's .blend files.
# ---------------------------------------------------------------------------

def _append_rig():
    """Append the main EpicFigRig collection from Append.blend."""
    bpy.ops.wm.append(
        filename="The EpicFigRig",
        directory=os.path.join(_ADDON_DIR, "Append.blend", "Collection", ""),
    )


def _append_cape():
    """Append the CapeRig collection from Cape_Rig.blend."""
    bpy.ops.wm.append(
        filename="CapeRig",
        directory=os.path.join(_ADDON_DIR, "Cape_Rig.blend", "Collection", ""),
    )


def _append_skirt():
    """Append the SkirtRig collection from Skirt_Rig.blend."""
    bpy.ops.wm.append(
        filename="SkirtRig",
        directory=os.path.join(_ADDON_DIR, "Skirt_Rig.blend", "Collection", ""),
    )


# ---------------------------------------------------------------------------
# LEPIN HAND BOOLEAN DRIVER
# Lepin-style hands use a Boolean modifier to cut the peg hole. The modifier
# visibility is driven by the "Lepin Hands" custom property on MasterBone so
# it can be toggled on/off from the panel.
# ---------------------------------------------------------------------------

def _add_lepin_boolean_driver(fig, rig, bool_obj_name):
    """Add a Boolean modifier to fig, driven by the rig's Lepin Hands property.

    Arguments:
        fig           -- the hand mesh object
        rig           -- the armature object
        bool_obj_name -- name of the boolean cutter object ("RHBool" or "RLBool")
    """
    fig.select_set(True)
    bpy.context.view_layer.objects.active = fig

    mod = fig.modifiers.new("Boolean", 'BOOLEAN')
    mod.object = bpy.data.objects[bool_obj_name]
    if bpy.app.version >= (5,0,0):
        mod.solver = 'FLOAT'
    elif bpy.app.version >= (4,0,0):
        mod.solver = 'FAST'
    else: 
        mod.solver = 'FLOAT'

    armature_data = bpy.data.armatures[rig.name]

    for driver_path in ("show_viewport", "show_render"):
        fcurve = mod.driver_add(driver_path)
        driver = fcurve.driver

        var            = driver.variables.new()
        var.type       = 'SINGLE_PROP'
        var.name       = "hide"
        target         = var.targets[0]
        target.id_type = 'ARMATURE'
        target.id      = armature_data
        target.data_path = '["Lepin Hands"]'

        driver.expression = "hide"


# ---------------------------------------------------------------------------
# AUTORIG — PARENT HELPER
# Used inside AutoRig to parent one mesh part to a bone, copy its material
# to the smear object, and set up the smear visibility driver.
# ---------------------------------------------------------------------------

def _parent_to_bone(fig, rig, bone_name, use_smear, smear_prop,
                    empty_name, context):
    """Parent a mesh object to a bone on the rig, and set up its smear driver.

    Arguments:
        fig        -- the mesh object to parent
        rig        -- the armature object
        bone_name  -- the bone to parent to
        use_smear  -- True if this part has a paired smear mesh (arms, legs)
        smear_prop -- the data path of the smear custom property, e.g. '["LLegSmear"]'
        empty_name -- name of the empty used for transform normalisation
        context    -- the Blender context
    """
    fig.select_set(True)

    # Give this object its own copy of the mesh data so drivers don't
    # accidentally share data with other instances
    fig.data = fig.data.copy()

    # Set up the smear visibility driver
    # use_smear=True means the part has two properties driving its visibility
    # (the base SmearsTest plus a per-limb smear), so we pass the bonus path
    if use_smear:
        create_visibility_driver(
            obj_name      = fig.name,
            armature_name = rig.name,
            prop_path     = '["SmearsTest"]',
            bonus_path    = smear_prop,
            expression    = "hide + hide2",
        )
    else:
        create_visibility_driver(
            obj_name      = fig.name,
            armature_name = rig.name,
            prop_path     = '["SmearsTest"]',
            expression    = "hide",
        )

    # Normalise transforms if the option is enabled
    if context.scene.normalize_mini:
        fig.matrix_world = bpy.data.objects[empty_name].matrix_world.copy()

    # Parent to the bone
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    rig.data.bones.active = rig.data.bones[bone_name]
    bpy.ops.object.parent_set(type='BONE', keep_transform=True)
    bpy.ops.object.select_all(action='DESELECT')


# ---------------------------------------------------------------------------
# AUTORIG OPERATOR
# ---------------------------------------------------------------------------

class AutoRig(bpy.types.Operator):
    """Auto-rig the selected Mecabricks minifigure"""
    bl_label  = "  Rig Selected Minifigure  "
    bl_idname = 'auto.rig'

    def execute(self, context):

        # Enable Copy Attributes addon if needed (used for pose copying)
        addon_was_on = addon_utils.check("space_view3d_copy_attributes") != (False, False)
        if not addon_was_on:
            addon_utils.enable("space_view3d_copy_attributes")

        selected_objects = list(context.selected_objects)

        # --- Get the figure's collection name to use as the rig name ---
        context.view_layer.objects.active = selected_objects[1]
        col   = context.active_object.users_collection[0]
        mname = col.name

        # Set that collection as the active one so the appended rig lands in it
        for collection in context.view_layer.layer_collection.children:
            if collection.name == mname:
                context.view_layer.active_layer_collection = collection

        # --- Remove parent empty if present ---
        # Bug fix: original compared .parent == True, but .parent returns an
        # object or None, never a boolean. Fixed to use 'is not None'.
        if selected_objects[0].parent is not None:
            empty = selected_objects[0].parent
            bpy.data.objects.remove(empty)

        # --- Detect child figure (shorter legs) ---
        is_child = any(
            num[:5] in fig.data.name
            for fig in selected_objects
            for num in BRICK_CHILD_LEG
        )

        # --- Append the rig ---
        _append_rig()

        rig = bpy.data.objects['Rig']

        # Hide the bone shapes collection
        bpy.data.collections['BoneShapes'].hide_viewport = True
        bpy.data.collections['BoneShapes'].hide_render   = True

        collections = rig.data.collections_all if hasattr(rig.data, "collections_all") else rig.data.collections

        for col_name in ["Pivot Controls", "BodyRockControl", "Smear Loc"]:
            if col_name in collections:
                collections[col_name].is_visible = False

        # --- Move rig to the hip brick's location ---
        loc = selected_objects[0]
        for obj in selected_objects:
            if "3814" in obj.data.name:
                if context.scene.normalize_mini:
                    obj.matrix_world = bpy.data.objects["Hip Empty"].matrix_world.copy()
                loc = obj
        rig.location = loc.location

        # --- Parent each selected object to its matching bone ---
        for fig in selected_objects:

            # Child legs / single child leg (e.g. short leg piece)
            try:

                _ = fig.data.name
            except ReferenceError:
                continue

            for num in BRICK_CHILD_LEG_SINGLE:
                if num in fig.data.name:
                    _parent_to_bone(fig, rig, BONE_TORSO, False,
                                    '["LLegSmear"]', "Hip Empty", context)
                    rig.data.bones[BONE_RIGHT_FOOT_IK].hide = True
                    rig.data.bones[BONE_LEFT_FOOT_IK].hide  = True
                    rig.data.bones["RightLeg"].hide          = True
                    rig.data.bones["LeftLeg"].hide           = True

            # Dress bricks (replace legs)
            for brick_list in (BRICK_DRESS, BRICK_DRESS_REGULAR):
                for num in brick_list:
                    if num in fig.data.name:
                        _parent_to_bone(fig, rig, BONE_TORSO, False,
                                        '["LLegSmear"]', "Hip Empty", context)
                        rig.data.bones[BONE_RIGHT_FOOT_IK].hide = True
                        rig.data.bones[BONE_LEFT_FOOT_IK].hide  = True
                        rig.data.bones["RightLeg"].hide          = True
                        rig.data.bones["LeftLeg"].hide           = True

            # Left leg
            for num in BRICK_LEG_LEFT:
                if num in fig.data.name:
                    _parent_to_bone(fig, rig, BONE_LEFT_LEG_INVERT, True,
                                    '["LLegSmear"]', "Left Leg Empty", context)
                    bpy.data.objects["LlegS"].material_slots[0].material = \
                        fig.material_slots[0].material

            # Right leg
            for num in BRICK_LEG_RIGHT:
                if num in fig.data.name:
                    _parent_to_bone(fig, rig, BONE_RIGHT_LEG_INVERT, True,
                                    '["RLegSmear"]', "Right Leg Empty", context)
                    bpy.data.objects["RlegS"].material_slots[0].material = \
                        fig.material_slots[0].material

            # IK hip brick
            if "3815" in fig.data.name:
                _parent_to_bone(fig, rig, BONE_TORSO, False,
                                '["LLegSmear"]', "Hip Empty", context)

            # Torso gear / backpack (adjusts head and torso bone scales)
            for num in BRICK_TORSO_GEAR:
                if num in fig.data.name:
                    _parent_to_bone(fig, rig, BONE_TORSO_ROCK, False,
                                    '["LLegSmear"]', "Head Empty", context)
                    rig.pose.bones[MASTER_BONE]["Head Bone Transform"] = 1.5
                    rig.pose.bones[MASTER_BONE]["Torso Bone Scale"]    = 0.75

            # Torso
            for num in BRICK_TORSO:
                if num in fig.data.name:
                    _parent_to_bone(fig, rig, BONE_TORSO_ROCK, False,
                                    '["LLegSmear"]', "Hip Empty", context)

            # Left arm
            for num in BRICK_ARM_LEFT:
                if num in fig.data.name:
                    _parent_to_bone(fig, rig, BONE_LEFT_ARM, True,
                                    '["LArmSmear"]', "Left Arm Empty", context)
                    bpy.data.objects["LarmS"].material_slots[0].material = \
                        fig.material_slots[0].material

            # Right arm
            for num in BRICK_ARM_RIGHT:
                if num in fig.data.name:
                    _parent_to_bone(fig, rig, BONE_RIGHT_ARM, True,
                                    '["RArmSmear"]', "Right Arm Empty", context)
                    bpy.data.objects["RarmS"].material_slots[0].material = \
                        fig.material_slots[0].material

            # Head
            for num in BRICK_HEAD:
                if num in fig.data.name:
                    _parent_to_bone(fig, rig, BONE_HEAD, False,
                                    '["LLegSmear"]', "Head Empty", context)

            # Head accessories (hats, hair, helmets)
            for num in BRICK_HEAD_ACCESSORY:
                if num in fig.data.name:
                    _parent_to_bone(fig, rig, BONE_HEAD_ACCESSORY, False,
                                    '["LLegSmear"]', "Hair Empty", context)
                    rig.pose.bones[MASTER_BONE]["Head Bone Scale"]           = 0.85
                    rig.pose.bones[MASTER_BONE]["Head Accessory Bone Scale"] = 1.0
                    break

            # Head clothing (hoods, cloaks)
            for num in BRICK_HEAD_CLOTHING:
                if num in fig.data.name:
                    _parent_to_bone(fig, rig, BONE_HEAD_ACCESSORY, False,
                                    '["LLegSmear"]', "Hair Empty", context)

            # Head visors
            for num in BRICK_HEAD_VISORS:
                if num in fig.data.name:
                    _parent_to_bone(fig, rig, BONE_HEAD_ACCESSORY, False,
                                    '["LLegSmear"]', "Hair Empty", context)

            # Cape
            for num in BRICK_CAPE:
                if num in fig.data.name:
                    self._rig_cape(fig, rig, mname, context)

            # Skirt
            for num in BRICK_SKIRT:
                if num in fig.data.name:
                    self._rig_skirt(fig, rig, mname, context)

            # Hands — find closest hand bone and parent, with Lepin boolean
            for num in BRICK_HAND:
                if num in fig.data.name:
                    self._rig_hand(fig, rig, context)

        # --- Post-rig setup ---
        rig.select_set(True)

        if is_child:
            rig.pose.bones[MASTER_BONE]["Leg Height"]          = 2.0
            rig.pose.bones[MASTER_BONE]["Prop Bones Transform"] = 2.0
        else:
            rig.pose.bones[MASTER_BONE]["Leg Height"] = 0.0

        # Hide prop bones by default
        rig.pose.bones[MASTER_BONE]["Prop Bone A Visibility"] = 0
        rig.pose.bones[MASTER_BONE]["Prop Bone B Visibility"] = 0

        # Hide Lepin boolean helpers
        context.view_layer.objects['RHBool'].hide_viewport = True
        context.view_layer.objects['RLBool'].hide_viewport = True

        # Rename all rig objects and collections to include the figure name
        r = " Rig"
        b = " Bone Shapes"
        bpy.data.armatures["Rig"].name              = mname + r
        rig.name                                    = mname + r
        bpy.data.collections["BoneShapes"].name     = mname + b
        bpy.data.collections["The EpicFigRig"].name = mname + r

        # Rename smear/boolean objects so they don't clash with the next rig
        objects = bpy.data.objects
        objects["LlegS"].name  = mname + " LlegS"
        objects["RlegS"].name  = mname + " RlegS"
        objects["LarmS"].name  = mname + " LarmS"
        objects["RarmS"].name  = mname + " RarmS"
        objects["RHBool"].name = mname + " RHBool"
        objects["RLBool"].name = mname + " RLBool"

        # Restore Copy Attributes state
        if not addon_was_on:
            if addon_utils.check("space_view3d_copy_attributes") == (False, True):
                addon_utils.disable("space_view3d_copy_attributes")

        return {'FINISHED'}

    # -----------------------------------------------------------------------
    # CAPE RIGGING
    # -----------------------------------------------------------------------

    def _rig_cape(self, fig, rig, mname, context):
        """Append the cape rig and connect it to the main rig's arm bones."""

        # Build the cape mesh object name from the brick ID
        currentcape = fig.data.name[:5] + ".append"
        if currentcape == "34721.append":
            currentcape = "34721p1.append"

        _append_cape()
        rigcape          = bpy.data.objects['CapeRig']
        rigcape.location = fig.location

        # Connect cape rig bones to the main rig's arm bones
        rigcape.pose.bones['LL'].constraints['Transformation'].target       = rig
        rigcape.pose.bones['LL'].constraints['Transformation'].subtarget    = BONE_LEFT_ARM
        rigcape.pose.bones['LL'].constraints['Transformation.001'].target   = rig
        rigcape.pose.bones['LL'].constraints['Transformation.001'].subtarget = "Left Arm Socket Control"

        rigcape.pose.bones['RR'].constraints['Transformation'].target       = rig
        rigcape.pose.bones['RR'].constraints['Transformation'].subtarget    = BONE_RIGHT_ARM
        rigcape.pose.bones['RR'].constraints['Transformation.001'].target   = rig
        rigcape.pose.bones['RR'].constraints['Transformation.001'].subtarget = "Right Arm Socket Control"

        # Transfer the cape mesh material from the original brick
        bpy.data.objects[currentcape].material_slots[0].material = \
            fig.material_slots[0].material

        # Delete the original flat cape brick and replace with the rigged cape
        bpy.ops.object.select_all(action='DESELECT')
        fig.select_set(True)
        bpy.context.view_layer.objects.active = fig
        bpy.ops.object.delete()
        fig = rigcape

        _parent_to_bone(fig, rig, BONE_TORSO_ROCK, False,
                        '["LLegSmear"]', "Head Empty", context)

        # Move the cape mesh into the CapeRig collection
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = None
        context.scene.objects[currentcape].select_set(True)

        for obj in bpy.context.selected_objects:
            bpy.context.view_layer.objects.active = obj
        cape_mesh = bpy.context.active_object

        bpy.data.collections['CapeRig'].objects.link(cape_mesh)
        bpy.data.collections['Cape Appends'].objects.unlink(cape_mesh)
        bpy.ops.object.select_all(action='DESELECT')

        # Clean up the temporary Cape Appends collection
        append_col = bpy.data.collections.get('Cape Appends')
        if append_col:
            for obj in append_col.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(append_col)

        # Rename cape objects and collections
        bpy.data.objects[currentcape].name        = mname + " Cape"
        bpy.data.objects['CapeRig'].name           = mname + " Cape Rig"
        bpy.data.collections['CapeRig'].name       = mname + " Cape Rig"
        bpy.data.collections['ShapesBones'].hide_viewport = True
        bpy.data.collections['ShapesBones'].hide_render   = True

    # -----------------------------------------------------------------------
    # SKIRT RIGGING
    # -----------------------------------------------------------------------

    def _rig_skirt(self, fig, rig, mname, context):
        """Append the skirt rig and connect it to the main rig's leg bones."""

        currentskirt = fig.data.name[:4] + ".append"

        _append_skirt()
        rigskirt          = bpy.data.objects['SkirtRig']
        rigskirt.location = fig.location

        # Connect skirt rig bones to the main rig's leg bones
        for bone_name in ('Front.L', 'Back.L'):
            rigskirt.pose.bones[bone_name].constraints['Transformation'].target    = rig
            rigskirt.pose.bones[bone_name].constraints['Transformation'].subtarget = "LeftLeg"

        for bone_name in ('Front.R', 'Back.R'):
            rigskirt.pose.bones[bone_name].constraints['Transformation'].target    = rig
            rigskirt.pose.bones[bone_name].constraints['Transformation'].subtarget = "RightLeg"

        bpy.data.objects[currentskirt].material_slots[0].material = \
            fig.material_slots[0].material

        # Delete original and replace with rigged skirt
        bpy.ops.object.select_all(action='DESELECT')
        fig.select_set(True)
        bpy.context.view_layer.objects.active = fig
        bpy.ops.object.delete()
        fig = rigskirt

        _parent_to_bone(fig, rig, BONE_TORSO, False,
                        '["LLegSmear"]', "Skirt Empty", context)

        # Move skirt mesh into the SkirtRig collection
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = None
        context.scene.objects[currentskirt].select_set(True)

        for obj in bpy.context.selected_objects:
            bpy.context.view_layer.objects.active = obj
        skirt_mesh = bpy.context.active_object

        bpy.data.collections['SkirtRig'].objects.link(skirt_mesh)
        bpy.data.collections['Skirt Appends'].objects.unlink(skirt_mesh)
        bpy.ops.object.select_all(action='DESELECT')

        # Clean up temporary collection
        append_col = bpy.data.collections.get('Skirt Appends')
        if append_col:
            for obj in append_col.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(append_col)

        # Rename
        bpy.data.objects[currentskirt].name         = mname + " Cape"
        bpy.data.objects['SkirtRig'].name            = mname + " Cape Rig"
        bpy.data.collections['SkirtRig'].name        = mname + " Cape Rig"
        bpy.data.collections['SkirtShapes'].hide_viewport = True
        bpy.data.collections['SkirtShapes'].hide_render   = True

    # -----------------------------------------------------------------------
    # HAND RIGGING
    # -----------------------------------------------------------------------

    def _rig_hand(self, fig, rig, context):
        """Find the closest hand bone and parent the hand to it."""

        # Get world-space positions of both hand bones directly from the
        # pose bone matrices — no need to enter/exit pose mode
        left_pb  = rig.pose.bones[BONE_LEFT_HAND]
        right_pb = rig.pose.bones[BONE_RIGHT_HAND]

        left_pos  = (rig.matrix_world @ left_pb.matrix).translation
        right_pos = (rig.matrix_world @ right_pb.matrix).translation

        dist_left  = (left_pos  - fig.location).length
        dist_right = (right_pos - fig.location).length

        if dist_left < dist_right:
            handname   = BONE_LEFT_HAND
            bool_obj   = "RLBool"
            empty_name = "Left Hand Empty"
        else:
            handname   = BONE_RIGHT_HAND
            bool_obj   = "RHBool"
            empty_name = "Right Hand Empty"

        _add_lepin_boolean_driver(fig, rig, bool_obj)
        _parent_to_bone(fig, rig, handname, False,
                        '["LLegSmear"]', empty_name, context)

# ---------------------------------------------------------------------------
# PROP RIG OPERATORS
# PropRigA and PropRigB are nearly identical — they parent selected objects
# to one of the two prop bones. A shared helper handles the common logic.
# ---------------------------------------------------------------------------

def _rig_prop(context, bone_name, visibility_prop):
    """Parent selected mesh objects to a prop bone on the selected armature.

    Arguments:
        context         -- the Blender context
        bone_name       -- the prop bone to parent to (e.g. "AP Bone Transform")
        visibility_prop -- the MasterBone property that controls this prop's
                           visibility (e.g. "Prop Bone A Visibility")
    """
    armature = get_selected_armature(context)
    if armature is None:
        return False

    # Find the mesh object(s) in the selection
    mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
    if not mesh_objects:
        return False

    # Make the prop bone visible
    armature.pose.bones[MASTER_BONE][visibility_prop] = 1

    for mesh_obj in mesh_objects:
        # Switch to edit mode to set the active bone, then back to object mode
        bpy.ops.object.select_all(action='DESELECT')
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        armature.pose.bones[MASTER_BONE][visibility_prop] = 1
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.object.mode_set(mode='EDIT')

        armature.data.edit_bones.active = armature.data.edit_bones[bone_name]

        bpy.ops.object.mode_set(mode='OBJECT')

        # Parent the mesh to the active bone on the armature
        bpy.ops.object.select_all(action='DESELECT')
        mesh_obj.select_set(True)
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.parent_set(type='BONE', keep_transform=True)

    return True


class PropRigA(bpy.types.Operator):
    """Rig selected object(s) to Prop Bone A (default Right Hand)"""
    bl_label  = "  Prop A  "
    bl_idname = 'propa.rig'

    def execute(self, context):
        success = _rig_prop(context, BONE_PROP_A_TRANSFORM, "Prop Bone A Visibility")
        if not success:
            self.report({'ERROR'}, "Select a mesh and an armature")
            return {'CANCELLED'}
        return {'FINISHED'}


class PropRigB(bpy.types.Operator):
    """Rig selected object(s) to Prop Bone B (default Left Hand)"""
    bl_label  = "  Prop B  "
    bl_idname = 'propb.rig'

    def execute(self, context):
        success = _rig_prop(context, BONE_PROP_B_TRANSFORM, "Prop Bone B Visibility")
        if not success:
            self.report({'ERROR'}, "Select a mesh and an armature")
            return {'CANCELLED'}
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# PROXIMITY RIG
# Fallback for objects that don't have a recognised Mecabricks brick ID.
# Finds the nearest allowed bone and parents to that.
# ---------------------------------------------------------------------------

class ProxRig(bpy.types.Operator):
    """Parent additional selected objects to the nearest bone on the rig.
    Use this after AutoRig for any parts it couldn't identify automatically.
    Not 100% reliable with non-standard bricks."""
    bl_label  = "Additional Objects"
    bl_idname = 'prox.rig'

    # Bones that ProxRig is allowed to parent to — same set AutoRig uses
    ALLOWED_BONES = [
        BONE_RIGHT_HAND, BONE_LEFT_HAND,
        BONE_RIGHT_ARM,  BONE_LEFT_ARM,
        BONE_TORSO,      BONE_TORSO_ROCK,
        BONE_HEAD,       BONE_HEAD_ACCESSORY,
        BONE_RIGHT_LEG_INVERT, BONE_LEFT_LEG_INVERT,
    ]

    def execute(self, context):
        armature = context.active_object
        if armature is None or armature.type != 'ARMATURE':
            self.report({'ERROR'}, "Make the rig the active object")
            return {'CANCELLED'}

        mesh_objects = [obj for obj in context.selected_objects
                        if obj.type != 'ARMATURE']
        if not mesh_objects:
            self.report({'ERROR'}, "No mesh objects selected")
            return {'CANCELLED'}

        for obj in mesh_objects:
            if obj.parent == armature:
                self.report({'INFO'}, f"'{obj.name}' is already parented, skipping")
                continue

            closest = self._find_closest_bone(armature, obj)
            if closest is None:
                self.report({'WARNING'}, f"No nearby bone found for '{obj.name}'")
                continue

            # Store the world matrix so we can restore it after parenting
            world_matrix = obj.matrix_world.copy()

            obj.parent      = armature
            obj.parent_bone = closest.name
            obj.parent_type = 'BONE'
            obj.matrix_world = world_matrix

            self.report({'INFO'}, f"Parented '{obj.name}' to '{closest.name}'")

        return {'FINISHED'}

    def _find_closest_bone(self, armature, obj):
        """Return the closest allowed pose bone to obj's world position."""
        obj_loc      = obj.matrix_world.translation
        closest_bone = None
        min_dist     = float('inf')

        for pb in armature.pose.bones:
            if pb.name not in self.ALLOWED_BONES:
                continue

            # Check distance to both head and tail of the bone
            head = armature.matrix_world @ pb.bone.head_local
            tail = armature.matrix_world @ pb.bone.tail_local
            dist = min((obj_loc - head).length, (obj_loc - tail).length)

            if dist < min_dist:
                min_dist     = dist
                closest_bone = pb

        return closest_bone


# ---------------------------------------------------------------------------
# REGISTRATION
# ---------------------------------------------------------------------------

classes = [
    AutoRig,
    PropRigA,
    PropRigB,
    ProxRig,
]
