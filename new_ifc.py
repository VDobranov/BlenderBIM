# Импортируем библиотеки:
# для работы со временем: time
# для работы с IFC: ifcopenshell
# для математических операций: math

import time
import ifcopenshell as ios
# import math

import bpy

# Создаём пустой файл IFC

ifc = ios.file()

# Мировые константы

pO = 0., 0., 0.
dX = 1., 0., 0.
dY = 0., 1., 0.
dZ = 0., 0., 1.
adX = -1., 0., 0.
adY = 0., -1., 0.
adZ = 0., 0., -1.

globalAxisX = ifc.createIfcDirection(dX)
globalAxisY = ifc.createIfcDirection(dY)
globalAxisZ = ifc.createIfcDirection(dZ)
globalAxisXa = ifc.createIfcDirection(adX)
globalAxisYa = ifc.createIfcDirection(adY)
globalAxisZa = ifc.createIfcDirection(adZ)
originPoint = ifc.createIfcCartesianPoint(pO)

worldCoordinateSystem = ifc.createIfcAxis2Placement3D(
    originPoint, globalAxisZ, globalAxisX)

# Константы эстакады

PRWidth = 6000.0
PRSpans = [12000.0, 21000.0, 6000.0, 9000.0, 6000.0, 9000.0, 6000.0, 9000.0]
PRLength = sum(PRSpans)
PRLevels = {
    'Ground Level': 00.,
    'Tier 1': 6400.,
    'Tier 2': 10000.
}
PRSrps = [[1, 3], [4, 9]]

PRIfcOrigin = originPoint
PRIfcEnd = ifc.createIfcCartesianPoint([
    originPoint.Coordinates[0] + PRLength,
    originPoint.Coordinates[1],
    originPoint.Coordinates[2]
])


# Функции

# Creates an IfcAxis2Placement3D from Location, Axis and RefDirection

def create_ifcaxis2placement(
    ifcfile=ifc,
    point=originPoint,
    dir1=globalAxisZ,
    dir2=globalAxisX
):
    if point == originPoint and dir1 == globalAxisZ and dir2 == globalAxisX:
        axis2placement = worldCoordinateSystem
    else:
        axis2placement = ifcfile.createIfcAxis2Placement3D(point, dir1, dir2)
    return axis2placement

# Creates an IfcLocalPlacement from Location, Axis, RefDirection and relative placement


def create_ifclocalplacement(
    ifcfile=ifc,
    point=originPoint,
    dir1=globalAxisZ,
    dir2=globalAxisX,
    relativeTo=None
):
    if point == originPoint and dir1 == globalAxisZ and dir2 == globalAxisX:
        axis2placement = worldCoordinateSystem
    else:
        axis2placement = ifcfile.createIfcAxis2Placement3D(point, dir1, dir2)
    ifclocalplacement2 = ifcfile.createIfcLocalPlacement(
        relativeTo, axis2placement)
    return ifclocalplacement2


def find_axes_intersection(a1, a2):
    p11 = a1.AxisCurve.Points[0]
    p12 = a1.AxisCurve.Points[1]
    p21 = a2.AxisCurve.Points[0]
    p22 = a2.AxisCurve.Points[1]
    z0 = p11.Coordinates[2]
    x11 = p11.Coordinates[0]
    x12 = p12.Coordinates[0]
    y11 = p11.Coordinates[1]
    y12 = p12.Coordinates[1]
    x21 = p21.Coordinates[0]
    x22 = p22.Coordinates[0]
    y21 = p21.Coordinates[1]
    y22 = p22.Coordinates[1]
    A1 = y12 - y11
    B1 = x12 - x11
    C1 = y11 * (x12 - x11) - x11 * (y12 - y11)
    A2 = y22 - y21
    B2 = x22 - x21
    C2 = y21 * (x22 - x21) - x21 * (y22 - y21)
    x0 = (B1 * C2 - B2 * C1) / (A1 * B2 - A2 * B1)
    y0 = (C1 * A2 - C2 * A1) / (A1 * B2 - A2 * B1)
    return [x0, y0, z0]


def create_customgridplacement(axis1, axis2, dir1=globalAxisZ, dir2=globalAxisX):
    point = ifc.createIfcCartesianPoint(find_axes_intersection(axis1, axis2))
    axis2Placement = ifc.createIfcAxis2Placement3D(point, dir1, dir2)
    localPlacement = ifc.createIfcLocalPlacement(None, axis2Placement)
    return localPlacement

# Юридическая информация


engineer = ifc.createIfcActorRole('ENGINEER')
contractor = ifc.createIfcActorRole('CONTRACTOR')
owner = ifc.createIfcActorRole('OWNER')
projectManager = ifc.createIfcActorRole('PROJECTMANAGER')

myself = ifc.createIfcPerson()
myself.FamilyName = 'Dobranov'
myself.GivenName = 'Vyacheslav'
myself.Roles = [projectManager, owner, engineer]

myOrganization = ifc.createIfcOrganization()
myOrganization.Name = 'Klockwerk Kat'
myOrganization.Roles = [contractor]

meInMyOrg = ifc.createIfcPersonAndOrganization()
meInMyOrg.ThePerson = myself
meInMyOrg.TheOrganization = myOrganization
meInMyOrg.Roles = [owner]

myApp = ifc.createIfcApplication()
myApp.ApplicationDeveloper = myOrganization
myApp.Version = '0.0.1'
myApp.ApplicationFullName = 'KK-IFC'
myApp.ApplicationIdentifier = '…'

# creationDate = ifc.createIfcTimeStamp(int(time.time()))
ownerHistory = ifc.createIfcOwnerHistory()
ownerHistory.OwningUser = meInMyOrg
ownerHistory.OwningApplication = myApp
ownerHistory.CreationDate = int(time.time())

# Единицы измерения

lengthUnit = ifc.createIfcSIUnit()
lengthUnit.UnitType = "LENGTHUNIT"
lengthUnit.Prefix = "MILLI"
lengthUnit.Name = "METRE"

areaUnit = ifc.createIfcSIUnit()
areaUnit.UnitType = "AREAUNIT"
areaUnit.Name = "SQUARE_METRE"

volumeUnit = ifc.createIfcSIUnit()
volumeUnit.UnitType = "VOLUMEUNIT"
volumeUnit.Name = "CUBIC_METRE"

planeAngleUnit = ifc.createIfcSIUnit()
planeAngleUnit.UnitType = "PLANEANGLEUNIT"
planeAngleUnit.Name = "RADIAN"

myUnits = ifc.createIfcUnitAssignment(
    [lengthUnit, areaUnit, volumeUnit, planeAngleUnit])

# Общая геометрия

# globalAxisX = ifc.createIfcDirection(dX)
# globalAxisY = ifc.createIfcDirection(dY)
# globalAxisZ = ifc.createIfcDirection(dZ)
# originPoint = ifc.createIfcCartesianPoint(pO)

# worldCoordinateSystem = create_ifcaxis2placement(ifc)
# worldCoordinateSystem = ifc.createIfcAxis2Placement3D()
# worldCoordinateSystem.Location = originPoint
# worldCoordinateSystem.Axis = globalAxisZ
# worldCoordinateSystem.RefDirection = globalAxisX

modelContext = ifc.createIfcGeometricRepresentationContext()
modelContext.ContextType = 'Model'
modelContext.CoordinateSpaceDimension = 3
modelContext.Precision = 0.001
modelContext.WorldCoordinateSystem = worldCoordinateSystem
# modelContext.TrueNorth = globalAxisY

footprintContext = ifc.createIfcGeometricRepresentationSubContext()
footprintContext.ContextIdentifier = 'Footprint'
footprintContext.ContextType = 'Model'
footprintContext.ParentContext = modelContext
footprintContext.TargetView = 'MODEL_VIEW'

bodyContext = ifc.createIfcGeometricRepresentationSubContext()
bodyContext.ContextIdentifier = 'Body'
bodyContext.ContextType = 'Model'
bodyContext.ParentContext = modelContext
bodyContext.TargetView = 'MODEL_VIEW'

axisContext = ifc.createIfcGeometricRepresentationSubContext()
axisContext.ContextIdentifier = 'Axis'
axisContext.ContextType = 'Model'
axisContext.ParentContext = modelContext
axisContext.TargetView = 'MODEL_VIEW'

planContext = ifc.createIfcGeometricRepresentationContext()
planContext.ContextType = 'Plan'
planContext.CoordinateSpaceDimension = 2
planContext.Precision = 0.001
planContext.WorldCoordinateSystem = worldCoordinateSystem

# Создание проекта

project = ifc.createIfcProject(ios.guid.new())
project.OwnerHistory = ownerHistory
project.Name = 'Piperack test project'
project.Description = 'Creation of an IFC-file from the scratch with the ifcopenshell library.'
project.UnitsInContext = myUnits
project.RepresentationContexts = [modelContext, planContext]

# Создание площадки

sitePlacement = create_ifclocalplacement()

site = ifc.createIfcSite(ios.guid.new())
site.Name = "Construction Site"
site.ObjectPlacement = sitePlacement

siteContainer = ifc.createIfcRelAggregates(ios.guid.new())
siteContainer.RelatingObject = project
siteContainer.RelatedObjects = [site]

# Создание сетки осей

PRMainAxes = []
PRMainAxesPolylines = []

for a in range(3):
    p1 = ifc.createIfcCartesianPoint([
        originPoint.Coordinates[0],
        PRWidth/2*(a-1),
        0.
    ])
    p2 = ifc.createIfcCartesianPoint([
        originPoint.Coordinates[0] + PRLength,
        PRWidth/2*(a-1),
        0.
    ])
    axis = ifc.createIfcGridAxis()
    if p1.Coordinates[1] < 0:
        axis.AxisTag = "A"
    elif p1.Coordinates[1] == 0:
        axis.AxisTag = "Piperack Axis"
        PRMainAxis = axis
    else:
        axis.AxisTag = "B"
    axis.AxisCurve = ifc.createIfcPolyline([p1, p2])
    axis.SameSense = True
    PRMainAxes.append(axis)
    PRMainAxesPolylines.append(axis.AxisCurve)

#PRMainAxis = ifc.createIfcGridAxis()
#PRMainAxis.AxisTag = "Piperack Axis"
#PRMainAxis.AxisCurve = ifc.createIfcPolyline([PRIfcOrigin, PRIfcEnd])
#PRMainAxis.SameSense = True

PRCrossAxes = []
PRCrossAxesPolylines = []
for a in range(len(PRSpans)+1):
    p1 = ifc.createIfcCartesianPoint([
        float(sum(PRSpans[:a])),
        -PRWidth/2,
        0.
    ])
    p2 = ifc.createIfcCartesianPoint([
        float(sum(PRSpans[:a])),
        PRWidth/2,
        0.
    ])
    axis = ifc.createIfcGridAxis()
    axis.AxisTag = f"{a+1}"
    axis.AxisCurve = ifc.createIfcPolyline([p1, p2])
    axis.SameSense = True
    PRCrossAxes.append(axis)
    PRCrossAxesPolylines.append(axis.AxisCurve)

PRCrossAxis = PRCrossAxes[0]

PRMainGridPlacement = create_ifclocalplacement(relativeTo=sitePlacement)

PRMainGridGeomCurveSet = ifc.createIfcGeometricCurveSet(
    PRMainAxesPolylines + PRCrossAxesPolylines)

PRMainGridShapeRepresent = ifc.createIfcShapeRepresentation()
PRMainGridShapeRepresent.ContextOfItems = footprintContext
PRMainGridShapeRepresent.RepresentationIdentifier = 'FootPrint'
PRMainGridShapeRepresent.RepresentationType = 'GeometricCurveSet'
PRMainGridShapeRepresent.Items = [PRMainGridGeomCurveSet]

PRMainGridProductDefShape = ifc.createIfcProductDefinitionShape()
PRMainGridProductDefShape.Representations = [PRMainGridShapeRepresent]

PRMainGrid = ifc.createIfcGrid(ios.guid.new(), ownerHistory)
PRMainGrid.Name = 'Piperack Grid'
PRMainGrid.UAxes = PRMainAxes
PRMainGrid.VAxes = PRCrossAxes
PRMainGrid.ObjectPlacement = PRMainGridPlacement
PRMainGrid.Representation = PRMainGridProductDefShape

PRMainGridSpatialContainer = ifc.createIfcRelContainedInSpatialStructure(
    ios.guid.new())
PRMainGridSpatialContainer.Name = 'Piperack Main Grid Container'
PRMainGridSpatialContainer.RelatingStructure = site
PRMainGridSpatialContainer.RelatedElements = [PRMainGrid]

# Создание эстакады

piperackPlacement = create_ifclocalplacement(relativeTo=sitePlacement)

piperack = ifc.createIfcBuilding(ios.guid.new())
piperack.Name = "Piperack"
piperack.CompositionType = 'COMPLEX'
piperack.ObjectPlacement = piperackPlacement

piperackContainer = ifc.createIfcRelAggregates(ios.guid.new())
piperackContainer.Name = "Piperack Container"
piperackContainer.RelatingObject = site
piperackContainer.RelatedObjects = [piperack]

# Создание участков эстакады

#srp1Placement = create_ifclocalplacement(relativeTo=piperackPlacement)
#srp2Placement = create_ifclocalplacement(relativeTo=piperackPlacement)
#srp2Placement = ifc.createIfcGridPlacement()
# srp2Placement.PlacementLocation = ifc.createIfcVirtualGridIntersection(
# 	[PRMainAxis, PRCrossAxes[4]])

srps = []
srpsPlacement = []
srpsAxes = {}


def SrpCreation(_axesNums, _gridPlacement=False):
    _crossAxis = ''
    for ax in ifc.by_type('IfcGridAxis'):
        if ax.AxisTag == str(_axesNums[0]):
            _crossAxis = ax
            break
    if _gridPlacement:
        _srpPlacement = create_customgridplacement(
            PRMainAxis, _crossAxis)
    else:
        _globalOrigin = piperackPlacement.RelativePlacement.Location
        _origin = ifc.createIfcCartesianPoint([
            _globalOrigin.Coordinates[0] +
            _crossAxis.AxisCurve.Points[0].Coordinates[0],
            _globalOrigin.Coordinates[1],
            _globalOrigin.Coordinates[2]
        ])
        _axis2placement = ifc.createIfcAxis2Placement3D(
            _origin, globalAxisZ, globalAxisX)
        _srpPlacement = ifc.createIfcLocalPlacement(
            piperackPlacement, _axis2placement)
    _srp = ifc.createIfcBuilding(ios.guid.new(), ownerHistory)
    _srp.Name = 'Tag ' + str(PRSrps.index(_axesNums) + 1)
    _srp.CompositionType = 'COMPLEX'
    _srp.ObjectPlacement = _srpPlacement
    srps.append(_srp)
    srpsPlacement.append(_srpPlacement)
    _x = _axesNums[0]
    srpsAxes[_srp.Name] = []
    while _x <= _axesNums[-1]:
        srpsAxes[_srp.Name].append(PRCrossAxes[_x-1])
        _x += 1
    # _srp.Description = str(srpsAxes[_srp.Name])


for _axes in PRSrps:
    SrpCreation(_axes, True)

#srp1 = ifc.createIfcBuilding(ios.guid.new())
#srp1.Name = "Участок 1"
#srp1.CompositionType = 'PARTIAL'
#srp1.ObjectPlacement = srp1Placement

#srp2 = ifc.createIfcBuilding(ios.guid.new())
#srp2.Name = "Участок 2"
#srp2.CompositionType = 'PARTIAL'
#srp2.ObjectPlacement = srp2Placement

srpsContainer = ifc.createIfcRelAggregates(ios.guid.new())
srpsContainer.Name = "SRPs Container"
srpsContainer.RelatingObject = piperack
srpsContainer.RelatedObjects = srps

# Создание ярусов эстакады


def TierCreation(_name, _srp, _elevation):
    _tier = ifc.createIfcBuildingStorey(ios.guid.new(), ownerHistory)
    _tier.Name = _srp.Name + ". " + _name
    # _tier.Name = _name
    _tier.Elevation = _elevation
    return _tier


for _srp in srps:
    _tierContainer = ifc.createIfcRelAggregates(ios.guid.new())
    _tierContainer.RelatingObject = _srp
    _tiers = []
    for k, v in PRLevels.items():
        _tiers.append(TierCreation(k, _srp, v))
    _tierContainer.RelatedObjects = _tiers

# Создание рам

frames = []

for _srp in srps:
    _frames = []
    for _axis in srpsAxes[_srp.Name]:
        _frame = ifc.createIfcBuilding(ios.guid.new(), ownerHistory)
        _frame.Name = 'Frame on Axis ' + _axis.AxisTag
        _frame.ObjectPlacement = create_customgridplacement(PRMainAxis, _axis)
        _frames.append(_frame)
        frames.append(_frame)
    _frameContainer = ifc.createIfcRelAggregates(ios.guid.new())
    _frameContainer.RelatingObject = _srp
    _frameContainer.RelatedObjects = _frames


# Создание колонн

rectProfiles = []


def createRectProfile(
    _XDim=600.,
    _YDim=600.,
):
    _profile = ifc.createIfcRectangleProfileDef()
    _profile.ProfileType = 'AREA'
    _profile.ProfileName = f'{_XDim}x{_YDim}'
    _profile.XDim, _profile.YDim = _XDim, _YDim
    rectProfiles.append(_profile)
    return _profile


# Cardinal points:
#   Y
# 7 8 9
# 4 5 6 X
# 1 2 3

cardinalPoints = []
cardinalPointsCoords = []


def findCardinalPointCoords(xd=100., yd=100., index=5):
    if index == 1:
        x = -xd/2
        y = -yd/2
    elif index == 2:
        x = -xd/2
        y = 0.
    elif index == 3:
        x = xd/2
        y = -yd/2
    elif index == 4:
        x = 0.
        y = -yd/2
    elif index == 5:
        x = 0.
        y = 0.
    elif index == 6:
        x = 0.
        y = yd/2
    elif index == 7:
        x = -xd/2
        y = yd/2
    elif index == 8:
        x = 0.
        y = yd/2.
    elif index == 9:
        x = xd/2
        y = yd/2
    point = [x, y, 0.]
    return point


extrudedAreaSolids = []


def createExtrudedAreaSolid(
    _XDim=600.,
    _YDim=600.,
    _Depth=6000.,
    _CardinalIndex=5,
    _StartCut=0.,
    _EndCut=0.,
    #    _Axis=globalAxisZ
):
    # _profile=None
    # for p in rectProfiles:
    #     if _XDim == p.XDim and _YDim == p.YDim:
    #         _profile = p
    # if _profile == None:
    _profile = createRectProfile(_XDim, _YDim)
    _cardinalPoint = None
    _cardinalPointCoords = findCardinalPointCoords(
        _XDim, _YDim, _CardinalIndex)
    _cardinalPointCoords[2] += _StartCut
    for cp in cardinalPoints:
        if list(cp.Coordinates) == _cardinalPointCoords:
            _cardinalPoint = cp
    if _cardinalPoint == None:
        _cardinalPoint = ifc.createIfcCartesianPoint(_cardinalPointCoords)
        cardinalPoints.append(_cardinalPoint)
        cardinalPointsCoords.append(_cardinalPointCoords)
    _eas = ifc.createIfcExtrudedAreaSolid()
    _eas.SweptArea = _profile
    _eas.Position = ifc.createIfcAxis2Placement3d(_cardinalPoint)
    _eas.ExtrudedDirection = globalAxisZ
    _eas.Depth = _Depth - _StartCut - _EndCut
    extrudedAreaSolids.append(_eas)
    return _eas


productDefShapes = []


def ColumnPDSCreation(
    _XDim=600.,
    _YDim=600.,
    _Depth=6000.,
    #    _Axis=globalAxisZ
):
    _columnEAS = None
    for eas in extrudedAreaSolids:
        if (_XDim == eas.SweptArea.XDim and
            _YDim == eas.SweptArea.YDim and
            _Depth == eas.Depth
            ):
            _columnEAS = eas
    if _columnEAS == None:
        _columnEAS = createExtrudedAreaSolid(_XDim, _YDim, _Depth, 5)

    _columnPDS = None
    for pds in productDefShapes:
        if pds.Representations[0].Items[0] == _columnEAS:
            _columnPDS = pds
    if _columnPDS == None:
        _columnSP = ifc.createIfcShapeRepresentation()
        _columnSP.ContextOfItems = bodyContext
        _columnSP.RepresentationIdentifier = 'Body'
        _columnSP.RepresentationType = 'SweptSolid'
        _columnSP.Items = [_columnEAS]
        _columnPDS = ifc.createIfcProductDefinitionShape()
        _columnPDS.Name = f"{_XDim}x{_YDim}x{_Depth}"
        _columnPDS.Description = f"Column of {_XDim}x{_YDim} rectangular section and {_Depth} height"
        _columnPDS.Representations = [_columnSP]

    productDefShapes.append(_columnPDS)
    return _columnPDS


def ColumnCreation(
    _XDim=600.,
    _YDim=600.,
    _Depth=6000.,
    _Axis=globalAxisZ,
    _Name='Precast Column',
    _Tag='PCC',
    _RelatingStructure=site,
    _Side=None,
):
    _columnPlacement = ifc.createIfcLocalPlacement()
    _columnPlacement.PlacementRelTo = _RelatingStructure.ObjectPlacement
    _columnPlacement.RelativePlacement = ifc.createIfcAxis2Placement3d(
        _Side, _Axis)

    _columnPDS = ColumnPDSCreation(_XDim, _YDim, _Depth)

    _column = ifc.createIfcColumn(ios.guid.new(), ownerHistory)
    _column.Name = _Name
    _column.Tag = _Tag
    _column.PredefinedType = 'COLUMN'
    _column.ObjectPlacement = _columnPlacement
    _column.Representation = _columnPDS

    return _column


def BeamPDSCreation(
    _XDim=500.,
    _YDim=700.,
    _Depth=6000.,
    _CardinalIndex=0,
    _StartCut=0.,
    _EndCut=0.,
):
    _beamEAS = None
    for eas in extrudedAreaSolids:
        if (_XDim == eas.SweptArea.XDim and
                _YDim == eas.SweptArea.YDim and
                _Depth == eas.Depth
            ):
            _beamEAS = eas
    if _beamEAS == None:
        _beamEAS = createExtrudedAreaSolid(
            _XDim,
            _YDim,
            _Depth,
            _CardinalIndex,
            _StartCut,
            _EndCut,
        )

    _beamPDS = None
    for pds in productDefShapes:
        if pds.Representations[0].Items[0] == _beamEAS:
            _beamPDS = pds
    if _beamPDS == None:
        _beamSP = ifc.createIfcShapeRepresentation()
        _beamSP.ContextOfItems = bodyContext
        _beamSP.RepresentationIdentifier = 'Body'
        _beamSP.RepresentationType = 'SweptSolid'
        _beamSP.Items = [_beamEAS]
        _beamPDS = ifc.createIfcProductDefinitionShape()
        _beamPDS.Name = f"{_XDim}x{_YDim}x{_Depth}"
        _beamPDS.Description = f"Beam of {_XDim}x{_YDim} rectangular section and {_Depth} length"
#        _beamPDS.Description = f"{cardinalPoints}"
        _beamPDS.Representations = [_beamSP]

    productDefShapes.append(_beamPDS)
    return _beamPDS


def BeamCreation(
    _XDim=500.,
    _YDim=700.,
    _Depth=6000.,
    _Axis=globalAxisZ,
    _Name='Precast Beam',
    _Tag='PCB',
    _RelatingStructure=site,
    _Side=None,
    _CardinalIndex=0,
    _StartCut=0.,
    _EndCut=0.,
):
    _beamPlacement = ifc.createIfcLocalPlacement()
    _beamPlacement.PlacementRelTo = _RelatingStructure.ObjectPlacement
    _beamPlacement.RelativePlacement = ifc.createIfcAxis2Placement3d(
        _Side, _Axis)

    _beamPDS = BeamPDSCreation(
        _XDim,
        _YDim,
        _Depth,
        _CardinalIndex,
        _StartCut,
        _EndCut,
    )

    _beam = ifc.createIfcBeam(ios.guid.new(), ownerHistory)
    _beam.Name = _Name
    _beam.Tag = _Tag
    _beam.PredefinedType = 'BEAM'
    _beam.ObjectPlacement = _beamPlacement
    _beam.Representation = _beamPDS

    return _beam


LeftPoint = ifc.createIfcCartesianPoint(
    [0., PRWidth/2, PRLevels['Ground Level']])
RightPoint = ifc.createIfcCartesianPoint(
    [0., -PRWidth/2, PRLevels['Ground Level']])
Tier1Point = ifc.createIfcCartesianPoint([0., -PRWidth/2, PRLevels['Tier 1']])
Tier2Point = ifc.createIfcCartesianPoint([0., -PRWidth/2, PRLevels['Tier 2']])

for _frame in frames:
    _columnSize = 600., 600.
    _TagC = 'PCC' + str(frames.index(_frame) + 1)
    _TagB = 'PCB' + str(frames.index(_frame) + 1)
    _Depth = PRLevels['Tier 2']-PRLevels['Ground Level'],
    # _Depth, = _Depth
    _Depth = _Depth[0]
#    _columnPDS = ColumnPDSCreation(600.,600.,_Depth,globalAxisY)
    _leftColumn = ColumnCreation(
        _XDim=_columnSize[0],
        _YDim=_columnSize[1],
        _Depth=_Depth,
        _Axis=globalAxisZ,
        _RelatingStructure=_frame,
        _Tag=_TagC,
        _Side=LeftPoint
    )
    _rightColumn = ColumnCreation(
        _XDim=_columnSize[0],
        _YDim=_columnSize[1],
        _Depth=_Depth,
        _Axis=globalAxisZ,
        _RelatingStructure=_frame,
        _Tag=_TagC,
        _Side=RightPoint
    )
    _lowerBeam = BeamCreation(
        _XDim=500.,
        _YDim=700.,
        _Depth=PRWidth,
        _Axis=globalAxisY,
        _RelatingStructure=_frame,
        _Tag=_TagB,
        _Side=Tier1Point,
        _CardinalIndex=8,
        _StartCut=_columnSize[0]/2,
        _EndCut=_columnSize[0]/2,
    )
    _upperBeam = BeamCreation(
        _XDim=500.,
        _YDim=700.,
        _Depth=PRWidth,
        _Axis=globalAxisY,
        _RelatingStructure=_frame,
        _Tag=_TagB,
        _Side=Tier2Point,
        _CardinalIndex=8,
        _StartCut=_columnSize[0]/2,
        _EndCut=_columnSize[0]/2,
    )
    _elementsContainer = ifc.createIfcRelContainedInSpatialStructure(
        ios.guid.new())
    _elementsContainer.RelatingStructure = _frame
    _elementsContainer.RelatedElements = [
        _leftColumn, _rightColumn, _lowerBeam, _upperBeam]


beamPlacement = ifc.createIfcLocalPlacement()
beamPlacement.PlacementRelTo = frames[1].ObjectPlacement
beamPlacement.RelativePlacement = ifc.createIfcAxis2Placement3d(
    originPoint, globalAxisY)

beamP = ifc.createIfcRectangleProfileDef()
beamP.ProfileType = 'AREA'
#beamP.ProfileName = '600*600'
beamP.XDim, beamP.YDim = 500., 700.
beamEAS = ifc.createIfcExtrudedAreaSolid()
beamEAS.SweptArea = beamP
beamEAS.ExtrudedDirection = globalAxisZ
beamEAS.Depth = 6000.
beamPos = ifc.createIfcCartesianPoint([0., 350., 0.])
beamEAS.Position = ifc.createIfcAxis2Placement3d(beamPos)
beamStart = beamPlacement.RelativePlacement.Location
beamEnd = ifc.createIfcCartesianPoint([
    beamStart.Coordinates[0] + beamEAS.Depth *
    globalAxisZ.DirectionRatios[0],
    beamStart.Coordinates[1] + beamEAS.Depth *
    globalAxisZ.DirectionRatios[1],
    beamStart.Coordinates[2] + beamEAS.Depth *
    globalAxisZ.DirectionRatios[2],
])
beamAx = ifc.createIfcPolyline([beamStart, beamEnd])
beamSP0 = ifc.createIfcShapeRepresentation()
beamSP0.ContextOfItems = axisContext
beamSP0.RepresentationIdentifier = 'Axis'
beamSP0.RepresentationType = 'SweptSolid'
beamSP0.Items = [beamAx]
beamSP1 = ifc.createIfcShapeRepresentation()
beamSP1.ContextOfItems = bodyContext
beamSP1.RepresentationIdentifier = 'Body'
beamSP1.RepresentationType = 'SweptSolid'
beamSP1.Items = [beamEAS]
beamPDS = ifc.createIfcProductDefinitionShape()
beamPDS.Representations = [beamSP1, beamSP0]

beam = ifc.createIfcBeam(ios.guid.new(), ownerHistory)
beam.Name = f'{beamPlacement.RelativePlacement.Axis.DirectionRatios}'
beam.ObjectPlacement = beamPlacement
beam.Representation = beamPDS

beamContainer = ifc.createIfcRelContainedInSpatialStructure(ios.guid.new())
beamContainer.RelatingStructure = frames[1]
beamContainer.RelatedElements = [beam]

# print(project)

# path = 'H:\\PY\\new_model.ifc'
#path = 'D:\\DELETEME\\new_model.ifc'
path = '/Users/vdobranov/Yandex.Disk.localized/Python/Mac/ifcopenshell/new_model.ifc'
ifc.write(path)


def load_ifc_automatically(f):
    if (bool(f)) == True:
        _project = f.by_type('IfcProject')

        if _project != None:
            for i in _project:
                _collection_name = 'IfcProject/' + i.Name

            _collection = bpy.data.collections.get(str(_collection_name))

            if _collection != None:
                for _obj in _collection.objects:
                    bpy.data.objects.remove(_obj, do_unlink=True)

                bpy.data.collections.remove(_collection)

        bpy.ops.outliner.orphans_purge(
            do_local_ids=True, do_linked_ids=True, do_recursive=True)
        bpy.ops.bim.load_project(filepath=path)


load_ifc_automatically(ifc)
