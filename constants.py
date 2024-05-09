from .mocap_actionmaps import VRDefaultActions

BONE_ROTATION_MODE = 'XYZ'

CONTROLLER_BUTTONS = [
    (VRDefaultActions.FLY_FORWARD, "Up/Down Stick", "Thumbstick up and down direction. Up is positive Down is negative, not captured on Left Controller" ),
    (VRDefaultActions.FLY_LEFT, "Left/Right Stick", "Thumbstick left and right direction. Left is positive, Right is negative only captured on Left Controller"),
    (VRDefaultActions.NAV_RESET, "A Button", "A Button on Quest or equivalant 'nav_reset' button for your device"),
    (VRDefaultActions.NAV_GRAB, "Inner Trigger", "Inner Trigger on Questor equivalant 'nav_grab' button for your device"),
    (VRDefaultActions.TELEPORT, "Outer Trigger", "Outer Trigger on Quest or equivalant 'teleport' button for your device")

]
ALL_CONTROLLER_BUTTON_PROPS = [prop[1] for prop in CONTROLLER_BUTTONS]
COMMON_CONTROLLER_BUTTON_PROPS =ALL_CONTROLLER_BUTTON_PROPS[2:]
LEFT_ONLY_BUTTON_PROPS = ALL_CONTROLLER_BUTTON_PROPS[:2]
ALL_CONTROLLER_ACTIONS = [prop[0] for prop in CONTROLLER_BUTTONS]
LEFT_ONLY_CONTROLLER_ACTIONS = [prop[0] for prop in CONTROLLER_BUTTONS][2:]