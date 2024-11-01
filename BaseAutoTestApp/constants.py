"""
-------------------------------------------------------------------------------
                                Fidelicious
File:       constants.py
Purpose:    Store global constants used throughout the application

Creator:   Fidel Quezada Guzman
Cr. Date:   10/30/2024
-------------------------------------------------------------------------------
"""
from enum import Enum


class GuiElements:                              # GUI Elements Constants
    APP_TITLE = "AutoTest App"
    APP_ICON = "Images/jojo.ico"
    APP_SIZE = "600x500"                      # Width x Height
    MAIN = "main_page"
    BASIC = "basic_tests_page"
    SCRIPTED = "scripted_tests_page"
    MAIN_MSG = "Main Page"
    BASIC_MSG = "Basic Tests"
    SCRIPTED_MSG = "Scripted Tests"
    USER_MSG = "User: "
    CONN_MSG = "Get Device IP Address"
    FW_MSG = "Get Firmware Versions"
    SELECT_MSG = "Select tests to run"
    SELECT_ALL_MSG = "Select All"
    FEAT_MSG = "Feature Enable/Disable"
    DEBUG_MSG = "Debug Mode"
    JIRA_MSG = "JIRA Posting"
    RUN_MSG = "Run"
    DEFAULT_FONT = "Helvetica"
    XL_FONT_SIZE = 24
    L_FONT_SIZE = 16
    M_FONT_SIZE = 12


# Paths of files & directories of interest
class Paths(Enum):
    AUTOTEST = r"auto-test"
    DEPLOY = r"auto-test\deploy"
    CONFIG = r"auto-test\deploy\config"                                 # Qt TestApp pulls .tst files from here
    AT_LOG = r"auto-test\deploy\log"
    AT_ARM64 = r"auto-test\ARM64\CI"
    AT_WIN = r"auto-test\Windows\CI"
    AT_DOWNLOADS = r"auto-test-downloads"
    TEST_SUITES = r"test_suites"
    TEMPLATE_CONFIG = r"1template/config"
    ARM64_GROUP = "/ARM64/CI"                                           # Builds dir (within auto-test-downloads)
    WINDOWS_GROUP = "/Windows/CI"
    FPGA_GROUP = "/FPGA/CI"
    QT_EXE = "FwTestApp.exe"


# Feature Enable/Disable Flags
class Flags:
    DEBUG_MODE = False              # Help with printout on specific code modules
    DEPLOY_CI = False               # Download Deploy (True) or CI (False) Builds
    JIRA_POSTING = False            # Enable functionality to post test results onto Jira Execution
    JIRA_CLOUD = True               # Enable Jira Cloud functionality


# Miscellaneous Constants
class FwConstants:
    FW_FILE_TYPE = ".bin"                       # Firmware filetype
    TEST_FILE_TYPE = ".tst"                     # QT Test Script filetype
    MAIN = "Instr_MainBoard_FW"                  # Firmware Prefixes
    FW_VER = "CI"
    BOOT_TIME_DELAY = 60                        # CDG estimate boot time
    ARM_VER_INDEX = 7                           # Version Indexing
    WIN_VER_INDEX = 3
    FPGA_VER_INDEXING1 = 4
    FPGA_VER_INDEXING2 = 5
    FPGA_VER_INDEXING3 = 6
    ARM_BUILD_FORMAT = 1
    WIN_BUILD_FORMAT = 1
    FPGA_BUILD_FORMAT = 2


# Firmware Versions
class InstrumentInfo:
    main = 0
    camera = 0
    led = 0
    powermonitor = 0
    ip = 0


# Pass/Fail Test Execution Counters
class ResultCounters:
    connect_pass = 0
    connect_fail = 0


# Test Cases using Tuples to store values
class TestCases(Enum):
    """
    * Any [0] values that are non-integers will be excluded
    * any fields left blank, are non-applicable
    TestCase = (Number,
                Name,
                QtTemplatePrefix,
                QtExecutionPrefix,
                JiraTestCaseNum,
                JiraExecutionSummary,
                Delay(if 0: will not run TestApp on Instrument),
                ResultsName)
    """
    connect = (1,
              "Connect",                                                             # Non-Qt Test
              "",
              "",
              "",
              "",
              0,
              "")
