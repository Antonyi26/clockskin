import os
import sys
import xml.dom.minidom
from datetime import datetime, date
from PySide2.QtCore    import Qt, QPoint, QPointF, QRect, QTimer, QSize
from PySide2.QtWidgets import QApplication, QWidget, QMainWindow
from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout
from PySide2.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem
from PySide2.QtWidgets import QPushButton
from PySide2.QtGui     import QPixmap, QPen, QBrush

# ==============================================================================

CurrentDir = os.path.dirname(os.path.abspath(__file__))

# ==============================================================================

class DrawableItem(QGraphicsItem):
    # --------------------------------------------------------------------------
    def __init__(self, **d):
        super().__init__()
        self.file = d['file']

        if self.file.endswith('.png'):
            self.imgs = [QPixmap(self.file)]
        elif self.file.endswith('.xml'):
            doc = xml.dom.minidom.parse(self.file)
            drawablesNode = doc.documentElement
            imageNodes = [node for node in drawablesNode.childNodes if node.nodeName == 'image']
            self.imgs = [QPixmap(node.firstChild.nodeValue) for node in imageNodes]
        
        self.size = QSize(
            max(map(lambda img: img.rect().width(), self.imgs)), 
            max(map(lambda img: img.rect().height(), self.imgs))
        )

        self.arrayType = int(d.get('arraytype', 0))
        self.rotate = int(d.get('rotate', 0))
        self.mulrotate = int(d.get('mulrotate', 1))
        center = QPoint(int(d.get('centerX', 0)), int(d.get('centerY', 0)))
        r = self.boundingRect()
        self.setPos(center - r.center())
        self.setTransformOriginPoint(r.center())
        #  self.mousePressed = False

        if 'centerX' in d and 'centerY' in d:
            self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
    # --------------------------------------------------------------------------
    def getImgForDraw(self):
        res = []
        if self.file.endswith('.png'):
            res +=  self.imgs
        elif self.file.endswith('.xml'):
            if self.arrayType == 1:
                res += [self.imgs[int(i)] for i in str(datetime.now().year)]
                res += [self.imgs[-1]]
                res += [self.imgs[int(i)] for i in '{:02}'.format(datetime.now().month)]
                res += [self.imgs[-1]]
                res += [self.imgs[int(i)] for i in '{:02}'.format(datetime.now().day)]
            elif self.arrayType == 2:
                res += [self.imgs[int(i)] for i in '{:02}'.format(datetime.now().month)]
                res += [self.imgs[-1]]
                res += [self.imgs[int(i)] for i in '{:02}'.format(datetime.now().day)]                
            elif self.arrayType == 3: 
                ind = datetime.now().month - 1        # month
                res += [self.imgs[ind]]
            elif self.arrayType == 4:                 # date
                res += [self.imgs[int(i)] for i in '{:02}'.format(datetime.now().day)]
            elif self.arrayType == 5: 
                ind = (date.today().weekday() + 1) % 7      # week
                res += [self.imgs[ind]]
            elif self.arrayType == 6:        # time hh:mm
                res += [self.imgs[int(i)] for i in '{:02}'.format(datetime.now().hour)]
                res += [self.imgs[-1]]
                res += [self.imgs[int(i)] for i in '{:02}'.format(datetime.now().minute)]
            elif self.arrayType == 7:         # hours
                res += [self.imgs[int(i)] for i in '{:02}'.format(datetime.now().hour)]
            elif self.arrayType == 8:        # minute
                res += [self.imgs[int(i)] for i in '{:02}'.format(datetime.now().minute)]
            elif self.arrayType == 9:         # second
                res += [self.imgs[int(i)] for i in '{:02}'.format(datetime.now().second)]
            elif self.arrayType == 11:      # temperature
                t = 23
                if t < 0: res += [self.imgs[-2]]
                res += [self.imgs[int(i)] for i in '{:02}'.format(abs(t))]
                res += [self.imgs[-1]]
            elif self.arrayType == 12:      # steps
                res += [self.imgs[int(i)] for i in '{:05}'.format(234)]
                res += [self.imgs[-1]]                
            elif self.arrayType == 13:      # head rate
                res += [self.imgs[int(i)] for i in '{:03}'.format(63)]
            elif self.arrayType == 14:      # power
                res += [self.imgs[int(i)] for i in '98']
                res += [self.imgs[-1]]
            elif self.arrayType == 16:         # years
                res += [self.imgs[int(i)] for i in str(datetime.now().year)]
            else:
                res += [self.imgs[0]]
        return res
    # --------------------------------------------------------------------------
    def boundingRect(self):
        w = self.size.width() * len(self.getImgForDraw())
        return QRect(0, 0, w, self.size.height())
    # --------------------------------------------------------------------------
    def paint(self, painter, styleOptionGraphicsItem, widget):
        if self.rotate in (1, 7, 8):
            k = 12 if self.rotate == 1 else 24
            hours = datetime.now().hour % k + datetime.now().minute / 60
            self.setRotation(self.mulrotate * 360 // k * hours)            
        elif self.rotate in (2, 9):
            minutes = datetime.now().minute + datetime.now().second / 60
            self.setRotation(self.mulrotate * 6 * minutes)
        elif self.rotate in (3, 10):
            seconds = datetime.now().second + datetime.now().microsecond / 1000000
            self.setRotation(self.mulrotate * 6 * seconds)

        for i, img in enumerate(self.getImgForDraw()):
            if self.arrayType == 6 and img is self.imgs[-1]:
                if datetime.now().second % 2 == 0:
                    painter.drawPixmap(self.size.width() * i, 0, img)
            else:
                painter.drawPixmap(self.size.width() * i, 0, img.scaled(self.size, Qt.IgnoreAspectRatio))
                # painter.drawPixmap(self.size.width() * i, 0, img)
        
        if self.isSelected():
            r = self.boundingRect()
            painter.setPen(QPen(QBrush(Qt.yellow), 1, Qt.DashLine))
            painter.drawRect(r)         
            p1 = QPoint(r.left(), r.center().y())
            p2 = QPoint(r.right(), r.center().y())
            painter.drawLine(p1, p2)
            p1 = QPoint(r.center().x(), r.top())
            p2 = QPoint(r.center().x(), r.bottom())
            painter.drawLine(p1, p2)  

# ==============================================================================

class ClockSkinWidget(QGraphicsView):
    # --------------------------------------------------------------------------
    def __init__(self):
        super().__init__()
        self._scene = QGraphicsScene()
        self._scene.setSceneRect(QRect(-320, -240, 640, 480))
        self.setScene(self._scene)
        self.updateTimer = QTimer()
        self.updateTimer.timeout.connect(lambda: self.scene().update())
        self.xml = None
        # self.updateTimer.timeout.connect(self.refresh)
        self.updateTimer.start(1000//30)
    # --------------------------------------------------------------------------
    def setDir(self, _dir):
        if os.getcwd() != CurrentDir:
            os.chdir('..')
        os.chdir(_dir)
        self.xml = xml.dom.minidom.parse('clock_skin.xml')
        self.refresh()
    # --------------------------------------------------------------------------
    def refresh(self):
        self.scene().clear()
        self.create()        
    # --------------------------------------------------------------------------
    def save(self):
        pass
    # --------------------------------------------------------------------------
    def create(self):
        for drawable in [node for node in self.xml.documentElement.childNodes if node.nodeName == 'drawable']:
            elements = [node for node in drawable.childNodes if node.nodeType == node.ELEMENT_NODE]
            d = dict([(node.nodeName, node.firstChild.nodeValue) for node in elements])
            if 'name' in d:
                d['file'] = d['name']
                self.scene().addItem(DrawableItem(**d))

# ==============================================================================

if __name__ == '__main__':
    title = 'Clock skin'
    # делаем текущую директорию рабочей
    os.chdir(CurrentDir)

    app = QApplication([])

    clockSkinWidget = ClockSkinWidget()
    refreshBtn = QPushButton('Обновить')
    refreshBtn.pressed.connect(clockSkinWidget.refresh)
    saveBtn = QPushButton('Сохранить')
    saveBtn.pressed.connect(clockSkinWidget.save)
    btnLayout = QHBoxLayout()
    btnLayout.addWidget(refreshBtn)
    btnLayout.addWidget(saveBtn)

    mainLayout = QVBoxLayout()
    mainLayout.addWidget(clockSkinWidget)
    mainLayout.addLayout(btnLayout)
    mainLayout.setAlignment(clockSkinWidget, Qt.AlignCenter)
    mainLayout.setContentsMargins(0, 0, 0, 0)
    centralWidget = QWidget()
    centralWidget.setLayout(mainLayout)

    MainWindow = QMainWindow()
    skinsMenu = MainWindow.menuBar().addMenu('Skins')
    skinsMenu.triggered.connect(
        lambda action: [
            clockSkinWidget.setDir(action.text()), 
            MainWindow.setWindowTitle(f'{title} - {action.text()}')
        ]
    )
    [skinsMenu.addAction(_dir.name) for _dir in os.scandir() if _dir.is_dir()]
    MainWindow.setWindowTitle(title)
    MainWindow.setCentralWidget(centralWidget)
    MainWindow.show()

    sys.exit(app.exec_())
