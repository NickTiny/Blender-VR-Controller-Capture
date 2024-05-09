import bpy
from . import constants


def custom_float_create(
    target: bpy.types.PoseBone, name: str, value: str, min: str, max: str
) -> str:
    target[name] = value
    id_props = target.id_properties_ui(name)
    id_props.update(
        min=min,
        max=max,
        default=1.0,
        description=constants.CONTROLLER_BUTTONS[constants.ALL_CONTROLLER_BUTTON_PROPS.index(name)][2]
    )
    target.property_overridable_library_set(f'["{name}"]', True)
    return target[name]

def armature_filter(self, object):
    return object.type == 'ARMATURE'

def get_safely_string_prop(self, name: str) -> str:
    """Return String Prop without Key Error"""
    try:
        return self[name]
    except KeyError:
        return

class VRMOCAP_Properties(bpy.types.PropertyGroup):

    recording_active : bpy.props.BoolProperty( # type:ignore
        name="Recording VR MoCap", default=False
    )
    controller_override : bpy.props.BoolProperty( # type:ignore
        name="Override Controllers for VR MoCap", default=False
    )

    # Pointer definitions
    capture_obj : bpy.props.PointerProperty(# type:ignore
        name="Target Armature",
        description="Armature with the bones that will be VR MoCap Targets",
        type=bpy.types.Object, 
        poll=armature_filter,
    )

    def create_vr_props(self, prop_name, bone_name):
        """Creates custom properties needed for VR MoCap Recording
        these properties are floats created on the object, because
        they need to be keyframe-able. These properties represent
        the controller buttons found in Blender's XR Session"""
        bone = self["capture_obj"].pose.bones.get(bone_name)
        names = constants.ALL_CONTROLLER_BUTTON_PROPS
        if bone:
            # Create Controller Button Custom Properties
            self[prop_name] = bone_name
            for name in names:
                custom_float_create(
                    target=bone, value=0.0, name=name, min=-9999.9, max=9999.9
                )
            # Set Bone Rotation Mode
            bone.rotation_mode = constants.BONE_ROTATION_MODE
        else:
            self[prop_name] = ""
        return
    
    def check_bone_for_vr_props(self,  prop_name, bone_name):
        """Checks if Controller Button Properties have already
        been created on the active bone"""
        if not self["capture_obj"]:
            return 
        bone = self["capture_obj"].pose.bones.get(bone_name)
        if not bone:
            return
        try:
            bone[constants.COMMON_CONTROLLER_BUTTON_PROPS[0]]
            return
        except KeyError:
            self.create_vr_props(prop_name, bone_name)


    def get_right_bone(self):
        """Get String Property of Pose Bone Name"""
        bone_name = get_safely_string_prop(self, "right_bone_name")
        if not bone_name:
            return ""
        
        self.check_bone_for_vr_props("right_bone_name", bone_name)
        return bone_name
    
    def get_left_bone(self):
        """Get String Property of Pose Bone Name"""
        bone_name = get_safely_string_prop(self, "left_bone_name")
        if not bone_name:
            return ""
        self.check_bone_for_vr_props("left_bone_name", bone_name)
        return bone_name
    
    def set_left_bone(self, input):
        """Sets String Property, with Pose Bone Name"""
        self.create_vr_props("left_bone_name", input)
    
    def set_right_bone(self, input):
        """Sets String Property, with Pose Bone Name"""
        self.create_vr_props("right_bone_name", input)

    def get_bones(self, context, edit_text):
        if not self["capture_obj"]:
            return []
        return [bone.name for bone in self.capture_obj.pose.bones]

    right_bone_name : bpy.props.StringProperty(# type:ignore
        name="Right Bone", 
        description="VR MoCap Target for Right Controller", 
        get=get_right_bone, 
        set=set_right_bone, 
        options=set(),
        ) 
    left_bone_name : bpy.props.StringProperty(# type:ignore
        name="Left Bone", 
        description="VR MoCap Target for Left Controller", 
        get=get_left_bone, 
        set=set_left_bone, 
        options=set(), 
        ) 

    vr_offset_right : bpy.props.FloatVectorProperty( # type:ignore
        name="Right Rotation Offset", subtype="EULER", size=3, default=(-1.5708, 0, -1.5708)
    )
    vr_offset_left : bpy.props.FloatVectorProperty( # type:ignore
        name="Left Rotation Offset", subtype="EULER", size=3, default=(-1.5708, 0, -1.5708)
    )




classes = (VRMOCAP_Properties,)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.vr_mocap = bpy.props.PointerProperty(
        name="VR MoCap",
        type=VRMOCAP_Properties,
        description="", # TODO add description
    )


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)