import compiler.extensions as compExt
import os

# TODO : use argparse
TEST_FOLDER = "./tests"
verbose = True
keepIntermediaryFiles = False

# trick for verbosity
vprint = print if verbose else lambda a,b:None


extensions = [getattr(compExt, item) for item in dir(compExt) if not item.startswith("__")]
extensionsToClean = [ext for ext in extensions if compExt.DEFAULT_CODE_EXTENSION != ext != compExt.DEFAULT_TEST_RESULT_EXTENSION ]
vprint("extensions", extensions)


# generates a list of files in test folder with extensionsToSearch
def walkTests(extensionsToSearch):
	return [os.path.join(root, file) for root, dirs, files in os.walk(TEST_FOLDER) for file in files if any(file.endswith(ext) for ext in extensionsToSearch) ]
	
	
def clean():
	for file in walkTests(extensionsToClean):
		vprint("cleaning", file)
		#os.remove(file)


def generateCodeTestResults(filePath):
	vprint( "testing", filePath)
	# TODO : use subprocess to compile
	# TODO : use vm_simulator on compiled bytecode
	# TODO : catch any exceptions
	# TODO : add option to save results as expected results
	# TODO : compare any generated result with expected
	# TODO? : use real vm on compiled bytecode and compare output with vm_simulator


if __name__ == '__main__':
	vprint("files", walkTests(extensions))

	clean()

	for file in walkTests([compExt.DEFAULT_CODE_EXTENSION]):
		generateCodeTestResults(file)
	
	if not keepIntermediaryFiles:
		clean()