from typing import Any
import bpy # type: ignore
import math
# import numpy
import ifcopenshell as ios
from ifcopenshell import entity_instance
from ifcopenshell.api import run
from ifcopenshell.util import representation

f = './TEMPLATE.ifc'
# f = './TEMPLATE_2X3.ifc'
f1 = './AGGREGATE.ifc'

model: ios.file = ios.open(f)

body = representation.get_context(model, "Model", "Body", "MODEL_VIEW")
history = model.by_type("IfcOwnerHistory")[0]
site = model.by_type('IfcSite')[0]
storey = model.by_type('IfcBuildingStorey')[0]
origin = model.by_type('IfcCartesianPoint')[0]

placement3d = model.by_type("IfcAxis2Placement3D")[0]
placement2d = model.by_type("IfcAxis2Placement2D")[0]
dir_x = model.createIfcDirection([1.0, 0.0, 0.0])
dir_z = model.createIfcDirection([0.0, 0.0, 1.0])
# matrix = numpy.eye(4)

# material = model.by_type("IfcMaterial")

bolt_types: dict[str, entity_instance] = dict()
stud_types: dict[str, entity_instance] = dict()
nut_types: dict[str, entity_instance] = dict()
washer_types: dict[str, entity_instance] = dict()

bolt_dim: dict[str, list[float]] = dict()
nut_dim: dict[str, list[float]] = dict()
washer_dim: dict[str, list[float]] = dict()
exec(open('./DIM.py').read())

local_placements: dict[str, entity_instance] = dict()

# def create_IfcArbitraryClosedProfileDef(ProfileName: str, OuterCurve: entity_instance):
#     return model.createIfcArbitraryClosedProfileDef("AREA", ProfileName, OuterCurve)

def create_IfcArbitraryProfileDefWithVoids(ProfileName: str, OuterCurve: entity_instance, InnerCurves: list[entity_instance]) -> entity_instance:
    return model.createIfcArbitraryProfileDefWithVoids("AREA", ProfileName, OuterCurve, InnerCurves)

def create_IfcExtrudedAreaSolid(SweptArea: entity_instance, Depth: float) -> entity_instance:
    return model.createIfcExtrudedAreaSolid(SweptArea, None, dir_z, Depth)

def create_IfcSweptDiskSolid(Directrix, Radius) -> entity_instance:
    return model.createIfcSweptDiskSolid(Directrix, Radius, None, None, None)

def create_IfcCartesianPointList2D_stud(L,l,R,d) -> entity_instance:
    ll = L-d/2
    r = R+d/2
    p1 = 0.0,0.0,0.0
    p2 = 0.0,0.0,0.0-ll+r
    p3 = r-r/math.sqrt(2),0.0,0.0-(ll-r+r/math.sqrt(2))
    p4 = r,0.0,0.0-ll
    p5 = d/2+l,0.0,0.0-ll
    return model.createIfcCartesianPointList3D([p1,p2,p3,p4,p5])

def create_Segments_stud() -> list[entity_instance]:
    s1 = model.createIfcLineIndex([1,2])
    s2 = model.createIfcArcIndex([2,3,4])
    s3 = model.createIfcLineIndex([4,5])
    return [s1,s2,s3]

def create_IfcIndexedPolyCurve_stud(Points, Segments) -> entity_instance:
    return model.createIfcIndexedPolyCurve(Points, Segments)

def create_IfcCartesianPointList2D_hexagon(S) -> entity_instance:
    R = S/math.sqrt(3)
    p1 = 0.0, R
    p2 = S/2, R/2
    p3 = S/2, -R/2
    p4 = 0.0, -R
    p5 = -S/2, -R/2
    p6 = -S/2, R/2
    return model.createIfcCartesianPointList2D([p1,p2,p3,p4,p5,p6])

def create_Segments_hexagon() -> list[entity_instance]:
    s1 = model.createIfcLineIndex([1,2])
    s2 = model.createIfcLineIndex([2,3])
    s3 = model.createIfcLineIndex([3,4])
    s4 = model.createIfcLineIndex([4,5])
    s5 = model.createIfcLineIndex([5,6])
    s6 = model.createIfcLineIndex([6,1])
    return [s1,s2,s3,s4,s5,s6]

def create_IfcIndexedPolyCurve_hexagon(Points, Segments) -> entity_instance:
    return model.createIfcIndexedPolyCurve(Points, Segments)

def create_IfcCircle(Radius) -> entity_instance:
    return model.createIfcCircle(placement2d, Radius)

def create_LocalPlacement(offset) -> entity_instance:
    if f"{offset}" not in local_placements:
        offset = model.createIfcCartesianPoint([0.0,0.0,offset])
        placement = model.createIfcAxis2placement3d(offset, dir_z, dir_x)
        local_placement = model.createIfcLocalPlacement(None, placement)
        local_placements[f"{offset}"] = local_placement
    else:
        local_placement = local_placements[f"{offset}"]
    return local_placement

def create_FoundationStudType(L,l,R,d,l0):
    stud = run("root.create_entity", model, ifc_class="IfcMechanicalFastenerType", predefined_type="STUD", name=f"Шпилька 1.М{d}×{L} ГОСТ 24379.1-2012")
    # print(stud.Name)
    stud.NominalLength = L
    stud.NominalDiameter = d
    plist = create_IfcCartesianPointList2D_stud(L,l,R,d)
    pcurve = create_IfcIndexedPolyCurve_stud(plist, create_Segments_stud())
    sds = create_IfcSweptDiskSolid(pcurve, d/2)
    representation = model.createIfcShapeRepresentation(
    ContextOfItems=body, RepresentationIdentifier="Body", RepresentationType="AdvancedSweptSolid", Items=[sds])
    # offset = model.createIfcCartesianPoint([0.0,0.0,float(l0)])
    # placement = model.createIfcAxis2placement3d(offset, dir_z, dir_x)
    local_placement = create_LocalPlacement(float(l0))
    placement = local_placement.RelativePlacement
    representationmap = model.createIfcRepresentationMap(placement,representation)
    # run("geometry.assign_representation", model, product=stud, representation=representation)
    stud.RepresentationMaps = [representationmap]
    stud_types[f"{d}_{L}"] = stud

def create_FoundationNutType(d, S, m):
    nut = run("root.create_entity", model, ifc_class="IfcMechanicalFastenerType", predefined_type="NUT", name=f"Гайка М{d} ГОСТ 5915-70")
    nut.NominalDiameter = d
    plist = create_IfcCartesianPointList2D_hexagon(S)
    pcurve = create_IfcIndexedPolyCurve_hexagon(plist, create_Segments_hexagon())
    circle: entity_instance = create_IfcCircle(d/2)
    # profile = create_IfcArbitraryClosedProfileDef(f"Гайка М{d}", pcurve)
    profile = create_IfcArbitraryProfileDefWithVoids(f"Гайка М{d}", pcurve, [circle])
    eas = create_IfcExtrudedAreaSolid(profile, m)
    representation = model.createIfcShapeRepresentation(
    ContextOfItems=body, RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[eas])
    # placement = model.createIfcAxis2placement3d(placement3d, dir_z, dir_x)
    placement = placement3d
    representationmap = model.createIfcRepresentationMap(placement,representation)
    nut.RepresentationMaps = [representationmap]
    nut_types[f"{d}"] = nut

def create_FoundationWasherType(d, d0, D, s):
    washer = run("root.create_entity", model, ifc_class="IfcMechanicalFastenerType", predefined_type="WASHER", name=f"Шайба М{d} ГОСТ 24379.1-2012")
    washer.NominalDiameter = d
    outerCircle = create_IfcCircle(D/2)
    innerCircle = create_IfcCircle(d0/2)
    profile = create_IfcArbitraryProfileDefWithVoids(f"Шайба М{d}", outerCircle, [innerCircle])
    eas = create_IfcExtrudedAreaSolid(profile, s)
    representation = model.createIfcShapeRepresentation(
    ContextOfItems=body, RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[eas])
    placement = placement3d
    representationmap = model.createIfcRepresentationMap(placement,representation)
    washer.RepresentationMaps = [representationmap]
    washer_types[f"{d}"] = washer

def create_FoundationStud(d,L) -> entity_instance:
    stud_type = stud_types[f"{d}_{L}"]
    stud = run("root.create_entity", model, ifc_class="IfcMechanicalFastener")
    run("type.assign_type", model, related_objects=[stud], relating_type=stud_type)
    run("geometry.edit_object_placement", model, product=stud)
    run("attribute.edit_attributes", model, product=stud, attributes={
        "Name": stud_type.Name,
        "ObjectType": stud_type.ElementType,
        "PredefinedType": stud_type.PredefinedType,
        "NominalDiameter": stud_type.NominalDiameter,
        "NominalLength": stud_type.NominalLength
        })
    return stud

def create_FoundationNut(d,offset_height) -> entity_instance:
    nut_type = nut_types[f"{d}"]
    nut = run("root.create_entity", model, ifc_class="IfcMechanicalFastener")
    local_placement = create_LocalPlacement(offset_height)
    run("type.assign_type", model, related_objects=[nut], relating_type=nut_type)
    # run("geometry.edit_object_placement", model, product=nut, matrix=matrix, is_si=False)
    run("attribute.edit_attributes", model, product=nut, attributes={
        "Name": nut_type.Name,
        "ObjectPlacement": local_placement,
        "ObjectType": nut_type.ElementType,
        "PredefinedType": nut_type.PredefinedType,
        "NominalDiameter": nut_type.NominalDiameter
        })
    return nut

def create_FoundationWasher(d,offset_height) -> entity_instance:
    washer_type = washer_types[f"{d}"]
    washer = run("root.create_entity", model, ifc_class="IfcMechanicalFastener")
    local_placement = create_LocalPlacement(offset_height)
    run("type.assign_type", model, related_objects=[washer], relating_type=washer_type)
    run("attribute.edit_attributes", model, product=washer, attributes={
        "Name": washer_type.Name,
        "ObjectPlacement": local_placement,
        "ObjectType": washer_type.ElementType,
        "PredefinedType": washer_type.PredefinedType,
        "NominalDiameter": washer_type.NominalDiameter
        })
    return washer

def create_FoundationBoltType(L,d,l0):
    bolt = run("root.create_entity", model, ifc_class="IfcMechanicalFastenerType", predefined_type="ANCHORBOLT", name=f"Болт 1.1.М{d}×{L} ГОСТ 24379.1-2012")
    stud = create_FoundationStud(d,L)
    run("aggregate.assign_object", model, products=[stud], relating_object=bolt)
    offset_height = 30.
    washer = create_FoundationWasher(d,offset_height)
    run("aggregate.assign_object", model, products=[washer], relating_object=bolt)
    offset_height += washer_dim[f"{d}"][3]
    for n in range(2):
        nut = create_FoundationNut(d,offset_height)
        run("aggregate.assign_object", model, products=[nut], relating_object=bolt)
        offset_height += nut_dim[f"{d}"][2]
    pset1 = run("pset.add_pset", model, product=bolt, name="Pset_MechanicalFastenerAnchorBolt")
    pset2 = run("pset.add_pset", model, product=bolt, name="Pset_ElementComponentCommon")
    pset3 = run("pset.add_pset", model, product=bolt, name="Pset_ManufacturerTypeInformation")
    run("pset.edit_pset", model, pset=pset1, properties={
        "AnchorBoltLength": L,
        "AnchorBoltDiameter": d,
        "AnchorBoltThreadLength": l0,
        "AnchorBoltProtrusionLength": l0
        })
    run("pset.edit_pset", model, pset=pset2, properties={
        "Status": "NEW",
        "DeliveryType": "LOOSE",
        "CorrosionTreatment": "GALVANISED"
        })
    run("pset.edit_pset", model, pset=pset3, properties={
        "ModelLabel": f"Болт 1.1.М{d}×{L} ГОСТ 24379.1-2012",
        "AssemblyPlace": "SITE",
        "OperationalDocument": "ГОСТ 24379.1-2012"
        })
    bolt_types[f"{d}_{L}"] = bolt

def create_FoundationBolt(L,d,l0) -> entity_instance:
    bolt_type = bolt_types[f"{d}_{L}"]
    bolt = run("root.create_entity", model, ifc_class="IfcMechanicalFastener")
    run("type.assign_type", model, related_objects=[bolt], relating_type=bolt_type)
    run("geometry.edit_object_placement", model, product=bolt)
    run("attribute.edit_attributes", model, product=bolt, attributes={
        "Name": bolt_type.Name,
        "ObjectType": bolt_type.ElementType,
        "PredefinedType": bolt_type.PredefinedType
        })
    run("spatial.assign_container", model,products=[bolt],relating_structure=storey)
    stud = create_FoundationStud(d,L)
    run("aggregate.assign_object", model, products=[stud], relating_object=bolt)
    offset_height = 30.
    washer = create_FoundationWasher(d,offset_height)
    run("aggregate.assign_object", model, products=[washer], relating_object=bolt)
    offset_height += washer_dim[f"{d}"][3]
    for n in range(2):
        nut = create_FoundationNut(d,offset_height)
        run("aggregate.assign_object", model, products=[nut], relating_object=bolt)
        offset_height += nut_dim[f"{d}"][2]
    return bolt

# ass = run("root.create_entity", model, ifc_class="IfcElementAssemblyType", name="assembly", predefined_type="ANCHORBOLT_GROUP")

# create_FoundationStudType(1320,60,20,20,100)
# create_FoundationNutType(20, 30, 18)
# create_FoundationWasherType(20, 21, 45, 8)
# create_FoundationBoltType(1320,20,100)
# print(stud_types)
# print(nut_types)
# print(washer_types)

for v in nut_dim.values():
    create_FoundationNutType(v[0],v[1],v[2])
for v in washer_dim.values():
    create_FoundationWasherType(v[0],v[1],v[2],v[3])
for v in bolt_dim.values():
    create_FoundationStudType(v[0],v[1],v[2],v[3],v[4])
    create_FoundationBoltType(v[0],v[3],v[4])

diams_set: set[float] = set()
lengths_set: set[float] = set()
for v in bolt_dim.values():
    diams_set.add(v[3])
    lengths_set.add(v[0])

diams = sorted(diams_set)
lengths = sorted(lengths_set)

print(diams)
print(lengths)

gridpoints: dict[str, list[Any]] = {}
for d in diams:
    for l in lengths:
        gridpoints[f"{d}_{l}"] = [model.createIfcCartesianPoint([lengths.index(l)*200.,diams.index(d)*200.,0.]), d, l]

print(gridpoints)

for k in gridpoints.keys():
    if k in bolt_dim.keys():
        v = bolt_dim[k]
        _bolt = create_FoundationBolt(v[0],v[3],v[4])
        _placement = model.createIfcAxis2placement3d(gridpoints[k][0])
        _bolt.ObjectPlacement.RelativePlacement=_placement

# bolt = create_FoundationBolt(1000,20,100)

# _point=model.createIfcCartesianPoint([0.,2500.,0.])
# _placement = model.createIfcAxis2placement3d(_point)
# bolt.ObjectPlacement.RelativePlacement=_placement

grid = run("root.create_entity", model, ifc_class="IfcGrid")
run("spatial.assign_container", model, products=[grid], relating_structure=site)

for d in diams:
    axis = run("grid.create_grid_axis", model, axis_tag=f"M{d}", uvw_axes="UAxes", grid=grid)
    start = gridpoints[f"{d}_{min(lengths)}"][0]
    end = gridpoints[f"{d}_{max(lengths)}"][0]
    axis.AxisCurve = model.createIfcPolyline([start, end])

for l in lengths:
    axis = run("grid.create_grid_axis", model, axis_tag=f"{l}", uvw_axes="VAxes", grid=grid)
    start = gridpoints[f"{min(diams)}_{l}"][0]
    end = gridpoints[f"{max(diams)}_{l}"][0]
    axis.AxisCurve = model.createIfcPolyline([start, end])



model.write(f1)






def load_ifc_automatically(f):
    if (bool(f)) == True:
        # _project = f.by_type('IfcProject')
        _collection=bpy.data.scenes[0].collection # type: ignore
        for _col in _collection.children_recursive:
            bpy.data.collections.remove(_col) # type: ignore

        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True) # type: ignore
        bpy.ops.bim.load_project(filepath=f1, should_start_fresh_session=False) # type: ignore

# load_ifc_automatically(model)