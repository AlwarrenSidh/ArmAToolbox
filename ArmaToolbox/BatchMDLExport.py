import bpy
from bpy_extras.io_utils import ImportHelper, ExportHelper
from ArmaTools import GetObjectsByConfig, RunO2Script
from MDLexporter import exportObjectListAsMDL
import os.path as path
import sys

class ArmaToolboxBatchExportConfigProperty(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(name="name", description = "Name of the config")


class ATBX_PT_batch_export_configs(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Configs"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
       
        return operator.bl_idname == "ARMATOOLBOX_OT_batch_export_p3d"


    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator
        prp = operator.configs

        if context.scene.armaExportConfigs.exportConfigs.keys().__len__() != 0:
            row = layout.row()
            row.operator("armatoolbox.select_config", text="All").allNone = True
            row.operator("armatoolbox.select_config", text="None").allNone = False
            col = layout.box().column(align=True)
            for item in context.scene.armaExportConfigs.exportConfigs.values():
                row = col.row()
                row.alignment = 'LEFT'
                name = item.name
                is_enabled = name in prp.keys()
                row.operator(
                    "armatoolbox.rem_exp_config" if is_enabled else "armatoolbox.add_exp_config",
                    icon='CHECKBOX_HLT' if is_enabled else 'CHECKBOX_DEHLT',
                    text=name,
                    emboss=False
                ).config_name = name

class ATBX_PT_batch_export_options(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Options"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "ARMATOOLBOX_OT_batch_export_p3d"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "renumberComponents", text="Re-Number Components")
        layout.prop(operator, "applyModifiers")
        layout.prop(operator, "applyTransforms")

# Operators
class ATBX_OT_add_exp_config(bpy.types.Operator):
    bl_idname = "armatoolbox.add_exp_config"
    bl_label = ""
    bl_description = "Add an export config to export"

    config_name: bpy.props.StringProperty(name="config_name")

    def execute(self, context):
        sfile = context.space_data
        operator = sfile.active_operator
        prp = operator.configs
        item = prp.add()
        item.name = self.config_name
        return {"FINISHED"}


class ATBX_OT_rem_exp_config(bpy.types.Operator):
    bl_idname = "armatoolbox.rem_exp_config"
    bl_label = ""
    bl_description = "Remove an export config from export"

    config_name: bpy.props.StringProperty(name="config_name")

    def execute(self, context):
        sfile = context.space_data
        operator = sfile.active_operator
        prp = operator.configs
        active = prp.keys().index(self.config_name)
        if active != -1:
            prp.remove(active)
        return {"FINISHED"}

class ATBX_OT_select_config(bpy.types.Operator):
    bl_idname = "armatoolbox.select_config"
    bl_label = ""
    bl_description = "Select All/None"

    allNone: bpy.props.BoolProperty(name="allNone")

    def execute(self, context):
        sfile = context.space_data
        operator = sfile.active_operator
        prp = operator.configs

        prp.clear()

        if self.allNone:
            for item in context.scene.armaExportConfigs.exportConfigs.values():
                x = prp.add()
                x.name = item.name
        return {"FINISHED"}

class ATBX_OT_p3d_batch_export(bpy.types.Operator): #, ExportHelper):
    """Batch-Export P3D configs"""
    bl_idname = "armatoolbox.batch_export_p3d"
    bl_label = "Batch Export as P3D"
    #bl_description = "Batch Export as P3D"
    bl_options = {'PRESET', 'UNDO'}

    directory : bpy.props.StringProperty(
        name="Outdir Path",
        description="Where I will save my stuff"
        # subtype='DIR_PATH' is not needed to specify the selection mode.
        # But this will be anyway a directory path.
    )

    configs : bpy.props.CollectionProperty(
        description = "Configs to export",
        type=ArmaToolboxBatchExportConfigProperty,
        options={'HIDDEN'}
    )

    renumberComponents : bpy.props.BoolProperty(
        name = "Re-Number Components",
        description = "Re-Number Geometry Components",
        default = True
    )

    applyModifiers : bpy.props.BoolProperty(
        name = "Apply Modifiers",
        description = "Apply modifiers before exporting",
        default = True
    )
    applyTransforms: bpy.props.BoolProperty(
        name="Apply all transforms",
        description="Apply rotation, scale, and position transforms before exporting",
        default=True
    )

    filename_ext = "."
    use_filter_folder = True

    @classmethod
    def poll(cls, context):
        return context.scene.armaExportConfigs.exportConfigs.keys().__len__() != 0

    def invoke(self, context, event):
        if len(self.configs) == 0:
            for item in context.scene.armaExportConfigs.exportConfigs.values():
                x = self.configs.add()
                x.name = item.name

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if context.view_layer.objects.active == None:
            context.view_layer.objects.active = context.view_layer.objects[0]
        for item in self.configs:
            objs = GetObjectsByConfig(item.name)
            print("Config: " + item.name)
            config = context.scene.armaExportConfigs.exportConfigs[item.name]
            fileName = path.join(self.directory, config.fileName)
            try:
                filePtr = open(fileName, "wb")
                context.view_layer.objects.active = objs[0]
                exportObjectListAsMDL(self, filePtr, self.applyModifiers, True, objs,
                                      self.renumberComponents, self.applyTransforms, config.originObject)
                filePtr.close()
                RunO2Script(context, fileName)
            except Exception as inst:
                str =  "Error writing file " + fileName + " for config " + item.name + ":" + inst.args
                self.report({'ERROR'}, str)
                return {'CANCELLED'}
        
        return {'FINISHED'}

    def draw(self, context):
        pass

clses = (
    # Properties
    ArmaToolboxBatchExportConfigProperty,

    # Operators
    ATBX_OT_p3d_batch_export,
    ATBX_OT_add_exp_config,
    ATBX_OT_rem_exp_config,
    ATBX_OT_select_config,

    # Panels
    ATBX_PT_batch_export_configs,
    ATBX_PT_batch_export_options
)

def register():
    print("BatchMDLExport register")

    from bpy.utils import register_class

    for cs in clses:
        register_class(cs)

def unregister():
    print("BatchMDLExport unregister")
    
    from bpy.utils import unregister_class
    
    for cs in clses:
        unregister_class(cs)
