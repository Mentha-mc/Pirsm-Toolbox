import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,QGraphicsBlurEffect
from PyQt6.QtGui import QPainter, QBrush, QColor,QIcon,QPolygonF
from PyQt6.QtCore import Qt, QRectF, QPropertyAnimation, QEasingCurve,QRect,QPointF
class BlurredLabel(QLabel):
    def __init__(self, parent=None,items=[]):
        super().__init__(parent)
        self.setGeometry(0,0,parent.width(),parent.height())
        for item in items:
            type=item.get('type',11)
            color=item.get('color','red')
            last_time=item.get('last_time',3)
            shape=item.get('shape',1)
            # beisaier=item.get('beisaier',)
            MoveLabel(self,type=type,color=color,last_time=last_time,shape=shape)
        print(parent.size())
        print(self.size())

        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(300)
        self.setGraphicsEffect(blur_effect)
class MoveLabel(QLabel):
    def __init__(self, parent=None, type=11, shape=0, color='blue', last_time=5):
        super().__init__(parent)
        self.type = type  # 添加这行代码来保存 type 为实例变量
        self.shape = shape
        self.last_time = last_time
        self.color = color
        self.side_width = min(parent.width(), parent.height()) // 2
        self.setGeometry(0, 0, self.side_width, self.side_width)
        self.init_positions()
        self.animation = QPropertyAnimation(self, b'geometry')
        self.animation.finished.connect(self.toggleAnimation)
        self.startAnimation()

    def init_positions(self):
        # 由于 type 现在是实例变量，我们可以直接使用 self.type
        if self.type in (11, 12):
            self.start_rect = QRectF(0, 0, self.width(), self.height())
            self.end_rect = QRectF(self.parent().width() - self.side_width, self.parent().height() - self.side_width, self.side_width, self.side_width)
        elif self.type in (21, 22):
            self.start_rect = QRectF((self.parent().width() - self.side_width) // 2, 0, self.side_width, self.side_width)
            self.end_rect = QRectF((self.parent().width() - self.side_width) // 2, self.parent().height() - self.side_width, self.side_width, self.side_width)
        elif self.type in (31, 32):
            self.start_rect = QRectF(self.parent().width() - self.side_width, 0, self.side_width, self.side_width)
            self.end_rect = QRectF(0, self.parent().height() - self.side_width, self.side_width, self.side_width)
        elif self.type in (41, 42):
            self.start_rect = QRectF(self.parent().width() - self.side_width, (self.parent().height() - self.side_width) // 2, self.side_width, self.side_width)
            self.end_rect = QRectF(0, (self.parent().height() - self.side_width) // 2, self.side_width, self.side_width)

    # 其他方法保持不变...
        self.animation = QPropertyAnimation(self, b'geometry')
        self.animation.finished.connect(self.toggleAnimation)
        self.startAnimation()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.shape==1:
            # 计算圆的位置
            rect = self.rect().adjusted(1, 1, -1, -1)
            # 设置刷子
            brush = QBrush(QColor(self.color))  # 刷子颜色为半透明红色
            painter.setBrush(brush)
            # 绘制圆
            painter.drawEllipse(rect)
        elif self.shape==2:
            painter.fillRect(0, 0, self.side_width, self.side_width, QColor(self.color))  # 使用红色填充正方形
        elif self.shape==3:
            # 计算三角形的顶点坐标
            p1 = QPointF(self.width() / 2, (self.height() - self.side_width * 0.866) / 2)  # 0.866 为 sqrt(3)/2，即等边三角形的高度
            p2 = QPointF((self.width() - self.side_width) / 2, (self.height() + self.side_width * 0.866) / 2)
            p3 = QPointF((self.width() + self.side_width) / 2, (self.height() + self.side_width * 0.866) / 2)

            triangle = QPolygonF([p1, p2, p3])

            painter.setBrush(QBrush(QColor(0, 0, 255)))  # 使用蓝色填充三角形
            painter.drawPolygon(triangle)
    def toggleAnimation(self):
        # 切换动画的起始值和结束值
        a,b=self.animation.startValue(),self.animation.endValue()
        a,b=b,a
        self.animation.setStartValue(a)
        self.animation.setEndValue(b)
        self.animation.start()
    def startAnimation(self):
        self.animation.setStartValue(self.start_rect)
        self.animation.setEndValue(self.end_rect)
        self.animation.setDuration(self.last_time*1000)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)  # 设置缓动曲线
        self.animation.start()
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300,100,800,600)
        self.initUI()
    def initUI(self):
        self.setWindowIcon(QIcon('./logo.svg'))
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        # f, parent = None, type = 11, shape = 0, color = 'blue', last_time = 5, beisaier = None):
        shapes=[
            {"type":11,"shape":1,"color":"#7098da","last_time":6},
            {"type":21,"shape":3,"color":"#6eb6ff","last_time":5},
            {"type":31,"shape":1,"color":"#90f2ff","last_time":7},
            {"type":41,"shape":2,"color":"#e0fcff","last_time":8},
            {"type":12,"shape":1,"color":"#0000FF","last_time":9},
            {"type":22,"shape":1,"color":"#00FFFF","last_time":4}
        ]
        label = BlurredLabel(self,shapes)
        layout.addWidget(label)

        self.setCentralWidget(central_widget)
        self.setWindowTitle('磨砂动态背景')
        label_=QLabel('',self)
        label_.adjustSize()  # 调整标签大小以适应内容
        # label_.setWordWrap(True)
def main():
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
if __name__ == '__main__':
    main()