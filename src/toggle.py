from PySide2.QtCore import Qt, QPoint, QPointF, QSize, QRectF
from PySide2.QtWidgets import QCheckBox
from PySide2.QtGui import QPen, QPaintEvent, QBrush, QColor, QPainter


class Toggle(QCheckBox):

    _transparent_pen = QPen(Qt.transparent)
    _light_grey_pen = QPen(Qt.lightGray)

    def __init__(self, parent=None, width=65, height=30, bar_color=Qt.gray, checked_color="#48A23F", handle_color=Qt.white):
        super(Toggle, self).__init__()

        self._width = width
        self._height = height

        self._bar_brush = QBrush(bar_color)
        # Можно использовать QColor(checked_color).lighter()
        self._bar_checked_brush = QBrush(QColor(checked_color))

        self._handle_brush = QBrush(handle_color)
        self._handle_checked_brush = QBrush(QColor(checked_color))

        self._handle_position = 0

        self.stateChanged.connect(self.handle_state_change)

    def sizeHint(self):
        return QSize(self._width, self._height)

    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    def paintEvent(self, e: QPaintEvent):
        '''Метод, вызываемый при переключении'''
        contRect = self.contentsRect()
        handleRadius = round(0.35 * contRect.height())

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(self._transparent_pen)
        # Задать размер прямоугольника
        barRect = QRectF(
            0, 0,
            contRect.width() - handleRadius, 0.9 * contRect.height()
        )  # Коэффициент высоты "направляющей" (по дефолту  0.40)
        barRect.moveCenter(contRect.center())
        rounding = barRect.height() / 2

        # Расстояние между позициями ручки
        trailLength = contRect.width() - 4 * handleRadius
        xPos = contRect.x() + 2 * handleRadius + trailLength * self._handle_position

        if self.isChecked():
            p.setBrush(self._bar_checked_brush)
            # Нарисовать прямоугольник со скругленными высотами
            p.drawRoundedRect(barRect, rounding, rounding)
            # Нарисовать ручку
            p.setPen(QPen("#48A23F"))  # Линия ручки
            p.setBrush(self._handle_brush)  # Заливка ручки

        else:
            p.setBrush(self._bar_brush)
            # Нарисовать прямоугольник со скругленными высотами
            p.drawRoundedRect(barRect, rounding, rounding)
            # Нарисовать ручку
            p.setPen(self._light_grey_pen)  # Линия ручки
            p.setBrush(self._handle_brush)  # Заливка ручки

        # Нарисовать ручку (круг)
        p.drawEllipse(QPointF(xPos, barRect.center().y()), handleRadius, handleRadius)

        p.end()

    def handle_state_change(self, value):
        self._handle_position = 1 if value else 0
