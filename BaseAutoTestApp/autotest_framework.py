"""
-------------------------------------------------------------------------------
                                Fidelicious
File:       autotest_framework.py
Purpose:    Framework file for streamlining Test Suite creation

Creator:    Fidel Quezada Guzman
Cr. Date:   10/30/2014
-------------------------------------------------------------------------------
"""
import glob
import json
import shutil
import time
import os
import logging
import re
from datetime import datetime
import send2trash
from constants import Flags, Paths, FwConstants, TestCases, ResultCounters, InstrumentInfo


class AutoTestFramework:
    def __init__(self, stop_event):                                 # Initiate when Class is created
        try:
            self.stop_event = stop_event                            # Localized param stop event for threading
            self.flags = Flags
            self.paths = Paths
            self.const = FwConstants
            self.tests = TestCases
            self.results = ResultCounters
            self.inst_info = InstrumentInfo
        except Exception as e:
            print(f"Initialization error: {e}")
            raise  # Re-raise the exception to signal initialization failure


class TestSuiteInit(AutoTestFramework):
    """
    Initial Class used to create Test Suites that use Qt
    Class in Charge of:
        - Creating Connection to Instrument
        - Outputting initial Printout of Test Suite running
        - Timestamp
    """
    def __init__(self, stop_event, test_number, test_name):             # Initiate when Class is created
        super().__init__(stop_event)
        self.printing = Printing                                        # Class Instances
        self.logging = Logging(self.stop_event)
        self.test_number = test_number                                  # Local Variables
        self.test_name = test_name

    def find_instrument(self):                                          # Find Instrument before running test
        self.instrument_control.search_instrument()

    def test_suite_print(self, test_number, test_name):                 # Print Test Suite Running
        self.printing.test_suite_print(test_number, test_name)

    def time_stamp(self, test_name):                                    # Log Timestamp
        self.logging.get_unix_time(test_name)

    def run(self):                                                      # Execute test operations
        try:
            self.find_instrument()
            self.test_suite_print(self.test_number, self.test_name)
            self.time_stamp(self.test_name)
        except Exception as e:
            print(f"An error occurred during TestSuiteInit run function: {e}")
            return False


class TestSuiteDependencies(AutoTestFramework):
    """
    Dependencies Class used to make sure the Test Suites has all that it needs before running
    Class in Charge of:
        - Copying files that are the test execution depends on to execute as designed
    """
    def __init__(self, stop_event, source, destination):                # Initiate when Class is created
        super().__init__(stop_event)
        self.file_manip = FileManipulation(self.stop_event)             # Class Instances
        self.source = source                                            # Local Variable
        self.destination = destination

    def copy_file(self, source, destination):
        self.file_manip.file_copy_win(source, destination)

    def run(self):                                                      # Execute test operations
        try:
            self.copy_file(self.source, self.destination)
        except Exception as e:
            print(f"An error occurred during TestSuiteDependencies run function: {e}")
            return False


class TestSuiteCaptureLoopDependencies(AutoTestFramework):
    """
    Capture Loop Test Dependencies Class used to make sure the Capture Loop Test Suite run specific steps in order
    to execute as designed
        - Create capture_loop dir if not present within Root Dir of program
        - Remove Images in Save Directory (above) (before and after execution of test)
    """
    def __init__(self, stop_event):                # Initiate when Class is created
        super().__init__(stop_event)
        self.file_manip = FileManipulation(self.stop_event)             # Class Instances

    def create_capture_loop(self):                              # Create Dependency dir if not present within Root Dir
        self.file_manip.dir_check_create(str(self.paths.CAPTURE_LOOP.value))

    def remove_images_saved(self):                              # Remove Images in Save Directory in case
        self.file_manip.delete_dir_content(str(self.paths.CAPTURE_LOOP.value))


class TestSuiteQtDependencies(AutoTestFramework):
    """
    Dependency Class used to Generate the objects Qt execution needs to run
    Class in Charge of:
        - Get the build version that will be running
        - Generate the version dependant test case(s) (ran by TestSuiteQtExecution)
        - Get test cases that will be run
    """
    def __init__(self, stop_event, template_name, tc_name):
        super().__init__(stop_event)
        self.builds = Builds(self.stop_event)                                       # Class Instances
        self.test_gen = TestGeneration(self.stop_event)
        self.template_name = template_name                                          # Local Variable
        self.tc_name = tc_name

    def report_build_version(self):                                             # Returns Build Version Info String
        ver_string = self.builds.get_win_build_ver()
        return str(ver_string)

    def generate_test_case(self):                                           # Generate version dependent test case(s)
        ver_string = self.report_build_version()
        self.test_gen.generate_test_file(self.template_name, self.tc_name, ver_string)

    def get_test_case(self):
        ver_string = self.report_build_version()
        test_case = f"{self.tc_name}{ver_string}"
        return str(test_case)


class TestSuiteQtExecution(AutoTestFramework):
    """
    Execution Class used to Generate & Run the Qt test automatically
    Class in Charge of:
        - Run Qt TestAp Headless mode
        - Get & Log the Pass/Fails
        - Update Jira/Xray Execution Posting
        - Return Execution results to user
        - Run any Post-test dependencies for instrument
    """
    def __init__(self, stop_event, template_name, tc_name, jira_name, jira_num, seconds, results_prefix):
        super().__init__(stop_event)
        self.template_name = template_name                                          # Local Variable
        self.tc_name = tc_name
        self.jira_name = jira_name
        self.jira_num = jira_num
        self.seconds = seconds
        self.results_prefix = results_prefix
        self.test_gen = TestGeneration(self.stop_event)                         # Class Instances
        self.logging = Logging(self.stop_event)
        self.post_run = TestSuitePostRun(self.stop_event)
        self.qt_dep = TestSuiteQtDependencies(self.stop_event, self.template_name, self.tc_name)

    def run_qt_headless(self):                                              # Run QtTest App on PC in headless mode
        test_case = self.qt_dep.get_test_case()
        self.test_gen.run_qt_test_suite(test_case)
        time.sleep(5)

    def update_results(self):                                                               # Get Pass/Fail Count & Log
        test_case = self.qt_dep.get_test_case()
        pass_counter = getattr(self.results, f"{self.results_prefix}_pass")                 # Dynamically get counters
        fail_counter = getattr(self.results, f"{self.results_prefix}_fail")

        pass_counter, fail_counter, test_log = self.logging.get_test_result(test_case)      # Update values (locally)

        setattr(self.results, f"{self.results_prefix}_pass", pass_counter)                 # Update counters dynamically
        setattr(self.results, f"{self.results_prefix}_fail", fail_counter)

        return test_log

    def update_xray(self):                                                  # Update Xray/Jira Test Case
        test_log = self.update_results()
        if self.flags.JIRA_POSTING:
            self.logging.report_to_jira(test_log, self.jira_name, self.jira_num)

    def get_exec_results(self):                                             # Return Perfect or Failed Execution
        if self.results.basic_fail > 0:
            print(f"{self.jira_name} Failed!")
            time.sleep(5)
            return False
        else:
            self.post_run.delay(self.seconds)
            self.post_run.run_testapp_on_instrument(self.seconds)
            return True                                                                             # Successful Test

    def run(self):                                                          # Execute test operations
        try:
            self.qt_dep.generate_test_case()
            self.run_qt_headless()
            self.update_xray()
            self.get_exec_results()
        except Exception as e:
            print(f"An error occurred during TestSuiteQtExecution run function: {e}")
            return False


class TestSuiteFwUpdateExecution(AutoTestFramework):
    """
    FW Update Execution Class used to Generate & Run the FW update test automatically
    Class in Charge of:
        - Get Last Windows Build Zip & Version
        - Generate FW Update test file
        - Execution of FW update
    """
    def __init__(self, stop_event, template_name, tc_name, jira_name, jira_num, seconds, results_prefix):
        super().__init__(stop_event)
        self.template_name = template_name                                          # Local Variable
        self.tc_name = tc_name
        self.jira_name = jira_name
        self.jira_num = jira_num
        self.seconds = seconds
        self.results_prefix = results_prefix
        self.builds = Builds(self.stop_event)                                       # Class Instances
        self.test_gen = TestGeneration(self.stop_event)
        self.test_exec = TestSuiteQtExecution(self.stop_event, self.template_name, self.tc_name,
                                              self.jira_name, self.jira_num, self.seconds, self.results_prefix)

    def get_last_windows_build_zip_name(self):                                  # Get last Windows Build zip file name
        zip_file = self.builds.get_last_downloaded_zip_name(self.paths.WINDOWS_GROUP.value)
        return str(zip_file)

    def get_windows_build_version(self):                                        # Find Windows Build version
        zip_file = self.get_last_windows_build_zip_name()
        ver_string = self.builds.find_version(zip_file, self.const.WIN_VER_INDEX)
        if self.flags.DEBUG_MODE:
            print("Windows version_string: " + ver_string)
        return str(ver_string)

    def generate_fw_update_test_case(self):             # Generate FW Update Exclusive version dependent test case(s)
        ver_string = self.get_windows_build_version()
        self.test_gen.generate_fw_update_test_file(self.template_name, self.tc_name, ver_string)

    def run(self):                                                          # Execute test operations
        try:
            self.generate_fw_update_test_case()
            self.test_exec.run_qt_headless()
            self.test_exec.update_xray()
            self.test_exec.get_exec_results()
        except Exception as e:
            print(f"An error occurred during TestSuiteFwUpdateDependencies run function: {e}")
            return False


class TestSuitePostRun(AutoTestFramework):
    """
    Post Run Class used to run dependencies for instrument needed after specific runs
    Class in Charge of:
        - Adding extra Delays
        - Running TestApp on Instrument (requires BOOT_TIME_DELAY delay right after)
    """
    @staticmethod
    def delay(seconds):
        time.sleep(seconds)

    def run_testapp_on_instrument(self, run):                               # Run TestApp on Instrument
        if run:
            self.instrument_control.run_testapp_on_instrument()
            time.sleep(self.const.BOOT_TIME_DELAY)


class TestSuiteMiscellaneous(AutoTestFramework):
    """
    Class used to run miscellaneous commands/executions needed in between other standard steps (Init, QtExection, etc)
    """
    def __init__(self, stop_event, template_name, tc_name):                                     # Initiate when Class is created
        super().__init__(stop_event)
        self.template_name = template_name                                          # Local Variable
        self.tc_name = tc_name
        self.file_manip = FileManipulation(self.stop_event)             # Class Instances
        self.logging = Logging(self.stop_event)
        self.qt_dep = TestSuiteQtDependencies(self.stop_event, self.template_name, self.tc_name)

    def switch_to_testapp(self):                        # Confirm Instrument can switch Default Application to TestApp
        if not self.instrument_control.switch_default_application_to_test_app():
            print("Cannot switch application to testapp start up ...")
            return -98

    def dependency_dirs(self):                          # Checks/Creates dependency dirs for Auto-Test
        try:
            for path in [self.paths.AUTOTEST.value, self.paths.DEPLOY.value,
                         self.paths.CONFIG.value, self.paths.AT_DOWNLOADS.value]:
                self.file_manip.dir_check_create(path)
        except Exception as e:
            print(f"An error occurred during dependency_dirs method: {e}")
            return False

    def get_instrument_ip(self):                        # Gets Instrument IP & sets it to GUI variable
        self.instrument_control.search_instrument()
        self.inst_info.ip = str(self.instrument_control.read_server_ip_address())

    def get_fw_versions(self):                          # Gets Instrument FW vers & sets to GUI variables
        test_case = self.qt_dep.get_test_case()
        self.logging.get_fw_versions(test_case)


class TestGeneration(AutoTestFramework):
    @staticmethod
    def invalid_bin_name(name_list):
        if len(name_list) != 1:
            print("get_fw_bin_name: ERROR - Number of fw bin file is not 1!")
            print(name_list)
            return True

    @staticmethod
    def deploy_build_type(fw_name_token_list):
        """
        Bin formats for: Deploy
        """
        fw_name_version_string = fw_name_token_list[3] + '_' + \
                                 fw_name_token_list[4] + '_' + \
                                 fw_name_token_list[5] + '_' + \
                                 fw_name_token_list[6]
        return fw_name_version_string

    @staticmethod
    def normal_fw_build_type(fw_name_token_list):
        """
        Bin formats for: Main, LED, PM bins = 1
        """
        fw_name_version_string = (
                fw_name_token_list[3] + '_' +
                fw_name_token_list[4] + '_' +
                fw_name_token_list[5] + '_' +
                fw_name_token_list[6] + '_' +
                fw_name_token_list[7]
        )
        return fw_name_version_string

    @staticmethod
    def cam_fw_build_type(fw_name_token_list):
        """
        Bin formats for: Camera bin = 2
        """
        fw_name_version_string = (
                fw_name_token_list[4] + '_' +
                fw_name_token_list[5] + '_' +
                fw_name_token_list[6] + '_' +
                fw_name_token_list[7] + '_' +
                fw_name_token_list[8]
        )
        return fw_name_version_string

    @staticmethod
    def get_major_minor_build_number(debug, version_string):
        """ Returns Major, Minor & Build numbers of a build given version string """
        if debug:
            print("get_major_minor_build_number: version string = " + version_string)
        number_list = version_string.split('.')
        return number_list[0], number_list[1], number_list[2]

    def get_fw_bin_name(self, fw_string, build_type, bin_format):
        """
        Gets the FW binary file name strings via inputting full FW binary file name
        :param fw_string: FW Binary name string
        :param build_type: CI or Deploy build
        :param bin_format: Main, LED, PM bins = 1. Camera bin = 2. FPGA bin = 3
        :return: Firmware Name Version String
        """
        fw_bin_names_list = glob.glob(f"{self.paths.DEPLOY.value}/{fw_string}")
        if self.invalid_bin_name(fw_bin_names_list):
            return 0
        fw_name_strings_list = fw_bin_names_list[0].split('.')
        fw_name_token_list = fw_name_strings_list[0].split('_')

        if build_type == "Deploy":                                          # Deploy
            fw_name_version_string = self.deploy_build_type(fw_name_token_list)

        else:                                                               # CI
            match bin_format:
                case 1:
                    fw_name_version_string = self.normal_fw_build_type(fw_name_token_list)
                case 2:
                    fw_name_version_string = self.cam_fw_build_type(fw_name_token_list)
                case 3:
                    if (fw_name_token_list[1] == 'CameraBoard' and fw_name_token_list[2] == 'FPGA' and
                            fw_name_token_list[3] == '100T'):
                        fw_name_version_string = fw_name_token_list[4]
                        for token in fw_name_token_list[5:]:
                            fw_name_version_string += '_' + token
                case _:
                    fw_name_version_string = None  # Handle unexpected bin_format values
        return fw_name_version_string

    def generate_test_file(self, template_prefix, test_name_prefix, version_string):
        """
        Generate auto-test\deploy\config\<test>_<version>.tst from 1template\config\<file>.tst
        :param template_prefix: test case template prefix to grab
        :param test_name_prefix: test case prefix to be generated
        :param version_string: version grabbed from FW version being used
        """
        # Print Current Working Dir if Debug Mode ON
        if self.flags.DEBUG_MODE:
            print("CWD: " + os.getcwd())

        # Generate 1template\config\<file>.tst var
        file_template = f"{self.paths.TEMPLATE_CONFIG.value}/{template_prefix}{self.const.TEST_FILE_TYPE}"

        # Generate auto-test\deploy\config\<test>_<version>.tst var
        version_fw_file = f"{test_name_prefix}{version_string}"
        tst_version_fw_file = version_fw_file + self.const.TEST_FILE_TYPE
        auto_test_file = f"{self.paths.CONFIG.value}/{tst_version_fw_file}"

        # Generate var to open 1template\config\<file>.tst in read mode, then read it
        infile = open(file_template, "r")
        content_template = infile.read()

        # Replace all occurrences of template_prefix with version_fw_file
        content_template = content_template.replace(template_prefix, version_fw_file)

        # Create auto-test\deploy\config\<test>_<version>.tst via opening in Read/Write mode
        outfile = open(auto_test_file, "w+")
        outfile.write(content_template)

        # Close up .tst files
        infile.close()
        outfile.close()

        # Print to user
        print("Generated test case from template")

    def generate_fw_update_test_file(self, template_prefix, test_name_prefix, version_string):
        """
        generate_test_file Modified for usage on the Firmware Update test
        :param template_prefix: test case template prefix to grab
        :param test_name_prefix: test case prefix to be generated
        :param version_string: version grabbed from FW version being used
        :return:
        """
        # Begin workflow identical to generate_test_file
        if self.flags.DEBUG_MODE:
            print("CWD: " + os.getcwd())

        # Generate 1template\config\<file>.tst var
        file_template = f"{self.paths.TEMPLATE_CONFIG.value}/{template_prefix}{self.const.TEST_FILE_TYPE}"

        # Generate auto-test\deploy\config\<test>_<version>.tst var
        version_fw_file = f"{test_name_prefix}{version_string}"
        tst_version_fw_file = version_fw_file + self.const.TEST_FILE_TYPE
        auto_test_file = f"{self.paths.CONFIG.value}/{tst_version_fw_file}"

        # Generate var to open 1template\config\<file>.tst in read mode, then read it
        infile = open(file_template, "r")
        content_template = infile.read()

        # Replace all occurrences of template_prefix with version_fw_file
        content_template = content_template.replace(template_prefix, version_fw_file)

        # Diverge onto FW Update Specific: Set Major, Minor and Build number variables & assign to ver var
        major_no, minor_no, build_no = self.get_major_minor_build_number(self.flags.DEBUG_MODE, version_string)
        ver = f"{major_no}_{minor_no}_{build_no}"

        # Get all FW binary file name strings
        main_fw_suffix = self.get_fw_bin_name(self.const.MAIN + '_' + ver + "_*.bin", self.const.FW_VER, 1)
        led_fw_suffix = self.get_fw_bin_name(self.const.LED + '_' + ver + "_*.bin", self.const.FW_VER, 1)
        cam_fw_suffix = self.get_fw_bin_name(self.const.CAMERA + '_' + ver + "_*.bin", self.const.FW_VER, 2)
        fpga_fw_suffix = self.get_fw_bin_name(self.const.CAM_FPGA + "_*.bin", self.const.FW_VER, 3)
        pm_fw_suffix = self.get_fw_bin_name(self.const.PM + '_' + ver + "_*.bin", self.const.FW_VER, 1)
        if main_fw_suffix == 0 or led_fw_suffix == 0 or cam_fw_suffix == 0 or fpga_fw_suffix == 0 or pm_fw_suffix == 0:
            infile.close()
            print("Cannot get the fw binary file name string")
            exit(-7)

        # Finalize all Firmware Binary names
        main_fw_bin_name = self.const.MAIN + '_' + main_fw_suffix + self.const.FW_FILE_TYPE
        led_fw_bin_name = self.const.LED + '_' + led_fw_suffix + self.const.FW_FILE_TYPE
        camera_fw_bin_name = self.const.CAMERA + '_' + cam_fw_suffix + self.const.FW_FILE_TYPE
        fpga_bin_name = self.const.CAM_FPGA + '_' + fpga_fw_suffix + self.const.FW_FILE_TYPE
        pm_fw_bin_name = self.const.PM + '_' + pm_fw_suffix + self.const.FW_FILE_TYPE

        # Replace Firmware Binary names on template
        content_template = content_template.replace(self.const.MAIN + FwConstants.FW_FILE_TYPE, main_fw_bin_name)
        content_template = content_template.replace(self.const.LED + FwConstants.FW_FILE_TYPE, led_fw_bin_name)
        content_template = content_template.replace(self.const.CAMERA + FwConstants.FW_FILE_TYPE, camera_fw_bin_name)
        content_template = content_template.replace( self.const.CAM_FPGA + FwConstants.FW_FILE_TYPE, fpga_bin_name)
        content_template = content_template.replace( self.const.PM + FwConstants.FW_FILE_TYPE, pm_fw_bin_name)

        # Finalize w/ continuing generate_test_file workflow
        # Create auto-test\deploy\config\<test>_<version>.tst via opening in Read/Write mode
        outfile = open(auto_test_file, "w+")
        outfile.write(content_template)

        # Close up .tst files
        infile.close()
        outfile.close()

    def run_qt_test_suite(self, test_case_name):
        """
        Returns build version that test will run
        :param test_case_name: String with full Test Case name (found in TestCases const) & version
        """
        # Change to Deploy dir
        push_dir = os.getcwd()
        os.chdir(str(self.paths.DEPLOY.value))
        if self.flags.DEBUG_MODE:
            print("chdir to: " + os.getcwd())
            print("QtTestAppWin64 name: " + str(self.paths.QT_EXE.value))

        # Create QT TestApp run command & Log
        qt_cmd = '.\\' + str(self.paths.QT_EXE.value)
        qt_cmd = qt_cmd + " -t " + test_case_name + " --headless"
        print("qt_cmd: " + qt_cmd)
        logging.info('qt_cmd: starting ' + qt_cmd)

        # Run QT TestApp Headless & Report out
        exit_code = os.system(qt_cmd)
        if exit_code == 0:
            print(f"{test_case_name} Test Case Run Completed.")
            logging.info('qt_cmd: Run Completed')
            cmd_result = True
        else:
            print(f"{test_case_name} Run Failed with exit code: {exit_code}")
            logging.info(f"qt_cmd: Run Failed with exit code: {exit_code}")
            cmd_result = False

        # Get back to Base dir
        os.chdir(push_dir)
        if self.flags.DEBUG_MODE:
            print("chdir to: " + os.getcwd())

        return cmd_result


class FileManipulation(AutoTestFramework):
    def dir_check_create(self, directory):
        """
        Check if directory exists from where this function runs. Else it will create it
        :param directory: Directory name to check/create

        Example:
            dir = r"C:\path\to\your\directory"
            dir_check_create(dir)
        """
        dir_path = os.path.normpath(directory)                  # Normalize path for compatibility across diff OS's
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            if self.flags.DEBUG_MODE:
                print(f"Directory '{dir_path}' created.")
        else:
            if self.flags.DEBUG_MODE:
                print(f"Directory '{dir_path}' already exists.")

    @staticmethod
    def file_copy_win(src_path, dest_dir):
        """
        Copy file from source path to the destination directory.

        :param src_path: Path of the source file
        :param dest_dir: Path of the destination directory

        Example: file_copy_win(r'C:\path\to\source\file_*.txt', r'C:\path\to\destination\directory')
        """
        try:
            files_to_copy = glob.glob(src_path)                             # Expand the wildcard
            if not files_to_copy:
                print(f"No files found matching {src_path}")
                return

            for file in files_to_copy:                                      # Copy files
                shutil.copy(file, dest_dir)
                print(f"File copied from {file} to {dest_dir}")

        except FileNotFoundError as e:
            print(f"Error: {e}")
        except PermissionError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    @staticmethod
    def delete_dir_content(path_file):
        """
        Delete all the files inside the given path
        :param path_file: Directory with contents we want to delete
        """
        try:
            for filename in os.listdir(path_file):                  # Iterate over all files in the directory
                file_path = os.path.join(path_file, filename)

                if os.path.isfile(file_path):                       # Check if the path is a file, then delete
                    os.remove(file_path)
            print("All files deleted successfully.\n")
        except Exception as e:
            print(f"An error occurred: {e}")

    @staticmethod
    def delete_dir(dir_name):
        """
        Delete the inputted Directory
        :param dir_name: Dir to delete
        """
        group_dir = dir_name[1:]
        if os.path.exists(group_dir):
            try:
                send2trash.send2trash(group_dir)
            except Exception as e:
                print(f"send2trash failed to remove directory: {group_dir} due to {e}")


class Builds(AutoTestFramework):
    def __init__(self, stop_event):
        super().__init__(stop_event)
        self.file_manip = FileManipulation(self.stop_event)     # Instance

    @staticmethod
    def get_last_downloaded_build_name(group_name, downloads_path):
        """
        Returns last_<Build>_downloaded.txt name within downloads_path dir
        :param group_name: Group string within constants.py,  Ex: WINDOWS_GROUP = r"/Windows/CI"
        :param downloads_path: location of file in question, default: auto-test-downloads dir
        """
        group_prefix = group_name.replace('/', '_')
        build_name_saved_file = downloads_path + "/last" + group_prefix + "_downloaded.txt"
        print("file containing the name of build downloaded: " + build_name_saved_file)

        return build_name_saved_file

    @staticmethod
    def get_file_name_from_path_name(path_file_name):
        """ Returns the file name, given the Name of build. used for is_downloaded func."""
        name_list = path_file_name.split('/')
        return name_list[2]

    @staticmethod
    def compare_build_name(build_1, build_2, build_format):
        """
        Compare Build numbers & returns a value depending on comparison
        :param build_1: Newly downloaded zip
        :param build_2: Current_latest_zip
        :param build_format: ARM/Win/FPGA_BUILD_FORMAT from constants
        :return: 1 if build number is equal or greater than the one saved in last download file
        """
        # Inputted builds are blank
        if build_2 == "":  # No Current_latest_zip
            return 1
        if build_1 == "":  # No Newly downloaded zip
            return -1

        # ARM64 or Windows Format
        if build_format == 1:
            minor_number_1 = int(build_1.split('.')[1])
            build_number_1 = int(build_1.split('.')[2])

            minor_number_2 = int(build_2.split('.')[1])
            build_number_2 = int(build_2.split('.')[2])

        # FPGA Format
        elif build_format == 2:
            minor_number_1 = int(build_1.split('_')[5])
            build_number_1 = int(build_1.split('_')[6])

            minor_number_2 = int(build_2.split('_')[5])
            build_number_2 = int(build_2.split('_')[6])

        if minor_number_1 > minor_number_2:  # Newly downloaded zip is newer
            return 1

        if (minor_number_1 == minor_number_2) and (build_number_1 > build_number_2):  # Same Build
            return 1

        if (minor_number_1 == minor_number_2) and (build_number_1 == build_number_2):  # Current_latest_zip is newer
            return 0
        else:
            return -1

    def find_version(self, zip_file, index):
        """ Find Version # given Zip file & index """
        version_info_list = zip_file.split('_')
        if self.flags.DEBUG_MODE:
            print("version string: ", version_info_list[index])
        return version_info_list[index]

    def get_last_downloaded_zip_name(self, group_name):
        """
        Returns name of zip file needed within last_<Build>_downloaded.txt
        :param group_name: Group string within constants.py,  Ex: WINDOWS_GROUP = r"/Windows/CI"
        """
        downloaded_file = self.get_last_downloaded_build_name(group_name, self.paths.AT_DOWNLOADS.value)
        try:
            file = open(downloaded_file, "r")
            zip_file_name = file.read()
        except Exception as e:
            print(f"get_last_downloaded_zip_name error: {e}, zip_file_name blank")
            file = open(downloaded_file, "w")
            zip_file_name = ""

        file.close()
        return zip_file_name

    def get_latest_build(self, debug, group_name, nexus_fwapi_ci_page, build_format):
        """
        Pulls latest ARM64, Windows or FPGA CI Build
        :param debug: Debug Flag
        :param group_name: ARM64/Windows/FPGA_GROUP from constants
        :param nexus_fwapi_ci_page: NEXUS_ARM64/Win/FPGA_CI from constants
        :param build_format: ARM/Win/FPGA_BUILD_FORMAT from constants
        :return: Pass/Fail
        """
        # initialize the latest_build_number
        latest_build_zip_name = ""

        # Obtain CI build list:
        # curl_cmd = f"curl -X GET {self.paths.NEXUS_REPO.value}{group_name} -o {nexus_fwapi_ci_page}"
        curl_prefix = 'curl -X GET "http://10.240.20.40/service/rest/v1/search?repository=ChemiDocGo-FW&group='
        curl_cmd = curl_prefix + group_name + '"'
        curl_cmd = curl_cmd + " -o " + nexus_fwapi_ci_page

        # Run curl_cmd to get .json file
        if debug:
            print("curl_cmd: " + curl_cmd)
        try:
            os.system(curl_cmd)
        except Exception as e:
            print(f"An error occurred running curl_cmd: {e}")
            exit(-15)

        # Read in the ARM64/Win/FPGA_html.json file & store list in variable
        f = open(nexus_fwapi_ci_page)
        build_image_list = json.load(f)
        f.close()

        # Update latest_build_zip_name w/ the latest build version
        latest_build_zip_name = self.update_latest(latest_build_zip_name, build_image_list, build_format)

        # Confirm we checked the last page
        contTokenString = build_image_list['continuationToken']
        while contTokenString != None:
            curl_cmd_cont = curl_prefix + group_name + '&continuationToken=' + contTokenString + '"'
            curl_cmd_cont = curl_cmd_cont + " -o " + nexus_fwapi_ci_page
            if debug:
                print("curl_cmd_cont: " + curl_cmd_cont)
            os.system(curl_cmd_cont)

            f = open(nexus_fwapi_ci_page)
            build_image_list = json.load(f)
            contTokenString = build_image_list['continuationToken']
            f.close()

            # Update latest_build_zip_name w/ the latest build version
            latest_build_zip_name = self.update_latest(latest_build_zip_name, build_image_list, build_format)
        if debug:
            print("last page downloaded")
            print(f"Latest C/I zip built: {latest_build_zip_name}")

        # Confirm name of the last build file is newer than the one previously downloaded
        latest_build_zip_path = group_name[1:] + '/' + latest_build_zip_name            # Construct path name
        if self.is_downloaded(group_name, latest_build_zip_path):
            print(latest_build_zip_path + " has been downloaded already.")
            return False
        if debug:
            print(f"URL of latest zip file: {latest_build_zip_name}")

        # Create group path under AT_DOWNLOADS dir
        self.file_manip.dir_check_create(str(self.paths.AT_DOWNLOADS.value + group_name))

        # Download new build zip file
        curl_cmd2 = ("curl -X GET " + "http://10.240.20.40/repository/ChemiDocGo-FW" + group_name + "/" +
                     latest_build_zip_name + " -o " + self.paths.AT_DOWNLOADS.value + '/' + latest_build_zip_path)
        if debug:
            print("curl_cmd2 = " + curl_cmd2)
        os.system(curl_cmd2)
        logging.info("Downloaded new zip file from Nexus: " + latest_build_zip_path)

        # Create group path under auto-test directory
        FileManipulation.delete_dir(str(self.paths.AUTOTEST.value + group_name))
        self.file_manip.dir_check_create(str(self.paths.AUTOTEST.value + group_name))

        # Copy the zip file just downloaded from downloads to auto_test directory
        self.file_manip.file_copy_win(f"{self.paths.AT_DOWNLOADS.value}/{latest_build_zip_path}",
                                      f"{self.paths.AUTOTEST.value}/{latest_build_zip_path}")

        # Update the last download file record with the downloaded file
        self.set_last_downloaded_build_name(group_name, latest_build_zip_path)

        if debug:
            print("End of get_latest_build")
        return True

    def generate_deploy_build(self, build, path):
        """
        Generates new (ARM64/Windows) Build when running Deploy version
        :param build: ARM64 or Windows specific build name
        :param path: Arm64 or Windows group dir (from constants.py)
        :return Pass/Fail
        """
        try:
            # Wipe old Deploy (ARM64/Windows) build from auto-test-downloads Dir
            build_path = path + "/" + build
            cur_dir = os.getcwd()
            os.chdir(str(self.paths.AUTOTEST.value))
            FileManipulation.delete_dir(path)
            self.file_manip.dir_check_create(path)
            os.chdir(cur_dir)

            # Copy build Zip file from resources to auto-test Dir
            self.file_manip.file_copy_win(f"resources/{build}", f"{self.paths.AUTOTEST.value}/{build_path}")

            # Update auto-test-downloads\last_X_CI_downloaded.txt
            self.set_last_downloaded_build_name(path, build_path)
        except Exception as e:
            print(f"generate_deploy_build error: {e}")
            return False
        return True

    def deploy_windows_qt_build(self, debug):
        push_dir = os.getcwd()
        os.chdir(self.paths.AUTOTEST.value)
        if debug:
            print("chdir to: " + os.getcwd())

        # Convert group_name to Windows format
        windows_group_name = self.paths.WINDOWS_GROUP.value.replace("/", "\\")
        source_path = os.getcwd() + windows_group_name
        target_path = 'deploy'

        # clean up firmware binary files in the target path: CameraBoard_FX3, LedBoard, MainBoard, and PMBoard binary files
        if debug:
            print("clean up firmware binary files: CameraBoard_FX3, LedBoard, MainBoard, and PMBoard binary files")
        clean_up_cmd = "del /q " + target_path + "\\CDGo_CameraBoard_FX3_*.bin"
        os.system(clean_up_cmd)
        clean_up_cmd = "del /s /q " + target_path + "\\CDGo_LedBoard_*.bin"
        os.system(clean_up_cmd)
        clean_up_cmd = "del /s /q " + target_path + "\\CDGo_MainBoard_*.bin"
        os.system(clean_up_cmd)
        clean_up_cmd = "del /s /q " + target_path + "\\CDGo_PMBoard_*.bin"
        os.system(clean_up_cmd)

        if debug:
            print("source_path: ", source_path)
            print("target_path: ", target_path)

        deep_copy_cmd = f'xcopy "{source_path}" "{target_path}" /s /e /k /h /y'
        deep_copy_status = os.system(deep_copy_cmd)
        if deep_copy_status != 0:
            print("deploy_windows_qt_build: xcopy failed: status code = " + str(deep_copy_status))
            exit(-40)
        else:
            print("Deployed Windows Qt Build to deploy directory")

        os.chdir(push_dir)
        if debug:
            print("chdir to: " + os.getcwd())

    def get_build_version(self, group_path, ver_index):
        """
        Returns build version that test will run
        """
        # Get last Windows Build zip file name
        zip_file = self.get_last_downloaded_zip_name(group_path)

        # Find Version info of Windows Build
        version_string = self.find_version(zip_file, ver_index)

        return version_string

    def get_win_build_ver(self):
        """
        Returns Windows build version that test will run
        """
        # Get last Windows Build zip file name
        zip_file = self.get_last_downloaded_zip_name(self.paths.WINDOWS_GROUP.value)

        # Find Version info of Windows Build
        version_string = self.find_version(zip_file, self.const.WIN_VER_INDEX)

        return version_string

    def unzip_build(self, zip_file_path):
        """
        Unzips file name within last_<Build>_downloaded.txt, given the Windows/Arm64/FPGA path
        :param zip_file_path:
        :return:
        """
        # Get zip file name needed within last_<Build>_downloaded.txt
        zip_file_name = self.get_last_downloaded_zip_name(zip_file_path)
        print("Zip file name: " + zip_file_name)

        # Go to zip file location dir (auto-test/X)
        cur_dir = os.getcwd()
        group_auto_test_dir = self.paths.AUTOTEST.value + zip_file_path
        os.chdir(group_auto_test_dir)

        # Unzip & remove original zip file
        if os.path.exists(zip_file_name):
            shutil.unpack_archive(zip_file_name)
            os.remove(zip_file_name)

        # Go back to Dir where we started & return zip file name
        os.chdir(cur_dir)
        return zip_file_name

    def update_latest(self, latest_build_zip, build_image_list, build_format):
        """
        Returns currently latest zip file name after comparing
        :param latest_build_zip: Current latest build zip before comparing
        :param build_image_list: List created from ARM64/Win/FPGA_html.json file
        :param build_format: ARM/Win/FPGA_BUILD_FORMAT from constants
        :return: 1 if build number is equal or greater than the one saved in last download file
        """
        # Initialize latest zip to be returned & items elements in List inputted
        current_latest_zip = latest_build_zip
        items = build_image_list['items']
        items_length = len(items)

        # Handle last page with null list in items exceptional case
        if items_length == 0:
            return current_latest_zip

        # Iterate items: find name, extension, & zip name
        for item in items:
            item_name = item['name']
            item_extension = item_name.split('.')[-1]
            item_zip_name = item_name.split('/')[-1]
            if item_extension != "zip":  # skip if not a zip file
                continue
            # Compare builds
            if self.compare_build_name(item_zip_name, current_latest_zip, build_format) > 0:
                current_latest_zip = item_zip_name  # found later build zip than current one

        return current_latest_zip

    def is_downloaded(self, group_name, build_name):
        """
        Returns if name of the last build file is newer than the one previously downloaded or not
        :param group_name: ARM64/Windows/FPGA_GROUP from constants
        :param build_name: Name of build to confirm whether the build has been downloaded
        :return: True if downloaded already or False if it has not been downloaded yet
        """

        ci_build_name_saved = self.get_last_downloaded_build_name(group_name, self.paths.AT_DOWNLOADS.value)
        if not os.path.exists(ci_build_name_saved):
            print(ci_build_name_saved + " does not exists")
            return False

        current_build_name = self.get_file_name_from_path_name(build_name)
        print("Current build name on Nexus Server: " + current_build_name)

        savefile = open(ci_build_name_saved, "r")
        previous_build_name = savefile.read()
        print("Previous downloaded build name: " + previous_build_name)
        savefile.close()

        if previous_build_name == current_build_name:
            print(current_build_name + " was downloaded previously!")
            return True
        print(current_build_name + " has NOT been downloaded")
        return False

    def set_last_downloaded_build_name(self, group_name, build_name):
        """ Updates last_X_CI_downloaded.txt file """
        # Store last_X_CI_downloaded.txt name in var
        saved_file_name = self.get_last_downloaded_build_name(group_name, str(self.paths.AT_DOWNLOADS.value))

        # Update file
        saved_file = open(saved_file_name, "w")
        saved_file.write(self.get_file_name_from_path_name(build_name))
        saved_file.close()


class Logging(AutoTestFramework):
    def log_init(self):
        """ Initialize Logging under auto-test\deploy\log """
        print("\nauto_test_main: initializing logging")
        history_log_file = f"{os.getcwd()}/{self.paths.AUTOTEST.value}/{self.paths.AT_LOG_FILE.value}"
        logging.basicConfig(filename=history_log_file, format='%(asctime)s %(message)s', level=logging.INFO)

    def get_fw_versions(self, test_case_name):
        """
        Returns the Firmware versions from the get_firmware_versions test case
        :param test_case_name: String with full Test Case name (found in TestCases const) & version
        """
        # Get latest test case Log
        test_log_file_list = str(self.paths.AT_LOG.value) + '/' + test_case_name + "*.log"
        latest_log_file = ""
        for file in glob.glob(test_log_file_list):
            if file > latest_log_file:
                latest_log_file = file

        # Open Log in Read Mode
        try:
            file = open(latest_log_file, "r")
        except Exception as e:
            print(f"get_test_result: Error reading log file: {e}")

        # Parse the JSON file
        test_result_json = json.load(file)

        # Check if the 'tests' key exists and access it safely
        if 'tests' in test_result_json:
            tests = test_result_json['tests']

            # Iterate through the tests and process them
            for test in tests:
                cmd_str = test.get('cmdStr', '')                                        # Access the 'cmdStr' safely
                log_str = test.get('logStr', '')                                        # Access 'logStr' safely

                # Extract the versions based on cmdStr for each firmware type
                if cmd_str == "version(firmware,main,)":
                    self.extract_version(log_str, 'main')

                elif cmd_str == "version(firmware,camera,)":
                    self.extract_version(log_str, 'camera')

                elif cmd_str == "version(firmware,led,)":
                    self.extract_version(log_str, 'led')

                elif cmd_str == "version(firmware,powermonitor,)":
                    self.extract_version(log_str, 'powermonitor')
        else:
            print("'tests' key not found in the JSON structure.")

        # Close file & Report out
        file.close()

        return self.inst_info.main, self.inst_info.camera, self.inst_info.led, self.inst_info.powermonitor

    def extract_version(self, log_str, fw_type):
        """
        Helper function to extract firmware version and assign it to the respective attribute.
        :param log_str: Log string containing firmware version information
        :param fw_type: Type of firmware (main, camera, led, powermonitor)
        """
        version_match = re.search(r"firmwareVersion = ([\d.]+)", log_str)
        if version_match:
            version = version_match.group(1)
            if fw_type == 'main':
                self.inst_info.main = version
            elif fw_type == 'camera':
                self.inst_info.camera = version
            elif fw_type == 'led':
                self.inst_info.led = version
            elif fw_type == 'powermonitor':
                self.inst_info.powermonitor = version
        else:
            print(f"No {fw_type} firmware version found in the logStr.")

    def get_unix_time(self, test_suite):
        """
        Print out Unix Time
        :param test_suite: Test being run for printing
        """
        start_time_float = time.time()
        start_time = int(start_time_float)
        dt_object = datetime.fromtimestamp(start_time)
        start_time_formatted = dt_object.strftime("%B %d, %Y - %H:%M:%S")
        if self.flags.DEBUG_MODE:
            print(f"FW API {test_suite} test start time: {start_time_formatted}")


class Printing(AutoTestFramework):
    @staticmethod
    def tests_exec_print(start_end):
        """
        Printout for Start/End of Test Execution
        :param start_end: Pass in if test is starting or ending to know what to print out
        """
        print("\n")
        print("=" * 25)
        if start_end == 0:
            print(" CDG Auto-Test Starting ")
        else:
            print(" CDG Auto-Test Completed ")
        print("=" * 25)

    @staticmethod
    def test_suite_print(test_num, test_case):
        """ Printout every time a new Test Case Begins """
        print(f"\n{test_num} - {test_case} Test Starting")

    def print_results(self):
        """ Printout ResultCounters at the end of Test Execution """
        results = []                                                                # List to collect each result string

        for test_case in self.tests:
            test_name = test_case.value[1]                                          # Get from TestCases
            pass_count = getattr(self.results, f"{test_case.name.lower()}_pass")    # Match pass/fail
            fail_count = getattr(self.results, f"{test_case.name.lower()}_fail")

            # Print only if the test ran
            if pass_count != 0 or fail_count != 0:
                result = f"{test_name}\t\t\t\t -  Pass: {pass_count}\t\t -  Fail: {fail_count}"
                results.append(result)                                              # Add each result to the list

        return "\n".join(results)                                                   # Return as single string w/ newline
