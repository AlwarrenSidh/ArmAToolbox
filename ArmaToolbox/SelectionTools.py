'''
Created on Sep 22, 2017

@author: hfrieden
'''

from bpy.types import Panel
import bpy
#from ArmaToolbox import ArmaToolboxGUIProps


class ArmaToolboxSelectionMaker(Panel):
    bl_label = "Arma Toolbox: Hidden Selection Maker"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        obj = context.active_object
        arma = obj.armaObjProps
        
        return context.active_object.active_material!=None and arma.isArmaObject == True

    def draw(self, context):
        guiProps = context.window_manager.armaGUIProps
        obj = bpy.context.active_object
        layout = self.layout
        layout.prop(guiProps, "hiddenSelectionName", text="Hidden Selection")