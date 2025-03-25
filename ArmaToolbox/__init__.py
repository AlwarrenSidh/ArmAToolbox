bl_info = {
    "name": "Arma: Toolbox",
    "description": "Collection of tools for editing RV Engine content",
    "author": "Hans-Joerg \"Alwarren\" Frieden.",
    "version": (4, 2, 1),
    "blender": (4, 2, 0),
    "location": "View3D > Panels",
    "warning": '',
    "wiki_url": "https://github.com/AlwarrenSidh/ArmAToolbox/wiki",
    "tracker_url": "https://github.com/AlwarrenSidh/ArmAToolbox/issues",
    "category": "3D View"}

import sys, os
#sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ArmaToolbox'))

import bpy
import bpy_extras
import bmesh
import os
import sys
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.app.handlers import persistent

from . import (
    BITxtWriter,
    MDLImporter,
    RTMExporter,
    ASCImporter,
    ASCExporter,
    ArmaTools,
    ArmaProxy,
    RVMatTools,
    BatchMDLExport,
    MDLExporter,
    panels,
    properties,
    lists,
    menus,
    RtmTools
)

from subprocess import call
from time import sleep
from traceback import print_tb
# from . import *

#from RVMatTools import rt_CopyRVMat, mt_RelocateMaterial, mt_getMaterialInfo
import tempfile
from math import *
from mathutils import *
#from ArmaProxy import CopyProxy, CreateProxyPos
import os.path as Path

from bpy.types import AddonPreferences
#from panels import createToggleBox


class ArmaToolboxPreferences(AddonPreferences):
    bl_idname = __name__
    
    o2ScriptProp : bpy.props.StringProperty(
        name="o2Script Path", 
        description="O2Script binary location", 
        subtype="FILE_PATH",
        default="")
    
    # Never worked anyway
    #toolBoxShelf : bpy.props.StringProperty(
    #    name = "Tools shelf Tab name",
    #    description="Name of the shelf that tools will be put on.",
    #    default="Arma 3 Tools"
    #)

    #propertyShelf : bpy.props.StringProperty(
    #    name = "Property Shelf Path Name",
    #    description = "Name of the shelf that properties will be put on",
    #    default = "Arma 3"
    #)

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text="Paths")
        box.prop(self, "o2ScriptProp")

        #box = layout.box()
        #box.label(text="Shelf Names")
        #box.prop(self, "toolBoxShelf")
        #box.prop(self, "propertyShelf")

        #box = layout.box()
        #box.label(text="Defaults")
        #box.prop(self, "defaultApplyModifiers")
        #box.prop(self, "defaultMergeLOD")

def updateMassArray(obj):
    finalArray = {}
    
    for ob in obj.vertex_groups:
        finalArray[ob.name] = 0
        
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    weight_layer = bm.verts.layers.float['FHQWeights']
    
    for v in obj.data.vertices:
        grps = v.groups
        w = bm.verts[v.index][weight_layer]
        for g in grps:
            idx = g.group
            name = obj.vertex_groups[idx].name
            finalArray[name] += w
    
    return finalArray

def getMassForSelection(obj, selectionName):
    for ob in obj.vertex_groups:
        if ob.name == selectionName:
            weight = 0
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            try:
                weight_layer = bm.verts.layers.float['FHQWeights']
            except:
                weight_layer = bm.verts.layers.float.new('FHQWeights')
    
            for v in obj.data.vertices:
                grps = v.groups
                w = bm.verts[v.index][weight_layer]
                for g in grps:
                    idx = g.group
                    if idx == ob.index:
                        weight += w
            return weight
    return 0

def vgroupExtra(self, context):
    layout = self.layout
    obj = context.object
    arma = obj.armaObjProps
    actGrp = obj.vertex_groups.active_index
    guiProps = context.window_manager.armaGUIProps

    # Search and Replace
    row = layout.row()
    box = panels.createToggleBox(context, row, "vgrpRename_open",
                          "VGroup Find and Replace", "armatoolbox.batch_rename_vgrp")
    if guiProps.vgrpRename_open:
        row = box.row()
        row.prop(guiProps, "vgrpRename_from", text="Find")
        row = box.row()
        row.prop(guiProps, "vgrpRename_to", text="Replace")

    # Batch Operation
    row = layout.row()
    box = panels.createToggleBox(context, row, "vgrpB_open",
                          "VGroup Batch Operation", "armatoolbox.match_vgrp")
    if guiProps.vgrpB_open:
        row = box.row()
        row.prop(guiProps, "vgrpB_match", text="Match Pattern")
        row = box.row()
        row.prop(guiProps, "vgrpB_operator", text="Operator")
        row = box.row()
        row.prop(guiProps, "vgrpB_operation", text="Perform")

    layout.separator()

    if obj.mode == 'EDIT':
        row = layout.row()
        row.operator("armatoolbox.vgroup_redefine")
    if arma.isArmaObject and (arma.lod == '1.000e+13' or arma.lod == '4.000e+13' or arma.lod == '6.000e+15'):
        if actGrp>=0:
            row = layout.row()
            row.label(text = "ARMA group weight {:6.2f}".format(getMassForSelection(obj, obj.vertex_groups[actGrp].name)))
        totalWeight = 0
        for k in obj.vertex_groups.keys():
            if k[:9].lower() == "component":
                totalWeight = totalWeight + getMassForSelection(obj, k)
        row.label(text = "Total weight {:6.2f}".format(totalWeight))

    if arma.isArmaObject and (arma.lod == '1.000e+13' or arma.lod == '4.000e+13' or arma.lod == '7.000e+15'):
        row = layout.row()
        row.operator("armatoolbox.create_components")
        row = layout.row()
        row.operator("armatoolbox.renumber_components")
            # TODO:
            # - Need a way to edit this. Possibility is to either extend vertex groups by Arma
            #   weight attribute, or use a global attribute like in some of the arma tools.
            # - Find out if panels can have (temporary) properties
            # - Find a way to split the whole thing into different parts for easier editing
            
#####################################################################################################

#O2Script = "\"" + os.path.join(os.path.dirname(__file__), "convert.bio2s") + "\""
#O2ScriptImport = "\"" + os.path.join(os.path.dirname(__file__), "import.bio2s") + "\""

# from properties import (lodPresets,textureTypes,textureClass)

def getLodPresets():
    return properties.lodPresets
       
###
##   Export RTM Operator
#

class ATBX_OT_rtm_export(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    """Export RTM Animation file"""
    bl_idname = "armatoolbox.export_rtm"
    bl_label = "Export as RTM"
    bl_description = "Export an Arma 2/3 RTM Animation file"
    bl_options = {'PRESET'}
    
    filename_ext = ".rtm"
    filter_glob : bpy.props.StringProperty(
            default="*.rtm",
            options={'HIDDEN'})
    staticPose : bpy.props.BoolProperty(
            name="Static Pose", 
            description="Export the current pose as a static pose", 
            default=False)
    clipFrames : bpy.props.BoolProperty(
            name="Clip Frames to [0,1]", 
            description="Do not export frames that are outside the 0,1 interval for RTM files", 
            default=True)
    
    # Should only pop up on armature
    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj is not None) and (obj.type == 'ARMATURE') and (obj.armaObjProps.isArmaObject == True)
        
    
    # Make sure that the start and end frames are up to date
    def invoke(self, context, event):
        self.startFrame = context.scene.frame_start
        self.endFrame = context.scene.frame_end
        return super().invoke(context, event)
    
    def execute(self, context):
        if self.startFrame == 0 and self.endFrame == 0:
            self.startFrame = context.scene.frame_start
            self.endFrame = context.scene.frame_end

        keyframeList = []
        obj = context.active_object
        prp = obj.armaObjProps.keyFrames
        
        for k in prp:
            keyframeList.append(k.timeIndex)
        if len(keyframeList) == 0: 
            self.staticPose = True
       
        RTMExporter.exportRTM(context, keyframeList, self.filepath, self.staticPose, self.clipFrames)
        
        return{'FINISHED'}

###
##   Export Operator
#
        
class ATBX_OT_asc_export(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname="armatoolbox.ascexport"
    bl_label = "Export as ASC"
    bl_description = "Export as ASC"
    bl_options = {'PRESET'}
    
    filter_glob : bpy.props.StringProperty(
        default="*.p3d",
        options={'HIDDEN'})
    
    filename_ext = ".asc"
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj is not None) and (obj.type == 'MESH') and (obj.armaHFProps.isHeightfield == True)
    
    def execute(self, context):
        try:
            exportASC(context, self.filepath)
        except Exception as e:
            exc_tb = sys.exc_info()[2]
            print_tb(exc_tb)
            print ("{0}".format(exc_tb))
            self.report({'WARNING', 'INFO'}, "I/O error: {0}\n{1}".format(e, exc_tb))
            
        return{'FINISHED'}
        
###
##   Import Operator
#
        
class ATBX_OT_p3d_import(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname="armatoolbox.import_p3d"
    bl_label = "Import P3D"
    bl_description = "Import P3D"
    bl_options = {'PRESET'}
    
    filter_glob : bpy.props.StringProperty(
        default="*.p3d",
        options={'HIDDEN'})

    layeredLods : bpy.props.BoolProperty(
       name="Try to put each LOD on its own layer",
       description = "Tried to put each LOD imported on a separate layer, provided there aren't more than 20",
       default = True)

    filename_ext = ".p3d"

    def execute (self, context):
        error = -2
        try:
            error = MDLImporter.importMDL(context, self.filepath, self.layeredLods)
        except Exception as e:
            exc_tb = sys.exc_info()[2]
            print_tb(exc_tb)
            print ("{0}".format(exc_tb))
            self.report({'WARNING', 'INFO'}, "I/O error: {0}\n{1}".format(e, exc_tb))

        if error == -1:
            self.report({'WARNING', 'INFO'}, "I/O error: Wrong MDL version")
        if error == -2:
            self.report({'WARNING', 'INFO'}, "I/O error: Exception while reading")
        if error == -3:
            self.report({'WARNING', 'INFO'}, "I/O Error: Won't load binarized files")

        return{'FINISHED'}


class ATBX_OT_asc_import(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname="armatoolbox.importasc"
    bl_label = "Import ASC"
    bl_description = "Import ASC"
    bl_options = {'PRESET'}
    
    filter_glob : bpy.props.StringProperty(
        default="*.asc",
        options={'HIDDEN'})

    filename_ext = ".asc"

    def execute (self, context):
        error = -2
        try:
            error = importASC(context, self.filepath)
        except Exception as e:
            exc_tb = sys.exc_info()[2]
            print_tb(exc_tb)
            print ("{0}".format(exc_tb))
            self.report({'WARNING', 'INFO'}, "I/O error: {0}\n{1}".format(e, exc_tb))

        if error == -1:
            self.report({'WARNING', 'INFO'}, "I/O error: Wrong MDL version")
        if error == -2:
            self.report({'WARNING', 'INFO'}, "I/O error: Exception while reading")

        return{'FINISHED'}
        
def ArmaToolboxExportMenuFunc(self, context):
    self.layout.operator(MDLExporter.ATBX_OT_p3d_export.bl_idname, text="Arma 3 P3D (.p3d)")

def ArmaToolboxImportMenuFunc(self, context):
    self.layout.operator(ATBX_OT_p3d_import.bl_idname, text="Arma 3 P3D (.p3d)")

def ArmaToolboxImportASCMenuFunc(self, context):
    self.layout.operator(ATBX_OT_asc_import.bl_idname, text="Arma 3 ASC DEM File (.asc)")

def ArmaToolboxExportASCMenuFunc(self, context):
    self.layout.operator(ATBX_OT_asc_export.bl_idname, text="Arma 3 ASC DEM File (.asc)")

def ArmaToolboxExportBatchMenuFunc(self, context):
    self.layout.operator(BatchMDLExport.ATBX_OT_p3d_batch_export.bl_idname, text="Arma 3 P3D Batch Export (.p3d)")

'''def addProxy():
    verts = [(0,0,0),
             (0,0,2),
             (0,1,0)]

    faces = [(0, 1, 2)]
    return verts, faces

class ArmaToolboxAddProxy(bpy.types.Operator):
    """Add an Arma 2 proxy triangle"""
    bl_idname = "mesh.primitive_armaproxy_add"
    bl_label = "Arma Proxy"
    bl_options = {'REGISTER', 'UNDO'}

    proxy = bpy.props.StringProperty(
            name="Proxy Object",
            description="Box Width"
            )
    prId = bpy.props.IntProperty(
           name = "Proxy ID", 
           description = "Proxy ID", 
           min=1
           )
    
    view_align = bpy.props.BoolProperty(
            name="Align to View",
            default=False,
            )
        
    location = bpy.props.FloatVectorProperty(
            name="Location",
            subtype='TRANSLATION',
            )
    rotation = bpy.props.FloatVectorProperty(
            name="Rotation",
            subtype='EULER',
            )
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' 
    
    def execute(self, context):

        verts_loc, faces = addProxy()

        mesh = bpy.data.meshes.new("Proxy")
        bm = bmesh.new()

        for v_co in verts_loc:
            bm.verts.new(v_co)

        for f_idx in faces:
            bm.faces.new([bm.verts[i] for i in f_idx])

        bm.to_mesh(mesh)
        mesh.update()        

        # add the mesh as an object into the scene with this utility module
        from bpy_extras import object_utils
        objBase = object_utils.object_data_add(context, mesh, operator=self)
        obj = objBase.object   
        
        vgrp = obj.vertex_groups.new("proxy:" + self.proxy + "." + "%03d" % (self.prId))
        vgrp.add([0],1,'ADD')
        vgrp.add([1],1,'ADD')
        vgrp.add([2],1,'ADD')
        
        return {'FINISHED'}

def ArmaToolboxAddProxyMenuFunc(self, context):
    self.layout.operator(ArmaToolboxAddProxy.bl_idname, icon='MESH_CUBE')
'''

def ArmaToolboxExportRTMMenuFunc(self, context):
    self.layout.operator(ATBX_OT_rtm_export.bl_idname, text="Arma 3 .RTM Animation")
        

###################################
# This code is from BlenderNation
'''def select():
    if bpy.context.mode=="OBJECT":
        obj = bpy.context.object
        sel = len(bpy.context.selected_objects)

        if sel==0:
            bpy.selection=[]
        else:
            if sel==1:
                bpy.selection=[]
                bpy.selection.append(obj)
            elif sel>len(bpy.selection):
                for sobj in bpy.context.selected_objects:
                    if sobj not in bpy.selection:
                        bpy.selection.append(sobj)

            elif sel<len(bpy.selection):
                for it in bpy.selection:
                    if it not in bpy.context.selected_objects:
                        bpy.selection.remove(it)

class Selection(bpy.types.Header):
    bl_label = "Selection"
    bl_space_type = "VIEW_3D"
    
    def __init__(self):
        select()

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        if hasattr(bpy, "selection"):
            row.label("Sel: "+str(len(bpy.selection)))
        else:
            row.label("---")
        
# Up to here
###############################################
''' 

###
##   Load Handler - check if there are things that need fixing in a loaded scene
#

def getLodsToFix():
    objects = [obj
               for obj in bpy.data.objects
   
                   if obj.type == 'MESH' and obj.armaObjProps.isArmaObject
              ]
    objList = []
    for o in objects:
        lod = o.armaObjProps.lod
        res = o.armaObjProps.lodDistance
        if lod == "1.000e+4":
            if res == 0:
                objList.append(o)
        elif lod == "1.001e+4":
            objList.append(o)
        elif lod == "1.100e+4":
            if res == 0:
                objList.append(o)
        elif lod == "1.101e+4":
            objList.append(o)
    
    return objList

def fixMassLods():
    objects = [obj
               for obj in bpy.data.objects
   
                   if obj.type == 'MESH' and obj.armaObjProps.isArmaObject
              ]
    for o in objects:
        lod = o.armaObjProps.lod
        #if lod == '1.000e+13' or lod == '4.000e+13':
        #    ArmaTools.attemptFixMassLod (o)
        
        
@persistent
def load_handler(dummy):
    if bpy.data.filepath == "":
        return
    
    print("Load Hook:", bpy.data.filepath)
    
    # Fix old Mass LODs
    fixMassLods()
    
    # Fix Shadows
    #objects = getLodsToFix()       
    #if len(objects) > 0:
    #    bpy.ops.armaToolbox.fixshadows('INVOKE_DEFAULT')


class ImportP3D(bpy.types.Operator, ImportHelper):
    """Load a P3D file"""
    bl_idname = "import_scene.p3d"
    bl_label = "Import P3D"
    bl_options = {'UNDO', 'PRESET'}


    files: bpy.props.CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )

    def execute(self, context):
        if self.files:
            ret = {'CANCELLED'}
            dirname = os.path.dirname(self.filepath)
            for file in self.files:
                path = os.path.join(dirname, file.name)
                if MDLImporter.importMDL(context, path, True) == 0:
                    ret = {'FINISHED'}
            return ret
        else:
            if MDLImporter.importMDL(context,self.filepath, True) == 0:
                ret = {'FINISHED'}
            return ret
        
###
##  Registration
#     

classes = (
    ArmaToolboxPreferences,
    ImportP3D,
    ATBX_OT_p3d_import,
    ATBX_OT_asc_import,
    ATBX_OT_asc_export,
    ATBX_OT_rtm_export
)

def ATBX_vp_menu(self, context):
    self.layout.menu('ATBX_MT_ArmaToolbox_menu')

def register():
    print (__name__ + " registering")
    from bpy.utils import register_class
    
    print("Internal classes...")
    for c in classes:
        register_class(c)

    from . import properties
    properties.register()
    properties.addCustomProperties()

    from . import operators
    operators.register()

    from . import menus
    menus.register()

    from . import panels
    panels.register()

    from . import lists
    lists.register()
    BatchMDLExport.register()
    MDLExporter.register()

    bpy.types.TOPBAR_MT_file_export.append(ArmaToolboxExportMenuFunc)
    bpy.types.TOPBAR_MT_file_import.append(ArmaToolboxImportMenuFunc)
    bpy.types.TOPBAR_MT_file_export.append(ArmaToolboxExportBatchMenuFunc)
    bpy.types.TOPBAR_MT_file_import.append(ArmaToolboxImportASCMenuFunc)
    bpy.types.TOPBAR_MT_file_export.append(ArmaToolboxExportASCMenuFunc)
    #bpy.types.INFO_MT_mesh_add.append(ArmaToolboxAddProxyMenuFunc)
    bpy.types.TOPBAR_MT_file_export.append(ArmaToolboxExportRTMMenuFunc)

    bpy.types.VIEW3D_MT_editor_menus.append(ATBX_vp_menu)

    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)
    bpy.types.DATA_PT_vertex_groups.append(vgroupExtra)
    print("Register done")

def unregister():
    bpy.types.DATA_PT_vertex_groups.remove(vgroupExtra)
    try:
        del bpy.types.WindowManager.armatoolbox
    except:
        pass

    bpy.app.handlers.load_post.remove(load_handler)

    bpy.types.VIEW3D_MT_editor_menus.remove(ATBX_vp_menu)

    bpy.types.TOPBAR_MT_file_export.remove(ArmaToolboxExportMenuFunc)
    bpy.types.TOPBAR_MT_file_import.remove(ArmaToolboxImportMenuFunc)
    bpy.types.TOPBAR_MT_file_export.remove(ArmaToolboxExportBatchMenuFunc)
    bpy.types.TOPBAR_MT_file_import.remove(ArmaToolboxImportASCMenuFunc)
    bpy.types.TOPBAR_MT_file_export.remove(ArmaToolboxExportASCMenuFunc)
    #bpy.utils.unregister_class(ArmaToolboxAddNewProxy)
    #bpy.types.TOPBAR_MT_file_import.remove(ArmaToolboxAddProxyMenuFunc)
    bpy.types.TOPBAR_MT_file_export.remove(ArmaToolboxExportRTMMenuFunc)

    from bpy.utils import unregister_class
    from . import properties,panels,lists,operators,menus

    BatchMDLExport.unregister()
    MDLExporter.unregister()

    lists.unregister()
    panels.unregister()
    menus.unregister()
    operators.unregister()
    properties.unregister()
    for cls in reversed(classes):
        unregister_class(cls)
