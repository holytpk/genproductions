import FWCore.ParameterSet.Config as cms
import os

# Get environment variables (set by HTCondor script)
seed = int(os.getenv('NANOGEN_SEED', '123'))
outfile = os.getenv('NANOGEN_OUTFILE', 'file:nanogen_TT01j2l_SM.root')

from Configuration.Eras.Era_Run2_2018_cff import Run2_2018
process = cms.Process('NANOGEN', Run2_2018)

# Standard config loads
process.load('Configuration.StandardSequences.Services_cff')
process.load('SimGeneral.HepPDTESSource.pythiapdt_cfi')
process.load('FWCore.MessageService.MessageLogger_cfi')
process.load('Configuration.EventContent.EventContent_cff')
process.load('SimGeneral.MixingModule.mixNoPU_cfi')
process.load('Configuration.StandardSequences.GeometryRecoDB_cff')
process.load('Configuration.StandardSequences.MagneticField_cff')
process.load('Configuration.StandardSequences.Generator_cff')
process.load('IOMC.EventVertexGenerators.VtxSmearedRealistic25ns13TeVEarly2018Collision_cfi')
process.load('GeneratorInterface.Core.genFilterSummary_cff')
process.load('PhysicsTools.NanoAOD.nanogen_cff')
process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')

# Max events
process.maxEvents = cms.untracked.PSet(input = cms.untracked.int32(10000))
process.source = cms.Source("EmptySource")

process.options = cms.untracked.PSet(
    allowUnscheduled = cms.untracked.bool(False)
)

# Metadata
process.configurationMetadata = cms.untracked.PSet(
    annotation = cms.untracked.string('NanoGEN production'),
    name = cms.untracked.string('Applications'),
    version = cms.untracked.string('$Revision: 1.19 $')
)

# Output file
process.NANOAODGENoutput = cms.OutputModule("NanoAODOutputModule",
    SelectEvents = cms.untracked.PSet(
        SelectEvents = cms.vstring('generation_step')
    ),
    compressionAlgorithm = cms.untracked.string('LZMA'),
    compressionLevel = cms.untracked.int32(9),
    dataset = cms.untracked.PSet(
        dataTier = cms.untracked.string('NANOAOD'),
        filterName = cms.untracked.string('')
    ),
    fileName = cms.untracked.string(outfile),
    outputCommands = process.NANOAODGENEventContent.outputCommands
)

# Global Tag
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2018_realistic_v4', '')

# Hadronizer
process.generator = cms.EDFilter("Pythia8HadronizerFilter",
    comEnergy = cms.double(13000.0),
    maxEventsToPrint = cms.untracked.int32(1),
    pythiaHepMCVerbosity = cms.untracked.bool(False),
    pythiaPylistVerbosity = cms.untracked.int32(1),
    filterEfficiency = cms.untracked.double(1.0),
    PythiaParameters = cms.PSet(
        parameterSets = cms.vstring('pythia8CommonSettings', 'pythia8CP5Settings', 'processParameters'),
        processParameters = cms.vstring(
            'JetMatching:setMad = off',
            'JetMatching:scheme = 1',
            'JetMatching:merge = on',
            'JetMatching:jetAlgorithm = 2',
            'JetMatching:etaJetMax = 5.',
            'JetMatching:coneRadius = 1.',
            'JetMatching:slowJetPower = 1',
            'JetMatching:qCut = 30.',
            'JetMatching:nQmatch = 5',
            'JetMatching:nJetMax = 1',
            'JetMatching:doShowerKt = off'
        ),
        pythia8CommonSettings = cms.vstring(
            'Tune:preferLHAPDF = 2',
            'Main:timesAllowErrors = 10000',
            'Check:epTolErr = 0.01',
            'Beams:setProductionScalesFromLHEF = off',
            'SLHA:keepSM = on',
            'SLHA:minMassSM = 1000.',
            'ParticleDecays:limitTau0 = on',
            'ParticleDecays:tau0Max = 10',
            'ParticleDecays:allowPhotonRadiation = on'
        ),
        pythia8CP5Settings = cms.vstring(
            'Tune:pp 14',
            'Tune:ee 7',
            'MultipartonInteractions:ecmPow=0.03344',
            'MultipartonInteractions:bProfile=2',
            'MultipartonInteractions:pT0Ref=1.41',
            'MultipartonInteractions:coreRadius=0.7634',
            'MultipartonInteractions:coreFraction=0.63',
            'ColourReconnection:range=5.176',
            'SigmaTotal:zeroAXB=off',
            'SpaceShower:alphaSorder=2',
            'SpaceShower:alphaSvalue=0.118',
            'SigmaProcess:alphaSvalue=0.118',
            'SigmaProcess:alphaSorder=2',
            'MultipartonInteractions:alphaSvalue=0.118',
            'MultipartonInteractions:alphaSorder=2',
            'TimeShower:alphaSorder=2',
            'TimeShower:alphaSvalue=0.118',
            'SigmaTotal:mode = 0',
            'SigmaTotal:sigmaEl = 21.89',
            'SigmaTotal:sigmaTot = 100.309',
            'PDF:pSet=LHAPDF6:NNPDF31_nnlo_as_0118'
        )
    )
)

# External LHE Producer
process.externalLHEProducer = cms.EDProducer("ExternalLHEProducer",
    args = cms.vstring('/eos/user/l/lingqian/EFT_FullRun2/gridpack/TT01j2l_SM_slc7_amd64_gcc700_CMSSW_10_6_19_tarball.tar.xz'),
    nEvents = cms.untracked.uint32(10000),
    numberOfParameters = cms.uint32(1),
    outputFile = cms.string('cmsgrid_final.lhe'),
    scriptName = cms.FileInPath('GeneratorInterface/LHEInterface/data/run_generic_tarball_cvmfs.sh')
)

# Define paths
process.lhe_step = cms.Path(process.externalLHEProducer)
process.generation_step = cms.Path(process.pgen)
process.nanoAOD_step = cms.Path(process.nanogenSequence)
process.genfiltersummary_step = cms.EndPath(process.genFilterSummary)
process.endjob_step = cms.EndPath(process.endOfProcess)
process.NANOAODGENoutput_step = cms.EndPath(process.NANOAODGENoutput)

# Schedule
process.schedule = cms.Schedule(
    process.lhe_step,
    process.generation_step,
    process.genfiltersummary_step,
    process.nanoAOD_step,
    process.endjob_step,
    process.NANOAODGENoutput_step
)

# Prepend generator to all steps after LHE
from PhysicsTools.PatAlgos.tools.helpers import associatePatAlgosToolsTask
associatePatAlgosToolsTask(process)
for path in process.paths:
    if path != 'lhe_step':
        getattr(process, path).insert(0, process.generator)

# Apply customizations
from PhysicsTools.NanoAOD.nanogen_cff import customizeNanoGEN
process = customizeNanoGEN(process)

# Remove genWeightsTable to prevent crash due to weight mismatch
if hasattr(process, "genWeightsTable"):
    process.nanoAOD_step.remove(process.genWeightsTable)

from Configuration.DataProcessing.Utils import addMonitoring
process = addMonitoring(process)

# Seeds
process.RandomNumberGeneratorService = cms.Service("RandomNumberGeneratorService",
    externalLHEProducer = cms.PSet(
        initialSeed = cms.untracked.uint32(seed)
    ),
    generator = cms.PSet(
        initialSeed = cms.untracked.uint32(seed + 100),
        engineName = cms.untracked.string('TRandom3')
    ),
    VtxSmeared = cms.PSet(
        initialSeed = cms.untracked.uint32(seed + 200),
        engineName = cms.untracked.string('TRandom3')
    )
)

# Early deletion
from Configuration.StandardSequences.earlyDeleteSettings_cff import customiseEarlyDelete
process = customiseEarlyDelete(process)
