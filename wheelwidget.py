from PyQt5.QtWidgets import QGraphicsScene, QGraphicsItemGroup, QApplication, QGraphicsView, QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsProxyWidget
from PyQt5.Qt import QColor, QFont, QPointF, QTransform
from PyQt5 import QtTest
from PyQt5.QtCore import QRectF

import sys, random


class TestWheel(QGraphicsEllipseItem):
    def __init__(self, w, x, y, z):
        super(TestWheel, self).__init__(w, x, y, z, parent=None)

    def boundingRect(self) -> QRectF:
        return QRectF(-1.*(self.rect().width()/2.),
                      -1.*(self.rect().height()/2.),
                      self.rect().width(),
                      self.rect().height())

class TestWheelScene(QGraphicsScene):
    def __init__(self, parent=None):
        super(TestWheelScene, self).__init__(parent)
        families = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        sector_names = ["freespin", "bankruptcy", "dogs", "cats",
                        "PC", "OP", "loseturn", "colors", "numbers",
                        "states", "countries", "people"]

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
            # ellipse = QGraphicsEllipseItem(0,0,400,400)
            ellipse = QGraphicsEllipseItem(0, 0, 400.0, 400.0)
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
            font = QFont()
            font.setPointSize(10)
            font.setBold(True)
            font.setWeight(101)
            text.setFont(font)
            text.setTextWidth(20)
            # print("angle=%s, set_angle=%s, sector_name=%s" % (angle, set_angle, sector_names[i]))
            text.setPlainText(sector_names[i])
            text.setRotation((set_angle/5760)*360)
            text.setPos(195,150)
            # set_angle+=1
            set_angle += angle
            count1 += 1
            self.addItem(ellipse)
            self.addItem(text)
        self.setSceneRect(0, 0, 400, 400)
        print("scenesize= %s" % self.sceneRect())


# written/taken from  https://www.codesd.com/item/how-to-create-a-pie-chart-with-pyqt-in-python.html
app = QApplication(sys.argv)
scene = TestWheelScene()

view = QGraphicsView(scene)
view.setSceneRect(0,0,400,400)
group = scene.createItemGroup(scene.items())
print("view: sceneRect=%s" %view.sceneRect())
#print("view: rect=%s" %view.cen)
view.show()


i = 0
while True:
    transform = QTransform()
    offset = group.boundingRect().center()
    # print("group.sceneBoundingRect()=%s" % group.sceneBoundingRect())
    # print("offset=%s" % offset)
    transform.translate(offset.x(), offset.y())
    transform.rotate(i)
    transform.translate(-offset.x(), -offset.y())
    group.setTransform(transform)
    #scene.destroyItemGroup(group)
    scene.update()
    view.transform()
    QtTest.QTest.qWait(10)
    i += 5
app.exec_()

