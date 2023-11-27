# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import time
import gpu
from bpy.app.translations import pgettext_data as data_
from bpy.types import (
    Gizmo,
    GizmoGroup,
    Operator,
)
import math
import mathutils
from math import radians
from mathutils import Euler, Matrix, Quaternion, Vector
from .custom_properties import custom_float_create
from .mocap_actionmaps import vr_mocap_actionmaps_clear, vr_mocap_actionmaps_restore


class VRMOCAP_OT_vr_save_position_start(bpy.types.Operator):
    bl_idname = "view3d.vr_save_pose"
    bl_label = "Start Saving VR Poses"

    _left_target = None
    _right_target = None
    _wm = None

    @classmethod
    def poll(cls, context):
        view3d = context.space_data
        return context.window_manager.xr_session_state != None

    @staticmethod
    def _get_controller_pose_matrix(context, idx, wm):
        # TODO Fix Matrix Math so bones sync with controllers
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
        bone_name = (
            self.get_bone_via_hand(context, "left")
            if idx == 0
            else self.get_bone_via_hand(context, "right")
        )
        armature = context.scene.obj_selection
        bones = armature.pose.bones
        target_bone = bones[bone_name]
        # TODO Make this better
        offset = (
            context.scene.vr_offset_left if idx == 0 else context.scene.vr_offset_right
        )
        # quat_matrix = mathutils.Quaternion(offset).to_matrix().to_4x4()
        target_bone.matrix = self._get_controller_pose_matrix(
            context, idx, wm
        ) @ target_bone.matrix.Rotation(offset.x, 4, "X")
        target_bone.matrix = self._get_controller_pose_matrix(
            context, idx, wm
        ) @ target_bone.matrix.Rotation(offset.y, 4, "Y")
        target_bone.matrix = self._get_controller_pose_matrix(
            context, idx, wm
        ) @ target_bone.matrix.Rotation(offset.z, 4, "X")
        target_bone.keyframe_insert('location')
        target_bone.keyframe_insert('rotation_euler')

    def create_new_action(self, obj: bpy.types.Object):
        obj.animation_data_create()
        action = bpy.data.actions.new(obj.name)
        obj.animation_data.action = action
        return obj.animation_data.action

    def get_bone_via_hand(self, context, hand):
        scene = context.scene
        if hand == "right":
            return scene.right_bone_selection
        else:
            return scene.left_bone_selection

    def save_controller_data(self, context, session_state, hand, key):
        scene = context.scene
        armature = scene.obj_selection
        bones = armature.pose.bones
        bone_name = self.get_bone_via_hand(context, hand)
        target = bones[bone_name]
        target[f'{key}'] = session_state.action_state_get(
            context=context,
            action_set_name=session_state.actionmaps[0].name,
            action_name=f"{key}",
            user_path=f'/user/hand/{hand}',
        )[0]
        armature.keyframe_insert(data_path=f'pose.bones["{bone_name}"]["{key}"]')

    def cancel(self, context):
        bpy.ops.screen.animation_cancel()
        context.scene.vr_motion_capture = False

    def modal(self, context, event):
        if event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'FINISHED'}

        if context.scene.frame_current == context.scene.frame_end:
            self.cancel(context)
            return {'FINISHED'}

        self.keyframe_grip(context, 0, self._wm)  # TODO make one function call
        self.keyframe_grip(context, 1, self._wm)
        session_state = context.window_manager.xr_session_state
        self.save_controller_data(context, session_state, 'left', 'fly_forward')
        self.save_controller_data(context, session_state, 'left', 'fly_left')
        self.save_controller_data(context, session_state, 'left', 'nav_grab')
        self.save_controller_data(context, session_state, 'left', 'teleport')
        self.save_controller_data(context, session_state, 'left', 'nav_reset')
        self.save_controller_data(context, session_state, 'right', 'fly_forward')
        self.save_controller_data(context, session_state, 'right', 'fly_left')
        self.save_controller_data(context, session_state, 'right', 'nav_grab')
        self.save_controller_data(context, session_state, 'right', 'teleport')
        self.save_controller_data(context, session_state, 'right', 'nav_reset')
        return {'PASS_THROUGH'}

    def execute(self, context):
        if context.scene.vr_motion_capture == True:
            self.report({'ERROR'}, "VR Mocap Session Already in Progress")
            return {'CANCELLED'}
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
        bpy.ops.screen.animation_play()
        return {'RUNNING_MODAL'}


class VRMOCAP_OT_enable_mocap_controllers(bpy.types.Operator):
    bl_idname = "view3d.enable_mocap_controllers"
    bl_label = "Enable Mocap on Controllers"

    @classmethod
    def poll(cls, context):
        if not context.scene.vr_mocap_controllers:
            return True

    def execute(self, context):
        bpy.ops.wm.xr_session_toggle()
        while context.window_manager.xr_session_state is None:
            wait_time += 1
            time.sleep(1)
            if wait_time == 5:
                self.report(
                    {'ERROR'},
                    "Failed to get device information. Is a device plugged in?",
                )
                return {'CANCELLED'}
            print("waiting for vr session")
        vr_mocap_actionmaps_clear(context.window_manager.xr_session_state)
        context.scene.vr_mocap_controllers = True
        bpy.ops.wm.xr_session_toggle()
        return {'FINISHED'}


class VRMOCAP_OT_disable_mocap_controllers(bpy.types.Operator):
    bl_idname = "view3d.disable_mocap_controllers"
    bl_label = "Disable Mocap Controllers"

    @classmethod
    def poll(cls, context):
        if context.scene.vr_mocap_controllers:
            return True

    def execute(self, context):
        bpy.ops.wm.xr_session_toggle()
        wait_time = 0
        while context.window_manager.xr_session_state is None:
            wait_time += 1
            time.sleep(1)
            if wait_time == 5:
                self.report(
                    {'ERROR'},
                    "Failed to get device information. Is a device plugged in?",
                )
                return {'CANCELLED'}
            print("waiting for vr session")
        vr_mocap_actionmaps_restore(context.window_manager.xr_session_state)
        context.scene.vr_mocap_controllers = False
        bpy.ops.wm.xr_session_toggle()
        return {'FINISHED'}


class VRMOCAP_OT_add_custom_properties(bpy.types.Operator):
    bl_idname = "view3d.add_custom_properties"
    bl_label = "Add Custom Properties"

    def execute(self, context):
        armature = context.scene.obj_selection
        left_target = armature.pose.bones[context.scene.left_bone_selection]
        right_target = armature.pose.bones[context.scene.right_bone_selection]
        names = ["fly_forward", "fly_left", "nav_reset", "nav_grab", "teleport"]
        for target in [left_target, right_target]:
            for name in names:
                custom_float_create(
                    target=target, value=0.0, name=name, min=-9999.9, max=9999.9
                )
        return {'FINISHED'}


classes = (
    VRMOCAP_OT_enable_mocap_controllers,
    VRMOCAP_OT_disable_mocap_controllers,
    VRMOCAP_OT_vr_save_position_start,
    VRMOCAP_OT_add_custom_properties,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
