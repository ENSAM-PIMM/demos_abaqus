# -*- coding: mbcs -*-

''' 
 ARTS ET METIERS - ABAQUS DEMOS
 
 Cross Plate
 
 Eric Monteiro - PIMM    
 
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
param['dim']=[30.e-3,30.e-3,5.e-3]     # dimensions of sample
param['rad']= 8.e-3                    # radius of the hole
param['idim']= 2                        # flag 
param['load']=[1.e-3,1.e-3]                   # displacement amplitude in X- & Y- direction
param['quad']=False                      # linear/quadratic elements
param['selt']=[1.0e-3, 0.1]                     # element size
param['run']=False                      # run


# MATERIAL (11 22 33 12 13 23)
#----------------------------------------------------------------------------
mdb.models['Model-1'].Material(name='alu')
mdb.models['Model-1'].materials['alu'].Density(table=((2700.0, ), ))
mdb.models['Model-1'].materials['alu'].Elastic(table=((70.0e9, 0.3), ))


# GEOMETRY
#----------------------------------------------------------------------------   
s = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=200.0); s.setPrimaryObject(option=STANDALONE)
s.Line(point1=(0.0, 0.0), point2=(0.0, param['dim'][1]/2.))
s.Line(point1=(0.0, param['dim'][1]/2.), point2=(param['dim'][0]/2.-param['rad'], param['dim'][1]/2.))
s.Line(point1=(param['dim'][0]/2., param['dim'][1]/2.-param['rad']), point2=(param['dim'][0]/2., 0.0))
s.Line(point1=(param['dim'][0]/2., 0.0), point2=(0.0, 0.0))
s.ArcByCenterEnds(center=(param['dim'][0]/2., param['dim'][1]/2.),  direction=CLOCKWISE, 
   point1=(param['dim'][0]/2., param['dim'][1]/2.-param['rad']), point2=(param['dim'][0]/2.-param['rad'], param['dim'][1]/2.))
if param['idim']==3 :
  p = mdb.models['Model-1'].Part(dimensionality=THREE_D, name='sample', type=DEFORMABLE_BODY)
  p.BaseSolidExtrude(depth=param['dim'][2]/2., sketch=s)
else:
 param['idim']=2
 p = mdb.models['Model-1'].Part(name='sample', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
 p.BaseShell(sketch=s) 
s.unsetPrimaryObject()
del mdb.models['Model-1'].sketches['__profile__']

# SETS & SURFACES
#---------------------------------------------------------------------------- 
p = mdb.models['Model-1'].parts['sample']
if param['idim']==3 :
 f1 = p.faces.getByBoundingBox(xMax=1e-6); p.Set(name='x0', faces=f1) 
 f1 = p.faces.getByBoundingBox(yMax=1e-6); p.Set(name='y0', faces=f1) 
 f1 = p.faces.getByBoundingBox(zMax=1e-6); p.Set(name='z0', faces=f1) 
 f1 = p.faces.getByBoundingBox(xMin=param['dim'][0]/2.-1e-6); p.Set(name='xL', faces=f1) 
 f1 = p.faces.getByBoundingBox(yMin=param['dim'][1]/2.-1e-6); p.Set(name='yL', faces=f1)
else:
 f1 = p.edges.getByBoundingBox(xMax=1e-6); p.Set(name='x0', edges=f1) 
 f1 = p.edges.getByBoundingBox(yMax=1e-6); p.Set(name='y0', edges=f1) 
 f1 = p.edges.getByBoundingBox(xMin=param['dim'][0]/2.-1e-6); p.Set(name='xL', edges=f1) 
 f1 = p.edges.getByBoundingBox(yMin=param['dim'][1]/2.-1e-6); p.Set(name='yL', edges=f1) 
 
# SECTION
#----------------------------------------------------------------------------
if param['idim']==3 :
  r1=p.cells.getByBoundingBox()
  mdb.models['Model-1'].HomogeneousSolidSection(name='sec', material='alu', thickness=None)
  p.SectionAssignment(sectionName='sec', offsetField='', offsetType=MIDDLE_SURFACE, offset=0.0, 
     region=(r1,),  thicknessAssignment=FROM_SECTION)
     
else:
  r1=p.faces.getByBoundingBox()
  mdb.models['Model-1'].HomogeneousSolidSection(name='sec', material='alu', thickness=param['dim'][2])
  p.SectionAssignment(sectionName='sec', offsetField='', offsetType=MIDDLE_SURFACE, offset=0.0, 
     region=(r1,),  thicknessAssignment=FROM_SECTION)

# MESH
#----------------------------------------------------------------------------
if param['idim']==3 :
 if param['quad']:
  #quadratic 
  elemType1 = mesh.ElemType(elemCode=C3D20, elemLibrary=STANDARD)
  elemType2 = mesh.ElemType(elemCode=C3D15, elemLibrary=STANDARD)
  elemType3 = mesh.ElemType(elemCode=C3D10, elemLibrary=STANDARD)
 else:
  #linear
  elemType1 = mesh.ElemType(elemCode=C3D8, elemLibrary=STANDARD)
  elemType2 = mesh.ElemType(elemCode=C3D6, elemLibrary=STANDARD)
  elemType3 = mesh.ElemType(elemCode=C3D4, elemLibrary=STANDARD)
 elemtypes=(elemType1,elemType2,elemType3)
else:
 if param['quad']:
  #quadratic
  elemType1 = mesh.ElemType(elemCode=CPS8, elemLibrary=STANDARD)
  elemType2 = mesh.ElemType(elemCode=CPS6, elemLibrary=STANDARD) 
 else:
  #linear   
  elemType1 = mesh.ElemType(elemCode=CPS4, elemLibrary=STANDARD)
  elemType2 = mesh.ElemType(elemCode=CPS3, elemLibrary=STANDARD)
 elemtypes=(elemType1,elemType2)  
#   
p.setElementType(regions=(r1,), elemTypes=elemtypes)
p.seedPart(size=param['selt'][0], deviationFactor=param['selt'][1], minSizeFactor=0.1)
p.generateMesh()

# ASSEMBLY
#----------------------------------------------------------------------------  
a = mdb.models['Model-1'].rootAssembly;a.DatumCsysByDefault(CARTESIAN)
a.Instance(dependent=ON, name='sample',part=p)
 
# STEP
#---------------------------------------------------------------------------- 
mdb.models['Model-1'].ImplicitDynamicsStep(name='demo_TensileTest', previous='Initial', 
    timePeriod=10.0, maxNumInc=1000000, initialInc=1., minInc=1e-04, application=QUASI_STATIC, amplitude=RAMP)


# OUTPUT
#----------------------------------------------------------------------------
mdb.models['Model-1'].fieldOutputRequests['F-Output-1'].setValues(variables=(
    'S', 'E', 'EE', 'U', 'RF'), timeInterval=1.)

    
# LOAD
#---------------------------------------------------------------------------- 
a = mdb.models['Model-1'].rootAssembly
#
r1 = a.instances['sample'].sets['x0']
mdb.models['Model-1'].XsymmBC(name='xsym', createStepName='Initial', region=r1, localCsys=None)
#
r1 = a.instances['sample'].sets['y0']
mdb.models['Model-1'].YsymmBC(name='ysym', createStepName='Initial', region=r1, localCsys=None)
#
if param['idim']==3:
  r1 = a.instances['sample'].sets['z0']
  mdb.models['Model-1'].ZsymmBC(name='zsym', createStepName='Initial', region=r1, localCsys=None)
#
r1 = a.instances['sample'].sets['xL']
mdb.models['Model-1'].DisplacementBC(name='moveX', createStepName='demo_TensileTest', region=r1,   
    u1=param['load'][0], u2=UNSET, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET, amplitude=UNSET, fixed=OFF, 
    distributionType=UNIFORM, fieldName='', localCsys=None)
#
r1 = a.instances['sample'].sets['yL']
mdb.models['Model-1'].DisplacementBC(name='moveY', createStepName='demo_TensileTest', region=r1,   
    u1=UNSET, u2=param['load'][1], u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET, amplitude=UNSET, fixed=OFF, 
    distributionType=UNIFORM, fieldName='', localCsys=None)    

# JOB
#----------------------------------------------------------------------------
mdb.Job(name='demo_TensileTest', model='Model-1', description='', type=ANALYSIS, 
    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90, 
    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, 
    explicitPrecision=SINGLE, nodalOutputPrecision=FULL, echoPrint=OFF, 
    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='', 
    scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT, numCpus=2, 
    numDomains=2, numGPUs=0)

if param['run']:
 mdb.jobs['demo_TensileTest'].submit(consistencyChecking=OFF)	
 mdb.jobs['demo_TensileTest'].waitForCompletion()
 
# POST
#---------------------------------------------------------------------------- 
if param['run']:
 o3 = session.openOdb(name=os.path.join(os.getcwd(),'demo_TensileTest.odb'))
 session.viewports['Viewport: 1'].setValues(displayedObject=o3)
 session.viewports['Viewport: 1'].odbDisplay.display.setValues(plotState=(CONTOURS_ON_DEF, ))
 session.viewports['Viewport: 1'].odbDisplay.setFrame(step=0, frame=0 )
 session.viewports['Viewport: 1'].odbDisplay.setPrimaryVariable(variableLabel='S', 
    outputPosition=INTEGRATION_POINT, refinement=(COMPONENT, 'S11'), )
 session.viewports['Viewport: 1'].makeCurrent()

 
