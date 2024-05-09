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
else:
    from . import mocap_gui, mocap_operators

import bpy

from . import mocap_gui
import addon_utils
addon_utils.enable("viewport_vr_preview")


def register():
    bpy.types.Scene.vr_target_left = bpy.props.PointerProperty(type=bpy.types.Object)
    bpy.types.Scene.vr_target_right = bpy.props.PointerProperty(type=bpy.types.Object)
    bpy.types.Scene.vr_motion_capture = bpy.props.BoolProperty(
        name="VR Motion Capture Enabled", default=False
    )
    bpy.types.Scene.vr_mocap_controllers = bpy.props.BoolProperty(
        name="VR Controller Ready for Mocap", default=False
    )
    bpy.types.Scene.fly_forward = bpy.props.FloatProperty(
        name="Thumb Up", options={"ANIMATABLE"}
    )
    bpy.types.Scene.fly_backward = bpy.props.FloatProperty(name="Thumb Down")
    bpy.types.Scene.fly_left = bpy.props.FloatProperty(name="Thumb Left")
    bpy.types.Scene.fly_right = bpy.props.FloatProperty(name="Thumb Right")
    bpy.types.Scene.nav_reset = bpy.props.FloatProperty(name="x_button")
    bpy.types.Scene.nav_grab = bpy.props.FloatProperty(name="Inner Trigger")
    bpy.types.Scene.teleport = bpy.props.FloatProperty(name="Outer Trigger")

    mocap_gui.register()
    mocap_operators.register()


def unregister():
    del bpy.types.Scene.vr_target_left
    del bpy.types.Scene.vr_target_right
    if not bpy.app.build_options.xr_openxr:
        bpy.utils.unregister_class(mocap_gui.VRMOCAP_PT_vr_info)
        return
    del bpy.types.Scene.vr_mocap_controllers

    mocap_gui.unregister()
    mocap_operators.unregister()
