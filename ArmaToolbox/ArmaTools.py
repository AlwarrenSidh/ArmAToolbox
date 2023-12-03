'''
Created on 16.01.2014

@author: hfrieden
'''

import bpy
import bmesh
from ArmaProxy import RebaseProxies, GetMaxProxy
import tempfile
from subprocess import call
import os

def bulkRename(context, frm, t):
    mats = bpy.data.materials
            
    for mat in mats:
        matProp = mat.armaMatProps
        
        if matProp.texture == frm:
            matProp.texture = t
        if matProp.rvMat == frm:
            matProp.rvMat = t
        if matProp.colorString == frm:
            matProp.colorString = t


def changeParentIf(origString, fromParent, toParent):
    if not origString.startswith(fromParent):
        return origString
    else:
        n = len(fromParent)
        return toParent + origString[n:]

def  bulkReparent(context, frm, t):
    mats = bpy.data.materials
            
    for mat in mats:
        matProp = mat.armaMatProps
        
        matProp.texture = changeParentIf(matProp.texture, frm, t)
        matProp.rvMat = changeParentIf(matProp.rvMat, frm, t)
        matProp.colorString = changeParentIf(matProp.colorString, frm, t)

def bulkRenameSelections(context, frm, t):
    for obj in bpy.data.objects:
        if obj.armaObjProps.isArmaObject:
            for vgroup in obj.vertex_groups:
                i  = vgroup.name.lower().find(frm.lower())
                if i != -1:
                    p1 = vgroup.name[:i]
                    p2 = vgroup.name[i+frm.__len__():]
                    vgroup.name = p1 + t + p2
                    
                    
translateTable = {
"otocvez":"main_turret",
"osaveze":"main_turret_axis",
"damagevez":"damage_main_turret",
"vez":"main_turret_hit",
"otochlaven":"main_gun",
"osahlavne":"main_gun_axis",
"damagehlaven":"damage_main_gun",
"recoilhlaven":"main_gun_recoil",
"recoilhlaven_axis":"main_gun_recoil_axis",
#"zbran":"main_gun_hit",
#"telo":"hull_hit",
#"zbytek":"hull_hit",
"brzdove svetlo":"light_brake",
"zadni svetlo":"light_rear",
"reverseLight":"light_reverse",
"palivo":"fuel_hit",
"motor":"engine_hit",
"otocvelitele":"commander_turret",
"osa velitele":"commander_turret_axis",
"vezvelitele":"commander_turret_hit",
"otochlavenvelitele":"commander_gun",
"osa hlavne velitele":"commander_gun_axis",
"zbranvelitele":"commander_gun_hit",
"koll1":"wheel_1_1",
"koll2":"wheel_1_9",
"pasoffsetl":"track_l",
"pas_l":"track_l_hit",
"kolp1":"wheel_2_1",
"kolp2":"wheel_2_9",
"pasoffsetp":"track_r",
"pas_p":"track_r_hit",
"poklop_driver":"hatch_driver",
"poklop_driver_axis":"hatch_driver_axis",
"poklop_commander":"hatch_commander",
"poklop_commander_axis":"hatch_commander_axis",
"poklop_gunner":"hatch_gunner",
"poklop_gunner_axis":"hatch_gunner_axis",
"usti hlavne":"muzzle_pos",
"konec hlavne":"muzzle_end",
"spice rakety":"missile_pos",
"konec rakety":"missile_end",
"doplnovani":"supply",
"zamerny":"aimpoint",
"kulas":"machinegun",
"damagehide":"damage_hide",
"driveroptics":"optics_driver",
"driveropticsout":"optics_driver_out",
"gunnverview":"optics_gunner",
"gunnerviewout":"optics_gunner_out",
"commanderview":"optics_commander",
"commanderviewout":"optics_commander_out",
"zasleh":"muzzleFlash"
}                    

def getTranslated(input):
    try:
        translate = translateTable[input.lower()]
        return translate
    except:
        return input

def autotranslateSelections():
    for obj in bpy.data.objects:
        if obj.armaObjProps.isArmaObject:
            for vgroup in obj.vertex_groups:
                name = vgroup.name.lower()
                translate = getTranslated(name)
                print (vgroup.name.lower(), translate)
                if name != translate:
                    vgroup.name = translate
                       

# These require more effort, I'll do them later when I get the time
#"podkoloL(#)":"wheel_1_(#+1)",
#"podkoloL(#)_hide":"wheel_1_(#+1)_hide",
#"podkoloP(#)":"wheel_2_(#+1)",
#"podkoloP(#)_hide":"wheel_2_(#+1)_hide",
#"stopa %%%":"track_%1_%2_%3",
#"vrtule%":"propeller_#",
#"osavrtule%":"propeller_#_axis",
#"usti hlavne #":"muzzle_#_pos",
#"konec hlavne #":"muzzle_#_end",


def mesh_to_weight_list(ob, me):
    """
    Takes a mesh and return its group names and a list of lists,
    one list per vertex.
    aligning the each vert list with the group names,
    each list contains float value for the weight.
    """

    # clear the vert group.
    group_names = [g.name for g in ob.vertex_groups]
    group_names_tot = len(group_names)

    if not group_names_tot:
        # no verts? return a vert aligned empty list
        return [], [[] for i in range(len(me.vertices))]
    else:
        weight_ls = [[0.0] * group_names_tot for i in range(len(me.vertices))]

    for i, v in enumerate(me.vertices):
        for g in v.groups:
            # possible weights are out of range
            index = g.group
            if index < group_names_tot:
                weight_ls[i][index] = g.weight

    return group_names, weight_ls


bonesTable = {
"Pelvis",
"Spine",
"Spine1",
"Spine2",
"Spine3",
"Camera",
"weapon",
"launcher",
"neck",
"neck1",
"head",
"Face_Hub",
"Face_Jawbone",
"Face_Jowl",
"Face_chopRight",
"Face_chopLeft",
"Face_LipLowerMiddle",
"Face_LipLowerLeft",
"Face_LipLowerRight",
"Face_Chin",
"Face_Tongue",
"Face_CornerRight",
"Face_CheekSideRight",
"Face_CornerLeft",
"Face_CheekSideLeft",
"Face_CheekFrontRight",
"Face_CheekFrontLeft",
"Face_CheekUpperRight",
"Face_CheekUpperLeft",
"Face_LipUpperMiddle",
"Face_LipUpperRight",
"Face_LipUpperLeft",
"Face_NostrilRight",
"Face_NostrilLeft",
"Face_Forehead",
"Face_BrowFrontRight",
"Face_BrowFrontLeft",
"Face_BrowMiddle",
"Face_BrowSideRight",
"Face_BrowSideLeft",
"Face_Eyelids",
"Face_EyelidUpperRight",
"Face_EyelidUpperLeft",
"Face_EyelidLowerRight",
"Face_EyelidLowerLeft",
"EyeLeft",
"EyeRight",        
"LeftShoulder",
"LeftArm",
"LeftArmRoll",
"LeftForeArm",
"LeftForeArmRoll",
"LeftHand",
"LeftHandRing",
"LeftHandRing1",
"LeftHandRing2",
"LeftHandRing3",
"LeftHandPinky1",
"LeftHandPinky2",
"LeftHandPinky3",
"LeftHandMiddle1",
"LeftHandMiddle2",
"LeftHandMiddle3",
"LeftHandIndex1",
"LeftHandIndex2",
"LeftHandIndex3",
"LeftHandThumb1",
"LeftHandThumb2",
"LeftHandThumb3",
"RightShoulder",
"RightArm",
"RightArmRoll",
"RightForeArm",
"RightForeArmRoll",
"RightHand",
"RightHandRing",
"RightHandRing1",
"RightHandRing2",
"RightHandRing3",
"RightHandPinky1",
"RightHandPinky2",
"RightHandPinky3",
"RightHandMiddle1",
"RightHandMiddle2",
"RightHandMiddle3",
"RightHandIndex1",
"RightHandIndex2",
"RightHandIndex3",
"RightHandThumb1",
"RightHandThumb2",
"RightHandThumb3",
"LeftUpLeg",
"LeftUpLegRoll",
"LeftLeg",
"LeftLegRoll",
"LeftFoot",
"LeftToeBase",
"RightUpLeg",
"RightUpLegRoll",
"RightLeg",
"RightLegRoll",
"RightFoot",
"RightToeBase",
}

def isBone(name):
    name = name.lower()
    for n in bonesTable:
        if n.lower() == name:
            return True
    return False

def selectOverweightVertices():
    obj = bpy.context.active_object
    mesh = obj.data
    if obj.armaObjProps.isArmaObject:
        
        bpy.ops.mesh.select_all(action = 'DESELECT')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        for v in mesh.vertices:
            grps = []
            for g in v.groups:
                grp = obj.vertex_groups[g.group]
                elem = [grp.name, g.weight]
                grps.append(elem)
                
            # Check for real bones in the groups
            num = 0
            for g in grps:
                if isBone(g[0]):
                    num = num + 1
            if num > 4:
                # print ("Vertex " + str(v.index) + " has " + str(num) + " bones")
                v.select = True
        
        bpy.ops.object.mode_set(mode = 'EDIT')
        

def pruneVertex(obj, v, num):
    while num > 4:
        # Find the bone vertex group with the lowest weight and remove the vertex from it.
        lowWeight = 5;
        lowIndex = -1 
        for g in v.groups:
            if g.weight < lowWeight and isBone(obj.vertex_groups[g.group].name):
                lowWeight = g.weight
                lowIndex = g.group
        if lowIndex == -1 or lowWeight > 0.5: 
            return # Can't prune this, weight might be too high
        else:
            grp = obj.vertex_groups[lowIndex]
            grp.remove([v.index])
            num = num - 1



        
def pruneOverweightVertices():
    obj = bpy.context.active_object
    mesh = obj.data
    if obj.armaObjProps.isArmaObject:
        
        bpy.ops.mesh.select_all(action = 'DESELECT')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
        for v in mesh.vertices:
            grps = []
            for g in v.groups:
                grp = obj.vertex_groups[g.group]
                elem = [grp.name, g.weight]
                grps.append(elem)
                
            # Check for real bones in the groups
            num = 0
            for g in grps:
                if isBone(g[0]):
                    num = num + 1
            if num > 4:
                #bpy.ops.object.mode_set(mode = 'EDIT')
                pruneVertex(obj, v, num)
                #bpy.ops.object.mode_set(mode = 'OBJECT')
        
        bpy.ops.object.mode_set(mode = 'EDIT')
        
def setVertexMass(obj, mass):
    # For some reason this might produce garbage if we do it twice in edit mode
    # so I am going out and back into edit mode once
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="EDIT")
    # End Workaround
    
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    try:
        weight_layer = bm.verts.layers.float['FHQWeights']
    except KeyError:
        weight_layer = bm.verts.layers.float.new('FHQWeights')
    
    for v in range(0, len(bm.verts)):
        if bm.verts[v].select:
            bm.verts[v][weight_layer] = mass
    
    bm.free()
    return

def distributeVertexMass(obj, mass):
    # For some reason this might produce garbage if we do it twice in edit mode
    # so I am going out and back into edit mode once
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="EDIT")
    # End Workaround
    
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    try:
        weight_layer = bm.verts.layers.float['FHQWeights']
    except KeyError:
        weight_layer = bm.verts.layers.float.new('FHQWeights')
   
    numSelected = 0
    
    for v in range(0, len(bm.verts)):
        if bm.verts[v].select:
            numSelected = numSelected + 1
    
    for v in range(0, len(bm.verts)):
        if bm.verts[v].select:
            bm.verts[v][weight_layer] = mass / numSelected
    
    bm.free()
    return

def mesh_to_weight_list(ob, me):
    """
    Takes a mesh and return its group names and a list of lists,
    one list per vertex.
    aligning the each vert list with the group names,
    each list contains float value for the weight.
    """

    # clear the vert group.
    group_names = [g.name for g in ob.vertex_groups]
    group_names_tot = len(group_names)

    if not group_names_tot:
        # no verts? return a vert aligned empty list
        return [], [[] for i in range(len(me.vertices))]
    else:
        weight_ls = [[0.0] * group_names_tot for i in range(len(me.vertices))]

    for i, v in enumerate(me.vertices):
        for g in v.groups:
            # possible weights are out of range
            index = g.group
            if index < group_names_tot:
                weight_ls[i][index] = g.weight

    return group_names, weight_ls

def attemptFixMassLod(obj):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    
    if "FHQWeights" not in bm.verts.layers.float.keys():
        weight_layer = bm.verts.layers.float.new('FHQWeights')
        
        # Check for the _BLENDER_DUMMY_
        vg = obj.vertex_groups.get('__BLENDER__Dummy')
        
        if vg is not None:
            obj.vertex_groups.remove(vg)
        
        verts = [0.0 for _ in bm.verts]
        totalVerts = len(bm.verts)
        
        grpNames, weightList = mesh_to_weight_list(obj, mesh)
    
        for n,grp in enumerate(grpNames):
            try:
                totalWeight = obj.armaObjProps.massArray[grp].weight
            except:
                totalWeight = obj.armaObjProps.mass / len(grpNames)
                
            totalVertsC = 0
            totalVertsM = 0.0
            for v in range(0,totalVerts):
                if weightList[v][n] > 0.0:
                    totalVertsC += 1
                    totalVertsM += weightList[v][n] 
            
            if totalVertsM > 0:
                for i in range(0, len(verts)):
                    verts[i] += (weightList[i][n] * totalWeight)/totalVertsM;
                
        for i in range(0, len(verts)):
            #print("verts[",i,"] = ", verts[i])
            bm.verts[i][weight_layer] =  verts[i]
        
        bm.to_mesh(obj.data)
        
def createComponents(context):
    
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_mode(type="VERT")
    
    # delete all old ComponentXX
    ob = bpy.context.active_object
    vgroup_names = {vgroup.index: vgroup.name for vgroup in ob.vertex_groups}

    for v in vgroup_names:
        grp = vgroup_names[v]
        if grp[:9] == "Component":
            bpy.ops.object.vertex_group_set_active(group=grp)
            bpy.ops.object.vertex_group_remove()

    componentNr = 1
    bpy.ops.mesh.select_all(action = 'DESELECT')
    
    for i in range(0,len(bpy.context.active_object.data.vertices)):
        if (bpy.context.active_object.data.vertices[i].hide == False):
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.context.active_object.data.vertices[i].select = True;
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_linked()
            bpy.ops.object.mode_set(mode="OBJECT")
            mesh = bpy.context.active_object.data;
            selected_verts = list(filter(lambda v: v.select, mesh.vertices))
            bpy.ops.object.mode_set(mode="EDIT")
            if (len(selected_verts) > 3):
                cmp = ("Component%02d" % componentNr)
                vgrp = bpy.context.active_object.vertex_groups.new(name=cmp)
                componentNr = componentNr + 1
                bpy.ops.object.vertex_group_assign()
            
            bpy.ops.mesh.hide()
            bpy.ops.object.mode_set(mode="OBJECT")
        
     
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.reveal()   
    bpy.ops.object.mode_set(mode="OBJECT")
    
    
def hitpointCreator(context, selection, radius):

    bpy.ops.object.mode_set(mode='OBJECT')

    ob = context.active_object
    mesh = ob.data
    selected_verts = [v for v in mesh.vertices if v.select]
    
    xmin = 100000000; ymin = xmin; zmin = xmin;
    xmax = -100000000; ymax = xmax; zmax = xmax;
    
    for vert in selected_verts:
        co = vert.co
        if co[0] < xmin:
            xmin = co[0]
            
        if co[0] > xmax:
            xmax = co[0]
            
        if co[1] < ymin:
            ymin = co[1]
            
        if co[1] > ymax:
            ymax = co[1]
            
        if co[2] < zmin:
            zmin = co[2]
            
        if co[2] > zmax:
            zmax = co[2]

    effective_diameter = radius

    xpoints = int(round((xmax - xmin) / (effective_diameter)))
    ypoints = int(round((ymax - ymin) / (effective_diameter)))
    zpoints = int(round((zmax - zmin) / (effective_diameter)))
    
    bm = bmesh.new()
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.delete()
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # convert the current mesh to a bmesh (must be in edit mode)
    bpy.ops.object.mode_set(mode='EDIT')
    bm.from_mesh(mesh)
    bpy.ops.object.mode_set(mode='OBJECT')  # return to object mode

    
    for xi in range(0,xpoints):
        for yi in range(0,ypoints):
            for zi in range(0,zpoints):
                x = effective_diameter + xmin + xi*effective_diameter
                y = effective_diameter + ymin + yi*effective_diameter
                z = effective_diameter + zmin + zi*effective_diameter
                
                v = [x,y,z]
                newV = bm.verts.new(v)
                newV.select = True
    
    bm.to_mesh(mesh)  
    bm.free()
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.active_object.vertex_groups.new(name=selection)
    bpy.ops.object.vertex_group_assign()
    return


def tessNonQuads(context):
    selectedOnly = False
    objects = [obj
            for obj in bpy.data.objects

                if (selectedOnly == False or obj.selected == True)
                    and obj.type == 'MESH'
                    and obj.armaObjProps.isArmaObject
            ]

    if len(objects) == 0:
        return False

    for obj in objects:
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_face_by_sides(number=4, type='GREATER')
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.select_set(False)


def messageReport(myop, message):
    myop.report({'INFO'}, message)
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

def optimizeSectionCount(context):
    obj = context.active_object
    optimizeSectionCountObj(obj)

def optimizeSectionCountObj(obj):
    tempGrpName = "-TOOLBOX_OPTIMIZE_TEMP"

    # Set to FACE select mode
    bpy.ops.mesh.select_mode(type="FACE", action="ENABLE")

    # create a vertex group with the current selection
    vgrp = bpy.context.active_object.vertex_groups.new(name=tempGrpName)
    bpy.ops.object.vertex_group_assign()

    # select all and sort mesh elements by Material
    bpy.ops.mesh.reveal() # Make sure everything is visible
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.sort_elements(type='MATERIAL', reverse=False)

    # select the vertex group only
    bpy.ops.mesh.select_all(action='DESELECT')                  # deselect all
    bpy.ops.object.vertex_group_set_active(group=tempGrpName)   # make sure our group is active
    bpy.ops.object.vertex_group_select()                        # select them

    # sort mesh elements by Selected, reverse
    bpy.ops.mesh.sort_elements(type='SELECTED', reverse=True)

    # delete vertex group again
    bpy.ops.object.vertex_group_remove()

def GetMaxComponents(objTarget):
    index = 0
    for v in objTarget.vertex_groups:
        name = v.name
        if name[:9] == "Component":
            x = int(name[9:])
            if x>index:
                index = x
    return index

# join objJoin to objTarget, merging the proxy arrays.
# Note that no comparison is made to verify that the
# objects are the same LOD
def joinObjectToObject(context):
    objTarget = context.active_object
    objsJoin = [obj for obj in context.selected_objects if obj != context.active_object]

    for objJoin in objsJoin:
        newSecondBase = GetMaxProxy(objTarget)
        if newSecondBase != -1:
            # Rebase proxies if the current object has any
            RebaseProxies(objJoin, newSecondBase+1)

        for p in objJoin.armaObjProps.proxyArray:
            n = objTarget.armaObjProps.proxyArray.add()
            n.name = p.name
            n.index = p.index
            n.path = p.path

        for np in objJoin.armaObjProps.namedProps:
            newnp = objTarget.armaObjProps.namedProps.add()
            newnp.name = np.name
            newnp.value = np.value

        if objJoin.armaObjProps is not None:
            if objJoin.armaObjProps.lod in ['1.000e+13','6.000e+15','7.000e+15','8.000e+15','9.000e+15','1.100e+16','1.200e+16','1.300e+16','1.400e+16','1.500e+16','1.600e+16','2.000e+13','4.000e+13']:
                for v in objJoin.vertex_groups:
                    name = v.name
                    if name[:9] == "Component":
                        v.name = name + "_" + objJoin.name



    bpy.ops.object.join()
    RenumberComponents(objTarget)


def selectBadUV(self, context, maxAngleDiff = 0.001):
    bm = bmesh.from_edit_mesh(context.active_object.data)
    uv_layers = bm.loops.layers.uv.verify()

    bpy.ops.uv.select_all(action='DESELECT')

    for face in bm.faces:
        loops = len(face.loops)

        for i in range(loops):
            i2 = (i + 1) % loops
            i3 = (i + 2) % loops
            a = face.loops[i].vert.co - face.loops[i2].vert.co
            b = face.loops[i].vert.co - face.loops[i3].vert.co

            uva = face.loops[i][uv_layers].uv - face.loops[i2][uv_layers].uv
            uvb = face.loops[i][uv_layers].uv - face.loops[i3][uv_layers].uv

            if a.length > 0 and b.length > 0:
                wa = a.angle(b)
            else:
                wa = 1000

            if uva.length > 0 and uvb.length > 0:
                ua = uva.angle(uvb)
            else:
                ua = 0

            if (abs(wa - ua) > maxAngleDiff):
                face.loops[i][uv_layers].select = True
                face.loops[i2][uv_layers].select = True
                face.loops[i3][uv_layers].select = True

def markTransparency(self, context, transparent):
    # FIXME: Needed?
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="EDIT")

    bm = bmesh.from_edit_mesh(context.active_object.data)
    if "FHQTransparency" not in bm.faces.layers.int.keys():
        trlayer = bm.faces.layers.int.new('FHQTransparency')
    else:
        trlayer = bm.faces.layers.int["FHQTransparency"]

    for face in bm.faces:
        if face.select:
            face[trlayer] = transparent


def selectTransparency(self, context, selectIndex = 1):
    selectTransparencyObj(context.active_object, selectIndex)


def selectTransparencyObj(obj, selectIndex = 1):
    bm = bmesh.from_edit_mesh(obj.data)
    if "FHQTransparency" not in bm.faces.layers.int.keys():
        trlayer = bm.faces.layers.int.new('FHQTransparency')
    else:
        trlayer = bm.faces.layers.int["FHQTransparency"]

    for face in bm.faces:
        if face[trlayer] == selectIndex:
            face.select = True
        else:
            face.select = False

    bmesh.update_edit_mesh(obj.data)

def optimize_export_lod(obj):
    # ? bpy.context.scene.objects.active = obj
    obj.select_set(True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')

    selectTransparencyObj(obj)
    optimizeSectionCountObj(obj)

    # Sort different transparency priorities, from high to low.
    pri = 6
    while pri > 0:
        selectTransparencyObj(obj, pri)
        bpy.ops.mesh.sort_elements(type='SELECTED', reverse=True)
        pri = pri - 1


    # select faces for the opposite site
    selectTransparencyObj(obj, -1)
    # sort mesh elements by Selected, reverse
    bpy.ops.mesh.sort_elements(type='SELECTED', reverse=False)

    bpy.ops.object.mode_set(mode='OBJECT')

def PostProcessLOD(obj):
    print("PostProcessLOD enter")
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)

    if "FHQTransparency" not in bm.faces.layers.int.keys():
        trlayer = bm.faces.layers.int.new('FHQTransparency')
    else:
        trlayer = bm.faces.layers.int["FHQTransparency"]

    for face in bm.faces:
        matIndex = face.material_index
        if matIndex != -1 and obj.material_slots.__len__() != 0:
            material = obj.material_slots[matIndex].material
            if material != None:
                ap = material.armaMatProps
                if ap.texType == 'Texture':
                    if ap.texture.find("_ca.") != -1:
                        face[trlayer] = 1
                elif ap.texType == 'Color':
                    if ap.colorType == 'CA':
                        face[trlayer] = 1
                elif ap.texType == 'Custom':
                    if ap.colorString.find("#(argb") != -1:
                        face[trlayer] = 1
                        
    bm.to_mesh(me)
    bm.free()
    print("PostProcessLOD exit")

def RenumberComponents(obj, baseIndex = 1):
    index = 1
    for grp in obj.vertex_groups:
        if grp.name[:9] == "Component":
            grp.name = "__TOOLBOX_TEMP__" + str(index)
            index = index + 1

    index = baseIndex
    for grp in obj.vertex_groups:
        if grp.name[:16] == "__TOOLBOX_TEMP__":
            grp.name = "Component{num:02d}".format(num=index)
            index = index + 1

def GetObjectsByConfig(configName):
    objects = []

    for obj in bpy.data.objects:
        if obj.armaObjProps != None:
            if obj.armaObjProps.isArmaObject == True:
                arma = obj.armaObjProps
                if configName in arma.exportConfigs.keys() or arma.alwaysExport == True:
                    objects.append(obj)

    return objects

def RunO2Script(context, fileName):
    # Write a temporary O2script file for this
    filePtr = tempfile.NamedTemporaryFile("w", delete=False)
    tmpName = filePtr.name
    filePtr.write("p3d = newLodObject;\n")
    filePtr.write('_res = p3d loadP3D "%s";\n' % (fileName))
    filePtr.write("_res = p3d setActive 4e13;")
    filePtr.write('save p3d;\n')
    filePtr.close()

    user_preferences = context.preferences
    addon_prefs = user_preferences.addons["ArmaToolbox"].preferences
    command = addon_prefs.o2ScriptProp
    command = '"' + command + '" "' + tmpName + '"'
    call(command, shell=True)
    os.remove(tmpName)

def NeedsResolution(lod):
    lodPresetsNeedingResolution = [
        
        '-1.0',     # 'Custom', 'Custom Viewing Distance'),
        '1.200e+3',  # 'View Cargo', 'View Cargo'),
        '1.000e+4', # 'Stencil Shadow', 'Stencil Shadow'),
        '1.001e+4', # 'Stencil Shadow 2', 'Stencil Shadow 2'),
        '1.100e+4', # 'Shadow Volume', 'Shadow Volume'),
        '1.101e+4', # 'Shadow Volume 2', 'Shadow Volume 2'),
        '8.000e+15', # 'View Cargo Geometry', 'View Cargo Geometry'),
        '1.800e+16', # 'Shadow Volume - View Cargo', 'Cargo View shadow volume'),
        '2.000e+4',  # 'Edit', 'Edit'),
    ]

    if type(lod) == type(0.0):
        return FloatNeedsResolution(lod)

    if lod in lodPresetsNeedingResolution:
        return True
    else:
        return False


def FloatNeedsResolution(lod):
    lodPresetsNeedingResolution = [

        '-1.0',     # 'Custom', 'Custom Viewing Distance'),
        '1.200e+03',  # 'View Cargo', 'View Cargo'),
        '1.000e+04',  # 'Stencil Shadow', 'Stencil Shadow'),
        '1.001e+04',  # 'Stencil Shadow 2', 'Stencil Shadow 2'),
        '1.100e+04',  # 'Shadow Volume', 'Shadow Volume'),
        '1.101e+04',  # 'Shadow Volume 2', 'Shadow Volume 2'),
        '8.000e+15',  # 'View Cargo Geometry', 'View Cargo Geometry'),
        '1.800e+16',  # 'Shadow Volume - View Cargo', 'Cargo View shadow volume'),
        '2.000e+04',  # 'Edit', 'Edit'),
    ]

    lod = format(lod, ".3e")

    if lod in lodPresetsNeedingResolution:
        return True
    else:
        return False

def GetVertexGroupsForVertex(obj, vertex):
    groupNames = []
    for grp in obj.data.vertices[vertex].groups:
        if grp.weight > 0:
            index = grp.group
            groupNames.append(obj.vertex_groups[index].name)

    return groupNames

def GetFirstVertexOfGroup(obj, groupName):
    groupIndex = obj.vertex_groups.find(groupName)
    if groupIndex == -1:
        return -1

    for v in obj.data.vertices:
        for g in v.groups:
            if g.group == groupIndex:
                return v.index
    
    return -1


def testBatchCondition(guiProps, configList, obj):
    if guiProps.bex_applyAll:
        return True

    # Test if the guiProps set up config batch operation matches the object
    if guiProps.bex_choice == 'any':
        for conf in guiProps.bex_exportConfigs:
            arma = obj.armaObjProps
            if conf.name in arma.exportConfigs.keys() or arma.alwaysExport == True:
                return True
    elif guiProps.bex_choice == 'all':
        ret = True
        for conf in guiProps.bex_exportConfigs:
            arma = obj.armaObjProps
            if not (conf.name in arma.exportConfigs.keys() or arma.alwaysExport == True):
                ret = False
                break
        return ret
    elif guiProps.bex_choice == 'exact':
        
        arma = obj.armaObjProps
        for name in configList.keys():
            inObj = name in arma.exportConfigs.keys()
            inList = name in guiProps.bex_exportConfigs.keys()
            if inObj != inList:
                return False
        return True

    return False

def getBMeshFaceFlags(bmesh):
    if "FHQFaceFlags" not in bmesh.faces.layers.int.keys():
        fflayer = bmesh.faces.layers.int.new('FHQFaceFlags')
    else:
        fflayer = bmesh.faces.layers.int["FHQFaceFlags"]

    return fflayer

def selectFaceFlags(self, context, flags, mask):
    selectFaceFlagsObj(context.active_object, flags, mask)

def selectFaceFlagsObj(obj, flags, mask):
    bm = bmesh.from_edit_mesh(obj.data)
    fflayer = getBMeshFaceFlags(bm)

    for face in bm.faces:
        if face[fflayer] & mask == flags:
            face.select = True
        else:
            face.select = False

    bmesh.update_edit_mesh(obj.data)


def setFaceFlags(self, context, flags, mask):
    # FIXME: Needed?
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="EDIT")

    bm = bmesh.from_edit_mesh(context.active_object.data)
    fflayer = getBMeshFaceFlags(bm)

    for face in bm.faces:
        if face.select:
            fl = face[fflayer] & ~mask
            face[fflayer] = fl | flags

def matchAllConfigs(context, mainObject, testObject):
    mainArma = mainObject.armaObjProps
    testArma = testObject.armaObjProps

    if not testArma.isArmaObject: 
        return False
    
    ## Generate the list of configs to check against
    ## On always export, use the list of all configs
    mainConfigs = mainArma.exportConfigs.keys()
    if mainArma.alwaysExport:
        mainConfigs = context.scene.armaExportConfigs.exportConfigs.keys()
    testConfigs = testArma.exportConfigs.keys()
    if testArma.alwaysExport:
        testConfigs = context.scene.armaExportConfigs.exportConfigs.keys()
    configs = context.scene.armaExportConfigs.exportConfigs.keys()

    for c in configs:
        if c in mainConfigs and c not in testConfigs:
            return False
        if c not in mainConfigs and c in testConfigs:
            return False

    return True

def matchAnyConfigs(context, mainObject, testObject):
    mainArma = mainObject.armaObjProps
    testArma = testObject.armaObjProps

    if not testArma.isArmaObject: 
        return False
    
    ## Generate the list of configs to check against
    ## On always export, use the list of all configs
    mainConfigs = mainArma.exportConfigs.keys()
    if mainArma.alwaysExport:
        mainConfigs = context.scene.armaExportConfigs.exportConfigs.keys()
    testConfigs = testArma.exportConfigs.keys()
    if testArma.alwaysExport:
        testConfigs = context.scene.armaExportConfigs.exportConfigs.keys()
    
    for c in mainConfigs:
        if c in testConfigs:
            return True
        
    return False

def matchAtLeastConfigs(context, mainObject, testObject):
    mainArma = mainObject.armaObjProps
    testArma = testObject.armaObjProps

    if not testArma.isArmaObject: 
        return False
    
    ## Generate the list of configs to check against
    ## On always export, use the list of all configs
    mainConfigs = mainArma.exportConfigs.keys()
    if mainArma.alwaysExport:
        mainConfigs = context.scene.armaExportConfigs.exportConfigs.keys()
    testConfigs = testArma.exportConfigs.keys()
    if testArma.alwaysExport:
        testConfigs = context.scene.armaExportConfigs.exportConfigs.keys()
    
    for c in mainConfigs:
        if c not in testConfigs:
            return False
        
    return True

def deleteVertexGroupList(context, vgrpList):
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.mode_set(mode="EDIT")

    o = context.active_object
    if o is None:
        print ("No Object Selected")
        return
    
    for v in vgrpList:
        if o.vertex_groups.get(v) is not None:
            o.vertex_groups.active = o.vertex_groups[v]
            bpy.ops.mesh.select_all( action = 'DESELECT' )
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.delete(type='VERT')

    bpy.ops.object.mode_set(mode="OBJECT")

def findNamedSelectionString(obj, selectionName):
    index = obj.armaObjProps.namedProps.find(selectionName)
    
    if index is -1: 
        return None

    output = obj.armaObjProps.namedProps[selectionName]
    
    if len(output.value) is 0:
        return None
    
    return output.value