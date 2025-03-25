# GPL 3.0

import bpy
from bpy.props import (    
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
#from NamedSelections import NamSel_UpdateName
from . import NamedSelections

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


###
##   Custom Property Collections
#
class ArmaToolboxNamedProperty(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(name="Name", 
        description = "Property Name")
    value : bpy.props.StringProperty(name="Value",
        description="Property Value") 

class ArmaToolboxNamedSelection(bpy.types.PropertyGroup):

    def get_name(self):
        return self.get("name", "Named Selection")

    def set_name(self, value):
        oldname = self.get("name")
        newname = NamSel_UpdateName(bpy.context.active_object, oldname, value)
        if newname == None: # UpdateName didn't change the name
            newname = value
        self["name"] = newname

    name: bpy.props.StringProperty(name="Name",
                                   description="Selection Name",
                                   set = set_name,
                                   get = get_name)

class ArmaToolboxKeyframeProperty(bpy.types.PropertyGroup):
    timeIndex : bpy.props.IntProperty(name="Frame Index",
        description="Frame Index for keyframe")

class ArmaToolboxComponentProperty(bpy.types.PropertyGroup):
    name   : bpy.props.StringProperty(name="name", description="Component name")
    weight : bpy.props.FloatProperty(name="weight", description="Weight of Component", default = 0.0)

# Would have preferred to have that in ArmaProxy, but apparently that doesn't work.
class ArmaToolboxProxyProperty(bpy.types.PropertyGroup):
    open   : bpy.props.BoolProperty(name="open", description="Show proxy data in GUI", default=False)
    name   : bpy.props.StringProperty(name="name", description="Proxy name")
    path   : bpy.props.StringProperty(name="path", description="File path", subtype="FILE_PATH")
    index  : bpy.props.IntProperty(name="index", description="Index of Proxy", default=1)

class ArmaToolboxHeightfieldProperties(bpy.types.PropertyGroup):
    isHeightfield : bpy.props.BoolProperty(
        name = "IsArmaHeightfield",
        description = "Is this an ARMA Heightfield object",
        default = False)
    cellSize : bpy.props.FloatProperty(
        name="cell size",
        description = "Size of a single cell in meters",
        default = 4.0)
    northing : bpy.props.FloatProperty(
        name="northing",
        description="Northing",
        default = 200000.0)
    easting : bpy.props.FloatProperty(
        name="easting",
        description = "Easting",
        default = 0)
    undefVal : bpy.props.FloatProperty(
        name="NODATA value",
        description = "Value for Heightfield holes",
        default=-9999)


class ArmaToolboxExportConfigObjectProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="name", description="Export Configs")


class ArmaToolboxCollectedMeshesProperty(bpy.types.PropertyGroup):
    object: bpy.props.PointerProperty(type = bpy.types.Object, name="object",
                                      description = "Object Name")


class ArmaToolboxDeletionListProperty(bpy.types.PropertyGroup):
    vname: bpy.props.StringProperty(name="vname", description="Group Name")

class ArmaToolboxProperties(bpy.types.PropertyGroup):
    isArmaObject : bpy.props.BoolProperty(
        name = "IsArmaObject",
        description = "Is this an ARMA exportable object",
        default = False)
    
    # Special Object
    isMeshCollector : bpy.props.BoolProperty(
        name = "IsMeshCollector",
        description = "Collect meshes from other objects",
        default = False
    )

    # Mesh Objects
    lod : bpy.props.EnumProperty(
        name="LOD Type",
        description="Type of LOD",
        items=lodPresets,
        default='-1.0')
    lodDistance : bpy.props.FloatProperty(
        name="Distance",
        description="Distance of Custom LOD",
        default=1.0)
    mass : bpy.props.FloatProperty(
        name="Mass",
        description="Object Mass",
        default=1.0)
    massArray : bpy.props.CollectionProperty(type = ArmaToolboxComponentProperty, description="Masses")

    namedProps : bpy.props.CollectionProperty(type = ArmaToolboxNamedProperty,
          description="Named Properties")
    namedPropIndex : bpy.props.IntProperty("namedPropIndex", default = -1)
    
    proxyArray : bpy.props.CollectionProperty(type = ArmaToolboxProxyProperty, description = "Proxies")
    
    # Armature
    keyFrames : bpy.props.CollectionProperty(type = ArmaToolboxKeyframeProperty,
          description="Keyframes")
    keyFramesIndex : bpy.props.IntProperty("keyFrameIndex", default = -1)
    motionVector : bpy.props.FloatVectorProperty(name = "RTM Motion Vector", 
         description = "Motion Vector written to the RTM Animation",
          subtype='TRANSLATION')
    centerBone : bpy.props.StringProperty(name="Center Of Animation", 
          description="The center of animation for calculating the motion vector")
    
    # model.cfg
    exportBone : bpy.props.StringProperty(name="Bone to export", 
          description="Export for model.cfg")
    selectionName : bpy.props.StringProperty(name="selection name", description="selection that is animated")
    animSource : bpy.props.StringProperty(name="Animation source", default="reloadMagazine", description="Name of the animation source")
    prefixString : bpy.props.StringProperty(name="Output Prefix String", default="", description="String to prefix output with")
    outputFile : bpy.props.StringProperty(
        name="Output File", 
        description="Output file for model.cfg inclusion", 
        subtype="FILE_PATH", 
        default="")

    # Export configs
    exportConfigs : bpy.props.CollectionProperty(type = ArmaToolboxExportConfigObjectProperty, description = "Export Configs")
    configIndex: bpy.props.IntProperty("configIndex", default=-1)
    alwaysExport : bpy.props.BoolProperty(name = "alwaysExport", default=False, description="If True, include this in all exports on a batch export")
    
    # Named Selections
    namedSelection : bpy.props.CollectionProperty(type = ArmaToolboxNamedSelection,
          description="Named Selection")
    namedSelectionIndex : bpy.props.IntProperty("namedSelectionIndex", default = -1)
    previousSelectionIndex: bpy.props.IntProperty(
        "previousSelectionIndex", default=-1)
    previousVertexGroupIndex: bpy.props.IntProperty(
        "previousVertexGroupIndex", default=-1
    )

    # Mesh Collector objects
    collectedMeshes : bpy.props.CollectionProperty(
        type = ArmaToolboxCollectedMeshesProperty,
        description = "Object Capture List")
    collectedMeshesIndex : bpy.props.IntProperty("collectedMeshesIndex", default = -1)
    collectedMeshesDelete : bpy.props.CollectionProperty(
        type = ArmaToolboxDeletionListProperty,
        description = "Object Capture List")
    collectedMeshesDeleteIndex : bpy.props.IntProperty("collectedMeshesDeleteIndex", default = -1)

    
class ArmaToolboxMaterialProperties(bpy.types.PropertyGroup):
    texture : bpy.props.StringProperty(
        name="Face Texture", 
        description="ARMA texture", 
        subtype="FILE_PATH", 
        default="")
    rvMat : bpy.props.StringProperty(
        name="RVMat Material", 
        description="RVMat associated with this materiaL", 
        subtype="FILE_PATH",
        default="")
    texType : bpy.props.EnumProperty(
        name="Color Map Type",
        description="The type/source of the color for this surface",
        items=textureClass)
    colorValue : bpy.props.FloatVectorProperty(
        name= "Color",
        description= "Color for procedural texture",
        subtype= 'COLOR',
        min= 0.0,
        max= 1.0,
        soft_min= 0.0,
        soft_max= 1.0,
        default= (1.0,1.0,1.0))
    colorType : bpy.props.EnumProperty(
        name="Color Type",
        description="The Type of color, corresponding to the suffix of a texture name",
        items = textureTypes)
    colorString : bpy.props.StringProperty (
        name = "Resulting String", 
        description = "Resulting value for the procedural texture")

class ArmaToolboxRenamableProperty(bpy.types.PropertyGroup):
    renamable : bpy.props.StringProperty(name="Texture Path")


def bex_add_defined_export_configs(self, context):
    items = []
    scene = context.scene
    for item in scene.armaExportConfigs.exportConfigs.values():
        items.append((item.name, item.name, ""))

    return items

class ArmaToolboxGUIProps(bpy.types.PropertyGroup):
    framePanelOpen : bpy.props.BoolProperty(name="Open Frames Settings Panel",
        description="Open or close the settings of the 'Add Frame Range' tool",
        default = False)
    framePanelStart : bpy.props.IntProperty(name="Start of frame range",
        description = "Start of the range of frames to add to the list",
        default = -1, min = 0)
    framePanelEnd : bpy.props.IntProperty(name="ENd of frame range",
        description = "End of the range of frames to add to the list",
        default = -1, min=1)
    framePanelStep : bpy.props.IntProperty(name="Step of frame range",
        description = "Step of the range of frames to add to the list",
        default = 5, min=1)

    bulkRenamePanelOpen : bpy.props.BoolProperty(name="Open Bulk Rename Settings Panel",
        description="Open or close the settings of the 'Bulk Rename' tool",
        default = False) 
    bulkReparentPanelOpen : bpy.props.BoolProperty(name="Open Bulk Reparent Settings Panel",
        description="Open or close the settings of the 'Bulk Reparent' tool",
        default = False) 
    selectionRenamePanelOpen : bpy.props.BoolProperty(name="Open Selection Renaming Settings Panel",
        description="Open or close the settings of the 'Bulk Reparent' tool",
        default = False) 
    rvmatRelocPanelOpen : bpy.props.BoolProperty(name="Open RVMat Relocation Settings Panel",
        description="Open or close the settings of the 'RVMat Relocator' tool",
        default = False) 
    
    hitpointCreatorPanelOpen : bpy.props.BoolProperty(name="Open hitpoint creator settings panel", 
        description="Open or close the 'Hitpoint Creator' tool",
        default = False)
    
    # Bulk Rename features
    renamableList : bpy.props.CollectionProperty(type = ArmaToolboxRenamableProperty,
          description="Renamables")
    renamableListIndex : bpy.props.IntProperty()

    renameFrom : bpy.props.StringProperty("renameFrom", description="Rename From", subtype='FILE_PATH')
    renameTo : bpy.props.StringProperty("renameTo", description="Rename to", subtype='FILE_PATH')
    
    # Bulk Reparent features
    parentFrom : bpy.props.StringProperty("parentFrom", description="Parent From", subtype='DIR_PATH')
    parentTo : bpy.props.StringProperty("parentTo", description="Parent to", subtype='DIR_PATH')
    
    # Selection Rename
    renameSelectionFrom : bpy.props.StringProperty("renameSelectionFrom", description="Rename from")
    renameSelectionTo : bpy.props.StringProperty("renameSelectionTo", description="Rename to")
    
    # RVMat Relocator
    rvmatRelocFile : bpy.props.StringProperty("rvmatRelocFile", description="RVMat to relocate", subtype = 'FILE_PATH')
    rvmatOutputFolder : bpy.props.StringProperty("rvmatOutputFolder", description="RVMat output", subtype = 'DIR_PATH')
      
    
    # Material Relocator
    matOutputFolder : bpy.props.StringProperty("matOutputFolder", description="RVMat output", subtype = 'DIR_PATH')
    matAutoHandleRV : bpy.props.BoolProperty(name="matAutoHandleRV", description="Automatically relocate RVMat", default=True)
    matPrefixFolder : bpy.props.StringProperty("matPrefixFolder", description="Prefix for texture search", subtype = 'DIR_PATH', 
                                               default= "P:\\")
    # Merge as Proxy
    mapProxyObject : bpy.props.StringProperty("mapProxyObject", description="Proxy Object", subtype = 'FILE_PATH')
    mapProxyIndex :  bpy.props.IntProperty("mapProxyIndex", description="Base Index", default=1)
    mapProxyDelete : bpy.props.BoolProperty("mapProxyDelete", description="Delete original", default=True)
    mapProxyEnclose : bpy.props.StringProperty("mapProxyEnclose", description="Enclosed Selection")
    mapOpen : bpy.props.BoolProperty(name="mapOpen", default=False)
    mapUseNamedSelection : bpy.props.BoolProperty(name="mapUseNamedSelection", default=True)
    mapAutoIncrementProxy : bpy.props.BoolProperty(name="mapAutoIncrementProxy", default=False)
    
    # Proxy Path Changer
    proxyPathFrom : bpy.props.StringProperty("proxyPathFrom", description="Proxy Path From", subtype = 'FILE_PATH')
    proxyPathTo : bpy.props.StringProperty("proxyPathTo", description="Proxy path To", subtype = 'FILE_PATH')
    
    # Weight setter
    vertexWeight : bpy.props.FloatProperty("vertexWeight", description="Vertex Weight to set to", default = 0, min=0)
    
    # Selection Tools
    hiddenSelectionName : bpy.props.StringProperty("hiddenSelectionName", description = "Name of the hidden selection to create", default="camo")

    # Hitpoint creator
    hpCreatorSelectionName : bpy.props.StringProperty("hpCreatorSelectionName", description = "Name of the hitpoint selection create", default="_point")
    hpCreatorRadius : bpy.props.FloatProperty("hpCreatorRadius", description = "radius of hitpont sphere", default = 0.3, min = 0.001)

    # UV Island angle
    uvIslandAngle : bpy.props.FloatProperty("maxUVAngle", description="Maximum angle for UV island stretch", default = 5)

    # VGroup Maker/Extender
    vgr_deselect_all: bpy.props.EnumProperty(name="deselect_all",
        items={
            ('nothing"', 'Nothing', "Do Nothing"),
            ('deselect', 'Deselect', "Deselect"),
            ('hide', 'Hide', "Hide")
        })
    vgr_vgroup_name: bpy.props.StringProperty(name="vgroup_name", default="grp_%d")
    vgr_vgroup_num: bpy.props.IntProperty(name="vgroup_num", default=1)
    vgr_vgroup_base: bpy.props.IntProperty(name="vgroup_base", default = 1);
    vgr_vgroup_baseEnable: bpy.props.BoolProperty(name = "vgroup_baseEnable", default = False);

    # Batch Operation on Configs
    bex_exportConfigs: bpy.props.CollectionProperty(
        type=ArmaToolboxExportConfigObjectProperty, description="Export Configs")
    bex_configIndex: bpy.props.IntProperty("configIndex", default=-1)

    bex_config: bpy.props.EnumProperty(
        name="Export",
        description="What to export",
        items=bex_add_defined_export_configs,
        default=0
    )

    bex_choice: bpy.props.EnumProperty(
        name = "Choice",
        description="All or any",
        items = {
            ('all', 'All of these (maybe more)', 'All of these'),
            ('any', 'Any of these', 'Any of these'),
            ('exact', 'Exact match', 'Exact match')
        }
    )

    bex_applyAll : bpy.props.BoolProperty(
        name = "ApplyAll",
        default = False,
        description = "Apply to All"
    )

    # Transparency level
    trlevel_level: bpy.props.IntProperty(
        name = "Transparency Priority",
        description = "Priority for transparency sorting. Lower numbers appear closer to the observer's eye.",
        min = 0,
        max = 5
    )

    # ZBias
    zbias_level: bpy.props.BoolProperty(
        name = "ZBias",
        description = "ZBias of a face. True means the face has ZBias",
        default = True
    );

    # VGroup Rename
    vgrpRename_from : bpy.props.StringProperty(name="vgrpRename_from", default="")
    vgrpRename_to   : bpy.props.StringProperty(name="vgrpRename_to", default = "")
    vgrpRename_open : bpy.props.BoolProperty(name="vgrpRename_open", default = False)

    # VGroup Batch ops
    vgrpB_match : bpy.props.StringProperty(name="vgrpB_match", default=".*")
    vgrpB_operator : bpy.props.StringProperty(name="vgrpB_operator", default="")
    vgrpB_operation : bpy.props.EnumProperty(
        name="Operation",
        description="What to do",
        items={
            ('append', 'Append operator to matching group', 'Append'),
            ('prefix', 'Prefix operator to matching group', 'Prefix')
        }
    )
    vgrpB_open : bpy.props.BoolProperty(name="vgrpB_open", default = False)

    # Meshcollectivfy
    mcify_lod : bpy.props.EnumProperty(
        name="LOD Type",
        description="Type of LOD",
        items=lodPresets,
        default='-1.0')
    mcify_lodDistance : bpy.props.FloatProperty(
        name="Distance",
        description="Distance of Custom LOD",
        default=1.0)
    mcify_collectionName : bpy.props.StringProperty(
        name="Collection Name", 
        description="Name of the collection to create, leave empty to not create a collection",
        default="")
    mcify_add_decimate: bpy.props.BoolProperty(
        name="Add Decimate",
        description = "Add a decimate modifier to the collected meshes",
        default = False)
    mcify_decimateRatio: bpy.props.FloatProperty(
        name="Decimate Ratio",
        description="Ratio for the decimate modifier",
        default=0.5,
        min=0.0,
        max=1.0)
    mcify_deleteGroup : bpy.props.StringProperty(
        name="Delete Group",
        description="Vertex Groups to delete, empty for none, multiple with comma",
        default="")

class ArmaToolboxCopyHelper(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(name="name", 
        description = "Name")
    doCopy : bpy.props.BoolProperty(name="doCopy",
        description="Do copy Value")
    index : bpy.props.IntProperty(name="index", description="Index")

class ArmaToolboxExportConfigEntryProperty(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(name="name", description = "Configuration Name")
    fileName : bpy.props.StringProperty(name="fileName", description = "Export File Name", subtype="FILE_NAME")
    originObject : bpy.props.PointerProperty(type=bpy.types.Object, name="originObject", description = "Optional center reference")

class ArmaToolboxExportConfigsProperty(bpy.types.PropertyGroup):
    exportConfigs: bpy.props.CollectionProperty(type = ArmaToolboxExportConfigEntryProperty, description = "Export Configs")

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

    try:
        if bpy.types.Scene.armaExportConfigs:
            pass
    except:
        bpy.types.Scene.armaExportConfigs = bpy.props.PointerProperty(
            type=ArmaToolboxExportConfigsProperty,
            description = "Export Config List"
        )

    try:
        if bpy.types.WindowManager.armaActiveExportConfig:
            pass
    except:
        bpy.types.WindowManager.armaActiveExportConfig = IntProperty(
            name = "armaActiveExportConfig",
            default = -1
        )

class ArmaToolboxFixShadowsHelper(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty(name="name", 
        description = "Object Name")
    fixThis : bpy.props.BoolProperty(name="fixThis",
        description="Fix") 

prpclasses = (
    ArmaToolboxDeletionListProperty,
    ArmaToolboxExportConfigObjectProperty,
    ArmaToolboxCollectedMeshesProperty,
    ArmaToolboxCopyHelper,
    ArmaToolboxNamedProperty,
    ArmaToolboxNamedSelection,
    ArmaToolboxKeyframeProperty,
    ArmaToolboxComponentProperty,
    ArmaToolboxProxyProperty,
    ArmaToolboxHeightfieldProperties,
    ArmaToolboxProperties,
    ArmaToolboxMaterialProperties,
    ArmaToolboxRenamableProperty,
    ArmaToolboxGUIProps,
    ArmaToolboxFixShadowsHelper, 
    ArmaToolboxExportConfigEntryProperty,
    ArmaToolboxExportConfigsProperty
)

def register():
    print ("registering properties")
    from bpy.utils import register_class
    for cls in prpclasses:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in prpclasses:
        unregister_class(cls)


def lodName(lod):
    for l in lodPresets:
        f = float(l[0])
        if lod == f:
            return l[1]
