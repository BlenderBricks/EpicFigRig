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

# panels.py
# All Panel classes and small UI-toggle operators (tab switches, hand/leg menu toggles).
# Operators that do actual rigging or bone manipulation live in the operators/ folder.

import bpy
from .constants import MASTER_BONE


# ---------------------------------------------------------------------------
# POLL HELPER
# A single function used by all sub-panels that need an active EpicFigRig
# armature. Centralising this means if the rig ever changes (e.g. MasterBone
# gets renamed), there's only one place to update.
# ---------------------------------------------------------------------------

def is_epic_rig_active(context):
    """Return True if the active object is an EpicFigRig armature.

    Used as the poll check for all sub-panels that show rig properties.
    This prevents panels from crashing when a non-rig object is active,
    and also hides the panels cleanly when you're working on anything else
    in the scene — including other armatures that aren't EpicFigRigs.
    """
    obj = context.active_object
    return (
        obj is not None
        and obj.type == 'ARMATURE'
        and MASTER_BONE in obj.pose.bones
    )


# ---------------------------------------------------------------------------
# MAIN PANEL
# The top-level panel that always shows in the EpicFigRig tab.
# Contains the rigging buttons and the Main/Advanced tab switcher.
# Sub-panels are registered separately with bl_parent_id pointing here.
# ---------------------------------------------------------------------------

class EpicFigRigPanel(bpy.types.Panel):
    bl_label       = "The EpicFigRig"
    bl_idname      = "EPIC_FIGRIG_PT_PANEL"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'EpicFigRig 2.0' 

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        # User manual link
        box = layout.box()
        box.operator(
            "wm.url_open",
            text="JabLab User Manual",
            icon='URL',
            emboss=False,
        ).url = "https://docs.google.com/document/d/1DUYLJnJKtjcgSzyi8djITjD8QRpN_i40ziz6wifAG0Q/edit?usp=sharing"

        # Main rigging button
        box = layout.box()
        box.operator('auto.rig')

        # Secondary rigging tools
        box = layout.box()
        box.label(text="More Rigging:")
        box.prop(scene, "normalize_mini")
        box.operator('prox.rig')
        row = box.row(align=True)
        row.operator('propa.rig')
        row.operator('propb.rig')

        # Tab switcher — sets scene.EpicRigTabs to 0 (Main) or 1 (Advanced)
        layout.separator()
        layout.label(text="Rig Settings:", icon='OPTIONS')
        row = layout.row(align=True)
        row.operator('main.tab')
        row.operator('advanced.tab')


# ---------------------------------------------------------------------------
# MAIN TAB PANELS  (visible when EpicRigTabs == 0)
# ---------------------------------------------------------------------------

class EpicButtons(bpy.types.Panel):
    """Accessory snapping, pivot controls, master bone controls."""
    bl_label       = "Epic Buttons"
    bl_idname      = "EPIC_PT_BUTTONS"
    bl_parent_id   = "EPIC_FIGRIG_PT_PANEL"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'EpicFigRig 2.0'

    @classmethod
    def poll(cls, context):
        # Only show on the Main tab AND when an EpicFigRig armature is active
        return context.scene.EpicRigTabs == 0 and is_epic_rig_active(context)

    def draw(self, context):
        layout = self.layout

        # Accessory snapping
        layout.label(text="Accessory Snapping:", icon='SNAP_ON')
        row = layout.row(align=True)
        row.operator('snap_left.add')
        row.operator('snap_right.add')
        layout.operator('snap_head.add')

        layout.separator()

        # Pivot foot switch
        layout.label(text="Pivot Foot Switch:", icon='ARROW_LEFTRIGHT')
        row = layout.row(align=True)
        row.operator('pivot.left')
        row.operator('pivot.right')
        layout.operator('reset.pivot')

        layout.separator()

        # Master bone
        layout.label(text="Master Bone Control:")
        layout.operator('rig.reset')
        layout.operator('snap.masterbone')


class ArmMenu(bpy.types.Panel):
    """Per-arm IK/FK controls. Toggle between Left and Right arm with the
    buttons at the top of the panel."""
    bl_label       = "Arm Menu"
    bl_idname      = "ARM_MENU"
    bl_parent_id   = "EPIC_FIGRIG_PT_PANEL"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'EpicFigRig 2.0'
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.EpicRigTabs == 0 and is_epic_rig_active(context)

    def draw(self, context):
        layout     = self.layout
        masterbone = context.active_object.pose.bones[MASTER_BONE]

        # Which arm is currently shown is stored in the rig's "Hand Menu" property
        # 0 = Left arm, 1 = Right arm
        showing_left = masterbone["Hand Menu"] == 0

        # Tab buttons — active side gets the highlighted icon
        row = layout.row(align=True)
        row.operator('left_hand.menu',  icon='EVENT_L' if showing_left  else 'NONE')
        row.operator('right_hand.menu', icon='EVENT_R' if not showing_left else 'NONE')

        layout.separator()

        if showing_left:
            self._draw_arm(layout, masterbone,
                           ik_prop     = '["LeftArmIK"]',
                           snap_to_ik  = 'fk_to.ik_larm',
                           snap_to_fk  = 'ik_to.fk_larm',
                           invert_prop = '["Invert Left Arm"]',
                           mirror_prop = '["Mirror Left Arm"]',
                           smear_prop  = '["LArmSmear"]',
                           clay_prop   = '["Clay Left Arm Visibility"]')
        else:
            self._draw_arm(layout, masterbone,
                           ik_prop     = '["RightArmIK"]',
                           snap_to_ik  = 'fk_to.ik_rarm',
                           snap_to_fk  = 'ik_to.fk_rarm',
                           invert_prop = '["Invert Right Arm"]',
                           mirror_prop = '["Mirror Right Arm"]',
                           smear_prop  = '["RArmSmear"]',
                           clay_prop   = '["Clay Right Arm Visibility"]')

        layout.separator()

        # These properties apply to both arms so they sit outside the if/else
        layout.prop(masterbone, '["Lepin Hands"]',       slider=True)
        layout.prop(masterbone, '["Auto Arm Rotation"]', slider=True)

    def _draw_arm(self, layout, masterbone, ik_prop, snap_to_ik, snap_to_fk,
                  invert_prop, mirror_prop, smear_prop, clay_prop):
        """Draw the controls for one arm. Called by draw() with the correct
        property names for whichever arm is currently selected.

        Splitting the repeated left/right logic into a helper like this means
        any future changes only need to be made once.
        """
        layout.prop(masterbone, ik_prop, slider=True)

        # Show the appropriate snap button depending on current IK/FK state
        # Bug fix: original used == instead of = for sub.enabled in the else branch
        if masterbone[ik_prop[2:-2]] == 0:
            # Currently FK — offer to snap to IK
            layout.operator(snap_to_ik)
        else:
            # Currently IK — offer to snap to FK
            layout.operator(snap_to_fk)
            layout.prop(masterbone, '["IK Arm Socket Lock"]', slider=True)

        layout.prop(masterbone, invert_prop, slider=True)
        layout.prop(masterbone, mirror_prop, slider=True)
        layout.prop(masterbone, smear_prop,  slider=True)
        layout.prop(masterbone, clay_prop,   slider=True)


class LegMenu(bpy.types.Panel):
    """Per-leg IK/FK controls. Toggle between Left and Right leg with the
    buttons at the top of the panel."""
    bl_label       = "Leg Menu"
    bl_idname      = "LEG_MENU"
    bl_parent_id   = "EPIC_FIGRIG_PT_PANEL"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'EpicFigRig 2.0'
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.EpicRigTabs == 0 and is_epic_rig_active(context)

    def draw(self, context):
        layout     = self.layout
        masterbone = context.active_object.pose.bones[MASTER_BONE]

        # 0 = Left leg, 1 = Right leg
        showing_left = masterbone["Leg Menu"] == 0

        row = layout.row(align=True)
        row.operator('left_leg.menu',  icon='EVENT_L' if showing_left  else 'NONE')
        row.operator('right_leg.menu', icon='EVENT_R' if not showing_left else 'NONE')

        layout.separator()

        if showing_left:
            self._draw_leg(layout, masterbone,
                           ik_prop     = '["LeftLegIK"]',
                           snap_to_ik  = 'fk_to.ik_lleg',
                           snap_to_fk  = 'ik_to.fk_lleg',
                           invert_prop = '["Invert Left Leg"]',
                           smear_prop  = '["LLegSmear"]')
        else:
            self._draw_leg(layout, masterbone,
                           ik_prop     = '["RightLegIK"]',
                           snap_to_ik  = 'fk_to.ik_rleg',
                           snap_to_fk  = 'ik_to.fk_rleg',
                           invert_prop = '["Invert Right Leg"]',
                           smear_prop  = '["RLegSmear"]')

    def _draw_leg(self, layout, masterbone, ik_prop, snap_to_ik, snap_to_fk,
                  invert_prop, smear_prop):
        """Draw the controls for one leg."""
        layout.prop(masterbone, ik_prop, slider=True)

        if masterbone[ik_prop[2:-2]] == 0:
            layout.operator(snap_to_ik)
        else:
            layout.operator(snap_to_fk)

        layout.prop(masterbone, invert_prop, slider=True)
        layout.prop(masterbone, smear_prop,  slider=True)


# ---------------------------------------------------------------------------
# ADVANCED TAB PANELS  (visible when EpicRigTabs == 1)
# ---------------------------------------------------------------------------

class SmearSlider(bpy.types.Panel):
    """Quick access to all four smear sliders together."""
    bl_label       = "Smears"
    bl_idname      = "SMEAR_SLIDER"
    bl_parent_id   = "EPIC_FIGRIG_PT_PANEL"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'EpicFigRig 2.0'
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.EpicRigTabs == 1 and is_epic_rig_active(context)

    def draw(self, context):
        layout     = self.layout
        masterbone = context.active_object.pose.bones[MASTER_BONE]
        layout.prop(masterbone, '["LLegSmear"]', slider=True)
        layout.prop(masterbone, '["RLegSmear"]', slider=True)
        layout.prop(masterbone, '["LArmSmear"]', slider=True)
        layout.prop(masterbone, '["RArmSmear"]', slider=True)


class BoneAdjust(bpy.types.Panel):
    """Scale and transform adjustments for major rig bones."""
    bl_label       = "Bone Adjustments"
    bl_idname      = "BONE_ADJUST"
    bl_parent_id   = "EPIC_FIGRIG_PT_PANEL"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'EpicFigRig 2.0'
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.EpicRigTabs == 1 and is_epic_rig_active(context)

    def draw(self, context):
        layout     = self.layout
        masterbone = context.active_object.pose.bones[MASTER_BONE]
        layout.prop(masterbone, '["Head Accessory Bone Scale"]', slider=True)
        layout.prop(masterbone, '["Head Bone Scale"]',           slider=True)
        layout.prop(masterbone, '["Head Bone Transform"]',       slider=True)
        layout.prop(masterbone, '["Torso Bone Scale"]',          slider=True)
        layout.prop(masterbone, '["Leg Height"]',                slider=True)


class BoneVis(bpy.types.Panel):
    """Toggle visibility of various rig bones and helpers."""
    bl_label       = "Bone Visibility"
    bl_idname      = "BONE_VISIBILITY"
    bl_parent_id   = "EPIC_FIGRIG_PT_PANEL"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'EpicFigRig 2.0'
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.EpicRigTabs == 1 and is_epic_rig_active(context)

    def draw(self, context):
        layout     = self.layout
        masterbone = context.active_object.pose.bones[MASTER_BONE]
        layout.prop(masterbone, '["Second Master Bone"]',       slider=True)
        layout.prop(masterbone, '["Locators"]',                 slider=True)
        layout.prop(masterbone, '["Clay Right Arm Visibility"]', slider=True)
        layout.prop(masterbone, '["Clay Left Arm Visibility"]',  slider=True)
        layout.prop(masterbone, '["Prop Bone A Visibility"]',    slider=True)
        layout.prop(masterbone, '["Prop Bone B Visibility"]',    slider=True)


class BoneShapes(bpy.types.Panel):
    """Control which hand shape is shown on each arm."""
    bl_label       = "Bone Shapes"
    bl_idname      = "BONE_SHAPES"
    bl_parent_id   = "EPIC_FIGRIG_PT_PANEL"
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'EpicFigRig 2.0'
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.EpicRigTabs == 1 and is_epic_rig_active(context)

    def draw(self, context):
        layout     = self.layout
        masterbone = context.active_object.pose.bones[MASTER_BONE]
        layout.prop(masterbone, '["Left Hand Shape"]',  slider=True)
        layout.prop(masterbone, '["Right Hand Shape"]', slider=True)


class Props(bpy.types.Panel):
    """Controls for Prop Bone A and B (objects held in hands)."""
    bl_label       = "Props"
    bl_idname      = "PROPS_PANEL"   # bug fix: original used "Props" which is
    bl_parent_id   = "EPIC_FIGRIG_PT_PANEL"  # too generic and can conflict
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'EpicFigRig 2.0'
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.EpicRigTabs == 1 and is_epic_rig_active(context)

    def draw(self, context):
        layout     = self.layout
        masterbone = context.active_object.pose.bones[MASTER_BONE]
        layout.prop(masterbone, '["Prop A"]',             slider=True)
        layout.prop(masterbone, '["Prop A Transform"]',   slider=True)
        layout.prop(masterbone, '["Prop A Rotation"]',    slider=True)
        layout.separator()
        layout.prop(masterbone, '["Prop B"]',             slider=True)
        layout.prop(masterbone, '["Prop B Transform"]',   slider=True)
        layout.prop(masterbone, '["Prop B Rotation"]',    slider=True)
        layout.separator()
        layout.prop(masterbone, '["Back Hip Parent"]',    slider=True)


# ---------------------------------------------------------------------------
# UI TOGGLE OPERATORS
# These live here rather than in the operators folder because they do nothing
# except switch the scene property that controls which tab is visible.
# ---------------------------------------------------------------------------

class MainTab(bpy.types.Operator):
    """Switch to the Main tab"""
    bl_label  = "Main"
    bl_idname = 'main.tab'

    def execute(self, context):
        # Bug fix: original did bpy.types.Scene.EpicRigTabs = IntProperty(...)
        # which re-registers the type at runtime. The correct way is to just
        # set the value on the scene instance directly.
        context.scene.EpicRigTabs = 0
        return {'FINISHED'}


class AdvancedTab(bpy.types.Operator):
    """Switch to the Advanced tab"""
    bl_label  = "Advanced"
    bl_idname = 'advanced.tab'

    def execute(self, context):
        context.scene.EpicRigTabs = 1
        return {'FINISHED'}


class LeftHandMenu(bpy.types.Operator):
    """Show the Left Hand controls in the Arm Menu"""
    bl_label  = "Left Hand"
    bl_idname = 'left_hand.menu'

    def execute(self, context):
        context.active_object.pose.bones[MASTER_BONE]["Hand Menu"] = 0
        return {'FINISHED'}


class RightHandMenu(bpy.types.Operator):
    """Show the Right Hand controls in the Arm Menu"""
    bl_label  = "Right Hand"
    bl_idname = 'right_hand.menu'

    def execute(self, context):
        context.active_object.pose.bones[MASTER_BONE]["Hand Menu"] = 1
        return {'FINISHED'}


class LeftLegMenu(bpy.types.Operator):
    """Show the Left Leg controls in the Leg Menu"""
    bl_label  = "Left Leg"
    bl_idname = 'left_leg.menu'

    def execute(self, context):
        context.active_object.pose.bones[MASTER_BONE]["Leg Menu"] = 0
        return {'FINISHED'}


class RightLegMenu(bpy.types.Operator):
    """Show the Right Leg controls in the Leg Menu"""
    bl_label  = "Right Leg"
    bl_idname = 'right_leg.menu'

    def execute(self, context):
        context.active_object.pose.bones[MASTER_BONE]["Leg Menu"] = 1
        return {'FINISHED'}


# ---------------------------------------------------------------------------
# REGISTRATION
# All classes in this file that need to be registered with Blender.
# __init__.py will call register/unregister on these.
# ---------------------------------------------------------------------------

classes = [
    EpicFigRigPanel,
    EpicButtons,
    ArmMenu,
    LegMenu,
    SmearSlider,
    BoneAdjust,
    BoneVis,
    BoneShapes,
    Props,
    MainTab,
    AdvancedTab,
    LeftHandMenu,
    RightHandMenu,
    LeftLegMenu,
    RightLegMenu,
]
