# SPDX-License-Identifier: GPL-2.0-or-later
if "bpy" in locals():
    import importlib

    importlib.reload(properties)
else:
    from . import properties


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
from .custom_properties import custom_float_create


class VRMOCAP_OT_vr_save_position_start(bpy.types.Operator):
    bl_idname = "view3d.vr_save_pose"
    bl_label = "Stop Saving VR Poses"


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
        # TODO Verify this works on all bone rolls, see if there is a better way
        target_bone.matrix = self._get_controller_pose_matrix(context, idx, wm)
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


### Landmarks.
class VIEW3D_OT_vr_landmark_add(Operator):
    bl_idname = "view3d.vr_landmark_add"
    bl_label = "Add VR Landmark"
    bl_description = "Add a new VR landmark to the list and select it"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        landmarks = scene.vr_landmarks

        landmarks.add()

        # select newly created set
        scene.vr_landmarks_selected = len(landmarks) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_landmark_from_camera(Operator):
    bl_idname = "view3d.vr_landmark_from_camera"
    bl_label = "Add VR Landmark from Camera"
    bl_description = (
        "Add a new VR landmark from the active camera object to the list and select it"
    )
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        cam_selected = False

        vl_objects = bpy.context.view_layer.objects
        if vl_objects.active and vl_objects.active.type == 'CAMERA':
            cam_selected = True
        return cam_selected

    def execute(self, context):
        scene = context.scene
        landmarks = scene.vr_landmarks
        cam = context.view_layer.objects.active
        lm = landmarks.add()
        lm.type = 'OBJECT'
        lm.base_pose_object = cam
        lm.name = "LM_" + cam.name

        # select newly created set
        scene.vr_landmarks_selected = len(landmarks) - 1

        return {'FINISHED'}


class VIEW3D_OT_vr_landmark_from_session(Operator):
    bl_idname = "view3d.vr_landmark_from_session"
    bl_label = "Add VR Landmark from Session"
    bl_description = "Add VR landmark from the viewer pose of the running VR session to the list and select it"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return bpy.types.XrSessionState.is_running(context)

    def execute(self, context):
        scene = context.scene
        landmarks = scene.vr_landmarks
        wm = context.window_manager

        lm = landmarks.add()
        lm.type = "CUSTOM"
        scene.vr_landmarks_selected = len(landmarks) - 1

        loc = wm.xr_session_state.viewer_pose_location
        rot = wm.xr_session_state.viewer_pose_rotation.to_euler()

        lm.base_pose_location = loc
        lm.base_pose_angle = rot[2]

        return {'FINISHED'}


class VIEW3D_OT_vr_camera_landmark_from_session(Operator):
    bl_idname = "view3d.vr_camera_landmark_from_session"
    bl_label = "Add Camera and VR Landmark from Session"
    bl_description = "Create a new Camera and VR Landmark from the viewer pose of the running VR session and select it"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return bpy.types.XrSessionState.is_running(context)

    def execute(self, context):
        scene = context.scene
        landmarks = scene.vr_landmarks
        wm = context.window_manager

        lm = landmarks.add()
        lm.type = 'OBJECT'
        scene.vr_landmarks_selected = len(landmarks) - 1

        loc = wm.xr_session_state.viewer_pose_location
        rot = wm.xr_session_state.viewer_pose_rotation.to_euler()

        cam = bpy.data.cameras.new(data_("Camera") + "_" + lm.name)
        new_cam = bpy.data.objects.new(data_("Camera") + "_" + lm.name, cam)
        scene.collection.objects.link(new_cam)
        new_cam.location = loc
        new_cam.rotation_euler = rot

        lm.base_pose_object = new_cam

        return {'FINISHED'}


class VIEW3D_OT_update_vr_landmark(Operator):
    bl_idname = "view3d.update_vr_landmark"
    bl_label = "Update Custom VR Landmark"
    bl_description = (
        "Update the selected landmark from the current viewer pose in the VR session"
    )
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        selected_landmark = properties.VRLandmark.get_selected_landmark(context)
        return (
            bpy.types.XrSessionState.is_running(context)
            and selected_landmark.type == 'CUSTOM'
        )

    def execute(self, context):
        wm = context.window_manager

        lm = properties.VRLandmark.get_selected_landmark(context)

        loc = wm.xr_session_state.viewer_pose_location
        rot = wm.xr_session_state.viewer_pose_rotation.to_euler()

        lm.base_pose_location = loc
        lm.base_pose_angle = rot

        # Re-activate the landmark to trigger viewer reset and flush landmark settings to the session settings.
        properties.vr_landmark_active_update(None, context)

        return {'FINISHED'}


class VIEW3D_OT_vr_landmark_remove(Operator):
    bl_idname = "view3d.vr_landmark_remove"
    bl_label = "Remove VR Landmark"
    bl_description = "Delete the selected VR landmark from the list"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        landmarks = scene.vr_landmarks

        if len(landmarks) > 1:
            landmark_selected_idx = scene.vr_landmarks_selected
            landmarks.remove(landmark_selected_idx)

            scene.vr_landmarks_selected -= 1

        return {'FINISHED'}


class VIEW3D_OT_cursor_to_vr_landmark(Operator):
    bl_idname = "view3d.cursor_to_vr_landmark"
    bl_label = "Cursor to VR Landmark"
    bl_description = "Move the 3D Cursor to the selected VR Landmark"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        lm = properties.VRLandmark.get_selected_landmark(context)
        if lm.type == 'SCENE_CAMERA':
            return context.scene.camera is not None
        elif lm.type == 'OBJECT':
            return lm.base_pose_object is not None

        return True

    def execute(self, context):
        scene = context.scene
        lm = properties.VRLandmark.get_selected_landmark(context)
        if lm.type == 'SCENE_CAMERA':
            lm_pos = scene.camera.location
        elif lm.type == 'OBJECT':
            lm_pos = lm.base_pose_object.location
        else:
            lm_pos = lm.base_pose_location
        scene.cursor.location = lm_pos

        return {'FINISHED'}


class VIEW3D_OT_add_camera_from_vr_landmark(Operator):
    bl_idname = "view3d.add_camera_from_vr_landmark"
    bl_label = "New Camera from VR Landmark"
    bl_description = "Create a new Camera from the selected VR Landmark"
    bl_options = {'UNDO', 'REGISTER'}

    def execute(self, context):
        scene = context.scene
        lm = properties.VRLandmark.get_selected_landmark(context)

        cam = bpy.data.cameras.new(data_("Camera") + "_" + lm.name)
        new_cam = bpy.data.objects.new(data_("Camera") + "_" + lm.name, cam)
        scene.collection.objects.link(new_cam)
        angle = lm.base_pose_angle
        new_cam.location = lm.base_pose_location
        new_cam.rotation_euler = (math.pi / 2, 0, angle)

        return {'FINISHED'}


class VIEW3D_OT_camera_to_vr_landmark(Operator):
    bl_idname = "view3d.camera_to_vr_landmark"
    bl_label = "Scene Camera to VR Landmark"
    bl_description = "Position the scene camera at the selected landmark"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera is not None

    def execute(self, context):
        scene = context.scene
        lm = properties.VRLandmark.get_selected_landmark(context)

        cam = scene.camera
        angle = lm.base_pose_angle
        cam.location = lm.base_pose_location
        cam.rotation_euler = (math.pi / 2, 0, angle)

        return {'FINISHED'}


class VIEW3D_OT_vr_landmark_activate(Operator):
    bl_idname = "view3d.vr_landmark_activate"
    bl_label = "Activate VR Landmark"
    bl_description = "Change to the selected VR landmark from the list"
    bl_options = {'UNDO', 'REGISTER'}

    index: bpy.props.IntProperty(
        name="Index",
        options={'HIDDEN'},
    )

    def execute(self, context):
        scene = context.scene

        if self.index >= len(scene.vr_landmarks):
            return {'CANCELLED'}

        scene.vr_landmarks_active = (
            self.index
            if self.properties.is_property_set("index")
            else scene.vr_landmarks_selected
        )

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
    VRMOCAP_GT_vr_camera_cone,
    VRMOCAP_GT_vr_controller_grip,
    VRMOCAP_GT_vr_controller_aim,
    VRMOCAP_GGT_vr_viewer_pose,
    VRMOCAP_GGT_vr_controller_poses,
    VRMOCAP_OT_vr_save_position_start,
    VRMOCAP_OT_add_custom_properties,
    VIEW3D_OT_vr_landmark_add,
    VIEW3D_OT_vr_landmark_from_camera,
    VIEW3D_OT_vr_landmark_from_session,
    VIEW3D_OT_vr_camera_landmark_from_session,
    VIEW3D_OT_update_vr_landmark,
    VIEW3D_OT_vr_landmark_remove,
    VIEW3D_OT_cursor_to_vr_landmark,
    VIEW3D_OT_add_camera_from_vr_landmark,
    VIEW3D_OT_camera_to_vr_landmark,
    VIEW3D_OT_vr_landmark_activate,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
