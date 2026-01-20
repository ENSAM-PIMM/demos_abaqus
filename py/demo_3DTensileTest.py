# -*- coding: mbcs -*-

''' 
 ARTS ET METIERS - ABAQUS DEMOS
 
 TENSILE TEST
 
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
param['dim']=[150.e-3,40.e-3,5.e-3]     # dimensions of sample
param['red']=[2.e-3,1.]                 # middle thickness & radius
param['load']=100.                      # force amplitude & velocity
param['quad']=True                      # linear/quadratic elements
param['selt']=5.e-3                     # element size
param['run']=False                      # run


# MATERIAL (11 22 33 12 13 23)
#----------------------------------------------------------------------------
mdb.models['Model-1'].Material(name='alu')
mdb.models['Model-1'].materials['alu'].Density(table=((2700.0, ), ))
mdb.models['Model-1'].materials['alu'].Elastic(table=((70.0e9, 0.3), ))


# GEOMETRY
#----------------------------------------------------------------------------   
s = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=200.0); s.setPrimaryObject(option=STANDALONE)
x0=sqrt(param['red'][1]**2-(param['red'][0]/2.+param['red'][1]-param['dim'][2]/2.)**2)
s.Line(point1=(0.0, 0.0), point2=(param['dim'][0]/2., 0.0))
s.Line(point1=(param['dim'][0]/2., 0.), point2=(param['dim'][0]/2., param['dim'][2]/2.))
s.Line(point1=(param['dim'][0]/2., param['dim'][2]/2.), point2=(x0, param['dim'][2]/2.))
s.ArcByCenterEnds(center=(0.0, param['red'][0]/2.+param['red'][1]), point1=(x0, param['dim'][2]/2.), point2=(0.0, param['red'][0]/2.),  direction=CLOCKWISE)
s.Line(point1=(0.0, param['red'][0]/2.), point2=(0.0, 0.0))
p = mdb.models['Model-1'].Part(dimensionality=THREE_D, name='sample', type=DEFORMABLE_BODY)
p.BaseSolidExtrude(depth=param['dim'][1]/2., sketch=s); s.unsetPrimaryObject()
del mdb.models['Model-1'].sketches['__profile__']


# PARTITION
#---------------------------------------------------------------------------- 
p = mdb.models['Model-1'].parts['sample']
e1=p.edges.getByBoundingBox(xMin=x0-1e-5, xMax=x0+1e-5, yMin=0.)
e2=p.edges.getByBoundingBox(xMin=param['dim'][0]/2.-1e-5, zMax=1e-5)
p.PartitionCellBySweepEdge(sweepPath=e2[0], cells=p.cells.getByBoundingBox(), edges=(e1[0],))


# SYMMETRY
#---------------------------------------------------------------------------- 
p = mdb.models['Model-1'].parts['sample']
f1 = p.faces.getByBoundingBox(xMax=1e-6); p.Mirror(mirrorPlane=f1[0], keepOriginal=ON, keepInternalBoundaries=ON)
f1 = p.faces.getByBoundingBox(yMax=1e-6); p.Mirror(mirrorPlane=f1[0], keepOriginal=ON, keepInternalBoundaries=ON)
f1 = p.faces.getByBoundingBox(zMax=1e-6); p.Mirror(mirrorPlane=f1[0], keepOriginal=ON, keepInternalBoundaries=ON)


# SETS & SURFACES
#----------------------------------------------------------------------------  
f1 = p.faces.getByBoundingBox(xMax=-param['dim'][0]/2.+1e-5); p.Set(name='X0', faces=f1)
f1 = p.faces.getByBoundingBox(xMin=param['dim'][0]/2.-1e-5); p.Set(name='XL', faces=f1)
f1 = p.faces.getByBoundingBox(zMax=-param['dim'][1]/2.+1e-5); p.Set(name='Z0', faces=f1) 
f1 = p.faces.getByBoundingBox(zMin=param['dim'][1]/2.-1e-5); p.Set(name='ZL', faces=f1) 
f1 = p.faces.getByBoundingBox(xMin=-1e-5, xMax=1e-5); p.Set(name='MIDDLE', faces=f1) 


# SECTION
#----------------------------------------------------------------------------
mdb.models['Model-1'].HomogeneousSolidSection(name='sec', material='alu', thickness=None)
p.SectionAssignment(sectionName='sec', offsetField='', offsetType=MIDDLE_SURFACE, offset=0.0, 
  region=(p.cells.getByBoundingBox(),),  thicknessAssignment=FROM_SECTION)

 
# MESH
#----------------------------------------------------------------------------
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
p.setElementType(regions=(p.cells.getByBoundingBox(),), elemTypes=(elemType1,elemType2,elemType3))
p.seedPart(size=param['selt'], deviationFactor=0.1, minSizeFactor=0.1)
p.generateMesh()


# ASSEMBLY
#----------------------------------------------------------------------------  
a = mdb.models['Model-1'].rootAssembly;a.DatumCsysByDefault(CARTESIAN)
a.Instance(dependent=ON, name='sample',part=p)
#
rp1 = a.ReferencePoint(point=(1.25*param['dim'][0]/2., 0., 0.))
a.Set(name='RP1', referencePoints=(a.referencePoints[rp1.id], ))  
mdb.models['Model-1'].MultipointConstraint(name='RGB1', mpcType=BEAM_MPC, csys=None,
    controlPoint=a.sets['RP1'], surface=a.instances['sample'].sets['XL'], userMode=DOF_MODE_MPC, userType=0) 

 
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
mdb.models['Model-1'].EncastreBC(name='fix', createStepName='Initial', region=a.instances['sample'].sets['X0'], localCsys=None)
mdb.models['Model-1'].ConcentratedForce(name='Load', createStepName='demo_TensileTest', 
     region=a.sets['RP1'], cf1=param['load'], distributionType=UNIFORM, field='', localCsys=None)


# JOB
#----------------------------------------------------------------------------
jobname='demo_3DTensileTest'

mdb.Job(name=jobname, model='Model-1', description='', type=ANALYSIS, 
    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90, 
    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, 
    explicitPrecision=SINGLE, nodalOutputPrecision=FULL, echoPrint=OFF, 
    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='', 
    scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT, numCpus=2, 
    numDomains=2, numGPUs=0)

mdb.saveAs(pathName=os.path.join(os.getcwd(),jobname))
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
 session.viewports['Viewport: 1'].odbDisplay.display.setValues(plotState=(CONTOURS_ON_DEF, ))
 session.viewports['Viewport: 1'].odbDisplay.setFrame(step=0, frame=0 )
 session.viewports['Viewport: 1'].odbDisplay.setPrimaryVariable(variableLabel='S', 
    outputPosition=INTEGRATION_POINT, refinement=(COMPONENT, 'S11'), )
 session.viewports['Viewport: 1'].makeCurrent()

 