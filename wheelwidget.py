from PyQt5.QtWidgets import QLabel, QGraphicsScene, QGraphicsItemGroup, QApplication, QGraphicsView, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsProxyWidget, QWidget
from PyQt5.Qt import QColor, QFont, QPointF, QTransform
from PyQt5 import QtTest, QtGui, QtWidgets, uic
from PyQt5.QtCore import QRectF, QRect, Qt
import math
import sys
import random
import textwrap
import logging
import logs

class ArrowPointer(QLabel):
    def __init__(self, parent=None, imageName: str="Arrow_90_Degrees_Left.png", loglevel=logging.DEBUG):
        super(ArrowPointer, self).__init__(parent)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel
        self.setText("")
        self.setAlignment(Qt.AlignLeft)
        self.setAlignment(Qt.AlignVCenter)
        self.imageName = imageName
        with open(self.imageName, 'rb') as f:
                image_data = f.read()
                self.image = QtGui.QImage.fromData(image_data, self.imageName.split(".")[1].lower())
        self.maximumHeight = self.image.height()
        self.maximumWidth = self.image.width()
        self.setPixmap(QtGui.QPixmap(self.image))

class WheelPhoto(QLabel):
    def __init__(self, parent=None, imageName: str="Wheel_12.png", loglevel=logging.DEBUG):
        super(WheelPhoto, self).__init__(parent)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel

        self.setEnabled(True)
        self.setGeometry(QRect(100, 20, 375, 375))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setText("")
        self.setAlignment(Qt.AlignCenter)
        self.wheel_resting_place = None
        self.rotation_angle = 0
        self.image = None
        self.imageName = imageName
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        with open(self.imageName, 'rb') as f:
            image_data = f.read()
            self.image = QtGui.QImage.fromData(image_data, self.imageName.split(".")[1].lower())
        self.image = self.image.scaledToHeight(self.height())
        self.use_image = self.getRightHalfImage(QtGui.QPixmap(self.image))
        #self.setPixmap(self.use_image)
        # self.setPixmap(QtGui.QPixmap(self.image))
        # self.setPixmap(QtGui.QPixmap(self.image))

        self.setMinimumWidth(self.use_image.width()*1.1)
        self.rotate(360/12/2)

    def getRightHalfImage(self, image: QtGui.QImage) -> QtGui.QImage:
        current = QtGui.QPixmap(image)
        return current.copy(current.width()/2, 0, current.width()/2, current.height())

    def rotate(self, angle: float, offset: int = 0) -> None:
        current_pixel_map = QtGui.QPixmap(self.image)

        rot_angle = ((self.rotation_angle + angle + offset) % 360)
        transform = QtGui.QTransform().rotate(rot_angle)

        transformed_new_pixel_map = current_pixel_map.transformed(transform, Qt.SmoothTransformation)
        xoffset = (transformed_new_pixel_map.width() - current_pixel_map.width())/2
        yoffset = (transformed_new_pixel_map.height() - current_pixel_map.height()) / 2

        #help by goetz from https://forum.qt.io/topic/13421/how-to-rotate-a-content-of-qpixmap-without-changing-size/3
        cropped_obj = transformed_new_pixel_map.copy(xoffset,
                                                     yoffset,
                                                     current_pixel_map.width(),
                                                     current_pixel_map.height()
                                                     )

        self.setPixmap(self.getRightHalfImage(cropped_obj))
        self.rotation_angle = rot_angle

    def getAngle(self):
        return self.rotation_angle

class WheelLabel(QLabel):
    def __init__(self, radius=200, parent=None, categories=[], loglevel=logging.DEBUG):
        super(WheelLabel, self).__init__(parent)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel
        #super(TestWheelScene, self).__init__(parent)
        # self.wheel_gui = QtWidgets.QLabel(self.centralwidget)
        self.setEnabled(True)
        self.setGeometry(QRect(120, 200, 121, 16))
        self.setText("")
        self.setObjectName("wheel_label_1")

class WheelScene(QGraphicsScene):
    def __init__(self, radius=200, parent=None, categories=[], loglevel=logging.DEBUG):
        super(WheelScene, self).__init__(parent)
        self.logger = logs.build_logger(__name__, loglevel)
        self.loglevel = loglevel
        #super(TestWheelScene, self).__init__(parent)
        families = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        if len(categories) == 0:
            sector_names = ["freespin", "bankruptcy", "dogs", "cats",
                        "PC", "OP", "loseturn", "colors", "numbers",
                        "states", "countries", "people"]
        else:
            sector_names = categories
        self.radius = radius
        total = 0
        set_angle = 0
        count1 = 0
        colours = []
        total = sum(families)

        for count in range(len(families)):
            number = []
            for count in range(3):
                number.append(random.randrange(0, 255))
            colours.append(QColor(number[0], number[1], number[2]))

        for i, family in enumerate(families):
            # Max span is 5760, so we have to calculate corresponding span angle
            angle = round(float(family * 5760) / total)
            subangle = round(float((family * 5760) / total/2 ))
            subangle += 120
            # ellipse = QGraphicsEllipseItem(0,0,400,400)
            ellipse = QGraphicsEllipseItem(0, 0, self.radius*2, self.radius*2)
            #ellipse.setPos(QPointF(0, 0))
            # ellipse.setPos(ellipse.boundingRect().center())
            #print(ellipse.rect().center())
            #ellipse.setTransformOriginPoint(200, 200)
            # ellipse.setRect(-200,200,400,400)
            ellipse.setStartAngle(set_angle)
            ellipse.setSpanAngle(angle)
            ellipse.setBrush(colours[count1])
            # https://stackoverflow.com/questions/3312016/text-in-a-qgraphicsscene
            text = QGraphicsTextItem()


            #text.setFont(QFont("Helvetica", 65))
            #text.setTextWidth(20)
            # print("angle=%s, set_angle=%s, sector_name=%s" % (angle, set_angle, sector_names[i]))

            document = QtGui.QTextDocument()
            document.setDocumentMargin(0)
            text.setDocument(document)
            self.font = QFont()
            self.default_font_size = 14
            self.font.setPointSize(self.default_font_size)
            self.font.setBold(True)
            self.font.setFamily("Helvetica")
            self.font.setCapitalization(True)
            text.setPlainText(textwrap.fill(sector_names[i], width=1))
            text.setFont(self.font)

            # print("render_piece label=%s, textangle=%s sub_angle=%s, set_angle=%s, angle=%s" %
            #                         (sector_names[i],
            #                          ((set_angle+subangle)/5760)*360,
            #                          subangle,
            #                          set_angle,
            #                          angle))
            #print("textpos=%s" % ellipse.rect().center())

            reduction_factor = 0
            while text.boundingRect().height() > self.radius-(self.radius*.01):

                # print("category=%s, real_height=%s, radius=%s" % (sector_names[i],
                #                                                   text.boundingRect().height(),
                #                                                   self.radius))
                # print("trying changing reduction factor from %s to %s" % (reduction_factor,
                #                                                           reduction_factor + 1))
                reduction_factor += 1
                self.font.setPointSize(self.default_font_size - reduction_factor)
                text.deleteLater()
                text = None
                text = QGraphicsTextItem()
                text.setDocument(document)
                #text.setFont(QFont("Helvetica", 65- reduction_factor))
                text.setPlainText(textwrap.fill(sector_names[i], width=1))
                text.setFont(self.font)

            text.setZValue(2)

            if sector_names[i] == False:
                #scrap this part for now until we can figure out how to safely offset titles.
                # print("ellipse center=%s" % ellipse.rect().center())
                hypotenuse = self.radius*.01
                degree_subangle = (((set_angle + subangle)/5760)*360)
                degree_subangle += 90
                degree_subangle = degree_subangle % 360
                doTranslate = True
                if doTranslate:
                    #math.cos(degree_subangle) = adjacent/hypotenuse
                    x = math.cos(degree_subangle) * hypotenuse
                    y = math.sin(degree_subangle) * hypotenuse
                    extra = True
                    if extra:
                        if degree_subangle > 0. and degree_subangle < 90.:
                            pass
                        elif degree_subangle > 90 and degree_subangle < 180:
                            pass
                        elif degree_subangle > 180 and degree_subangle < 270:
                            pass
                            #y = -y
                        elif degree_subangle > 270:
                            pass
                    target = ellipse.rect().center()
                    target.setX(x + target.x())
                    target.setY(y + target.y())
                    # print("target=%s" % target)
                    print("do_move_text_offset cat=%s, offset=%s degree_subangle=%s, x=%s, y=%s" % (
                                                sector_names[i],
                                        target,
                        degree_subangle,
                        x,
                        y
                    ))
                    text.setPos(target)
                else:
                    text.setPos(ellipse.rect().center())
            text.setPos(ellipse.rect().center())
            self.logger.debug("ellipse rect: %s" % ellipse.rect())

            text.setRotation((((set_angle + subangle)/5760)*360))
            #text.setRotation(30)
            # set_angle+=1
            set_angle += angle
            count1 += 1
            self.addItem(ellipse)
            self.addItem(text)
        self.setSceneRect(0, 0, self.radius*2, self.radius*2)
        self.logger.debug("scenesize= %s" % self.sceneRect())


if __name__ == "__main__":
    # written/taken from  https://www.codesd.com/item/how-to-create-a-pie-chart-with-pyqt-in-python.html
    app = QApplication(sys.argv)
    radius=200
    scene = WheelScene(radius=radius)
    wheel = WheelPhoto()
    wheel.show()
    wheel.spinWheel(7)
    wheel_label = WheelLabel()
    wheel_label.show()
    view = QGraphicsView(scene)
    view.setStyleSheet("background: transparent")
    view.setSceneRect(0,0,radius*2,radius*2)
    group = scene.createItemGroup(scene.items())
    print("view: sceneRect=%s" %view.sceneRect())
    #print("view: rect=%s" %view.cen)
    view.show()

    i = 0
    while True:
        transform = QTransform()
        offset = group.boundingRect().center()
        transform.translate(offset.x(), offset.y())
        transform.rotate(i)
        transform.translate(-offset.x(), -offset.y())
        group.setTransform(transform)
        view.transform()
        QtTest.QTest.qWait(50)
        i += 1
    app.exec_()
