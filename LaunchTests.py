import compiler.extensions as compExt
import os


# set by argparse when script is main
# pre-set here in case someone imports this script
VERBOSE = True 
TEST_FOLDER = './tests'

# trick for verbosity
vprint = print if VERBOSE else lambda a,b:None

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
		#os.remove(file)


def generateCodeTestResults(filePath):
	vprint( 'testing', filePath)
	# TODO : use subprocess to compile
	# TODO : use vm_simulator on compiled bytecode
	# TODO : catch any exceptions
	# TODO : add option to save results as expected results
	# TODO : compare any generated result with expected
	# TODO? : use real vm on compiled bytecode and compare output with vm_simulator

def parseExpectedResults(filePath):
	vprint('retrieving expected results')
	expectedfile = filePath.replace(compExt.DEFAULT_CODE_EXTENSION, compExt.DEFAULT_TEST_RESULT_EXTENSION)
	vprint('expected reulst file name', expectedfile)


if __name__ == '__main__':

	extensions = [getattr(compExt, item)
				  for item in dir(compExt)
					if not item.startswith('__')]
	
	extensionsToClean = [ext
						 for ext in extensions
							if  ext != compExt.DEFAULT_CODE_EXTENSION
							and ext != compExt.DEFAULT_TEST_RESULT_EXTENSION ]
	
	vprint('extensions', extensions)
	
	import argparse
	commandLineArgs = argparse.ArgumentParser(description='code tests launcher for project scripting language')
	commandLineArgs.add_argument('-i', '--input', nargs = '?',  help='path of test folder', default = './tests')
	commandLineArgs.add_argument('-v', '--verbose', nargs = '?', help='if set will print additional execution logs', default = True )
	commandLineArgs.add_argument('-k', '--keep', nargs = '?', help='if set will keep generated files', default = False )
	commandLineArgs.add_argument('-u', '--update', nargs = '?', help='if set will update expected results', default = True )
	commandLineArgs.add_argument('-c', '--clean', nargs = '?', help='if set will only clean (and not launch tests)', default = False )
	args = commandLineArgs.parse_args()
	VERBOSE = args.verbose
	TEST_FOLDER = args.input
	
	if not args.clean:
		vprint('files found', listFiles(extensions))

		#clean()

		for file in listFiles([compExt.DEFAULT_CODE_EXTENSION]):
			generateCodeTestResults(file)
	
	if not args.keep:
		clean()