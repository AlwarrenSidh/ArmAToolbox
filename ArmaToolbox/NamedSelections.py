
def NamSel_AddNew(obj, name):
    print("Add Name = ", name)

    vgrp = obj.vertex_groups.new(name=name)
    pname = vgrp.name

    prp = obj.armaObjProps.namedSelection
    item = prp.add()
    item.name = pname

    layerName = "SEL:" + pname
### TODO: Set index
    mesh = obj.data
    if layerName not in mesh.polygon_layers_float.keys():
        newLayer = mesh.polygon_layers_float.new(name=layerName)

def NamSel_Remove(obj, name):
    print("Remove Name = ", name)

def NamSel_UpdateName(obj, oldname, newname):
    print("Update obj ", obj, "old name " , oldname, " to new name ", newname)
    if oldname == None:
        return None # Initial creation, nothing to do

    try:
        grp = obj.vertex_groups.get(oldname)
    except:
        return None
    else:
        grp.name = newname
        return grp.name
    

    
    