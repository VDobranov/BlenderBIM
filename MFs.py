import math
import ifcopenshell as ios
from ifcopenshell.api import run
from ifcopenshell.util import representation

f = '/Users/vdobranov/Yandex.Disk.localized/Работа/BlenderBIM/FRSAS.ifc'
f1 = '/Users/vdobranov/Yandex.Disk.localized/Работа/BlenderBIM/FRSAS1.ifc'

model = ios.open(f)

body = representation.get_context(model, "Model", "Body", "MODEL_VIEW")

# profile = model.by_type("IfcRectangleProfileDef")[0]
# element = model.by_type("IfcColumnType")[0]

# start = model.createIfcCartesianPoint([0.0, 0.0, 0.0])
# end = model.createIfcCartesianPoint([0.0, 1000.0, 5000.0])
dir_x = model.createIfcDirection([1.0, 0.0, 0.0])
dir_z = model.createIfcDirection([0.0, 0.0, 1.0])

# def create_IfcPolyline(Points):
#     return model.createIfcPolyline(Points)

# def create_IfcFixedReferenceSweptAreaSolid(SweptArea, Directrix, FixedReference):
#     return model.createIfcFixedReferenceSweptAreaSolid(SweptArea, None, Directrix, None, None, FixedReference)

def create_IfcSweptDiskSolid(Directrix, Radius):
    return model.createIfcSweptDiskSolid(Directrix, Radius, None, None, None)

def create_IfcCartesianPointList2D(L,l,R,d):
    ll = L-d/2
    r = R+d/2
    p1 = 0.0,0.0,0.0
    p2 = 0.0,0.0,0.0-ll+r
    p3 = r-r/math.sqrt(2),0.0,0.0-(ll-r+r/math.sqrt(2))
    p4 = r,0.0,0.0-ll
    p5 = d/2+l,0.0,0.0-ll
    return model.createIfcCartesianPointList3D([p1,p2,p3,p4,p5])

def create_Segments():
    s1 = model.createIfcLineIndex([1,2])
    s2 = model.createIfcArcIndex([2,3,4])
    s3 = model.createIfcLineIndex([4,5])
    return [s1,s2,s3]

def create_IfcIndexedPolyCurve(Points, Segments):
    return model.createIfcIndexedPolyCurve(Points, Segments)

def create_FoundationStud(L,l,R,d,l0):
    stud = run("root.create_entity", model, ifc_class="IfcMechanicalFastenerType", predefined_type="ANCHORBOLT", name=f"Шпилька 1.М{d}×{L}")
    # print(stud.Name)
    stud.NominalLength = L
    stud.NominalDiameter = d
    plist = create_IfcCartesianPointList2D(L,l,R,d)
    pcurve = create_IfcIndexedPolyCurve(plist, create_Segments())
    sds = create_IfcSweptDiskSolid(pcurve, d/2)
    representation = model.createIfcShapeRepresentation(
    ContextOfItems=body, RepresentationIdentifier="Body", RepresentationType="AdvancedSweptSolid", Items=[sds])
    offset = model.createIfcCartesianPoint([0.0,0.0,float(l0)])
    placement = model.createIfcAxis2placement3d(offset, dir_z, dir_x)
    representationmap = model.createIfcRepresentationMap(placement,representation)
    # run("geometry.assign_representation", model, product=stud, representation=representation)
    stud.RepresentationMaps = [representationmap]
    abolt = run("root.create_entity", model, ifc_class="IfcMechanicalFastenerType", predefined_type="ANCHORBOLT", name=f"Болт 1.1.М{d}×{L}")
    run("aggregate.assign_object", model, product=stud, relating_object=abolt)
    pset1 = run("pset.add_pset", model, product=abolt, name="Pset_MechanicalFastenerAnchorBolt")
    pset2 = run("pset.add_pset", model, product=abolt, name="Pset_ElementComponentCommon")
    pset3 = run("pset.add_pset", model, product=abolt, name="Pset_ManufacturerTypeInformation")
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
        "ModelLabel": f"Болт 1.1.М{d}×{L}",
        "AssemblyPlace": "SITE",
        "OperationalDocument": "ГОСТ 24379.1-2012"
        })


# create_FoundationStud(1320,60,20,20,500)
# create_FoundationStud(600,75,24,24,200)


#plist = model.createIfcCartesianPointList2D([[0.0,0.0], [1000.0,5000.0]])


# pline = create_IfcPolyline([start, end])
# frsas = create_IfcFixedReferenceSweptAreaSolid(profile, pline, dir_x)


# box = representation.get_context(model, "Model", "Box", "MODEL_VIEW")

#sweptsolid = representation.get_representation(element, "Model", "Body")
#run("geometry.unassign_representation", model, product=element, representation=sweptsolid)


gost = [[300, 40, 12, 12, 80],
[400, 40, 12, 12, 80],
[500, 40, 12, 12, 80],
[600, 40, 12, 12, 80],
[710, 40, 12, 12, 80],
[800, 40, 12, 12, 80],
[900, 40, 12, 12, 80],
[1000, 40, 12, 12, 80],
[300, 50, 16, 16, 90],
[400, 50, 16, 16, 90],
[500, 50, 16, 16, 90],
[600, 50, 16, 16, 90],
[710, 50, 16, 16, 90],
[800, 50, 16, 16, 90],
[900, 50, 16, 16, 90],
[1000, 50, 16, 16, 90],
[1120, 50, 16, 16, 90],
[1250, 50, 16, 16, 90],
[400, 60, 20, 20, 100],
[500, 60, 20, 20, 100],
[600, 60, 20, 20, 100],
[710, 60, 20, 20, 100],
[800, 60, 20, 20, 100],
[900, 60, 20, 20, 100],
[1000, 60, 20, 20, 100],
[1120, 60, 20, 20, 100],
[1250, 60, 20, 20, 100],
[1320, 60, 20, 20, 100],
[1400, 60, 20, 20, 100],
[500, 75, 24, 24, 110],
[600, 75, 24, 24, 110],
[710, 75, 24, 24, 110],
[800, 75, 24, 24, 110],
[900, 75, 24, 24, 110],
[1000, 75, 24, 24, 110],
[1120, 75, 24, 24, 110],
[1250, 75, 24, 24, 110],
[1320, 75, 24, 24, 110],
[1400, 75, 24, 24, 110],
[1500, 75, 24, 24, 110],
[1600, 75, 24, 24, 110],
[1700, 75, 24, 24, 110],
[600, 90, 30, 30, 120],
[710, 90, 30, 30, 120],
[800, 90, 30, 30, 120],
[900, 90, 30, 30, 120],
[1000, 90, 30, 30, 120],
[1120, 90, 30, 30, 120],
[1250, 90, 30, 30, 120],
[1320, 90, 30, 30, 120],
[1400, 90, 30, 30, 120],
[1500, 90, 30, 30, 120],
[1600, 90, 30, 30, 120],
[1700, 90, 30, 30, 120],
[1800, 90, 30, 30, 120],
[1900, 90, 30, 30, 120],
[2000, 90, 30, 30, 120],
[710, 110, 36, 36, 130],
[800, 110, 36, 36, 130],
[900, 110, 36, 36, 130],
[1000, 110, 36, 36, 130],
[1120, 110, 36, 36, 130],
[1250, 110, 36, 36, 130],
[1320, 110, 36, 36, 130],
[1400, 110, 36, 36, 130],
[1500, 110, 36, 36, 130],
[1600, 110, 36, 36, 130],
[1700, 110, 36, 36, 130],
[1800, 110, 36, 36, 130],
[1900, 110, 36, 36, 130],
[2000, 110, 36, 36, 130],
[2120, 110, 36, 36, 130],
[2240, 110, 36, 36, 130],
[2300, 110, 36, 36, 130],
[800, 125, 42, 42, 140],
[900, 125, 42, 42, 140],
[1000, 125, 42, 42, 140],
[1120, 125, 42, 42, 140],
[1250, 125, 42, 42, 140],
[1320, 125, 42, 42, 140],
[1400, 125, 42, 42, 140],
[1500, 125, 42, 42, 140],
[1600, 125, 42, 42, 140],
[1700, 125, 42, 42, 140],
[1800, 125, 42, 42, 140],
[1900, 125, 42, 42, 140],
[2000, 125, 42, 42, 140],
[2120, 125, 42, 42, 140],
[2240, 125, 42, 42, 140],
[2300, 125, 42, 42, 140],
[2360, 125, 42, 42, 140],
[2500, 125, 42, 42, 140],
[900, 150, 48, 48, 150],
[1000, 150, 48, 48, 150],
[1120, 150, 48, 48, 150],
[1250, 150, 48, 48, 150],
[1320, 150, 48, 48, 150],
[1400, 150, 48, 48, 150],
[1500, 150, 48, 48, 150],
[1600, 150, 48, 48, 150],
[1700, 150, 48, 48, 150],
[1800, 150, 48, 48, 150],
[1900, 150, 48, 48, 150],
[2000, 150, 48, 48, 150],
[2120, 150, 48, 48, 150],
[2240, 150, 48, 48, 150],
[2300, 150, 48, 48, 150],
[2360, 150, 48, 48, 150],
[2500, 150, 48, 48, 150],
[2650, 150, 48, 48, 150],
[2800, 150, 48, 48, 150]]

for f in gost:
    create_FoundationStud(f[0],f[1],f[2],f[3],f[4])

    
model.write(f1)