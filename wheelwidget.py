from PyQt5.QtWidgets import QLabel, QGraphicsScene, QGraphicsItemGroup, QApplication, QGraphicsView, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsProxyWidget
from PyQt5.Qt import QColor, QFont, QPointF, QTransform
from PyQt5 import QtTest, QtGui
from PyQt5.QtCore import QRectF, Qt
import math

import sys, random
import textwrap


class WheelScene(QGraphicsScene):
    def __init__(self, radius=200, parent=None, categories=[]):
        super(WheelScene, self).__init__(parent)
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
            print("ellipse rect: %s" % ellipse.rect())

            text.setRotation((((set_angle + subangle)/5760)*360))
            #text.setRotation(30)
            # set_angle+=1
            set_angle += angle
            count1 += 1
            self.addItem(ellipse)
            self.addItem(text)
        self.setSceneRect(0, 0, self.radius*2, self.radius*2)
        print("scenesize= %s" % self.sceneRect())


if __name__ == "__main__":
    # written/taken from  https://www.codesd.com/item/how-to-create-a-pie-chart-with-pyqt-in-python.html
    app = QApplication(sys.argv)
    radius=200
    scene = WheelScene(radius=radius)

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

