#!/usr/bin/python
# coding: UTF-8

from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import pyqtgraph as pg
import signal
import Queue
import sys
import time
import threading


class RobotItem(QtGui.QGraphicsItem):
    """a sample robot item"""
    def __init__(self):
        super(RobotItem, self).__init__()
        #self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setCacheMode(QtGui.QGraphicsItem.DeviceCoordinateCache)
        self.setZValue(1)

    def boundingRect(self):
        adjust = 2.0
        return QtCore.QRectF(-10 - adjust, -10 - adjust, 20 + adjust,
                20 + adjust)

    def paint(self, painter, option, widget):
        #Draw a sample robot
        pen = QtGui.QPen()
        pen.setWidth(1);
        pen.setBrush(QtCore.Qt.blue)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawEllipse(QtCore.QPointF(0.0, 0.0), 5, 5)
        painter.drawLine(0, 0, 5, 0)


class LSLAMGUI(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.q = Queue.Queue()

    def run(self):
        #Create qtwindow
        app = QtGui.QApplication([])
        w = pg.GraphicsWindow()
        w.show()
        w.resize(800,800)
        w.setWindowTitle("viewer")
        #Create ViewBox
        vb = w.addViewBox()
        ## lock the aspect ratio
        vb.setAspectLocked(True)
        ## Set initial view bounds
        vb.setRange(QtCore.QRectF(0, 0, 400, 400))

        #Create ImageItem for map
        self.img = pg.ImageItem(np.zeros((400,400)))
        vb.addItem(self.img)

        ## Set image level
        self.img.setLevels([0, 1])

        #Create ScatterPlotItem for scan data 
        self.sct = pg.ScatterPlotItem(pen = pg.mkPen(None), 
                                      brush = pg.mkBrush("g"), 
                                      size =5, 
                                      antialias = False)
        self.sct.setParentItem(self.img)

        #Create RobotItem(custom) for showing robot pose 
        self.robot = RobotItem()
        self.robot.setParentItem(self.img)

        #Set timer
        timer = pg.QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(30)

        import sys
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()
              
    def update(self):
        try:
            #remove previous laser scan data
            self.sct.clear()
            #Check is there any new data in queue
            data, pose, newscan = self.q.get(block=False)
            self.q.queue.clear()
            #update map
            I = np.zeros(data.shape)
            I.fill(1)
            self.img.setImage(I - data)
            #update robot pose
            self.robot.setRotation(180.*pose[2]/np.pi)
            self.robot.setPos(pose[0],pose[1])
            #update laser scan
            #spots = [{'pos': pos} for pos in newscan]
            spots = [{'pos': list(newscan[i,:])} for i in range(newscan.shape[0])]
            self.sct.addPoints(spots)
        except Queue.Empty:
            pass

    def setdata(self, mapdata, robotpose, newscan):
        self.q.put( (mapdata,robotpose, newscan) )
        pass

if __name__ == "__main__":
    gui = LSLAMGUI()
    gui.start()
    print 'sample gui test'
    for i in range(1000):
        time.sleep(0.1)
        newscan = np.zeros((10,2))
        newscan.fill(0.1)
        gui.setdata(np.random.rand(400,400), [0,0,i], newscan)

    
