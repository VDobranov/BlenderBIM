import bpy

from dataclasses import dataclass, field, asdict
from typing import Callable, Optional, Any

import ifcopenshell
import ifcopenshell.api
from ifcopenshell.api import run
from ifcopenshell.util import element
from ifcopenshell.util import representation
from ifcopenshell.util.shape_builder import V
import ifcpatch


@dataclass
class IfcOpenShellPythonAPI:
    """Helper class to make use of pythonic notation with the IfcOpenShell API
    standard use -> ifcopenshell.api.run('root.create_entity', file, ifc_class='IfcWall')
    instantiating this class as "ios" -> ios.root.create_entity(file, ifc_class='IfcWall')"""

    module_stack: list[str] = field(default_factory=list)

    def __getattr__(self, module: str) -> Optional[Callable]:
        if module == 'shape' or module.startswith('_'):
            return  # weird PyCharm and/or JupyterLab silent calls
        self.module_stack.append(module)
        return self

    def __call__(self, *args, **kwargs) -> Any:
        try:
            result: Any = ifcopenshell.api.run('.'.join(self.module_stack), *args, **kwargs)
        except Exception as err:
            raise err
        finally:
            self.reset()
        return result

    def reset(self) -> None:
        self.module_stack = []

ios = IfcOpenShellPythonAPI()

# f = r'H:\BBIM\aggregate_tests.ifc'
# f1 = r'H:\BBIM\aggregate_tests_.ifc'

f = r'./aggregate_tests.ifc'
f1 = r'./aggregate_test.ifc'

model = ifcopenshell.open(f)
body = representation.get_context(model, "Model", "Body", "MODEL_VIEW")
builder = ifcopenshell.util.shape_builder.ShapeBuilder(model)

origin = model.by_type("IfcCartesianPoint")[0]
dir_z = model.by_type("IfcDirection")[0]
dir_x = model.by_type("IfcDirection")[1]
placement3d = model.by_type("IfcAxis2Placement3D")[0]
placement2d = model.by_type("IfcAxis2Placement2D")[0]
dir_y = model.createIfcDirection([0.0, 1.0, 0.0])

storey = model.by_type('IfcBuildingStorey')[0]
plate_type = model.by_type('IfcPlateType')[0]
insu_type = model.by_type('IfcBuildingElementPartType')[0]
slab_type = model.by_type('IfcSlabType')[0]

def createLocalPlacement(refplacement=None, point=origin, up=dir_z, forward=dir_x):
    if up == forward:
        if up == dir_z: forward = dir_x
        if up == dir_x: forward = dir_y
        if up == dir_y: forward = dir_z
    if point != origin or up != dir_z or forward != dir_x:
        placement = model.createIfcAxis2placement3d(point, up, forward)
        local_placement = model.createIfcLocalPlacement(refplacement, placement)
    else:
        local_placement = model.createIfcLocalPlacement(refplacement, placement3d)
    return local_placement

def createRectangle(XDim=100.,YDim=100.):
    for prof in model.by_type("IfcRectangleProfileDef"):
        if prof.XDim == XDim and prof.YDim == YDim:
            return prof
    return model.createIfcRectangleProfileDef("AREA",XDim=XDim,YDim=YDim,ProfileName=f"{int(XDim)}×{int(YDim)}")

def createExtrudedAreaSolid(SweptArea, Depth):
    for eas in model.by_type("IfcExtrudedAreaSolid"):
        if eas.SweptArea == SweptArea and eas.Depth == Depth:
            return eas
    return model.createIfcExtrudedAreaSolid(SweptArea, None, dir_z, Depth)

def createPlate(profile):
    plate = ios.root.create_entity(model,ifc_class="IfcPlate")
    _layerThickness = plate_type.HasAssociations[0].RelatingMaterial.MaterialLayers[0].LayerThickness
    eas = createExtrudedAreaSolid(profile, _layerThickness)
    representation = model.createIfcShapeRepresentation(ContextOfItems=body, RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[eas])
    # representation = ios.geometry.add_profile_representation(model,context=body,profile=profile,depth=_layerThickness,unit_scale=.001)
    ios.geometry.assign_representation(model, product=plate, representation=representation)
    ios.type.assign_type(model,related_object=plate,relating_type=plate_type)
    # _relAggregates = ios.aggregate.assign_object(model,product=plate,relating_object=storey)
    # _aggregatePlacement = _relAggregates.RelatingObject.ObjectPlacement
    ios.spatial.assign_container(model,product=plate,relating_structure=storey)
    _spatialPlacement = plate.ContainedInStructure[0].RelatingStructure.ObjectPlacement
    plateXDim = representation.Items[0].SweptArea.XDim
    plateYDim = representation.Items[0].SweptArea.YDim
    _origin=model.createIfcCartesianPoint([plateXDim/2,plateYDim/2,0.])
    local_placement = createLocalPlacement(refplacement=_spatialPlacement,point=_origin)
    ios.attribute.edit_attributes(model, product=plate, attributes={
        "Name": f"Sheet {profile.ProfileName}",
        "ObjectPlacement": local_placement,
        "PredefinedType": plate_type.PredefinedType,
    })
    return plate

def createInsu(profile):
    insu = ios.root.create_entity(model,ifc_class="IfcBuildingElementPart")
    _layerThickness = insu_type.HasAssociations[0].RelatingMaterial.MaterialLayers[0].LayerThickness
    eas = createExtrudedAreaSolid(profile, _layerThickness)
    representation = model.createIfcShapeRepresentation(ContextOfItems=body, RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[eas])
    ios.geometry.assign_representation(model, product=insu, representation=representation)
    ios.type.assign_type(model,related_object=insu,relating_type=insu_type)
    ios.spatial.assign_container(model,product=insu,relating_structure=storey)
    _spatialPlacement = insu.ContainedInStructure[0].RelatingStructure.ObjectPlacement
    insuXDim = representation.Items[0].SweptArea.XDim
    insuYDim = representation.Items[0].SweptArea.YDim
    _origin=model.createIfcCartesianPoint([insuXDim/2,insuYDim/2,0.])
    local_placement = createLocalPlacement(refplacement=_spatialPlacement,point=_origin)
    ios.attribute.edit_attributes(model, product=insu, attributes={
        "Name": f"Insulation {int(_layerThickness)}",
        "ObjectPlacement": local_placement,
        "PredefinedType": insu_type.PredefinedType,
    })
    return insu

def createSlab(profile):
    slab = ios.root.create_entity(model,ifc_class="IfcSlab")
    _layerThickness = slab_type.HasAssociations[0].RelatingMaterial.MaterialLayers[0].LayerThickness
    eas = createExtrudedAreaSolid(profile, _layerThickness)
    representation = model.createIfcShapeRepresentation(ContextOfItems=body, RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[eas])
    ios.geometry.assign_representation(model, product=slab, representation=representation)
    ios.type.assign_type(model,related_object=slab,relating_type=slab_type)
    ios.spatial.assign_container(model,product=slab,relating_structure=storey)
    _spatialPlacement = slab.ContainedInStructure[0].RelatingStructure.ObjectPlacement
    slabXDim = representation.Items[0].SweptArea.XDim
    slabYDim = representation.Items[0].SweptArea.YDim
    _origin=model.createIfcCartesianPoint([slabXDim/2,slabYDim/2,0.])
    local_placement = createLocalPlacement(refplacement=_spatialPlacement,point=_origin)
    ios.attribute.edit_attributes(model, product=slab, attributes={
        "Name": f"Slab {int(_layerThickness)}",
        "ObjectPlacement": local_placement,
        "PredefinedType": slab_type.PredefinedType,
    })
    return slab

def createSubAssm(type):
    subassm = ios.root.create_entity(model,ifc_class="IfcElementAssembly")
    ios.type.assign_type(model,related_object=subassm,relating_type=type)
    ios.spatial.assign_container(model,product=subassm,relating_structure=storey)
    _spatialPlacement = subassm.ContainedInStructure[0].RelatingStructure.ObjectPlacement
    local_placement = createLocalPlacement(refplacement=_spatialPlacement)
    ios.attribute.edit_attributes(model, product=subassm, attributes={
        "Name": type.Name,
        "ObjectPlacement": local_placement,
        "PredefinedType": type.PredefinedType,
    })
    copyPartsFromType(subassm,type)
    return subassm

def createAssm(type):
    assm = ios.root.create_entity(model,ifc_class="IfcElementAssembly")
    ios.type.assign_type(model,related_object=assm,relating_type=type)
    ios.spatial.assign_container(model,product=assm,relating_structure=storey)
    _spatialPlacement = assm.ContainedInStructure[0].RelatingStructure.ObjectPlacement
    local_placement = createLocalPlacement(refplacement=_spatialPlacement)
    ios.attribute.edit_attributes(model, product=assm, attributes={
        "Name": type.Name,
        "ObjectPlacement": local_placement,
        "PredefinedType": type.PredefinedType,
    })
    copyPartsFromType(assm,type)
    return assm

def copyPartsFromType(elem, type):
    if len(type.IsDecomposedBy) > 0:
        for part in type.IsDecomposedBy[0].RelatedObjects:
            new = element.copy(model, element=part)
            assign_object(related_object=new, relating_object=part)
            aggregate_assign_object(product=new, relating_object=elem)
            new.ObjectPlacement = createLocalPlacement(elem.ObjectPlacement)
            new.ObjectPlacement.RelativePlacement = part.ObjectPlacement.RelativePlacement
            print(f"{part} > {new}")
            copyPartsFromType(new, part)
    

def aggregate_assign_object(product, relating_object):
    if len(relating_object.IsDecomposedBy) > 0:
        _relObjs = list(relating_object.IsDecomposedBy[0].RelatedObjects)
        _relObjs.append(product)
        relating_object.IsDecomposedBy[0].RelatedObjects = tuple(_relObjs)
        _relAggr = relating_object.IsDecomposedBy[0]
    else:
        _relAggr = ios.root.create_entity(model, ifc_class="IfcRelAggregates")
        _relAggr.RelatingObject = relating_object
        _relAggr.RelatedObjects = [product]
#    if hasattr(relating_object, "ObjectPlacement"):
#        product.ObjectPlacement.PlacementRelTo = relating_object.ObjectPlacement
#    else:
#        product.ObjectPlacement.PlacementRelTo = None
    return _relAggr

def assign_object(related_object, relating_object):
    if len(relating_object.Declares) > 0:
        _relObjs = list(relating_object.Declares[0].RelatedObjects)
        _relObjs.append(related_object)
        relating_object.Declares[0].RelatedObjects = tuple(_relObjs)
    else:
        model.create_entity(
            "IfcRelDefinesByObject",
            **{
                "GlobalId": ifcopenshell.guid.new(),
                "OwnerHistory": ios.owner.create_owner_history(model),
                "RelatedObjects": [related_object],
                "RelatingObject": relating_object,
            }
        )
    if getattr(relating_object, "RepresentationMaps", None):
        ios.type.map_type_representations(
            model,
            related_object=related_object,
            relating_object=relating_object,
        )
    type_material = element.get_material(relating_object)
    if not type_material:
        return
    if type_material.is_a("IfcMaterialLayerSet"):
        ios.material.assign_material(
            model,
            product=related_object,
            type="IfcMaterialLayerSetUsage",
        )
    elif type_material.is_a("IfcMaterialProfileSet"):
        ios.material.assign_material(
            model,
            product=related_object,
            type="IfcMaterialProfileSetUsage",
        )


prof1 = createRectangle(500.,1000.)
prof2 = createRectangle(500.,500.)
prof3 = createRectangle(536.,1000.)
prof4 = createRectangle(500.,964.)
prof5 = createRectangle(2500.,2000.)
# createExtrudedAreaSolid(prof1,18.)
plate1=createPlate(prof3)
plate2=createPlate(prof1)
plate3=createPlate(prof1)
plate4=createPlate(prof2)
plate5=createPlate(prof2)
plate1.ObjectPlacement.RelativePlacement.Location.Coordinates=(268.,500.,0.)
plate2.ObjectPlacement.RelativePlacement.Axis=dir_x
plate2.ObjectPlacement.RelativePlacement.RefDirection=dir_z
plate2.ObjectPlacement.RelativePlacement.Location.Coordinates=(0.,500.,268.)
plate3.ObjectPlacement.RelativePlacement.Axis=dir_x
plate3.ObjectPlacement.RelativePlacement.RefDirection=dir_z
plate3.ObjectPlacement.RelativePlacement.Location.Coordinates=(518.,500.,268.)
plate4.ObjectPlacement.RelativePlacement.Axis=dir_y
plate4.ObjectPlacement.RelativePlacement.RefDirection=dir_z
plate4.ObjectPlacement.RelativePlacement.Location.Coordinates=(268.,0.,268.)
plate5.ObjectPlacement.RelativePlacement.Axis=dir_y
plate5.ObjectPlacement.RelativePlacement.RefDirection=dir_z
plate5.ObjectPlacement.RelativePlacement.Location.Coordinates=(268.,982.,268.)
insu=createInsu(prof4)
insu.ObjectPlacement.RelativePlacement.Location.Coordinates=(268.,500.,18.)

subassm_type = ios.root.create_entity(model,ifc_class="IfcElementAssemblyType")
subassm_type.Name="Sub-Assembly"
subassm_type.PredefinedType="ACCESSORY_ASSEMBLY"

aggregate_assign_object(product=plate1,relating_object=subassm_type)
aggregate_assign_object(product=plate2,relating_object=subassm_type)
aggregate_assign_object(product=plate3,relating_object=subassm_type)
aggregate_assign_object(product=plate4,relating_object=subassm_type)
aggregate_assign_object(product=plate5,relating_object=subassm_type)
aggregate_assign_object(product=insu,relating_object=subassm_type)

subassm1 = createSubAssm(subassm_type)
subassm2 = createSubAssm(subassm_type)

#_point=model.createIfcCartesianPoint([500.,500.,500.])
_dir=model.createIfcDirection([1.,1.,0.])
#_placement = model.createIfcAxis2placement3d(_point, dir_z, _dir)
_point=model.createIfcCartesianPoint([500.,500.,0.])
_placement = model.createIfcAxis2placement3d(_point)
subassm1.ObjectPlacement.RelativePlacement=_placement
_point=model.createIfcCartesianPoint([1500.,500.,0.])
_placement = model.createIfcAxis2placement3d(_point)
subassm2.ObjectPlacement.RelativePlacement=_placement

#insu.ObjectPlacement.RelativePlacement.Location.Coordinates=[268.,500.,500.]

slab=createSlab(prof5)
slab.ObjectPlacement.RelativePlacement.Location.Coordinates=(1250.,1000.,-100.)

assm_type = ios.root.create_entity(model,ifc_class="IfcElementAssemblyType")
assm_type.Name="Assembly"
assm_type.PredefinedType="ACCESSORY_ASSEMBLY"

aggregate_assign_object(product=subassm1,relating_object=assm_type)
aggregate_assign_object(product=subassm2,relating_object=assm_type)
aggregate_assign_object(product=slab,relating_object=assm_type)

assm1 = createAssm(assm_type)
_placement = model.createIfcAxis2placement3d(origin)
assm1.ObjectPlacement.RelativePlacement=_placement

assm2 = createAssm(assm_type)
_point=model.createIfcCartesianPoint([0.,2500.,0.])
_placement = model.createIfcAxis2placement3d(_point)
assm2.ObjectPlacement.RelativePlacement=_placement

#subassm1.ObjectPlacement.RelativePlacement.RefDirection = _dir




model = ifcpatch.execute({
    "input": "input.ifc",
    "file": model,
    "recipe": "Optimise",
    "arguments": [],
})

#relassmat = model.by_type("IfcRelAssociatesMaterial")[1]
#for ram in model.by_type("IfcRelAssociatesMaterial")[2:]:
#    if ram.RelatingMaterial == relassmat.RelatingMaterial:
#        _ramRO = list(relassmat.RelatedObjects)
#        _ramRO += ram.RelatedObjects
#        relassmat.RelatedObjects = tuple(_ramRO)
#        model.remove(ram)












model.write(f1)



def load_ifc_automatically(f):
    if (bool(f)) == True:
        _project = f.by_type('IfcProject')
        
#        if _project != None:
#            for i in _project:
#                _collection_name = 'IfcProject/' + i.Name
#                
#                _collection = bpy.data.collections.get(_collection_name)
#                
#                if _collection != None:
#                    for _obj in _collection.all_objects:
#                        bpy.data.objects.remove(_obj, do_unlink=True)
#                    for _col in _collection.children_recursive:
#                        bpy.data.collections.remove(_col)
#                    bpy.data.collections.remove(_collection)
        
        _collection=bpy.data.scenes[0].collection
#       for _obj in _collection.all_objects:
#           bpy.data.objects.remove(_obj, do_unlink=True)
        for _col in _collection.children_recursive:
            bpy.data.collections.remove(_col)

        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        bpy.ops.bim.load_project(filepath=f1, should_start_fresh_session=False)

load_ifc_automatically(model)