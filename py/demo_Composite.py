# -*- coding: mbcs -*- 

''' 
 ARTS ET METIERS - ABAQUS DEMOS
 
 Composite 
 
 Eric Monteiro - PIMM - PARIS - FRANCE     
 
 v0.0 - 20/01/2025
'''

from abaqus import *
from abaqusConstants import *
from caeModules import *
import numpy as np

Mdb()

# PARAMETERS  (units: SI)
#----------------------------------------------------------------------------
tol1=1e-6
param=dict()
param['name']='sample'              # name of the part
param['dim']=[40e-3,10e-3,40e-3]    # dimensions of sample
param['fiber']=[6,3,1.25e-3,2]      # nx ny, radius, ntimes
param['selt']=1e-3                  # element size
param['quad']=False                 # linear/quadratic elements
param['load']=1e-3                  # applied displacement
param['run']=False                  # run
    
# MATERIALS  (units: SI)
mat=dict()
mat['matrix']=dict([('dens',2800.), ('elastic',['isotropic',(70.0e9, 0.3)])])
mat['allfibers']=dict([('dens',2800.), ('elastic',['isotropic',(7.0e9, 0.3)])])


# MATERIAL (11 22 33 12 13 23)
#----------------------------------------------------------------------------
for key in mat.keys():
 mdb.models['Model-1'].Material(name=key)
 mdb.models['Model-1'].materials[key].Density(table=((mat[key]['dens'],), ))
 eval('mdb.models["Model-1"].materials[key].Elastic(type='+mat[key]['elastic'][0].upper()+', table=('+str(mat[key]['elastic'][1])+', ))')


# GEOMETRY
#----------------------------------------------------------------------------   
# 3D plate
s = mdb.models['Model-1'].ConstrainedSketch(name='__profile__',sheetSize=2.*max(param['dim']))
s.setPrimaryObject(option=STANDALONE)
s.rectangle(point1=(0.0, 0.0), point2=(param['dim'][0], param['dim'][1]))			 	
p = mdb.models['Model-1'].Part(name=param['name'], dimensionality=THREE_D, type=DEFORMABLE_BODY)
#p.BaseSolidExtrude(sketch=s, depth=param['dim'][2]); s.unsetPrimaryObject(); 
p.BaseShell(sketch=s); s.unsetPrimaryObject();
session.viewports['Viewport: 1'].setValues(displayedObject=p)
del mdb.models['Model-1'].sketches['__profile__']
# Fibers position
le=param['dim'][0]/param['fiber'][0]; he=param['dim'][1]/param['fiber'][1] 
xc=np.linspace(0,param['fiber'][0]-1,param['fiber'][0])*le+le/2.
yc=np.linspace(0,param['fiber'][1]-1,param['fiber'][1])*he+he/2.
# Partition for fibers
p = mdb.models['Model-1'].parts[param['name']]
f1 = p.faces.getByBoundingBox(); e1=p.edges.getByBoundingBox(xMax=tol1)
t = p.MakeSketchTransform(sketchPlane=f1[0], sketchUpEdge=e1[0], sketchOrientation=LEFT, sketchPlaneSide=SIDE1, origin=(0.0, 0.0, 0.0))
s = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=param['dim'][0], gridSpacing=param['dim'][0]/100, transform=t)
g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
s.setPrimaryObject(option=SUPERIMPOSE); p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
for x in xc:
 for j1 in range(yc.shape[0]):
  delta=0. if j1%2==0 else param['fiber'][2]*1.
  s.CircleByCenterPerimeter(center=((x+delta), yc[j1]), point1=((x+param['fiber'][2]+delta), yc[j1]))
p.PartitionFaceBySketch(sketchUpEdge=e1[0], sketchOrientation=LEFT, faces=f1, sketch=s)
s.unsetPrimaryObject(); del mdb.models['Model-1'].sketches['__profile__']


# MESH 
#----------------------------------------------------------------------------
if param['quad']: 
 elemType1 = mesh.ElemType(elemCode=S8R, elemLibrary=STANDARD)
 elemType2 = mesh.ElemType(elemCode=STRI65, elemLibrary=STANDARD) 
 elem3DT1 = mesh.ElemType(elemCode=C3D20, elemLibrary=STANDARD)
 elem3DT2 = mesh.ElemType(elemCode=C3D15, elemLibrary=STANDARD)
 elem3DT3 = mesh.ElemType(elemCode=C3D10, elemLibrary=STANDARD, secondOrderAccuracy=ON, distortionControl=DEFAULT)
else: 
 elemType1 = mesh.ElemType(elemCode=S4, elemLibrary=STANDARD, secondOrderAccuracy=OFF)
 elemType2 = mesh.ElemType(elemCode=S3, elemLibrary=STANDARD, secondOrderAccuracy=OFF)
 elem3DT1 = mesh.ElemType(elemCode=C3D8, elemLibrary=STANDARD, secondOrderAccuracy=ON, distortionControl=DEFAULT)
 elem3DT2 = mesh.ElemType(elemCode=C3D6, elemLibrary=STANDARD, secondOrderAccuracy=ON, distortionControl=DEFAULT)
 elem3DT3 = mesh.ElemType(elemCode=C3D4, elemLibrary=STANDARD, secondOrderAccuracy=ON, distortionControl=DEFAULT) 
#
p.setElementType(regions=(p.faces,), elemTypes=(elemType1, elemType2))
p.seedPart(size=param['selt'], deviationFactor=0.05, minSizeFactor=0.1)
p.generateMesh()
#
r1 = regionToolset.Region(side1Elements=p.elements)
p.generateMeshByOffset(region=r1, meshType=SOLID, offsetDirection=OUTWARD, 
  totalThickness=param['dim'][2], numLayers=round(param['dim'][2]/param['selt']), 
  shareNodes=False, deleteBaseElements=True, extendElementSets=False)
p.deleteMesh(regions=p.faces)
p.setElementType(regions=(p.elements,), elemTypes=(elem3DT1, elem3DT2,elem3DT3))
#
p.Set(name='all', elements=p.elements); allfibers=[]
for jx in range(xc.shape[0]):
 for jy in range(yc.shape[0]):
  delta=0. if jy%2==0 else param['fiber'][2]*1.
  e0 = p.elements.getByBoundingCylinder(radius=param['fiber'][2]+tol1,
    center1=(xc[jx]+delta,yc[jy],0.0), center2=(xc[jx]+delta,yc[jy],param['dim'][2]))
  allfibers.append(p.Set(name='fiber'+str(jx)+'_'+str(jy), elements=e0))
p.SetByBoolean(name='allfibers', sets=tuple(allfibers), operation=UNION)
p.SetByBoolean(name='matrix', sets=(p.sets['all'],p.sets['allfibers']), operation=DIFFERENCE)


# SECTION
#----------------------------------------------------------------------------
st0=['matrix', 'allfibers']
for mat in st0:
 mdb.models['Model-1'].HomogeneousSolidSection(name=mat, material=mat, thickness=None)
 p.SectionAssignment(region=p.sets[mat], sectionName=mat, offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
 

# ASSEMBLY
#---------------------------------------------------------------------------- 
a = mdb.models['Model-1'].rootAssembly; a.DatumCsysByDefault(CARTESIAN)
p = mdb.models['Model-1'].parts[param['name']]; alllayers=[]
for j1 in range(param['fiber'][3]): 
 st0='layer'+str(j1+1); alllayers.append(a.Instance(name=st0, part=p, dependent=ON))
 if j1>0:
  a.translate(instanceList=(st0, ), vector=(0.0, j1*param['dim'][1], 0.0))
  if j1%2:
   a.rotate(instanceList=(st0, ), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 1.0, 0.0), angle=90.0)
   a.translate(instanceList=(st0, ), vector=(0.0, 0.0, param['dim'][2]))
#
a.InstanceFromBooleanMerge(name='Composite', instances=tuple(alllayers), keepIntersections=ON,  
  originalInstances=DELETE, mergeNodes=BOUNDARY_ONLY, nodeMergingTolerance=tol1, domain=BOTH)
mdb.models['Model-1'].rootAssembly.features.changeKey(fromName='Composite-1', toName='Composite')


# SETS
#----------------------------------------------------------------------------
p = mdb.models['Model-1'].parts['Composite']
n1 = p.nodes.getByBoundingBox(xMax=tol1); p.Set(name='x0', nodes=n1) 
n1 = p.nodes.getByBoundingBox(yMax=tol1); p.Set(name='y0', nodes=n1) 
n1 = p.nodes.getByBoundingBox(zMax=tol1); p.Set(name='z0', nodes=n1) 
n1 = p.nodes.getByBoundingBox(xMin=param['dim'][0]-tol1); p.Set(name='xL', nodes=n1) 
n1 = p.nodes.getByBoundingBox(yMin=param['fiber'][3]*param['dim'][1]-tol1); p.Set(name='yL', nodes=n1) 
n1 = p.nodes.getByBoundingBox(zMin=param['dim'][2]-tol1); p.Set(name='zL', nodes=n1) 


# STEP
#---------------------------------------------------------------------------- 
mdb.models['Model-1'].StaticStep(name='Static', previous='Initial', 
    timePeriod=10.0, maxNumInc=1000, initialInc=0.1, minInc=1e-06, maxInc=1.0)


# OUTPUT
#----------------------------------------------------------------------------
mdb.models['Model-1'].fieldOutputRequests['F-Output-1'].setValues(variables=(
    'S', 'E', 'EE', 'U', 'RF'), timeInterval=1.)


# LOAD
#---------------------------------------------------------------------------- 
a = mdb.models['Model-1'].rootAssembly
#
r1 = a.instances['Composite'].sets['x0']
mdb.models['Model-1'].DisplacementBC(name='fixX', createStepName='Initial', 
    region=r1, u1=SET, u2=UNSET, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET, 
    amplitude=UNSET, distributionType=UNIFORM, fieldName='', localCsys=None)
#
r1 = a.instances['Composite'].sets['y0']
mdb.models['Model-1'].DisplacementBC(name='fixY', createStepName='Initial', 
    region=r1, u1=UNSET, u2=SET, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET, 
    amplitude=UNSET, distributionType=UNIFORM, fieldName='', localCsys=None)
#
r1 = a.instances['Composite'].sets['z0']
mdb.models['Model-1'].DisplacementBC(name='fixZ', createStepName='Initial', 
    region=r1, u1=UNSET, u2=UNSET, u3=SET, ur1=UNSET, ur2=UNSET, ur3=UNSET, 
    amplitude=UNSET, distributionType=UNIFORM, fieldName='', localCsys=None)
#
r1 = a.instances['Composite'].sets['xL']
mdb.models['Model-1'].DisplacementBC(name='BC-4', createStepName='Static', 
    region=r1, u1=param['load'], u2=UNSET, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET, 
    amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='', localCsys=None)


# JOB
#----------------------------------------------------------------------------
jobname='demo_Composite'

mdb.Job(name=jobname, model='Model-1', description='', type=ANALYSIS, 
    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90, 
    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, 
    explicitPrecision=SINGLE, nodalOutputPrecision=FULL, echoPrint=OFF, 
    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='', 
    scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT, numCpus=2, 
    numDomains=2, numGPUs=0)

mdb.saveAs(pathName=os.path.join(os.getcwd(), jobname))
session.viewports['Viewport: 1'].setValues(displayedObject=mdb.models['Model-1'].rootAssembly)
if param['run']:
 mdb.jobs[jobname].submit(consistencyChecking=OFF)	
 mdb.jobs[jobname].waitForCompletion()
else:
 mdb.jobs[jobname].writeInput(consistencyChecking=OFF)


# POST
#---------------------------------------------------------------------------- 
if param['run']:
 o3 = session.openOdb(name=os.path.join(os.getcwd(), jobname+'.odb'))
 session.viewports['Viewport: 1'].setValues(displayedObject=o3)
 session.viewports['Viewport: 1'].odbDisplay.display.setValues(plotState=(CONTOURS_ON_UNDEF, CONTOURS_ON_DEF, ))
 session.viewports['Viewport: 1'].odbDisplay.setFrame(step=0, frame=-1 )
 session.viewports['Viewport: 1'].odbDisplay.setPrimaryVariable(variableLabel='S', 
    outputPosition=INTEGRATION_POINT, refinement=(COMPONENT, 'S11'), )
 session.viewports['Viewport: 1'].makeCurrent()