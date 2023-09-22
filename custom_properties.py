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
