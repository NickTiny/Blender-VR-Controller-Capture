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
        self.layout.prop(context.scene, "vr_target")
        self.layout.operator("view3d.vr_save_pose")


class VIEW3D_OT_vr_save_position(bpy.types.Operator):
    bl_idname = "view3d.vr_save_pose"
    bl_label = "Save VR Poses"

    ## TODO WARN USER IF VR ADDON IS NOT ENABLED OR SESSIONS IS NOT STARTED

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

    def execute(self, context):
        if context.scene.vr_target is None:
            self.report({'ERROR'}, "No object is set")
            return {'CANCELLED'} 
        idx = 0
        is_grip = True

        obj = context.scene.vr_target 
        obj.matrix_basis = self._get_controller_pose_matrix(context, idx, is_grip, 1.0)
        obj.keyframe_insert('location')
        obj.keyframe_insert('rotation_euler')

        return {'FINISHED'}



classes = (VIEW3D_OT_vr_save_position,VIEW3D_PT_vr_save_position)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.vr_target = bpy.props.PointerProperty(type=bpy.types.Object)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.vr_target