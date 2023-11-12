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

f = r'./aggregate_tests.ifc'
f1 = r'./aggregate_tests_.ifc'

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
    if hasattr(relating_object, "ObjectPlacement"):
        product.ObjectPlacement.PlacementRelTo = relating_object.ObjectPlacement
    else:
        product.ObjectPlacement.PlacementRelTo = None
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
# createExtrudedAreaSolid(prof1,18.)
plate1=createPlate(prof1)
plate2=createPlate(prof1)
plate3=createPlate(prof1)
plate4=createPlate(prof2)
plate5=createPlate(prof2)
plate2.ObjectPlacement.RelativePlacement.Axis=dir_x
plate2.ObjectPlacement.RelativePlacement.RefDirection=dir_z
plate2.ObjectPlacement.RelativePlacement.Location.Coordinates=(0.,500.,250.)
plate3.ObjectPlacement.RelativePlacement.Axis=dir_x
plate3.ObjectPlacement.RelativePlacement.RefDirection=dir_z
plate3.ObjectPlacement.RelativePlacement.Location.Coordinates=(500.,500.,250.)
plate4.ObjectPlacement.RelativePlacement.Axis=dir_y
plate4.ObjectPlacement.RelativePlacement.RefDirection=dir_z
plate4.ObjectPlacement.RelativePlacement.Location.Coordinates=(250.,0.,250.)
plate5.ObjectPlacement.RelativePlacement.Axis=dir_y
plate5.ObjectPlacement.RelativePlacement.RefDirection=dir_z
plate5.ObjectPlacement.RelativePlacement.Location.Coordinates=(250.,1000.,250.)

assm_type = ios.root.create_entity(model,ifc_class="IfcElementAssemblyType")
assm_type.Name="Sub-Assembly"
assm_type.PredefinedType="ACCESSORY_ASSEMBLY"

aggregate_assign_object(product=plate1,relating_object=assm_type)
aggregate_assign_object(product=plate2,relating_object=assm_type)
aggregate_assign_object(product=plate3,relating_object=assm_type)
aggregate_assign_object(product=plate4,relating_object=assm_type)
aggregate_assign_object(product=plate5,relating_object=assm_type)

assm = ios.root.create_entity(model,ifc_class="IfcElementAssembly")
ios.type.assign_type(model,related_object=assm,relating_type=assm_type)
ios.spatial.assign_container(model,product=assm,relating_structure=storey)
_spatialPlacement = assm.ContainedInStructure[0].RelatingStructure.ObjectPlacement
local_placement = createLocalPlacement(refplacement=_spatialPlacement,point=origin)
ios.attribute.edit_attributes(model, product=assm, attributes={
    "Name": assm_type.Name,
    "ObjectPlacement": local_placement,
    "PredefinedType": assm_type.PredefinedType,
})
for el in assm_type.IsDecomposedBy[0].RelatedObjects:
        new = element.copy(model, element=el)
        assign_object(related_object=new, relating_object=el)
        run("aggregate.assign_object", model, product=new, relating_object=assm)


model = ifcpatch.execute({
    "input": "input.ifc",
    "file": model,
    "recipe": "Optimise",
    "arguments": [],
})

relassmat = model.by_type("IfcRelAssociatesMaterial")[1]
for ram in model.by_type("IfcRelAssociatesMaterial")[2:]:
    if ram.RelatingMaterial == relassmat.RelatingMaterial:
        _ramRO = list(relassmat.RelatedObjects)
        _ramRO += ram.RelatedObjects
        relassmat.RelatedObjects = tuple(_ramRO)
        model.remove(ram)












model.write(f1)



def load_ifc_automatically(f):
    if (bool(f)) == True:
        _project = f.by_type('IfcProject')
        
        if _project != None:
            for i in _project:
                _collection_name = 'IfcProject/' + i.Name
                
                _collection = bpy.data.collections.get(_collection_name)
                
                if _collection != None:
                    for _obj in _collection.objects:
                        bpy.data.objects.remove(_obj, do_unlink=True)
                        
                    bpy.data.collections.remove(_collection)
        
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
        bpy.ops.bim.load_project(filepath=f1, should_start_fresh_session=False)

load_ifc_automatically(model)