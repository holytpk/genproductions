import FWCore.ParameterSet.Config as cms
import os

# Get environment variables (set by HTCondor script)
seed = int(os.getenv('NANOGEN_SEED', '123'))
outfile = os.getenv('NANOGEN_OUTFILE', 'file:nanogen_TT01j2lCARef_noEFT.root')

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

# Output file (dynamic)
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
    args = cms.vstring('/afs/cern.ch/user/l/lingqian/EFT_FullRun2/genproductions/bin/MadGraph5_aMCatNLO/TT01j2lCARef_noEFT_slc7_amd64_gcc700_CMSSW_10_6_19_tarball.tar.xz'),
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

from Configuration.DataProcessing.Utils import addMonitoring
process = addMonitoring(process)

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

# Reduce memory (optional)
from Configuration.StandardSequences.earlyDeleteSettings_cff import customiseEarlyDelete
process = customiseEarlyDelete(process)
named_weights = [  
"dummy # Name of first argument seems to be rwgt_1. Add dummy to fix it.",
"EFTrwgt0_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt1_ctGRe_1.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt2_ctGRe_0.0_ctGIm_1.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt3_ctGRe_0.0_ctGIm_0.0_cQj18_1.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt4_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_1.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt5_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_1.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt6_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_1.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt7_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_1.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt8_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_1.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt9_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_1.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt10_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_1.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt11_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_1.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt12_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_1.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt13_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_1.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt14_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_1.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt15_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_1.0_cQd1_0.0",
"EFTrwgt16_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_1.0",
"EFTrwgt17_ctGRe_2.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt18_ctGRe_1.0_ctGIm_1.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt19_ctGRe_1.0_ctGIm_0.0_cQj18_1.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt20_ctGRe_1.0_ctGIm_0.0_cQj18_0.0_cQj38_1.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt21_ctGRe_1.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_1.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt22_ctGRe_1.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_1.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt23_ctGRe_1.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_1.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt24_ctGRe_1.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_1.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt25_ctGRe_1.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_1.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt26_ctGRe_1.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_1.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt27_ctGRe_1.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_1.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt28_ctGRe_1.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_1.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt29_ctGRe_1.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_1.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt30_ctGRe_1.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_1.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt31_ctGRe_1.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_1.0_cQd1_0.0",
"EFTrwgt32_ctGRe_1.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_1.0",
"EFTrwgt33_ctGRe_0.0_ctGIm_2.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt34_ctGRe_0.0_ctGIm_1.0_cQj18_1.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt35_ctGRe_0.0_ctGIm_1.0_cQj18_0.0_cQj38_1.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt36_ctGRe_0.0_ctGIm_1.0_cQj18_0.0_cQj38_0.0_cQj11_1.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt37_ctGRe_0.0_ctGIm_1.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_1.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt38_ctGRe_0.0_ctGIm_1.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_1.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt39_ctGRe_0.0_ctGIm_1.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_1.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt40_ctGRe_0.0_ctGIm_1.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_1.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt41_ctGRe_0.0_ctGIm_1.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_1.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt42_ctGRe_0.0_ctGIm_1.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_1.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt43_ctGRe_0.0_ctGIm_1.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_1.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt44_ctGRe_0.0_ctGIm_1.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_1.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt45_ctGRe_0.0_ctGIm_1.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_1.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt46_ctGRe_0.0_ctGIm_1.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_1.0_cQd1_0.0",
"EFTrwgt47_ctGRe_0.0_ctGIm_1.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_1.0",
"EFTrwgt48_ctGRe_0.0_ctGIm_0.0_cQj18_2.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt49_ctGRe_0.0_ctGIm_0.0_cQj18_1.0_cQj38_1.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt50_ctGRe_0.0_ctGIm_0.0_cQj18_1.0_cQj38_0.0_cQj11_1.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt51_ctGRe_0.0_ctGIm_0.0_cQj18_1.0_cQj38_0.0_cQj11_0.0_cQj31_1.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt52_ctGRe_0.0_ctGIm_0.0_cQj18_1.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_1.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt53_ctGRe_0.0_ctGIm_0.0_cQj18_1.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_1.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt54_ctGRe_0.0_ctGIm_0.0_cQj18_1.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_1.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt55_ctGRe_0.0_ctGIm_0.0_cQj18_1.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_1.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt56_ctGRe_0.0_ctGIm_0.0_cQj18_1.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_1.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt57_ctGRe_0.0_ctGIm_0.0_cQj18_1.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_1.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt58_ctGRe_0.0_ctGIm_0.0_cQj18_1.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_1.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt59_ctGRe_0.0_ctGIm_0.0_cQj18_1.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_1.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt60_ctGRe_0.0_ctGIm_0.0_cQj18_1.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_1.0_cQd1_0.0",
"EFTrwgt61_ctGRe_0.0_ctGIm_0.0_cQj18_1.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_1.0",
"EFTrwgt62_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_2.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt63_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_1.0_cQj11_1.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt64_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_1.0_cQj11_0.0_cQj31_1.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt65_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_1.0_cQj11_0.0_cQj31_0.0_ctu8_1.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt66_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_1.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_1.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt67_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_1.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_1.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt68_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_1.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_1.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt69_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_1.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_1.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt70_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_1.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_1.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt71_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_1.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_1.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt72_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_1.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_1.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt73_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_1.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_1.0_cQd1_0.0",
"EFTrwgt74_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_1.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_1.0",
"EFTrwgt75_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_2.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt76_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_1.0_cQj31_1.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt77_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_1.0_cQj31_0.0_ctu8_1.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt78_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_1.0_cQj31_0.0_ctu8_0.0_ctd8_1.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt79_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_1.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_1.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt80_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_1.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_1.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt81_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_1.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_1.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt82_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_1.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_1.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt83_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_1.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_1.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt84_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_1.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_1.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt85_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_1.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_1.0_cQd1_0.0",
"EFTrwgt86_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_1.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_1.0",
"EFTrwgt87_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_2.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt88_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_1.0_ctu8_1.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt89_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_1.0_ctu8_0.0_ctd8_1.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt90_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_1.0_ctu8_0.0_ctd8_0.0_ctj8_1.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt91_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_1.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_1.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt92_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_1.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_1.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt93_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_1.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_1.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt94_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_1.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_1.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt95_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_1.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_1.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt96_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_1.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_1.0_cQd1_0.0",
"EFTrwgt97_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_1.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_1.0",
"EFTrwgt98_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_2.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt99_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_1.0_ctd8_1.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt100_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_1.0_ctd8_0.0_ctj8_1.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt101_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_1.0_ctd8_0.0_ctj8_0.0_cQu8_1.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt102_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_1.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_1.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt103_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_1.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_1.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt104_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_1.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_1.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt105_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_1.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_1.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt106_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_1.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_1.0_cQd1_0.0",
"EFTrwgt107_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_1.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_1.0",
"EFTrwgt108_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_2.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt109_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_1.0_ctj8_1.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt110_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_1.0_ctj8_0.0_cQu8_1.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt111_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_1.0_ctj8_0.0_cQu8_0.0_cQd8_1.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt112_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_1.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_1.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt113_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_1.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_1.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt114_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_1.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_1.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt115_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_1.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_1.0_cQd1_0.0",
"EFTrwgt116_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_1.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_1.0",
"EFTrwgt117_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_2.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt118_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_1.0_cQu8_1.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt119_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_1.0_cQu8_0.0_cQd8_1.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt120_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_1.0_cQu8_0.0_cQd8_0.0_ctu1_1.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt121_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_1.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_1.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt122_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_1.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_1.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt123_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_1.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_1.0_cQd1_0.0",
"EFTrwgt124_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_1.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_1.0",
"EFTrwgt125_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_2.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt126_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_1.0_cQd8_1.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt127_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_1.0_cQd8_0.0_ctu1_1.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt128_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_1.0_cQd8_0.0_ctu1_0.0_ctd1_1.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt129_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_1.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_1.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt130_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_1.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_1.0_cQd1_0.0",
"EFTrwgt131_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_1.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_1.0",
"EFTrwgt132_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_2.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt133_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_1.0_ctu1_1.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt134_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_1.0_ctu1_0.0_ctd1_1.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt135_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_1.0_ctu1_0.0_ctd1_0.0_ctj1_1.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt136_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_1.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_1.0_cQd1_0.0",
"EFTrwgt137_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_1.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_1.0",
"EFTrwgt138_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_2.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt139_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_1.0_ctd1_1.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt140_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_1.0_ctd1_0.0_ctj1_1.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt141_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_1.0_ctd1_0.0_ctj1_0.0_cQu1_1.0_cQd1_0.0",
"EFTrwgt142_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_1.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_1.0",
"EFTrwgt143_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_2.0_ctj1_0.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt144_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_1.0_ctj1_1.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt145_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_1.0_ctj1_0.0_cQu1_1.0_cQd1_0.0",
"EFTrwgt146_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_1.0_ctj1_0.0_cQu1_0.0_cQd1_1.0",
"EFTrwgt147_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_2.0_cQu1_0.0_cQd1_0.0",
"EFTrwgt148_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_1.0_cQu1_1.0_cQd1_0.0",
"EFTrwgt149_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_1.0_cQu1_0.0_cQd1_1.0",
"EFTrwgt150_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_2.0_cQd1_0.0",
"EFTrwgt151_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_1.0_cQd1_1.0",
"EFTrwgt152_ctGRe_0.0_ctGIm_0.0_cQj18_0.0_cQj38_0.0_cQj11_0.0_cQj31_0.0_ctu8_0.0_ctd8_0.0_ctj8_0.0_cQu8_0.0_cQd8_0.0_ctu1_0.0_ctd1_0.0_ctj1_0.0_cQu1_0.0_cQd1_2.0",
]
process.genWeightsTable.namedWeightIDs = named_weights
process.genWeightsTable.namedWeightLabels = named_weights
