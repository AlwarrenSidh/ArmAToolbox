import bpy

from . import (
    lists,
    properties,
    ArmaProxy,
    ArmaTools,
    RVMatTools,
    BatchMDLExport,
    NamedSelections
)

#from lists import safeAddTime

#from ArmaProxy import CopyProxy, CreateProxyPosRot, SelectProxy, DeleteProxy
import bmesh
from math import *
from mathutils import *
from . import getLodsToFix
#from BatchMDLExport import ATBX_OT_p3d_batch_export
import os.path as Path
#from RtmTools import exportModelCfg
# from NamedSelections import *
import re

class ATBX_OT_add_frame_range(bpy.types.Operator):
    bl_idname = "armatoolbox.add_frame_range"
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
            lists.safeAddTime(frame, prp)
            
        return {"FINISHED"}
        
class ATBX_OT_add_key_frame(bpy.types.Operator):
    bl_idname = "armatoolbox.add_key_frame"
    bl_label = ""
    bl_description = "Add a keyframe"
    
    def execute(self, context):
        obj = context.active_object
        prp = obj.armaObjProps.keyFrames
        frame = context.scene.frame_current
        lists.safeAddTime(frame, prp)
        return {"FINISHED"}
  
class ATBX_OT_add_all_key_frames(bpy.types.Operator):
    bl_idname = "armatoolbox.add_all_key_frames"
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
            lists.safeAddTime(frame, prp)
            
        return {"FINISHED"}  
  
class ATBX_OT_rem_key_frame(bpy.types.Operator):
    bl_idname = "armatoolbox.rem_key_frame"
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
        
class ATBX_OT_rem_all_key_frames(bpy.types.Operator):
    bl_idname = "armatoolbox.rem_all_key_frames"
    bl_label = ""
    bl_description = "Remove a keyframe"

    def execute(self, context):
        obj = context.active_object
        arma = obj.armaObjProps
        arma.keyFrames.clear()
        return {"FINISHED"}        
        
class ATBX_OT_add_prop(bpy.types.Operator):
    bl_idname = "armatoolbox.add_prop"
    bl_label = ""
    bl_description = "Add a named Property"
    
    def execute(self, context):
        obj = context.active_object
        prp = obj.armaObjProps.namedProps
        item = prp.add()
        item.name = "<new property>"
        return {"FINISHED"}

class ATBX_OT_rem_prop(bpy.types.Operator):
    bl_idname = "armatoolbox.rem_prop"
    bl_label = ""
    bl_description = "Remove named property"
    
    def execute(self, context):
        obj = context.active_object
        arma = obj.armaObjProps
        if arma.namedPropIndex != -1:
            arma.namedProps.remove(arma.namedPropIndex)
        return {"FINISHED"}

class ATBX_OT_clear_props(bpy.types.Operator):
    bl_idname = "armatoolbox.clear_props"
    bl_label = ""
    bl_description = "Remove all named properties"

    def execute(self, context):
        obj = context.active_object
        arma = obj.armaObjProps
        arma.namedProps.clear()
        return {"FINISHED"}

###
##   Enable Operator
#

class ATBX_OT_enable(bpy.types.Operator):
    bl_idname = "armatoolbox.enable"
    bl_label = "Enable for Arma Toolbox"
    
    def execute(self, context):
        obj = context.active_object
        if (obj.armaObjProps.isArmaObject == False):
            obj.armaObjProps.isArmaObject = True
        return{'FINISHED'}

###
##   Proxy Operators
#


class ATBX_OT_add_new_proxy(bpy.types.Operator):
    bl_idname = "armatoolbox.add_new_proxy"
    bl_label = ""
    bl_description = "Add a proxy"
    
    def execute(self, context):
        bpy.ops.object.mode_set(mode="EDIT")
        obj = context.active_object
        mesh = obj.data
        
        cursor_location = bpy.context.scene.cursor.location
        cursor_location = cursor_location - obj.location

        bm = bmesh.from_edit_mesh(mesh)

        i = len(bm.verts)
        v1 = bm.verts.new(cursor_location + Vector((0,0,0)))
        v2 = bm.verts.new(cursor_location + Vector((0,0,1)))
        v3 = bm.verts.new(cursor_location + Vector((0,0.5,0)))
        
        f = bm.faces.new((v1,v2,v3))
        print (v1.index)  
        bpy.ops.object.mode_set(mode="OBJECT")

        #bm.to_mesh(mesh)
        #mesh.update()
              
        vgrp = obj.vertex_groups.new(name = "@@armaproxy")
        vgrp.add([i+0],1,'ADD')
        vgrp.add([i+1],1,'ADD')
        vgrp.add([i+2],1,'ADD')

        fnd = obj.vertex_groups.find("-all-proxies")
        if (fnd == -1):
            vgrp2 = obj.vertex_groups.new(name = "-all-proxies")
        else:
            vgrp2 = obj.vertex_groups[fnd]
        
        vgrp2.add([i+0],1,'ADD')
        vgrp2.add([i+1],1,'ADD')
        vgrp2.add([i+2],1,'ADD')

        bpy.ops.object.mode_set(mode="EDIT")
        
        p = obj.armaObjProps.proxyArray.add()
        p.name = vgrp.name
        
        
        return {"FINISHED"}    

# This does two things. First, it goes through the model checking if the
# proxies in the list are still in the model, and delete all that arent.
#
# Secondly, it looks for "standard" proxy definition like "proxy:xxxx.001" and
# converts them into new proxies.
class ATBX_OT_add_sync_proxies(bpy.types.Operator):
    bl_idname = "armatoolbox.sync_proxies"
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

class ATBX_OT_add_toggle_proxies(bpy.types.Operator):
    bl_idname = "armatoolbox.toggle_proxies"
    bl_label = ""
    bl_description = "Toggle GUI visibilityl"
    
    prop : bpy.props.StringProperty()
    
    def execute(self, context):
        obj = context.active_object
        prop = obj.armaObjProps.proxyArray[self.prop]
        if prop.open == True:
            prop.open = False
        else:
            prop.open = True  
        return {"FINISHED"}     

class ATBX_OT_copy_proxy(bpy.types.Operator):
    bl_idname = "armatoolbox.copy_proxy"
    bl_label = ""
    bl_description = "Copy proxy to other LOD's"    

    objectArray : bpy.props.CollectionProperty(type=properties.ArmaToolboxCopyHelper)
    copyProxyName : bpy.props.StringProperty()
    encloseInto : bpy.props.StringProperty(description="Enclose the proxy in a selection. Leave blank to not create any extra selection")

    def execute(self, context):
        sObj = context.active_object
        if len(context.selected_objects) > 1:
            for obj in context.selected_objects:
                if obj != context.active_object:
                    ArmaProxy.CopyProxy(sObj, bpy.data.objects[obj.name], self.copyProxyName)
        else:
            for obj in self.objectArray:
                if obj.doCopy:
                    enclose = self.encloseInto
                    enclose = enclose.strip()
                    if len(enclose) == 0:
                        enclose = None
                    
                    ArmaProxy.CopyProxy(sObj, bpy.data.objects[obj.name], self.copyProxyName, enclose)

            self.objectArray.clear()
        return {"FINISHED"}
   
    def invoke(self, context, event):
        if len(context.selected_objects) > 1:
            return self.execute(context)
        for obj in bpy.data.objects.values():
            if obj.armaObjProps.isArmaObject == True and obj != context.active_object:
                prop = self.objectArray.add()
                prop.name  = obj.name
                prop.doCopy = True
        
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        if len(context.selected_objects) > 1:
            return
        layout = self.layout
        col = layout.column()
        col.label(text="Copy Proxy!")
        for s in self.objectArray:
            row = layout.row()
            row.prop(s, "doCopy", text=s.name)
        row = layout.row()
        row.prop(self, "encloseInto", text="Enclose in:")

class ATBX_OT_delete_proxy(bpy.types.Operator):
    bl_idname = "armatoolbox.delete_proxy"
    bl_label = ""
    bl_description = "Delete given proxy"  
    
    proxyName : bpy.props.StringProperty()
    
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

class ATBX_OT_select_proxy(bpy.types.Operator):
    bl_idname = "armatoolbox.select_proxy"
    bl_label = ""
    bl_description = "selects given proxy"  
    
    proxyName : bpy.props.StringProperty()
    
    @classmethod
    def poll(self, context):
        if context.active_object.mode == 'EDIT':
            return True
        else:
            return False
    
    def execute(self, context):
        sObj = context.active_object
        ArmaProxy.SelectProxy(sObj, self.proxyName)
        return {"FINISHED"}

###
##  Weight Tools
#

class ATBX_OT_select_weight_vertex(bpy.types.Operator):
    bl_idname = "armatoolbox.sel_weights"
    bl_label = "Select vertices with more than 4 bones weights"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'  
    
    def execute(self, context):
        ArmaTools.selectOverweightVertices()
        return {'FINISHED'}

class ATBX_OT_prune_weight_vertex(bpy.types.Operator):
    bl_idname = "armatoolbox.prune_weights"
    bl_label = "Prune vertices with more than 4 bones weights"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'  
    
    def execute(self, context):
        ArmaTools.pruneOverweightVertices()
        return {'FINISHED'}

class ATBX_OT_bulk_rename(bpy.types.Operator):
    bl_idname = "armatoolbox.bulk_rename"
    bl_label = "Bulk Rename Arma material paths"
    
    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        if guiProps.renamableListIndex > -1 and guiProps.renamableList.__len__() > guiProps.renamableListIndex:
            frm = guiProps.renamableList[guiProps.renamableListIndex].name
            t   = guiProps.renameTo 
            ArmaTools.bulkRename(context, frm, t)
        return {'FINISHED'}
    
class ATBX_OT_create_components(bpy.types.Operator):
    bl_idname = "armatoolbox.create_components"
    bl_label = "Create Geometry Components"
    
    def execute(self, context):
        ArmaTools.createComponents(context)
        return {'FINISHED'}

class ATBX_OT_renumber_components(bpy.types.Operator):
    bl_idname = "armatoolbox.renumber_components"
    bl_label = "Renumber existing components"

    def execute(self, context):
        ArmaTools.RenumberComponents(context.active_object)
        return {'FINISHED'}

class ATBX_OT_bulk_reparent(bpy.types.Operator):
    bl_idname = "armatoolbox.bulk_reparent"
    bl_label = "Bulk Re-parent Arma material paths"

    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        frm = guiProps.parentFrom
        t   = guiProps.parentTo
        ArmaTools.bulkReparent(context, frm, t)
        return {'FINISHED'}

class ATBX_OT_selection_rename(bpy.types.Operator):
    bl_idname = "armatoolbox.bulk_rename_selection"
    bl_label = "Bulk Re-parent Arma material paths"

    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        frm = guiProps.renameSelectionFrom
        t   = guiProps.renameSelectionTo
        ArmaTools.bulkRenameSelections(context, frm, t)
        return {'FINISHED'}      

class ATBX_OT_hitpoint_creator(bpy.types.Operator):
    bl_idname = "armatoolbox.hitpoint_creator"
    bl_label = "Create Hitpoint Volume"
    
    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        selection = guiProps.hpCreatorSelectionName
        radius = guiProps.hpCreatorRadius
        ArmaTools.hitpointCreator(context, selection, radius)
        return {'FINISHED'}

# Make sure all ArmaObjects do not have n-gons with more than four vertices
class ATBX_OT_ensure_quads(bpy.types.Operator):
    '''Make sure all ArmaObjects do not have n-gons with more than four vertices'''
    bl_idname = "armatoolbox.ensure_quads"
    bl_label = "Tesselate all n-gons > 4 in all objects flagged as Arma Objects"

    def execute(self, context):
        ArmaTools.tessNonQuads(context)
        return {'FINISHED'}

class ATBX_OT_rvmat_relocator(bpy.types.Operator):
    '''Relocate a single RVMat to a different directory'''
    bl_idname = "armatoolbox.rvmatrelocator"
    bl_label = "Relocate RVMat"
    
    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        rvfile = guiProps.rvmatRelocFile
        rvout  = guiProps.rvmatOutputFolder
        prefixPath = guiProps.matPrefixFolder
        RVMatTools.rt_CopyRVMat(rvfile, rvout, prefixPath)
        return {'FINISHED'}

class ATBX_OT_material_relocator(bpy.types.Operator):
    ''' Relocate RVMATs'''
    bl_idname = "armatoolbox.materialrelocator"
    bl_label = "Relocate Material"
    
    material : bpy.props.StringProperty()
    texture : bpy.props.StringProperty()
    
    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps

        outputPath = guiProps.matOutputFolder
        if len(outputPath) == 0:
            self.report({'ERROR_INVALID_INPUT'}, "Output folder name missing")
        
        prefixPath = guiProps.matPrefixFolder
        if len(prefixPath) == 0:
            prefixPath = "P:\\"
        
        materialName = self.material
        textureName = self.texture
        RVMatTools.mt_RelocateMaterial(textureName, materialName, outputPath, guiProps.matAutoHandleRV, prefixPath)

        return {'FINISHED'}

class ATBX_OT_toggle_gui_prop(bpy.types.Operator):
    bl_idname = "armatoolbox.toggleguiprop"
    bl_label = ""
    bl_description = "Toggle GUI visibilityl"
    
    prop : bpy.props.StringProperty()
        
    def execute(self, context):
        prop = context.window_manager.armaGUIProps
        if prop.is_property_set(self.prop) == True and prop[self.prop] == True:
            prop[self.prop] = False
        else:
            prop[self.prop] = True  
        return {"FINISHED"}   


class ATBX_OT_join_as_proxy(bpy.types.Operator):
    bl_idname = "armatoolbox.joinasproxy"
    bl_label = ""
    bl_description = "Join as Proxy"
    
    @classmethod
    def poll(cls, context):
        ## Visible when there is a selected object, it is a mesh
        obj = context.active_object
       
        return (obj 
            and obj.select_get() == True
            and obj.armaObjProps.isArmaObject == True
            and obj.type == "MESH" 
            and len(bpy.context.selected_objects) > 1
            )
        
    def execute(self, context):
        obj = context.active_object
        selected = context.selected_objects
        
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
                if context.window_manager.armaGUIProps.mapUseNamedSelection:
                    newPath = ArmaTools.findNamedSelectionString(sel, "proxy")
                    if newPath is not None:
                        path = newPath
                    else:
                        path = context.window_manager.armaGUIProps.mapProxyObject

                if enclose == None:
                    e = None
                else:
                    e = enclose
                pos = sel.location - obj.location 
                ArmaProxy.CreateProxyPosRot(obj, pos, sel.rotation_euler, path, index, e)
                index = index + 1
        
        if doDel == True:
            obj.select_set(False)
            bpy.ops.object.delete();      
        
        if context.window_manager.armaGUIProps.mapAutoIncrementProxy:
            context.window_manager.armaGUIProps.mapProxyIndex = index

        return {"FINISHED"}   

###
##  Proxy Path Changer
#
#   Code contributed by Cowcancry

class ATBX_OT_proxy_path_changer(bpy.types.Operator):
    bl_idname = "armatoolbox.proxypathchanger"
    bl_label = "Proxy Path Change"
    
    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        pathFrom = guiProps.proxyPathFrom
        pathTo = guiProps.proxyPathTo

        for obj in bpy.data.objects.values():
            if (obj 
            and obj.armaObjProps.isArmaObject == True
            and obj.type == "MESH"):
                for proxy in obj.armaObjProps.proxyArray:
                    proxy.path = proxy.path.replace(pathFrom, pathTo)
        return {'FINISHED'}

class ATBX_OT_selection_translator(bpy.types.Operator):
    bl_idname = "armatoolbox.autotranslate"
    bl_label = "Attempt to automatically translate Czech selection names"

    def execute(self, context):
        ArmaTools.autotranslateSelections()
        return {'FINISHED'}
 

class ATBX_OT_set_mass(bpy.types.Operator):
    bl_idname = "armatoolbox.setmass"
    bl_label = ""
    bl_description = "Set the same mass for all selected vertices"
    
    @classmethod
    def poll(cls, context):
        ## Visible when there is a selected object, it is a mesh
        obj = context.active_object
        return (obj
            and obj.select_get() == True
            and obj.armaObjProps.isArmaObject == True
            and obj.type == "MESH" 
            and (obj.armaObjProps.lod == '1.000e+13' or obj.armaObjProps.lod == '4.000e+13')
            and obj.mode == 'EDIT'
            ) 
        
    def execute(self, context):
        obj = context.active_object
        selected = context.selected_objects
               
        mass = context.window_manager.armaGUIProps.vertexWeight

        ArmaTools.setVertexMass(obj, mass)
        return {"FINISHED"}   

class ATBX_OT_distribute_mass(bpy.types.Operator):
    bl_idname = "armatoolbox.distmass"
    bl_label = ""
    bl_description = "Distribute the given mass equally to all selected vertices"
    
    @classmethod
    def poll(cls, context):
        ## Visible when there is a selected object, it is a mesh
        obj = context.active_object
        
        return (obj
            and obj.select_get() == True
            and obj.armaObjProps.isArmaObject == True
            and obj.type == "MESH" 
            and (obj.armaObjProps.lod == '1.000e+13' or obj.armaObjProps.lod == '4.000e+13')
            and obj.mode == 'EDIT'
            ) 
        
    def execute(self, context):
        obj = context.active_object
        selected = context.selected_objects
               
        mass = context.window_manager.armaGUIProps.vertexWeight

        ArmaTools.distributeVertexMass(obj, mass)
        return {"FINISHED"} 


# Fix shadow volumes
class ATBX_OT_fix_shadows(bpy.types.Operator):
    bl_idname = "armatoolbox.fixshadows"
    bl_label = "Items to fix"
    bl_description = "Fix Shadow volumes resolutions"
    
    objectArray : bpy.props.CollectionProperty(type=properties.ArmaToolboxFixShadowsHelper)
    
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
        row.label (text  = "Click 'OK' to fix")

""" class ATBX_OT_export_bone(bpy.types.Operator):
    bl_idname = "armatoolbox.exportbone"
    bl_label = ""
    bl_description = "Export a bone as model.cfg animation"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        
        return (obj
            and obj.select_get() == True
            and obj.armaObjProps.isArmaObject == True
            and obj.type == "ARMATURE"
            )  
        
    def execute(self, context):
        obj = context.active_object
        arma = obj.armaObjProps

        exportModelCfg(context, obj, arma.exportBone, arma.selectionName, arma.animSource, arma.prefixString, arma.outputFile)
               
        return {"FINISHED"}  """


class ATBX_OT_section_optimize(bpy.types.Operator):
    bl_idname = "armatoolbox.section_optimize"
    bl_label = "Optimize section count."
    bl_description = "Available in Edit mode. Select transparent faces and click this button to minimize section count."

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'  

    def execute(self, context):
        ArmaTools.optimizeSectionCount(context)

        return {"FINISHED"}

class ATBX_OT_vgroup_redefine(bpy.types.Operator):
    bl_idname = "armatoolbox.vgroup_redefine"
    bl_label = "Redefine Vertex Group"
    bl_description = "Delete the vertex group and recreate it with the selected vertices only"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        obj = context.active_object
        try:
            vg_name = obj.vertex_groups.active.name
            bpy.ops.object.vertex_group_remove()
            vgrp = bpy.context.active_object.vertex_groups.new(name=vg_name)
            bpy.ops.object.vertex_group_assign()
        except:
            pass
        return {"FINISHED"}

class ATBX_OT_join(bpy.types.Operator):
    bl_idname = "armatoolbox.join"
    bl_label = "Join selected objects with active object"
    bl_description = "Joins all selected objects with the active one, maintaining the proxies of all joined objects"

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        ArmaTools.joinObjectToObject(context)
        return {"FINISHED"}

class ATBX_OT_selectBadUV(bpy.types.Operator):
    bl_idname = "armatoolbox.select_bad_uv"
    bl_label = "Select distorted UV islands"
    bl_description = "select all islands with UV distortion."

    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        naxAngle = radians(guiProps.uvIslandAngle)

        ArmaTools.selectBadUV(self, context, naxAngle)
        
        return {'FINISHED'}

class ATBX_OT_set_transparency(bpy.types.Operator):
    bl_idname = "armatoolbox.set_transparency"
    bl_label = "Mark as Transparent"
    bl_description = "Mark selected faces as transparent for sorting purposes"

    @classmethod
    def poll(self, context):
        if context.active_object != None and context.active_object.mode == 'EDIT':
            return True
        else:
            return False

    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        ArmaTools.markTransparency(self, context, 1+guiProps.trlevel_level)
        return {'FINISHED'}


class ATBX_OT_set_nontransparency(bpy.types.Operator):
    bl_idname = "armatoolbox.set_nontransparency"
    bl_label = "Mark as Opposite to Transparent"
    bl_description = "Mark selected faces as opposite to transparent for sorting purposes"

    @classmethod
    def poll(self, context):
        if context.active_object != None and context.active_object.mode == 'EDIT':
            return True
        else:
            return False

    def execute(self, context):
        ArmaTools.markTransparency(self, context, -1)
        return {'FINISHED'}

class ATBX_OT_unset_transparency(bpy.types.Operator):
    bl_idname = "armatoolbox.unset_transparency"
    bl_label = "Mark as non-transparent"
    bl_description = "Mark selected faces as non-transparent for sorting purposes"

    @classmethod
    def poll(self, context):
        if context.active_object != None and context.active_object.mode == 'EDIT':
            return True
        else:
            return False

    def execute(self, context):
        ArmaTools.markTransparency(self, context, 0)
        return {'FINISHED'}


class ATBX_OT_select_transparent(bpy.types.Operator):
    bl_idname = "armatoolbox.select_transparent"
    bl_label = "Select transparent faces"
    bl_description = "Select all faces marked as transparent"

    @classmethod
    def poll(self, context):
        if context.active_object != None and context.active_object.mode == 'EDIT':
            return True
        else:
            return False

    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        ArmaTools.selectTransparency(self, context, 1+guiProps.trlevel_level)
        return {'FINISHED'}


class ATBX_OT_add_config(bpy.types.Operator):
    bl_idname = "armatoolbox.add_config"
    bl_label = ""
    bl_description = "Add an export config"

    def execute(self, context):
        prp = context.scene.armaExportConfigs.exportConfigs
        item = prp.add()
        item.name = "New Export Config"
        item.fileName = ".p3d"
        return {"FINISHED"}


class ATBX_OT_rem_config(bpy.types.Operator):
    bl_idname = "armatoolbox.rem_config"
    bl_label = ""
    bl_description = "Remove an export config"

    def execute(self, context):
        prp = context.scene.armaExportConfigs.exportConfigs
        active = context.window_manager.armaActiveExportConfig
        if active != -1:
            prp.remove(active)
        return {"FINISHED"}

class ATBX_OT_save_configs(bpy.types.Operator):
    bl_idname = "armatoolbox.save_configs"
    bl_label = ""
    bl_description = "Save Configs to the clipboard"

    def execute(self, context):
        prp = context.scene.armaExportConfigs.exportConfigs
        text = ""
        for p in prp:
            text = text + p.name + "|"
            text = text + p.fileName + "|"
            if (p.originObject == None):
                text = text + "\n"
            else:
                text = text + p.originObject.name + "\n"
            
        
        context.window_manager.clipboard = text
        return {"FINISHED"}

class ATBX_OT_load_configs(bpy.types.Operator):
    bl_idname = "armatoolbox.load_configs"
    bl_label = ""
    bl_description = "Load Configs from Clipboard"

    def execute(self, context):
        prp = context.scene.armaExportConfigs.exportConfigs
        text = context.window_manager.clipboard

        prp.clear()

        for line in text.splitlines():
            results = line.split("|")
            name = ""
            fileName = ""
            centerName = ""
            if len(results) > 0:
                name = results[0]
            if len(results) > 1:
                fileName = results[1]
            if len(results) > 2:
                centerName = results[2]
            
            item = prp.add()
            item.name = name
            item.fileName = fileName
            if len(centerName):
                item.originObject = bpy.data.objects[centerName]

        return {"FINISHED"}

class ATBX_OT_add_obj_config(bpy.types.Operator):
    bl_idname = "armatoolbox.add_obj_config"
    bl_label = ""
    bl_description = "Add an export config to an object"

    config_name : bpy.props.StringProperty(name="config_name")

    def execute(self, context):
        obj = context.active_object
        prp = obj.armaObjProps.exportConfigs
        item = prp.add()
        item.name = self.config_name
        return {"FINISHED"}


class ATBX_OT_rem_obj_config(bpy.types.Operator):
    bl_idname = "armatoolbox.rem_obj_config"
    bl_label = ""
    bl_description = "Remove an export config from an object"

    config_name: bpy.props.StringProperty(name="config_name")

    def execute(self, context):
        obj = context.active_object
        prp = obj.armaObjProps.exportConfigs
        active = prp.keys().index(self.config_name)
        if active != -1:
            prp.remove(active)
        return {"FINISHED"}


class ATBX_OT_add_guiprop_config(bpy.types.Operator):
    bl_idname = "armatoolbox.add_guiprop_config"
    bl_label = ""
    bl_description = "Add an export config to a gui list"

    config_name: bpy.props.StringProperty(name="config_name")

    def execute(self, context):
        obj = context.active_object
        prp = context.window_manager.armaGUIProps.bex_exportConfigs
        item = prp.add()
        item.name = self.config_name
        return {"FINISHED"}


class ATBX_OT_rem_guiprop_config(bpy.types.Operator):
    bl_idname = "armatoolbox.rem_guiprop_config"
    bl_label = ""
    bl_description = "Remove an export config from a gui list"

    config_name: bpy.props.StringProperty(name="config_name")

    def execute(self, context):
        obj = context.active_object
        prp = context.window_manager.armaGUIProps.bex_exportConfigs
        active = prp.keys().index(self.config_name)
        if active != -1:
            prp.remove(active)
        return {"FINISHED"}


class ATBX_OT_all_obj_config(bpy.types.Operator):
    bl_idname = "armatoolbox.all_obj_config"
    bl_label = ""
    bl_description = "Add all/Remove all configs"

    add_all : bpy.props.BoolProperty(name="add_all")

    def execute(self, context):
        obj = context.active_object
        prp = obj.armaObjProps.exportConfigs
        prp.clear()
        if self.add_all:
            for item in context.scene.armaExportConfigs.exportConfigs.values():
                prp.add(item.name)
    

class ATBX_OT_rep_vgroup_maker(bpy.types.Operator):
    bl_idname = "armatoolbox.rep_vgroup_maker"
    bl_label = "Make VGroup"
    bl_description = "Make a repeating vgroup from the name pattern"

    @classmethod
    def poll(self, context):
        if context.active_object != None and context.active_object.mode == 'EDIT':
            return True
        else:
            return False

    def execute(self, context):
        obj = context.active_object
        guiProps = context.window_manager.armaGUIProps

        i = 1
        if guiProps.vgr_vgroup_baseEnable:
            i = guiProps.vgr_vgroup_base
        # Find the name of the next free group given the pattern
        while True:
            group_name = guiProps.vgr_vgroup_name % i
            if obj.vertex_groups.get(group_name) == None:
                break
            i = i + 1

        # This vertex group is guaranteed not to exist
        obj.vertex_groups.new(name=group_name)
        bpy.ops.object.vertex_group_assign()
        if guiProps.vgr_deselect_all == 'deselect':
            bpy.ops.mesh.select_all(action="DESELECT")
        elif guiProps.vgr_deselect_all == 'hide':
            bpy.ops.mesh.hide()


        return {'FINISHED'}


class ATBX_OT_rep_vgroup_extender(bpy.types.Operator):
    bl_idname = "armatoolbox.rep_vgroup_extender"
    bl_label = "Extend VGroup"
    bl_description = "Extend a repeating vgroup from the name pattern"

    @classmethod
    def poll(self, context):
        if context.active_object != None and context.active_object.mode == 'EDIT':
            return True
        else:
            return False

    def execute(self, context):
        obj = context.active_object
        guiProps = context.window_manager.armaGUIProps

        i = guiProps.vgr_vgroup_num             # Get the current index
        guiProps.vgr_vgroup_num = i+1           # increment it
        # check if the group exists.
        group_name = guiProps.vgr_vgroup_name % i

        group = obj.vertex_groups.get(group_name)
        if group == None:
            return {'FINISHED'}

        bpy.ops.object.vertex_group_set_active(group=group_name)
        bpy.ops.object.vertex_group_assign()
        if guiProps.vgr_deselect_all == 'deselect':
            bpy.ops.mesh.select_all(action="DESELECT")
        elif guiProps.vgr_deselect_all == 'hide':
            bpy.ops.mesh.hide()

        return {'FINISHED'}

class ATBX_OT_copy_proxy_to_objects(bpy.types.Operator):
    bl_idname = "armatoolbox.copy_proxy_to_objects"
    bl_label = "Copy Proxies"
    bl_description = "Copy Proxies to a number of other objects."

    proxyArray : bpy.props.CollectionProperty(type=properties.ArmaToolboxCopyHelper)
    copySelections : bpy.props.BoolProperty(name="copySelections")

    @classmethod
    def poll(self, context):
        objects = [obj
                   for obj in bpy.context.selected_objects
                   if obj.type == 'MESH' and obj.armaObjProps.isArmaObject
                   ]
        if context.mode == 'OBJECT' and len(objects)>=2:
            return True
        else:
            return False

    def invoke(self, context, event):
        obj = context.active_object
        
        self.proxyArray.clear()

        for idx,prox in enumerate(obj.armaObjProps.proxyArray):
            name = Path.basename(prox.path)
            p = self.proxyArray.add()
            p.name = name
            p.doCopy = True
            p.index = idx

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

        for s in self.proxyArray:
            row = layout.row()
            row.prop(s, "doCopy", text=s.name)

        row = layout.row()
        row.label(text="Options:")
        row = layout.row()
        row.prop(self, "copySelections", text = "Copy Proxy's Selections")
        

    def execute(self, context):
        obj = context.active_object
        objects = [obj
                   for obj in bpy.context.selected_objects
                   if obj.type == 'MESH' and obj.armaObjProps.isArmaObject
                   ]

        for single in objects:
            if single != obj: # Don't touch yourself. It's a sin!
                for proxy in self.proxyArray:
                    if proxy.doCopy:
                        proxyName = obj.armaObjProps.proxyArray[proxy.index].name
                        vert = ArmaTools.GetFirstVertexOfGroup(obj, proxyName)
                        if self.copySelections:
                            groups = ArmaTools.GetVertexGroupsForVertex(obj, vert)
                        else:
                            groups = ["-all-proxies"]
                        try:
                            groups.remove(proxyName)
                        except:
                            pass
                        
                        ArmaProxy.CopyProxy(obj, single, proxyName, groups)

        return {'FINISHED'}


class ATBX_OT_delete_all_proxies(bpy.types.Operator):
    bl_idname = "armatoolbox.delete_all_proxies"
    bl_label = "Delete all Proxies"
    bl_description = "Delete all proxies on this object"


    def execute(self, context):
        obj = context.active_object
        while len(obj.armaObjProps.proxyArray) > 0:
            proxy = obj.armaObjProps.proxyArray[0]
            ArmaProxy.DeleteProxy(obj, proxy.name)

        return {'FINISHED'}   


class ATBX_OT_apply_config_batch(bpy.types.Operator):
    bl_idname = "armatoolbox.apply_config_batch"
    bl_label = "Perform Config batch task"
    bl_description = "Perform the Config Batch task"

    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        objs = [obj 
            for obj in context.view_layer.objects
                if obj.type == 'MESH' and obj.armaObjProps.isArmaObject and ArmaTools.testBatchCondition(guiProps, context.scene.armaExportConfigs.exportConfigs, obj)
        ]

        configToAdd = guiProps.bex_config

        for obj in objs:
            prp = obj.armaObjProps.exportConfigs
            item = prp.add()
            item.name = configToAdd
        
        return {'FINISHED'}

class ATBX_OT_add_named_selection(bpy.types.Operator):
    bl_idname = "armatoolbox.add_named_selection"
    bl_label = ""
    bl_description = "Add a named selection"

    def execute(self, context):
        obj = context.active_object
        NamedSelections.NamSel_AddNew(obj, name="Named Selection")
        return {'FINISHED'}

class ATBX_OT_add_remove_selection(bpy.types.Operator):
    bl_idname = "armatoolbox.sub_named_selection"
    bl_label = ""
    bl_description = "Delete named selection"

    def execute(self, context):
        obj = context.active_object
        arma = obj.armaObjProps
        if arma.namedSelectionIndex != -1:
            name = arma.namedSelection[arma.namedSelectionIndex].name
            NamedSelections.NamSel_Remove(obj, name=name)
            arma.namedSelection.remove(arma.namedSelectionIndex)
        return {'FINISHED'}
        
class ATBX_OT_named_selection_move(bpy.types.Operator):
    bl_idname = "armatoolbox.named_selection_move"
    bl_label = ""
    bl_description = "Move vertex group up or down"

    direction: bpy.props.StringProperty(name = "direction", description = "Direction")

    def execute(self, context):
        obj = context.active_object
        arma = obj.armaObjProps
        index = arma.namedSelectionIndex
        if self.direction == 'UP':
            if index > 0:
                arma.namedSelection.move(index, index-1)
                arma.namedSelectionIndex = index - 1
                arma.previousSelectionIndex = -1
        elif self.direction == 'DOWN':
            if index < arma.namedSelection.__len__()-1:
                arma.namedSelection.move(index, index+1)
                arma.namedSelectionIndex = index + 1
                arma.previousSelectionIndex = -1

        return {'FINISHED'}


class ATBX_OT_set_zbias(bpy.types.Operator):
    bl_idname = "armatoolbox.set_zbias"
    bl_label = "Set ZBias"
    bl_description = "Set the ZBias on selected faces"

    @classmethod
    def poll(self, context):
        if context.active_object != None and context.active_object.mode == 'EDIT':
            return True
        else:
            return False

    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        mask = 0x300
        flags = 0
        if guiProps.zbias_level == True:
            flags = 0x300 # High ZBias is the only working one in Arma 3

        ArmaTools.setFaceFlags(self, context, flags, mask)
        return {'FINISHED'}


class ATBX_OT_select_zbiased(bpy.types.Operator):
    bl_idname = "armatoolbox.select_zbiased"
    bl_label = "Select all faces with ZBias"
    bl_description = "Select all faces marked as Z Biased"

    @classmethod
    def poll(self, context):
        if context.active_object != None and context.active_object.mode == 'EDIT':
            return True
        else:
            return False

    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        ArmaTools.selectFaceFlags(self, context, 0x300, 0x300)
        return {'FINISHED'}


class ATBX_OT_batch_rename_vgrp(bpy.types.Operator):
    bl_idname = "armatoolbox.batch_rename_vgrp"
    bl_label = "Find and replace in VGroups"
    bl_description = "Replace one string by another in VGroups"

    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        fstring = guiProps.vgrpRename_from
        tstring = guiProps.vgrpRename_to


        obj = bpy.context.active_object
        bpy.ops.object.mode_set(mode='OBJECT', toggle=True)
        for g in obj.vertex_groups:
            g.name = g.name.replace(fstring, tstring)

        return {'FINISHED'}


class ATBX_OT_match_vgrp(bpy.types.Operator):
    bl_idname = "armatoolbox.match_vgrp"
    bl_label = "Perform operation on matching VGroup"
    bl_description = "Perform operation on matching VGroup"

    def execute(self, context):
        guiProps = context.window_manager.armaGUIProps
        obj = bpy.context.active_object
        bpy.ops.object.mode_set(mode='OBJECT', toggle=True)
        try:
            for g in obj.vertex_groups:
                match = re.fullmatch(guiProps.vgrpB_match, g.name)
                if match != None:
                    # If we get a result, we matched
                    if guiProps.vgrpB_operation == 'append':
                        g.name = g.name + guiProps.vgrpB_operator
                    elif guiProps.vgrpB_operation == 'prefix':
                        g.name = guiProps.vgrpB_operator + g.name
        except:
            self.report({'INFO'}, 'Invalid Matching Pattern')
            return {'CANCELLED'}

        return {'FINISHED'}

class ATBX_OT_add_selected_meshes(bpy.types.Operator):
    bl_idname = "armatoolbox.add_selected_meshes"
    bl_label = "Add selected meshes to active mesh capture list"
    bl_description ="Add selected meshes to active mesh capture list"

    @classmethod
    def poll(cls, context):
        l = len(context.selected_objects)
        return l>=2 and context.active_object.armaObjProps.isMeshCollector
    
    def execute(self, context):
        objs = context.selected_objects
        arma = context.active_object.armaObjProps
        for o in objs:
            if o != context.active_object and o.type == 'MESH':
                if o not in [x.object for x in arma.collectedMeshes]:
                    item = context.active_object.armaObjProps.collectedMeshes.add()
                    print(item)
                    item.object = o
                
        return {'FINISHED'}

class ATBX_OT_rem_selected_meshes(bpy.types.Operator):
    bl_idname = "armatoolbox.rem_selected_meshes"
    bl_label = "Remove Active meshes from active mesh capture list"
    bl_description ="Remove Active meshes from active mesh capture list"

    @classmethod
    def poll(cls, context):
       return context.active_object.armaObjProps.collectedMeshesIndex != -1

    def execute(self, context):
        obj = context.active_object
        arma = obj.armaObjProps
        if arma.collectedMeshesIndex != -1:
            arma.collectedMeshes.remove(arma.collectedMeshesIndex)

        return {'FINISHED'}

class ATBX_MT_clear_mesh_collector(bpy.types.Operator):
    bl_idname = "armatoolbox.clear_mesh_collector"
    bl_label = "Remove all meshes from the list"
    bl_description = "Remove all meshes from the list"

    def execute(self,context):
        obj = context.active_object
        arma = obj.armaObjProps
        arma.collectedMeshes.clear()

        return {'FINISHED'}

class ATBX_MT_add_same_config_mesh_collector(bpy.types.Operator):
    bl_idname = "armatoolbox.add_same_config_mesh_collector"
    bl_label = "Add all objects with the same config combo"
    bl_description = "Add all objects to this collector that have the exact same combination of configs"

    def execute(self, context):
        arma = context.active_object.armaObjProps
        if len(context.selected_objects)>1:
            cobjs = context.selected_objects
        else:
            cobjs = context.view_layer.objects
            
        objs = [obj for  obj in cobjs
                    if obj.type == 'MESH' 
                    and obj.armaObjProps.isArmaObject
                    and obj != context.active_object
                    and ArmaTools.matchAllConfigs(context, context.active_object, obj)]
            
        for o in objs:
            if o != context.active_object and o.type == 'MESH':
                if o not in [x.object for x in arma.collectedMeshes]:
                    item = context.active_object.armaObjProps.collectedMeshes.add()
                    item.object = o
                
        return {'FINISHED'}

class ATBX_MT_add_any_config_mesh_collector(bpy.types.Operator):
    bl_idname = "armatoolbox.add_any_config_mesh_collector"
    bl_label = "Add all objects with the at least one common config"
    bl_description = "Add all objects to this collector that have the one or more of the objects configs"

    def execute(self, context):
        arma = context.active_object.armaObjProps
        if len(context.selected_objects)>1:
            cobjs = context.selected_objects
        else:
            cobjs = context.view_layer.objects
            
        objs = [obj for  obj in cobjs
                if obj.type == 'MESH' 
                and obj.armaObjProps.isArmaObject
                and obj != context.active_object
                and ArmaTools.matchAnyConfigs(context, context.active_object, obj)]
        for o in objs:
            if o != context.active_object and o.type == 'MESH':
                if o not in [x.object for x in arma.collectedMeshes]:
                    item = context.active_object.armaObjProps.collectedMeshes.add()
                    item.object = o
                
        return {'FINISHED'}

class ATBX_MT_add_atleast_config_mesh_collector(bpy.types.Operator):
    bl_idname = "armatoolbox.add_atleast_config_mesh_collector"
    bl_label = "Add all objects with the at least one common config"
    bl_description = "Add all objects to this collector that have the one or more of the objects configs"

    def execute(self, context):
        arma = context.active_object.armaObjProps
        if len(context.selected_objects)>1:
            cobjs = context.selected_objects
        else:
            cobjs = context.view_layer.objects
            
        objs = [obj for  obj in cobjs
                if obj.type == 'MESH' 
                and obj.armaObjProps.isArmaObject
                and obj != context.active_object
                and ArmaTools.matchAtLeastConfigs(context, context.active_object, obj)]
        for o in objs:
            if o != context.active_object and o.type == 'MESH':
                if o not in [x.object for x in arma.collectedMeshes]:
                    item = context.active_object.armaObjProps.collectedMeshes.add()
                    item.object = o
                
        return {'FINISHED'}

class ATBX_OT_add_del_vgroup(bpy.types.Operator):
    bl_idname = "armatoolbox.add_deletion_vgroup"
    bl_label = "Add vgroup to deletion list"
    bl_description ="Add vgroup to deletion list"
   
    def execute(self, context):
        arma = context.active_object.armaObjProps
        item = context.active_object.armaObjProps.collectedMeshesDelete.add()
        item.vname = "<new item>"
        return {'FINISHED'}

class ATBX_OT_rem_del_vgroup(bpy.types.Operator):
    bl_idname = "armatoolbox.rem_deletion_vgroup"
    bl_label = "Remove vgroup from deletion list"
    bl_description ="Remove vgroup from deletion list"

    @classmethod
    def poll(cls, context):
       return context.active_object.armaObjProps.collectedMeshesDeleteIndex != -1

    def execute(self, context):
        obj = context.active_object
        arma = obj.armaObjProps
        if arma.collectedMeshesDeleteIndex != -1:
            arma.collectedMeshesDelete.remove(arma.collectedMeshesDeleteIndex)

        return {'FINISHED'}

class ATBX_MT_clear_del_vgroup(bpy.types.Operator):
    bl_idname = "armatoolbox.clear_del_vgroup"
    bl_label = "Remove all vgroups"
    bl_description = "Remove all vgroups"

    def execute(self,context):
        obj = context.active_object
        arma = obj.armaObjProps
        arma.collectedMeshesDelete.clear()

        return {'FINISHED'}

class ATBX_OT_meshcollectify(bpy.types.Operator):
    bl_idname = "armatoolbox.meshcollectify"
    bl_label = "Mesh Collectify"
    bl_description = "Collectify the meshes"

    def execute(self, context):
        objects = ArmaTools.getSelectedObjects(context)
        guiProps = bpy.context.window_manager.armaGUIProps
        mcify_lod = guiProps.mcify_lod
        mcify_lodDistance = guiProps.mcify_lodDistance
        mcify_collectionName = guiProps.mcify_collectionName
        mcify_addDecimate = guiProps.mcify_add_decimate
        mcify_decimateRatio = guiProps.mcify_decimateRatio
        mcify_deleteGroup = guiProps.mcify_deleteGroup
        for obj in objects:
            ArmaTools.meshCollectify(context, obj, mcify_lod, mcify_lodDistance, mcify_collectionName,
                                     mcify_addDecimate, mcify_decimateRatio, mcify_deleteGroup)
        return {'FINISHED'}


op_classes = (
    ATBX_OT_add_frame_range,
    ATBX_OT_add_key_frame,
    ATBX_OT_add_all_key_frames,
    ATBX_OT_rem_key_frame,
    ATBX_OT_rem_all_key_frames,
    ATBX_OT_add_prop,
    ATBX_OT_rem_prop,
    ATBX_OT_clear_props,
    ATBX_OT_enable,
    ATBX_OT_add_new_proxy,
    ATBX_OT_add_sync_proxies,
    ATBX_OT_add_toggle_proxies,
    ATBX_OT_copy_proxy,
    ATBX_OT_delete_proxy,
    ATBX_OT_select_weight_vertex,
    ATBX_OT_prune_weight_vertex,
    ATBX_OT_bulk_rename,
    ATBX_OT_create_components,
    ATBX_OT_bulk_reparent,
    ATBX_OT_selection_rename,
    ATBX_OT_hitpoint_creator,
    ATBX_OT_ensure_quads,
    ATBX_OT_rvmat_relocator,
    ATBX_OT_material_relocator,
    ATBX_OT_toggle_gui_prop,
    ATBX_OT_join_as_proxy,
    ATBX_OT_proxy_path_changer,
    ATBX_OT_selection_translator,
    ATBX_OT_set_mass,
    ATBX_OT_distribute_mass,
    ATBX_OT_fix_shadows,
    #ATBX_OT_export_bone,
    ATBX_OT_section_optimize,
    ATBX_OT_vgroup_redefine,
    ATBX_OT_select_proxy,
    ATBX_OT_join,
    ATBX_OT_selectBadUV,
    ATBX_OT_set_transparency,
    ATBX_OT_unset_transparency,
    ATBX_OT_select_transparent,
    ATBX_OT_set_nontransparency,
    ATBX_OT_add_config,
    ATBX_OT_rem_config,
    ATBX_OT_add_obj_config,
    ATBX_OT_rem_obj_config,
    ATBX_OT_all_obj_config,
    ATBX_OT_renumber_components,
    ATBX_OT_rep_vgroup_maker,
    ATBX_OT_copy_proxy_to_objects,
    ATBX_OT_delete_all_proxies,
    ATBX_OT_rep_vgroup_extender,
    ATBX_OT_add_guiprop_config,
    ATBX_OT_rem_guiprop_config,
    ATBX_OT_apply_config_batch,
    ATBX_OT_add_named_selection,
    ATBX_OT_add_remove_selection,
    ATBX_OT_named_selection_move,
    ATBX_OT_set_zbias,
    ATBX_OT_select_zbiased,
    ATBX_OT_batch_rename_vgrp,
    ATBX_OT_match_vgrp,
    ATBX_OT_add_selected_meshes,
    ATBX_OT_rem_selected_meshes,
    ATBX_MT_clear_mesh_collector,
    ATBX_MT_add_same_config_mesh_collector,
    ATBX_MT_add_any_config_mesh_collector,
    ATBX_MT_add_atleast_config_mesh_collector,
    ATBX_OT_add_del_vgroup,
    ATBX_OT_rem_del_vgroup,
    ATBX_MT_clear_del_vgroup,
    ATBX_OT_save_configs,
    ATBX_OT_load_configs,
    ATBX_OT_meshcollectify
)


def register():
    from bpy.utils import register_class
    for c in op_classes:
        register_class(c)

def unregister():
    from bpy.utils import unregister_class
    for c in op_classes:
        unregister_class(c)
        
