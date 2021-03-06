from . import properties_panels
from . import pie_menu

classes = (
    properties_panels.CollissionPanel,
    properties_panels.CollisionMenu,
    pie_menu.VIEW3D_MT_PIE_template
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
