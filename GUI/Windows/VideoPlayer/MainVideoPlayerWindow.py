#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import traceback

import qtawesome as qta
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox, QDataWidgetMapper, QPushButton
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import QDir, QTimer, Qt, QModelIndex, QSortFilterProxyModel, pyqtSignal, pyqtSlot

from lib import vlc
from app.model import TimestampModel, ToggleButtonModel, TimestampDelta

from GUI.Model.Errors import SimpleErrorStatusMixin
from GUI.Model.DataMovieLinkInfo import *

from GUI.Helpers.DateTimeRenders import DateTimeRenderMixin

"""
The software displays/plays a video file with variable speed and navigation settings.
The software runs a timer, which calls both self.timer_handler() and self.update_ui().

self.update_ui():
    - Updates the slider_progress (playback slider) when the video plays
    - Updates the video labels

self.vlc_event_media_time_change_handler(...) is called on VLC's MediaPlayerTimeChanged event:
    - 
"""


""" Classes belonging to the main media widget
lblVideoName
lblVideoSubtitle
dateTimeEdit
lblCurrentFrame
spinBoxCurrentFrame
lblTotalFrames
lblCurrentTime
lblTotalDuration
lblFileFPS
spinBoxFrameJumpMultiplier

btnSkipLeft
btnSkipRight
btnLeft
btnRight

button_play_pause
button_full_screen

button_speed_up
doubleSpinBoxPlaybackSpeed
button_slow_down

button_mark_start
button_mark_end

slider_progress

## DATA MODEL:
self.media_start_time = None
        self.media_end_time = None
        self.restart_needed = False
        self.timer_period = 100
        self.is_full_screen = False
        self.media_started_playing = False
        self.media_is_playing = False
        self.original_geometry = None
play_pause_model


"""

""" MediaPlayerUpdatingMixin: used by MainVideoPlayerWindow to load/change media
        self._movieLink = None
"""
class MediaPlayerUpdatingMixin(SimpleErrorStatusMixin, object):
    loaded_media_changed = pyqtSignal() # Called when the loaded video is changed

    # Internal Signals
    _movie_link_changed = pyqtSignal()
    _video_filename_changed = pyqtSignal()

    def get_video_filename(self):
        if self._movieLink is None:
            return None
        else:
            return str(self._movieLink.get_video_url())

    def get_movie_link(self):
        return self._movieLink


    @property
    def video_filename(self):
        return self.get_video_filename()


    # @property
    # def movieLink(self):
    #     return self.get_movie_link()



    @pyqtSlot()
    def set_video_media_link(self, newMediaLink):
        self._movieLink = newMediaLink
        self._movie_link_changed.emit()

        
    @pyqtSlot()
    def _on_movie_link_changed(self):
        newVideoFilename = self.get_video_filename()
        if not os.path.isfile(newVideoFilename):
            self.set_has_error("ERROR: Cannot access video file " + newVideoFilename)
            self._show_error("ERROR: Cannot access video file " + newVideoFilename)
            return
        else:
            self._video_filename_changed.emit()

    @pyqtSlot()
    def _on_video_filename_changed(self):
        """
        Set the video filename
        """
        # Close the previous file:
        self.media_stop()

        self.startDirectory = os.path.pardir
        # self.video_filename = filename

        self.media = self.vlc_instance.media_new(self.video_filename)
        self.media.parse()
        if not self.media.get_duration():
            self.set_has_error("Cannot play this media file")
            self._show_error("Cannot play this media file")
            self.media_player.set_media(None)
        else:
            self.media_player.set_media(self.media)

            # The media player has to be 'connected' to the QFrame (otherwise the
            # video would be displayed in it's own window). This is platform
            # specific, so we must give the ID of the QFrame (or similar object) to
            # vlc. Different platforms have different functions for this
            if sys.platform.startswith('linux'): # for Linux using the X Server
                self.media_player.set_xwindow(self.ui.frame_video.winId())
            elif sys.platform == "win32": # for Windows
                self.media_player.set_hwnd(self.ui.frame_video.winId())
            elif sys.platform == "darwin": # for MacOS
                self.media_player.set_nsobject(self.ui.frame_video.winId())
            else:
                print("WARNING: MainVideoPlayerWindow.set_video_filename(...): Unknown platform! {0}".format(str(sys.platform)))

            self.update_window_title()
            self.update_video_file_labels_on_file_change()
            self.media_started_playing = False
            self.media_is_playing = False
            # self.set_volume(self.ui.slider_volume.value())
            self.play_pause_model.setState(True)
            self.update_preview_frame()

        self.loaded_media_changed.emit()

""" VideoPlaybackRenderingWidgetMixin: Renders the frame under the video that displays the current video playback information
Implementor Requirements:
    video_playback_position_updated = pyqtSignal(float)
    loaded_media_changed = pyqtSignal()

GUI:
    frame_CurrentVideoPlaybackInformation

    # Duration Representations:
    lblPlayheadRelativeDuration
    lblTotalVideoDuration

    # Frames Representation:
    lblPlayheadFrame
    lblTotalVideoFrames

    # Datetime Representations:
    btn_VideoStartDatetime
    btn_PlayheadDatetime
    btn_VideoEndDatetime
"""
class VideoPlaybackRenderingWidgetMixin(DateTimeRenderMixin, object):

    def init_VideoPlaybackRenderingWidgetMixin(self):
        are_buttons_initially_enabled = False

        # Duration Representations:
        self.ui.lblPlayheadRelativeDuration.setText("--")
        self.ui.lblTotalVideoDuration.setText("--")

        # Frames Representations:
        self.ui.lblPlayheadFrame.setText("--")
        self.ui.lblTotalVideoFrames.setText("--")

        # Datetime Representations:
        self.ui.btn_VideoStartDatetime.setText("--")
        self.ui.btn_PlayheadDatetime.setText("--")
        self.ui.btn_VideoEndDatetime.setText("--")

        self.ui.btn_VideoStartDatetime.setEnabled(are_buttons_initially_enabled)
        self.ui.btn_PlayheadDatetime.setEnabled(are_buttons_initially_enabled)
        self.ui.btn_VideoEndDatetime.setEnabled(are_buttons_initially_enabled)

        self.ui.btn_VideoStartDatetime.clicked.connect(lambda: self.on_date_button_click(self.ui.btn_VideoStartDatetime))
        self.ui.btn_PlayheadDatetime.clicked.connect(lambda: self.on_date_button_click(self.ui.btn_PlayheadDatetime))
        self.ui.btn_VideoEndDatetime.clicked.connect(lambda: self.on_date_button_click(self.ui.btn_VideoEndDatetime))


        # Connect to signals ## TODO: Assumes it's connected to a video player widget
        self.loaded_media_changed.connect(self.on_media_changed_VideoPlaybackRenderingWidgetMixin)
        self.video_playback_position_updated.connect(self.on_playback_position_changed_VideoPlaybackRenderingWidgetMixin)


    # Updates only the dynamic (playback-position-dependent) labels and buttons
    @pyqtSlot(float)
    def on_playback_position_changed_VideoPlaybackRenderingWidgetMixin(self, newPlaybackPosition):
        # Dynamic info:
        are_buttons_enabled = True
        dynamic_curr_playhead_duration_text = "--"
        dynamic_curr_playhead_frame_text = "--"
        dynamic_curr_playhead_datetime_text = "--"

        curr_playback_frame = self.get_current_playhead_frame()
        if curr_playback_frame is not None:
            dynamic_curr_playhead_frame_text = str(curr_playback_frame)
        else:
            dynamic_curr_playhead_frame_text = "--"
            are_buttons_enabled = False

        curr_playback_position_duration = self.get_current_playhead_duration_offset()
        if curr_playback_position_duration is not None:
            dynamic_curr_playhead_duration_text = (str(curr_playback_position_duration) + " [ms]")  # Gets time in [ms]
        else:
            dynamic_curr_playhead_duration_text = "--"  # Gets time in [ms]
            are_buttons_enabled = False

        curr_video_movie_link = self.get_movie_link()
        if curr_video_movie_link is not None:
            # curr_video_playback_datetime = curr_video_movie_link.get_active_absolute_datetime()
            curr_video_playback_datetime = curr_video_movie_link.compute_absolute_time(newPlaybackPosition)
            dynamic_curr_playhead_datetime_text = self.get_full_long_date_time_string(curr_video_playback_datetime)
            pass
        else:
            dynamic_curr_playhead_datetime_text = "--"
            are_buttons_enabled = False
            pass
        
        # Duration Representations:
        self.ui.lblPlayheadRelativeDuration.setText(dynamic_curr_playhead_duration_text)

        # Frames Representations:
        self.ui.lblPlayheadFrame.setText(dynamic_curr_playhead_frame_text)

        # Datetime Representations:
        self.ui.btn_PlayheadDatetime.setText(dynamic_curr_playhead_datetime_text)
        self.ui.btn_PlayheadDatetime.setEnabled(are_buttons_enabled)
            

    # Updates the indicators when a new video is loaded or the movie link is changed
    @pyqtSlot()
    def on_media_changed_VideoPlaybackRenderingWidgetMixin(self):

        are_buttons_enabled = True

        # Static info:
        total_video_duration_text = "--"
        total_video_frames_text = "--"
        video_start_datetime_text = "--"
        video_end_datetime_text = "--"

        # Dynamic info:
        dynamic_curr_playhead_duration_text = "--"
        dynamic_curr_playhead_frame_text = "--"
        dynamic_curr_playhead_datetime_text = "--"
        

        if self.video_filename is None:
            are_buttons_enabled = False
        else:
            # Only updated when the video file is changed:
            curr_total_duration = self.media_player.get_length()
            totalNumFrames = self.get_media_total_num_frames()
            if totalNumFrames > 0:
                total_video_frames_text = str(totalNumFrames)
                dynamic_curr_playhead_frame_text = "--"

                curr_playback_frame = self.get_current_playhead_frame()
                if curr_playback_frame is not None:
                    dynamic_curr_playhead_frame_text = str(curr_playback_frame)
                else:
                    dynamic_curr_playhead_frame_text = "--"
                    
            else:
                total_video_frames_text = "--"
                dynamic_curr_playhead_frame_text = "--"
                are_buttons_enabled = False

            if curr_total_duration > 0:
                total_video_duration_text = (str(curr_total_duration) + " [ms]")  # Gets duration in [ms]
                
                curr_playback_position_duration = self.get_current_playhead_duration_offset()
                if curr_playback_position_duration is not None:
                    dynamic_curr_playhead_duration_text = (str(curr_playback_position_duration) + " [ms]")  # Gets time in [ms]
                else:
                    dynamic_curr_playhead_duration_text = "--"  # Gets time in [ms]

            else:
                total_video_duration_text = "--"
                dynamic_curr_playhead_duration_text = "--"
                are_buttons_enabled = False

            # Get video start and end datetimes
            curr_video_movie_link = self.get_movie_link()
            if curr_video_movie_link is not None:
                video_start_time = curr_video_movie_link.get_video_start_time()
                video_start_datetime_text = self.get_full_long_date_time_string(video_start_time)
                video_end_time = curr_video_movie_link.get_video_end_time()                
                video_end_datetime_text = self.get_full_long_date_time_string(video_end_time)

                # curr_video_playback_datetime = curr_video_movie_link.get_active_absolute_datetime()
                curr_video_playback_datetime = video_start_time # Assume the playhead is at the starttime to start.
                dynamic_curr_playhead_datetime_text = self.get_full_long_date_time_string(curr_video_playback_datetime)

                pass
            else:
                video_start_datetime_text = "--"
                video_end_datetime_text = "--"
                dynamic_curr_playhead_datetime_text = "--"

                are_buttons_enabled = False
                pass

        # Duration Representations:
        self.ui.lblPlayheadRelativeDuration.setText(dynamic_curr_playhead_duration_text)
        self.ui.lblTotalVideoDuration.setText(total_video_duration_text)

        # Frames Representations:
        self.ui.lblPlayheadFrame.setText(dynamic_curr_playhead_frame_text)
        self.ui.lblTotalVideoFrames.setText(total_video_frames_text)

        # Datetime Representations:
        self.ui.btn_VideoStartDatetime.setText(video_start_datetime_text)
        self.ui.btn_PlayheadDatetime.setText(dynamic_curr_playhead_datetime_text)
        self.ui.btn_VideoEndDatetime.setText(video_end_datetime_text)

        self.ui.btn_VideoStartDatetime.setEnabled(are_buttons_enabled)
        self.ui.btn_PlayheadDatetime.setEnabled(are_buttons_enabled)
        self.ui.btn_VideoEndDatetime.setEnabled(are_buttons_enabled)

    # _copy_to_clipboard(clipboardText): sets the system's clipboard to clipboardText
    def _copy_to_clipboard(self, clipboardText):
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard )
        cb.setText(clipboardText, mode=cb.Clipboard)

    @pyqtSlot(QPushButton)
    def on_date_button_click(self, button):
        # Copy the button's text to clipboard
        buttonText = button.text()
        self._copy_to_clipboard(buttonText)


""" VLCVideoEventMixin: handles VLC callback events

"""
class VLCVideoEventMixin(object):
    
    # vlc_event_media_time_change_handler(...) is called on VLC's MediaPlayerTimeChanged event
    @vlc.callbackmethod
    def vlc_event_media_time_change_handler(self, _):
        # print('Time changed!')

        if (not (self.media_player is None)):
            currPos = self.media_player.get_position()
            self.video_playback_position_updated.emit(currPos)

        if (self.is_display_initial_frame_playback):
            # self.is_display_initial_frame_playback: true to indicate that we're just trying to play the media long enough to get the first frame, so it's not a black square
            # Pause
            self.media_pause()
            self.is_display_initial_frame_playback = False # Set the variable to false so it quits pausing

        if self.media_end_time == -1:
            return
        if self.media_player.get_time() > self.media_end_time:
            self.restart_needed = True

    # vlc_event_media_player_media_changed_handler(...) is called on VLC's MediaPlayerMediaChanged event
    @vlc.callbackmethod
    def vlc_event_media_player_media_changed_handler(self, _):
        print("vlc_event_media_player_media_changed_handler()")
        print("    - length: {0}, num_frames: {1}".format(str(self.media_player.get_length()), str(self.get_media_total_num_frames())))
        self.update_video_file_labels_on_file_change()
        self.on_media_changed_VideoPlaybackRenderingWidgetMixin()

    # vlc_event_media_duration_changed_handler(...) is called on VLC's MediaDurationChanged event
    @vlc.callbackmethod
    def vlc_event_media_duration_changed_handler(self, _):
        print("vlc_event_media_duration_changed_handler()")
        print("    - length: {0}, num_frames: {1}".format(str(self.media_player.get_length()), str(self.get_media_total_num_frames())))


    # vlc_event_media_player_parsed_changed_handler(...) is called on VLC's MediaParsedChanged event
    @vlc.callbackmethod
    def vlc_event_media_player_parsed_changed_handler(self, _):
        print("vlc_event_media_player_parsed_changed_handler()")
        print("    - length: {0}, num_frames: {1}".format(str(self.media_player.get_length()), str(self.get_media_total_num_frames())))


    # vlc_event_media_player_length_changed_handler(...) is called on VLC's MediaPlayerLengthChanged event
    @vlc.callbackmethod
    def vlc_event_media_player_length_changed_handler(self, _):
        print("vlc_event_media_player_length_changed_handler()")
        print("    - length: {0}, num_frames: {1}".format(str(self.media_player.get_length()), str(self.get_media_total_num_frames())))
        self.update_video_file_labels_on_file_change()
        self.on_media_changed_VideoPlaybackRenderingWidgetMixin()


class MainVideoPlayerWindow(VideoPlaybackRenderingWidgetMixin, MediaPlayerUpdatingMixin, VLCVideoEventMixin, QMainWindow):
    """
    The main window class
    """

    SpeedBurstPlaybackRate = 16.0
    EnableFrameSpinBox = False

    video_playback_position_updated = pyqtSignal(float) # video_playback_position_updated:  called when the playback position of the video changes. Either due to playing, or after a user event
    video_playback_state_changed = pyqtSignal() # video_playback_state_changed: called when play/pause state changes
    close_signal = pyqtSignal() # Called when the window is closing. 


    def __init__(self, parent=None):
        # QMainWindow.__init__(self, parent)
        super().__init__(parent=parent)
        self.ui = uic.loadUi("GUI/Windows/VideoPlayer/MainVideoPlayerWindow.ui", self)

        self.timestamp_filename = None
        # self.video_filename = None
        self.media_start_time = None
        self.media_end_time = None
        self.restart_needed = False
        self.timer_period = 100
        self.is_full_screen = False
        self.media_started_playing = False
        self.media_is_playing = False
        self.original_geometry = None

        self.startDirectory = None

        # TODO: REMOVE
        self.timestamp_model = TimestampModel(None, self)
        self.proxy_model = QSortFilterProxyModel(self)

        self.vlc_instance = vlc.Instance()
        self.media_player = self.vlc_instance.media_player_new()
        self.is_display_initial_frame_playback = False

        self.is_speed_burst_mode_active = False
        self.speedBurstPlaybackRate = MainVideoPlayerWindow.SpeedBurstPlaybackRate
        # if sys.platform == "darwin":  # for MacOS
        #     self.ui.frame_video = QMacCocoaViewContainer(0)

        self._movieLink = None

        # MediaPlayerUpdatingMixin init
        self._error_string = None
        self._movie_link_changed.connect(self._on_movie_link_changed)
        self._video_filename_changed.connect(self._on_video_filename_changed)

        self.initUI()

    def initUI(self):

        # TODO: bind the signals and such to self.ui.timestampSidebarWidget
        # self.ui.timestampSidebarWidget.

        self.init_VideoPlaybackRenderingWidgetMixin()

        self.timer = QTimer(self)
        self.timer.setInterval(self.timer_period)
        self.timer.timeout.connect(self.update_ui)
        self.timer.timeout.connect(self.timer_handler)


        self.ui.frame_video.doubleClicked.connect(self.toggle_full_screen)
        self.ui.frame_video.wheel.connect(self.wheel_handler)

        # TODO: would send twice when the frame_video has focus.
        # self.keyPressEvent.connect(self.key_handler)
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
        self.ui.spinBoxCurrentFrame.setHidden(not MainVideoPlayerWindow.EnableFrameSpinBox)
        if MainVideoPlayerWindow.EnableFrameSpinBox:
            self.ui.spinBoxCurrentFrame.valueChanged.connect(self.handle_frame_value_changed)

        self.ui.lblTotalFrames.setText("")

        self.ui.lblCurrentTime.setText("")
        self.ui.lblTotalDuration.setText("")

        self.ui.lblFileFPS.setText("")

        self.ui.spinBoxFrameJumpMultiplier.value = 1

        # Set up buttons

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

        # Set up default volume
        # self.set_volume(self.ui.slider_volume.value())

        self.vlc_events = self.media_player.event_manager()
        self.vlc_events.event_attach(
            vlc.EventType.MediaPlayerTimeChanged, self.vlc_event_media_time_change_handler
        )
        self.vlc_events.event_attach(
            vlc.EventType.MediaPlayerMediaChanged, self.vlc_event_media_player_media_changed_handler
        )

        # Strangely never called.
        self.vlc_events.event_attach(
            vlc.EventType.MediaDurationChanged, self.vlc_event_media_duration_changed_handler
        )

        # Never called
        self.vlc_events.event_attach(
            vlc.EventType.MediaParsedChanged, self.vlc_event_media_player_parsed_changed_handler
        )

        # Successfully called after vlc_event_media_player_media_changed_handler()
        self.vlc_events.event_attach(
            vlc.EventType.MediaPlayerLengthChanged, self.vlc_event_media_player_length_changed_handler
        )


        
            

        # Let our application handle mouse and key input instead of VLC
        self.media_player.video_set_mouse_input(False)
        self.media_player.video_set_key_input(False)

        self.timer.start()

        self.update_video_frame_overlay_text("")

        self.ui.show()

    # Called when the window is closing.
    def closeEvent(self, event):
        print("MainVideoPlayerWindow.closeEvent({0})".format(str(event)))
        self.on_close()
        # self.close()
        event.accept()

    def on_close(self):
        """ Perform on close stuff here """
        print("MainVideoPlayerWindow.on_close()!")
        self.timer.stop() # Stop the timer
        self.media_player.stop() # Stop the playing media
        self._movieLink = None
        self.close_signal.emit()

    # Movie Link:
    def get_movie_link(self):
        return self._movieLink

    # Called when the UI slider position is updated via user-click
    def set_media_position(self, position):
        percentage = position / 10000.0
        self.media_player.set_position(percentage)
        absolute_position = percentage * \
            self.media_player.get_media().get_duration()
        if absolute_position > self.media_end_time:
            self.media_end_time = -1

    # on_timeline_position_updated(...): called when the main timeline window updates the position. Results in programmatically setting the video playback position
    @pyqtSlot(float)
    def on_timeline_position_updated(self, new_video_percent_offset):
        print("on_timeline_position_updated({0})".format(str(new_video_percent_offset)))
        aPosition = new_video_percent_offset * 10000.0 # Not sure what this does, but it does the inverse of what's done in the start of the "set_media_position(...)" function to get the percentage
        self.set_media_position(aPosition)

        ### NOT YET IMPLEMENTED
        print("TODO: NOT YET IMPLEMENTED!!!!")

        # Or we could rely on the signals generated by the slider, which is how it normally works. Just set the slider's position and everything else should update.
        # TODO: the only provision is that it shouldn't re-emit a "video_playback_position_updated" signal to avoid a cycle
        # TODO: can I block a specific signal? like self.video_playback_position_updated.blockSignals(True)
        self.ui.slider_progress.blockSignals(True)
        self.ui.slider_progress.setValue(aPosition)
        self.ui.slider_progress.blockSignals(False)


    def set_mark(self, start_time=None, end_time=None):
        pass
        # if len(self.ui.list_timestamp.selectedIndexes()) == 0:
        #     blankRowIndex = self.timestamp_model.blankRowIndex()
        #     if not blankRowIndex.isValid():
        #         self.add_entry()
        #     else:
        #         index = self.proxy_model.mapFromSource(blankRowIndex)
        #         self.ui.list_timestamp.selectRow(index.row())
        # selectedIndexes = self.ui.list_timestamp.selectedIndexes()
        # if start_time:
        #     self.proxy_model.setData(selectedIndexes[0],
        #                              TimestampDelta.string_from_int(
        #                                  start_time))
        # if end_time:
        #     self.proxy_model.setData(selectedIndexes[1],
        #                              TimestampDelta.string_from_int(
        #                                  end_time))

    # self.update_ui(): called when the timer fires
    def update_ui(self):
        if self.media_player is None:
            return

        # Update the UI Slider to match the current video playback value
        self.ui.slider_progress.blockSignals(True)
        self.ui.slider_progress.setValue(
            self.media_player.get_position() * 10000.0
        )
        #print(self.media_player.get_position() * 10000)

        self.update_video_file_play_labels()

        self.ui.slider_progress.blockSignals(False)

        self.ui.doubleSpinBoxPlaybackSpeed.blockSignals(True)
        self.ui.doubleSpinBoxPlaybackSpeed.setValue(self.media_player.get_rate())
        self.ui.doubleSpinBoxPlaybackSpeed.blockSignals(False)

        currPos = self.media_player.get_position()
        self.video_playback_position_updated.emit(currPos)
        
        # When the video finishes
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

    # self.timer_handler(): called when the timer fires
    def timer_handler(self):
        """
        This is a workaround, because for some reason we can't call set_time()
        inside the MediaPlayerTimeChanged handler (as the video just stops
        playing)
        """
        if self.restart_needed:
            self.media_player.set_time(self.media_start_time)
            self.restart_needed = False


    # Input Handelers:
    def key_handler(self, event):
        print("MainVideoPlayerWindow key handler: {0}".format(str(event.key())))
        if event.key() == Qt.Key_Escape and self.is_full_screen:
            self.toggle_full_screen()
        if event.key() == Qt.Key_F:
            self.toggle_full_screen()
        if event.key() == Qt.Key_Space:
            self.play_pause()
        if event.key() == Qt.Key_P:
            self.toggle_speed_burst()


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



        
    # TODO: REMOVE?? Check
    def update_slider_highlight(self):
        # if self.ui.list_timestamp.selectionModel().hasSelection():
        #     selected_row = self.ui.list_timestamp.selectionModel(). \
        #         selectedRows()[0]
        #     self.media_start_time = self.ui.list_timestamp.model().data(
        #         selected_row.model().index(selected_row.row(), 0),
        #         Qt.UserRole
        #     )
        #     self.media_end_time = self.ui.list_timestamp.model().data(
        #         selected_row.model().index(selected_row.row(), 1),
        #         Qt.UserRole
        #     )
        #     duration = self.media_player.get_media().get_duration()
        #     self.media_end_time = self.media_end_time \
        #         if self.media_end_time != 0 else duration
        #     if self.media_start_time > self.media_end_time:
        #         raise ValueError("Start time cannot be later than end time")
        #     if self.media_start_time > duration:
        #         raise ValueError("Start time not within video duration")
        #     if self.media_end_time > duration:
        #         raise ValueError("End time not within video duration")
        #     slider_start_pos = (self.media_start_time / duration) * \
        #                        (self.ui.slider_progress.maximum() -
        #                         self.ui.slider_progress.minimum())
        #     slider_end_pos = (self.media_end_time / duration) * \
        #                      (self.ui.slider_progress.maximum() -
        #                       self.ui.slider_progress.minimum())
        #     self.ui.slider_progress.setHighlight(
        #         int(slider_start_pos), int(slider_end_pos)
        #     )

        # else:
            
        self.media_start_time = 0
        self.media_end_time = -1

    def run(self):
        """
        Execute the loop
        """
        # if self.timestamp_filename is None:
        #     self._show_error("No timestamp file chosen")
        #     return
        if self.video_filename is None:
            self._show_error("No video file chosen")
            return
        try:
            self.update_slider_highlight()
            self.media_player.play()
            self.media_player.set_time(self.media_start_time) # Looks like the media playback time is actually being set from the slider.
            self.media_started_playing = True
            self.media_is_playing = True
            self.play_pause_model.setState(False)
        except Exception as ex:
            self._show_error(str(ex))
            print(traceback.format_exc())

    # Toggles play/pause status:
    def play_pause(self):
        """Toggle play/pause status
        """
        if not self.media_started_playing:
            self.run()
            return
        if self.media_is_playing:
            self.media_pause()
        else:
            self.media_play()
            
    # Plays the media:
    def media_play(self):
        if not self.media_started_playing:
            self.run()
            return
        if self.media_is_playing:
            return # It's already playing, just return
        else:
            self.media_player.play()
            self.post_playback_state_changed_update()

    # Pauses the media:
    def media_pause(self):
        if not self.media_started_playing:
            self.run()
            return
        if self.media_is_playing:
            self.media_player.pause()
            self.post_playback_state_changed_update()
        else:
            return # It's already paused, just return

    # Stops the media:
    def media_stop(self):
        if not self.media_started_playing:
            return # It's already stopped, just return
        if self.media_is_playing:
            self.media_player.pause()

        self.media_player.stop()        
        self.post_playback_state_changed_update()
        
    def post_playback_state_changed_update(self):
        # Called after the play, pause, stop state changed
        self.media_is_playing = not self.media_is_playing
        self.play_pause_model.setState(not self.media_is_playing)
        self.video_playback_state_changed.emit()

    # Updates the window title with the filename
    # TODO: doesn't work
    def update_window_title(self):
        print("update_window_title(): {0}".format(self.video_filename))
        if (self.video_filename is None):
            # self.setWindowFilePath(None)
            self.setWindowTitle("Video Player: No Video")
            pass
        else:
            # self.setWindowFilePath(self.video_filename)
            self.setWindowTitle("Video Player: " + str(self.video_filename))
            pass

        
    # This updates the text that is overlayed over the top of the video frame. It serves to temporarily display changes in state, like play, pause, stop, skip, etc to provide feedback and notifications to the user.
    def update_video_frame_overlay_text(self, new_string):
        #TODO: should display the message for a few seconds, and then timeout and disappear
        self.ui.lblVideoStatusOverlay.setText(new_string)

    # After a new media has been set, this function is called to start playing for a short bit to display the first few frames of the video
    def update_preview_frame(self):
        # Updates the frame displayed in the media player
        self.is_display_initial_frame_playback = True
        self.media_play()
        # Pause is called in the self.vlc_event_media_time_change_handler(...)

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
            self.ui.lblPlaybackPercent.setText("{:.4f}".format(curr_percent_complete))
        else:
            self.ui.lblPlaybackPercent.setText("--")

        curr_frame = self.get_current_playhead_frame()

        # Disable frame change on spinBox update to prevent infinite loop
        if MainVideoPlayerWindow.EnableFrameSpinBox:
            self.ui.spinBoxCurrentFrame.blockSignals(True)
            if curr_frame is not None:
                self.ui.lblCurrentFrame.setText(str(curr_frame))
                #self.ui.spinBoxCurrentFrame.setValue(curr_frame)
                #self.ui.spinBoxCurrentFrame.setEnabled(True)
            else:
                self.ui.lblCurrentFrame.setText("--")
                #self.ui.spinBoxCurrentFrame.setEnabled(False)
                #self.ui.spinBoxCurrentFrame.setValue(1)

            # Re-enable signals from the frame spin box after update
            self.ui.spinBoxCurrentFrame.blockSignals(False)

        curr_playback_position_duration = self.get_current_playhead_duration_offset()
        if curr_playback_position_duration is not None:
            self.ui.lblCurrentTime.setText(str(curr_playback_position_duration) + "[ms]")  # Gets time in [ms]
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
                if MainVideoPlayerWindow.EnableFrameSpinBox:
                    self.ui.spinBoxCurrentFrame.setMaximum(totalNumFrames)
                    self.ui.spinBoxCurrentFrame.setEnabled(True)
            else:
                self.ui.lblTotalFrames.setText("--")
                if MainVideoPlayerWindow.EnableFrameSpinBox:
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

    ## Current playhead functions
    """ get_current_playhead_frame(): Gets the current frame position of the playhead
    Returns: duration in [ms] or None
    """
    def get_current_playhead_frame(self):
        if self.media_player is None:
            return None

        curr_percent_complete = self.media_player.get_position()  # Current percent complete between 0.0 and 1.0
        totalNumFrames = self.get_media_total_num_frames()

        if curr_percent_complete >= 0:
            curr_frame = int(round(curr_percent_complete * totalNumFrames))
            return curr_frame
        else:
            return None


    """ get_current_playhead_duration_offset(): Gets the current duration since the start of the video
    Returns: duration in [ms] or None
    """
    def get_current_playhead_duration_offset(self):
        if self.media_player is None:
            return None

        if self.media_player.get_time() >= 0:
            return self.media_player.get_time() # Gets time in [ms]
        else:
            return None 


    # Playback Navigation (Left/Right) Handlers:
    def step_left_handler(self):
        print('step: left')
        self.seek_frames(-1 * self.get_frame_multipler())
        
    def skip_left_handler(self):
        print('skip: left')
        self.seek_frames(-10 * self.get_frame_multipler())

    def step_right_handler(self):
        print('step: right')
        self.seek_frames(1 * self.get_frame_multipler())

    def skip_right_handler(self):
        print('skip: right')
        self.seek_frames(10 * self.get_frame_multipler())

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
     # TODO: REMOVE
    def browse_timestamp_handler(self):
        # """
        # Handler when the timestamp browser button is clicked
        # """
        # tmp_name, _ = QFileDialog.getOpenFileName(
        #     self, "Choose Timestamp file", None,
        #     "Timestamp File (*.tmsp);;All Files (*)"
        # )
        # if not tmp_name:
        #     return
        # self.set_timestamp_filename(QDir.toNativeSeparators(tmp_name))
        pass

    # TODO: REMOVE
    def create_timestamp_file_handler(self):
        """
        Handler when the timestamp file create button is clicked
        """
        # tmp_name, _ = QFileDialog.getSaveFileName(
        #     self, "Create New Timestamp file", None,
        #     "Timestamp File (*.tmsp);;All Files (*)"
        # )
        # if not tmp_name:
        #     return

        # try:
        #     if (os.stat(QDir.toNativeSeparators(tmp_name)).st_size == 0):
        #             # File is empty, create a non-empty one:
        #             with open(QDir.toNativeSeparators(tmp_name), "w") as fh:
        #                 fh.write("[]")  # Write the minimal valid JSON string to the file to allow it to be used
        #     else:
        #         pass

        # except WindowsError:
        #     with open(tmp_name, "w") as fh:
        #         fh.write("[]") # Write the minimal valid JSON string to the file to allow it to be used

        # # Create new file:
        # self.set_timestamp_filename(QDir.toNativeSeparators(tmp_name))
        pass

    # TODO: REMOVE
    def _sort_model(self):
        # self.ui.list_timestamp.sortByColumn(0, Qt.AscendingOrder)
        pass

    # TODO: REMOVE
    def _select_blank_row(self, parent, start, end):
        # self.ui.list_timestamp.selectRow(start)
        pass

    # TODO: REMOVE
    def set_timestamp_filename(self, filename):
        """
        Set the timestamp file name
        """
        pass
        # if not os.path.isfile(filename):
        #     self._show_error("Cannot access timestamp file " + filename)
        #     return

        # try:
        #     self.timestamp_model = TimestampModel(filename, self)
        #     self.timestamp_model.timeParseError.connect(
        #         lambda err: self._show_error(err)
        #     )
        #     self.proxy_model.setSortRole(Qt.UserRole)
        #     self.proxy_model.dataChanged.connect(self._sort_model)
        #     self.proxy_model.dataChanged.connect(self.update_slider_highlight)
        #     self.proxy_model.setSourceModel(self.timestamp_model)
        #     self.proxy_model.rowsInserted.connect(self._sort_model)
        #     self.proxy_model.rowsInserted.connect(self._select_blank_row)
        #     self.ui.list_timestamp.setModel(self.proxy_model)

        #     self.timestamp_filename = filename
        #     self.ui.entry_timestamp.setText(self.timestamp_filename)

        #     self.mapper.setModel(self.proxy_model)
        #     self.mapper.addMapping(self.ui.entry_start_time, 0)
        #     self.mapper.addMapping(self.ui.entry_end_time, 1)
        #     self.mapper.addMapping(self.ui.entry_description, 2)
        #     self.ui.list_timestamp.selectionModel().selectionChanged.connect(
        #         self.timestamp_selection_changed)
        #     self._sort_model()

        #     directory = os.path.dirname(self.timestamp_filename)
        #     basename = os.path.basename(self.timestamp_filename)
        #     timestamp_name_without_ext = os.path.splitext(basename)[0]
        #     for file_in_dir in os.listdir(directory):
        #         current_filename = os.path.splitext(file_in_dir)[0]
        #         found_video = (current_filename == timestamp_name_without_ext
        #                        and file_in_dir != basename)
        #         if found_video:
        #             found_video_file = os.path.join(directory, file_in_dir)
        #             self.set_video_filename(found_video_file)
        #             break
        # except ValueError as err:
        #     self._show_error("Timestamp file is invalid")

    # TODO: REMOVE
    def timestamp_selection_changed(self, selected, deselected):
        pass
        # if len(selected) > 0:
        #     self.mapper.setCurrentModelIndex(selected.indexes()[0])
        #     self.ui.button_save.setEnabled(True)
        #     self.ui.button_remove_entry.setEnabled(True)
        #     self.ui.entry_start_time.setReadOnly(False)
        #     self.ui.entry_end_time.setReadOnly(False)
        #     self.ui.entry_description.setReadOnly(False)
        # else:
        #     self.mapper.setCurrentModelIndex(QModelIndex())
        #     self.ui.button_save.setEnabled(False)
        #     self.ui.button_remove_entry.setEnabled(False)
        #     self.ui.entry_start_time.clear()
        #     self.ui.entry_end_time.clear()
        #     self.ui.entry_description.clear()
        #     self.ui.entry_start_time.setReadOnly(True)
        #     self.ui.entry_end_time.setReadOnly(True)
        #     self.ui.entry_description.setReadOnly(True)

    # TODO: REMOVE
    def browse_video_handler(self):
        # """
        # Handler when the video browse button is clicked
        # """
        # tmp_name, _ = QFileDialog.getOpenFileName(
        #     self, "Choose Video file", self.startDirectory,
        #     "All Files (*)"
        # )
        # if not tmp_name:
        #     return
        # self.set_video_filename(QDir.toNativeSeparators(tmp_name))
        pass

    def _show_error(self, message, title="Error"):
        QMessageBox.warning(self, title, message)





    # Playback Speed/Rate:
    def speed_changed_handler(self, val):
        # print(val)
        self.media_player.set_rate(val)
        # self.media_player.set_rate(self.ui.doubleSpinBoxPlaybackSpeed.value())
        # TODO: Fix playback speed. Print current playback rate (to a label or something, so the user can see).

    def speed_up_handler(self):
        self.modify_rate(0.1)

    def slow_down_handler(self):
        self.modify_rate(-0.1)

    def modify_rate(self, delta):
        new_rate = self.media_player.get_rate() + delta
        if new_rate < 0.2 or new_rate > 6.0:
            return
        self.media_player.set_rate(new_rate)


    # Speed Burst Features:
    def toggle_speed_burst(self):
        curr_is_speed_burst_enabled = self.is_speed_burst_mode_active
        updated_speed_burst_enabled = (not curr_is_speed_burst_enabled)
        if (updated_speed_burst_enabled):
            self.engage_speed_burst()
        else:
            self.disengage_speed_burst()

    # Engages a temporary speed burst 
    def engage_speed_burst(self):
        print("Speed burst enabled!")
        self.is_speed_burst_mode_active = True
        # Set the playback speed temporarily to the burst speed
        self.media_player.set_rate(self.speedBurstPlaybackRate)

        self.ui.toolButton_SpeedBurstEnabled.setEnabled(True)
        self.ui.doubleSpinBoxPlaybackSpeed.setEnabled(False)
        self.ui.button_slow_down.setEnabled(False)
        self.ui.button_speed_up.setEnabled(False)
        
    def disengage_speed_burst(self):
        print("Speed burst disabled!")
        self.is_speed_burst_mode_active = False
        # restore the user specified playback speed
        self.media_player.set_rate(self.ui.doubleSpinBoxPlaybackSpeed.value)

        self.ui.toolButton_SpeedBurstEnabled.setEnabled(False)
        self.ui.doubleSpinBoxPlaybackSpeed.setEnabled(True)
        self.ui.button_slow_down.setEnabled(True)
        self.ui.button_speed_up.setEnabled(True)
