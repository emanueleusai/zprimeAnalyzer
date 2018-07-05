import os,sys,fnmatch

thisDir = os.getcwd()
templateDir = thisDir+'/../makeTemplates/templates_2018_4_29'
thetaConfigTemp = thisDir+'/theta_config_template.py'
lumiInFile = '36p0fb'

toFilter0 = []#['pileup','jec','jer','jms','jmr','tau21','taupt','topsf','toppt','muRFcorrdNew','pdfNew','trigeff','btag','mistag']#,'jsf'
toFilter0 = ['__'+item+'__' for item in toFilter0]

limitConfs = {#'<limit type>':[filter list]
			  'all':[],
# 			  'isE':['isM'], #only electron channel
# 			  'isM':['isE'], #only muon channel
			  }

limitType = '_test'
outputDir = '/user_data/ssagir/Zprime_limits_2018/'+templateDir.split('/')[-1]+limitType+'/' #prevent writing these (they are large) to brux6 common area
if not os.path.exists(outputDir): os.system('mkdir '+outputDir)
print outputDir

def findfiles(path, filtre):
    for root, dirs, files in os.walk(path):
        for f in fnmatch.filter(files, filtre):
            yield os.path.join(root, f)
            
rootfilelist = []
i=0
for rootfile in findfiles(templateDir, '*.root'):
    if 'rebinned_stat0p5.' not in rootfile: continue
    if 'plots' in rootfile: continue
    if 'YLD' in rootfile: continue
    rootfilelist.append(rootfile)
    i+=1

f = open(thetaConfigTemp, 'rU')
thetaConfigLines = f.readlines()
f.close()

def makeThetaConfig(rFile,outDir,toFilter):
	with open(outDir+'/'+rFile.split('/')[-1].replace('.root','.py'),'w') as fout:
		for line in thetaConfigLines:
			if line.startswith('input ='): fout.write('input = \''+rFile+'\'')
			elif line.startswith('    model = build_model_from_rootfile('): 
				if len(toFilter)!=0:
					model='    model = build_model_from_rootfile(input,include_mc_uncertainties=True,histogram_filter = (lambda s:  s.count(\''+toFilter[0]+'\')==0'
					for item in toFilter: 
						if item!=toFilter[0]: model+=' and s.count(\''+item+'\')==0'
					model+='))'
					fout.write(model)
				else: fout.write(line)
			else: fout.write(line)
	with open(outDir+'/'+rFile.split('/')[-1].replace('.root','.sh'),'w') as fout:
		fout.write('#!/bin/sh \n')
		fout.write('cd /home/ssagir/CMSSW_7_3_0/src/\n')
		fout.write('source /cvmfs/cms.cern.ch/cmsset_default.sh\n')
		fout.write('cmsenv\n')
		fout.write('cd '+outDir+'\n')
		fout.write('/home/ssagir/CMSSW_7_3_0/src/theta/utils/theta-auto.py ' + outDir+'/'+rFile.split('/')[-1].replace('.root','.py'))

count=0
for limitConf in limitConfs:
	toFilter = toFilter0 + limitConfs[limitConf]
	print limitConf,'=',toFilter
	for file in rootfilelist:
		fileName = file.split('/')[-1]
		signal = fileName.split('_')[2]
		BRStr = fileName[fileName.find(signal)+len(signal):fileName.find('_'+lumiInFile)]
		outDir = outputDir+limitConf+BRStr+'/'
		print signal,BRStr
		if not os.path.exists(outDir): os.system('mkdir '+outDir)
		os.chdir(outDir)
		fileDir = ''
		if templateDir.split('/')[-1]!=file.split('/')[-2]:
			fileDir = file.split('/')[-2]
			if not os.path.exists(outDir+fileDir): os.system('mkdir '+fileDir)
			os.chdir(fileDir)
		outDir=outDir+fileDir
		makeThetaConfig(file,outDir,toFilter)

		dict={'configdir':outDir,'configfile':file.split('/')[-1].replace('.root','')}

		jdf=open(file.split('/')[-1].replace('.root','.job'),'w')
		jdf.write(
"""universe = vanilla
Executable = %(configfile)s.sh
Should_Transfer_Files = YES
WhenToTransferOutput = ON_EXIT
Notification = Error
request_memory = 3072
Output = %(configfile)s.out
Error = %(configfile)s.err
Log = %(configfile)s.log

Queue 1"""%dict)
		jdf.close()

		os.system('chmod +x '+file.split('/')[-1].replace('.root','.sh'))
		os.system('condor_submit '+file.split('/')[-1].replace('.root','.job'))
		os.chdir('..')
		count+=1
print "Total number of jobs submitted:", count
                  
