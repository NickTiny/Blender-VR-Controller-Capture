# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import time
from mathutils import  Matrix, Quaternion, Vector
from .mocap_actionmaps import vr_mocap_actionmaps_clear, vr_mocap_actionmaps_restore
from . import constants
import addon_utils


class VRMPCAP_OT_enabled_vr_preview_addon(bpy.types.Operator):
    bl_idname = "view3d.enabled_vr_preview_addon"
    bl_label = "Enable 'VR Scene Inspection Add-On'"
    bl_description = "Ensure VR Scene Inspection Add-On is enabled"

    def execute(self, context):
        addon_utils.enable("viewport_vr_preview")
        return {'FINISHED'}


class VRMOCAP_OT_vr_save_position_start(bpy.types.Operator):
    bl_idname = "view3d.vr_save_pose"
    bl_label = "Start Recording VR MoCap Session"
    bl_description = (
        "Begins playback in the current scene, while capturing all inputs "
        "from VR Controllers onto the target armature's bones. All button "
        "presses are saved as custom properties, location and scale in Saved to the "
        "bone's transforms. To end recording hit used `ESC` key"
    )

    _left_target = None
    _right_target = None
    _wm = None
    _vr_mocap = None

    @classmethod
    def poll(cls, context):
        vr_mocap = context.scene.vr_mocap
        if not context.window_manager.xr_session_state:
            cls.poll_message_set("Please Start VR MoCap Session First")
        if not vr_mocap.controller_override:
            cls.poll_message_set("Please Restart VR MoCap Session, controller override faild to activate")
        if vr_mocap.left_bone_name == vr_mocap.right_bone_name:
            cls.poll_message_set("Cannot target the same bone with both controllers")
        return True

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
        armature = self._vr_mocap.capture_obj
        bones = armature.pose.bones
        target_bone = bones[bone_name]
        # TODO Make this better
        offset = (
            self._vr_mocap.vr_offset_left if idx == 0 else self._vr_mocap.vr_offset_right
        )
        # quat_matrix = mathutils.Quaternion(offset).to_matrix().to_4x4()
        matrix_x = self._get_controller_pose_matrix(
            context, idx, wm
        ) @ target_bone.matrix.Rotation(offset.x, 4, "X")
        matrix_x_y = matrix_x @ target_bone.matrix.Rotation(offset.y, 4, "Y")
        target_bone.matrix = matrix_x_y @ target_bone.matrix.Rotation(offset.z, 4, "Z")
        target_bone.keyframe_insert('location')
        target_bone.keyframe_insert('rotation_euler')

    def create_new_action(self, obj: bpy.types.Object):
        obj.animation_data_create()
        action = bpy.data.actions.new(obj.name)
        obj.animation_data.action = action
        return obj.animation_data.action

    def get_bone_via_hand(self, context, hand):
        if hand == "right":
            return self._vr_mocap.right_bone_name
        else:
            return self._vr_mocap.left_bone_name

    def save_controller_data(self, context, session_state, hand, key):
        armature = self._vr_mocap.capture_obj
        bones = armature.pose.bones
        bone_name = self.get_bone_via_hand(context, hand)
        target = bones[bone_name]
        prop_name = constants.CONTROLLER_BUTTONS[constants.ALL_CONTROLLER_ACTIONS.index(key)][1]
        target[f'{prop_name}'] = session_state.action_state_get(
            context=context,
            action_set_name=session_state.actionmaps[0].name,
            action_name=f"{key}",
            user_path=f'/user/hand/{hand}',
        )[0]
        armature.keyframe_insert(data_path=f'pose.bones["{bone_name}"]["{prop_name}"]')

    def cancel(self, context):
        bpy.ops.screen.animation_cancel()
        self._vr_mocap.recording_active = False

    def modal(self, context, event):
        if event.type in {'ESC'}:
            self.cancel(context)
            return {'FINISHED'}

        if context.scene.frame_current == context.scene.frame_end:
            self.cancel(context)
            return {'FINISHED'}

        self.keyframe_grip(context, 0, self._wm)  # TODO make one function call
        self.keyframe_grip(context, 1, self._wm)
        session_state = context.window_manager.xr_session_state
        for action_name in constants.LEFT_ONLY_CONTROLLER_ACTIONS:
            self.save_controller_data(context, session_state, 'right', action_name)
        for action_name in constants.ALL_CONTROLLER_ACTIONS:
            self.save_controller_data(context, session_state, 'left', action_name)

        return {'PASS_THROUGH'}

    def execute(self, context):
        self._vr_mocap  = context.scene.vr_mocap
        if self._vr_mocap.recording_active == True:
            self.report({'ERROR'}, "VR Mocap Session Already in Progress")
            return {'CANCELLED'}
        # TODO Check if properties are ready for capture
        self._vr_mocap.recording_active = True
        self._left_target = self._vr_mocap.capture_obj.pose.bones[
            self._vr_mocap.left_bone_name
        ]
        self._right_target = self._vr_mocap.capture_obj.pose.bones[
            self._vr_mocap.right_bone_name
        ]
        self.create_new_action(self._vr_mocap.capture_obj)
        self._left_target
        self._wm = context.window_manager
        self._wm.modal_handler_add(self)
        bpy.ops.screen.animation_play()
        return {'RUNNING_MODAL'}
        


class VRMOCAP_OT_start_mocap_session(bpy.types.Operator):
    bl_idname = "view3d.start_mocap_session"
    bl_label = "Start VR MoCap Session"
    bl_description = (
        "Start VR Session with Motion Capture mode enabled. "
        "This will disable all controller inputs, controller inputs will instead be captured "
        "Always Enable/Disable your MoCap session with this operator only"
    )

    @classmethod
    def poll(cls, context):
        vr_mocap = context.scene.vr_mocap
        if context.window_manager.xr_session_state:
            cls.poll_message_set("Close the existing VR Sessions before starting MoCap")
        if vr_mocap.recording_active:
            cls.poll_message_set("Cannot stop VR Session while recording is active")
        return True
    
    def safely_toggle_vr_session(self, context):
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

    def execute(self, context):
        if context.window_manager.xr_session_state:
            # Disable VR Mocap Action Maps if session is already active
            context.scene.vr_actions_enable = True
            vr_mocap_actionmaps_restore(context.window_manager.xr_session_state)
            context.scene.vr_mocap.controller_override = False
            self.safely_toggle_vr_session(context)
        else:
            # Enable VR Mocap Action Maps if session is already inactive
            self.safely_toggle_vr_session(context)
            vr_mocap_actionmaps_clear(context.window_manager.xr_session_state)
            context.scene.vr_mocap.controller_override = True
        return {'FINISHED'}



classes = (
    VRMPCAP_OT_enabled_vr_preview_addon,
    VRMOCAP_OT_start_mocap_session,
    VRMOCAP_OT_vr_save_position_start,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
