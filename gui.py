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


def armature_filter(self, object):
    return object.type == 'ARMATURE'


class VRMOCAP_PT_vr_save_position(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "VR Capture"

    # Pointer definitions
    bpy.types.Scene.obj_selection = bpy.props.PointerProperty(
        type=bpy.types.Object,
        poll=armature_filter,
    )
    bpy.types.Scene.right_bone_selection = bpy.props.StringProperty()
    bpy.types.Scene.left_bone_selection = bpy.props.StringProperty()

    def draw_controller_properties(self, context, col, target):
        col.prop(target, "fly_forward")
        col.prop(target, "fly_left")
        col.prop(target, "nav_reset")
        col.prop(target, "nav_grab")
        col.prop(target, "teleport")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        scene = context.scene
        enabled = scene.vr_motion_capture
        layout.operator("view3d.vr_save_pose", depress=enabled)
        scene = context.scene
        row = layout.row()
        row.prop_search(
            scene,
            "obj_selection",
            context.scene,
            "objects",
            text="Object",
        )
        if context.scene.obj_selection is None:
            return
        row = layout.row()
        row.prop_search(
            scene,
            "right_bone_selection",
            context.scene.obj_selection.pose,
            "bones",
            text="Bone",
        )
        row.prop_search(
            scene,
            "left_bone_selection",
            scene.obj_selection.pose,
            "bones",
            text="Bone",
        )
        row = self.layout.row()
        split = row.split(factor=0.5)
        if scene.vr_target_left:
            col = split.column()
            target = context.scene.obj_selection.pose.bones[
                context.scene.left_bone_selection
            ].vr_mocap
            self.draw_controller_properties(context, col, target)

        if scene.vr_target_left:
            col = split.column()
            target = context.scene.obj_selection.pose.bones[
                context.scene.right_bone_selection
            ].vr_mocap
            self.draw_controller_properties(context, col, target)


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


### Landmarks.
class VRMOCAP_MT_vr_landmark_menu(Menu):
    bl_label = "Landmark Controls"

    def draw(self, _context):
        layout = self.layout

        layout.operator("vrmocap.vr_camera_landmark_from_session")
        layout.operator("vrmocap.vr_landmark_from_camera")
        layout.operator("vrmocap.update_vr_landmark")
        layout.separator()
        layout.operator("vrmocap.cursor_to_vr_landmark")
        layout.operator("vrmocap.camera_to_vr_landmark")
        layout.operator("vrmocap.add_camera_from_vr_landmark")


class VRMOCAP_UL_vr_landmarks(UIList):
    def draw_item(
        self, context, layout, _data, item, icon, _active_data, _active_propname, index
    ):
        landmark = item
        landmark_active_idx = context.scene.vr_landmarks_active

        layout.emboss = 'NONE'

        layout.prop(landmark, "name", text="")

        icon = 'RADIOBUT_ON' if (index == landmark_active_idx) else 'RADIOBUT_OFF'
        props = layout.operator("view3d.vr_landmark_activate", text="", icon=icon)
        props.index = index


class VRMOCAP_PT_vr_landmarks(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "Landmarks"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        landmark_selected = properties.VRLandmark.get_selected_landmark(context)

        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        row = layout.row()

        row.template_list(
            "VRMOCAP_UL_vr_landmarks",
            "",
            scene,
            "vr_landmarks",
            scene,
            "vr_landmarks_selected",
            rows=3,
        )

        col = row.column(align=True)
        col.operator("view3d.vr_landmark_add", icon='ADD', text="")
        col.operator("view3d.vr_landmark_remove", icon='REMOVE', text="")
        col.operator("view3d.vr_landmark_from_session", icon='PLUS', text="")

        col.menu("VRMOCAP_MT_vr_landmark_menu", icon='DOWNARROW_HLT', text="")

        if landmark_selected:
            layout.prop(landmark_selected, "type")

            if landmark_selected.type == 'OBJECT':
                layout.prop(landmark_selected, "base_pose_object")
                layout.prop(landmark_selected, "base_scale", text="Scale")
            elif landmark_selected.type == 'CUSTOM':
                layout.prop(landmark_selected, "base_pose_location", text="Location")
                layout.prop(landmark_selected, "base_pose_angle", text="Angle")
                layout.prop(landmark_selected, "base_scale", text="Scale")


classes = (
    VRMOCAP_PT_vr_session,
    VRMOCAP_PT_vr_session_view,
    # VRMOCAP_PT_vr_session_view_object_type_visibility,
    VRMOCAP_PT_vr_actionmaps,
    VRMOCAP_PT_vr_viewport_feedback,
    VRMOCAP_PT_vr_save_position,
    VRMOCAP_MT_vr_landmark_menu,
    VRMOCAP_UL_vr_landmarks,
    VRMOCAP_PT_vr_landmarks,
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