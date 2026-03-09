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


# constants.py
# EpicFigRig - Constant values used across the addon.
#
# Keeping data here (rather than inside functions) means:
#   - Lists are created once at import time, not on every operator call
#   - Brick IDs and bone names are easy to find and update in one place
#   - Other modules can import what they need without duplication


# ---------------------------------------------------------------------------
# BONE NAMES
# These strings match the actual bone names inside the .blend rig file.
# If a bone is ever renamed in the rig, change it here and it updates
# everywhere automatically.
# ---------------------------------------------------------------------------

MASTER_BONE = "MasterBone"

# IK/FK - Legs
BONE_RIGHT_LEG_FK       = "RightLeg"
BONE_RIGHT_LEG_SNAP     = "RightLegSnap"
BONE_RIGHT_FOOT_IK      = "RightFootIK"
BONE_RIGHT_FOOT_IK_SNAP = "RightFootIKSnap"
BONE_RIGHT_LEG_IK_PROP  = "RightLegIK"

BONE_LEFT_LEG_FK        = "LeftLeg"
BONE_LEFT_LEG_SNAP      = "LeftLegSnap"
BONE_LEFT_FOOT_IK       = "LeftFootIK"
BONE_LEFT_FOOT_IK_SNAP  = "LeftFootIKSnap"
BONE_LEFT_LEG_IK_PROP   = "LeftLegIK"

# IK/FK - Arms
BONE_RIGHT_ARM_FK       = "Right Arm Socket Control"
BONE_RIGHT_ARM_SNAP     = "Right Arm Snap"
BONE_RIGHT_ARM_IK       = "Right Arm IK"
BONE_RIGHT_ARM_IK_SNAP  = "Right Arm IK Snap"
BONE_RIGHT_ARM_IK_PROP  = "RightArmIK"

BONE_LEFT_ARM_FK        = "Left Arm Socket Control"
BONE_LEFT_ARM_SNAP      = "Left Arm Snap"
BONE_LEFT_ARM_IK        = "Left Arm IK"
BONE_LEFT_ARM_IK_SNAP   = "Left Arm IK Snap"
BONE_LEFT_ARM_IK_PROP   = "LeftArmIK"

# Parenting targets (bones used as parents when rigging parts)
BONE_TORSO              = "Torso"
BONE_TORSO_ROCK         = "Torso Rock"
BONE_HEAD               = "Head"
BONE_HEAD_ACCESSORY     = "Head Accessory"
BONE_LEFT_ARM           = "Left Arm"
BONE_RIGHT_ARM          = "Right Arm"
BONE_LEFT_LEG_INVERT    = "LeftLegInvert"
BONE_RIGHT_LEG_INVERT   = "RightLegInvert"
BONE_LEFT_HAND          = "Left Hand"
BONE_RIGHT_HAND         = "Right Hand"

# Pivot & control bones
BONE_PIVOT              = "Pivot"
BONE_PIVOT_LOCK_L       = "Pivot lock L"
BONE_PIVOT_LOCK_R       = "Pivot lock R"
BONE_CENTER_OF_MASS     = "Center of Mass"
BONE_BODY_CONTROL_IK    = "BodyControlBoneIK"
BONE_MASTER_BONE_SNAP   = "Master Bone Snap"

# Snap bones (used by accessory snapping operators)
BONE_RIGHT_HAND_SNAP    = "Right Hand Snap Bone"
BONE_LEFT_HAND_SNAP     = "Left Hand Snap Bone"

# Prop bones
BONE_PROP_A_TRANSFORM   = "AP Bone Transform"
BONE_PROP_B_TRANSFORM   = "AP Bone B Transform"

# Armature bone collections (Blender 4.0+ uses collections instead of layers)
COLLECTION_PIVOT        = "Pivot Contols"   # note: typo is intentional, matches the rig


# ---------------------------------------------------------------------------
# BRICK ID LISTS
# Mecabricks exports objects whose mesh data is named after the LEGO part ID.
# AutoRig uses these lists to figure out which bone each part should attach to.
# ---------------------------------------------------------------------------

# Legs
BRICK_LEG_LEFT = ["77338", "3817", "20926", "24083", "37364p2", "37366", "LEGL"]
BRICK_LEG_RIGHT = ["77337", "3816", "20932", "24082", "37364p1", "2532", "LEGR"]

# Child figure legs (shorter legs, e.g. for children/short figures)
BRICK_CHILD_LEG = ["37365", "37366", "16709", "37679", "41879"]
BRICK_CHILD_LEG_SINGLE = ["16709", "37679", "41879"]

# Torso
BRICK_TORSO = ["3814", "973", "TORSO"]
BRICK_HIP = ["3814", "973"]  # Used separately for hip location detection

# Torso gear / backpack attachments
BRICK_TORSO_GEAR = [
    "95348", "61976", "6132", "93223", "93069", "10052", "10065", "42446",
    "48724", "92590", "4523", "2524", "12397", "4498", "2526", "30133",
    "2610", "97895", "38781", "3838", "3840", "2587", "72326", "11260",
    "15339", "30091", "15490", "15428", "34685", "24135", "18986", "15423",
    "98132", "24097", "22402", "28350", "12618", "19723", "4524", "11097",
    "26966", "93250", "99250", "26073", "4736", "11438", "15406", "18827",
    "27325", "10183", "6158", "27148", "27151", "27147", "98722", "64802",
    "23983", "28716", "25376", "30174", "24588", "15086", "13791", "20566",
    "24217", "88295", "39260", "41637", "34706", "41811", "39796", "41162",
    "41202", "37822", "65183", "79786", "34721p2",
]

# Arms
# NOTE: The original code had a bug on the left arm list:
#   "62691""ARML" -- missing comma, silently created "62691ARML"
# This is fixed below.
BRICK_ARM_RIGHT = ["16000", "3818", "62691", "ARMR"]
BRICK_ARM_LEFT  = ["16001", "3819", "62691", "ARML"]  # <-- comma added (bug fix)

# Hands
BRICK_HAND = ["3820", "2531", "9532"]

# Head
BRICK_HEAD = [
    "24581", "3626", "28621", "94590", "28650", "28649", "26683", "93248",
    "30480", "30378", "98103", "64804", "92743", "1735", "24601", "24629",
    "98365", "98384", "93068", "19729", "20613", "41201", "18828", "65431", "HEADEPIC",
]

# Head accessories (hats, hair, helmets, etc.)
BRICK_HEAD_ACCESSORY = [
    "64798", "64807", "85974", "887990", "87991", "87995", "88283", "88286",
    "92081", "92083", "93217", "93562", "93563", "18228", "99240", "11908",
    "99930", "99248", "98726", "10301", "10166", "10048", "10048", "10055",
    "10066", "11256", "12893", "13768", "13251", "13664", "13785", "13750",
    "13765", "13766", "15443", "15427", "15491", "15500", "15485", "17346",
    "17630", "18858", "21787", "20688", "20877", "20595", "20597", "20596",
    "21777", "21268", "21269", "21778", "23186", "23187", "24072", "25775",
    "28798", "25378", "25379", "26139", "25972", "27186", "27385", "27160",
    "28551", "28144", "28149", "27323", "28664", "28432", "28432", "25411",
    "25412", "25409", "28430", "34316", "25405", "34693", "36060", "36489",
    "37823", "40938", "3901", "62810", "40239", "3625", "96859", "62711",
    "6093", "62696", "59363", "95225", "6025", "99245", "92746", "61183",
    "40240", "98371", "20603", "21788", "21789", "92756", "40233", "24071",
    "28139", "65425", "35182", "35620", "49362", "92259", "18637", "15675",
    "18640", "92255", "19196", "65471", "65463", "66912", "3842", "50665",
    "16599", "30124", "49663", "36293", "93560", "35458", "15851", "3834",
    "90541", "4505", "26079", "4506", "2338", "3844", "3896", "48493",
    "30273", "89520", "4503", "71015", "2544", "2528", "2543", "23973",
    "30048", "93554", "2545", "40235", "18822", "3629", "30167", "61506",
    "15424", "13565", "13788", "13746", "6131", "4485", "86035", "11303",
    "93219", "35660", "11258", "3878", "3624", "41334", "3898", "30287",
    "95678", "36933", "62537", "46303", "3833", "16178", "16175", "98289",
    "99254", "43057", "22380", "85975", "90386", "98381", "30370", "61189",
    "11217", "15308", "30369", "23947", "20904", "20905", "20950", "98119",
    "21829", "30561", "16497", "57900", "52345", "20908", "20954", "21557",
    "19916", "19917", "87610", "87571", "60768", "92761", "6030", "10051",
    "10056d1", "13767", "10173", "30171", "15530", "17351", "99244", "25971",
    "18831", "66972", "18819", "24076", "25977", "29575", "35697", "20695",
    "95674", "95319", "13789", "30381", "10113", "27161", "18987", "98729",
    "27326", "10907", "10908", "28631", "20917", "17016", "11620", "10909",
    "15554", "33862", "18936", "19303", "25264", "19026", "65589", "19730",
    "18962", "98130", "96034", "98133", "19857", "24496", "24504", "40925",
    "65072", "93059", "26007", "98128", "25407", "25742", "25743", "25748",
    "25113", "25114", "28679", "30668", "96204", "18984", "90388", "24073",
    "19861", "90392", "98366", "25978", "15404", "98378", "22425", "13792",
    "13787", "11265", "30172", "27955", "37038", "10164", "34704", "54001",
    "52684", "93557", "65532", "30926", "67145", "66917", "11420", "3320",
]

# Head clothing: soft goods (hoods, cloaks worn on head)
BRICK_HEAD_CLOTHING = [
    "91190", "64647", "30126", "98379", "12886", "33322", "25974", "14045",
    "25634", "13665", "24131", "44553", "41944", "54568", "87696", "87695",
    "11437", "22411", "88964", "39262", "35183",
]

# Head clothing: visors (attached to helmets)
BRICK_HEAD_VISORS = [
    "2447", "41805", "23318", "89159", "30170", "6119", "30090", "15446",
    "2594", "22393", "22395", "22400", "22401", "22394", "23851", "28976",
]

# Dress/skirt bricks that replace legs
BRICK_DRESS = ["3678", "75103", "98376", "19859"]  # original used 3678[:4] — kept as "3678"
BRICK_DRESS_REGULAR = ["36036", "95351"]

# Capes (soft goods, get their own CapeRig)
BRICK_CAPE = [
    "20547", "23901", "29453", "34721p1", "50231", "50525",
    "56630", "65384", "99464",
]

# Skirts (soft goods, get their own SkirtRig)
BRICK_SKIRT = ["txt2", "txt3", "33426", "26697", "68054"]
