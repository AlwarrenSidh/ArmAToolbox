# GPL 3.0

import bpy
import os.path as Path
import ArmaTools
from bpy.types import Menu

class ATBX_MT_named_selection_menu(Menu):
    bl_label = "Named Selections"

    def draw(self, context):
        layout = self.layout



class ATBX_MT_named_properties_menu(Menu):
    bl_label = "Named Properties"

    def draw(self, context):
        layout = self.layout
        layout.operator("armatoolbox.clear_props", text="Clear all", icon='CANCEL')


menu_classes = (
    #ATBX_MT_named_selection_menu,
    ATBX_MT_named_properties_menu,
)


def register():
    from bpy.utils import register_class
    for c in menu_classes:
        register_class(c)


def unregister():
    from bpy.utils import unregister_class
    for c in menu_classes:
        unregister_class(c)
