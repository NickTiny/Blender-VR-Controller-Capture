import bpy

def custom_float_create(
    target: bpy.types.PoseBone, name: str, value: str, min: str, max: str
) -> str:
    target[name] = value
    id_props = target.id_properties_ui(name)
    id_props.update(
        min=min,
        max=max,
        default=1.0,
    )
    target.property_overridable_library_set(f'["{name}"]', True)
    return target[name]

def armature_filter(self, object):
    return object.type == 'ARMATURE'

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
    right_bone_name : bpy.props.StringProperty(name="Right Bone", description="VR MoCap Target for Right Controller") # type:ignore
    left_bone_name : bpy.props.StringProperty(name="Left Bone", description="VR MoCap Target for Left Controller") # type:ignore

    vr_offset_right : bpy.props.FloatVectorProperty( # type:ignore
        name="Rotation Offset", subtype="EULER", size=3, default=(-1.5708, 0, -1.5708)
    )
    vr_offset_left : bpy.props.FloatVectorProperty( # type:ignore
        name="Rotation Offset", subtype="EULER", size=3, default=(-1.5708, 0, -1.5708)
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