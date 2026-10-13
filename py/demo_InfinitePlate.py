# -*- coding: mbcs -*-

''' 
 ARTS ET METIERS - ABAQUS DEMOS
 
 Infinite PLATE 
 
 Eric Monteiro - PIMM - PARIS - FRANCE   
 
 v0.0 - 10/10/2026
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
param['dim']=[100.e-3,10.e-3,100.e-3]  # dimensions of medium
param['2Dopt']= 'stress'               # flag: 'stress' (plane stress) or 'strain' (plane strain)
param['selt']=[1.0e-3, 0.1]            # element size
param['quad']=True                     # linear/quadratic elements
param['load']=[20e-3, 40e-3, 2, -1.]  # applied load: [xstart, Lzone, dir, load]
param['freq']=[2e3, 3e3, 3, 1]         # frequency range
param['run']=False                     # run
#
param['Linf'] = 100*param['selt'][0]   # infinite length


# MATERIAL (11 22 33 12 13 23)
#----------------------------------------------------------------------------
mdb.models['Model-1'].Material(name='alu')
mdb.models['Model-1'].materials['alu'].Density(table=((2700.0, ), ))
mdb.models['Model-1'].materials['alu'].Elastic(table=((70.0e9, 0.3), ))


# GEOMETRY
#----------------------------------------------------------------------------   
s = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=200.0); s.setPrimaryObject(option=STANDALONE)
s.Line(point1=(0.0, 0.0), point2=(param['load'][0], 0.0))  
s.Line(point1=(param['load'][0], 0.0), point2=(param['load'][0]+param['load'][1], 0.0))
s.Line(point1=(param['load'][0]+param['load'][1], 0.0), point2=(param['dim'][0], 0.0))
s.Line(point1=(param['dim'][0], 0.0), point2=(param['dim'][0]+param['Linf'], 0.0))
s.Line(point1=(param['dim'][0]+param['Linf'], 0.0), point2=(param['dim'][0]+param['Linf'], param['dim'][1]))  
s.Line(point1=(param['dim'][0]+param['Linf'], param['dim'][1]), point2=(param['dim'][0], param['dim'][1]))
s.Line(point1=(param['dim'][0], param['dim'][1]), point2=(param['load'][0]+param['load'][1], param['dim'][1]))
s.Line(point1=(param['load'][0]+param['load'][1], param['dim'][1]), point2=(param['load'][0], param['dim'][1]))
s.Line(point1=(param['load'][0], param['dim'][1]), point2=(0.0, param['dim'][1]))
s.Line(point1=(0.0, param['dim'][1]), point2=(-param['Linf'], param['dim'][1]))
s.Line(point1=(-param['Linf'], param['dim'][1]), point2=(-param['Linf'], 0.0))
s.Line(point1=(-param['Linf'], 0.0), point2=(0.0, 0.0))
p = mdb.models['Model-1'].Part(name='sample', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
p.BaseShell(sketch=s) ; s.unsetPrimaryObject()
del mdb.models['Model-1'].sketches['__profile__']


# PARTITIONS
#----------------------------------------------------------------------------
p = mdb.models['Model-1'].parts['sample']
f1 = p.faces.getByBoundingBox()
v1 = p.vertices.getByBoundingSphere(center=(0.0,0.0,0.0), radius=1e-6)
v2 = p.vertices.getByBoundingSphere(center=(0.0,param['dim'][1],0.0), radius=1e-6)
p.PartitionFaceByShortestPath(point1=v1[0], point2=v2[0], faces=f1)
#
p = mdb.models['Model-1'].parts['sample']
f1 = p.faces.getByBoundingBox()
v1 = p.vertices.getByBoundingSphere(center=(param['dim'][0],0.0,0.0), radius=1e-6)
v2 = p.vertices.getByBoundingSphere(center=(param['dim'][0],param['dim'][1],0.0), radius=1e-6)
p.PartitionFaceByShortestPath(point1=v1[0], point2=v2[0], faces=f1)


# SETS & SURFACES
#---------------------------------------------------------------------------- 
p = mdb.models['Model-1'].parts['sample']
f1 = p.edges.getByBoundingBox(xMin=-1e-6, xMax=1e-6); p.Set(name='x0', edges=f1)  
f1 = p.edges.getByBoundingBox(xMin=param['dim'][0]-1e-6, xMax=param['dim'][0]+1e-6); p.Set(name='xL', edges=f1) 
f1 = p.edges.getByBoundingBox(yMax=1e-6); p.Set(name='ally0', edges=f1)
f1 = p.edges.getByBoundingBox(yMax=1e-6, xMin=-1e-6, xMax=param['dim'][0]+1e-6); p.Set(name='y0', edges=f1)
f1 = p.edges.getByBoundingBox(yMin=param['dim'][1]-1e-6); p.Set(name='allyL', edges=f1) 
f1 = p.edges.getByBoundingBox(yMin=param['dim'][1]-1e-6, xMin=-1e-6, xMax=param['dim'][0]+1e-6); p.Set(name='yL', edges=f1)
f1 = p.edges.getByBoundingBox(yMin=param['dim'][1]-1e-6, xMin=1e-6, xMax=param['load'][0]+param['load'][1]); p.Set(name='yload', edges=f1)
p.Surface(side1Edges=f1, name='yload')
#
f1 = p.faces.getByBoundingBox(); p.Set(name='all', faces=f1) 
f1 = p.faces.getByBoundingBox(xMin=-1e-6, xMax=param['dim'][0]+1e-6); p.Set(name='medium', faces=f1) 
p.SetByBoolean(name='Linf', sets=(p.sets['all'],p.sets['medium']), operation=DIFFERENCE)
p.SetByBoolean(name='y0inf', sets=(p.sets['ally0'],p.sets['y0']), operation=DIFFERENCE)
p.SetByBoolean(name='yLinf', sets=(p.sets['allyL'],p.sets['yL']), operation=DIFFERENCE)
p.SetByBoolean(name='yinf', sets=(p.sets['y0inf'],p.sets['yLinf']), operation=UNION)
 

# SECTION
#----------------------------------------------------------------------------
mdb.models['Model-1'].HomogeneousSolidSection(name='Salu', material='alu', thickness=param['dim'][2])
p.SectionAssignment(sectionName='Salu', offsetField='', offsetType=MIDDLE_SURFACE, offset=0.0, 
     region=p.sets['medium'],  thicknessAssignment=FROM_SECTION)
#
mdb.models['Model-1'].HomogeneousSolidSection(name='Sinf', material='alu', thickness=param['dim'][2])
p.SectionAssignment(sectionName='Sinf', offsetField='', offsetType=MIDDLE_SURFACE, offset=0.0, 
     region=p.sets['Linf'],  thicknessAssignment=FROM_SECTION)


# MESH
#----------------------------------------------------------------------------
if param['2Dopt']=='strain':
 if param['quad']:
   #quadratic
   elemType1 = mesh.ElemType(elemCode=CPE8, elemLibrary=STANDARD)
   elemType2 = mesh.ElemType(elemCode=CPE6, elemLibrary=STANDARD) 
 else:
   #linear   
   elemType1 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
   elemType2 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
else:
 if param['quad']:
  #quadratic
  elemType1 = mesh.ElemType(elemCode=CPS8, elemLibrary=STANDARD)
  elemType2 = mesh.ElemType(elemCode=CPS6, elemLibrary=STANDARD) 
 else:
  #linear   
  elemType1 = mesh.ElemType(elemCode=CPS4, elemLibrary=STANDARD)
  elemType2 = mesh.ElemType(elemCode=CPS3, elemLibrary=STANDARD)  
#  
elemtypes=(elemType1,elemType2) 
p.setElementType(regions=p.sets['all'], elemTypes=elemtypes)
p.seedPart(size=param['selt'][0], deviationFactor=param['selt'][1], minSizeFactor=0.1)
p.generateMesh(regions=(p.sets['medium'].faces,))
# add acoustic elements (CAE doesn't support solid infinite element)
if param['quad']:
   #quadratic
   elemType1 = mesh.ElemType(elemCode=AC2D6, elemLibrary=STANDARD)
   elemType2 = mesh.ElemType(elemCode=AC2D8, elemLibrary=STANDARD) 
else:
   #linear   
   elemType1 = mesh.ElemType(elemCode=AC2D3, elemLibrary=STANDARD)
   elemType2 = mesh.ElemType(elemCode=AC2D4, elemLibrary=STANDARD)
elemINF = (elemType1,elemType2)
p.setElementType(regions=p.sets['Linf'], elemTypes=elemINF)
p.seedEdgeByNumber(edges=p.sets['yinf'].edges, number=1, constraint=FINER)
p.generateMesh(regions=(p.sets['Linf'].faces,))

# ASSEMBLY
#----------------------------------------------------------------------------  
a = mdb.models['Model-1'].rootAssembly;a.DatumCsysByDefault(CARTESIAN)
a.Instance(dependent=ON, name='sample',part=p)
 

# STEP
#---------------------------------------------------------------------------- 
mdb.models['Model-1'].SteadyStateDirectStep(name='Freq', previous='Initial', frequencyRange=(tuple(param['freq']), ))


# OUTPUT
#----------------------------------------------------------------------------
mdb.models['Model-1'].fieldOutputRequests['F-Output-1'].setValues(variables=('S', 'E', 'EE', 'U', 'RF'))

    
# LOAD
#---------------------------------------------------------------------------- 
a = mdb.models['Model-1'].rootAssembly
#
vecload=(1.0, 0.0, 0.0) if param['load'][2]==1 else (0.0, 1.0, 0.0)
#
r1 = a.instances['sample'].surfaces['yload']
mdb.models['Model-1'].SurfaceTraction(name='piezo', createStepName='Freq', 
    region=r1, magnitude=param['load'][3]+0j, directionVector=((0.0, 0.0, 0.0), vecload), 
    distributionType=UNIFORM, field='', localCsys=None, traction=GENERAL)   


# JOB
#----------------------------------------------------------------------------
jobname='demo_InfinitePlate'

mdb.Job(name=jobname, model='Model-1', description='', type=ANALYSIS, 
    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90, 
    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, 
    explicitPrecision=SINGLE, nodalOutputPrecision=FULL, echoPrint=OFF, 
    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='', 
    scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT, numCpus=2, 
    numDomains=2, numGPUs=0)

mdb.saveAs(pathName=os.path.join(os.getcwd(), jobname))
session.viewports['Viewport: 1'].setValues(displayedObject=mdb.models['Model-1'].rootAssembly)


# modify element name (CAE doesn't support solid infinite element)
#----------------------------------------------------------------------------
mdb.models['Model-1'].keywordBlock.synchVersions(storeNodesAndElements=False)
nKblock=len(mdb.models['Model-1'].keywordBlock.sieBlocks)
for j1 in range(nKblock):
    st1=mdb.models['Model-1'].keywordBlock.sieBlocks[j1]
    if st1.startswith('*Element, type=AC2D'):break
if j1<nKblock:
  st1='*Element, type=CINP'
  st1+='E' if param['2Dopt']=='strain' else 'S' 
  st1+='5R' if param['quad'] else '4' 
  mdb.models['Model-1'].keywordBlock.replace(j1, st1)
  

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
 session.viewports['Viewport: 1'].odbDisplay.display.setValues(plotState=(CONTOURS_ON_UNDEF, ))
 session.viewports['Viewport: 1'].odbDisplay.setFrame(step=0, frame=-1 )
 session.viewports['Viewport: 1'].odbDisplay.setPrimaryVariable(
    variableLabel='U', outputPosition=NODAL, refinement=(COMPONENT, 'U1'), )
 #session.viewports['Viewport: 1'].odbDisplay.setPrimaryVariable(variableLabel='S', 
 #   outputPosition=INTEGRATION_POINT, refinement=(COMPONENT, 'S11'), )
 leaf = dgo.LeafFromOdbElementTypes(elementTypes=("CINPE4","CINPS4","CINPE5R","CINPS5R" ))
 session.viewports['Viewport: 1'].odbDisplay.displayGroup.remove(leaf=leaf)
 session.viewports['Viewport: 1'].makeCurrent()
 session.viewports['Viewport: 1'].odbDisplay.basicOptions.setValues(numericForm=REAL)
 #session.viewports['Viewport: 1'].odbDisplay.basicOptions.setValues(numericForm=IMAGINARY)
 #session.viewports['Viewport: 1'].odbDisplay.basicOptions.setValues(numericForm=COMPLEX_MAGNITUDE)
 #session.viewports['Viewport: 1'].odbDisplay.basicOptions.setValues(numericForm=COMPLEX_PHASE)

 