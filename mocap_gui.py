import bpy
import addon_utils

from . import constants
from bpy.app.translations import pgettext_iface as iface_


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
        try:
            target["fly_forward"]
        except KeyError:
            col.operator("view3d.add_custom_properties")
        # if not target.fly_forward:
        col.prop(target, '["fly_forward"]')
        col.prop(target, '["fly_left"]')
        col.prop(target, '["nav_reset"]')
        col.prop(target, '["nav_grab"]')
        col.prop(target, '["teleport"]')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        enabled = scene.vr_motion_capture

        if addon_utils.check("viewport_vr_preview") == (False, False):
            layout.operator("view3d.enabled_vr_preview_addon")
            layout.alert = True
            layout.label(text="Enable 'VR Scene Inspection' addon", icon="ERROR")
            return

        box = layout.box()
        box.label(text="VR Controller Motion Capture")
        is_session_running = bpy.types.XrSessionState.is_running(context)
        toggle_session_info = (
            (iface_("Start VR MoCap Session"), 'PLAY')
            if not is_session_running
            else (iface_("Stop VR MoCap Session"), 'SNAP_FACE')
        )

        layout.operator(
            "view3d.start_mocap_session",
            text=toggle_session_info[0],
            translate=False,
            icon=toggle_session_info[1],
        )

        toggle_rec_info = (
            "Start Recording" if not context.scene.vr_motion_capture else "Recording..."
        )
        layout.operator(
            "view3d.vr_save_pose",
            text=toggle_rec_info,
            translate=False,
            icon="RADIOBUT_ON",
            depress=enabled,
        )
        cont_sets = layout.column()
        cont_sets.enabled = context.scene.vr_mocap_controllers
        row = cont_sets.row()
        row.prop_search(
            scene,
            "obj_selection",
            context.scene,
            "objects",
            text="Armature",
        )
        if context.scene.obj_selection is None:
            return
        row = cont_sets.row()
        row.prop_search(
            scene,
            "left_bone_selection",
            scene.obj_selection.pose,
            "bones",
            text="Bone",
        )
        row.prop_search(
            scene,
            "right_bone_selection",
            context.scene.obj_selection.pose,
            "bones",
            text="Bone",
        )
        row = cont_sets.row()
        split = row.split(factor=0.5)
        if scene.left_bone_selection:
            col = split.column()
            target = context.scene.obj_selection.pose.bones[
                context.scene.left_bone_selection
            ]
            self.draw_controller_properties(context, col, target)
            col.prop(context.scene, "vr_offset_left")

            if target.rotation_mode != constants.BONE_ROTATION_MODE:
                alert_col = col.column()
                alert_col.alert = True
                alert_col.operator("view3d.set_rotation_mode").bone_name = (
                    context.scene.left_bone_selection
                )

        if scene.right_bone_selection:
            col = split.column()
            target = context.scene.obj_selection.pose.bones[
                context.scene.right_bone_selection
            ]
            self.draw_controller_properties(context, col, target)
            col.prop(context.scene, "vr_offset_right")
            if target.rotation_mode != constants.BONE_ROTATION_MODE:
                alert_col = col.column()
                alert_col.alert = True
                alert_col.operator("view3d.set_rotation_mode").bone_name = (
                    context.scene.right_bone_selection
                )


classes = (VRMOCAP_PT_vr_save_position,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.vr_offset_right = bpy.props.FloatVectorProperty(
        name="Rotation Offset", subtype="EULER", size=3, default=(-1.5708, 0, -1.5708)
    )
    bpy.types.Scene.vr_offset_left = bpy.props.FloatVectorProperty(
        name="Rotation Offset", subtype="EULER", size=3, default=(-1.5708, 0, -1.5708)
    )


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.vr_offset_right
    del bpy.types.Scene.vr_offset_left
