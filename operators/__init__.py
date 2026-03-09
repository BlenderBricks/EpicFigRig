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

# operators/__init__.py
# Collects all operator classes from the sub-modules into one flat list.
#
# The top-level __init__.py imports this 'classes' list and loops over it
# to register everything with Blender. Adding a new operator file just means
# importing its classes list here and adding it to the chain below —
# no changes needed anywhere else.

from .rigging  import classes as rigging_classes
from .snapping import classes as snapping_classes
from .misc     import classes as misc_classes
from .ik_fk    import classes as ik_fk_classes

# Single flat list of every operator class in the addon
classes = (
    rigging_classes
    + snapping_classes
    + misc_classes
    + ik_fk_classes
)
