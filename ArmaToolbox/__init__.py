bl_info = {
    "name": "Arma: Toolbox",
    "description": "Collection of tools for editing Arma 2/3 content",
    "author": "Hans-Joerg \"Alwarren\" Frieden.",
    "version": (2, 0, 0),
    "blender": (2, 7, 0),
    "location": "View3D > Panels",
    "warning": '',
    "wiki_url": "https://github.com/AlwarrenSidh/ArmAToolbox/wiki",
    "tracker_url": "https://github.com/AlwarrenSidh/ArmAToolbox/issues",
    "category": "3D View"}

import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ArmaToolbox'))

import bpy
import bpy_extras
import bmesh
import os
import sys
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.app.handlers import persistent
from BITxtWriter import exportBITxt
from MDLImporter import importMDL
from RTMExporter import exportRTM
from ASCImporter import importASC
from ASCExporter import exportASC
from subprocess import call
from time import sleep
from traceback import print_tb
from ArmaTools import *
from MDLexporter import exportMDL
from RVMatTools import rt_CopyRVMat, mt_RelocateMaterial, mt_getMaterialInfo
import tempfile
#import winreg 
from math import *
from mathutils import *
from ArmaProxy import CopyProxy, CreateProxyPos
import os.path as Path
from SelectionTools import ArmaToolboxSelectionMaker

from bpy.types import AddonPreferences

class ArmaToolboxPreferences(AddonPreferences):
    bl_idname = __package__
    
    o2ScriptProp = bpy.props.StringProperty(
        name="o2Script Path", 
        description="O2Script binary location", 
        subtype="FILE_PATH",
        default="")
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "o2ScriptProp")



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
            weight_layer = bm.verts.layers.float['FHQWeights']
    
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
    if arma.isArmaObject and (arma.lod == '1.000e+13' or arma.lod == '4.000e+13'):
        if actGrp>=0:
            row = layout.row()
            row.label("ARMA group weight {:6.2f}".format(getMassForSelection(obj, obj.vertex_groups[actGrp].name)))

    if arma.isArmaObject and (arma.lod == '1.000e+13' or arma.lod == '4.000e+13' or arma.lod == '7.000e+15'):
        row = layout.row()
        row.operator("armatoolbox.createcomponents")
            # TODO:
            # - Need a way to edit this. Possibility is to either extend vertex groups by Arma
            #   weight attribute, or use a global attribute like in some of the arma tools.
            # - Find out if panels can have (temporary) properties
            # - Find a way to split the whole thing into different parts for easier editing
            
#####################################################################################################

O2Script = "\"" + os.path.join(os.path.dirname(__file__), "convert.bio2s") + "\""
O2ScriptImport = "\"" + os.path.join(os.path.dirname(__file__), "import.bio2s") + "\""





lodPresets=[
    ## Graphical LOD
        ('-1.0', 'Custom', 'Custom Viewing Distance'),
    ## Functional lod
        ('1.000e+3', 'View Gunner', 'View Gunner'),
        ('1.100e+3', 'View Pilot', 'View Pilot'),
        ('1.200e+3', 'View Cargo', 'View Cargo'),
        ('1.000e+4', 'Stencil Shadow', 'Stencil Shadow'),
        ('1.001e+4', 'Stencil Shadow 2', 'Stencil Shadow 2'),
        ('1.100e+4', 'Shadow Volume', 'Shadow Volume'),
        ('1.101e+4', 'Shadow Volume 2', 'Shadow Volume 2'),
        ('1.000e+13', 'Geometry', 'Geometry'),
        ('1.000e+15', 'Memory', 'Memory'),
        ('2.000e+15', 'Land Contact', 'Land Contact'),
        ('3.000e+15', 'Roadway', 'Roadway'),
        ('4.000e+15', 'Paths', 'Paths'),
        ('5.000e+15', 'HitPoints', 'Hit Points'),
        ('6.000e+15', 'View Geometry', 'View Geometry'),
        ('7.000e+15', 'Fire Geometry', 'Fire Geometry'),
        ('8.000e+15', 'View Cargo Geometry', 'View Cargo Geometry'),
        ('9.000e+15', 'View Cargo Fire Geometry', 'View Cargo Fire Geometry'),
        ('1.000e+16', 'View Commander', 'View Commander'),
        ('1.100e+16', 'View Commander Geometry', 'View Commander Geometry'),
        ('1.200e+16', 'View Commander Fire Geometry', 'View Commander Fire Geometry'),
        ('1.300e+16', 'View Pilot Geometry', 'View Pilot Geometry'),
        ('1.400e+16', 'View Pilot Fire Geometry', 'View Pilot Fire Geometry'),
        ('1.500e+16', 'View Gunner Geometry', 'View Gunner Geometry'),
        ('1.600e+16', 'View Gunner Fire Geometry', 'View Gunner Fire Geometry'),
        ('1.700e+16', 'Sub Parts', 'Sub Parts'),
        ('1.800e+16', 'Shadow Volume - View Cargo', 'Cargo View shadow volume'),
        ('1.900e+16', 'Shadow Volume - View Pilot', 'Pilot View shadow volume'),
        ('2.000e+16', 'Shadow Volume - View Gunner', 'Gunner View shadow volume'),
        ('2.100e+16', 'Wreck', 'Wreckage'),
        ('2.000e+13', 'Geometry Buoyancy', 'Geometry Buoyancy'),
        ('4.000e+13', 'Geometry PhysX', 'Geometry PhysX'),
        ('2.000e+4',  'Edit', 'Edit'),
        ]

textureTypes = [
            ("CO", "CO", "Color Value"),
            ("CA", "CA", "Texture with Alpha"),
            ("LCO", "LCO", "Terrain Texture Layer Color"),
            ("SKY", "SKY", "Sky texture"),
            ("NO", "NO", "Normal Map"),
            ("NS", "NS", "Normal map specular with Alpha"),
            ("NOF", "NOF", "Normal map faded"),
            ("NON", "NON", "Normal map noise"),
            ("NOHQ", "NOHQ", "Normal map High Quality"),
            ("NOPX", "NOPX", "Normal Map with paralax"),
            ("NOVHQ", "NOVHQ", "two-part DXT5 compression"),
            ("DT", "DT", "Detail Texture"),
            ("CDT", "CDT", "Colored detail texture"),
            ("MCO", "MCO", "Multiply color"),
            ("DTSMDI", "DTSMDI", "Detail SMDI map"),
            ("MC", "MC", "Macro Texture"),
            ("AS", "AS", "Ambient Shadow texture"),
            ("ADS", "ADS", "Ambient Shadow in Blue"),
            ("PR", "PR", "Ambient shadow from directions"),
            ("SM", "SM", "Specular Map"),
            ("SMDI", "SMDI", "Specular Map, optimized"),
            ("mask", "mask", "Mask for multimaterial"),
            ("TI", "TI", "Thermal imaging map")
]

textureClass = [
            ("Texture", "Texture", "Texture Map"),
            ("Color", "Color", "Procedural Color"),
            ("Custom", "Custom", "Custom Procedural String")
]

def getLodPresets():
    return lodPresets

###
##   Custom Property Collections
#
class ArmaToolboxNamedProperty(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="Name", 
        description = "Property Name")
    value = bpy.props.StringProperty(name="Value",
        description="Property Value") 

class ArmaToolboxKeyframeProperty(bpy.types.PropertyGroup):
    timeIndex = bpy.props.IntProperty(name="Frame Index",
        description="Frame Index for keyframe")

class ArmaToolboxComponentProperty(bpy.types.PropertyGroup):
    name   = bpy.props.StringProperty(name="name", description="Component name")
    weight = bpy.props.FloatProperty(name="weight", description="Weight of Component", default = 0.0)

# Would have preferred to have that in ArmaProxy, but apparently that doesn't work.
# Seriously, can I have JAVA plugins for Blender? Please? Python is shit.
class ArmaToolboxProxyProperty(bpy.types.PropertyGroup):
    open   = bpy.props.BoolProperty(name="open", description="Show proxy data in GUI", default=False)
    name   = bpy.props.StringProperty(name="name", description="Proxy name")
    path   = bpy.props.StringProperty(name="path", description="File path", subtype="FILE_PATH")
    index  = bpy.props.IntProperty(name="index", description="Index of Proxy", default=1)

class ArmaToolboxHeightfieldProperties(bpy.types.PropertyGroup):
    isHeightfield = bpy.props.BoolProperty(
        name = "IsArmaHeightfield",
        description = "Is this an ARMA Heightfield object",
        default = False)
    cellSize = bpy.props.FloatProperty(
        name="cell size",
        description = "Size of a single cell in meters",
        default = 4.0)
    northing = bpy.props.FloatProperty(
        name="northing",
        description="Northing",
        default = 200000.0)
    easting = bpy.props.FloatProperty(
        name="easting",
        description = "Easting",
        default = 0)
    undefVal = bpy.props.FloatProperty(
        name="NODATA value",
        description = "Value for Heightfield holes",
        default=-9999)

class ArmaToolboxProperties(bpy.types.PropertyGroup):
    isArmaObject = bpy.props.BoolProperty(
        name = "IsArmaObject",
        description = "Is this an ARMA exportable object",
        default = False)
    
    # Mesh Objects
    lod = bpy.props.EnumProperty(
        name="LOD Type",
        description="Type of LOD",
        items=lodPresets,
        default='-1.0')
    lodDistance = bpy.props.FloatProperty(
        name="Distance",
        description="Distance of Custom LOD",
        default=1.0)
    mass = bpy.props.FloatProperty(
        name="Mass",
        description="Object Mass",
        default=1.0)
    massArray = bpy.props.CollectionProperty(type = ArmaToolboxComponentProperty, description="Masses")

    namedProps = bpy.props.CollectionProperty(type = ArmaToolboxNamedProperty,
          description="Named Properties")
    namedPropIndex = bpy.props.IntProperty("namedPropIndex", default = -1)
    
    proxyArray = bpy.props.CollectionProperty(type = ArmaToolboxProxyProperty, description = "Proxies")
    
    # Armature
    keyFrames = bpy.props.CollectionProperty(type = ArmaToolboxKeyframeProperty,
          description="Keyframes")
    keyFramesIndex = bpy.props.IntProperty("keyFrameIndex", default = -1)
    motionVector = bpy.props.FloatVectorProperty(name = "RTM Motion Vector", 
         description = "Motion Vector written to the RTM Animation",
          subtype='TRANSLATION')
    centerBone = bpy.props.StringProperty(name="Center Of Animation", 
          description="The center of animation for calculating the motion vector")
    

class ArmaToolboxMaterialProperties(bpy.types.PropertyGroup):
    texture = bpy.props.StringProperty(
        name="Face Texture", 
        description="ARMA texture", 
        subtype="FILE_PATH", 
        default="")
    rvMat = bpy.props.StringProperty(
        name="RVMat Material", 
        description="RVMat associated with this materiaL", 
        subtype="FILE_PATH",
        default="")
    texType = bpy.props.EnumProperty(
        name="Color Map Type",
        description="The type/source of the color for this surface",
        items=textureClass)
    colorValue = bpy.props.FloatVectorProperty(
        name= "Color",
        description= "Color for procedural texture",
        subtype= 'COLOR',
        min= 0.0,
        max= 1.0,
        soft_min= 0.0,
        soft_max= 1.0,
        default= (1.0,1.0,1.0))
    colorType = bpy.props.EnumProperty(
        name="Color Type",
        description="The Type of color, corresponding to the suffix of a texture name",
        items = textureTypes)
    colorString = bpy.props.StringProperty (
        name = "Resulting String", 
        description = "Resulting value for the procedural texture")

#class ArmaToolboxSettingsProperties(bpy.types.PropertyGroup):
#    o2path = bpy.props.StringProperty(
#             name="O2 Installation Paht", 
#             description="The place where Oxygen is installed", 
#             default=O2Path,
#             subtype = "DIR_PATH")


###
##   Material Properties Panel
#

class Arma2MaterialSettingsPanel(bpy.types.Panel):

    bl_label = "Arma Toolbox Material Settings"
    #bl_idname = "Arma2MaterialSettingsPanel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        return (context.active_object
            and context.active_object.select == True
            and context.active_object.type == 'MESH'
            and context.active_object.active_material
            and context.active_object.armaObjProps
            and context.active_object.armaObjProps.isArmaObject
            )

    def draw(self, context):
        obj = bpy.context.active_object
        layout = self.layout
        self.enable = obj.active_material
        
        if self.enable:
            arma = obj.active_material.armaMatProps
            box = layout.box()
            # - box
            row = box.row()
            row.prop(arma, "texType", "Procedural Texture", expand=True)
            row = box.row()
            matType = arma.texType
            if matType == 'Texture':
                row.prop(arma, "texture", "Face Texture")
            elif matType == 'Color':
                row.prop(arma, "colorValue", "Color Texture")
                row.prop(arma, "colorType", "Type")
            elif matType == 'Custom':
                row.prop(arma, "colorString", "Custom Procedural Texture")
            row = box.row()
                    
            # end of box
            layout.separator()
            row = layout.row()
            row.prop(arma, "rvMat", "RV Material file")

 
###
##   Properties Panel
#

class ArmaToolboxNamedPropList(bpy.types.UIList):
    # The draw_item function is called for each item of the collection that is visible in the list.
    #   data is the RNA object containing the collection,
    #   item is the current drawn item of the collection,
    #   icon is the "computed" icon for the item (as an integer, because some objects like materials or textures
    #   have custom icons ID, which are not available as enum items).
    #   active_data is the RNA object containing the active property for the collection (i.e. integer pointing to the
    #   active item of the collection).
    #   active_propname is the name of the active property (use 'getattr(active_data, active_propname)').
    #   index is index of the current item in the collection.
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        prop = item
        layout.label(prop.name)

class ArmaToolboxKeyFrameList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        prop = item
    
        startFrame = context.scene.frame_start
        endFrame = context.scene.frame_end
        frameIdx = prop.timeIndex - startFrame
        timeIdx = frameIdx / (endFrame - startFrame)

        layout.label("%d (time: %f)" %  (prop.timeIndex, timeIdx))
    
    def filter_items(self, context, data, propname):
        helper_funcs = bpy.types.UI_UL_list
        keyFrames = getattr(data, propname)
        # Default return values.
        flt_flags = []
        flt_neworder = []

        # Reorder by name or average weight.
        _sort = [(idx, frame) for idx, frame in enumerate(keyFrames)]
        flt_neworder = helper_funcs.sort_items_helper(_sort, lambda e: e[1].timeIndex, False)

        return flt_flags, flt_neworder

class ArmaToolboxRenameablePropList(bpy.types.UIList):
    # The draw_item function is called for each item of the collection that is visible in the list.
    #   data is the RNA object containing the collection,
    #   item is the current drawn item of the collection,
    #   icon is the "computed" icon for the item (as an integer, because some objects like materials or textures
    #   have custom icons ID, which are not available as enum items).
    #   active_data is the RNA object containing the active property for the collection (i.e. integer pointing to the
    #   active item of the collection).
    #   active_propname is the name of the active property (use 'getattr(active_data, active_propname)').
    #   index is index of the current item in the collection.
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        prop = item
        layout.label(prop.renameable)

class ArmaToolboxRenamableProperty(bpy.types.PropertyGroup):
    renamable = bpy.props.StringProperty(name="Texture Path")
        
class ArmaToolboxGUIProps(bpy.types.PropertyGroup):
    framePanelOpen = bpy.props.BoolProperty(name="Open Frames Settings Panel",
        description="Open or close the settings of the 'Add Frame Range' tool",
        default = False)
    framePanelStart = bpy.props.IntProperty(name="Start of frame range",
        description = "Start of the range of frames to add to the list",
        default = -1, min = 0)
    framePanelEnd = bpy.props.IntProperty(name="ENd of frame range",
        description = "End of the range of frames to add to the list",
        default = -1, min=1)
    framePanelStep = bpy.props.IntProperty(name="Step of frame range",
        description = "Step of the range of frames to add to the list",
        default = 5, min=1)

    bulkRenamePanelOpen = bpy.props.BoolProperty(name="Open Bulk Rename Settings Panel",
        description="Open or close the settings of the 'Bulk Rename' tool",
        default = False) 
    bulkReparentPanelOpen = bpy.props.BoolProperty(name="Open Bulk Reparent Settings Panel",
        description="Open or close the settings of the 'Bulk Reparent' tool",
        default = False) 
    selectionRenamePanelOpen = bpy.props.BoolProperty(name="Open Selection Renaming Settings Panel",
        description="Open or close the settings of the 'Bulk Reparent' tool",
        default = False) 
    rvmatRelocPanelOpen = bpy.props.BoolProperty(name="Open RVMat Relocation Settings Panel",
        description="Open or close the settings of the 'RVMat Relocator' tool",
        default = False) 
    
    hitpointCreatorPanelOpen = bpy.props.BoolProperty(name="Open hitpoint creator settings panel", 
        description="Open or close the 'Hitpoint Creator' tool",
        default = False)
    
    # Bulk Rename features
    renamableList = bpy.props.CollectionProperty(type = ArmaToolboxRenamableProperty,
          description="Renamables")
    renamableListIndex = bpy.props.IntProperty()

    renameFrom = bpy.props.StringProperty("renameFrom", description="Rename From", subtype='FILE_PATH')
    renameTo = bpy.props.StringProperty("renameTo", description="Rename to", subtype='FILE_PATH')
    
    # Bulk Reparent features
    parentFrom = bpy.props.StringProperty("parentFrom", description="Parent From", subtype='DIR_PATH')
    parentTo = bpy.props.StringProperty("parentTo", description="Parent to", subtype='DIR_PATH')
    
    # Selection Rename
    renameSelectionFrom = bpy.props.StringProperty("renameSelectionFrom", description="Rename from")
    renameSelectionTo = bpy.props.StringProperty("renameSelectionTo", description="Rename to")
    
    # RVMat Relocator
    rvmatRelocFile = bpy.props.StringProperty("rvmatRelocFile", description="RVMat to relocate", subtype = 'FILE_PATH')
    rvmatOutputFolder = bpy.props.StringProperty("rvmatOutputFolder", description="RVMat output", subtype = 'DIR_PATH')
      
    
    # Material Relocator
    matOutputFolder = bpy.props.StringProperty("matOutputFolder", description="RVMat output", subtype = 'DIR_PATH')
    matAutoHandleRV = bpy.props.BoolProperty(name="matAutoHandleRV", description="Automatically relocate RVMat", default=True)
    matPrefixFolder = bpy.props.StringProperty("matPrefixFolder", description="Prefix for texture search", subtype = 'DIR_PATH', 
                                               default= "P:\\")
    # Merge as Proxy
    mapProxyObject = bpy.props.StringProperty("mapProxyObject", description="Proxy Object", subtype = 'FILE_PATH')
    mapProxyIndex =  bpy.props.IntProperty("mapProxyIndex", description="Base Index", default=1)
    mapProxyDelete = bpy.props.BoolProperty("mapProxyDelete", description="Delete original", default=True)
    mapProxyEnclose= bpy.props.StringProperty("mapProxyEnclose", description="Enclosed Selection")
    mapOpen = bpy.props.BoolProperty(name="mapOpen", default=False)
    
    # Proxy Path Changer
    proxyPathFrom = bpy.props.StringProperty("proxyPathFrom", description="Proxy Path From", subtype = 'FILE_PATH')
    proxyPathTo = bpy.props.StringProperty("proxyPathTo", description="Proxy path To", subtype = 'FILE_PATH')
    
    # Weight setter
    vertexWeight = bpy.props.FloatProperty("vertexWeight", description="Vertex Weight to set to", default = 0, min=0)
    
    # Selection Tools
    hiddenSelectionName = bpy.props.StringProperty("hiddenSelectionName", description = "Name of the hidden selection to create", default="camo")

    # Hitpoint creator
    hpCreatorSelectionName = bpy.props.StringProperty("hpCreatorSelectionName", description = "Name of the hitpoint selection create", default="_point")
    hpCreatorRadius = bpy.props.FloatProperty("hpCreatorRadius", description = "radius of hitpont sphere", default = 0.3, min = 0.001)

###
##  Update the component list for the mass distribution
#
class ArmaToolboxUpdateList(bpy.types.Operator):
    bl_idname = "armatoolbox.updatelist"
    bl_label = ""
    bl_description = "Update List of components"
    
    def execute(self, context):
        obj = context.active_object
        prp = obj.armaObjProps.massArray

        for grp in obj.vertex_groups:
            if grp.name in prp.keys():
                pass
            else:
                n = prp.add()
                n.name = grp.name
                n.weight = 0.0

        # Is there really no better way to do this? Bummer!
        delList = []
        max = prp.values().__len__()
        for i in range(0,max):
            if prp[i].name not in obj.vertex_groups.keys():
                delList.append(i)
        if len(delList) > 0:
            delList.reverse()
            for item in delList:
                prp.remove(item)

        return {"FINISHED"}

class ArmaToolboxConvertList(bpy.types.Operator):
    bl_idname = "armatoolbox.convertlist"
    bl_label = ""
    bl_description = "Convert Single mass to component mass"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        prp = obj.armaObjProps
        return (prp.mass > 0)
    
    def execute(self, context):
        obj = context.active_object
        prp = obj.armaObjProps.massArray
        num = len(obj.vertex_groups)
        perComponent = obj.armaObjProps.mass / num
        obj.armaObjProps.mass = 0

        for grp in obj.vertex_groups:
            if grp.name in prp.keys():
                pass
            else:
                n = prp.add()
                n.name = grp.name
                n.weight = perComponent

        return {"FINISHED"}

class ArmaToolboxHFPropertiesPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Arma Heightfield Properties"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        ## Visible when there is a selected object, it is a mesh
        obj = context.active_object
       
        return (obj 
            and obj.select == True
            and (obj.type == "MESH" or obj.type == "ARMATURE") )
        
    def draw_header(self, context):
        obj = context.active_object
        hrp = obj.armaHFProps

        self.layout.prop(hrp, "isHeightfield", text="")
        
    def draw(self, context):
        obj = context.active_object
        layout = self.layout
        self.enable = obj.select
        
        hrp = obj.armaHFProps
        layout.active = hrp.isHeightfield
        if obj.type == "MESH" and hrp.isHeightfield:
            row = layout.row()
            row.prop(hrp, "cellSize", "Cell Size")
            
            row = layout.row()
            row.prop(hrp, "northing", "Northing")
            
            row = layout.row()
            row.prop(hrp, "easting", "Easting")
            
            row = layout.row()
            row.prop(hrp, "undefVal", "NODATA_value")
            
            verts = len(obj.data.vertices)
            verts = sqrt(verts)
            row = layout.row()
            row.label("rows/cols: " + str(int(verts)))
            
class ArmaToolboxPropertiesPanel(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Arma Object Properties"
    bl_options = {'DEFAULT_CLOSED'}
    
    @classmethod
    def poll(cls, context):
        ## Visible when there is a selected object, it is a mesh
        obj = context.active_object
       
        return (obj 
            and obj.select == True
            and (obj.type == "MESH" or obj.type == "ARMATURE") )

    def draw_header(self, context):
        obj = context.active_object
        arma = obj.armaObjProps

        self.layout.prop(arma, "isArmaObject", text="")
            
    def draw(self, context):
        obj = context.active_object
        layout = self.layout
        self.enable = obj.select
        
        arma = obj.armaObjProps
        layout.active = arma.isArmaObject
        if obj.type == "MESH":
            #--- Add a button to enable this object for Arma
            #if (arma.isArmaObject == False):
            #    row = layout.row();
            #    row.operator("armatoolbox.enable", text="Make Arma Object")
            #else:
            #--- The LOD selection
            row = layout.row()
            if arma.lod == '-1.0':
                box = row.box()
                newrow = box.row()
                newrow.prop(arma, "lod", "LOD Preset")
                newrow = box.row()
                newrow.prop(arma, "lodDistance", "Resolution")
            elif arma.lod == "1.000e+4" or arma.lod == "1.001e+4" or arma.lod == "1.100e+4" or arma.lod == "1.101e+4" or arma.lod == "2.000e+4":
                box = row.box();
                newrow = box.row()
                newrow.prop(arma, "lod", "LOD Preset")
                if arma.lod == "1.001e+4" or arma.lod == "1.101e+4":
                    newrow = box.row()
                    newrow.label(icon="ERROR", text="That LOD is deprecated")
                newrow = box.row()
                newrow.prop(arma, "lodDistance", "Resolution")
            else:
                row.prop(arma,  "lod", "LOD Preset")
            
            
                    
                    
            
            #--- Named Props
            row = layout.row()
            row.label("Named Properties")
            row = layout.row()
            
            row = layout.row()
            row.template_list(listtype_name = "ArmaToolboxNamedPropList", 
                              dataptr = arma,
                              propname = "namedProps",
                              active_dataptr = arma,
                              active_propname="namedPropIndex");
            col = row.column(align=True)
            col.operator("armatoolbox.addprop", icon="ZOOMIN")
            col.operator("armatoolbox.remprop", icon="ZOOMOUT")    
            
            if arma.namedPropIndex > -1 and arma.namedProps.__len__() > arma.namedPropIndex:
                nprop = arma.namedProps[arma.namedPropIndex]
                box = layout.box()
                row = box.row()
                row.prop(nprop, "name", "Name")
                row = box.row()
                row.prop(nprop, "value", "Value")
            else:
                box = layout.box()
                row = box.row()
                row.label("Name")
                row = box.row()
                row.label("Value")
        else:
            #if (arma.isArmaObject == False):
            #    row = layout.row();
            #    row.operator("armatoolbox.enable", text="Make Arma RTM Armature")
            #else:
            guiProps = context.window_manager.armaGUIProps
            row = layout.row()
            row.label("RTM Keyframes")
            row = layout.row()
            row.template_list(listtype_name="ArmaToolboxKeyFrameList",
                dataptr = arma,
                propname = "keyFrames",
                active_dataptr = arma,
                active_propname="keyFramesIndex"
                )
            row = layout.row()
            row.operator("armatoolbox.addkeyframe", text="Add This Frame", icon="ZOOMIN")
            row = layout.row()
            row.operator("armatoolbox.remkeyframe", text="Remove Frame", icon="ZOOMOUT")
            row = layout.row()
            row.operator("armatoolbox.remallframes", text="Clear", icon="CANCEL")
            row = layout.row()
            row.operator("armatoolbox.addallkeyframes", text="Add Armature Timeline Keys", icon="NDOF_TRANS")
            col = layout.column(align=True)
            split = col.split(percentage=0.15)
            if guiProps.framePanelOpen:
                split.prop(guiProps, "framePanelOpen", text="", icon='DOWNARROW_HLT')
            else:
                split.prop(guiProps, "framePanelOpen", text="", icon='RIGHTARROW')
                
            split.operator("armatoolbox.addframerange", text="Add Frame Range", icon="ARROW_LEFTRIGHT")
            if guiProps.framePanelOpen:
                box = layout.box()
                sub = box.column(align=True)
                if guiProps.framePanelStart == -1:
                    guiProps.framePanelStart = context.scene.frame_start
                if guiProps.framePanelEnd == -1:
                    guiProps.framePanelEnd = context.scene.frame_end
                sub.label("Frame Range")    
                sub.prop(guiProps, "framePanelStart", text="Start")
                sub.prop(guiProps, "framePanelEnd", text="End")
                sub.prop(guiProps, "framePanelStep", text="Step")
            
            box = layout.box()
            row = box.row()
            row.label("RTM Motion Vector")
            if len(arma.centerBone) == 0:
                row = box.row()
                row.prop(arma, "motionVector", text="")
            row = box.row()
            row.prop_search(arma, "centerBone", obj.data, "bones",  text="")
            

def safeAddTime(frame, prop):
    for k in prop:
        if k.timeIndex == frame:
            return
        
    item = prop.add()
    item.timeIndex = frame
    item.name = str(frame)
    return item

class ArmaToolboxAddFrameRange(bpy.types.Operator):
    bl_idname = "armatoolbox.addframerange"
    bl_label = ""
    bl_description = "Add a range of keyframes"
    
    def execute(self, context):
        obj = context.active_object
        prp = obj.armaObjProps.keyFrames
        guiProps = context.window_manager.armaGUIProps
        start = guiProps.framePanelStart
        end = guiProps.framePanelEnd
        step = guiProps.framePanelStep
        
        for frame in range(start, end, step):
            safeAddTime(frame, prp)
            
        return {"FINISHED"}
        
class ArmaToolboxAddKeyFrame(bpy.types.Operator):
    bl_idname = "armatoolbox.addkeyframe"
    bl_label = ""
    bl_description = "Add a keyframe"
    
    def execute(self, context):
        obj = context.active_object
        prp = obj.armaObjProps.keyFrames
        frame = context.scene.frame_current
        safeAddTime(frame, prp)
        return {"FINISHED"}
  
class ArmaToolboxAddAllKeyFrames(bpy.types.Operator):
    bl_idname = "armatoolbox.addallkeyframes"
    bl_label = ""
    bl_description = "Add a keyframe"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj.animation_data is not None and obj.animation_data.action is not None
    
    def execute(self, context):
        obj = context.active_object
        prp = obj.armaObjProps.keyFrames
        
        keyframes = [] 

        if obj.animation_data is not None and obj.animation_data.action is not None:
            fcurves = obj.animation_data.action.fcurves
            for curve in fcurves:
                for kp in curve.keyframe_points:
                    if kp.co.x not in keyframes:
                        keyframes.append(kp.co.x)
        
        keyframes.sort()
        
        for frame in keyframes:
            safeAddTime(frame, prp)
            
        return {"FINISHED"}  
  
class ArmaToolboxRemKeyFrame(bpy.types.Operator):
    bl_idname = "armatoolbox.remkeyframe"
    bl_label = ""
    bl_description = "Remove a keyframe"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        arma = obj.armaObjProps
        return arma.keyFramesIndex != -1
    

    def execute(self, context):
        obj = context.active_object
        arma = obj.armaObjProps
        if arma.keyFramesIndex != -1:
            arma.keyFrames.remove(arma.keyFramesIndex)
        return {"FINISHED"}        
        
class ArmaToolboxRemAllKeyFrame(bpy.types.Operator):
    bl_idname = "armatoolbox.remallframes"
    bl_label = ""
    bl_description = "Remove a keyframe"

    def execute(self, context):
        obj = context.active_object
        arma = obj.armaObjProps
        arma.keyFrames.clear()
        return {"FINISHED"}        
        
        
#class ArmaToolboxSettingsPanel(bpy.types.Panel):
#    bl_space_type = "VIEW_3D"
#    bl_region_type = "UI"
#    bl_label = "Arma Toolbox Settings"
#    
#    @classmethod
#    def poll(cls, context):
#        return True
#            
#    def draw(self, context):
#        layout = self.layout
#          
#        at = context.window_manager.armatoolbox
#
#        row = layout.row()
#        row.label("Path to O2Script.exe")
#        row = layout.row()
#        row.prop(at, "o2path", "")
#        row = layout.row()
#        row.operator("armatoolbox.savesettings", text="Save Settings")

class ArmaToolboxAddProp(bpy.types.Operator):
    bl_idname = "armatoolbox.addprop"
    bl_label = ""
    bl_description = "Add a named Property"
    
    def execute(self, context):
        obj = context.active_object
        prp = obj.armaObjProps.namedProps
        item = prp.add()
        item.name = "<new property>"
        return {"FINISHED"}

class ArmaToolboxRemProp(bpy.types.Operator):
    bl_idname = "armatoolbox.remprop"
    bl_label = ""
    bl_description = "Remove named property"
    
    def execute(self, context):
        obj = context.active_object
        arma = obj.armaObjProps
        if arma.namedPropIndex != -1:
            arma.namedProps.remove(arma.namedPropIndex)
        return {"FINISHED"}
    
###
##   Enable Operator
#

class ArmaToolboxEnable(bpy.types.Operator):
    bl_idname = "armatoolbox.enable"
    bl_label = "Enable for Arma Toolbox"
    
    def execute(self, context):
        obj = context.active_object
        if (obj.armaObjProps.isArmaObject == False):
            obj.armaObjProps.isArmaObject = True
        return{'FINISHED'}
        
###
##   Export RTM Operator
#

class ArmaToolboxExportRTM(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    """Export RTM Animation file"""
    bl_idname = "armatoolbox.exportrtm"
    bl_label = "Export as RTM"
    bl_description = "Export an Arma 2/3 RTM Animation file"
    
    filename_ext = ".rtm"
    filter_glob = bpy.props.StringProperty(
            default="*.rtm",
            options={'HIDDEN'})
    staticPose = bpy.props.BoolProperty(
            name="Static Pose", 
            description="Export the current pose as a static pose", 
            default=False)
    clipFrames = bpy.props.BoolProperty(
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
       
        exportRTM(context, keyframeList, self.filepath, self.staticPose, self.clipFrames)
        
        return{'FINISHED'}

###
##   Export Operator
#
        
#class ArmaToolboxExportBITxt(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
#    bl_idname="armatoolbox.export"
#    bl_label = "Export as P3D"
#    bl_description = "Export as P3D"
#    
#    filter_glob = bpy.props.StringProperty(
#        default="*.p3d",
#        options={'HIDDEN'})
#    
#    selectionOnly = bpy.props.BoolProperty(
#       name = "Selection Only", 
#       description = "Export selected objects only", 
#       default = False)
#    mergeLods = bpy.props.BoolProperty(
#       name="Merge Identical Lods",
#       description = "Merge identical LODs in target file",
#       default = True)
#    keepTemporary = bpy.props.BoolProperty(
#       name="Keep BiTXT file",
#       description = "Keep the temporary BiTXT file (do not delete it)",
#       default = False)
#
#    filename_ext = ".p3d"
#   
#    def execute(self, context):
#        try:
#            # Generate a temporary file name for the bitxt file
#            bitxtName = self.filepath + ".bitxt"
#            bictrlName = self.filepath + ".ctrl"
#            # Open the file and export 
#            file = open(bitxtName, "w")
#            ctrlFile = open(bictrlName, "w")
#            uvsetFile = open(bitxtName + ".uvset", "w")
#            hasUVSets = exportBITxt(file, ctrlFile, uvsetFile, self.selectionOnly, self.mergeLods)
#            file.close()
#            ctrlFile.close()
#            uvsetFile.close()
#            # Run O2Script to output the P3D
#            params = "-q -w -a " + O2Script + " \"" + bitxtName + "\" \"" + self.filepath + "\" \"" + bictrlName + "\"";
#            if hasUVSets:
#                params = params + " \"" + bitxtName + ".uvset\""
#            
#            command = os.path.join(context.window_manager.armatoolbox.o2path, "O2Script.exe") 
#            command = '"' + command +'" ' + params
#            print("command = " + command)
#            call (command, shell=True)
#            
#            # Delete the text file
#            if self.keepTemporary == False:
#                os.remove(bitxtName)
#               os.remove(bictrlName)
#                os.remove(bitxtName + ".uvset")
#        except Exception as e:
#            self.report({'WARNING', 'INFO'}, "I/O error: {0}".format(e))
#            
#        return{'FINISHED'}
        
class ArmaToolboxExport(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname="armatoolbox.export"
    bl_label = "Export as P3D"
    bl_description = "Export as P3D"
    
    filter_glob = bpy.props.StringProperty(
        default="*.p3d",
        options={'HIDDEN'})
    
    selectionOnly = bpy.props.BoolProperty(
       name = "Selection Only", 
       description = "Export selected objects only", 
       default = False)

    filename_ext = ".p3d"
    
    def execute(self, context):
        if bpy.context.scene.objects.active == None:
            bpy.context.scene.objects.active = bpy.data.objects[0]
            
        #try:
        # Open the file and export 
        filePtr = open(self.filepath, "wb")
        exportMDL(filePtr, self.selectionOnly);
        filePtr.close()
        
        # Write a temporary O2script file for this
        filePtr = tempfile.NamedTemporaryFile("w", delete=False)
        tmpName = filePtr.name
        filePtr.write("p3d = newLodObject;\n")
        filePtr.write('_res = p3d loadP3D "%s";\n' % (self.filepath))
        filePtr.write("_res = p3d setActive 4e13;")
        filePtr.write('save p3d;\n')
        filePtr.close()
        
        # Run O2Script to output the P3D
        #command = os.path.join(context.window_manager.armatoolbox.o2path, "O2Script.exe")
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__name__].preferences
        command = addon_prefs.o2ScriptProp
        command = '"' + command +'" "' + tmpName + '"'
        #print("command (before abspath) = " + command)
        #command = os.path.abspath(command)
        print("command = " + command)
        call (command, shell=True)
        os.remove(tmpName)
        #except Exception as e:
        #    self.report({'WARNING', 'INFO'}, "I/O error: {0}".format(e))
            
        return{'FINISHED'}
        
        
class ArmaToolboxASCExport(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname="armatoolbox.ascexport"
    bl_label = "Export as ASC"
    bl_description = "Export as ASC"
    
    filter_glob = bpy.props.StringProperty(
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
        
class ArmaToolboxImport(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname="armatoolbox.import"
    bl_label = "Import P3D"
    bl_description = "Import P3D"
    
    filter_glob = bpy.props.StringProperty(
        default="*.p3d",
        options={'HIDDEN'})

    layeredLods = bpy.props.BoolProperty(
       name="Try to put each LOD on its own layer",
       description = "Tried to put each LOD imported on a separate layer, provided there aren't more than 20",
       default = True)
#    keepTemporary = bpy.props.BoolProperty(
#       name="Keep BiTXT file",
#       description = "Keep the temporary BiTXT file (do not delete it)",
#       default = False)

    filename_ext = ".p3d"

    def execute (self, context):
        error = -2
        try:
            error = importMDL(context, self.filepath, self.layeredLods)
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


class ArmaToolboxASCImport(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    bl_idname="armatoolbox.importasc"
    bl_label = "Import ASC"
    bl_description = "Import ASC"
    
    filter_glob = bpy.props.StringProperty(
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
        
###
##   Save Settings Operator
#

#class ArmaToolboxSaveSettings(bpy.types.Operator):
#    bl_idname = "armatoolbox.savesettings"
#    bl_label = "Save Arma Toolbox settings"
#    
#    def execute(self, context):
#        at = context.window_manager.armatoolbox
#        try:
#            saveO2Path(at)
#        except Exception as e:
#            self.report({'WARNING', 'INFO'}, "I/O error: {0}".format(e))
#            
#        return{'FINISHED'}

def ArmaToolboxExportMenuFunc(self, context):
    self.layout.operator(ArmaToolboxExport.bl_idname, text="Arma 2/3 P3D (.p3d)")

def ArmaToolboxImportMenuFunc(self, context):
    self.layout.operator(ArmaToolboxImport.bl_idname, text="Arma 2/3 P3D (.p3d)")

def ArmaToolboxImportASCMenuFunc(self, context):
    self.layout.operator(ArmaToolboxASCImport.bl_idname, text="Arma 2/3 ASC DEM File (.asc)")

def ArmaToolboxExportASCMenuFunc(self, context):
    self.layout.operator(ArmaToolboxASCExport.bl_idname, text="Arma 2/3 ASC DEM File (.asc)")

def addCustomProperties():
    try:
        if bpy.types.Material.armaMatProps:
            pass
    except:
        bpy.types.Material.armaMatProps = bpy.props.PointerProperty(
            type=ArmaToolboxMaterialProperties,
            description = "Arma Toolbox Properties")  

    try:
        if bpy.types.Object.armaObjProps:
            pass
    except:
        bpy.types.Object.armaObjProps = bpy.props.PointerProperty(
            type = ArmaToolboxProperties,
            description = "Arma Toolbox Properties")

    try:
        if bpy.types.Object.armaHFProps:
            pass
    except:
        bpy.types.Object.armaHFProps = bpy.props.PointerProperty(
            type = ArmaToolboxHeightfieldProperties,
            description = "Arma Toolbox Heightfield Properties")

    try:
        if bpy.types.WindowManager.armaGUIProps:
            pass
    except:
        bpy.types.WindowManager.armaGUIProps = bpy.props.PointerProperty(
            type = ArmaToolboxGUIProps,
            description="Arma Toolbox GUI settings")


def addProxy():
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

def ArmaToolboxExportRTMMenuFunc(self, context):
    self.layout.operator(ArmaToolboxExportRTM.bl_idname, text="Arma 2/3 .RTM Animation")


class ArmaToolboxBulkRename(bpy.types.Operator):
    bl_idname = "armatoolbox.bulkrename"
    bl_label = "Bulk Rename Arma material paths"
    
    
    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        if guiProps.renamableListIndex > -1 and guiProps.renamableList.__len__() > guiProps.renamableListIndex:
            frm = guiProps.renamableList[guiProps.renamableListIndex].name
            t   = guiProps.renameTo 
            bulkRename(context, frm, t)
        return {'FINISHED'}
    
class ArmaToolboxCreateComponents(bpy.types.Operator):
    bl_idname = "armatoolbox.createcomponents"
    bl_label = "Create Geometry Components"

    
    def execute(self, context):
        createComponents(context)
        return {'FINISHED'}

class ArmaToolboxBulkReparent(bpy.types.Operator):
    bl_idname = "armatoolbox.bulkreparent"
    bl_label = "Bulk Re-parent Arma material paths"

    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        frm = guiProps.parentFrom
        t   = guiProps.parentTo
        bulkReparent(context, frm, t)
        return {'FINISHED'}

class ArmaToolboxSelectionRename(bpy.types.Operator):
    bl_idname = "armatoolbox.bulkrenameselection"
    bl_label = "Bulk Re-parent Arma material paths"

    
    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        frm = guiProps.renameSelectionFrom
        t   = guiProps.renameSelectionTo
        bulkRenameSelections(context, frm, t)
        return {'FINISHED'}      

class ArmaToolboxHitpointCreator(bpy.types.Operator):
    bl_idname = "armatoolbox.hitpointcreator"
    bl_label = "Create Hitpoint Volume"
    
    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        selection = guiProps.hpCreatorSelectionName
        radius = guiProps.hpCreatorRadius
        hitpointCreator(context, selection, radius)
        return {'FINISHED'}

class ArmaToolboxSelectionTranslator(bpy.types.Operator):
    bl_idname = "armatoolbox.autotranslate"
    bl_label = "Attempt to automatically translate Czech selection names"

    def execute(self, context):
        autotranslateSelections()
        return {'FINISHED'}

class ArmaToolboxSelectWeightVertex(bpy.types.Operator):
    bl_idname = "armatoolbox.selweights"
    bl_label = "Select vertices with more than 4 bones weights"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'  
    
    def execute(self, context):
        selectOverweightVertices()
        return {'FINISHED'}

class ArmaToolboxPruneWeightVertex(bpy.types.Operator):
    bl_idname = "armatoolbox.pruneweights"
    bl_label = "Prune vertices with more than 4 bones weights"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'  
    
    def execute(self, context):
        pruneOverweightVertices()
        return {'FINISHED'}

class ArmaToolboxRVMatRelocator(bpy.types.Operator):
    bl_idname = "armatoolbox.rvmatrelocator"
    bl_label = "Relocate RVMat"
    
    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        rvfile = guiProps.rvmatRelocFile
        rvout  = guiProps.rvmatOutputFolder
        prefixPath = guiProps.matPrefixFolder
        rt_CopyRVMat(rvfile, rvout, prefixPath)
        return {'FINISHED'}
 
class ArmaToolBoxToolPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    #bl_context = "objectmode"
    bl_label = "Arma Tools"
    bl_category = "Arma"
    bl_options = {'DEFAULT_CLOSED'}
    
    lastId = -1
    
    def safeAddRenamable(self, name, prop):
        if len(name) == 0: 
            return None
       
        for p in prop:
            if p.name == name:
                return None
        
        item = prop.add()
        item.name = name
        return item 
 
    def fillList(self, guiProps):
        # Fill the renamable list
        guiProps.renamableList.clear()
            
        mats = bpy.data.materials
            
        for mat in mats:
            self.safeAddRenamable(mat.armaMatProps.texture, guiProps.renamableList)
            self.safeAddRenamable(mat.armaMatProps.rvMat, guiProps.renamableList)
            self.safeAddRenamable(mat.armaMatProps.colorString, guiProps.renamableList)
 
    def draw(self, context):
        layout = self.layout
        guiProps = context.window_manager.armaGUIProps
        col = layout.column(align=True)
        
        # Bulk Renamer
        split = col.split(percentage=0.15)
        if guiProps.bulkRenamePanelOpen:
            split.prop(guiProps, "bulkRenamePanelOpen", text="", icon='DOWNARROW_HLT')
        else:
            split.prop(guiProps, "bulkRenamePanelOpen", text="", icon='RIGHTARROW')
        split.operator("armatoolbox.bulkrename", "Path Rename")
        
        # Bulk Renamer Settings
        if guiProps.bulkRenamePanelOpen:
            box = col.column(align=True).box().column()
            row = box.row()
            
            self.fillList(guiProps)
             
            row.template_list(listtype_name = "ArmaToolboxNamedPropList", 
                              dataptr = guiProps,
                              propname = "renamableList",
                              active_dataptr = guiProps,
                              active_propname="renamableListIndex")
            
            
            if guiProps.renamableListIndex > -1 and guiProps.renamableList.__len__() > guiProps.renamableListIndex:
                guiProps.renameFrom = guiProps.renamableList[guiProps.renamableListIndex].name
                row = box.row()
                row.prop(guiProps, "renameFrom", "Rename From")
                row = box.row()
                row.prop(guiProps, "renameTo", "To")
            else:
                row = box.row()
                row.label("Rename From")
                row = box.row()
                row.label("To")
        
        # Bulk Renamer
        row = layout.row()
        col = row.column(align=True)
        split = col.split(percentage=0.15)
        if guiProps.bulkReparentPanelOpen:
            split.prop(guiProps, "bulkReparentPanelOpen", text="", icon='DOWNARROW_HLT')
        else:
            split.prop(guiProps, "bulkReparentPanelOpen", text="", icon='RIGHTARROW')
        split.operator("armatoolbox.bulkreparent", "Change File Parent")
      
        # Bulk Reparent Settings
        if guiProps.bulkReparentPanelOpen:
            box = col.column(align=True).box().column()
            row = box.row()
            row = box.row()
            row.prop(guiProps, "parentFrom", "Change Parent From")
            row = box.row()
            row.prop(guiProps, "parentTo", "To")
            
        # Selection Renamer
        row = layout.row()
        col = row.column(align=True)
        split = col.split(percentage=0.15)
        if guiProps.selectionRenamePanelOpen:
            split.prop(guiProps, "selectionRenamePanelOpen", text="", icon='DOWNARROW_HLT')
        else:
            split.prop(guiProps, "selectionRenamePanelOpen", text="", icon='RIGHTARROW')
        split.operator("armatoolbox.bulkrenameselection", "Rename selections / vertex groups")
        
        # Selection Renamer settings    
        if guiProps.selectionRenamePanelOpen:
            box = col.column(align=True).box().column()
            row = box.row()
            row = box.row()
            row.prop(guiProps, "renameSelectionFrom", "Rename Selection From")
            row = box.row()
            row.prop(guiProps, "renameSelectionTo", "To")   
        
        # Hitpoint Creator
        row = layout.row()
        col = row.column(align=True)
        split = col.split(percentage=0.15)
        if guiProps.hitpointCreatorPanelOpen:
            split.prop(guiProps, "hitpointCreatorPanelOpen", text="", icon='DOWNARROW_HLT')
        else:
            split.prop(guiProps, "hitpointCreatorPanelOpen", text="", icon='RIGHTARROW')
        split.operator("armatoolbox.hitpointcreator", "Create Hitpoint Cloud")
        
        # Hitpoint Creator Settings
        if guiProps.hitpointCreatorPanelOpen:
            box = col.column(align=True).box().column()
            row = box.row()
            row = box.row()
            row.prop(guiProps, "hpCreatorSelectionName", "Selection Name")
            row = box.row()
            row.prop(guiProps, "hpCreatorRadius", "Sphere Radius") 
          
        # Component Creator
        row = layout.row()
        row.operator("armatoolbox.createcomponents", "Create Geometry Components")
        
class ArmaToolBoxWeightToolPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    #bl_context = "objectmode"
    bl_label = "Arma Weight Tools"
    bl_category = "Arma"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        row = layout.row()
        row.operator("armatoolbox.selweights", text = "Problematic Weighted Vertices")
        row = layout.row()
        row.operator("armatoolbox.pruneweights", text = "Prune weights to 4 bones max")
        

class ArmaToolBoxRelocationToolPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    #bl_context = "objectmode"
    bl_label = "Arma Relocation Tools"
    bl_category = "Arma"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        guiProps = context.window_manager.armaGUIProps

        layout.operator("armatoolbox.rvmatrelocator", text = "Relocate external RVMat")
        layout.prop(guiProps, "rvmatRelocFile", "Relocate RVMat")
        layout.prop(guiProps, "rvmatOutputFolder", "Output Folder")
        layout.prop(guiProps, "matPrefixFolder", "Search Prefix")
        layout.separator()

class ArmaToolboxMaterialRelocator(bpy.types.Operator):
    bl_idname = "armatoolbox.materialrelocator"
    bl_label = "Relocate Material"
    
    material = bpy.props.StringProperty()
    texture = bpy.props.StringProperty()
    
    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps

        outputPath = guiProps.matOutputFolder
        if len(outputPath) is 0:
            self.report({'ERROR_INVALID_INPUT'}, "Output folder name missing")
        
        prefixPath = guiProps.matPrefixFolder
        if len(prefixPath) == 0:
            prefixPath = "P:\\"
        
        materialName = self.material
        textureName = self.texture
        mt_RelocateMaterial(textureName, materialName, outputPath, guiProps.matAutoHandleRV, prefixPath)

        return {'FINISHED'}

class ArmaToolBoxMaterialRelocationPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Arma Material Relocation"
    bl_category = "Arma"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        guiProps = context.window_manager.armaGUIProps
        layout.prop(guiProps, "matOutputFolder", "Output Folder")
        layout.prop(guiProps, "matPrefixFolder", "Search Prefix")
        layout.prop(guiProps, "matAutoHandleRV", "Automatically translate RVMat")
        data = bpy.data
        materials = data.materials
        
        texNames = []
        matNames = []
        
        for mat in materials:
            matName, texName = mt_getMaterialInfo(mat)
            if len(texName) > 0 and texName not in texNames and texName[0] is not "#":
                texNames.append(texName)
            if len(matName)> 0 and matName not in matNames:
                matNames.append(matName)
            
        for tex in texNames:
            box = layout.box()
            row = box.row()
            row.label(tex)
            p = row.operator("armatoolbox.materialrelocator", "Relocate")
            p.texture = tex
            p.material = ""
            
        for mat in matNames:    
            box = layout.box()
            row = box.row()
            row.label(mat)
            p = row.operator("armatoolbox.materialrelocator", "Relocate")
            p.texture = ""
            p.material = mat
        
            
# Proxies
# The more I use it, the more I get to the conclusion that I hate Python,
# and I hate the Blender API, and especially the shitty UI. Seriously, guys, it's 2014.
class ArmaToolboxAddNewProxy(bpy.types.Operator):
    bl_idname = "armatoolbox.addnewproxy"
    bl_label = ""
    bl_description = "Add a proxy"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode="EDIT")
        obj = context.active_object
        mesh = obj.data
        
        cursor_location = bpy.context.scene.cursor_location
        cursor_location = cursor_location - obj.location

        bm = bmesh.from_edit_mesh(mesh)

        i = len(bm.verts)
        v1 = bm.verts.new(cursor_location + Vector((0,0,0)))
        v2 = bm.verts.new(cursor_location + Vector((0,0,2)))
        v3 = bm.verts.new(cursor_location + Vector((0,1,0)))
        
        f = bm.faces.new((v1,v2,v3))
        print (v1.index)  
        bpy.ops.object.mode_set(mode="OBJECT")

        #bm.to_mesh(mesh)
        #mesh.update()
              
        vgrp = obj.vertex_groups.new("@@armaproxy")
        vgrp.add([i+0],1,'ADD')
        vgrp.add([i+1],1,'ADD')
        vgrp.add([i+2],1,'ADD')
            
        bpy.ops.object.mode_set(mode="EDIT")
        
        p = obj.armaObjProps.proxyArray.add()
        p.name = vgrp.name
        
        
        return {"FINISHED"}    

# This does two things. First, it goes through the model checking if the
# proxies in the list are still in the model, and delete all that arent.
#
# Secondly, it looks for "standard" proxy definition like "proxy:xxxx.001" and
# converts them into new proxies.
class ArmaToolboxAddSyncProxies(bpy.types.Operator):
    bl_idname = "armatoolbox.syncproxies"
    bl_label = ""
    bl_description = "Synchronize the proxy list with the model"
    
    def execute(self, context):
        obj = context.active_object
        prp = obj.armaObjProps.proxyArray

        # Gp through our proxy list
        delList = []
        max = prp.values().__len__()
        for i in range(0,max):
            if prp[i].name not in obj.vertex_groups.keys():
                delList.append(i)
        if len(delList) > 0:
            delList.reverse()
            for item in delList:
                prp.remove(item)
        
        # Go through the vertex groups
        for grp in obj.vertex_groups:
            if len(grp.name) > 5:
                if grp.name[:6] == "proxy:":
                    prx = grp.name.split(":")[1]
                    if prx.find(".") != -1:
                        a = prx.split(".")
                        prx = a[0]
                        idx = a[1]
                    else:
                        idx = "1"
                    n = prp.add()
                    n.name = grp.name
                    n.index = int(idx)
                    n.path = "P:" + prx
                    
                
        return {"FINISHED"}         

class ArmaToolboxAddToggleProxies(bpy.types.Operator):
    bl_idname = "armatoolbox.toggleproxies"
    bl_label = ""
    bl_description = "Toggle GUI visibilityl"
    
    prop = bpy.props.StringProperty()
    
    def execute(self, context):
        obj = context.active_object
        prop = obj.armaObjProps.proxyArray[self.prop]
        if prop.open == True:
            prop.open = False
        else:
            prop.open = True  
        return {"FINISHED"}     

class ArmaToolboxCopyHelper(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="name", 
        description = "Object Name")
    doCopy = bpy.props.BoolProperty(name="doCopy",
        description="Do copy Value") 

class ArmaToolboxCopyProxy(bpy.types.Operator):
    bl_idname = "armatoolbox.copyproxy"
    bl_label = ""
    bl_description = "Copy proxy to other LOD's"    

    objectArray = bpy.props.CollectionProperty(type=ArmaToolboxCopyHelper)
    copyProxyName = bpy.props.StringProperty()
    encloseInto = bpy.props.StringProperty(description="Enclose the proxy in a selection. Leave blank to not create any extra selection")

    def execute(self, context):
        sObj = context.active_object
        for obj in self.objectArray:
            if obj.doCopy:
                enclose = self.encloseInto
                enclose = enclose.strip()
                if len(enclose) == 0:
                    enclose = None
                
                CopyProxy(sObj, bpy.data.objects[obj.name], self.copyProxyName, enclose)

        self.objectArray.clear()
        return {"FINISHED"}
   
    def invoke(self, context, event):
        
        for obj in bpy.data.objects.values():
            if obj.armaObjProps.isArmaObject == True and obj != context.active_object:
                prop = self.objectArray.add()
                prop.name  = obj.name
                prop.doCopy = True
        
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="Copy Proxy!")
        for s in self.objectArray:
            row = layout.row()
            row.prop(s, "doCopy", text=s.name)
        row = layout.row()
        row.prop(self, "encloseInto", text="Enclose in:")

class ArmaToolboxDeleteProxy(bpy.types.Operator):
    bl_idname = "armatoolbox.deleteproxy"
    bl_label = ""
    bl_description = "Delete given proxy"  
    
    proxyName = bpy.props.StringProperty()
    
    @classmethod
    def poll(self, context):
        if context.active_object.mode == 'OBJECT':
            return True
        else:
            return False
    
    def execute(self, context):
        sObj = context.active_object
        mesh = sObj.data

        idxList = []

        grp = sObj.vertex_groups[self.proxyName]
        for v in mesh.vertices:
            for g in v.groups:
                if g.group == grp.index:
                    if g.weight > 0:
                        idxList.append(v.index)
                        
        if len(idxList) > 0:
            bm = bmesh.new()
            bm.from_mesh(mesh)
            if hasattr(bm.verts, "ensure_lookup_table"): 
                bm.verts.ensure_lookup_table()
            
            vList = []
            for i in idxList:
                vList.append(bm.verts[i])
            
            for v in vList:
                bm.verts.remove(v)
        
            bm.to_mesh(mesh)
            bm.free()
            mesh.update()
            
        sObj.vertex_groups.remove(grp)
        prp = sObj.armaObjProps.proxyArray
        for i,pa in enumerate(prp):
            if pa.name == self.proxyName:
                prp.remove(i)
            
            
        return {"FINISHED"}
    
class ArmaToolboxProxyPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Proxies"
    bl_category = "Arma"
    
    @classmethod
    def poll(cls, context):
        ## Visible when there is a selected object, it is a mesh
        obj = context.active_object
       
        return (obj 
            and obj.select == True
            and obj.armaObjProps.isArmaObject == True
            and (obj.type == "MESH" or obj.type == "ARMATURE") )

    def draw(self, context):
        obj = context.active_object
        layout = self.layout
        row = layout.row()
        row.operator("armatoolbox.addnewproxy", "Add Proxy")
        row.operator("armatoolbox.syncproxies", "Sync with model")
        
        for prox in obj.armaObjProps.proxyArray:
            box = layout.box()
            row = box.row()
            if prox.open == True:
                toggle = row.operator("armatoolbox.toggleproxies", icon="TRIA_DOWN", emboss=False)
                toggle.prop = prox.name
                row.label(prox.name)
            else:
                toggle = row.operator("armatoolbox.toggleproxies", icon="TRIA_RIGHT", emboss=False)
                name = Path.basename(prox.path)
                toggle.prop = prox.name
                iconName = "NONE"
                if name.upper() == "DRIVER" or name.upper() == "COMMANDER" or name.upper() == "GUNNER":
                    iconName="GHOST_ENABLED"
                if name[:5].upper() == "CARGO":
                    iconName="GHOST_ENABLED" 
                row.label(name, icon=iconName)
            
            
            if prox.open:
                # For later
                ##row.operator("armatoolbox.deleteproxy", "", icon="X")
                ##row.operator("armatoolbox.selectproxy", "", icon="VIEWZOOM")
                copyOp = row.operator("armatoolbox.copyproxy", "", icon="PASTEDOWN", emboss=False)
                copyOp.copyProxyName = prox.name
                delOp = row.operator("armatoolbox.deleteproxy", "", icon="X", emboss=False)
                delOp.proxyName = prox.name
                row = box.row()
                row.prop(prox, "path", "Path")
                row = box.row()
                row.prop(prox, "index", "Index")
            else:
                delOp = row.operator("armatoolbox.deleteproxy", "", icon="X", emboss=False)
                delOp.proxyName = prox.name
                
        row = layout.row()
        row.operator("armatoolbox.addnewproxy", "Add Proxy")
        row.operator("armatoolbox.syncproxies", "Sync with model")
#########################################################
# Proxy Tools Panel and associated operators

class ArmaToolboxToggleGUIProp(bpy.types.Operator):
    bl_idname = "armatoolbox.toggleguiprop"
    bl_label = ""
    bl_description = "Toggle GUI visibilityl"
    
    prop = bpy.props.StringProperty()
        
    def execute(self, context):
        prop = context.window_manager.armaGUIProps
        if prop.is_property_set(self.prop) == True and prop[self.prop] == True:
            prop[self.prop] = False
        else:
            prop[self.prop] = True  
        return {"FINISHED"}   


class ArmaToolboxJoinAsProxy(bpy.types.Operator):
    bl_idname = "armatoolbox.joinasproxy"
    bl_label = ""
    bl_description = "Join as Proxy"
    
    @classmethod
    def poll(cls, context):
        ## Visible when there is a selected object, it is a mesh
        obj = context.active_object
       
        return (obj 
            and obj.select == True
            and obj.armaObjProps.isArmaObject == True
            and obj.type == "MESH" 
            and len(bpy.context.selected_objects) > 1
            )
        
    def execute(self, context):
        obj = context.active_object
        selected = bpy.selection
        
        path =  context.window_manager.armaGUIProps.mapProxyObject
        index = context.window_manager.armaGUIProps.mapProxyIndex
        doDel = context.window_manager.armaGUIProps.mapProxyDelete
        
        enclose = context.window_manager.armaGUIProps.mapProxyEnclose
        if len(enclose) == 0:
            enclose = None
        
        for sel in selected:
            if sel == obj:
                pass
            else:
                if enclose == None:
                    e = None
                else:
                    e = enclose + str(index)
                pos = sel.location - obj.location 
                CreateProxyPos(obj, pos, path, index, e)
                index = index + 1
        
        if doDel == True:
            obj.select = False
            bpy.ops.object.delete();
                    
                
        
        return {"FINISHED"}   

def createToggleBox(context, layout, propName, label, openOp = None):
    box = layout.box()
    row = box.row()
    guiProp = context.window_manager.armaGUIProps
    
    if guiProp.is_property_set(propName) == True and guiProp[propName] == True:
        toggle = row.operator("armatoolbox.toggleguiprop", icon="TRIA_DOWN", emboss=False)
        toggle.prop = propName
        if openOp == None:
            row.label(label)
        else:
            row.operator(openOp, text = label)
    else:
        toggle = row.operator("armatoolbox.toggleguiprop", icon="TRIA_RIGHT", emboss=False)
        toggle.prop = propName
        row.label(label)
        
    return box

class ArmaToolboxProxyToolsPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Proxy Tools"
    bl_category = "Arma"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        obj = context.active_object
        guiProp = context.window_manager.armaGUIProps
        layout = self.layout
        row = layout.row()
        box = createToggleBox(context, row, "mapOpen", "Join as Proxy", "armatoolbox.joinasproxy")
        if guiProp.mapOpen == True:
            row = box.row()
            row.prop(guiProp, "mapProxyObject", text="Path")
            row = box.row()
            row.prop(guiProp, "mapProxyIndex",  text="Index")
            row = box.row()
            row.prop(guiProp, "mapProxyDelete", text="Delete source objects")
            row = box.row()
            bx = row.box()
            bx.label("Enclose in selection")
            bx.prop(guiProp, "mapProxyEnclose", text="(Empty for none)")
                
      
      
      
      
###################################
# This code is from BlenderNation
def select():
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

###
##  Proxy Path Changer
#
#   Code contributed by Cowcancry

class ArmaToolboxProxyPathChanger(bpy.types.Operator):
    bl_idname = "armatoolbox.proxypathchanger"
    bl_label = "Proxy Path Change"
    
    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        pathFrom = guiProps.proxyPathFrom
        pathTo = guiProps.proxyPathTo
        #print(pathFrom)
        #print(pathTo)
        for obj in bpy.data.objects.values():
            if (obj 
            and obj.armaObjProps.isArmaObject == True
            and obj.type == "MESH"):
                for proxy in obj.armaObjProps.proxyArray:
                    proxy.path = proxy.path.replace(pathFrom, pathTo)
        return {'FINISHED'}

class ArmaToolBoxMassProxyPathChangePanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    #bl_context = "objectmode"
    bl_label = "Arma Proxy Path Change"
    bl_category = "Arma"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        guiProps = context.window_manager.armaGUIProps

        layout.operator("armatoolbox.proxypathchanger", text = "Proxy Path Change")
        layout.prop(guiProps, "proxyPathFrom", "Proxy path from")
        layout.prop(guiProps, "proxyPathTo", "Proxy path to")
        layout.separator()

###
##   Mass Tools
#

class ArmaToolboxSetMass(bpy.types.Operator):
    bl_idname = "armatoolbox.setmass"
    bl_label = ""
    bl_description = "Set the same mass for all selected vertices"
    
    @classmethod
    def poll(cls, context):
        ## Visible when there is a selected object, it is a mesh
        obj = context.active_object
        return (obj
            and obj.select == True
            and obj.armaObjProps.isArmaObject == True
            and obj.type == "MESH" 
            and (obj.armaObjProps.lod == '1.000e+13' or obj.armaObjProps.lod == '4.000e+13')
            and obj.mode == 'EDIT'
            ) 
        
    def execute(self, context):
        obj = context.active_object
        selected = bpy.selection
               
        mass = context.window_manager.armaGUIProps.vertexWeight

        setVertexMass(obj, mass)
        return {"FINISHED"}   

class ArmaToolboxDistributeMass(bpy.types.Operator):
    bl_idname = "armatoolbox.distmass"
    bl_label = ""
    bl_description = "Distribute the given mass equally to all selected vertices"
    
    @classmethod
    def poll(cls, context):
        ## Visible when there is a selected object, it is a mesh
        obj = context.active_object
        return (obj
            and obj.select == True
            and obj.armaObjProps.isArmaObject == True
            and obj.type == "MESH" 
            and (obj.armaObjProps.lod == '1.000e+13' or obj.armaObjProps.lod == '4.000e+13')
            and obj.mode == 'EDIT'
            ) 
        
    def execute(self, context):
        obj = context.active_object
        selected = bpy.selection
               
        mass = context.window_manager.armaGUIProps.vertexWeight

        distributeVertexMass(obj, mass)
        return {"FINISHED"} 

class ArmaToolboxMassToolsPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Mass Tools"
    bl_category = "Arma"
    
    @classmethod
    def poll(cls, context):
        ## Visible when there is a selected object, it is a mesh
        obj = context.active_object
        
        return (obj
            and obj.select == True
            and obj.armaObjProps.isArmaObject == True
            and obj.type == "MESH" 
            and (obj.armaObjProps.lod == '1.000e+13' or obj.armaObjProps.lod == '4.000e+13')
            and obj.mode == 'EDIT'
            )  
        
    def draw(self, context):
        obj = context.active_object
        guiProp = context.window_manager.armaGUIProps
        layout = self.layout
        row = layout.row()

        guiProps = context.window_manager.armaGUIProps
                
        row = layout.row()
        row.prop(guiProps, "vertexWeight", "Weight To Set")
        layout.operator("armatoolbox.setmass", text = "Set Mass on selected")
        layout.operator("armatoolbox.distmass", text = "Distribute Mass to selected")


###
##   Load Handler - check if there are things that need fixing in a loaded scene
#

# Fix shadow volumes
class ArmaToolboxFixShadowsHelper(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name="name", 
        description = "Object Name")
    fixThis = bpy.props.BoolProperty(name="fixThis",
        description="Fix") 

class ArmaToolboxFixShadows(bpy.types.Operator):
    bl_idname = "armatoolbox.fixshadows"
    bl_label = "Items to fix"
    bl_description = "Fix Shadow volumes resolutions"
    
    objectArray = bpy.props.CollectionProperty(type=ArmaToolboxFixShadowsHelper)
    
    def execute(self, context):
        for prop in self.objectArray:
            obj = bpy.data.objects[prop.name]

            lod = obj.armaObjProps.lod
            res = obj.armaObjProps.lodDistance
            
            print (obj.name, " " , lod , " " , res)
            
            if lod == "1.000e+4":
                if res == 0:
                    obj.armaObjProps.lodDistance = 1.0
            elif lod == "1.001e+4":
                print("Stencil 2")
                obj.armaObjProps.lod = "1.000e+4"
                obj.armaObjProps.lodDistance = 10.0
            elif lod == "1.100e+4":
                if res == 0:
                    obj.armaObjProps.lodDistance = 1.0
            elif lod == "1.101e+4":
                obj.armaObjProps.lod = "1.100e+4"
                obj.armaObjProps.lodDistance = 10.0
            
        self.objectArray.clear()
        return {"FINISHED"}

    def invoke(self, context, event):
        self.objectArray.clear()
        objs = getLodsToFix()
        for o in objs:
            prop = self.objectArray.add()
            prop.name = o.name
            prop.fixThis = True
            
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(icon="MODIFIER", text="The following objects have shadow volume issues")
        col = layout.column()

        for s in self.objectArray:
            row = layout.row()
            row.prop(s, "fixThis", text=s.name)
        
        row = layout.row()
        row.label ("Click 'OK' to fix")

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
        if lod == '1.000e+13' or lod == '4.000e+13':
            attemptFixMassLod (o)
        
        
@persistent
def load_handler(dummy):
    if bpy.data.filepath == "":
        return
    
    print("Load Hook:", bpy.data.filepath)
    
    # Fix old Mass LODs
    fixMassLods()
    
    # Fix Shadows
    objects = getLodsToFix()       
    if len(objects) > 0:
        bpy.ops.armaToolbox.fixshadows('INVOKE_DEFAULT')
            
###
##  Registration
#            
def register():
    
    bpy.utils.register_module(__name__, verbose=True)
    #bpy.utils.register_class(ArmaToolboxPreferences)
    bpy.utils.register_class(ArmaToolboxSelectionMaker)
    bpy.types.INFO_MT_file_export.append(ArmaToolboxExportMenuFunc)
    bpy.types.INFO_MT_file_import.append(ArmaToolboxImportMenuFunc)
    bpy.types.INFO_MT_file_import.append(ArmaToolboxImportASCMenuFunc)
    bpy.types.INFO_MT_file_export.append(ArmaToolboxExportASCMenuFunc)
    #bpy.utils.register_class(ArmaToolboxAddNewProxy)
    bpy.types.INFO_MT_mesh_add.append(ArmaToolboxAddProxyMenuFunc)
    bpy.types.INFO_MT_file_export.append(ArmaToolboxExportRTMMenuFunc)
    
    addCustomProperties()
#    bpy.types.WindowManager.armatoolbox = bpy.props.PointerProperty(
#        type = ArmaToolboxSettingsProperties)    
    
    if load_handler not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(load_handler)
    bpy.types.DATA_PT_vertex_groups.append(vgroupExtra)
    print("Register done")
    
def unregister():
    print("Unregister")
    bpy.types.DATA_PT_vertex_groups.remove(vgroupExtra)
    try:
        del bpy.types.WindowManager.armatoolbox
    except:
        pass
    bpy.types.INFO_MT_file_export.remove(ArmaToolboxExportMenuFunc)
    bpy.types.INFO_MT_file_import.remove(ArmaToolboxImportMenuFunc)
    bpy.types.INFO_MT_file_import.remove(ArmaToolboxImportASCMenuFunc)
    bpy.types.INFO_MT_file_export.remove(ArmaToolboxExportASCMenuFunc)
    #bpy.utils.unregister_class(ArmaToolboxAddNewProxy)
    bpy.types.INFO_MT_mesh_add.remove(ArmaToolboxAddProxyMenuFunc)
    bpy.types.INFO_MT_file_export.remove(ArmaToolboxExportRTMMenuFunc)
    #bpy.utils.unregister_class(ArmaToolboxPreferences)
    bpy.utils.unregister_class(ArmaToolboxSelectionMaker)
    bpy.utils.unregister_module(__name__)
