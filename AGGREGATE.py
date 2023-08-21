import math
import ifcopenshell as ios
from ifcopenshell.api import run
from ifcopenshell.util import representation

f = '/Users/vdobranov/Yandex.Disk.localized/Работа/BlenderBIM/TEMPLATE.ifc'
f1 = '/Users/vdobranov/Yandex.Disk.localized/Работа/BlenderBIM/AGGREGATE.ifc'

model = ios.open(f)

body = representation.get_context(model, "Model", "Body", "MODEL_VIEW")

placement3d = model.by_type("IfcAxis2Placement3D")[0]
placement2d = model.by_type("IfcAxis2Placement2D")[0]
dir_x = model.createIfcDirection([1.0, 0.0, 0.0])
dir_z = model.createIfcDirection([0.0, 0.0, 1.0])

def create_IfcArbitraryClosedProfileDef(ProfileName, OuterCurve):
    return model.createIfcArbitraryClosedProfileDef("AREA", ProfileName, OuterCurve)

def create_IfcArbitraryProfileDefWithVoids(ProfileName, OuterCurve, InnerCurves):
    return model.createIfcArbitraryProfileDefWithVoids("AREA", ProfileName, OuterCurve, InnerCurves)

def create_IfcExtrudedAreaSolid(SweptArea, Depth):
    return model.createIfcExtrudedAreaSolid(SweptArea, None, dir_z, Depth)

def create_IfcCartesianPointList2D(S):
    R = S/math.sqrt(3)
    p1 = 0.0, R
    p2 = S/2, R/2
    p3 = S/2, -R/2
    p4 = 0.0, -R
    p5 = -S/2, -R/2
    p6 = -S/2, R/2
    return model.createIfcCartesianPointList2D([p1,p2,p3,p4,p5,p6])

def create_Segments():
    s1 = model.createIfcLineIndex([1,2])
    s2 = model.createIfcLineIndex([2,3])
    s3 = model.createIfcLineIndex([3,4])
    s4 = model.createIfcLineIndex([4,5])
    s5 = model.createIfcLineIndex([5,6])
    s6 = model.createIfcLineIndex([6,1])
    return [s1,s2,s3,s4,s5,s6]

def create_IfcIndexedPolyCurve(Points, Segments):
    return model.createIfcIndexedPolyCurve(Points, Segments)\

def create_IfcCircle(Radius):
    return model.createIfcCircle(placement2d, Radius)

def create_FoundationWasher(d, d0, D, s):
    nut = run("root.create_entity", model, ifc_class="IfcMechanicalFastenerType", predefined_type="WASHER", name=f"Шайба М{d} ГОСТ 24379.1-2012")
    nut.NominalDiameter = d
    outerCircle = create_IfcCircle(D/2)
    innerCircle = create_IfcCircle(d0/2)
    profile = create_IfcArbitraryProfileDefWithVoids(f"Шайба М{d}", outerCircle, [innerCircle])
    eas = create_IfcExtrudedAreaSolid(profile, s)
    representation = model.createIfcShapeRepresentation(
    ContextOfItems=body, RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[eas])
    placement = placement3d
    representationmap = model.createIfcRepresentationMap(placement,representation)
    nut.RepresentationMaps = [representationmap]

ass = run("root.create_entity", model, ifc_class="IfcElementAssemblyType", name="assembly", predefined_type="ANCHORBOLT_GROUP")
bolt = run("root.create_entity", model, ifc_class="IfcMechanicalFastenerType", name="bolt", predefined_type="ANCHORBOLT")
nuttype = run("root.create_entity", model, ifc_class="IfcMechanicalFastenerType", name="nut", predefined_type="NUT")
nut1 = run("root.create_entity", model, ifc_class="IfcMechanicalFastener", name="nut", predefined_type="NUT")
nut2 = run("root.create_entity", model, ifc_class="IfcMechanicalFastener", name="nut", predefined_type="NUT")
run("type.assign_type", model, related_object=nut1, relating_type=nuttype)
run("type.assign_type", model, related_object=nut2, relating_type=nuttype)

run("aggregate.assign_object", model, product=nut1, relating_object=bolt)
run("aggregate.assign_object", model, product=nut2, relating_object=bolt)
run("aggregate.assign_object", model, product=bolt, relating_object=ass)

pset = run("pset.add_pset", model, product=bolt, name="Pset_MechanicalFastenerAnchorBolt")
run("pset.edit_pset", model, pset=pset, properties={"AnchorBoltLength": 1320})
    
model.write(f1)