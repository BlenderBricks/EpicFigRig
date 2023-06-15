# EpicFigRig
Blender Lego Minifigure Rig Addon

This is the official github for BlenderBricks's EpicFigRig. Shown in the video below. https://www.youtube.com/watch?v=mZM0jk-jfP0

# JabLab Changelog - Blender 3.3 and above

![Demo](https://github.com/BlenderBricks/EpicFigRig/assets/53737901/7e6743ba-b5d3-4e53-889b-6a0084a11645)

Updates on the 15th of every month!

Version 1.0

- Fixed Head Bone Size slider

- Added Arm Invert sliders

- Added Arm Mirror sliders

- Added FK to IK Snapping for Legs

- Changed the way the add-on imports Child Rigs

Version 1.0.5

- Split FK to IK Snapping buttons into 2 buttons, for each side of the rig

- Added FK to IK Snapping for Arms

- Added system to detect most torso/neck pieces

- Added Leg Invert Sliders

- Changed the way the add-on imports Child Rigs... again

- Extra control features

- Added option to scale Torso Control

- Added toggleable second Master Bone

- Added two internal locators for animation

Version 1.1

- Fixed Lepin Booleans for 3.4 users

- Other Bug Fixes

- Increased the Number of Capes the add-on will autorig.

- Modified UI
    - Moved more uncommon features into the "Advanced" tab
	 
- Made roadmap document public, added in add-on underneath user info document. 

- Removed Herobrine

Version 1.1.1

- Fixed issue when rigging mutiple minifigures with capes in one blend file where cape would be parented to the wrong fig

- Updated the naming system for better organization

Version 1.1.2

- Patched LEPIN Hands in later updates (.... again)

- Fixed issue where one of the neck capes would turn into a different rigged cape

Version 1.1.3

- Added various skirt rigs for autorig

- Props!
    - Added the ability to rig props after the rig has been rigged. Selection order will not matter, so no accidentally rigging the rig to itself
    - Props can be attached to any of the following 8 attachment points
    - 0: No parent
    - 1: Master Bone
    - 2: Left Hand
    - 3: Right Hand
    - 4: Upper Back
    - 5: Lower Back/Hip
    - 6: Left Leg
    - 7: Right Leg
    - By default props will be rigged to hands (Right hand for Prop A, Left hand for Prop B)
    - Props can be transformed and rotated in Local Y space to allow for different pivot points
    - As of right now, only one prop object can be rigged at a time. Looking to change that in future updates
    - Props on child rigs work, but look a lttle funky and may be a little buggy. 

- New Custom Bone Shapes
    - Hook for left hand
    - Minimalistic hand for both left and right hands

- Sliders
    - Changed all custom property sliders to be linked to the rig's masterbone instead of the the armature itself. This was done to make these custom properties hidden in the timeline on deselection and avoid accidentally selecting them later when using multiple rigs

- Bug fix for pivot controller
