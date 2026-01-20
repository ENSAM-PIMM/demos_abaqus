# -*- coding: mbcs -*- 

''' 
 ARTS ET METIERS - ABAQUS DEMOS
 
 Structural Health Monitoring with piezoelectric transducers 
 
 Eric Monteiro - PIMM - PARIS - FRANCE     
 
 v0.0 - 04/06/2019
'''

from abaqus import *
from abaqusConstants import *
from caeModules import *
import numpy as np
import os

Mdb()

# PARAMETERS  (units: SI)
#----------------------------------------------------------------------------
tol1=1e-6
param=dict()
param['name']='sample'              # name of the part
param['dim']=[200e-3,30e-3,1e-3]    # dimensions of sample
param['quad']=False                 # linear/quadratic elements
param['selt']=1e-3                  # element size
param['load']=[100., 10e3]          # voltage amplitude & frequency
param['run']=False                  # run
# piezo [xc, yc, th, rad]    
param['pzt']=[[param['dim'][0]/4., param['dim'][1]/2., 0.5e-3, 12.5e-3],
              [3.*param['dim'][0]/4.,  param['dim'][1]/2., 0.5e-3, 12.5e-3]]

# TIME CONTROL
simu=dict()
simu['tend']=1e-3                      # time period
simu['dt']=[1e-6,1e-8,1e-4]            # step time [init/min/max]
simu['tout']=2e-6                      # step time for output

# MATERIALS  (units: SI)
mat=dict()
mat['alu']=dict([('dens',2800.), ('elastic',['isotropic',(70.0e9, 0.3)])])
#NCE51  (warning: ABQ:11 22 33 12 13 23 datasheet:11 22 33 23 13 12)
mat['nce51']=dict([('dens',7850.), ('elastic',['orthotropic',(13.2e10, 8.76e10, 13.2e10, 7.34e10, 7.34e10, 16.2e10, 2.24e10, 4.37e10, 4.37e10)]),
    ('piezoelectric', ['strain',(  0.0,   0.0,  0.0,  0.0, 13.7, 0.0,    0.0,   0.0,  0.0,  0.0, 0.0, 13.7,   -6.06, -6.06, 17.2,  0.0, 0.0, 0.0)]),
    ('dielectric',['orthotropic', (1.72e-08, 1.72e-08, 1.68e-08)])])


# MATERIAL (11 22 33 12 13 23)
#----------------------------------------------------------------------------
for key in mat.keys():
 mdb.models['Model-1'].Material(name=key)
 if 'dens' in mat[key].keys():
  mdb.models['Model-1'].materials[key].Density(table=((mat[key]['dens'],), ))
 if 'elastic' in mat[key].keys():
  eval('mdb.models["Model-1"].materials[key].Elastic(type='+mat[key]['elastic'][0].upper()+', table=('+str(mat[key]['elastic'][1])+', ))')
 if 'piezoelectric' in mat[key].keys():
  eval('mdb.models["Model-1"].materials[key].Piezoelectric(type='+mat[key]['piezoelectric'][0].upper()+', table=('+str(mat[key]['piezoelectric'][1])+', ))')
 if 'dielectric' in mat[key].keys():
  eval('mdb.models["Model-1"].materials[key].Dielectric(type='+mat[key]['dielectric'][0].upper()+', table=('+str(mat[key]['dielectric'][1])+', ))')
 

# GEOMETRY
#----------------------------------------------------------------------------   
# 3D plate
s = mdb.models['Model-1'].ConstrainedSketch(name='__profile__',sheetSize=2.*max(param['dim']))
s.setPrimaryObject(option=STANDALONE)
s.rectangle(point1=(0.0, 0.0), point2=(param['dim'][0], param['dim'][1]))			 	
p = mdb.models['Model-1'].Part(name=param['name'], dimensionality=THREE_D, type=DEFORMABLE_BODY)
p.BaseSolidExtrude(sketch=s, depth=param['dim'][2]); s.unsetPrimaryObject(); #p.BaseShell(sketch=s);
session.viewports['Viewport: 1'].setValues(displayedObject=p)
del mdb.models['Model-1'].sketches['__profile__']
# sets
p.Set(name=param['name'], cells=p.cells.getByBoundingBox())
# partition for PZT
p = mdb.models['Model-1'].parts[param['name']]
f = p.faces.getByBoundingBox(zMin=param['dim'][2]-tol1, zMax=param['dim'][2]+tol1)
e = p.edges.getByBoundingBox(zMin=tol1,xMax=tol1)
t = p.MakeSketchTransform(sketchPlane=f[0], sketchUpEdge=e[0], sketchPlaneSide=SIDE1, sketchOrientation=LEFT, origin=(0., 0., 0.))
s = mdb.models['Model-1'].ConstrainedSketch(name='__profile__', sheetSize=0.200, gridSpacing=0.005, transform=t)
g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
s.sketchOptions.setValues(decimalPlaces=3); s.setPrimaryObject(option=SUPERIMPOSE)
p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
for jpzt in range(len(param['pzt'])):  
  curpzt=param['pzt'][jpzt]
  s.CircleByCenterPerimeter(center=(curpzt[0], curpzt[1]), point1=(curpzt[0], curpzt[1]+curpzt[3]))
p.PartitionFaceBySketch(sketchUpEdge=e[0], faces=f, sketch=s)
s.unsetPrimaryObject(); del mdb.models['Model-1'].sketches['__profile__']
# sets
for jpzt in range(len(param['pzt'])): 
  p = mdb.models['Model-1'].parts[param['name']]
  curpzt=param['pzt'][jpzt]; st1='pzt'+str(jpzt+1)
  f = p.faces.getByBoundingBox(xMin=curpzt[0]-curpzt[3]-tol1, xMax=curpzt[0]+curpzt[3]+tol1, yMin=curpzt[1]-curpzt[3]-tol1, yMax=curpzt[1]+curpzt[3]+tol1,  zMin=param['dim'][2]-tol1, zMax=param['dim'][2]+tol1);  
  p.Set(name=st1+'_bot', faces=f);p.Surface(name=st1+'_bot', side1Faces=f)  


# MESH (3D)
#----------------------------------------------------------------------------
if param['quad']: 
 elem3DT1E = mesh.ElemType(elemCode=C3D20E, elemLibrary=STANDARD)
 elem3DT2E = mesh.ElemType(elemCode=C3D15E, elemLibrary=STANDARD)
 elem3DT3E = mesh.ElemType(elemCode=C3D10E, elemLibrary=STANDARD)
 elem3DT1 = mesh.ElemType(elemCode=C3D20, elemLibrary=STANDARD)
 elem3DT2 = mesh.ElemType(elemCode=C3D15, elemLibrary=STANDARD)
 elem3DT3 = mesh.ElemType(elemCode=C3D10, elemLibrary=STANDARD, secondOrderAccuracy=ON, distortionControl=DEFAULT)
else:
 elem3DT1E = mesh.ElemType(elemCode=C3D8E, elemLibrary=STANDARD)
 elem3DT2E = mesh.ElemType(elemCode=C3D6E, elemLibrary=STANDARD)
 elem3DT3E = mesh.ElemType(elemCode=C3D4E, elemLibrary=STANDARD)  
 elem3DT1 = mesh.ElemType(elemCode=C3D8, elemLibrary=STANDARD, secondOrderAccuracy=ON, distortionControl=DEFAULT)
 elem3DT2 = mesh.ElemType(elemCode=C3D6, elemLibrary=STANDARD, secondOrderAccuracy=ON, distortionControl=DEFAULT)
 elem3DT3 = mesh.ElemType(elemCode=C3D4, elemLibrary=STANDARD, secondOrderAccuracy=ON, distortionControl=DEFAULT) 
# mesh plate
p = mdb.models['Model-1'].parts[param['name']]; r1=p.cells.getByBoundingBox()
p.setElementType(regions=(r1,), elemTypes=(elem3DT1,elem3DT2,elem3DT3))
p.seedPart(size=param['selt'], deviationFactor=0.1, minSizeFactor=0.001)
p.generateMesh(); p.Set(name='allelt', elements=p.elements.getByBoundingBox())
# mesh PZT
mn_pzt=[]
for jpzt in range(len(param['pzt'])): 
 p = mdb.models['Model-1'].parts[param['name']]; curpzt=param['pzt'][jpzt]; st1='pzt'+str(jpzt+1)
 s = regionToolset.Region(side1Elements=p.surfaces[st1+'_bot'].elements)
 p.generateMeshByOffset(region=s, offsetDirection=OUTWARD, 
        meshType=SOLID, totalThickness=curpzt[2], numLayers=1, shareNodes=True)
 # sets
 e = p.elements.getByBoundingBox(xMin=curpzt[0]-curpzt[3]-tol1, xMax=curpzt[0]+curpzt[3]+tol1, yMin=curpzt[1]-curpzt[3]-tol1, yMax=curpzt[1]+curpzt[3]+tol1,  zMin=param['dim'][2]-tol1);  
 p.Set(name=st1+'_elt', elements=e); p.Set(name=st1+'_nbot', nodes=p.surfaces[st1+'_bot'].nodes)  
 p.Surface(face2Elements=p.sets[st1+'_elt'].elements, name=st1+'_top'); p.Set(name=st1+'_ntop', nodes=p.surfaces[st1+'_top'].nodes)
 p.Set(name=st1+'_mntop', nodes=p.surfaces[st1+'_top'].nodes[0:1])
 p.SetByBoolean(name=st1+'_sntop', sets=(p.sets[st1+'_ntop'],p.sets[st1+'_mntop']), operation=DIFFERENCE)
 mn_pzt.append(p.sets[st1+'_mntop'])
 # convert to piezo elements
 p.setElementType(regions=p.sets[st1+'_elt'], elemTypes=(elem3DT1E,elem3DT2E,elem3DT3E))
#
p.SetByBoolean(name='mn_pzt', sets=tuple(mn_pzt), operation=UNION)


# SECTION
#----------------------------------------------------------------------------
for key in mat.keys(): mdb.models['Model-1'].HomogeneousSolidSection(name='S'+key, material=key, thickness=None)
# plate
p = mdb.models['Model-1'].parts[param['name']]
p.SectionAssignment(sectionName='Salu', offsetField='', offsetType=MIDDLE_SURFACE, offset=0.0, 
  region=p.sets[param['name']],  thicknessAssignment=FROM_SECTION)
# piezo
for jpzt in range(len(param['pzt'])): 
 p = mdb.models['Model-1'].parts[param['name']]; curpzt=param['pzt'][jpzt]; st1='pzt'+str(jpzt+1)
 p.SectionAssignment(sectionName='Snce51', offsetField='', offsetType=MIDDLE_SURFACE, offset=0.0, 
  region=p.sets[st1+'_elt'],  thicknessAssignment=FROM_SECTION)
 p.MaterialOrientation(region=p.sets[st1+'_elt'], orientationType=GLOBAL, axis=AXIS_1,   
    additionalRotationType=ROTATION_NONE, localCsys=None, fieldName='', stackDirection=STACK_3)


# ASSEMBLY
#----------------------------------------------------------------------------  
a = mdb.models['Model-1'].rootAssembly;a.DatumCsysByDefault(CARTESIAN)
a.Instance(dependent=ON, name=param['name'],part=p)


# STEP
#---------------------------------------------------------------------------- 
mdb.models['Model-1'].ImplicitDynamicsStep(name='dyna', previous='Initial', timePeriod=simu['tend'],  
    maxNumInc=int(simu['tend']/simu['dt'][1]+1), initialInc=simu['dt'][0], minInc=simu['dt'][1], maxInc=simu['dt'][2])


# OUTPUT
#----------------------------------------------------------------------------
mdb.models['Model-1'].fieldOutputRequests['F-Output-1'].setValues(timeInterval=simu['tout'],
  variables=('S', 'EE', 'U', 'V', 'A', 'RF', 'CF','EPOT'))
#
r1 = mdb.models['Model-1'].rootAssembly.allInstances[param['name']].sets['mn_pzt']
mdb.models['Model-1'].HistoryOutputRequest(name='allpzt', createStepName='dyna',  
    variables=('EPOT', ), timeInterval=simu['tout'], 
    region=r1, sectionPoints=DEFAULT, rebar=EXCLUDE)


# LOAD
#---------------------------------------------------------------------------- 
a = mdb.models['Model-1'].rootAssembly
#
for jpzt in range(len(param['pzt'])):
 st1='pzt'+str(jpzt+1)
 #null potential
 r1 = a.instances[param['name']].sets[st1+'_nbot']
 mdb.models['Model-1'].ElectricPotentialBC(name=st1+'_Vnul', createStepName='Initial',  
    region=r1, distributionType=UNIFORM, fieldName='', magnitude=0.0)
 #applied voltage on pzt1
 if jpzt==0:
  #
  mdb.models['Model-1'].PeriodicAmplitude(name='sinus', timeSpan=STEP, 
    frequency=2*pi*param['load'][1], start=0.0, a_0=0.0, data=((0.0, 1.0), ))
  #
  r1 = a.instances[param['name']].sets[st1+'_ntop']
  mdb.models['Model-1'].ElectricPotentialBC(name=st1+'_Vapp', createStepName='dyna', 
    region=r1, fixed=OFF, distributionType=UNIFORM, fieldName='', 
    magnitude=param['load'][0], amplitude='sinus')


# JOB
#----------------------------------------------------------------------------
jobname='demo_3Dplate_with_pzt'

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
 session.viewports['Viewport: 1'].odbDisplay.display.setValues(plotState=(CONTOURS_ON_UNDEF, ))
 session.viewports['Viewport: 1'].odbDisplay.setFrame(step=0, frame=0 )
 session.viewports['Viewport: 1'].odbDisplay.setPrimaryVariable(variableLabel='U', 
    outputPosition=NODAL, refinement=(INVARIANT, 'Magnitude'), )
 session.viewports['Viewport: 1'].makeCurrent()

