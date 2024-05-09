# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "VR Capture",
    "author": "Nick Alberelli",
    "version": (0, 11, 2),
    "blender": (3, 6, 0),
    "location": "3D View > Sidebar > VR",
    "description": """TODO""",
    "support": "OFFICIAL",
    "warning": "This is an early, limited preview of in development "
    "VR support for Blender.",
    "category": "3D View",
}


if "bpy" in locals():
    import importlib

    importlib.reload(mocap_gui)
    importlib.reload(mocap_operators)
    importlib.reload(props)
else:
    from . import mocap_gui, mocap_operators, props

import bpy

from . import mocap_gui
import addon_utils
addon_utils.enable("viewport_vr_preview")


def register():
    props.register()
    mocap_gui.register()
    mocap_operators.register()


def unregister():
    if not bpy.app.build_options.xr_openxr:
        bpy.utils.unregister_class(mocap_gui.VRMOCAP_PT_vr_info)
        return

    props.unregister()
    mocap_gui.unregister()
    mocap_operators.unregister()