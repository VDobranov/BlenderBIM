import math
import ifcopenshell as ios
from ifcopenshell.api import run
from ifcopenshell.util import representation

f = '/Users/vdobranov/Yandex.Disk.localized/Работа/BlenderBIM/TEMPLATE.ifc'
f1 = '/Users/vdobranov/Yandex.Disk.localized/Работа/BlenderBIM/NUTS.ifc'

model = ios.open(f)

body = representation.get_context(model, "Model", "Body", "MODEL_VIEW")

start = model.by_type("IfcCartesianPoint")[0]
dir_x = model.createIfcDirection([1.0, 0.0, 0.0])
dir_z = model.createIfcDirection([0.0, 0.0, 1.0])

def create_IfcArbitraryClosedProfileDef(ProfileName, OuterCurve):
    return model.createIfcArbitraryClosedProfileDef("AREA", ProfileName, OuterCurve)

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
    return model.createIfcIndexedPolyCurve(Points, Segments)

def create_FoundationNut(d, S, m):
    nut = run("root.create_entity", model, ifc_class="IfcMechanicalFastenerType", predefined_type="NUT", name=f"Гайка М{d} ГОСТ 5915-70")
    nut.NominalDiameter = d
    plist = create_IfcCartesianPointList2D(S)
    pcurve = create_IfcIndexedPolyCurve(plist, create_Segments())
    profile = create_IfcArbitraryClosedProfileDef("Гайка М{d}", pcurve)
    eas = create_IfcExtrudedAreaSolid(profile, m)
    representation = model.createIfcShapeRepresentation(
    ContextOfItems=body, RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[eas])
    placement = model.createIfcAxis2placement3d(start, dir_z, dir_x)
    representationmap = model.createIfcRepresentationMap(placement,representation)
    nut.RepresentationMaps = [representationmap]

# create_FoundationNut(20,30,18)

gost = [[12, 18, 10.8],
[16, 24, 14.8],
[20, 30, 18],
[24, 36, 21.5],
[30, 46, 25.6],
[36, 55, 31],
[42, 65, 34],
[48, 75, 38]]

for f in gost:
    create_FoundationNut(f[0],f[1],f[2])
    
model.write(f1)