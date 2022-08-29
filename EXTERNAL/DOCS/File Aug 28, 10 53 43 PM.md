✴️9️⃣📚 PyQt Timeline References:

# Multitasking in PyQt5 (Keep 01-07-2020)
https://doc.qt.io/archives/qq/qq27-responsive-guis.html#solvingaproblemstepbystep
https://stackoverflow.com/questions/46511239/pyqt-qthreadpool-with-qrunnables-taking-time-to-quit
https://stackoverflow.com/questions/45157006/python-pyqt-pulsing-progress-bar-with-multithreading

Example:
https://www.walletfox.com/course/qrunnableexample.php



# Packaging PyQt5 Apps (Keep 01-07-2020)
https://www.learnpyqt.com/courses/packaging-and-distribution/packaging-pyqt5-apps-fbs/

https://hackernoon.com/the-one-stop-guide-to-easy-cross-platform-python-freezing-part-1-c53e66556a0a

https://docs.python-guide.org/shipping/freezing/


# PyQt5 Video Player GUI (Keep 11-06-2019)
https://pythonprogramminglanguage.com/pyqt5-video-widget/
https://stackoverflow.com/questions/53321617/pyqt5-open-qmediaplayer-in-new-window-and-play-video

Errors:
https://github.com/ContinuumIO/anaconda-issues/issues/138
https://github.com/ContinuumIO/anaconda-issues/issues/1394
https://stackoverflow.com/questions/42497689/importerror-pyqt5-anaconda

# Python Timeline Tracks (Keep 11-06-2019):
https://github.com/dsgou/annotator
https://stackoverflow.com/questions/47858801/create-a-timeline-with-pyqt5


PyQtGraph
http://www.pyqtgraph.org/documentation/widgets/progressdialog.html

# Qt5 Scrollable Areas (Keep 11-08-2019):
https://www.qtcentre.org/threads/29289-paint-in-the-viewport-of-a-scrollarea
- recommends implementing a QAbstractScrollArea instead of widgets for each event, and drawing there.
https://doc.qt.io/qt-5/qabstractscrollarea.html#details
https://stackoverflow.com/questions/52867354/possible-rendering-issue-with-qscrollarea-and-qpainter

// SOLVED: In the embedded widget's paint function, use self.rect() instead of event.rect().

Custom Widget in QScrollArea Redrawing on Scroll (Keep 01-07-2019)
https://stackoverflow.com/questions/52460376/custom-widget-in-qscrollarea-badly-redrawing-only-on-scroll/52461619#52461619

https://stackoverflow.com/questions/52867354/possible-rendering-issue-with-qscrollarea-and-qpainter


https://eli.thegreenplace.net/2011/04/25/passing-extra-arguments-to-pyqt-slot


Python "wrapper-class" helpers (Keep 11-27-2019)
```python
def __getattr__(self, name):
    if name in {"x", "y", "distance_to_origin"}:
        return getattr(self._point, name)
def __setattr__(self, name, value):
    if name in {"x", "y"}:
        setattr(self._point, name, value)
    else:
        super().__setattr__(name, value)
```

# Set image on QPushButton (Keep 12-18-2019)
https://stackoverflow.com/questions/3137805/how-to-set-image-on-qpushbutton

# PyQt5 Progress Bars: (Keep 12-17-2019)
https://riptutorial.com/pyqt5/example/29500/basic-pyqt-progress-bar
https://stackoverflow.com/questions/19442443/busy-indication-with-pyqt-progress-bar
https://learndataanalysis.org/create-a-simple-progress-bar-with-pyqt5-in-python/
https://learndataanalysis.org/learn-how-to-create-a-progress-bar-widget-for-beginners-pyqt5-tutorial/
https://pythonprogramming.net/progress-bar-pyqt-tutorial/


# PyQT5 Draw a Vertical Label (unsolved) (Keep 11-07-2019)
https://stackoverflow.com/questions/34080798/pyqt-draw-a-vertical-label
https://stackoverflow.com/questions/3757246/pyqt-rotate-a-qlabel-so-that-its-positioned-diagonally-instead-of-horizontally
https://stackoverflow.com/questions/7339685/how-to-rotate-a-qpushbutton

http://zetcode.com/gui/pyqt5/painting/
https://stackoverflow.com/questions/47621360/placing-a-text-with-coordinates-with-drawtext


# Properly Resizing QTMediaPlayer (Keep 03-29-2019)
https://www.qtcentre.org/threads/53656-QGraphicsGridLayout-amp-QGraphicsLayoutItem-boundingRect-struggles

https://forum.qt.io/topic/21499/qt5-with-qmediaplayer-and-qvideowidget/4


# Problems with QTMultimedia on Windows: (Keep 04-01-2019)
Problems with QTMultimedia on Windows:
"DirectShowPlayerService::doRender: Unresolved error code 0x80040266 (IDispatch error #102)"

https://forum.qt.io/topic/57675/which-file-formats-or-codecs-does-qmediaplayer-support

QMediaPlayer fails to play some fomats (mp4/mkv):
https://bugreports.qt.io/browse/QTBUG-51692

QMediaPlayer should select its backend depending on the media played:
https://bugreports.qt.io/browse/QTBUG-32783


Windows Direct Show Plugins:
http://www.gdcl.co.uk/mpeg4/
https://1f0.de/lav-splitter/
https://github.com/cisco/openh264/releases

