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



import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

class VIEW3D_PT_vr_save_position(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VR"
    bl_label = "VR Capture"
    
    def draw(self, context):
        row = self.layout.row()
        row.prop(context.scene, "vr_target_left", text= "Left")
        row.prop(context.scene, "vr_target_right", text="Right")
        enabled = context.scene.vr_motion_capture
        self.layout.operator("view3d.vr_save_pose", depress=enabled)


class VIEW3D_OT_vr_save_position(bpy.types.Operator):
    bl_idname = "view3d.vr_save_pose"
    bl_label = "Save VR Poses"

    ## TODO WARN USER IF VR ADDON IS NOT ENABLED OR SESSIONS IS NOT STARTED
    _left_target = None
    _right_target = None
    _wm = None

    @staticmethod
    def _get_controller_pose_matrix(context, idx, wm):
        scale=1.0
        loc = wm.xr_session_state.controller_grip_location_get(context, idx)
        rot = wm.xr_session_state.controller_grip_rotation_get(context, idx)
        rotmat = Matrix.Identity(3)
        rotmat.rotate(Quaternion(Vector(rot)))
        rotmat.resize_4x4()
        transmat = Matrix.Translation(loc)
        scalemat = Matrix.Scale(scale, 4)
        return transmat @ rotmat @ scalemat
    
    def keyframe_grip(self, context, idx:int,wm):
        target_object = self._left_target if idx == 0 else self._right_target
        target_object.matrix_basis = self._get_controller_pose_matrix(context, idx, wm)
        target_object.keyframe_insert('location')
        target_object.keyframe_insert('rotation_euler')

    def create_new_action(self,  obj:bpy.types.Object):
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
        self.keyframe_grip(context, 1, self._wm)
        return {'PASS_THROUGH'}

    def execute(self, context):
        if context.scene.vr_target_left is None or  context.scene.vr_target_right is None:
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
    





classes = (VIEW3D_OT_vr_save_position,VIEW3D_PT_vr_save_position)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.vr_target_left = bpy.props.PointerProperty(type=bpy.types.Object)
    bpy.types.Scene.vr_target_right = bpy.props.PointerProperty(type=bpy.types.Object)
    bpy.types.Scene.vr_motion_capture = bpy.props.BoolProperty(name="VR Motion Capture Enabled", default=False)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.vr_target_left
    del bpy.types.Scene.vr_target_right