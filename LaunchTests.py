import compiler.extensions as compExt
import os
from subprocess import run as runCommandLine
from sys import executable as Python
from difflib import HtmlDiff

# set by argparse when script is main
# pre-set here in case someone imports this script
VERBOSE = False 
TEST_FOLDER = './tests'
SECTION_SPLITTER = '__SECTION__'

# trick for verbosity
vprint = print if VERBOSE else lambda a,*b:None


def quote(text):
	return '\t' + '\t'.join(text.splitlines(True))

# to allow different dynamic sections
class Document(dict):
	__getattr__= dict.__getitem__
	__setattr__= dict.__setitem__
	
	def __str__(self):
		endline = '\n'
		return endline.join( [ f'{section}: { endline if (content and endline in content) else "" }{quote(content)}' for section, content in self.items()] )


# generates a list of files in test folder with extensionsToSearch
def listFiles(extensionsToSearch):
	return [os.path.join(root, file)
			for root, dirs, files in os.walk(TEST_FOLDER)
				for file in files
					if any(
						file.endswith(ext) for ext in extensionsToSearch
					) ]
	
def clean():
	for file in listFiles(extensionsToClean):
		vprint('cleaning', file)
		os.remove(file)


def generateCodeTestResults(filePath):
	vprint( 'testing', filePath)
	result = Document()
	
	def prepString(bytes):
		res = bytes.decode("utf-8")
		if res: return res.strip()
		return ""
	
	compile = runCommandLine([Python, './compiler/compiler.py', '-i', filePath], capture_output=True)
	result.compile_Out = prepString(compile.stdout)
	result.compile_Err = prepString(compile.stderr)
	
	simulation = runCommandLine([Python, './compiler/vm_simulator.py', '-i', filePath], capture_output=True)
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
			sectionName, _, sectionContent = section.partition(':\n')
			result[sectionName.strip()] = sectionContent
		vprint(f'parsed :\n{result}')
		return result
	else:
		print(f'no expected results for {filePath}')
		vprint(f'\t expected : {expectedfile}')

def writeFile(filePath, content):
	with open(filePath,'w', newline='') as file:
		file.write(	content )

def writeExpectedResults(filePath, result):
	expectedfile = filePath.replace(compExt.DEFAULT_CODE_EXTENSION, compExt.DEFAULT_TEST_RESULT_EXTENSION)
	res = f'\n{SECTION_SPLITTER}\n'.join([ f'{key}:\n{value}'for key, value in result.items()])
	vprint(f'writing:\n{quote(res)}')
	writeFile(expectedfile, res)


if __name__ == '__main__':

	extensions = [getattr(compExt, item)
				  for item in dir(compExt)
					if not item.startswith('__')]
	
	extensionsToClean = [ext
						 for ext in extensions
							if  ext not in ( compExt.DEFAULT_CODE_EXTENSION,
											 compExt.DEFAULT_TEST_RESULT_EXTENSION ) ] +['.html'] # for verbose diff
	
	vprint('extensions', extensions)
	
	import argparse
	commandLineArgs = argparse.ArgumentParser(description='code tests launcher for project scripting language')
	commandLineArgs.add_argument('-i', '--input', nargs = '?',  help='path of test folder', default = './tests')
	commandLineArgs.add_argument('-v', '--verbose', action='store_true', default = False, help='if set will print additional execution logs')
	commandLineArgs.add_argument('-k', '--keep',    action='store_true', default = False, help='if set will keep generated files')
	commandLineArgs.add_argument('-u', '--update',  action='store_true', default = False, help='if set will update expected results')
	commandLineArgs.add_argument('-c', '--clean',   action='store_true', default = False, help='if set will only clean (and not launch tests)')
	args = commandLineArgs.parse_args()
	
	TEST_FOLDER = args.input
	VERBOSE = args.verbose
	vprint = print if VERBOSE else lambda a,*b:None
	
	if not args.clean:
		vprint('files found', listFiles(extensions))

		#clean()
		
		TestsRan = 0
		TestFails = 0

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
				
				if expected:
					for section, content in expected.items():
						if section in result:
							resultSplit = result[section].splitlines()
							expectedSplit = expected[section].splitlines()
							if any( res != exp for res, exp in zip(resultSplit,expectedSplit)):
								print(f'unexpected result {file}:{section}\n{quote(result[section])}')
								vprint(f'expected :\n{quote(expected[section])}')
								TestFails +=1
								if VERBOSE:
									diff = HtmlDiff()
									htmlText = diff.make_file(result[section].splitlines(), expected[section].splitlines())
									writeFile(file.replace(compExt.DEFAULT_CODE_EXTENSION, '_fail.html'), htmlText)
								break
						else: vprint(f'results missing section {section}')
					
					sectionsMissingFromExpected = [section for section in result.keys() if section not in expected]
					if sectionsMissingFromExpected:
						vprint(f'expected results missing section {sectionsMissingFromExpected}')
				else:
					shouldPrintResult = True
			
			
			if shouldPrintResult:
				print(f'results:\n{result}')
				shouldPrintSeparator = True
			
			if shouldPrintSeparator:
				print('-------------------')
			
		print(f'Ran {TestsRan}')
		print(f'Failed {TestFails}')
	
	if TestFails == 0 and not args.keep:
		clean()