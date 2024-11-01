"""
-------------------------------------------------------------------------------
                                Fidelicious
File:       basic.py
Purpose:    Test suite for conducting basic tests on device such as connection

Creator:    Fidel Quezada Guzman
Cr. Date:   10/30/2024
-------------------------------------------------------------------------------
"""

from autotest_framework import AutoTestFramework


class Connect(AutoTestFramework):
    def __init__(self, stop_event):             # Initiate when Class is created
        super().__init__(stop_event)

    @staticmethod
    def connect():
        try:
            pass
            return True
        except Exception as e:
            print(f"An error occurred during connect function: {e}")
            return False

    def run(self):
        self.connect()


class FwVersions(AutoTestFramework):
    def __init__(self, stop_event):  # Initiate when Class is created
        super().__init__(stop_event)

    @staticmethod
    def get_fw_versions():
        try:
            pass
            return True
        except Exception as e:
            print(f"An error occurred during get_fw_versions function: {e}")
            return False

    def run(self):
        self.get_fw_versions()
