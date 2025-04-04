'''
Created on 21.02.2014

@author: hfrieden
'''

import bpy
import bpy_extras
import os
import math
import struct
import bmesh
from . import (
    ArmaTools,
    properties
)
import os.path as path


geometryLods = [
    '1.000e+13',
    '6.000e+15',
    '7.000e+15',
    '8.000e+15',
    '9.000e+15',
    '1.100e+16',
    '1.200e+16',
    '1.300e+16',
    '1.400e+16',
    '1.500e+16',
    '1.600e+16',
    '2.000e+13',
    '4.000e+13'
]

def getTempCollection():
    coll = bpy.data.collections.get("tempStuff")
    if (coll == None):
        coll = bpy.data.collections.new("tempStuff")
    return coll

def FixupResolution(lod, offset):
    if lod < 8.0e15:
        return lod+offset
    
    exp = format(lod, ".3e")
    expnt = exp[-2:]
    if expnt == "15":
        offs = format(offset, "02.0f")
        res = exp[0:2] + offs + "e+15"
        print("Fixup: lod = ", float(res), "string=",res,"offs = ", offs)
        return float(res)

    if expnt == '16':
        offs = format(offset, "02.0f")
        res = exp[0:3] + offs + "e+16"
        print("Fixup: lod = ", float(res), "string=", res, "offs = ", offs)
        return float(res)

    return float(exp)

def stripAddonPath(path):
    if path == "" or path == None: 
        return ""
    if os.path.isabs(path):
        p = os.path.splitdrive(path)
        return p[1][1:]
    elif path[0] == '\\':
        return path[1:]
    else:
        return path
    
    
def getMaterialInfo(face, obj):
    textureName = ""
    materialName = ""
    
    if face.material_index >= 0 and face.material_index < len(obj.material_slots):
        material = obj.material_slots[face.material_index].material

        if material == None:
            # print("****WARNING**** Polygon without assigned material in object ", obj.name)
            return("","#(argb,8,8,3)color(1,0,1,1)")

        texType = material.armaMatProps.texType;
    
        if texType == 'Texture':
            textureName = material.armaMatProps.texture;
            textureName = stripAddonPath(textureName);
        elif texType == 'Custom':
            textureName = material.armaMatProps.colorString;
        elif texType == 'Color':
            textureName = "#(argb,8,8,3)color({0:.3f},{1:.3f},{2:.3f},1.0,{3})".format( 
                material.armaMatProps.colorValue.r, 
                material.armaMatProps.colorValue.g, 
                material.armaMatProps.colorValue.b, 
                material.armaMatProps.colorType)

        materialName = stripAddonPath(material.armaMatProps.rvMat)
        
    
    return (materialName, textureName)

def lodKey(obj):
    if obj.armaObjProps.lod == "-1.0":
        return obj.armaObjProps.lodDistance
    elif ArmaTools.NeedsResolution(obj.armaObjProps.lod):
        return float(obj.armaObjProps.lod) + obj.armaObjProps.lodDistance
    else:
        return float(obj.armaObjProps.lod)

def convertWeight(weight):
    if weight > 1:
        weight = 1
    if weight < 0:
        weight = 0
    value = round(255 - 254 * weight)
    
    if value == 255:
        value = 0

    return value

def writeByte(filePtr, value):
    filePtr.write(struct.pack("B", value))

def writeSignature(filePtr, sig):
    filePtr.write(bytes(sig, "UTF-8"))

def writeULong(filePtr, value):
    filePtr.write(struct.pack("I", value))
    
def writeFloat(filePtr, value):
    filePtr.write(struct.pack("f", value))

def writeString(filePtr, value):
    data = value.encode('ASCII')
    packFormat = '<%ds' % (len(data) + 1)
    filePtr.write(struct.pack(packFormat, data))

def writeBytes(filePtr, value):
    filePtr.write(value)

###
## Export a single object as a LOD into the P3D file        
#
def OLDwriteNormals(filePtr, mesh, numberOfNormals):
    for v in range(0,numberOfNormals):
        writeFloat(filePtr, 0)
        writeFloat(filePtr, 1)
        writeFloat(filePtr, 0)
    
    #return v

# FaceNormals must be inverted (-X, -Y, -Z) for clockwise vertex order (default for DirectX), and not changed for counterclockwise order.
def writeNormals(filePtr, mesh, numberOfNormals):
    print("faces = ", len(mesh.polygons))
    if (4,1,0) > bpy.app.version:
        mesh.calc_normals_split()
    for poly in mesh.polygons:
        #print("index = ", poly.index)
        loops = poly.loop_indices
        for l in loops:
            normal = mesh.loops[l].normal
            writeFloat(filePtr, -normal[0])
            writeFloat(filePtr, -normal[1])
            writeFloat(filePtr, -normal[2])
            #print("normal = " , normal)

def writeVertices(filePtr, mesh):
    for v in mesh.vertices:
        writeFloat(filePtr, v.co.x)
        writeFloat(filePtr, v.co.z)
        writeFloat(filePtr, v.co.y)
        writeULong(filePtr, 0)



def writeFaces(filePtr, obj, mesh):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    fflayer = ArmaTools.getBMeshFaceFlags(bm)

    for idx,face in enumerate(mesh.polygons):
        faceFlags = bm.faces[idx][fflayer]

        if len(face.vertices) > 4:
            raise RuntimeError("Model " + obj.name + " contains n-gons and cannot be exported")
        materialName, textureName = getMaterialInfo(face, obj)
        writeULong(filePtr, len(face.vertices))

        # UV'S
        uvs = []
        for i1, loopindex in enumerate(face.loop_indices):
            meshloop = mesh.loops[i1]
            
            try:
                uv = mesh.uv_layers[0].data[loopindex].uv
            except IndexError:
                uv = [0,0]
            uvs.append([uv[0], uv[1]])

        for v in range(len(face.vertices)):
            writeULong(filePtr, face.vertices[v]) # vert id
            writeULong(filePtr, face.vertices[v]) # normal id
            uv = uvs[v]
            #print("u = ", uv[0], "v = ",uv[1])
            uv[1] = 1 - uv[1]
            writeFloat(filePtr, uv[0])
            writeFloat(filePtr, uv[1])
        
        if len(face.vertices) == 3:
            writeULong(filePtr, 0)
            writeULong(filePtr, 0)
            writeFloat(filePtr, 0.0)
            writeFloat(filePtr, 0.0)
        writeULong(filePtr, faceFlags)
        writeString(filePtr, textureName)
        writeString(filePtr, materialName)
    
    bm.free()

def proxyPathStrip(pathName):
    if len(pathName) > 3:
        if pathName[0].upper() == 'P' and pathName[1] == ':':
            pathName = pathName[2:]
    if pathName.find(".p3d") != -1:
        pathName = pathName[:-4]
    return pathName

def proxyIndex(index):
    return "%03d" % (index)

#
# This function is one of the reasons that export is slow (that and sharp edges).
#
# Possible idea to optimize: Instead of writing named selections one by one, go through the
# vertices one by one, enter each named selection into a dictionary and append the vertex index
# to the list of vertices. Then, cycle over the list and dump them.
#
# Potential issue: Memory consumption might be too high.
""" def writeNamedSelection(filePtr, obj, mesh, idx):
    name = obj.vertex_groups[idx].name
    writeByte(filePtr, 1) # Always active
    # Check the name for a proxy name
    if name in obj.armaObjProps.proxyArray:
        proxy = obj.armaObjProps.proxyArray[name]
        name = "proxy:" + proxyPathStrip(proxy.path) + "." + proxyIndex(proxy.index) 
    writeString(filePtr, name)
    writeULong(filePtr, len(mesh.vertices) + len(mesh.polygons))
    for vert in mesh.vertices:
        grps = [grp for grp in vert.groups if grp.group == idx]
        if len(grps) > 0: # Should only ever be 0 or 1
            weight = convertWeight(grps[0].weight)
            if weight < 0 or weight > 255:
                print("Illegal weight " , grps[0].weight, "in group " + name)
            writeByte(filePtr, weight)
        else:
            writeByte(filePtr, 0)
    
    for face in mesh.polygons:
        grps = [grp for vert in face.vertices for grp in mesh.vertices[vert].groups if grp.group == idx]
        if len(grps) == len(face.vertices):
            weight = 0
            for grpF in grps:
                weight += grpF.weight
            if (weight > 0):
                writeByte(filePtr, convertWeight(1))
            else:
                writeByte(filePtr, 0)
        else:
            writeByte(filePtr, 0) 

def OLDwriteNamedSelections(filePtr, obj, mesh):
    for idx in range(len(obj.vertex_groups)):
        writeNamedSelection(filePtr, obj, mesh, idx)
"""

def fullNameIfProxy(obj,name):
    if name in obj.armaObjProps.proxyArray:
        proxy = obj.armaObjProps.proxyArray[name]
        name = "proxy:" + proxyPathStrip(proxy.path) + "." + proxyIndex(proxy.index) 
    return name


def writeNamedSelections(filePtr, obj, mesh):
    # Build the array
    print("named selections: Building list of selections")
    selections = dict()
    selectionsFace = dict()
    for idx in range(len(obj.vertex_groups)):
        name = obj.vertex_groups[idx].name
        selections[name] = set()
        selectionsFace[name] = set()

    # We now go through all vertices and add their index to the appropriate groups
    print("named selections: Going through vertices")
    for vertex in mesh.vertices:
        groups = vertex.groups
        for group in groups:
            name = obj.vertex_groups[group.group].name
            weight = group.weight
            selections[name].add((vertex.index, weight))

    # Now, collect face related weights. This can be either of two conditions:
    # 1) The face is part of a Face Map
    # 2) The vertices of this face have a weight greater than zero.
    for face in mesh.polygons:
        # This will get all the group indices in the current face
        # Using a set will make sure they are unique
        groups = set([grp.group for vert in face.vertices for grp in mesh.vertices[vert].groups])
        for grpIdx in groups:
            weight = ([grp.weight>0 for vert in face.vertices for grp in mesh.vertices[vert].groups if grp.group == grpIdx])
            #print("weight = ",weight)
            if len(weight) == len(face.vertices):
                name = obj.vertex_groups[grpIdx].name
                selectionsFace[name].add(face.index)

    # At this point we can dump the array of groups into a file
    print("named selections: writing to disk")
    for name in selections:
        selName = fullNameIfProxy(obj, name)
        print(name, "->", selName)
        writeByte(filePtr, 1)
        writeString(filePtr, selName)
        writeULong(filePtr, len(mesh.vertices) + len(mesh.polygons))
        # Create a blob for the vertices and polygons
        vertBlob = bytearray(len(mesh.vertices))
        verts = selections[name]
        for v in verts:
            idx = v[0]
            weight = convertWeight(v[1])
            vertBlob[idx] = weight
        writeBytes(filePtr, vertBlob)
        # Polygons. TODO: use Face Map
        polyBlob = bytearray(len(mesh.polygons))
        faces = selectionsFace[name]
        for f in faces:
            polyBlob[f] = 1
        writeBytes(filePtr, polyBlob)
    print("named selections: done")

def writeSharpEdges(filePtr, mesh):
    # First, gather the edges of the flat shaded faces.
    edges = [edge for face in mesh.polygons if not face.use_smooth for edge in face.edge_keys]
    edges = sorted(set(edges))
    print("taggs: sharp edges - gather sharp edges")
    ###
    # OLD CODE - new code below
    ###
    # Gather the edges with the "sharp" flag set
    #edges2 = [edge for edge in mesh.edges if edge.use_edge_sharp]
    #print("taggs: sharp edges - find doubles")
    # We need to go through the edges to find the doubles.
    #for edge in edges2:
    #    v1 = edge.vertices[0]
    #    v2 = edge.vertices[1]
    #    if not (v1, v2) in edges and not (v2, v1) in edges:
    #        edges = edges + [(v1, v2)]
    
    ###
    # NEW CODE
    ###
    # ALternative approach: Insert the pairs of vertices into the edge list sorted, smallest index first
    # Turn the list into a set to eliminate doubles
    # turn it back into a list
    for edge in mesh.edges:
        if edge.use_edge_sharp:
            v1 = edge.vertices[0]
            v2 = edge.vertices[1]
            if v1 < v2:
                edges = edges + [(v1,v2)]
            else:
                edges = edges + [(v2,v1)]
    
    edge_set = set(edges)
    edges = list(edge_set)


    print("taggs: sharp edges - write them")
    if (len(edges) > 0): # Only write this if we have sharp edges
        writeByte(filePtr, 1)
        writeString(filePtr, '#SharpEdges#')
        writeULong(filePtr, len(edges) * 2 * 4)
        for edge in edges:
            writeULong(filePtr, edge[0])
            writeULong(filePtr, edge[1])



def writeMass(filePtr, obj, mesh):
    writeByte(filePtr, 1)
    writeString(filePtr, "#Mass#")
    totalVerts = len(mesh.vertices)
    writeULong(filePtr, totalVerts * 4)
    if (totalVerts > 0):
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        weight_layer = bm.verts.layers.float['FHQWeights']
        
        for i in range(0, len(bm.verts)):
            f = bm.verts[i][weight_layer]
            writeFloat(filePtr, f)
    


def writeNamedProperty(filePtr, name, value):
    writeByte(filePtr, 1)
    writeString(filePtr, "#Property#")
    writeULong(filePtr, 128)
    filePtr.write(struct.pack("<64s", name.encode("ASCII")))
    filePtr.write(struct.pack("<64s", value.encode("ASCII")))

""" def writeUVSet(filePtr, layer, mesh, obj, totalUVs, idx):
    writeByte(filePtr, 1)
    writeString(filePtr, "#UVSet#")
    writeULong(filePtr, 4+totalUVs * 8)
    writeULong(filePtr, idx)
    # Write UV Pairs
    for i, face in enumerate(mesh.polygons):
        for vertIdx in range(0, len(face.vertices)):
            uvPair = [0,0]
            try:
                uvPair = [uvPair for 
                    uvPair in 
                    mesh.uv_layers[idx].data[face.index].uv[vertIdx]]
            except Exception as e:
                #print(e)
                pass
            writeFloat(filePtr, uvPair[0])
            writeFloat(filePtr, 1-uvPair[1]) """

def writeUVSet(filePtr, layer, mesh, obj, totalUVs, idx):
    writeByte(filePtr, 1)
    writeString(filePtr, "#UVSet#")
    writeULong(filePtr, 4+totalUVs * 8)
    writeULong(filePtr, idx)
    # Write UV Pairs
    for i, polygon in enumerate(mesh.polygons):
        for vertIdx, loopindex in enumerate(polygon.loop_indices):
            meshloop = mesh.loops[vertIdx]
            try:
                uv = mesh.uv_layers[idx].data[loopindex].uv
            except:
                uv = [0,0]
            uvPair = [uv[0],uv[1]]
            writeFloat(filePtr, uvPair[0])
            writeFloat(filePtr, 1-uvPair[1])

def checkMass(obj, lod, mesh):
    # Check if the LOD is a geometry or physx, and add a dummy selection
    # if it doesn't exist.
    dummyName = "__BLENDER__Dummy"
    for idx in range(len(obj.vertex_groups)):
        name = obj.vertex_groups[idx].name
        if name == dummyName:
            return
    vgrp = obj.vertex_groups.new(dummyName)
    for idx in range(0,len(mesh.vertices)):
        vgrp.add([idx],1,'ADD')


def export_lod(filePtr, obj, wm, idx):
    ArmaTools.optimize_export_lod(obj)
    # Header
    writeSignature(filePtr, 'P3DM')
    writeULong(filePtr, 0x1C)
    writeULong(filePtr, 0x100)
    print("Write lod ",idx)
    wm.progress_update(idx*5)
    
    mesh = obj.data
    #mesh.calc_loop_triangles()
    
    lod = lodKey(obj)
    if lod < 0:
        lod = -lod
    
    print("lod = ", lod, properties.lodName(lod), obj.armaObjProps.lodDistance)

    #if lod == 1.000e+13 or lod == 4.000e+13:
    #    checkMass(obj, lod, mesh)

    numberOfNormals = 0
    for f in mesh.polygons:
        numberOfNormals = numberOfNormals + len(f.vertices)    
    
    print("Writing Vertices")    
    # Write number of vertices, normals, and faces
    writeULong(filePtr, len(mesh.vertices))         # Number of Vertices
    writeULong(filePtr, numberOfNormals)            # Number of Normals
    writeULong(filePtr, len(mesh.polygons))         # Number of Faces
    writeULong(filePtr, 0)                          # Unused Flags
    
    # Write vertices/Points
    writeVertices(filePtr, mesh)
    wm.progress_update(idx*5+1)
    
    print("Writing Normals")
    # Write normals
    # We can basically write whatever we like here since they are recalculated
    #normalOffsetInFile = filePtr.tell();
    writeNormals(filePtr, mesh, numberOfNormals)
    wm.progress_update(idx*5+2)
            
    print("Writing faces")
    # Write faces
    writeFaces(filePtr, obj, mesh)
    wm.progress_update(idx*5+3)


            
    # Done, now write Taggs
    writeSignature(filePtr, 'TAGG')
    print("taggs: Named selections")
    # Write named selections
    writeNamedSelections(filePtr, obj, mesh)
    print("taggs: sharp edges")
    # Write sharp edges. This isn't the most efficient, but I don't really see a better possibility
    writeSharpEdges(filePtr, mesh)
    wm.progress_update(idx*5+4)
    
    print("taggs: mass (if any)")
    # Write a mass selection if this is a Geometry or PhysX LOD
    if lod == 1.000e+13: # or lod == 4.000e+13:
        writeMass(filePtr, obj, mesh)

    print("taggs: named props")
    # Write named properties
    for prop in obj.armaObjProps.namedProps:
        name = prop.name
        value = prop.value
        writeNamedProperty(filePtr, name, value)
    
    print("taggs: uvsets")
    # Write UVSets
    # First, count the number of polygon vertices
    totalUVs = 0
    for face in mesh.polygons:
        totalUVs = totalUVs + len(face.vertices)
    
    uvt = mesh.uv_layers
    for i,layer in enumerate(uvt):
        print("Writing UV Set ", i)
        writeUVSet(filePtr, layer, mesh, obj, totalUVs, i)
    
        
    # Close off the LOD
    writeByte(filePtr, True)
    writeString(filePtr, '#EndOfFile#')
    writeULong(filePtr, 0)
    
    if ArmaTools.NeedsResolution(lod): ## FIXME: Is this correct?
        #print("---------->Needs resolution for lod ", format(lod, ".3e"), " results in ", format(FixupResolution(lod, obj.armaObjProps.lodDistance), ".3e"))
        writeFloat(filePtr, FixupResolution(lod,obj.armaObjProps.lodDistance))
    else:
        writeFloat(filePtr, lod)
    
    
def sameLod(objects, index):
    #print("index = ", index, "len = ", len(objects))
    if (index + 1) >= len(objects):
        return False
    obj = objects[index]
    obj2 = objects[index + 1]
    #print("sameLOD: ",obj.name_full, "/",obj.armaObjProps.lod, "/", obj.armaObjProps.lodDistance)
    #print("sameLOD:     ", obj2.name_full, "/", obj2.armaObjProps.lod, "/", obj2.armaObjProps.lodDistance)
    # Handle Shadows by lod
    #if lodKey(obj) == 1.000e+4 and lodKey(obj2) == 1.000e+4:
    if ArmaTools.NeedsResolution(obj.armaObjProps.lod) and ArmaTools.NeedsResolution(obj2.armaObjProps.lod):
        if obj.armaObjProps.lodDistance == obj2.armaObjProps.lodDistance and obj.armaObjProps.lod == obj2.armaObjProps.lod:
            #print(obj.name_full, "is same LOD as ", obj2.name_full)
            return True
        else:
            #print(obj.name_full, "is NOT same LOD as ", obj2.name_full)
            return False

    # normal compare
    if lodKey(obj) == lodKey(obj2):
        #print(obj.name_full, "is same LOD as ",obj2.name_full, "(no resolution)")
        return True

    print(obj.name_full, "is same LOD as ", obj2.name_full, "(no resolution)")
    return False

def duplicateObject(obj, applyModifier = True):
    print("duplicateObject: ", obj.name_full)
    newObj = obj.copy()
    newObj.data = obj.data.copy()

    # Copy Modifiers
    for mSrc in obj.modifiers:
        mDst = newObj.modifiers.get(mSrc.name, None)
        if not mDst:
            mDst = newObj.modifiers.new(mSrc.name, mSrc.type)

        # collect names of writable properties
        properties = [p.identifier for p in mSrc.bl_rna.properties
                    if not p.is_readonly]

        # copy those properties
        for prop in properties:
            setattr(mDst, prop, getattr(mSrc, prop))
    

    bpy.context.scene.collection.objects.link(newObj)
    instantiateMeshCollector(newObj)

    return newObj

# Here is how instantiating a mesh collector works
# We get a copy of the original object
# a. we copy each and every collected object
# b. we apply the collected object's modifiers
# c. we join the object into our object.
# TODO: d. if desired, delete specified vertex groups.
def instantiateMeshCollector(master, applyModifiers = True):
    objs = [x.object for x in master.armaObjProps.collectedMeshes]
    vgrpList = [x.vname for x in master.armaObjProps.collectedMeshesDelete]

    instances = []

    for o in objs:
        copied = duplicateObject(o)
        if applyModifiers:
            applyModifiersOnObject(copied)
        instances.append(copied)

    bpy.ops.object.select_all(action='DESELECT')
    for x in instances:
        x.select_set(True)
    
    master.select_set(True)
    bpy.context.view_layer.objects.active = master
    ArmaTools.joinObjectToObject(bpy.context)
    ArmaTools.deleteVertexGroupList(bpy.context, vgrpList)


def exportLodLevelWithModifiers(myself, filePtr, obj, wm, idx, applyModifiers, renumberComponents, applyTransforms, originObject):
    print("Exporting lod " , lodKey(obj), "of object", obj.name)
    coll = getTempCollection()
    print("------------------------------- Origin Object = ", originObject)
    if applyModifiers == False and originObject == None:
        # Simply export if we don't want to apply modifiers
        export_lod(filePtr, obj, wm, idx)
    else:
        # If we have modifiers, copy the object and apply them
        bpy.ops.object.select_all(action='DESELECT')
        #obj.select_set(True)
        #res = bpy.ops.object.duplicate()
        #if res != {'FINISHED'}:
        #    myself.report({'ERROR'}, "Failed to apply modifiers")
        #    return

        #tmpObj = bpy.context.selected_objects[0]
        tmpObj = duplicateObject(obj)
        coll.objects.link(tmpObj)

        if originObject != None:
            applyTransforms = True # this implies applyTransforms
            # Move/rotate/scale the temp object into position.
            tmpObj.location = originObject.location
            tmpObj.rotation_euler = originObject.rotation_euler
            tmpObj.scale = originObject.scale
            #print("***************** Applying new location for exported object")
            #bpy.ops.object.transform_apply(
            #            location=True, rotation=True, scale=True)
            #if (int(tmpObj.armaObjProps.lod) < 100):
            #    raise(ValueError)
            


        if applyModifiers:
            applyModifiersOnObject(tmpObj)
        if applyTransforms:
                    bpy.ops.object.transform_apply(
                        location=True, rotation=True, scale=True)
                        
        if renumberComponents:
            possiblyRenumberComponents(tmpObj)


        export_lod(filePtr, tmpObj, wm, idx)
        bpy.ops.object.delete()

def applyModifiersOnObject(tmpObj):
    bpy.context.view_layer.objects.active = tmpObj
    tmpObj.select_set(True)
    for mod in tmpObj.modifiers:
        print("--> Applying modifier " , mod.name, "on",tmpObj.name)
        bpy.ops.object.modifier_apply(modifier=mod.name)

def possiblyRenumberComponents(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if obj.armaObjProps.lod in geometryLods:
        print("Renumbering components on " + obj.name)
        ArmaTools.RenumberComponents(obj)

# Export a couple of meshes to a P3D MLOD files    
def exportMDL(myself, filePtr, selectedOnly, applyModifiers, mergeSameLOD, renumberComponents, applyTransforms):
    if selectedOnly:
        objects = [obj
                    for obj in bpy.context.selected_objects
                        if obj.type == 'MESH' and obj.armaObjProps.isArmaObject
                  ] 
    else:
        objects = [obj
                   for obj in bpy.data.objects
       
                       if (selectedOnly == False or obj.selected == True)
                          and obj.type == 'MESH'
                          and obj.armaObjProps.isArmaObject
                  ]

    if len(objects) == 0:
        return False
    
    exportObjectListAsMDL(myself, filePtr, applyModifiers,
                          mergeSameLOD, objects, renumberComponents, applyTransforms, None)

    return True


def exportObjectListAsMDL(myself, filePtr, applyModifiers, mergeSameLOD, objects, renumberComponents, applyTransforms, originObject):

    print("exportObjectListAsMDL: originObject =", originObject)

    objects = sorted(objects, key=lodKey)

    # Make sure the object is in OBJECT mode, otherwise some of the functions might fail
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # Write file header
    writeSignature(filePtr, 'MLOD')
    writeULong(filePtr, 0x101)
    writeULong(filePtr, len(objects))
    
    wm = bpy.context.window_manager
    total = len(objects) * 5
    wm.progress_begin(0, total)

    coll = getTempCollection()
    bpy.context.scene.collection.children.link(coll)
    

    if mergeSameLOD == False:

        #numLods = objects.__len__()

        # For each object, export a LOD
        for idx, obj in enumerate(objects):
            exportLodLevelWithModifiers(
                myself, filePtr, obj, wm, idx, applyModifiers, renumberComponents, applyTransforms, originObject)


    else:
        
        hasMeshCollector = False
        for ob in objects:
            if ob.armaObjProps.isMeshCollector:
                hasMeshCollector = True

        print("has mesh collector: ", hasMeshCollector)

        idx = 0
        while  idx < len(objects):
            obj = objects[idx]
            realIndex = idx
            print ("Considering object ", objects[idx].name)
            if sameLod(objects, idx) or hasMeshCollector:
                print ("There are objects to merge")
                # Copy this object and merge all subsequent objects of the same LOD
                newTmpObj = duplicateObject(obj)
                coll.objects.link(newTmpObj)
                mergedObjects = []
                if applyModifiers:
                    applyModifiersOnObject(newTmpObj)
                
                while sameLod(objects, idx):
                    idx = idx + 1
                    mergeObj = objects[idx]
                    newObj = duplicateObject(mergeObj)
                    coll.objects.link(newObj)
                    if applyModifiers:
                        applyModifiersOnObject(newObj)
                    mergedObjects.append(newObj)
                
                # Now, select all objects and make newTmpObj active
                bpy.ops.object.select_all(action='DESELECT')
                for x in mergedObjects:
                    x.select_set(True)

                newTmpObj.select_set(True)
                bpy.context.view_layer.objects.active = newTmpObj
                ArmaTools.joinObjectToObject(bpy.context)

                if originObject != None:
                    applyTransforms = True # this implies applyTransforms
                    # Move/rotate/scale the temp object into position.
                    newTmpObj.location = originObject.location
                    newTmpObj.rotation_euler = originObject.rotation_euler
                    newTmpObj.scale = originObject.scale

                if applyTransforms:
                    bpy.ops.object.transform_apply(
                        location=True, rotation=True, scale=True)

                export_lod(filePtr, newTmpObj, wm, realIndex)

                # Make sure we only have this one selected and delete it
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.view_layer.objects.active = newTmpObj
                newTmpObj.select_set(True)
                bpy.ops.object.delete()
            else:
                exportLodLevelWithModifiers(
                    myself, filePtr, obj, wm, idx, applyModifiers, renumberComponents, applyTransforms, originObject)
                    
            idx = idx + 1


    if coll:
        obs = [o for o in coll.objects if o.users == 1]
        while obs:
            bpy.data.objects.remove(obs.pop())

        bpy.data.collections.remove(coll)

    wm.progress_end()
        

def add_defined_export_configs(self, context):
    items = []
    scene = context.scene
    items.append(("-2", "All", ""))
    items.append(("-1", "Selected Only", ""))
    for item in scene.armaExportConfigs.exportConfigs.values():
        items.append((item.name, item.name, ""))

    return items

# Operators and Panels

class ATBX_PT_p3d_export_options(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Options"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        
        return operator.bl_idname == "ARMATOOLBOX_OT_export_p3d"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "config",
                    text="Export")
        layout.prop(operator, "applyModifiers")
        layout.prop(operator, "mergeSameLOD")
        layout.prop(operator, "renumberComponents")
        layout.prop(operator, "applyTransforms")

class ATBX_OT_p3d_export(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "armatoolbox.export_p3d"
    bl_label = "Export as P3D"
    bl_description = "Export as P3D"
    bl_options = {'PRESET'}

    filter_glob: bpy.props.StringProperty(
        default="*.p3d",
        options={'HIDDEN'})

    selectionOnly: bpy.props.BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=False)

    applyModifiers: bpy.props.BoolProperty(
        name="Apply Modifiers",
        description="Apply modifiers before export (experimental)",
        default=True)

    mergeSameLOD: bpy.props.BoolProperty(
        name="Merge Same LODs",
        description="Merge objects with the same LOD in exported file (experimental)",
        default=True)

    renumberComponents: bpy.props.BoolProperty(
        name="Re-Number Components in Geometry LODS",
        description="If set, geometry lods will get their components renumbered to be contiguous",
        default=True
    )

    applyTransforms: bpy.props.BoolProperty(
        name="Apply all transforms",
        description="Apply rotation, scale, and position transforms before exporting",
        default=True
    )

    specificConfig: bpy.props.StringProperty(
        name="Export Config",
        description = "Config to export"
    )

    config: bpy.props.EnumProperty(
        name="Export",
        description="What to export",
        items=add_defined_export_configs,
        default=0
    )

    filename_ext = ".p3d"

    def draw(self, context):
        pass

    def execute(self, context):

        if context.view_layer.objects.active == None:
            context.view_layer.objects.active = context.view_layer.objects[0]
        print("CONFIG: " + self.config)
        if self.config == "-1":
            self.selectionOnly = True
            objects = [obj
                       for obj in bpy.context.selected_objects
                       if obj.type == 'MESH' and obj.armaObjProps.isArmaObject
                       ]
            for o in objects:
                print("------" + o.name)
            filePtr = open(self.filepath, "wb")
            exportObjectListAsMDL(
                self, filePtr, self.applyModifiers, self.mergeSameLOD, objects, self.renumberComponents, self.applyTransforms, None)
            filePtr.close()

            ArmaTools.RunO2Script(context, self.filepath)
        elif self.config == "-2":
            #try:
            # Open the file and export
            filePtr = open(self.filepath, "wb")
            exportMDL(self, filePtr, False,
                    self.applyModifiers, self.mergeSameLOD, self.renumberComponents, self.applyTransforms)
            filePtr.close()

            ArmaTools.RunO2Script(context, self.filepath)

            
        else:
            print("Export config " + self.config)
            objs = ArmaTools.GetObjectsByConfig(self.config)
            print("Config: " + self.config)
            config = context.scene.armaExportConfigs.exportConfigs[self.config]
            fileName = self.filepath
            print("  exporting to " + fileName)
            try:
                filePtr = open(fileName, "wb")
                context.view_layer.objects.active = objs[0]
                exportObjectListAsMDL(
                    self, filePtr, self.applyModifiers, True, objs, self.renumberComponents, self.applyTransforms, config.originObject)
                filePtr.close()
                ArmaTools.RunO2Script(context, fileName)
            except:
                self.report({'ERROR'}, "Error writing file " + fileName +
                            " for config " + config.name + ":" + str(sys.exc_info()[0]))
                return {'CANCELLED'}
            
        return{'FINISHED'}

clses = (
    # Properties

    # Operators
    ATBX_OT_p3d_export,

    # Panels
    ATBX_PT_p3d_export_options,
)


def register():

    from bpy.utils import register_class

    for cs in clses:
        register_class(cs)


def unregister():

    from bpy.utils import unregister_class

    for cs in clses:
        unregister_class(cs)
