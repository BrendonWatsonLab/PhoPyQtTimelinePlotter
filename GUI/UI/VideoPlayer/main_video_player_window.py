#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import traceback

import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, \
    QMessageBox, QDataWidgetMapper
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import QDir, QTimer, Qt, QModelIndex, QSortFilterProxyModel

from lib import vlc
from app.model import TimestampModel, ToggleButtonModel, TimestampDelta

"""
The software displays/plays a video file with variable speed and navigation settings.
The software runs a timer.
"""
class MainVideoPlayerWindow(QMainWindow):
    """
    The main window class
    """
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = uic.loadUi("GUI/UI/VideoPlayer/main_video_player_window.ui")

        self.timestamp_filename = None
        self.video_filename = None
        self.media_start_time = None
        self.media_end_time = None
        self.restart_needed = False
        self.timer_period = 100
        self.is_full_screen = False
        self.media_started_playing = False
        self.media_is_playing = False
        self.original_geometry = None


        self.timestamp_model = TimestampModel(None, self)
        self.proxy_model = QSortFilterProxyModel(self)
        self.ui.list_timestamp.setModel(self.timestamp_model)
        self.ui.list_timestamp.doubleClicked.connect(
            lambda event: self.ui.list_timestamp.indexAt(event.pos()).isValid()
            and self.run()
        )

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.timeout.connect(self.timer_handler)
        self.timer.start(self.timer_period)

        self.vlc_instance = vlc.Instance()
        self.media_player = self.vlc_instance.media_player_new()
        # if sys.platform == "darwin":  # for MacOS
        #     self.ui.frame_video = QMacCocoaViewContainer(0)

        self.ui.frame_video.doubleClicked.connect(self.toggle_full_screen)
        self.ui.frame_video.wheel.connect(self.wheel_handler)
        self.ui.frame_video.keyPressed.connect(self.key_handler)

        # Set up Labels:
        # self.ui.lblVideoName.

        # self.displayed_video_title = bind("self.ui.lblVideoName", "text", str)
        self.ui.lblVideoName.setText(self.video_filename)
        self.ui.lblVideoSubtitle.setText("")
        self.ui.dateTimeEdit.setHidden(True)
        self.ui.lblCurrentFrame.setText("")
        self.ui.spinBoxCurrentFrame.setEnabled(False)
        self.ui.spinBoxCurrentFrame.setValue(1)
        self.ui.spinBoxCurrentFrame.valueChanged.connect(self.handle_frame_value_changed)
        self.ui.lblTotalFrames.setText("")

        self.ui.lblCurrentTime.setText("")
        self.ui.lblTotalDuration.setText("")

        self.ui.lblFileFPS.setText("")

        self.ui.spinBoxFrameJumpMultiplier.value = 1

        # Set up buttons
        self.ui.button_run.clicked.connect(self.run)
        self.ui.button_timestamp_browse.clicked.connect(
            self.browse_timestamp_handler
        )
        self.ui.button_timestamp_create.clicked.connect(
            self.create_timestamp_file_handler
        )
        self.ui.button_video_browse.clicked.connect(
            self.browse_video_handler
        )


        # Set up directional buttons
        self.ui.btnSkipLeft.clicked.connect(self.skip_left_handler)
        self.ui.btnSkipRight.clicked.connect(self.skip_right_handler)
        self.ui.btnLeft.clicked.connect(self.step_left_handler)
        self.ui.btnRight.clicked.connect(self.step_right_handler)

        self.play_pause_model = ToggleButtonModel(None, self)
        self.play_pause_model.setStateMap(
            {
                True: {
                    "text": "",
                    "icon": qta.icon("fa.play", scale_factor=0.7)
                },
                False: {
                    "text": "",
                    "icon": qta.icon("fa.pause", scale_factor=0.7)
                }
            }
        )
        self.ui.button_play_pause.setModel(self.play_pause_model)
        self.ui.button_play_pause.clicked.connect(self.play_pause)

        self.ui.button_full_screen.setIcon(
            qta.icon("ei.fullscreen", scale_factor=0.6)
        )
        self.ui.button_full_screen.setText("")
        self.ui.button_full_screen.clicked.connect(self.toggle_full_screen)

        # Playback Speed:
        self.ui.doubleSpinBoxPlaybackSpeed.value = 1.0
        self.ui.doubleSpinBoxPlaybackSpeed.valueChanged.connect(self.speed_changed_handler)

        self.ui.button_speed_up.clicked.connect(self.speed_up_handler)
        self.ui.button_speed_up.setIcon(
            qta.icon("fa.arrow-circle-o-up", scale_factor=0.8)
        )
        self.ui.button_speed_up.setText("")
        self.ui.button_slow_down.clicked.connect(self.slow_down_handler)
        self.ui.button_slow_down.setIcon(
            qta.icon("fa.arrow-circle-o-down", scale_factor=0.8)
        )
        self.ui.button_slow_down.setText("")

        self.ui.button_mark_start.setIcon(
            qta.icon("fa.quote-left", scale_factor=0.7)
        )
        self.ui.button_mark_start.setText("")
        self.ui.button_mark_end.setIcon(
            qta.icon("fa.quote-right", scale_factor=0.7)
        )
        self.ui.button_mark_end.setText("")
        self.ui.button_add_entry.clicked.connect(self.add_entry)
        self.ui.button_remove_entry.clicked.connect(self.remove_entry)

        self.ui.button_mark_start.clicked.connect(
            lambda: self.set_mark(start_time=int(
                self.media_player.get_position() *
                self.media_player.get_media().get_duration()))
        )
        self.ui.button_mark_end.clicked.connect(
            lambda: self.set_mark(end_time=int(
                self.media_player.get_position() *
                self.media_player.get_media().get_duration()))
        )

        self.ui.slider_progress.setTracking(False)
        self.ui.slider_progress.valueChanged.connect(self.set_media_position)

        # self.ui.slider_volume.valueChanged.connect(self.set_volume)
        self.ui.entry_description.setReadOnly(True)

        # Mapper between the table and the entry detail
        self.mapper = QDataWidgetMapper()
        self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
        self.ui.button_save.clicked.connect(self.mapper.submit)

        # Set up default volume
        # self.set_volume(self.ui.slider_volume.value())

        self.vlc_events = self.media_player.event_manager()
        self.vlc_events.event_attach(
            vlc.EventType.MediaPlayerTimeChanged, self.media_time_change_handler
        )

        # Let our application handle mouse and key input instead of VLC
        self.media_player.video_set_mouse_input(False)
        self.media_player.video_set_key_input(False)

        self.ui.show()

    # Timestamp entries:
    def add_entry(self):
        if not self.timestamp_filename:
            self._show_error("You haven't chosen a timestamp file yet")
        row_num = self.timestamp_model.rowCount()
        self.timestamp_model.insertRow(row_num)
        start_cell = self.timestamp_model.index(row_num, 0)
        end_cell = self.timestamp_model.index(row_num, 1)
        self.timestamp_model.setData(start_cell, TimestampDelta.from_string(""))
        self.timestamp_model.setData(end_cell, TimestampDelta.from_string(""))

    def remove_entry(self):
        if not self.timestamp_filename:
            self._show_error("You haven't chosen a timestamp file yet")
        selected = self.ui.list_timestamp.selectionModel().selectedIndexes()
        if len(selected) == 0:
            return
        self.proxy_model.removeRow(selected[0].row()) and self.mapper.submit()


    def set_media_position(self, position):
        percentage = position / 10000.0
        self.media_player.set_position(percentage)
        absolute_position = percentage * \
            self.media_player.get_media().get_duration()
        if absolute_position > self.media_end_time:
            self.media_end_time = -1

    def set_mark(self, start_time=None, end_time=None):
        if len(self.ui.list_timestamp.selectedIndexes()) == 0:
            blankRowIndex = self.timestamp_model.blankRowIndex()
            if not blankRowIndex.isValid():
                self.add_entry()
            else:
                index = self.proxy_model.mapFromSource(blankRowIndex)
                self.ui.list_timestamp.selectRow(index.row())
        selectedIndexes = self.ui.list_timestamp.selectedIndexes()
        if start_time:
            self.proxy_model.setData(selectedIndexes[0],
                                     TimestampDelta.string_from_int(
                                         start_time))
        if end_time:
            self.proxy_model.setData(selectedIndexes[1],
                                     TimestampDelta.string_from_int(
                                         end_time))

    def update_ui(self):
        self.ui.slider_progress.blockSignals(True)
        self.ui.slider_progress.setValue(
            self.media_player.get_position() * 10000
        )
        #print(self.media_player.get_position() * 10000)

        self.update_video_file_play_labels()

        # When the video finishes
        self.ui.slider_progress.blockSignals(False)
        if self.media_started_playing and \
           self.media_player.get_media().get_state() == vlc.State.Ended:
            self.play_pause_model.setState(True)
            # Apparently we need to reset the media, otherwise the player
            # won't play at all
            self.media_player.set_media(self.media_player.get_media())
            # self.set_volume(self.ui.slider_volume.value())
            self.media_is_playing = False
            self.media_started_playing = False
            self.run()

    # Event Handlers:
    def timer_handler(self):
        """
        This is a workaround, because for some reason we can't call set_time()
        inside the MediaPlayerTimeChanged handler (as the video just stops
        playing)
        """
        if self.restart_needed:
            self.media_player.set_time(self.media_start_time)
            self.restart_needed = False

    def key_handler(self, event):
        if event.key() == Qt.Key_Escape and self.is_full_screen:
            self.toggle_full_screen()
        if event.key() == Qt.Key_F:
            self.toggle_full_screen()
        if event.key() == Qt.Key_Space:
            self.play_pause()

    def wheel_handler(self, event):
        # self.modify_volume(1 if event.angleDelta().y() > 0 else -1)
        self.set_media_position(1 if event.angleDelta().y() > 0 else -1)

    def modify_volume(self, delta_percent):
        new_volume = self.media_player.audio_get_volume() + delta_percent
        if new_volume < 0:
            new_volume = 0
        elif new_volume > 40:
            new_volume = 40
        self.media_player.audio_set_volume(new_volume)
        # self.ui.slider_volume.setValue(self.media_player.audio_get_volume())

    def set_volume(self, new_volume):
        self.media_player.audio_set_volume(new_volume)

    def handle_frame_value_changed(self, newProposedFrame):
        # Tries to change the frame to the user provided one.
        ## TODO:
        print(newProposedFrame)

    # Playback Speed/Rate:
    def speed_changed_handler(self, val):
        print(val)
        self.media_player.set_rate(val)
        # self.media_player.set_rate(self.ui.doubleSpinBoxPlaybackSpeed.value())
        # TODO: Fix playback speed. Print current playback rate (to a label or something, so the user can see).

    def speed_up_handler(self):
        self.modify_rate(0.1)

    def slow_down_handler(self):
        self.modify_rate(-0.1)

    def modify_rate(self, delta_percent):
        new_rate = self.media_player.get_rate() + delta_percent
        if new_rate < 0.2 or new_rate > 2.0:
            return
        self.media_player.set_rate(new_rate)

    def media_time_change_handler(self, _):
        if self.media_end_time == -1:
            return
        if self.media_player.get_time() > self.media_end_time:
            self.restart_needed = True

    def update_slider_highlight(self):
        if self.ui.list_timestamp.selectionModel().hasSelection():
            selected_row = self.ui.list_timestamp.selectionModel(). \
                selectedRows()[0]
            self.media_start_time = self.ui.list_timestamp.model().data(
                selected_row.model().index(selected_row.row(), 0),
                Qt.UserRole
            )
            self.media_end_time = self.ui.list_timestamp.model().data(
                selected_row.model().index(selected_row.row(), 1),
                Qt.UserRole
            )
            duration = self.media_player.get_media().get_duration()
            self.media_end_time = self.media_end_time \
                if self.media_end_time != 0 else duration
            if self.media_start_time > self.media_end_time:
                raise ValueError("Start time cannot be later than end time")
            if self.media_start_time > duration:
                raise ValueError("Start time not within video duration")
            if self.media_end_time > duration:
                raise ValueError("End time not within video duration")
            slider_start_pos = (self.media_start_time / duration) * \
                               (self.ui.slider_progress.maximum() -
                                self.ui.slider_progress.minimum())
            slider_end_pos = (self.media_end_time / duration) * \
                             (self.ui.slider_progress.maximum() -
                              self.ui.slider_progress.minimum())
            self.ui.slider_progress.setHighlight(
                int(slider_start_pos), int(slider_end_pos)
            )

        else:
            self.media_start_time = 0
            self.media_end_time = -1


    def run(self):
        """
        Execute the loop
        """
        if self.timestamp_filename is None:
            self._show_error("No timestamp file chosen")
            return
        if self.video_filename is None:
            self._show_error("No video file chosen")
            return
        try:
            self.update_slider_highlight()
            self.media_player.play()
            self.media_player.set_time(self.media_start_time)
            self.media_started_playing = True
            self.media_is_playing = True
            self.play_pause_model.setState(False)
        except Exception as ex:
            self._show_error(str(ex))
            print(traceback.format_exc())

    def play_pause(self):
        """Toggle play/pause status
        """
        if not self.media_started_playing:
            self.run()
            return
        if self.media_is_playing:
            self.media_player.pause()
        else:
            self.media_player.play()
        self.media_is_playing = not self.media_is_playing
        self.play_pause_model.setState(not self.media_is_playing)

    # Info labels above the video that display the FPS/frame/time/etc info
    def update_video_file_play_labels(self):
        curr_total_fps = self.get_media_fps()
        curr_total_duration = self.media_player.get_length()
        totalNumFrames = self.get_media_total_num_frames()
        if totalNumFrames > 0:
            self.ui.lblTotalFrames.setText(str(totalNumFrames))
        else:
            self.ui.lblTotalFrames.setText("--")
        if curr_total_duration > 0:
            self.ui.lblTotalDuration.setText(str(curr_total_duration))  # Gets duration in [ms]
        else:
            self.ui.lblTotalDuration.setText("--")

        # Changing Values: Dynamically updated each time the playhead changes
        curr_percent_complete = self.media_player.get_position()  # Current percent complete between 0.0 and 1.0

        if curr_percent_complete >= 0:
            self.ui.lblPlaybackPercent.setText(str(curr_percent_complete))
        else:
            self.ui.lblPlaybackPercent.setText("--")

        curr_frame = int(round(curr_percent_complete * totalNumFrames))

        # Disable frame change on spinBox update to prevent infinite loop
        self.ui.spinBoxCurrentFrame.blockSignals(True)
        if curr_frame >= 0:
            self.ui.lblCurrentFrame.setText(str(curr_frame))
            #self.ui.spinBoxCurrentFrame.setValue(curr_frame)
            #self.ui.spinBoxCurrentFrame.setEnabled(True)
        else:
            self.ui.lblCurrentFrame.setText("--")
            #self.ui.spinBoxCurrentFrame.setEnabled(False)
            #self.ui.spinBoxCurrentFrame.setValue(1)

        # Re-enable signals from the frame spin box after update
        self.ui.spinBoxCurrentFrame.blockSignals(False)

        if self.media_player.get_time() >= 0:
            self.ui.lblCurrentTime.setText(str(self.media_player.get_time()) + "[ms]")  # Gets time in [ms]
        else:
            self.ui.lblCurrentTime.setText("-- [ms]")  # Gets time in [ms]

    # Called only when the video file changes:
    def update_video_file_labels_on_file_change(self):
        if self.video_filename is None:
            self.ui.lblVideoName.setText("")
        else:
            self.ui.lblVideoName.setText(self.video_filename)
            # Only updated when the video file is changed:
            curr_total_fps = self.get_media_fps()
            self.ui.lblFileFPS.setText(str(curr_total_fps))

            curr_total_duration = self.media_player.get_length()
            totalNumFrames = self.get_media_total_num_frames()
            if totalNumFrames > 0:
                self.ui.lblTotalFrames.setText(str(totalNumFrames))
                self.ui.spinBoxCurrentFrame.setMaximum(totalNumFrames)
                self.ui.spinBoxCurrentFrame.setEnabled(True)
            else:
                self.ui.lblTotalFrames.setText("--")
                self.ui.spinBoxCurrentFrame.setEnabled(False)
                self.ui.spinBoxCurrentFrame.setMaximum(1)

            if curr_total_duration > 0:
                self.ui.lblTotalDuration.setText(str(curr_total_duration)) # Gets duration in [ms]
            else:
                self.ui.lblTotalDuration.setText("--")

            self.update_video_file_play_labels()

    # Media Information:
    def get_frame_multipler(self):
        return self.ui.spinBoxFrameJumpMultiplier.value

    def get_media_fps(self):
        return (self.media_player.get_fps() or 30)

    def get_milliseconds_per_frame(self):
        """Milliseconds per frame"""
        return int(1000 // self.get_media_fps())

    def get_media_total_num_frames(self):
        return int(self.media_player.get_length() * self.get_media_fps())

    # Playback Navigation (Left/Right) Handlers:
    def step_left_handler(self):
        print('seek: left')
        self.seek_frames(-10 * self.get_frame_multipler())

    def skip_left_handler(self):
        print('skip: left')
        self.seek_frames(-1 * self.get_frame_multipler())

    def step_right_handler(self):
        print('seek: right')
        self.seek_frames(10 * self.get_frame_multipler())

    def skip_right_handler(self):
        print('skip: right')
        self.seek_frames(1 * self.get_frame_multipler())

    # Other:
    def seek_frames(self, relativeFrameOffset):
        """Jump a certain number of frames forward or back
        """
        if self.video_filename is None:
            self._show_error("No video file chosen")
            return
        # if self.media_end_time == -1:
        #     return

        curr_total_fps = self.get_media_fps()
        relativeSecondsOffset = relativeFrameOffset / curr_total_fps # Desired offset in seconds
        curr_total_duration = self.media_player.get_length()
        relative_percent_offset = relativeSecondsOffset / curr_total_duration # percent of the whole that we want to skip

        totalNumFrames = self.get_media_total_num_frames()

        try:
            didPauseMedia = False
            if self.media_is_playing:
                self.media_player.pause()
                didPauseMedia = True

            newPosition = self.media_player.get_position() + relative_percent_offset
            # newTime = int(self.media_player.get_time() + relativeFrameOffset)

            # self.update_slider_highlight()
            # self.media_player.set_time(newTime)
            self.media_player.set_position(newPosition)

            if (didPauseMedia):
                self.media_player.play()
            # else:
            #     # Otherwise, the media was already paused, we need to very quickly play the media to update the frame with the new time, and then immediately pause it again.
            #     self.media_player.play()
            #     self.media_player.pause()
            self.media_player.next_frame()

            print("Setting media playback time to ", newPosition)
        except Exception as ex:
            self._show_error(str(ex))
            print(traceback.format_exc())

    def toggle_full_screen(self):
        if self.is_full_screen:
            # TODO Artifacts still happen some time when exiting full screen
            # in X11
            self.ui.frame_media.showNormal()
            self.ui.frame_media.restoreGeometry(self.original_geometry)
            self.ui.frame_media.setParent(self.ui.widget_central)
            self.ui.layout_main.addWidget(self.ui.frame_media, 2, 3, 3, 1)
            # self.ui.frame_media.ensurePolished()
        else:
            self.ui.frame_media.setParent(None)
            self.ui.frame_media.setWindowFlags(Qt.FramelessWindowHint |
                                               Qt.CustomizeWindowHint)
            self.original_geometry = self.ui.frame_media.saveGeometry()
            desktop = QApplication.desktop()
            rect = desktop.screenGeometry(desktop.screenNumber(QCursor.pos()))
            self.ui.frame_media.setGeometry(rect)
            self.ui.frame_media.showFullScreen()
            self.ui.frame_media.show()
        self.ui.frame_video.setFocus()
        self.is_full_screen = not self.is_full_screen


    # File Loading:
    def browse_timestamp_handler(self):
        """
        Handler when the timestamp browser button is clicked
        """
        tmp_name, _ = QFileDialog.getOpenFileName(
            self, "Choose Timestamp file", None,
            "Timestamp File (*.tmsp);;All Files (*)"
        )
        if not tmp_name:
            return
        self.set_timestamp_filename(QDir.toNativeSeparators(tmp_name))

    def create_timestamp_file_handler(self):
        """
        Handler when the timestamp file create button is clicked
        """
        tmp_name, _ = QFileDialog.getSaveFileName(
            self, "Create New Timestamp file", None,
            "Timestamp File (*.tmsp);;All Files (*)"
        )
        if not tmp_name:
            return

        try:
            if (os.stat(QDir.toNativeSeparators(tmp_name)).st_size == 0):
                    # File is empty, create a non-empty one:
                    with open(QDir.toNativeSeparators(tmp_name), "w") as fh:
                        fh.write("[]")  # Write the minimal valid JSON string to the file to allow it to be used
            else:
                pass

            # with open(tmp_name, 'r') as fh:
            #     if fh.__sizeof__()>0:
            #         # File is not empty:
            #         pass
            #     else:
            #         # File is empty, create a non-empty one:
            #         fh.close()
            #         with open(tmp_name, "w") as fh:
            #             fh.write("[]")  # Write the minimal valid JSON string to the file to allow it to be used

        except WindowsError:
            with open(tmp_name, "w") as fh:
                fh.write("[]") # Write the minimal valid JSON string to the file to allow it to be used


        # Create new file:
        self.set_timestamp_filename(QDir.toNativeSeparators(tmp_name))

    def _sort_model(self):
        self.ui.list_timestamp.sortByColumn(0, Qt.AscendingOrder)

    def _select_blank_row(self, parent, start, end):
        self.ui.list_timestamp.selectRow(start)

    def set_timestamp_filename(self, filename):
        """
        Set the timestamp file name
        """
        if not os.path.isfile(filename):
            self._show_error("Cannot access timestamp file " + filename)
            return

        try:
            self.timestamp_model = TimestampModel(filename, self)
            self.timestamp_model.timeParseError.connect(
                lambda err: self._show_error(err)
            )
            self.proxy_model.setSortRole(Qt.UserRole)
            self.proxy_model.dataChanged.connect(self._sort_model)
            self.proxy_model.dataChanged.connect(self.update_slider_highlight)
            self.proxy_model.setSourceModel(self.timestamp_model)
            self.proxy_model.rowsInserted.connect(self._sort_model)
            self.proxy_model.rowsInserted.connect(self._select_blank_row)
            self.ui.list_timestamp.setModel(self.proxy_model)

            self.timestamp_filename = filename
            self.ui.entry_timestamp.setText(self.timestamp_filename)

            self.mapper.setModel(self.proxy_model)
            self.mapper.addMapping(self.ui.entry_start_time, 0)
            self.mapper.addMapping(self.ui.entry_end_time, 1)
            self.mapper.addMapping(self.ui.entry_description, 2)
            self.ui.list_timestamp.selectionModel().selectionChanged.connect(
                self.timestamp_selection_changed)
            self._sort_model()

            directory = os.path.dirname(self.timestamp_filename)
            basename = os.path.basename(self.timestamp_filename)
            timestamp_name_without_ext = os.path.splitext(basename)[0]
            for file_in_dir in os.listdir(directory):
                current_filename = os.path.splitext(file_in_dir)[0]
                found_video = (current_filename == timestamp_name_without_ext
                               and file_in_dir != basename)
                if found_video:
                    found_video_file = os.path.join(directory, file_in_dir)
                    self.set_video_filename(found_video_file)
                    break
        except ValueError as err:
            self._show_error("Timestamp file is invalid")

    def timestamp_selection_changed(self, selected, deselected):
        if len(selected) > 0:
            self.mapper.setCurrentModelIndex(selected.indexes()[0])
            self.ui.button_save.setEnabled(True)
            self.ui.button_remove_entry.setEnabled(True)
            self.ui.entry_start_time.setReadOnly(False)
            self.ui.entry_end_time.setReadOnly(False)
            self.ui.entry_description.setReadOnly(False)
        else:
            self.mapper.setCurrentModelIndex(QModelIndex())
            self.ui.button_save.setEnabled(False)
            self.ui.button_remove_entry.setEnabled(False)
            self.ui.entry_start_time.clear()
            self.ui.entry_end_time.clear()
            self.ui.entry_description.clear()
            self.ui.entry_start_time.setReadOnly(True)
            self.ui.entry_end_time.setReadOnly(True)
            self.ui.entry_description.setReadOnly(True)

    def set_video_filename(self, filename):
        """
        Set the video filename
        """
        if not os.path.isfile(filename):
            self._show_error("Cannot access video file " + filename)
            return

        self.video_filename = filename

        media = self.vlc_instance.media_new(self.video_filename)
        media.parse()
        if not media.get_duration():
            self._show_error("Cannot play this media file")
            self.media_player.set_media(None)
            self.video_filename = None
        else:
            self.media_player.set_media(media)
            if sys.platform.startswith('linux'): # for Linux using the X Server
                self.media_player.set_xwindow(self.ui.frame_video.winId())
            elif sys.platform == "win32": # for Windows
                self.media_player.set_hwnd(self.ui.frame_video.winId())
            elif sys.platform == "darwin": # for MacOS
                self.media_player.set_nsobject(self.ui.frame_video.winId())
            self.ui.entry_video.setText(self.video_filename)

            self.update_video_file_labels_on_file_change()
            self.media_started_playing = False
            self.media_is_playing = False
            # self.set_volume(self.ui.slider_volume.value())
            self.play_pause_model.setState(True)

    def browse_video_handler(self):
        """
        Handler when the video browse button is clicked
        """
        tmp_name, _ = QFileDialog.getOpenFileName(
            self, "Choose Video file", None,
            "All Files (*)"
        )
        if not tmp_name:
            return
        self.set_video_filename(QDir.toNativeSeparators(tmp_name))

    def _show_error(self, message, title="Error"):
        QMessageBox.warning(self, title, message)

