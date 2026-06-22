from PySide6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QGraphicsTextItem
)

from PySide6.QtGui import (
    QPixmap,
    QPen,
    QColor,
    QFont,
    QPainter,
    QImage
)

from PySide6.QtCore import Qt


class ImageViewer(QGraphicsView):

    def __init__(self):

        super().__init__()

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.main_window = None
        self.selected_region_id = None

        self.setDragMode(
            QGraphicsView.ScrollHandDrag
        )
        # text rendering settings (can be modified from main window)
        self.text_font_family = "Arial"
        self.text_font_size = 20
        self.text_color = QColor(0, 0, 255)


    def load_image(self, image_path):

        self.scene.clear()

        pixmap = QPixmap(image_path)

        pix_item = self.scene.addPixmap(
            pixmap
        )
        pix_item.setZValue(-10.0)

        self.setSceneRect(
            self.scene.itemsBoundingRect()
        )

        # fit image to width
        self.fitInView(
            self.scene.itemsBoundingRect(),
            Qt.KeepAspectRatio
        )

    def wheelEvent(self, event):

        factor = 1.15

        if event.angleDelta().y() > 0:

            self.scale(
                factor,
                factor
            )

        else:

            self.scale(
                1 / factor,
                1 / factor
            )

    def draw_regions(self, regions):

        self.rect_items = []
        for region in regions:

            polygon = region.polygon

            xs = [p[0] for p in polygon]
            ys = [p[1] for p in polygon]

            x = min(xs)
            y = min(ys)

            w = max(xs) - x
            h = max(ys) - y

            rect = OCRRect(
                self,
                region,
                x,
                y,
                w,
                h
            )
            rect.setZValue(0.0)
            self.scene.addItem(rect)
            self.rect_items.append(rect)

    def region_selected(self, region):

        if self.main_window:

            self.main_window.select_region(
                region
            )

    def render_translations(self, regions):
        """Draw translated text overlays for enabled regions."""
        for region in regions:
            if not region.enabled or not region.translation:
                continue

            polygon = region.polygon
            xs = [p[0] for p in polygon]
            ys = [p[1] for p in polygon]
            x = min(xs)
            y = min(ys)
            w = max(xs) - x
            h = max(ys) - y

            if region.render_bg:
                bg = QGraphicsRectItem(
                    x,
                    y,
                    w,
                    h
                )

                bg.setBrush(
                    QColor(
                        255,
                        255,
                        255
                    )
                )

                bg.setPen(
                    QPen(
                        Qt.NoPen
                    )
                )

                # Let mouse events pass through bg so underlying OCRRect remains clickable
                try:
                    bg.setAcceptedMouseButtons(Qt.NoButton)
                except Exception:
                    pass

                bg.setZValue(1.0)
                self.scene.addItem(bg)

            text_item = QGraphicsTextItem(
                region.translation
            )

            text_item.setFont(
                QFont(self.text_font_family, int(self.text_font_size))
            )
            text_item.setTextWidth(max(1, w - 8))
            text_item.setDefaultTextColor(self.text_color)

            rect = text_item.boundingRect()
            text_x = x + max(0, (w - rect.width()) / 2)
            text_y = y + max(0, (h - rect.height()) / 2)
            text_item.setPos(
                text_x,
                text_y
            )

            text_item.setZValue(2.0)
            self.scene.addItem(
                text_item
            )

            # make text not accept mouse so clicks go to underlying items
            try:
                text_item.setAcceptedMouseButtons(Qt.NoButton)
            except Exception:
                pass


    def save_image(self, path):

        rect = self.scene.sceneRect()

        image = QImage(
            int(rect.width()),
            int(rect.height()),
            QImage.Format_ARGB32
        )

        image.fill(Qt.white)

        painter = QPainter(image)

        self.scene.render(
            painter
        )

        painter.end()

        image.save(path)


class OCRRect(QGraphicsRectItem):

    def __init__(
        self,
        viewer,
        region,
        x,
        y,
        w,
        h
    ):

        super().__init__(
            x,
            y,
            w,
            h
        )

        self.viewer = viewer
        self.region = region
        self.setBrush(Qt.NoBrush)
        self.update_color()

    def mousePressEvent(self, event):

        if event.button() == Qt.RightButton:

            self.region.enabled = (
                not self.region.enabled
            )

            self.update_color()

            if self.viewer.main_window:
                self.viewer.main_window.refresh_region_list()
            event.accept()
            return

        self.viewer.region_selected(
            self.region
        )

        event.accept()

    def update_color(self):

        if not self.region.render_outline:
            self.setPen(QPen(Qt.NoPen))
            return

        color = QColor(self.region.outline_color)
        width = 3 if self.viewer.selected_region_id == self.region.id else 2
        style = Qt.SolidLine if self.region.enabled else Qt.DashLine

        pen = QPen(color, width, style)
        self.setPen(pen)

