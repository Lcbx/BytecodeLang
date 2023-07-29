import compiler.extensions as compExt
import os
from subprocess import run as runCommandLine
from sys import executable as PythonExePath
from difflib import HtmlDiff

# set by argparse when script is main
# pre-set here in case someone imports this script
VERBOSE = False 
TEST_PATH = './tests'
SECTION_SPLITTER = '__SECTION__'

# trick for verbosity
vprint = print if VERBOSE else lambda a,*b:None

# formats from blender build scripts
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

ENDLINE = '\n'
SPACEx2 = '  '
TAB = '\t'
EMPTY_STR = ''


def quote(text):
	return f'{OKBLUE}{SPACEx2}{SPACEx2.join(text.splitlines(True))}{ENDC}'

# to allow different dynamic sections
class Document(dict):
	__getattr__= dict.__getitem__
	__setattr__= dict.__setitem__
	
	def __str__(self):
		return ENDLINE.join( [ f'{section}:{ENDLINE + quote(content)if content else EMPTY_STR}' for section, content in self.items()] )


# generates a list of files in test folder that match extensionsToSearch
def listFiles(extensionsToSearch):
	res = None
	# if TEST_PATH is folder, find all files with extensions within
	if os.path.isdir(TEST_PATH):
		res = [ os.path.join(root, file)
				for root, dirs, files in os.walk(TEST_PATH)
					for file in files
						if any(	file.endswith(ext) for ext in extensionsToSearch )
				]
	# if TEST_PATH is file, find files with same name and different extensions
	else:
		res = [
			file for extension in extensionsToSearch
				if os.path.exists(
					file := TEST_PATH.replace(compExt.DEFAULT_CODE_EXTENSION, extension)
		)]
	# avoid mismatches because you used a different way of writing path of file
	return [os.path.relpath(filepath).replace('\\', '/') for filepath in res]

def clean():
	for filePath in listFiles(extensionsToClean):
		vprint(f'{BOLD}cleaning{ENDC} {UNDERLINE}{filePath}{ENDC}')
		os.remove(filePath)

def tokenize():
	for filePath in listFiles([compExt.DEFAULT_CODE_EXTENSION]):
		vprint(f'{BOLD}tokenizing{ENDC} {UNDERLINE}{filePath}{ENDC}')
		trace = runCommandLine([PythonExePath, './compiler/tokenizer.py', '-' + ('v' if VERBOSE else '') + 'i', filePath], capture_output=True)
		if trace.stdout or trace.stderr:
			print(_prepString(trace.stdout) )
			print(_prepString(trace.stderr) )


def _prepString(bytes):
	res = bytes.decode("utf-8")
	if res: return res.strip()
	return ""

def generateCodeTestResults(filePath):
	vprint( f'{BOLD}testing{ENDC} {UNDERLINE}{filePath}{ENDC}')
	result = Document()
	
	tokenize = runCommandLine([PythonExePath, './compiler/tokenizer.py', '-v', filePath], capture_output=True)
	result.tokenize_Out = _prepString(tokenize.stdout)
	result.tokenize_Err = _prepString(tokenize.stderr)
	
	compile = runCommandLine([PythonExePath, './compiler/compiler.py', '-v', filePath], capture_output=True)
	result.compile_Out = _prepString(compile.stdout)
	result.compile_Err = _prepString(compile.stderr)
	
	simfilePath = filePath.replace(compExt.DEFAULT_CODE_EXTENSION, compExt.DEFAULT_COMPILED_EXTENSION)
	simulation = runCommandLine([PythonExePath, './compiler/vm_simulator.py', '-b', "300", simfilePath], capture_output=True)
	result.simulation_Out = _prepString(simulation.stdout)
	result.simulation_Err = _prepString(simulation.stderr)
	
	# TODO? : use real vm on compiled bytecode and compare output with vm_simulator
	return result

def GetExpectedResultsFilePath(filePath):
	basename = os.path.basename(filePath)
	return filePath.replace(basename, '_'+basename).replace(compExt.DEFAULT_CODE_EXTENSION, compExt.DEFAULT_TEST_RESULT_EXTENSION)

def parseExpectedResults(filePath):
	expectedfile = GetExpectedResultsFilePath(filePath)
	
	def readFile(filePath):
		with open(filePath,'r') as file:
			return file.read()
	
	if os.path.exists(expectedfile):
		result = Document()
		for section in readFile(expectedfile).split(SECTION_SPLITTER):
			sectionName, _, sectionContent = section.partition(f':{ENDLINE}')
			result[sectionName.strip()] = sectionContent.strip()
		vprint( f'{BOLD}parsed :{ENDC}{ENDLINE}{result}')
		return result
	else:
		print(f'{BOLD}expected results {WARNING}missing{ENDC} : {UNDERLINE}{filePath}{ENDC}')
		vprint(f'\t expected : {expectedfile}')

def writeFile(filePath, content):
	with open(filePath,'w', newline='') as file:
		file.write(	content )

def writeExpectedResults(filePath, result):
	expectedfile = GetExpectedResultsFilePath(filePath)
	res = f'{ENDLINE}{SECTION_SPLITTER}{ENDLINE}'.join([ f'{key}:{ENDLINE}{value}'for key, value in result.items()])
	vprint(f'writing:{ENDLINE}{quote(res)}')
	writeFile(expectedfile, res)


if __name__ == '__main__':
	extensions = [getattr(compExt, item)
				  for item in dir(compExt)
					if not item.startswith('__')]
	
	extensionsToClean = [ext for ext in extensions
						if  ext not in ( compExt.DEFAULT_CODE_EXTENSION,
										 compExt.DEFAULT_TEST_RESULT_EXTENSION ) ] +['.html'] # for verbose diff
	
	import argparse
	commandLineArgs = argparse.ArgumentParser(description='code tests launcher for project scripting language')
	commandLineArgs.add_argument('filepath', nargs = '?',  help='path of test folder or file', default = './tests')
	commandLineArgs.add_argument('-v', '--verbose', action='store_true', default = False, help='print additional execution logs')
	commandLineArgs.add_argument('-k', '--keep',    action='store_true', default = False, help='keep generated files')
	commandLineArgs.add_argument('-u', '--update',  action='store_true', default = False, help='update expected results')
	commandLineArgs.add_argument('-t', '--tokenize',action='store_true', default = False, help='only tokenize code (and not launch tests)')
	commandLineArgs.add_argument('-c', '--clean',   action='store_true', default = False, help='only clean (and not launch tests)')
	args = commandLineArgs.parse_args()
	
	TEST_PATH = args.filepath
	VERBOSE = args.verbose
	vprint = print if VERBOSE else lambda a,*b:None
	
	vprint('extensions', extensions)
	
	TestsRan = 0
	TestFails = 0
	
	if not args.clean and not args.tokenize:
		vprint('files found', listFiles(extensions))

		for file in listFiles([compExt.DEFAULT_CODE_EXTENSION]):
			result = generateCodeTestResults(file)
			expected = None
			TestsRan +=1
			shouldPrintResult = False
			shouldPrintSeparator = VERBOSE
			
			if result and args.update:
				writeExpectedResults(file, result)
				if VERBOSE:
					shouldPrintResult = True
			elif result:
				expected = parseExpectedResults(file)
				failed = False
				
				if expected:
					for section, content in expected.items():
						if section in result:
							resultSplit =   result[section].replace(  ', ', f',{ENDLINE}').splitlines()
							expectedSplit = expected[section].replace(', ', f',{ENDLINE}').splitlines()
							if len(resultSplit) != len(expectedSplit) or any( res != exp for res,  exp in zip(resultSplit, expectedSplit)):
								failed = True
								resultPresentation =  quote(result[section]) if result[section] else f'{WARNING}section was empty !{ENDC}'
								print(f'{BOLD}result was {WARNING}unexpected{ENDC} : {UNDERLINE}{file}{ENDC} ({section}){ENDLINE}{resultPresentation}')
								print(f'{BOLD}expected :{ENDC}{ENDLINE}{quote(expected[section])}')
								if VERBOSE or args.keep:
									diff = HtmlDiff()
									htmlText = diff.make_file(resultSplit, expectedSplit)
									writeFile(file.replace(compExt.DEFAULT_CODE_EXTENSION, f'_{section}.html'), htmlText)
						else: print(f'{BOLD}{WARNING}results missing section {section}{ENDC}')
					
					sectionsMissingFromExpected = [section for section in result.keys() if section not in expected]
					if sectionsMissingFromExpected:
						vprint(f'expected results missing section {sectionsMissingFromExpected}')
			
				if failed:
					TestFails += 1
			
			if not expected:
				shouldPrintResult = True
				if TestFails == 0 and not VERBOSE:
					# do some prioritising (compiler errors first, then simulation)
					candidates = [ result.compile_Err, None if "0 errors" in result.compile_Out else result.compile_Out, result.simulation_Err, result.simulation_Out ]
					result = next(filter(lambda x:x, candidates))
			
			if shouldPrintResult:
				print(f'{BOLD}Run results:{ENDLINE}{ENDC}{result}')
				shouldPrintSeparator = True
			
			if shouldPrintSeparator:
				print('-------------------')
		
		format = OKGREEN if TestFails == 0 else FAIL
		print(f'{format}Ran {TestsRan}{ENDC}')
		print(f'{format}Failed {TestFails}{ENDC}')
	
	if args.tokenize:
		tokenize()
	elif TestFails == 0 and not args.keep:
		clean()