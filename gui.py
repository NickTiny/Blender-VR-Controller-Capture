# SPDX-License-Identifier: GPL-2.0-or-later

if "bpy" in locals():
    import importlib

    importlib.reload(properties)
else:
    from . import properties

import bpy
from bpy.app.translations import pgettext_iface as iface_
from bpy.types import (
    Menu,
    Panel,
    UIList,
)

# Add space_view3d.py to module search path for VRMOCAP_PT_object_type_visibility import.
import os.path, sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../../startup/bl_ui'))
)
# from space_view3d import VRMOCAP_PT_object_type_visibility


### Session.
class VRMOCAP_PT_vr_session(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "VR Session"

    def draw(self, context):
        layout = self.layout
        session_settings = context.window_manager.xr_session_settings
        scene = context.scene

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        is_session_running = bpy.types.XrSessionState.is_running(context)

        # Using SNAP_FACE because it looks like a stop icon -- I shouldn't
        # have commit rights...
        toggle_info = (
            (iface_("Start VR Session"), 'PLAY')
            if not is_session_running
            else (iface_("Stop VR Session"), 'SNAP_FACE')
        )
        layout.operator(
            "wm.xr_session_toggle",
            text=toggle_info[0],
            translate=False,
            icon=toggle_info[1],
        )

        layout.separator()

        col = layout.column(align=True, heading="Tracking")
        col.prop(session_settings, "use_positional_tracking", text="Positional")
        col.prop(session_settings, "use_absolute_tracking", text="Absolute")

        col = layout.column(align=True, heading="Actions")
        col.prop(scene, "mocapvr_actions_enable")


### View.
class VRMOCAP_PT_vr_session_view(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "View"

    def draw(self, context):
        layout = self.layout
        session_settings = context.window_manager.xr_session_settings

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        col = layout.column(align=True, heading="Show")
        col.prop(session_settings, "show_floor", text="Floor")
        col.prop(session_settings, "show_annotation", text="Annotations")

        col.prop(session_settings, "show_selection", text="Selection")
        col.prop(session_settings, "show_controllers", text="Controllers")
        col.prop(session_settings, "show_custom_overlays", text="Custom Overlays")
        col.prop(session_settings, "show_object_extras", text="Object Extras")

        col = col.row(align=True, heading=" ")
        col.scale_x = 2.0
        # col.popover(
        #     panel="VRMOCAP_PT_vr_session_view_object_type_visibility",
        #     icon_value=session_settings.icon_from_show_object_viewport,
        #     text="",
        # )

        col = layout.column(align=True)
        col.prop(session_settings, "controller_draw_style", text="Controller Style")

        col = layout.column(align=True)
        col.prop(session_settings, "clip_start", text="Clip Start")
        col.prop(session_settings, "clip_end", text="End")


# class VRMOCAP_PT_vr_session_view_object_type_visibility(
#     VRMOCAP_PT_object_type_visibility
# ):
#     def draw(self, context):
#         session_settings = context.window_manager.xr_session_settings
#         self.draw_ex(
#             context, session_settings, False
#         )  # Pass session settings instead of 3D view.


### Actions.
class VRMOCAP_PT_vr_actionmaps(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "Action Maps"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        col = layout.column(align=True)
        col.prop(scene, "mocapvr_actions_use_gamepad", text="Gamepad")

        col = layout.column(align=True, heading="Extensions")
        col.prop(scene, "mocapvr_actions_enable_reverb_g2", text="HP Reverb G2")
        col.prop(scene, "mocapvr_actions_enable_vive_cosmos", text="HTC Vive Cosmos")
        col.prop(scene, "mocapvr_actions_enable_vive_focus", text="HTC Vive Focus")
        col.prop(scene, "mocapvr_actions_enable_huawei", text="Huawei")


### Viewport feedback.
class VRMOCAP_PT_vr_viewport_feedback(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "Viewport Feedback"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        view3d = context.space_data
        session_settings = context.window_manager.xr_session_settings

        col = layout.column(align=True)
        col.label(icon='ERROR', text="Note:")
        col.label(text="Settings here may have a significant")
        col.label(text="performance impact!")

        layout.separator()

        layout.prop(view3d.shading, "mocapvr_show_virtual_camera")
        layout.prop(view3d.shading, "mocapvr_show_controllers")
        layout.prop(view3d, "mirror_xr_session")


class VRMOCAP_PT_vr_save_position(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "VR Capture"

    def draw(self, context):
        row = self.layout.row()
        scene = context.scene
        row.prop(scene, "vr_target_left", text="Left")
        row.prop(scene, "vr_target_right", text="Right")
        enabled = context.scene.vr_motion_capture
        self.layout.operator("view3d.vr_save_pose", depress=enabled)
        col = self.layout.column()
        col.prop(scene, "fly_forward")
        col.prop(scene, "fly_backward")
        col.prop(scene, "fly_left")
        col.prop(scene, "fly_right")
        col.prop(scene, "nav_reset")
        col.prop(scene, "nav_grab")
        col.prop(scene, "teleport")


### Info.
class VRMOCAP_PT_vr_info(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "VR Info"

    @classmethod
    def poll(cls, context):
        return not bpy.app.build_options.xr_openxr

    def draw(self, context):
        layout = self.layout
        layout.label(icon='ERROR', text="Built without VR/OpenXR features")


classes = (
    VRMOCAP_PT_vr_session,
    VRMOCAP_PT_vr_session_view,
    # VRMOCAP_PT_vr_session_view_object_type_visibility,
    VRMOCAP_PT_vr_actionmaps,
    VRMOCAP_PT_vr_viewport_feedback,
    VRMOCAP_PT_vr_save_position,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # View3DShading is the only per 3D-View struct with custom property
    # support, so "abusing" that to get a per 3D-View option.
    bpy.types.View3DShading.mocapvr_show_virtual_camera = bpy.props.BoolProperty(
        name="Show VR Camera"
    )
    bpy.types.View3DShading.mocapvr_show_controllers = bpy.props.BoolProperty(
        name="Show VR Controllers"
    )


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.View3DShading.mocapvr_show_virtual_camera
    del bpy.types.View3DShading.mocapvr_show_controllers
