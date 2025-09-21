import os
import subprocess
import sys
import shutil
import time

IS_TEST_ENV=False

LIST_TODO_FILENAME = "todo.txt"
LIST_SUCCESS_FILENAME = "successful.txt"
LIST_FAILED_FILENAME = "failed.txt"


def get_just_app_name(app: str, is_test_env: bool) -> str:
    if is_test_env:
        return app
    else:
        return app.strip('=').split('/')[-1]

def check_utilities_exist() -> None:
    # Check for emerge
    if shutil.which("emerge") is None:
        print("check_utilities_exist(): emerge utility not accessible, exiting...")
        sys.exit(2)

def make_lists_if_not_exist(listsDir: str) -> None:
    # Create each list file if it does not exist
    for listFileName in [LIST_TODO_FILENAME, LIST_SUCCESS_FILENAME, LIST_FAILED_FILENAME]:
        if not os.path.exists(listsDir + listFileName):
            try:
                open(listsDir + listFileName, 'a').close()
            except OSError as error:
                print("[ERROR] Failed to create list file at: {0}, exiting...".format(listsDir + listFileName))
                sys.exit(2)

def parse_application_list(is_test_env: bool) -> list[str]:
        appListResult = None
        if is_test_env == False:
            appListResult = subprocess.run(["emerge", "--pretend", "--emptytree", "@world"], capture_output=True, text=True)
        else:
            print("FEDORA: Passing list: ", FEDORA_TEST_CMD.split())
            appListResult = subprocess.run(FEDORA_TEST_CMD.split(), capture_output=True, text=True, shell=False)

        if appListResult.returncode != 0:
            print("Failed to gather application list:")
            print("[STDOUT]")
            print(appListResult.stdout)
            print("[STDERR]")
            print(appListResult.stderr)
            sys.exit(3)

        print("Successfully gathered the application list!")

        tmpAppList = None
        appList = []

        if is_test_env:
            tmpAppList = appListResult.stdout.strip('"\'\"').split("@")
            for app in tmpAppList:
                if (len(app) >= 1):
                    appList.append(app[2:])
        else:
            tempAppList1 = appListResult.stdout.split("\n")
            tempAppList2 = []

            # Remove non-package lines
            for line in tempAppList1:
                if len(line) > 3 and line[:2] == "[e":
                    tempAppList2.append(line)
            
            #Split so only package category and name are left
            packageCatNameList = []
            for line in tempAppList2:
                packageCatNameList.append(line[15:].split(" ")[1])
                print("Have package:", packageCatNameList[-1])
                time.sleep(.01)
                
            # Strip repo from package name
            strippedPackageCatNameList = []
            for line in packageCatNameList:
                appList.append(line[:line.find(":")])
            
            print("New output: ", tempAppList1)

        
        return appList

def create_failure_dir(dir: str, appName: str, processResult: subprocess.CompletedProcess) -> None:
    failDirName = dir + get_just_app_name(appName, False)
    srcBuildLogPath = "/var/tmp/portage/" + appName + "/temp/build.log"
    srcEnvLogPath = "/var/tmp/portage/" + appName + "/temp/environment"
    destBuildLogPath = failDirName + "build.log"
    destEnvLogPath = failDirName + "environment"
    stdoutFileName = failDirName + "stdout.txt"
    stderrFileName = failDirName + "stderr.txt"

    if not os.path.exists(failDirName):
        try:
            os.mkdir(failDirName)
        except OSError as error:
            print("[ERROR] Failed to create directory ({0}) for failed package: {1} exiting...".format(failDirName, appName))
            sys.exit(2)
    else:
        #delete existing files in dir
        if os.path.exists(destBuildLogPath):
            os.remove(destBuildLogPath)
        if os.path.exists(destEnvLogPath):
            os.remove(destEnvLogPath)
        if os.path.exists(stdoutFileName):
            os.remove(stdoutFileName)
        if os.path.exists(stderrFileName):
            os.remove(stderrFileName)

    #Add stdout to file
    with open(stdoutFileName, "+wt") as stdoutFile:
        stdoutFile.writelines(processResult.stdout)

    #Add stderr to file
    with open(stderrFileName, "+wt") as stderrFile:
        stderrFile.writelines(processResult.stderr)
    
    #Copy build log and environment for failed emerge to this dir
    #appName should contain the category as well

    if os.path.exists(srcBuildLogPath):
        try:
            shutil.copyfile(srcBuildLogPath, destBuildLogPath)
        except OSError as error:
            print("[ERROR] Failed to copy build.log at: {0} for failed package: {1}".format(srcBuildLogPath, appName))
    else:
        print("[ERROR] Failed to locate build.log at: {0} for failed package: {1}".format(srcBuildLogPath, appName))

    if os.path.exists(srcEnvLogPath):
        try:
            shutil.copyfile(srcEnvLogPath, destEnvLogPath)
        except OSError as error:
            print("[ERROR] Failed to copy environment at: {0} for failed package: {1}".format(srcEnvLogPath, appName))
    else:
        print("[ERROR] Failed to locate environment at: {0} for failed package: {1}".format(srcEnvLogPath, appName))
    

if __name__ == "__main__":
    DIRECTORY = "/root/.local/share/world_lists/"
    IS_FIRST_RUN = True
    EMERGE_REBUILD_COMMAND="emerge -v --oneshot ="
    FEDORA_TEST_CMD="dnf repoquery --userinstalled --qf \"%{name}@\""

    # Parse Arguments
    for i in range(len(sys.argv)):
        if sys.argv[i] == "--dir":
            if i + 1 < len(sys.argv):
                DIRECTORY = sys.argv[i+1]
                #append seperator if not there already
                if DIRECTORY[-1] != '/':
                    DIRECTORY = DIRECTORY + '/'
            else:
                print("[ERROR] Missing Directory!!")
                sys.exit(1)
        elif sys.argv[i] == "--continue":
            IS_FIRST_RUN = False
            
    # Create output directory if it does not exist
    if IS_FIRST_RUN == False and (os.path.exists(DIRECTORY) == False or os.path.exists(DIRECTORY + LIST_TODO_FILENAME) == False):
        print("[ERROR] continue flag added, but directory and/or todo list does not exist!")
        sys.exit(2)
    elif IS_FIRST_RUN == True and os.path.exists(DIRECTORY) == False:
        try:
            os.mkdir(DIRECTORY)
        except OSError as error:
            print("[ERROR] Failed to create output directory, exiting...")
            sys.exit(2)
    else:
        print("Output directory found! Continuing")
    
    if not IS_TEST_ENV:
        check_utilities_exist()

    currentEmergeList = None

    if IS_FIRST_RUN:
        make_lists_if_not_exist(DIRECTORY)
        currentEmergeList = parse_application_list(IS_TEST_ENV)
    else:
        #See if TODO file is remaining
        make_lists_if_not_exist(DIRECTORY)

        #Read in apps from todo
        with open(DIRECTORY + LIST_TODO_FILENAME, "+rt") as todoFile:
            currentEmergeList = todoFile.readlines() 

    successList = []
    failureList = []
    try: 
        if IS_TEST_ENV:
            #Loop through each package
            for i in range(len(currentEmergeList)):
                print("Emerging package #{0} of {1}: {2}".format(i+1, len(currentEmergeList), currentEmergeList[i]))
                time.sleep(1)
        else:
            successFile = open(DIRECTORY + LIST_SUCCESS_FILENAME, "+at")
            failFile = open(DIRECTORY + LIST_FAILED_FILENAME, "+at")
            
            for i in range(len(currentEmergeList)):
                CURR_EMERGE_REBUILD_COMMAND = EMERGE_REBUILD_COMMAND + currentEmergeList[i]
                appEmergeResult = subprocess.run(CURR_EMERGE_REBUILD_COMMAND.split(), capture_output=True, text=True, shell=False)

                if appEmergeResult.returncode == 0:
                    print("Successfully emerged app #{0}/{1}: {2}".format(i+1, len(currentEmergeList), currentEmergeList[i]))
                    print(currentEmergeList[i], file=successFile)
                    successList.append(currentEmergeList[i])
                else:
                    print("Failed to emerge app #{0}/{1}: {2}".format(i+1, len(currentEmergeList), currentEmergeList[i]))
                    print(currentEmergeList[i], file=failFile)
                    failureList.append(currentEmergeList[i])
                    create_failure_dir(DIRECTORY, currentEmergeList[i], appEmergeResult)

            successFile.close()
            failFile.close()             
            
    except KeyboardInterrupt:
        print("\nCtrl+C detected! Performing cleanup...")

        #Remove Successful emerges from todo
        for success in successList:
            currentEmergeList.remove(success)

        #Remove Successfull emerges from todo
        for failure in failureList:
            currentEmergeList.remove(failure)

        #Write to todo File
        with open(DIRECTORY + LIST_TODO_FILENAME, "+wt") as todoFile:
            for app in currentEmergeList:
                print(app, file=todoFile)
        print("Exiting program.")

    #appListResult = subprocess.run(EMERGE_REBUILD_COMMAND.split(), capture_output=True, text=True)
