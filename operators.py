# SPDX-License-Identifier: GPL-2.0-or-later
import bpy
import gpu
from bpy.app.translations import pgettext_data as data_
from bpy.types import (
    Gizmo,
    GizmoGroup,
    Operator,
)
import math
from math import radians
from mathutils import Euler, Matrix, Quaternion, Vector


class VRMOCAP_OT_vr_save_position(bpy.types.Operator):
    bl_idname = "view3d.vr_save_pose"
    bl_label = "Save VR Poses"

    ## TODO WARN USER IF VR ADDON IS NOT ENABLED OR SESSIONS IS NOT STARTED
    _left_target = None
    _right_target = None
    _wm = None

    @staticmethod
    def _get_controller_pose_matrix(context, idx, wm):
        scale = 1.0
        session_state = wm.xr_session_state
        loc = session_state.controller_grip_location_get(context, idx)
        rot = session_state.controller_grip_rotation_get(context, idx)
        rotmat = Matrix.Identity(3)
        rotmat.rotate(Quaternion(Vector(rot)))
        rotmat.resize_4x4()
        transmat = Matrix.Translation(loc)
        scalemat = Matrix.Scale(scale, 4)
        return transmat @ rotmat @ scalemat

    def keyframe_grip(self, context, idx: int, wm):
        target_object = self._left_target if idx == 0 else self._right_target
        target_object.matrix_basis = self._get_controller_pose_matrix(context, idx, wm)
        target_object.keyframe_insert('location')
        target_object.keyframe_insert('rotation_euler')

    def create_new_action(self, obj: bpy.types.Object):
        obj.animation_data_create()
        action = bpy.data.actions.new(obj.name)
        obj.animation_data.action = action
        return obj.animation_data.action

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            context.scene.vr_motion_capture = False
            return {'CANCELLED'}

        if context.scene.frame_current == context.scene.frame_end:
            context.scene.vr_motion_capture = False
            return {'FINISHED'}
        self.keyframe_grip(context, 0, self._wm)
        scene = context.scene
        session_state = context.window_manager.xr_session_state

        scene.fly_forward = session_state.action_state_get(
            context=context,
            action_set_name=session_state.actionmaps[0].name,
            action_name="fly_forward",
            user_path='/user/hand/left',
        )[0]
        scene.keyframe_insert(data_path='["fly_forward"]')
        scene.fly_backward = session_state.action_state_get(
            context=context,
            action_set_name=session_state.actionmaps[0].name,
            action_name="fly_backward",
            user_path='/user/hand/left',
        )[0]
        scene.keyframe_insert(data_path='["fly_backward"]')
        scene.fly_left = session_state.action_state_get(
            context=context,
            action_set_name=session_state.actionmaps[0].name,
            action_name="fly_left",
            user_path='/user/hand/left',
        )[0]
        scene.keyframe_insert(data_path='["fly_left"]')
        scene.fly_right = session_state.action_state_get(
            context=context,
            action_set_name=session_state.actionmaps[0].name,
            action_name="fly_right",
            user_path='/user/hand/left',
        )[0]
        scene.keyframe_insert(data_path='["fly_right"]')
        scene.nav_reset = session_state.action_state_get(
            context=context,
            action_set_name=session_state.actionmaps[0].name,
            action_name="nav_reset",
            user_path='/user/hand/left',
        )[0]
        scene.nav_grab = session_state.action_state_get(
            context=context,
            action_set_name=session_state.actionmaps[0].name,
            action_name="nav_grab",
            user_path='/user/hand/left',
        )[0]
        scene.keyframe_insert(data_path='["nav_grab"]')

        scene.teleport = session_state.action_state_get(
            context=context,
            action_set_name=session_state.actionmaps[0].name,
            action_name="teleport",
            user_path='/user/hand/left',
        )[0]
        scene.keyframe_insert(data_path='["teleport"]')
        scene.nav_reset = session_state.action_state_get(
            context=context,
            action_set_name=session_state.actionmaps[0].name,
            action_name="nav_reset",
            user_path='/user/hand/left',
        )[0]
        scene.keyframe_insert(data_path='["nav_reset"]')
        return {'PASS_THROUGH'}

    def execute(self, context):
        if (
            context.scene.vr_target_left is None
            or context.scene.vr_target_right is None
        ):
            self.report({'ERROR'}, "No object is set")
            return {'CANCELLED'}
        context.scene.vr_motion_capture = True
        self._left_target = context.scene.vr_target_left
        self._right_target = context.scene.vr_target_right
        self.create_new_action(self._left_target)
        self.create_new_action(self._right_target)
        self._left_target
        self._wm = context.window_manager
        self._wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}


### Gizmos.
class VRMOCAP_GT_vr_camera_cone(Gizmo):
    bl_idname = "VIEW_3D_GT_vr_camera_cone"

    aspect = 1.0, 1.0

    def draw(self, context):
        if not hasattr(self, "frame_shape"):
            aspect = self.aspect

            frame_shape_verts = (
                (-aspect[0], -aspect[1], -1.0),
                (aspect[0], -aspect[1], -1.0),
                (aspect[0], aspect[1], -1.0),
                (-aspect[0], aspect[1], -1.0),
            )
            lines_shape_verts = (
                (0.0, 0.0, 0.0),
                frame_shape_verts[0],
                (0.0, 0.0, 0.0),
                frame_shape_verts[1],
                (0.0, 0.0, 0.0),
                frame_shape_verts[2],
                (0.0, 0.0, 0.0),
                frame_shape_verts[3],
            )

            self.frame_shape = self.new_custom_shape('LINE_LOOP', frame_shape_verts)
            self.lines_shape = self.new_custom_shape('LINES', lines_shape_verts)

        # Ensure correct GL state (otherwise other gizmos might mess that up)
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set('ALPHA')

        self.draw_custom_shape(self.frame_shape)
        self.draw_custom_shape(self.lines_shape)


class VRMOCAP_GT_vr_controller_grip(Gizmo):
    bl_idname = "VIEW_3D_GT_vr_controller_grip"

    def draw(self, context):
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set('ALPHA')

        self.color = 0.422, 0.438, 0.446
        self.draw_preset_circle(self.matrix_basis, axis='POS_X')
        self.draw_preset_circle(self.matrix_basis, axis='POS_Y')
        self.draw_preset_circle(self.matrix_basis, axis='POS_Z')


class VRMOCAP_GT_vr_controller_aim(Gizmo):
    bl_idname = "VIEW_3D_GT_vr_controller_aim"

    def draw(self, context):
        gpu.state.line_width_set(1.0)
        gpu.state.blend_set('ALPHA')

        self.color = 1.0, 0.2, 0.322
        self.draw_preset_arrow(self.matrix_basis, axis='POS_X')
        self.color = 0.545, 0.863, 0.0
        self.draw_preset_arrow(self.matrix_basis, axis='POS_Y')
        self.color = 0.157, 0.565, 1.0
        self.draw_preset_arrow(self.matrix_basis, axis='POS_Z')


class VRMOCAP_GGT_vr_viewer_pose(GizmoGroup):
    bl_idname = "VRMOCAP_GGT_vr_viewer_pose"
    bl_label = "VR Viewer Pose Indicator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SCALE', 'VR_REDRAWS'}

    @classmethod
    def poll(cls, context):
        view3d = context.space_data
        return (
            view3d.shading.mocapvr_show_virtual_camera
            and bpy.types.XrSessionState.is_running(context)
            and not view3d.mirror_xr_session
        )

    @staticmethod
    def _get_viewer_pose_matrix(context):
        wm = context.window_manager

        loc = wm.xr_session_state.viewer_pose_location
        rot = wm.xr_session_state.viewer_pose_rotation

        rotmat = Matrix.Identity(3)
        rotmat.rotate(rot)
        rotmat.resize_4x4()
        transmat = Matrix.Translation(loc)

        return transmat @ rotmat

    def setup(self, context):
        gizmo = self.gizmos.new(VRMOCAP_GT_vr_camera_cone.bl_idname)
        gizmo.aspect = 1 / 3, 1 / 4

        gizmo.color = gizmo.color_highlight = 0.2, 0.6, 1.0
        gizmo.alpha = 1.0

        self.gizmo = gizmo

    def draw_prepare(self, context):
        self.gizmo.matrix_basis = self._get_viewer_pose_matrix(context)


class VRMOCAP_GGT_vr_controller_poses(GizmoGroup):
    bl_idname = "VRMOCAP_GGT_vr_controller_poses"
    bl_label = "VR Controller Poses Indicator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT', 'SCALE', 'VR_REDRAWS'}

    @classmethod
    def poll(cls, context):
        view3d = context.space_data
        return (
            view3d.shading.mocapvr_show_controllers
            and bpy.types.XrSessionState.is_running(context)
            and not view3d.mirror_xr_session
        )

    @staticmethod
    def _get_controller_pose_matrix(context, idx, is_grip, scale):
        wm = context.window_manager

        loc = None
        rot = None
        if is_grip:
            loc = wm.xr_session_state.controller_grip_location_get(context, idx)
            rot = wm.xr_session_state.controller_grip_rotation_get(context, idx)
        else:
            loc = wm.xr_session_state.controller_aim_location_get(context, idx)
            rot = wm.xr_session_state.controller_aim_rotation_get(context, idx)

        rotmat = Matrix.Identity(3)
        rotmat.rotate(Quaternion(Vector(rot)))
        rotmat.resize_4x4()
        transmat = Matrix.Translation(loc)
        scalemat = Matrix.Scale(scale, 4)

        return transmat @ rotmat @ scalemat

    def setup(self, context):
        for idx in range(2):
            self.gizmos.new(VRMOCAP_GT_vr_controller_grip.bl_idname)
            self.gizmos.new(VRMOCAP_GT_vr_controller_aim.bl_idname)

        for gizmo in self.gizmos:
            gizmo.aspect = 1 / 3, 1 / 4
            gizmo.color_highlight = 1.0, 1.0, 1.0
            gizmo.alpha = 1.0

    def draw_prepare(self, context):
        grip_idx = 0
        aim_idx = 0
        idx = 0
        scale = 1.0
        for gizmo in self.gizmos:
            is_grip = gizmo.bl_idname == VRMOCAP_GT_vr_controller_grip.bl_idname
            if is_grip:
                idx = grip_idx
                grip_idx += 1
                scale = 0.1
            else:
                idx = aim_idx
                aim_idx += 1
                scale = 0.5
            gizmo.matrix_basis = self._get_controller_pose_matrix(
                context, idx, is_grip, scale
            )


classes = (
    VRMOCAP_GT_vr_camera_cone,
    VRMOCAP_GT_vr_controller_grip,
    VRMOCAP_GT_vr_controller_aim,
    VRMOCAP_GGT_vr_viewer_pose,
    VRMOCAP_GGT_vr_controller_poses,
    VRMOCAP_OT_vr_save_position,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
