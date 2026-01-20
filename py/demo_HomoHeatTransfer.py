# -*- coding: mbcs -*-

''' 
 ARTS ET METIERS - ABAQUS DEMOS
 
 Homogeneization for heat transfer (steady-state)
 
 Eric Monteiro - PIMM - PARIS - FRANCE     
 
 v0.0 - 16/02/2023
'''

from abaqus import *
from abaqusConstants import *
from caeModules import *
import numpy as np
import os

Mdb()

# PARAMETERS  (units: SI)
#----------------------------------------------------------------------------
param=dict()
param['name']='sample'              # name of the part
param['dim']=[1.,10.,10.]           # dimensions of sample
param['fibre']=[5.,5.,2.]           # fibre position and radius [yf, zf, rf]
param['quad']=False                 # linear/quadratic elements
param['selt']=0.1                   # element size
param['run']=True                   # run

mat=dict()
mat['resin']=dict([('dens',1200.), ('elastic',[70.0e9, 0.3]), ('cond',237.)])
mat['fibre']=dict([('dens',1200.), ('elastic',[70.0e9, 0.3]), ('cond',237./100.)])

simu=dict()
simu['grad']=1                         # imposed gradient
simu['Timp']=10                        # imposed temperature
simu['tend']=1                         # time period
simu['dt']=0.1                         # step time

# MATERIAL (11 22 33 12 13 23)
#----------------------------------------------------------------------------
for key in mat.keys():
 mdb.models['Model-1'].Material(name=key)
 mdb.models['Model-1'].materials[key].Density(table=((mat[key]['dens'],), ))
 mdb.models['Model-1'].materials[key].Elastic(type=ISOTROPIC, table=(tuple(mat[key]['elastic']), ))
 mdb.models['Model-1'].materials[key].Conductivity(type=ISOTROPIC, table=((mat[key]['cond'],), ))

# GEOMETRY
#----------------------------------------------------------------------------   
s = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=200.0); s.setPrimaryObject(option=STANDALONE)
s.Line(point1=(0.0, 0.0), point2=(0.0, param['dim'][1]))
p = mdb.models['Model-1'].Part(dimensionality=THREE_D, name=param['name'], type=DEFORMABLE_BODY)
p.BaseShellExtrude(depth=param['dim'][2], sketch=s); s.unsetPrimaryObject()
del mdb.models['Model-1'].sketches['__profile__']

# PARTITION
#---------------------------------------------------------------------------- 
p = mdb.models['Model-1'].parts[param['name']]
f0 = p.faces.getByBoundingBox(xMin=-1e-6, xMax=1e-6)
e0 = p.edges.getByBoundingBox(xMin=-1e-6, xMax=1e-6, zMax=1e-6)
t = p.MakeSketchTransform(sketchPlane=f0[0], sketchUpEdge=e0[0], 
    sketchPlaneSide=SIDE1, sketchOrientation=LEFT, origin=(0.0, 0.0, 0.0))
s = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=200., gridSpacing=1, transform=t)
g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints 
s.sketchOptions.setValues(decimalPlaces=4) ; s.setPrimaryObject(option=SUPERIMPOSE)
p = mdb.models['Model-1'].parts[param['name']] ; p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
s.CircleByCenterPerimeter(center=(-param['fibre'][1], param['fibre'][0]), point1=(-(param['fibre'][1]+param['fibre'][2]), param['fibre'][0]))
p.PartitionFaceBySketch(sketchUpEdge=e0[0], faces=f0, sketchOrientation=LEFT, sketch=s)
s.unsetPrimaryObject(); del mdb.models['Model-1'].sketches['__profile__']

# MESH (2D)
#----------------------------------------------------------------------------
if param['quad']:
 #quadratic 
 elemType1 = mesh.ElemType(elemCode=DS8, elemLibrary=STANDARD)
 elemType2 = mesh.ElemType(elemCode=DS6, elemLibrary=STANDARD)
else:
 #linear
 elemType1 = mesh.ElemType(elemCode=DS4, elemLibrary=STANDARD)
 elemType2 = mesh.ElemType(elemCode=DS3, elemLibrary=STANDARD)
#
p = mdb.models['Model-1'].parts[param['name']]; r1=p.faces.getByBoundingBox()
p.setElementType(regions=(r1,), elemTypes=(elemType1,elemType2))
p.seedPart(size=param['selt'], deviationFactor=0.1, minSizeFactor=0.001)
p.generateMesh()

# MESH (3D)
#----------------------------------------------------------------------------
p = mdb.models['Model-1'].parts[param['name']]; r1=p.elements.getByBoundingBox()
p.generateMeshByOffset(region=regionToolset.Region(side1Elements=r1), offsetDirection=OUTWARD, 
    meshType=SOLID, totalThickness=param['dim'][0], numLayers=int(np.ceil(param['dim'][0]/param['selt'])))
p.deleteMesh(regions=p.faces.getByBoundingBox(xMin=-1e-6, xMax=1e-6))
p.RemoveFaces(faceList = p.faces.getByBoundingBox(), deleteCells=False)
#
if param['quad']:
 #quadratic 
 elemType1 = mesh.ElemType(elemCode=DC3D20, elemLibrary=STANDARD)
 elemType2 = mesh.ElemType(elemCode=DC3D15, elemLibrary=STANDARD)
 elemType3 = mesh.ElemType(elemCode=DC3D10, elemLibrary=STANDARD)
else:
 #linear
 elemType1 = mesh.ElemType(elemCode=DC3D8, elemLibrary=STANDARD)
 elemType2 = mesh.ElemType(elemCode=DC3D6, elemLibrary=STANDARD)
 elemType3 = mesh.ElemType(elemCode=DC3D4, elemLibrary=STANDARD)
p = mdb.models['Model-1'].parts[param['name']]; r1=p.elements.getByBoundingBox()
p.setElementType(regions=(r1,), elemTypes=(elemType1,elemType2,elemType3))

# SETS 
#----------------------------------------------------------------------------  
p = mdb.models['Model-1'].parts[param['name']]
#
c1 = p.elements.getByBoundingBox(); p.Set(name='allE', elements=c1)
c1 = p.elements.getByBoundingCylinder(center1=(-1.e-6,param['fibre'][0],param['fibre'][1]), 
    center2=(param['dim'][0]+1e-6,param['fibre'][0],param['fibre'][1]) , radius=param['fibre'][2]) ; p.Set(name='fibre', elements=c1)
p.SetByBoolean(name='resin', sets=(p.sets['allE'], p.sets['fibre'], ), operation=DIFFERENCE)
#
n1 = p.nodes.getByBoundingBox(); p.Set(name='allN', nodes=n1)
n1 = p.nodes.getByBoundingBox(xMax=1e-6); p.Set(name='nB', nodes=n1)
n1 = p.nodes.getByBoundingBox(xMin=param['dim'][0]-1e-6); p.Set(name='nF', nodes=n1)
n1 = p.nodes.getByBoundingBox(yMax=1e-6); p.Set(name='nL', nodes=n1) 
n1 = p.nodes.getByBoundingBox(yMin=param['dim'][1]-1e-6); p.Set(name='nR', nodes=n1) 
n1 = p.nodes.getByBoundingBox(zMax=1e-6); p.Set(name='nS', nodes=n1) 
n1 = p.nodes.getByBoundingBox(zMin=param['dim'][2]-1e-6); p.Set(name='nN', nodes=n1) 

# SECTION
#----------------------------------------------------------------------------
for key in ['resin','fibre']:
 mdb.models['Model-1'].HomogeneousSolidSection(name='S'+key, material=key, thickness=None)
 p = mdb.models['Model-1'].parts[param['name']]
 p.SectionAssignment(sectionName='S'+key, offsetField='', offsetType=MIDDLE_SURFACE, offset=0.0, 
  region=p.sets[key],  thicknessAssignment=FROM_SECTION)

# ASSEMBLY
#----------------------------------------------------------------------------  
a = mdb.models['Model-1'].rootAssembly;a.DatumCsysByDefault(CARTESIAN)
a.Instance(dependent=ON, name=param['name'],part=p)
 
# STEP
#---------------------------------------------------------------------------- 
mdb.models['Model-1'].HeatTransferStep(name='HeatTransfer', previous='Initial', response=STEADY_STATE,  
    timePeriod=simu['tend'], maxNumInc=10000000, initialInc=simu['dt'], minInc=1e-08, maxInc=simu['tend'], amplitude=RAMP)

# OUTPUT
#----------------------------------------------------------------------------
mdb.models['Model-1'].fieldOutputRequests['F-Output-1'].setValues(variables=(
    'NT', 'HFL', 'RFL', 'IVOL'), frequency=LAST_INCREMENT)

# INTERACTION 
#----------------------------------------------------------------------------  
p = mdb.models['Model-1'].parts[param['name']] ; D=np.zeros([3,3])
#
oppfaces = [['nB','nF'], ['nL','nR'], ['nS','nN']]
for jcase in range(len(oppfaces)):
 #delete previous constraints
 for key in mdb.models['Model-1'].constraints.keys():
  if key.startswith('eqn_'): del mdb.models['Model-1'].constraints[key]
 #
 curfaces = oppfaces[jcase] ; 
 n1=p.sets[curfaces[0]].nodes ; n2=p.sets[curfaces[1]].nodes 
 xyz=np.array([x.coordinates for x in n2]) 
 for i1 in range(len(n1)):
  i2=np.argmin(np.sqrt(np.sum((n1[i1].coordinates-xyz)**2,1)))
  pref = 'eq'+curfaces[0][0]+'_'+str(i1) ; pref2=param['name']+'.'+pref
  p.Set(name=pref+'_1', nodes=n1[i1:i1+1]) ; p.Set(name=pref+'_2', nodes=n2[i2:i2+1])  
  if i1==0: 
   p.Set(name='RNTm', nodes=n1[i1:i1+1]); p.Set(name='RNTp', nodes=n2[i2:i2+1]) 
  else:
   mdb.models['Model-1'].Equation(name=pref, terms=((1.0, pref2+'_2', 11), (-1.0, pref2+'_1', 11), (+1.0, param['name']+'.RNTm', 11), (-1.0, param['name']+'.RNTp', 11)))
 
 # LOAD
 #---------------------------------------------------------------------------- 
 a = mdb.models['Model-1'].rootAssembly
 #
 r1 = a.instances[param['name']].sets['RNTm']
 mdb.models['Model-1'].TemperatureBC(name='Timp', createStepName='HeatTransfer', 
    region=r1, fixed=OFF, distributionType=UNIFORM, fieldName='', 
    magnitude=simu['Timp'], amplitude=UNSET)
 #
 r1 = a.instances[param['name']].sets['RNTp']
 mdb.models['Model-1'].TemperatureBC(name='Timp2', createStepName='HeatTransfer', 
    region=r1, fixed=OFF, distributionType=UNIFORM, fieldName='', 
    magnitude=simu['Timp']+simu['grad']*param['dim'][jcase], amplitude=UNSET)

 # JOB
 #----------------------------------------------------------------------------
 jobname='demo_HomoHeatTransfer'+str(jcase)

 mdb.Job(name=jobname, model='Model-1', description='', type=ANALYSIS, 
    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90, 
    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, 
    explicitPrecision=SINGLE, nodalOutputPrecision=FULL, echoPrint=OFF, 
    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='', 
    scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT, numCpus=2, 
    numDomains=2, numGPUs=0)

 mdb.saveAs(pathName=os.path.join(os.getcwd(),jobname))
 if param['run']:
  mdb.jobs[jobname].submit(consistencyChecking=OFF)	
  mdb.jobs[jobname].waitForCompletion()
 else:
  mdb.jobs[jobname].writeInput(consistencyChecking=OFF)
 
 # POST
 #---------------------------------------------------------------------------- 
 if param['run']:
  o3 = session.openOdb(name=os.path.join(os.getcwd(),jobname+'.odb'))
  session.viewports['Viewport: 1'].setValues(displayedObject=o3)
  session.viewports['Viewport: 1'].odbDisplay.display.setValues(plotState=(CONTOURS_ON_DEF, ))
  session.viewports['Viewport: 1'].odbDisplay.setFrame(step=0, frame=-1 )
  session.viewports['Viewport: 1'].odbDisplay.setPrimaryVariable(variableLabel='NT11', outputPosition=NODAL,)
  session.viewports['Viewport: 1'].makeCurrent()
  #
  csys1 = o3.rootAssembly.DatumCsysByThreePoints(name='Csys1', coordSysType=CARTESIAN,
    origin=(0,0,0), point1=(1.0, 0.0, 0), point2=(0.0, 1.0, 0.0) )
  r1 = o3.rootAssembly.elementSets[' ALL ELEMENTS']
  #
  hfl0 = o3.steps['HeatTransfer'].frames[-1].fieldOutputs['HFL'].getTransformedField(datumCsys=csys1)
  ivol0 = o3.steps['HeatTransfer'].frames[-1].fieldOutputs['IVOL']
  #
  hfl1 = hfl0.getSubset(region=r1, position=INTEGRATION_POINT); HFL = hfl1.bulkDataBlocks[0].data
  ivol1 = ivol0.getSubset(region=r1, position=INTEGRATION_POINT); IVOL = ivol1.bulkDataBlocks[0].data
  #
  e_hfl = hfl1.bulkDataBlocks[0].elementLabels ; i_hfl = hfl1.bulkDataBlocks[0].integrationPoints
  e_ivol = ivol1.bulkDataBlocks[0].elementLabels ; i_ivol = ivol1.bulkDataBlocks[0].integrationPoints
  if not(np.all(e_ivol==e_hfl) and np.all(i_ivol==i_hfl)): print('check output order')
  #
  vol = np.sum(IVOL)
  mHFL = np.sum(HFL*IVOL,0)/vol
  #
  D[:,jcase]=-mHFL/(simu['grad'])
 
# PRINT EFFECTIVE PROPERTIES
#----------------------------------------------------------------------------
if param['run']: print('D=',D)

