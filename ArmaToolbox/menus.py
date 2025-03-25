# GPL 3.0

import bpy
import os.path as Path
from . import ArmaTools
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

class ATBX_MT_mesh_collector_menu(Menu):
    bl_label = "Mesh Collector"

    def draw(self, context):
        layout = self.layout
        layout.operator("armatoolbox.clear_mesh_collector", text="Clear Mesh List", icon='CANCEL')
        layout.operator("armatoolbox.add_same_config_mesh_collector", text="Add all meshes with the exact same config", icon='ADD')
        layout.operator("armatoolbox.add_any_config_mesh_collector", text="Add all meshes with one common config", icon='ADD')
        layout.operator("armatoolbox.add_atleast_config_mesh_collector", text="Add all meshes with at least all common config", icon='ADD')

class ATBX_MT_ArmaToolbox_menu(Menu):
    bl_label = "Arma 3 Toolbox"

    def draw(self, context):
        layout = self.layout
        layout.operator("armatoolbox.batch_export_p3d", text = "Batch Export", icon = 'EXPORT')
        layout.operator("armatoolbox.export_p3d", text = "Export single P3D", icon = 'EXPORT')
        layout.operator("armatoolbox.import_p3d", text = "Import MDL", icon = 'IMPORT')

menu_classes = (
    #ATBX_MT_named_selection_menu,
    ATBX_MT_named_properties_menu,
    ATBX_MT_mesh_collector_menu,
    ATBX_MT_ArmaToolbox_menu
)


def register():
    from bpy.utils import register_class
    for c in menu_classes:
        register_class(c)


def unregister():
    from bpy.utils import unregister_class
    for c in menu_classes:
        unregister_class(c)
