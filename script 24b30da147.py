import bpy

import ifcopenshell
from ifcopenshell.api import run
from ifcopenshell.util import element

f = r'./aggregate_test.ifc'
f1 = r'./aggregate_test_.ifc'

model = ifcopenshell.open(f)

el = model.by_id(122)
sa = model.by_id(130)
a1 = model.by_id(138)
a2 = model.by_id(142)

point1 = model.createIfcCartesianPoint([0.,0.,-1000.])
point2 = model.createIfcCartesianPoint([1500.,2000.,0.])

dir = model.createIfcDirection([1.,1.,0.])
dir1 = model.createIfcDirection([1.,1.,1.])
dir2 = model.createIfcDirection([0.,-1.,0.])

# el.ObjectPlacement.RelativePlacement.Location = point1
# el.ObjectPlacement.RelativePlacement.Axis = dir

# sa.ObjectPlacement.RelativePlacement.Location = point2
# sa.ObjectPlacement.RelativePlacement.Axis = dir1

# a1.ObjectPlacement.RelativePlacement.Axis = dir2

# a2.ObjectPlacement.RelativePlacement.Location = point2
# a2.ObjectPlacement.RelativePlacement.Axis = dir








model.write(f1)

def load_ifc_automatically(f):
    if (bool(f)) == True:
        _collection=bpy.data.scenes[0].collection
        for _col in _collection.children_recursive:
            bpy.data.collections.remove(_col)

        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        bpy.ops.bim.load_project(filepath=f1, should_start_fresh_session=False)

load_ifc_automatically(model)