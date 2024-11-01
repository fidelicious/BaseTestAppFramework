"""
-------------------------------------------------------------------------------
                                Fidelicious
File:       ui_framework.py
Purpose:    Framework file for streamlining GUI creation

Creator:    Fidel Quezada Guzman
Cr. Date:   10/30/2024
-------------------------------------------------------------------------------
"""
import tkinter as tk
from tkinter import ttk
from tkinter import *
import ttkbootstrap as tb
from tkinter.scrolledtext import ScrolledText
from collections import deque
import threading
import time
from autotest_framework import AutoTestFramework, Printing
from constants import GuiElements, TestCases, Flags, InstrumentInfo
from test_suites.connect import Connect, FwVersions


class UiFramework:
    def __init__(self, root):
        try:
            self.stop_event = threading.Event()                         # Init stop event for threading
            self.gui = GuiElements                                      # Init Constants Class
            self.tests = TestCases
            self.flags = Flags
            self.inst_info = InstrumentInfo
            self.frame = AutoTestFramework(self.stop_event)             # Init Test Framework
            self.printing = Printing(self.stop_event)
            self.connect_ts = Connect(self.stop_event)                  # Init Test Suites
            self.get_fw = FwVersions(self.stop_event)
        except Exception as e:
            print(f"UiFramework Initialization error: {e}")
            raise                                               # Raise exception to signal initialization failure
        self.root = root
        self.frames = {}                                                        # Init GUI Element variables
        self.main_nav_btn = None
        self.basic_nav_btn = None
        self.scripted_nav_btn = None
        self.user_label = None
        self.checkbox_label = None
        self.user = None
        self.connect_btn = None
        self.get_versions_btn = None
        self.ip_table = None
        self.fw_ver_table = None
        self.select_all_btn = None
        self.select_all_cmd = False
        self.test_vars = None
        self.selected_tests = deque()                                           # Run selected tests in Left Pop order
        self.debug_btn = None
        self.jira_btn = None
        self.debug_var = tk.BooleanVar(value=self.flags.DEBUG_MODE)
        self.jira_var = tk.BooleanVar(value=self.flags.JIRA_POSTING)
        self.status_text = None
        self.run_btn = None
        self.running = False

    """
    -------------------------------------------------------------------------------
    GUI Elements
    -------------------------------------------------------------------------------
    """

    def create_frame(self, parent=None, fill=None, side=None, padx=0, pady=0):
        """Default Frame creation with a specified parent"""
        if parent is None:
            parent = self.root                                      # Default to root if no parent is provided

        frame = tb.Frame(parent)                                    # Attach frame to the specified parent
        frame.pack(fill=fill, side=side, padx=padx, pady=pady)
        return frame

    def app_window(self, title, icon, window_size):                     # Application Window Setup
        self.root.title(title)              # Window Title
        self.root.iconbitmap(icon)          # Icon Image
        self.root.geometry(window_size)     # Default Size

    @staticmethod
    def create_button(frame=None, text=None, cmd=None, padx=0, pady=0, side=None):
        """Normal Button creation w/ Text & 1 command"""
        button = tb.Button(
            frame,
            text=text,
            command=cmd
        )
        button.pack(side=side, padx=padx, pady=pady)
        return button

    @staticmethod
    def create_button2(frame=None, text=None, cmd1=None, cmd2=None, padx=0, pady=0, side=None):
        """Special Button creation w/ Text & 2 commands"""

        button = tb.Button(
            frame,
            text=text,
            command=lambda: (cmd1(), cmd2())                    # Run cmd1 and cmd2 sequentially
        )
        button.pack(side=side, padx=padx, pady=pady)
        return button

    @staticmethod
    def create_checkbutton(frame=None, text=None, variable=None, cmd=None):
        """Normal CheckButton creation"""
        checkbutton = tb.Checkbutton(
            frame,
            text=text,
            variable=variable,
            onvalue=1,
            offvalue=0,
            command=cmd
        )
        checkbutton.pack(side=tk.TOP, anchor=tk.W, pady=5)
        return checkbutton

    @staticmethod
    def create_label(frame=None, text=None, font="Helvetica", size=12, side=None, padx=0, pady=0):
        """Normal Text Label creation"""
        label = tb.Label(
            frame,
            text=text,
            font=(font, size))
        label.pack(side=side, padx=padx, pady=pady)

    @staticmethod
    def create_fw_table(frame, fw_versions):                            # FW Versions Table
        # Create a treeview widget
        table = ttk.Treeview(frame, columns=('Main', 'Camera', 'LED', 'PowerMonitor'), show='headings', height=1)

        # Define column headers
        table.heading('Main', text='Main')
        table.heading('Camera', text='Camera')
        table.heading('LED', text='LED')
        table.heading('PowerMonitor', text='PowerMonitor')

        # Adjust column width and set center alignment
        table.column('Main', width=90, anchor=tk.CENTER)
        table.column('Camera', width=90, anchor=tk.CENTER)
        table.column('LED', width=90, anchor=tk.CENTER)
        table.column('PowerMonitor', width=90, anchor=tk.CENTER)

        # Insert data (First row: variable names, Second row: variable values)
        table.insert('', 'end',
                     values=(fw_versions.main, fw_versions.camera, fw_versions.led, fw_versions.powermonitor))

        # Add table to the window
        table.pack(pady=0)
        return table

    @staticmethod
    def create_ip_table(frame, ip):                                     # IP Address Table
        # Create a treeview widget
        table = ttk.Treeview(frame, columns='IP', show='headings', height=1)

        # Define column headers
        table.heading('IP', text='IP')

        # Adjust column width and set center alignment
        table.column('IP', width=80, anchor=tk.CENTER)

        # Insert data (First row: variable names, Second row: variable values)
        table.insert('', 'end', values=ip.ip)

        # Add table to the window
        table.pack(pady=5)
        return table

    @staticmethod
    def create_user_entry(frame=None, side=None):                                 # User Entry Slot
        entry = tb.Entry(frame)
        entry.pack(side=side)
        return entry

    @staticmethod
    def create_scroll_txt_wid(frame=None, height=8, expand=True):                   # Scrolled Text Widget
        text_widget = ScrolledText(frame, height=height, wrap=tb.WORD)
        text_widget.pack(fill=tb.BOTH, expand=expand)
        return text_widget

    """
    -------------------------------------------------------------------------------
    GUI Functionality/Commands
    -------------------------------------------------------------------------------
    """
    def update_fw_table(self):                                              # Update table w/ new firmware versions
        self.fw_ver_table.item(self.fw_ver_table.get_children()[0],
                               values=(self.inst_info.main, self.inst_info.camera,
                                       self.inst_info.led, self.inst_info.powermonitor))
        self.update_status_text(f"Instrument Firmware Versions:"
                                f"\n - Main: {self.inst_info.main}"
                                f"\n - Camera: {self.inst_info.camera}"
                                f"\n - LED: {self.inst_info.led}"
                                f"\n - PowerMonitor: {self.inst_info.powermonitor}")

    def update_ip_table(self):                                              # Update table w/ IP Address
        self.ip_table.item(self.ip_table.get_children()[0], values=self.inst_info.ip)
        self.update_status_text(f"Instrument IP Address: {self.inst_info.ip}")

    def toggle_test_selection(self):                                        # Select All Label & Functionality Toggle
        if self.select_all_cmd:
            # Deselect all
            for var, _, _ in self.test_vars:
                var.set(0)
            self.select_all_btn.config(text="Select All")
        else:
            # Select all
            for var, _, _ in self.test_vars:
                var.set(1)
            self.select_all_btn.config(text="Deselect All")
        self.select_all_cmd = not self.select_all_cmd

    def create_test_var(self, test_case):
        """Creates a test variable tuple for a given test case Enum member if the first value is an integer."""
        if isinstance(test_case.value[0], float) and not test_case.value[0].is_integer():
            return None                                 # Exclude cases where the first value is a non-integer float

        test_name = test_case.name                                  # Get the name of the Enum member
        test_display_name = test_case.value[1]                      # Access the display name from the Enum
        run_func = getattr(self, f"{test_name}_ts").run
        return IntVar(), f"{test_case.value[0]} : {test_display_name}", run_func

    def toggle_debug_mode(self):                                            # Update DEBUG_MODE w/ checkbox state
        self.flags.DEBUG_MODE = self.debug_var.get()

    def toggle_jira_posting(self):                                          # Update JIRA_POSTING w/ checkbox state
        self.flags.JIRA_POSTING = self.jira_var.get()

    def update_status_text(self, message):                                  # Updates Status Messages in GUI
        self.status_text.insert(tb.END, message + "\n")
        self.status_text.see(tb.END)

    def run_btn_label_update(self, button):                                 # Update Start/Stop Run Button Label
        button.config(text="Stop" if self.running else "Run")

    def run_tests(self):                                                    # Run Selected Tests
        try:
            while self.selected_tests and not self.stop_event.is_set():  # Confirm threading stop_event isn't set
                test_func = self.selected_tests.popleft()                # Execute selected test starting Left
                self.update_status_text(f"Running Test Suite: {test_func.__self__.__class__.__name__}")
                result = test_func()
                if not result:
                    self.update_status_text("\tTest Run Failed!")
                    break
                else:
                    self.update_status_text("\tTest Run Successfully!")
                time.sleep(1)                                            # stop_event checked every 1s
        except Exception as e:
            self.update_status_text(f"Error running tests: {e}")
        finally:
            self.running = False                                        # Reset running flag
            self.run_btn_label_update(self.run_btn)                     # Update run_button
            self.printing.tests_exec_print(1)                           # Print completion of Auto-Test
            self.update_status_text("\nAll Test Suites Completed.")
            results = str(self.printing.print_results())                # Print out results (Terminal & Status Box)
            self.update_status_text(f"{results}")

    def run_button_cmd(self):                                               # Run Button Click Handling
        if self.running:                                # Clicked when test running
            self.stop_event.set()                       # Signal threading stop event
            self.running = False                        # Reset running flag
            self.run_btn_label_update(self.run_btn)     # Update run_button
        else:
            for var, _, test_func in self.test_vars:                # Add selected test to the Right of deque
                if var.get() == 1:
                    self.selected_tests.append(test_func)
            if self.selected_tests:                                 # Run all Selected Tests
                self.stop_event.clear()                             # Clear threading stop event
                self.running = True                                 # Set running flag
                self.run_btn_label_update(self.run_btn)             # Update run_button
                self.printing.tests_exec_print(0)                   # Print Start of Auto-Test
                thread = threading.Thread(target=self.run_tests)    # Run tests selected in separate thread
                thread.start()
            else:
                self.update_status_text("No Tests selected to run")

    def run(self):                                                          # Start Tkinter main loop
        self.root.mainloop()
