"""
-------------------------------------------------------------------------------
                                Fidelicious
File:       ui.py
Purpose:    Create & Config the main GUI window & elements

Creator:    Fidel Quezada Guzman
Cr. Date:   10/30/2024
-------------------------------------------------------------------------------
"""
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ui_framework import UiFramework


class AutoTestApp(UiFramework):
    def __init__(self):                                                                 # Init when Class is created
        self.root = tb.Window(themename="darkly")                                       # Create Main Window w/ theme
        super().__init__(self.root)
        try:
            self.setup_ui()                                                             # Setup UI
            self.app_window(self.gui.APP_TITLE, self.gui.APP_ICON, self.gui.APP_SIZE)   # Setup Window
            self.frames[self.gui.MAIN] = self.create_main_page()                        # Init pages
            self.frames[self.gui.BASIC] = self.create_basic_tests_page()
            self.frames[self.gui.SCRIPTED] = self.create_scripted_tests_page()
            self.show_frame(self.gui.MAIN)                                              # First Frame to open
        except Exception as e:
            print(f"AutoTestApp Initialization error: {e}")
            raise                                                                       # Signal init failure

    def setup_ui(self):
        """ Main UI Setup function - Elements configured here will be in all Pages """

        """
        -------------------------------------------------------------------------------
        Page Navigation - Buttons used for switching between pages
        -------------------------------------------------------------------------------
        """
        navigation_frame = self.create_frame(parent=self.root, pady=5)                              # Frame

        self.main_nav_btn = self.create_button(frame=navigation_frame, text=self.gui.MAIN_MSG,      # Navigation Buttons
                                               cmd=lambda: self.show_frame(self.gui.MAIN), side="left", padx=5)
        self.basic_nav_btn = self.create_button(frame=navigation_frame, text=self.gui.BASIC_MSG,
                                                cmd=lambda: self.show_frame(self.gui.BASIC), side="left", padx=5)
        self.scripted_nav_btn = self.create_button(frame=navigation_frame, text=self.gui.SCRIPTED_MSG,
                                                   cmd=lambda: self.show_frame(self.gui.SCRIPTED), side="left", padx=5)

        """
        -------------------------------------------------------------------------------
        Status Messages - Kept at bottom of GUI
        -------------------------------------------------------------------------------
        """
        status_frame = self.create_frame(fill=tb.BOTH, side="bottom", padx=20, pady=10)         # Frame
        self.status_text = self.create_scroll_txt_wid(frame=status_frame)                       # Scrolled Text Widget

    def show_frame(self, frame_name):
        """ Show a specific frame and hide others """
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[frame_name].pack(fill="both", expand=True)

    def create_main_page(self):
        """ Main GUI, shows by default when App opens """
        frame = self.create_frame()                                                             # Frame
        main_label = self.create_label(frame=frame, text=self.gui.APP_TITLE,                    # Main Label
                                       size=self.gui.L_FONT_SIZE, pady=10)
        return frame

    def create_basic_tests_page(self):
        frame = self.create_frame()                                                             # Frame
        main_label = self.create_label(frame=frame, text=self.gui.BASIC_MSG,                    # Main Label
                                       size=self.gui.L_FONT_SIZE, pady=10)
        """
        -------------------------------------------------------------------------------
        Instrument Info (Quick Connect & Firmware Version Get)
        -------------------------------------------------------------------------------
        """
        info_btn_frame = self.create_frame(parent=frame)  # Frame
        self.connect_btn = self.create_button2(frame=info_btn_frame, text=self.gui.CONN_MSG,            # Connect Button
                                               cmd1=self.connect_ts.connect, cmd2=self.update_ip_table, side=LEFT)
        self.get_versions_btn = self.create_button2(frame=info_btn_frame, text=self.gui.FW_MSG,         # Get FW Button
                                                    cmd1=self.get_fw.get_fw_versions, cmd2=self.update_fw_table)
        info_frame = self.create_frame(parent=frame, fill=None, pady=0)  # Frame
        self.ip_table = self.create_ip_table(info_frame, self.inst_info)                                # IP Table
        self.fw_ver_table = self.create_fw_table(info_frame, self.inst_info)                            # FW Ver Table

        return frame

    def create_scripted_tests_page(self):
        frame = self.create_frame()                                                             # Frame
        main_label = self.create_label(frame=frame, text=self.gui.SCRIPTED_MSG,                 # Main Label
                                       size=self.gui.L_FONT_SIZE, pady=10)
        """
        -------------------------------------------------------------------------------
        User Entry
        -------------------------------------------------------------------------------
        """
        user_frame = self.create_frame(parent=frame, padx=10)  # Frame
        self.user_label = self.create_label(frame=user_frame, text=self.gui.USER_MSG,                   # Label
                                            size=self.gui.M_FONT_SIZE, side=LEFT)
        self.user = self.create_user_entry(frame=user_frame, side=LEFT)  # User Entry

        """
        -------------------------------------------------------------------------------
        Tests Selection
        -------------------------------------------------------------------------------
        """
        sel_all_frame = self.create_frame(parent=frame)                                                 # Frame
        self.checkbox_label = self.create_label(frame=sel_all_frame, text=self.gui.SELECT_MSG,          # Label
                                                size=self.gui.L_FONT_SIZE, pady=10)
        self.select_all_btn = self.create_button(frame=sel_all_frame, text=self.gui.SELECT_ALL_MSG,     # Button
                                                 cmd=self.toggle_test_selection)

        ts_frame = self.create_frame(parent=frame,fill=X, padx=20)                                      # Frame

        # Create the list of test variables using the Enum members, excluding any None entries
        self.test_vars = [tv for tc in self.tests if (tv := self.create_test_var(tc)) is not None]

        for var, text, _ in self.test_vars:                             # Test Selection using test_vars Tuples list
            self.create_checkbutton(frame=ts_frame, text=text, variable=var)

        """
        -------------------------------------------------------------------------------
        Feature On/Off CheckButtons (Debug, Jira Posting
        -------------------------------------------------------------------------------
        """
        self.checkbox_label = self.create_label(frame=frame, text=self.gui.FEAT_MSG,                    # Label
                                                size=self.gui.L_FONT_SIZE)
        feat_frame = self.create_frame(parent=frame)                                                    # Frame
        self.debug_btn = self.create_checkbutton(frame=feat_frame, text=self.gui.DEBUG_MSG,             # CheckButton
                                                 variable=self.debug_var, cmd=self.toggle_debug_mode)
        self.jira_btn = self.create_checkbutton(frame=feat_frame, text=self.gui.JIRA_MSG,               # CheckButton
                                                variable=self.jira_var, cmd=self.toggle_jira_posting)

        """
        -------------------------------------------------------------------------------
        Start/Stop Auto-Test Run Button
        -------------------------------------------------------------------------------
        """
        self.run_btn = self.create_button(frame=feat_frame, text=self.gui.RUN_MSG,                      # Button
                                          cmd=self.run_button_cmd, padx=10)

        return frame
