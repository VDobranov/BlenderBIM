import math
from typing import Any

import ifcopenshell as ios
from ifcopenshell import entity_instance, guid
from ifcopenshell.api import run
from ifcopenshell.util import representation
from ifcopenshell.util import element

f = './welded_profile.ifc'
f1 = './AGGREGATE_WELD_PROFILE.ifc'

model = ios.open(f)

body = representation.get_context(model, "Model", "Body", "MODEL_VIEW")
# history = model.by_type("IfcOwnerHistory")[0]

placement3d = model.by_type("IfcAxis2Placement3D")[0]
placement2d = model.by_type("IfcAxis2Placement2D")[0]
dir_x = model.by_id(8)
dir_z = model.by_id(7)

storey = model.by_type("IfcBuildingStorey")[0]

mechFasteners = model.by_type("IfcMechanicalFastenerType")
stud_type = [x for x in mechFasteners if x.ElementType == "STUD"][0]
nut_type = [x for x in mechFasteners if x.ElementType == "NUT"][0]
washer_type = [x for x in mechFasteners if x.ElementType == "WASHER"][0]

# print(washer_type.RepresentationMaps[0].MappedRepresentation.Items[0].Depth)

local_placements: dict[str, entity_instance]

def create_IfcArbitraryClosedProfileDef(ProfileName, OuterCurve):
    return model.createIfcArbitraryClosedProfileDef("AREA", ProfileName, OuterCurve)

def create_IfcArbitraryProfileDefWithVoids(ProfileName, OuterCurve, InnerCurves):
    return model.createIfcArbitraryProfileDefWithVoids("AREA", ProfileName, OuterCurve, InnerCurves)

def create_IfcExtrudedAreaSolid(SweptArea, Depth):
    return model.createIfcExtrudedAreaSolid(SweptArea, None, dir_z, Depth)

def create_IfcSweptDiskSolid(Directrix, Radius):
    return model.createIfcSweptDiskSolid(Directrix, Radius, None, None, None)

def create_IfcCartesianPointList2D_hexagon(S):
    R = S/math.sqrt(3)
    p1 = 0.0, R
    p2 = S/2, R/2
    p3 = S/2, -R/2
    p4 = 0.0, -R
    p5 = -S/2, -R/2
    p6 = -S/2, R/2
    return model.createIfcCartesianPointList2D([p1,p2,p3,p4,p5,p6])

def create_Segments_hexagon():
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

def create_FoundationStud(offset_height) -> entity_instance:
    stud = run("root.create_entity", model, ifc_class="IfcMechanicalFastener")
    local_placement = create_LocalPlacement(offset_height)
    run("type.assign_type", model, related_object=stud, relating_type=stud_type)
    run("geometry.edit_object_placement", model, product=stud)
    run("attribute.edit_attributes", model, product=stud, attributes={
        "Name": stud_type.Name,
        "ObjectPlacement": local_placement,
        "ObjectType": stud_type.ElementType,
        "PredefinedType": stud_type.PredefinedType,
        "NominalDiameter": stud_type.NominalDiameter,
        "NominalLength": stud_type.NominalLength
        })
    return stud

def create_FoundationNut(offset_height) -> entity_instance:
    nut = run("root.create_entity", model, ifc_class="IfcMechanicalFastener")
    local_placement = create_LocalPlacement(offset_height)
    run("type.assign_type", model, related_object=nut, relating_type=nut_type)
    run("attribute.edit_attributes", model, product=nut, attributes={
        "Name": nut_type.Name,
        "ObjectPlacement": local_placement,
        "ObjectType": nut_type.ElementType,
        "PredefinedType": nut_type.PredefinedType,
        "NominalDiameter": nut_type.NominalDiameter
        })
    return nut

def create_FoundationWasher(offset_height) -> entity_instance:
    washer = run("root.create_entity", model, ifc_class="IfcMechanicalFastener")
    local_placement = create_LocalPlacement(offset_height)
    run("type.assign_type", model, related_object=washer, relating_type=washer_type)
    run("attribute.edit_attributes", model, product=washer, attributes={
        "Name": washer_type.Name,
        "ObjectPlacement": local_placement,
        "ObjectType": washer_type.ElementType,
        "PredefinedType": washer_type.PredefinedType,
        "NominalDiameter": washer_type.NominalDiameter
        })
    return washer

def create_FoundationBoltType() -> entity_instance:
    bolt = run("root.create_entity", model, ifc_class="IfcMechanicalFastenerType", predefined_type="ANCHORBOLT", name=f"Bolt")
    offset_height = 100.
    stud = create_FoundationStud(offset_height)
    run("aggregate.assign_object", model, product=stud, relating_object=bolt)
    offset_height = washer_type.RepresentationMaps[0].MappedRepresentation.Items[0].Depth
    washer = create_FoundationWasher(offset_height)
    run("aggregate.assign_object", model, product=washer, relating_object=bolt)
    for n in range(2):
        offset_height += nut_type.RepresentationMaps[0].MappedRepresentation.Items[0].Depth
        nut = create_FoundationNut(offset_height)
        run("aggregate.assign_object", model, product=nut, relating_object=bolt)
    return bolt

def create_FoundationBolt() -> entity_instance:
    bolt = run("root.create_entity", model, ifc_class="IfcMechanicalFastener")
    run("type.assign_type", model, related_object=bolt, relating_type=bolt_type)
    run("aggregate.assign_object", model, product=bolt, relating_object=storey)
    # stud = bolt_type.IsDecomposedBy[0].RelatedObjects[3]
    # element.copy(model, element=stud)
    for el in bolt_type.IsDecomposedBy[0].RelatedObjects:
        new = element.copy(model, element=el)
        assign_object(related_object=new, relating_object=el)
        run("aggregate.assign_object", model, product=new, relating_object=bolt)
    run("attribute.edit_attributes", model, product=bolt, attributes={
        "Name": bolt_type.Name,
        "ObjectType": bolt_type.ElementType,
        "PredefinedType": bolt_type.PredefinedType
        })
    return bolt

def assign_object(related_object, relating_object):
    model.create_entity(
        "IfcRelDefinesByObject",
        **{
            "GlobalId": guid.new(),
            "OwnerHistory": run("owner.create_owner_history", model),
            "RelatedObjects": [related_object],
            "RelatingObject": relating_object,
        }
    )
    if getattr(relating_object, "RepresentationMaps", None):
        run(
            "type.map_type_representations",
            model,
            related_object=related_object,
            relating_object=relating_object,
        )
    type_material = element.get_material(relating_object)
    if not type_material:
        return
    if type_material.is_a("IfcMaterialLayerSet"):
        run(
            "material.assign_material",
            model,
            product=related_object,
            type="IfcMaterialLayerSetUsage",
        )
    elif type_material.is_a("IfcMaterialProfileSet"):
        run(
            "material.assign_material",
            model,
            product=related_object,
            type="IfcMaterialProfileSetUsage",
        )

bolt_type: entity_instance = create_FoundationBoltType()
create_FoundationBolt()

model.write(f1)