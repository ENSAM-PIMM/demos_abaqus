# -*- coding: mbcs -*-

''' 
 ARTS ET METIERS - ABAQUS DEMOS
 
 MESHED CROSS-SECTION BEAM
 
 Eric Monteiro - PIMM - PARIS - FRANCE    
 
 v0.0 - 21/01/2025
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
param['dim']=[150.e-3,4.e-3,2.e-3]     # dimensions of sample [L,R,E]
param['load']=100.                     # force amplitude 
param['quad']=False                    # linear/quadratic elements
param['selt']=[5.e-3,1e-3]             # element size [E_beam,E_sec]
param['run']=True                     # run


#----------------------------------------------------------------------------
# CROSS-SECTION GENERATION 
#----------------------------------------------------------------------------


# MATERIAL (11 22 33 12 13 23)
#----------------------------------------------------------------------------
mdb.models.changeKey(fromName='Model-1', toName='Model-CrossSection')
mdb.models['Model-CrossSection'].Material(name='alu')
mdb.models['Model-CrossSection'].materials['alu'].Density(table=((2700.0, ), ))
mdb.models['Model-CrossSection'].materials['alu'].Elastic(table=((70.0e9, 0.3), ))


# CROSS-SECTION GEOMETRY 
#----------------------------------------------------------------------------   
s = mdb.models['Model-CrossSection'].ConstrainedSketch(name='__profile__', sheetSize=200.0); s.setPrimaryObject(option=STANDALONE)
s.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(0.0, param['dim'][1]))
s.rectangle(point1=(-param['dim'][2]/2., -param['dim'][2]/2.), point2=(param['dim'][2]/2., param['dim'][2]/2.))
p = mdb.models['Model-CrossSection'].Part(name='GeoSection', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
p.BaseShell(sketch=s) ; s.unsetPrimaryObject()
del mdb.models['Model-CrossSection'].sketches['__profile__']
#
p = mdb.models['Model-CrossSection'].parts['GeoSection']
session.viewports['Viewport: 1'].setValues(displayedObject=p)


# CROSS-SECTION SECTION
#----------------------------------------------------------------------------
mdb.models['Model-CrossSection'].HomogeneousSolidSection(name='sec', material='alu', thickness=None)
p = mdb.models['Model-CrossSection'].parts['GeoSection']
p.SectionAssignment(sectionName='sec', offsetField='', offsetType=MIDDLE_SURFACE, offset=0.0, 
  region=(p.faces.getByBoundingBox(),),  thicknessAssignment=FROM_SECTION)


# CROSS-SECTION MESH
#----------------------------------------------------------------------------
elemType1 = mesh.ElemType(elemCode=WARP2D4, elemLibrary=STANDARD, secondOrderAccuracy=ON)
elemType2 = mesh.ElemType(elemCode=WARP2D3, elemLibrary=STANDARD, secondOrderAccuracy=ON)
p.setElementType(regions=(p.faces.getByBoundingBox(),), elemTypes=(elemType1,elemType2))
p.seedPart(size=param['selt'][1], deviationFactor=0.1, minSizeFactor=0.1)
p.generateMesh()


# CROSS-SECTION ASSEMBLY
#----------------------------------------------------------------------------  
a = mdb.models['Model-CrossSection'].rootAssembly;a.DatumCsysByDefault(CARTESIAN)
p = mdb.models['Model-CrossSection'].parts['GeoSection']
a.Instance(dependent=ON, name='CrossSection',part=p)


# STEP
#---------------------------------------------------------------------------- 
mdb.models['Model-CrossSection'].StaticStep(name='dummy', previous='Initial')
del mdb.models['Model-CrossSection'].fieldOutputRequests['F-Output-1']
del mdb.models['Model-CrossSection'].historyOutputRequests['H-Output-1']
#
mdb.models['Model-CrossSection'].keywordBlock.synchVersions()
nKblock=len(mdb.models['Model-CrossSection'].keywordBlock.sieBlocks)
for j1 in range(nKblock):
    st1=mdb.models['Model-CrossSection'].keywordBlock.sieBlocks[j1]
    if st1.startswith('*Step'):break
if j1<nKblock:
    mdb.models['Model-CrossSection'].keywordBlock.replace(j1, """*STEP""")
    mdb.models['Model-CrossSection'].keywordBlock.replace(j1+1, """*BEAM SECTION GENERATE""")
    for j2 in range(j1+2,nKblock-1): mdb.models['Model-CrossSection'].keywordBlock.replace(j2, """""")
    mdb.models['Model-CrossSection'].keywordBlock.insert(j1+1,"""*SECTION POINTS \n 1,1,1 \n 2,2,1 \n 3,3,1""")


# JOB
#----------------------------------------------------------------------------
mdb.Job(name='CrossSection', model='Model-CrossSection', description='', 
    type=ANALYSIS, atTime=None, waitMinutes=0, waitHours=0, queue=None, 
    memory=90, memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, 
    explicitPrecision=SINGLE, nodalOutputPrecision=FULL, echoPrint=OFF, 
    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='', 
    scratch='', resultsFormat=ODB, numThreadsPerMpiProcess=1, 
    multiprocessingMode=DEFAULT, numCpus=1, numGPUs=0)
mdb.jobs['CrossSection'].writeInput(consistencyChecking=OFF)










#----------------------------------------------------------------------------
# CANTILEVER BEAM
#----------------------------------------------------------------------------
mdb.Model(name='Model-LoadBeam', modelType=STANDARD_EXPLICIT)


# MATERIAL (11 22 33 12 13 23)
#----------------------------------------------------------------------------
mdb.models['Model-LoadBeam'].Material(name='alu')
mdb.models['Model-LoadBeam'].materials['alu'].Elastic(table=((70.0e9, 0.3), ))


# BEAM GEOMETRY 
#----------------------------------------------------------------------------   
s = mdb.models['Model-LoadBeam'].ConstrainedSketch(name='__profile__', sheetSize=200.0); s.setPrimaryObject(option=STANDALONE)
s.Line(point1=(0.0, 0.0), point2=(param['dim'][0], 0.0))
p = mdb.models['Model-LoadBeam'].Part(name='Beam', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
p.BaseWire(sketch=s) ; s.unsetPrimaryObject()
del mdb.models['Model-LoadBeam'].sketches['__profile__']
#
p = mdb.models['Model-LoadBeam'].parts['Beam']
session.viewports['Viewport: 1'].setValues(displayedObject=p)


# SETS 
#----------------------------------------------------------------------------  
n1 = p.vertices.getByBoundingBox(xMax=1e-5); p.Set(name='X0', vertices=n1)
n1 = p.vertices.getByBoundingBox(xMin=param['dim'][0]-1e-5); p.Set(name='XL', vertices=n1)


# BEAM SECTION
#----------------------------------------------------------------------------
p = mdb.models['Model-LoadBeam'].parts['Beam']
mdb.models['Model-LoadBeam'].CircularProfile(name='dummy', r=1.0)
mdb.models['Model-LoadBeam'].BeamSection(name='SecBeam', material='alu',  
    integration=DURING_ANALYSIS, poissonRatio=0.0, profile='dummy', 
    temperatureVar=LINEAR, beamSectionOffset=(0.0, 0.0), consistentMassMatrix=False)
p.SectionAssignment(region=(p.edges.getByBoundingBox(),), sectionName='SecBeam', offset=0.0, 
    offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)
p.assignBeamSectionOrientation(region=(p.edges.getByBoundingBox(),), method=N1_COSINES, n1=(0.0, 0.0, -1.0))


# BEAM MESH
#----------------------------------------------------------------------------
if param['quad']:
 #quadratic 
 elemType1 = mesh.ElemType(elemCode=B22, elemLibrary=STANDARD)
else:
 #linear
 elemType1 = mesh.ElemType(elemCode=B21, elemLibrary=STANDARD)
p.setElementType(regions=(p.edges.getByBoundingBox(),), elemTypes=(elemType1,))
p.seedPart(size=param['selt'][0], deviationFactor=0.1, minSizeFactor=0.1)
p.generateMesh()


# ASSEMBLY
#----------------------------------------------------------------------------  
a = mdb.models['Model-LoadBeam'].rootAssembly;a.DatumCsysByDefault(CARTESIAN)
p = mdb.models['Model-LoadBeam'].parts['Beam']
a.Instance(dependent=ON, name='Beam',part=p)


# STEP
#---------------------------------------------------------------------------- 
mdb.models['Model-LoadBeam'].StaticStep(name='Loading', previous='Initial')


# OUTPUT
#----------------------------------------------------------------------------
mdb.models['Model-LoadBeam'].fieldOutputRequests['F-Output-1'].setValues(variables=(
    'S', 'E', 'EE', 'U', 'RF'), timeInterval=0.1)

    
# LOAD
#---------------------------------------------------------------------------- 
a = mdb.models['Model-LoadBeam'].rootAssembly
#
mdb.models['Model-LoadBeam'].EncastreBC(name='fix', createStepName='Initial', region=a.instances['Beam'].sets['X0'], localCsys=None)
mdb.models['Model-LoadBeam'].ConcentratedForce(name='Load', createStepName='Loading', 
     region=a.instances['Beam'].sets['XL'], cf2=param['load'], distributionType=UNIFORM, field='', localCsys=None)


# MESHED-CROSS SECTION
#---------------------------------------------------------------------------- 
mdb.models['Model-LoadBeam'].keywordBlock.synchVersions()
nKblock=len(mdb.models['Model-LoadBeam'].keywordBlock.sieBlocks)
for j1 in range(nKblock):
    st1=mdb.models['Model-LoadBeam'].keywordBlock.sieBlocks[j1]
    if st1.startswith('*Beam Section'):break
if j1<nKblock:
    st2=st1.split('\n');st3=st2[0].split(',')
    mdb.models['Model-LoadBeam'].keywordBlock.replace(j1, '*BEAM GENERAL SECTION, '+st3[1]+', SECTION=MESHED \n'+st2[-1])
    mdb.models['Model-LoadBeam'].keywordBlock.insert(9, """*INCLUDE, input=CrossSection.bsp""")


# JOB
#----------------------------------------------------------------------------
mdb.Job(name='demo_MeshCrossSectionBeam', model='Model-LoadBeam', description='', type=ANALYSIS, 
    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90, 
    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True, 
    explicitPrecision=SINGLE, nodalOutputPrecision=FULL, echoPrint=OFF, 
    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='', 
    scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT, numCpus=2, 
    numDomains=2, numGPUs=0)
mdb.jobs['demo_MeshCrossSectionBeam'].writeInput(consistencyChecking=OFF)


# RUN ALL
#----------------------------------------------------------------------------
mdb.saveAs(pathName=os.path.join(os.getcwd(), 'demo_MeshCrossSectionBeam'))
session.viewports['Viewport: 1'].setValues(displayedObject=mdb.models['Model-LoadBeam'].rootAssembly)
if param['run']:
 mdb.jobs['CrossSection'].submit(consistencyChecking=OFF)	
 mdb.jobs['CrossSection'].waitForCompletion()
 #
 mdb.jobs['demo_MeshCrossSectionBeam'].submit(consistencyChecking=OFF)	
 mdb.jobs['demo_MeshCrossSectionBeam'].waitForCompletion()
 

# POST
#---------------------------------------------------------------------------- 
if param['run']:
 o3 = session.openOdb(name=os.path.join(os.getcwd(),'demo_MeshCrossSectionBeam.odb'))
 session.viewports['Viewport: 1'].setValues(displayedObject=o3)
 session.viewports['Viewport: 1'].odbDisplay.display.setValues(plotState=(CONTOURS_ON_DEF, ))
 session.viewports['Viewport: 1'].odbDisplay.setFrame(step=0, frame=-1 )
 session.viewports['Viewport: 1'].odbDisplay.setPrimaryVariable(variableLabel='S', 
    outputPosition=INTEGRATION_POINT, refinement=(COMPONENT, 'S11'), )
 session.viewports['Viewport: 1'].makeCurrent()
