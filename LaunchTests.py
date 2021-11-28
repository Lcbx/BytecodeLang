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

# colors fromm blender build scripts
os.system("color")
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
TAB = '\t'
EMPTY_STR = ''


def quote(text):
	return f'{OKBLUE}{TAB}{TAB.join(text.splitlines(True))}{ENDC}'

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
		[ file for extension in extensionsToSearch
			if os.path.exists(
				file := TEST_PATH.replace(compExt.DEFAULT_CODE_EXTENSION, extension)
		)]
		
	# avoid mismatches because you used a different way of writing path of file
	return [os.path.relpath(filepath) for filepath in res]

def clean():
	for filePath in listFiles(extensionsToClean):
		vprint(f'{BOLD}cleaning{ENDC} {UNDERLINE}{filePath}{ENDC}')
		os.remove(filePath)


def generateCodeTestResults(filePath):
	vprint( f'{BOLD}testing{ENDC} {UNDERLINE}{filePath}{ENDC}')
	result = Document()
	
	def prepString(bytes):
		res = bytes.decode("utf-8")
		if res: return res.strip()
		return ""
	
	compile = runCommandLine([PythonExePath, './compiler/compiler.py', '-i', filePath], capture_output=True)
	result.compile_Out = prepString(compile.stdout)
	result.compile_Err = prepString(compile.stderr)
	
	simfilePath = filePath.replace(compExt.DEFAULT_CODE_EXTENSION, compExt.DEFAULT_COMPILED_EXTENSION)
	simulation = runCommandLine([PythonExePath, './compiler/vm_simulator.py', '-i', simfilePath], capture_output=True)
	result.simulation_Out = prepString(simulation.stdout)
	result.simulation_Err = prepString(simulation.stderr)
	
	# TODO? : use real vm on compiled bytecode and compare output with vm_simulator
	return result



def parseExpectedResults(filePath):
	expectedfile = filePath.replace(compExt.DEFAULT_CODE_EXTENSION, compExt.DEFAULT_TEST_RESULT_EXTENSION)
	
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
		print(f'{BOLD}no expected results for{ENDC} {UNDERLINE}{filePath}{ENDC}')
		vprint(f'\t expected : {expectedfile}')

def writeFile(filePath, content):
	with open(filePath,'w', newline='') as file:
		file.write(	content )

def writeExpectedResults(filePath, result):
	expectedfile = filePath.replace(compExt.DEFAULT_CODE_EXTENSION, compExt.DEFAULT_TEST_RESULT_EXTENSION)
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
	
	vprint('extensions', extensions)
	
	import argparse
	commandLineArgs = argparse.ArgumentParser(description='code tests launcher for project scripting language')
	commandLineArgs.add_argument('-i', '--input', nargs = '?',  help='path of test folder or file', default = './tests')
	commandLineArgs.add_argument('-v', '--verbose', action='store_true', default = False, help='if set will print additional execution logs')
	commandLineArgs.add_argument('-k', '--keep',    action='store_true', default = False, help='if set will keep generated files')
	commandLineArgs.add_argument('-u', '--update',  action='store_true', default = False, help='if set will update expected results')
	commandLineArgs.add_argument('-c', '--clean',   action='store_true', default = False, help='if set will only clean (and not launch tests)')
	args = commandLineArgs.parse_args()
	
	TEST_PATH = args.input
	VERBOSE = args.verbose
	vprint = print if VERBOSE else lambda a,*b:None
	
	TestsRan = 0
	TestFails = 0
	
	if not args.clean:
		vprint('files found', listFiles(extensions))

		#clean()

		for file in listFiles([compExt.DEFAULT_CODE_EXTENSION]):
			result = generateCodeTestResults(file)
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
							resultSplit = result[section].splitlines()
							expectedSplit = expected[section].splitlines()
							if len(resultSplit) != len(expectedSplit) or any( res != exp for res,  exp in zip(resultSplit, expectedSplit)):
								failed = True
								resultPresentation =  quote(result[section]) if result[section] else f'{WARNING}section was empty !{ENDC}'
								print(f'{BOLD}unexpected result in {UNDERLINE}{file}:{section}{ENDC}{ENDLINE}{resultPresentation}')
								vprint(f'{BOLD}expected :{ENDC}{ENDLINE}{quote(expected[section])}')
								if VERBOSE:
									diff = HtmlDiff()
									htmlText = diff.make_file(result[section].splitlines(), expected[section].splitlines())
									writeFile(file.replace(compExt.DEFAULT_CODE_EXTENSION, '_fail.html'), htmlText)
						else: vprint(f'results missing section {section}')
					
					sectionsMissingFromExpected = [section for section in result.keys() if section not in expected]
					if sectionsMissingFromExpected:
						vprint(f'expected results missing section {sectionsMissingFromExpected}')
				else:
					shouldPrintResult = True
			
				if failed:
					TestFails += 1
			
			if shouldPrintResult:
				print(f'{BOLD}Run results:{ENDLINE}{ENDC}{result}')
				shouldPrintSeparator = True
			
			if shouldPrintSeparator:
				print('-------------------')
		
		format = OKGREEN if TestFails == 0 else FAIL
		print(f'{format}Ran {TestsRan}{ENDC}')
		print(f'{format}Failed {TestFails}{ENDC}')
	
	if TestFails == 0 and not args.keep:
		clean()