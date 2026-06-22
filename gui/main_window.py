from gui.image_viewer import ImageViewer
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QPushButton,
    QFileDialog,
    QTextEdit,
    QLabel,
    QListWidget,
    QListView,
    QAbstractItemView,
    QListWidgetItem,
    QComboBox,
    QSpinBox,
    QColorDialog,
    QProgressBar,
    QApplication
)
import copy
import json
import os
import zipfile
import tempfile
import shutil

from PySide6.QtCore import Qt
from PySide6.QtGui import QShortcut, QKeySequence, QPixmap, QIcon, QFontDatabase, QFont

from models.region import Region
from services.detector import TextDetector
from services.translator import Translator


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Comic Translator MVP")
        self.resize(1000, 700)

        self.image_path = None

        self.detector = TextDetector()
        self.translator = Translator()

        self.btn_open = QPushButton("Open Image")
        self.btn_open_cbz = QPushButton("Open CBZ")
        self.btn_detect = QPushButton("Detect")
        self.ocr_text = QTextEdit()

        self.translated_text = QTextEdit()
        self.region_list = QListWidget()
        self.region_list.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )
        self.btn_save_text = QPushButton(
            "Save Text"
        )
        self.btn_save_translation = QPushButton(
            "Save Translation"
        )
        self.btn_save_page = QPushButton(
            "Save Page"
        )
        self.btn_load_page = QPushButton(
            "Load Page"
        )
        self.btn_save_project = QPushButton(
            "Save Project"
        )
        self.btn_load_project = QPushButton(
            "Load Project"
        )
        self.btn_undo = QPushButton(
            "Undo"
        )
        self.btn_merge = QPushButton(
            "Merge Selected"
        )
        self.font_combo = QComboBox()
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(20)
        self.asset_font_map = {}
        self.color_btn = QPushButton("Text Color")
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(24, 16)
        self.color_preview.setStyleSheet("background: rgb(0,0,255);")
        self.btn_clear_render = QPushButton("Clear Render")
        self.btn_clear_all_render = QPushButton("Clear All Render")
        self.btn_translate = QPushButton(
            "Translate"
        )
        self.btn_translate_all = QPushButton(
            "Translate All"
        )
        self.btn_render = QPushButton(
            "Render"
        )
        self.btn_save_cbz = QPushButton(
            "Save CBZ"
        )
        self.lbl_status = QLabel(
            "Ready"
        )

        shortcut = QShortcut(
            QKeySequence("Delete"),
            self
        )

        shortcut.activated.connect(
            self.disable_selected
        )

        self.image_viewer = ImageViewer()
        self.image_viewer.main_window = self
        self.image_viewer.selected_region_id = None
        self.load_asset_fonts()
        # thumbnail list for CBZ pages
        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setViewMode(QListView.IconMode)
        self.thumbnail_list.setIconSize(self.image_viewer.size())
        self.thumbnail_list.setMaximumWidth(180)
        self.thumbnail_list.setResizeMode(QListView.Adjust)
        self.thumbnail_list.itemClicked.connect(self.on_thumbnail_clicked)
        self.cbz_progress = QProgressBar()
        self.cbz_progress.setVisible(False)
        self.cbz_progress.setTextVisible(True)
        # page selector (created early so layout can reference it)
        self.page_spin = QSpinBox()
        self.page_spin.setRange(1, 1)
        self.page_spin.setEnabled(False)
        self.page_spin.valueChanged.connect(self.on_cbz_page_changed)
        self.page_count_label = QLabel("")

        self.current_project_path = None

        # legacy layout options kept for reference
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        main_layout = QHBoxLayout()
        layout.addLayout(main_layout)

        # thumbnail widget
        self.thumbnail_list.setFixedWidth(160)
        thumb_widget = QWidget()
        thumb_layout = QVBoxLayout(thumb_widget)
        thumb_layout.setContentsMargins(4,4,4,4)
        thumb_layout.addWidget(self.thumbnail_list)

        # image widget
        self.image_viewer.setMinimumSize(420, 420)
        image_widget = QWidget()
        image_layout = QVBoxLayout(image_widget)
        image_layout.setContentsMargins(8,8,8,8)
        image_layout.addWidget(self.image_viewer)

        # text column using splitter
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(4,4,4,4)
        text_splitter = QSplitter(Qt.Vertical)
        text_splitter.addWidget(self.region_list)
        text_splitter.addWidget(self.ocr_text)
        text_splitter.addWidget(self.translated_text)
        text_layout.addWidget(text_splitter)

        # controls for selected text: save translation and font controls
        text_ctrl_row = QHBoxLayout()
        text_ctrl_row.addWidget(self.btn_save_translation)
        text_ctrl_row.addWidget(self.font_combo)
        text_ctrl_row.addWidget(self.font_size_spin)
        text_ctrl_row.addWidget(self.color_btn)
        text_ctrl_row.addWidget(self.color_preview)
        text_ctrl_row.addWidget(self.btn_clear_render)
        text_ctrl_row.addWidget(self.btn_clear_all_render)
        text_layout.addLayout(text_ctrl_row)

        # action buttons related to selection (moved from action column)
        text_action_row = QHBoxLayout()
        text_action_row.addWidget(self.btn_save_text)
        text_action_row.addWidget(self.btn_merge)
        text_action_row.addWidget(self.btn_translate)
        text_action_row.addWidget(self.btn_translate_all)
        text_layout.addLayout(text_action_row)

        # action column as a fixed-width widget
        action_widget = QWidget()
        action_layout = QVBoxLayout(action_widget)
        action_layout.setContentsMargins(6,6,6,6)
        action_layout.addWidget(self.btn_open)
        action_layout.addWidget(self.btn_open_cbz)
        action_layout.addWidget(self.cbz_progress)
        action_layout.addWidget(self.page_spin)
        action_layout.addWidget(self.page_count_label)
        action_layout.addWidget(self.btn_detect)
        action_layout.addWidget(self.btn_save_page)
        action_layout.addWidget(self.btn_load_page)
        action_layout.addWidget(self.btn_save_project)
        action_layout.addWidget(self.btn_load_project)
        action_layout.addWidget(self.btn_undo)
        action_layout.addWidget(self.btn_render)
        action_layout.addWidget(self.btn_save_cbz)
        action_layout.addWidget(self.lbl_status)
        action_layout.addStretch()
        action_widget.setFixedWidth(240)

        main_layout.addWidget(thumb_widget, 0)
        main_layout.addWidget(image_widget, 1)
        main_layout.addWidget(text_widget, 1)
        main_layout.addWidget(action_widget, 0)




        self.selected_region = None
        self.btn_open.clicked.connect(self.open_image)
        self.btn_detect.clicked.connect(self.detect)
        self.region_list.itemClicked.connect(
            self.region_list_item_clicked
        )
        self.btn_save_text.clicked.connect(
            self.save_text
        )
        self.btn_merge.clicked.connect(
            self.merge_selected
        )
        self.btn_save_translation.clicked.connect(self.save_translation)
        self.btn_translate.clicked.connect(
            self.translate_selected
        )
        self.btn_translate_all.clicked.connect(
            self.translate_all
        )

        self.btn_save_cbz.clicked.connect(
            self.save_cbz
        )
        self.btn_save_page.clicked.connect(
            self.save_page
        )
        self.btn_load_page.clicked.connect(
            self.load_page
        )
        self.btn_save_project.clicked.connect(
            self.save_project
        )
        self.btn_load_project.clicked.connect(
            self.load_project
        )
        self.btn_open_cbz.clicked.connect(lambda: self.open_cbz())
        self.font_combo.currentTextChanged.connect(self.on_font_changed)
        self.font_size_spin.valueChanged.connect(self.on_font_size_changed)
        self.color_btn.clicked.connect(self.on_choose_color)
        self.btn_clear_render.clicked.connect(self.clear_render)
        self.btn_clear_all_render.clicked.connect(self.clear_all_render)
        
        self.btn_undo.clicked.connect(
            self.undo
        )
        self.btn_render.clicked.connect(
            self.render
        )
        self.btn_undo.setEnabled(False)
        self.regions = []
        self.history = []
        # CBZ state
        self.cbz_path = None
        self.cbz_members = []
        self.cbz_index = 0
        self.cbz_tmpdir = None
        self.cbz_page_regions = {}
        self.cbz_page_status = {}
        self.is_closing = False

        # page selector (initialized earlier)

    def closeEvent(self, event):
        self.is_closing = True
        # clear tempdir on close
        if self.cbz_tmpdir and Path(self.cbz_tmpdir).exists():
            try:
                shutil.rmtree(self.cbz_tmpdir)
            except Exception:
                pass
        event.accept()

    def save_current_region_edits(self):
        if getattr(self, 'selected_region', None) is not None:
            self.selected_region.text = self.ocr_text.toPlainText()
            self.selected_region.translation = self.translated_text.toPlainText()

    def open_image(self):

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open",
            "",
            "Images (*.png *.jpg *.jpeg)",
            options=options
        )

        if not path:
            return

        self.image_path = path
        self.regions = []
        self.history = []
        self.btn_undo.setEnabled(False)
        self.image_viewer.load_image(
            path
        )
        self.lbl_status.setText(f"Opened image: {Path(path).name}")

        # reset CBZ state when loading a single image
        self.cbz_path = None
        self.cbz_members = []
        self.cbz_index = 0
        self.thumbnail_list.clear()
        self.page_spin.setEnabled(False)
        self.page_spin.setRange(1, 1)
        self.page_count_label.setText("")

        if self.cbz_tmpdir and Path(self.cbz_tmpdir).exists():
            try:
                shutil.rmtree(self.cbz_tmpdir)
            except Exception:
                pass
            self.cbz_tmpdir = None

    def _create_cbz_tempdir(self, source_path):

        cbz_name = Path(source_path).stem
        base_dir = Path(tempfile.gettempdir())
        temp_dir = base_dir / f"{cbz_name}_cbz"
        suffix = 0
        while temp_dir.exists():
            suffix += 1
            temp_dir = base_dir / f"{cbz_name}_cbz_{suffix}"

        try:
            temp_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            temp_dir = Path(tempfile.mkdtemp(prefix='cbz_'))

        self.cbz_tmpdir = str(temp_dir)

    def load_cbz_page(self, index, save_current=True):

        if not self.cbz_members:
            return

        if save_current:
            self.save_current_region_edits()

            # save current page regions
            try:
                if self.cbz_members and 0 <= self.cbz_index < len(self.cbz_members):
                    key = self.cbz_members[self.cbz_index]
                    self.cbz_page_regions[key] = copy.deepcopy(self.regions)
            except Exception:
                pass

        # clamp index
        index = max(0, min(index, len(self.cbz_members) - 1))

        member = self.cbz_members[index]

        try:
            with zipfile.ZipFile(self.cbz_path, 'r') as z:
                data = z.read(member)

            fname = Path(member).name
            out_path = Path(self.cbz_tmpdir) / fname
            out_path.write_bytes(data)

            # load image
            self.image_path = str(out_path)
            self.image_viewer.load_image(self.image_path)

            # restore regions for this page if any
            stored = self.cbz_page_regions.get(member)
            if stored is not None:
                self.regions = copy.deepcopy(stored)
            else:
                # Try to auto-load from individual page JSON file
                loaded_from_file = False
                if self.cbz_path:
                    cbz_dir = Path(self.cbz_path).resolve().parent
                    page_file = cbz_dir / f"{index + 1}.json"
                    if page_file.exists():
                        try:
                            print(f"DEBUG: Auto-loading page file on load: {page_file}")
                            with open(page_file, "r", encoding="utf-8") as pf:
                                pdata = json.load(pf)
                                pregions = pdata.get("regions", [])
                                self.regions = self._parse_regions(pregions)
                                self.cbz_page_regions[member] = copy.deepcopy(self.regions)
                                self.set_page_status(member, "saved")
                                loaded_from_file = True
                        except Exception as e:
                            print(f"DEBUG: Error auto-loading page file: {e}")
                
                if not loaded_from_file:
                    self.regions = []

            # update thumbnail selection
            try:
                item = self.thumbnail_list.item(index)
                if item:
                    self.thumbnail_list.setCurrentItem(item)
            except Exception:
                pass

            self.image_viewer.draw_regions(self.regions)
            self.image_viewer.render_translations(self.regions)
            self.refresh_region_list()
            if self.visible_regions:
                self.select_region(self.visible_regions[0])
                self.region_list.setCurrentRow(0)
            elif self.regions:
                self.select_region(self.regions[0])
            else:
                self.selected_region = None
                self.image_viewer.selected_region_id = None

            self.cbz_index = index
            # update page selector without emitting
            if self.page_spin:
                self.page_spin.blockSignals(True)
                self.page_spin.setValue(index + 1)
                self.page_spin.blockSignals(False)

        except Exception as e:
            self.lbl_status.setText(f'Load page failed: {e}')

    def open_cbz(self, path=None, auto_load_first_page=True):

        print("open_cbz called", path)
        self.lbl_status.setText("Opening CBZ dialog...")
        QApplication.processEvents()

        if path is None:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog

            dialog = QFileDialog(self, "Open CBZ", "", "CBZ Files (*.cbz);;ZIP Files (*.zip)")
            dialog.setOptions(options)
            dialog.setFileMode(QFileDialog.ExistingFile)
            dialog.setViewMode(QFileDialog.Detail)
            dialog.setWindowModality(Qt.ApplicationModal)
            dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
            dialog.setAcceptMode(QFileDialog.AcceptOpen)

            print("exec dialog")
            result = dialog.exec()
            print("dialog result", result)
            if result != QFileDialog.Accepted:
                self.lbl_status.setText("CBZ open cancelled")
                print("dialog cancelled")
                return

            selected_files = dialog.selectedFiles()
            print("selected files", selected_files)
            if not selected_files:
                self.lbl_status.setText("No CBZ selected")
                print("no selected files")
                return

            path = selected_files[0]

        if not path:
            return

        # reset CBZ state before opening a new archive
        self.cbz_page_regions = {}
        self.cbz_page_status = {}

        # clear previous tempdir
        if self.cbz_tmpdir and Path(self.cbz_tmpdir).exists():
            try:
                shutil.rmtree(self.cbz_tmpdir)
            except Exception:
                pass

        try:
            with zipfile.ZipFile(path, 'r') as z:
                members = [m for m in z.namelist() if m.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'))]
                members.sort()
                if not members:
                    self.lbl_status.setText('CBZ contains no image files')
                    return

                self.cbz_path = path
                self.cbz_members = members
                self.cbz_index = 0
                self._create_cbz_tempdir(path)

                # create thumbnails for all pages
                self.thumbnail_list.clear()
                self.cbz_progress.setMaximum(len(self.cbz_members))
                self.cbz_progress.setValue(0)
                self.cbz_progress.setVisible(True)
                for i, member in enumerate(self.cbz_members):
                    if getattr(self, 'is_closing', False):
                        break
                    try:
                        data = z.read(member)
                        pix = QPixmap()
                        pix.loadFromData(data)
                        icon = QIcon(pix.scaled(140, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                        item = QListWidgetItem(icon, str(i+1))
                        item.setData(Qt.UserRole, member)
                        self.thumbnail_list.addItem(item)
                        # initialize status
                        self.cbz_page_regions[member] = None
                        self.cbz_page_status[member] = 'unchanged'
                    except Exception:
                        item = QListWidgetItem(str(i+1))
                        item.setData(Qt.UserRole, member)
                        self.thumbnail_list.addItem(item)
                    self.cbz_progress.setValue(i + 1)
                    QApplication.processEvents()
                self.cbz_progress.setVisible(False)

            if getattr(self, 'is_closing', False):
                return

            # setup page selector
            self.page_spin.blockSignals(True)
            self.page_spin.setRange(1, max(1, len(self.cbz_members)))
            self.page_spin.setValue(1)
            self.page_spin.setEnabled(True)
            self.page_spin.blockSignals(False)
            self.page_count_label.setText(f"/ {len(self.cbz_members)}")

            if auto_load_first_page:
                self.load_cbz_page(0, save_current=False)

        except Exception as e:
            self.lbl_status.setText(f'Open CBZ failed: {e}')

    def on_cbz_page_changed(self, value):

        # value is 1-based
        page = max(1, value)
        self.load_cbz_page(page - 1)

    def on_thumbnail_clicked(self, item):

        member = item.data(Qt.UserRole)
        if not member:
            return
        try:
            index = self.cbz_members.index(member)
        except ValueError:
            return
        self.load_cbz_page(index)

    def detect(self):
        try:

            if not self.image_path:
                return

            self.regions = self.detector.detect(
                self.image_path
            )
            self.image_viewer.load_image(
                self.image_path
            )

            self.image_viewer.draw_regions(
                self.regions
            )
            self.refresh_region_list()
            self.history = []
            self.btn_undo.setEnabled(False)
            # write region details to selected text panel
            details = "\n\n".join(
                f"[{region.id}]\n{region.text}"
                for region in self.regions
            )
            self.ocr_text.setText(details)

        except Exception as e:
            self.ocr_text.setText(f"ERROR:\n{e}")
        if self.regions:

            self.select_region(
                self.regions[0]
            )
        if self.regions:
            self.region_list.setCurrentRow(0)

    def select_region(self, region):

        self.selected_region = region

        self.ocr_text.setText(
            region.text
        )

        self.translated_text.setText(
            region.translation
        )

        self.color_preview.setStyleSheet(
            f"background: {region.outline_color};"
        )

        self.image_viewer.selected_region_id = region.id
        self.image_viewer.load_image(self.image_path)
        self.image_viewer.draw_regions(self.regions)
        self.image_viewer.render_translations(self.regions)

        selected_items = self.region_list.selectedItems()
        selected = []

        for item in selected_items:

            row = self.region_list.row(item)

            selected.append(
                self.visible_regions[row]
            )

    def save_text(self):

        if not self.selected_region:
            return

        self.push_history()
        self.selected_region.text = (
            self.ocr_text.toPlainText()
        )

        self.refresh_region_list()

        index = self.regions.index(
            self.selected_region
        )

        self.region_list.setCurrentRow(
            index
        )

    def on_font_changed(self, font_name):

        family = str(font_name)
        if family:
            self.image_viewer.text_font_family = family
            if self.regions:
                self.image_viewer.load_image(self.image_path)
                self.image_viewer.draw_regions(self.regions)
                self.image_viewer.render_translations(self.regions)

    def load_asset_fonts(self):

        fonts_dir = Path(__file__).resolve().parent.parent / "assets" / "fonts"
        if not fonts_dir.exists():
            self.font_combo.addItem("Arial")
            return

        font_files = sorted(fonts_dir.glob("*.ttf")) + sorted(fonts_dir.glob("*.otf"))
        loaded_any = False

        for font_path in font_files:
            try:
                font_id = QFontDatabase.addApplicationFont(str(font_path))
                if font_id == -1:
                    continue
                families = QFontDatabase.applicationFontFamilies(font_id)
                if not families:
                    continue
                family = families[0]
                if family in self.asset_font_map:
                    continue
                self.asset_font_map[family] = str(font_path)
                self.font_combo.addItem(family)
                loaded_any = True
            except Exception:
                continue

        if not loaded_any:
            self.font_combo.addItem("Arial")

        if self.font_combo.count() > 0:
            self.font_combo.setCurrentIndex(0)
            self.image_viewer.text_font_family = self.font_combo.currentText()

    def on_font_size_changed(self, size):

        self.image_viewer.text_font_size = int(size)
        if self.regions:
            self.image_viewer.load_image(self.image_path)
            self.image_viewer.draw_regions(self.regions)
            self.image_viewer.render_translations(self.regions)

    def on_choose_color(self):

        color = QColorDialog.getColor()
        if not color.isValid():
            return

        if self.selected_region:
            self.push_history()
            self.selected_region.outline_color = color.name()
            self.color_preview.setStyleSheet(
                f"background: {color.name()};"
            )
            self.image_viewer.load_image(self.image_path)
            self.image_viewer.draw_regions(self.regions)
            self.image_viewer.render_translations(self.regions)
            try:
                if getattr(self, 'cbz_members', None):
                    member = self.cbz_members[self.cbz_index]
                    self.set_page_status(member, 'editing')
            except Exception:
                pass
            self.lbl_status.setText("Region color updated")
            return

        self.lbl_status.setText("Select a region first to change its color")

    def translate_selected(self):

        if not self.selected_region:
            return

        result = self.translator.translate(
            self.selected_region.text
        )

        self.push_history()
        self.selected_region.translation = result

        self.translated_text.setText(
            result
        )

        # region translation updated
    def save_cbz(self):

        self.save_current_region_edits()

        if not self.cbz_path or not self.cbz_members:
            self.lbl_status.setText(
                "No CBZ loaded. Cannot save CBZ."
            )
            return

        # ensure current page state is stored before saving
        current_member = self.cbz_members[self.cbz_index]
        self.cbz_page_regions[current_member] = copy.deepcopy(self.regions)

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CBZ",
            "",
            "CBZ (*.cbz);;ZIP (*.zip)"
        )

        if not path:
            return

        try:
            target_path = Path(path)
            temp_target = Path(str(target_path) + ".tmp")

            with zipfile.ZipFile(self.cbz_path, 'r') as source_archive:
                if not self.cbz_tmpdir or not Path(self.cbz_tmpdir).exists():
                    self.cbz_tmpdir = tempfile.mkdtemp(prefix='cbz_')

                self.cbz_progress.setMaximum(len(self.cbz_members))
                self.cbz_progress.setValue(0)
                self.cbz_progress.setVisible(True)

                with zipfile.ZipFile(temp_target, 'w', compression=zipfile.ZIP_DEFLATED) as dst_zip:
                    original_regions = copy.deepcopy(self.regions)
                    original_image_path = self.image_path

                    for i, member in enumerate(self.cbz_members):
                        if getattr(self, 'is_closing', False):
                            break
                        data = source_archive.read(member)
                        page_regions = self.cbz_page_regions.get(member)
                        if page_regions is not None:
                            image_name = Path(member).name
                            out_path = Path(self.cbz_tmpdir) / image_name
                            out_path.write_bytes(data)
                            self.image_viewer.load_image(str(out_path))
                            self.image_viewer.draw_regions(page_regions)
                            self.image_viewer.render_translations(page_regions)
                            self.image_viewer.save_image(str(out_path))
                            dst_zip.write(str(out_path), member)
                        else:
                            dst_zip.writestr(member, data)

                        self.cbz_progress.setValue(i + 1)
                        QApplication.processEvents()

                    # restore current view state after saving
                    self.image_path = original_image_path
                    self.regions = original_regions
                    if self.image_path:
                        self.image_viewer.load_image(self.image_path)
                        self.image_viewer.draw_regions(self.regions)
                        self.image_viewer.render_translations(self.regions)

            if getattr(self, 'is_closing', False):
                try:
                    if temp_target.exists():
                        temp_target.unlink()
                except Exception:
                    pass
                return

            # Safely finalize file replacement
            try:
                if temp_target.exists():
                    if target_path.exists():
                        target_path.unlink()
                    temp_target.rename(target_path)
            except Exception:
                try:
                    import os
                    os.replace(str(temp_target), str(target_path))
                except Exception as e:
                    raise Exception(f"Failed to finalize file: {e}")

            self.lbl_status.setText(
                f"Saved CBZ to {path}"
            )
        except Exception as e:
            self.lbl_status.setText(
                f"Save CBZ failed: {e}"
            )
        finally:
            self.cbz_progress.setVisible(False)

    def render(self):
        """Refresh the image and re-render all translated regions."""
        self.image_viewer.load_image(self.image_path)
        self.image_viewer.draw_regions(self.regions)
        self.image_viewer.render_translations(self.regions)

    def translate_all(self):

        if not self.regions:
            return

        self.push_history()
        translated = 0

        # mark page as translating
        try:
            if getattr(self, 'cbz_members', None):
                member = self.cbz_members[self.cbz_index]
                self.set_page_status(member, 'editing')
        except Exception:
            pass

        total = len([r for r in self.regions if r.enabled])

        for region in self.regions:
            if getattr(self, 'is_closing', False):
                break
            if not region.enabled:
                continue
            try:

                result = self.translator.translate(
                    region.text
                )

                region.translation = result

                translated += 1

                self.lbl_status.setText(
                    f"Translating {translated}/{total}"
                )

                # only update status badge (no progress counts on thumbnails)
                try:
                    if getattr(self, 'cbz_members', None):
                        member = self.cbz_members[self.cbz_index]
                        self.set_page_status(member, 'editing')
                except Exception:
                    pass

                QApplication.processEvents()

            except Exception as e:
                self.lbl_status.setText(f"Translate error: {e}")

        if getattr(self, 'is_closing', False):
            return

        # translation pass completed
        # mark page as saved/translated and show final counts
        try:
            if getattr(self, 'cbz_members', None):
                member = self.cbz_members[self.cbz_index]
                # update internal status first so badge shows ✓
                self.set_page_status(member, 'saved')
        except Exception:
            pass

        # update main status label
        self.lbl_status.setText(f"Translated {translated}/{total}")
    def disable_selected(self):

        if not self.selected_region:
            return

        self.push_history()
        self.selected_region.enabled = (
            not self.selected_region.enabled
        )

        self.image_viewer.load_image(
            self.image_path
        )

        self.image_viewer.draw_regions(
            self.regions
        )

        self.refresh_region_list()

    def refresh_region_list(self):

        self.region_list.clear()

        self.visible_regions = []

        for region in self.regions:

            if not region.enabled:
                continue

            self.visible_regions.append(
                region
            )

            preview = region.text[:30]

            self.region_list.addItem(
                f"[{region.id}] {preview}"
            )
    def merge_selected(self):
        items = self.region_list.selectedIndexes()

        if len(items) < 2:
            return

        selected = [
            self.visible_regions[i.row()]
            for i in items
        ]

        selected.sort(
            key=lambda r: (
                min(p[1] for p in r.polygon),
                min(p[0] for p in r.polygon)
            )
        )

        merged_text = " ".join(
            r.text
            for r in selected
            if r.enabled
        )

        all_x = []
        all_y = []

        for r in selected:

            for p in r.polygon:

                all_x.append(p[0])
                all_y.append(p[1])

        x1 = min(all_x)
        y1 = min(all_y)

        x2 = max(all_x)
        y2 = max(all_y)

        polygon = [
            [x1, y1],
            [x2, y1],
            [x2, y2],
            [x1, y2]
        ]

        master = selected[0]

        master.text = merged_text
        master.polygon = polygon

        for r in selected[1:]:

            r.enabled = False
            r.render_outline = False

        self.image_viewer.load_image(
            self.image_path
        )

        self.image_viewer.draw_regions(
            self.regions
        )

        self.refresh_region_list()

        self.select_region(master)

        self.push_history()

    def save_translation(self):

        if not self.selected_region:
            return

        self.push_history()
        self.selected_region.translation = (
            self.translated_text.toPlainText()
        )

        # re-render translations
        try:
            self.image_viewer.load_image(self.image_path)
            self.image_viewer.draw_regions(self.regions)
            self.image_viewer.render_translations(self.regions)
        except Exception:
            pass

        # mark page edited
        try:
            if getattr(self, 'cbz_members', None):
                member = self.cbz_members[self.cbz_index]
                self.set_page_status(member, 'editing')
        except Exception:
            pass

        self.lbl_status.setText("Translation saved")



    def save_page(self):

        self.save_current_region_edits()

        if not self.image_path or not self.regions:
            self.lbl_status.setText(
                "No page state available to save."
            )
            return

        default_name = "page.json"
        if getattr(self, 'cbz_members', None):
            default_name = f"{self.cbz_index + 1}.json"
        elif self.image_path:
            default_name = f"{Path(self.image_path).stem}.json"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Page",
            default_name,
            "JSON (*.json)"
        )

        if not path:
            return

        current_member = None
        if getattr(self, 'cbz_members', None) and 0 <= self.cbz_index < len(self.cbz_members):
            current_member = self.cbz_members[self.cbz_index]

        target_path = Path(path)
        temp_path = Path(f"{path}.tmp")

        data = {
            "image_path": self.image_path,
            "regions": [
                {
                    "id": int(region.id),
                    "polygon": [
                        [int(point[0]), int(point[1])]
                        for point in region.polygon
                    ],
                    "text": str(region.text),
                    "translation": str(region.translation),
                    "enabled": bool(region.enabled),
                    "outline_color": str(region.outline_color),
                    "render_bg": bool(region.render_bg),
                    "render_outline": bool(region.render_outline)
                }
                for region in self.regions
            ]
        }

        try:
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
                file.flush()
                os.fsync(file.fileno())
            temp_path.replace(target_path)
            if current_member is not None:
                self.cbz_page_regions[current_member] = copy.deepcopy(self.regions)
                try:
                    self.set_page_status(current_member, 'saved')
                except Exception:
                    pass
            self.lbl_status.setText(
                f"Saved page to {path}"
            )
            # mark current CBZ page saved if applicable
            try:
                if getattr(self, 'cbz_members', None) and current_member is not None:
                    self.set_page_status(current_member, 'saved')
            except Exception:
                pass
        except Exception as e:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            self.lbl_status.setText(
                f"Save failed: {e}"
            )

    def save_project(self):

        self.save_current_region_edits()

        if not self.regions and not self.cbz_members:
            self.lbl_status.setText(
                "Nothing to save in project."
            )
            return

        if self.cbz_members and self.cbz_path:
            current_member = self.cbz_members[self.cbz_index]
            self.cbz_page_regions[current_member] = copy.deepcopy(self.regions)
        else:
            current_member = None

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Project",
            "project.json",
            "JSON (*.json)"
        )

        if not path:
            return

        project = {
            "cbz_path": self.cbz_path if self.cbz_members else None,
            "image_path": self.image_path if not self.cbz_members else None,
            "current_member": current_member,
            "font_family": self.image_viewer.text_font_family,
            "font_size": self.image_viewer.text_font_size,
            "text_color": self.image_viewer.text_color.name(),
            "pages": []
        }

        if self.cbz_members:
            for member in self.cbz_members:
                page_regions = self.cbz_page_regions.get(member)
                regions_list = None
                if page_regions is not None:
                    regions_list = [
                        {
                            "id": int(region.id),
                            "polygon": [
                                [int(point[0]), int(point[1])]
                                for point in region.polygon
                            ],
                            "text": str(region.text),
                            "translation": str(region.translation),
                            "enabled": bool(region.enabled),
                            "outline_color": str(region.outline_color),
                            "render_bg": bool(region.render_bg),
                            "render_outline": bool(region.render_outline)
                        }
                        for region in page_regions
                    ]
                project["pages"].append({
                    "member": member,
                    "status": self.cbz_page_status.get(member, "unchanged"),
                    "regions": regions_list
                })
        else:
            project["pages"].append({
                "member": None,
                "status": "saved",
                "regions": [
                    {
                        "id": int(region.id),
                        "polygon": [
                            [int(point[0]), int(point[1])]
                            for point in region.polygon
                        ],
                        "text": str(region.text),
                        "translation": str(region.translation),
                        "enabled": bool(region.enabled),
                        "outline_color": str(region.outline_color),
                        "render_bg": bool(region.render_bg),
                        "render_outline": bool(region.render_outline)
                    }
                    for region in self.regions
                ]
            })

        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(project, file, ensure_ascii=False, indent=2)
            self.lbl_status.setText(
                f"Saved project to {path}"
            )
            self.current_project_path = path
        except Exception as e:
            self.lbl_status.setText(
                f"Save project failed: {e}"
            )

    def _parse_regions(self, regions_list):
        if regions_list is None:
            return []
        return [
            Region(
                id=item["id"],
                polygon=item["polygon"],
                text=item.get("text", ""),
                translation=item.get("translation", ""),
                enabled=item.get("enabled", True),
                outline_color=item.get("outline_color", "#00FF00"),
                render_bg=item.get("render_bg", True),
                render_outline=item.get("render_outline", True)
            )
            for item in regions_list
        ]

    def load_project(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Project",
            "",
            "JSON (*.json)"
        )

        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)

            project_dir = Path(path).parent

            # Restore project font settings if present
            font_family = data.get("font_family")
            font_size = data.get("font_size")
            text_color = data.get("text_color")

            if font_family:
                self.image_viewer.text_font_family = font_family
                idx = self.font_combo.findText(font_family)
                if idx != -1:
                    self.font_combo.blockSignals(True)
                    self.font_combo.setCurrentIndex(idx)
                    self.font_combo.blockSignals(False)
            if font_size:
                self.image_viewer.text_font_size = int(font_size)
                self.font_size_spin.blockSignals(True)
                self.font_size_spin.setValue(int(font_size))
                self.font_size_spin.blockSignals(False)
            if text_color:
                from PySide6.QtGui import QColor
                self.image_viewer.text_color = QColor(text_color)

            cbz_path = data.get("cbz_path")
            if cbz_path:
                cbz_file = Path(cbz_path)
                if not cbz_file.is_absolute():
                    cbz_file = project_dir / cbz_file
                if not cbz_file.exists():
                    raise FileNotFoundError(
                        f"CBZ file not found: {cbz_file}"
                    )

                self.open_cbz(str(cbz_file), auto_load_first_page=False)
                self.current_project_path = path

                # restore saved page states
                print("DEBUG: Restoring saved page states...")
                for page in data.get("pages", []):
                    member = page.get("member")
                    if not member:
                        continue

                    # Try to load from individual JSON file in the project directory first
                    loaded_from_file = False
                    try:
                        idx = self.cbz_members.index(member)
                        page_file = project_dir / f"{idx + 1}.json"
                        if page_file.exists():
                            print(f"DEBUG: Loading individual page file: {page_file}")
                            with open(page_file, "r", encoding="utf-8") as pf:
                                pdata = json.load(pf)
                                pregions = pdata.get("regions", [])
                                self.cbz_page_regions[member] = self._parse_regions(pregions)
                                self.set_page_status(member, "saved")
                                loaded_from_file = True
                                print(f"DEBUG: Successfully loaded {len(pregions)} regions for {member} from {page_file.name}")
                    except Exception as e:
                        print(f"DEBUG Error checking individual page file: {e}")

                    if not loaded_from_file:
                        regions_data = page.get("regions")
                        if regions_data is not None:
                            self.cbz_page_regions[member] = self._parse_regions(regions_data)
                            self.set_page_status(member, page.get("status", "saved"))
                            print(f"DEBUG: Loaded {len(regions_data)} regions for {member} from project.json")
                        else:
                            self.cbz_page_regions[member] = None
                            self.set_page_status(member, "unchanged")

                current_member = data.get("current_member")
                index = 0
                if current_member in self.cbz_members:
                    index = self.cbz_members.index(current_member)
                print(f"DEBUG: Loading current member={current_member} (index={index})")
                self.load_cbz_page(index, save_current=False)

                self.lbl_status.setText(
                    f"Loaded project from {path}"
                )
                return

            image_path = data.get("image_path")
            if not image_path:
                raise ValueError("Project file missing image_path or cbz_path")

            project_dir = Path(path).parent
            image_file = Path(image_path)
            if not image_file.is_absolute():
                image_file = project_dir / image_file

            if not image_file.exists():
                raise FileNotFoundError(
                    f"Image not found: {image_file}"
                )

            self.cbz_path = None
            self.cbz_members = []
            self.cbz_index = 0
            self.cbz_tmpdir = None
            self.cbz_page_regions = {}
            self.cbz_page_status = {}
            self.current_project_path = path

            self.image_path = str(image_file)

            # Determine where the regions are:
            # It could be under "regions" (Format B / page save) or under "pages"[0]["regions"] (Format A single image project)
            if "regions" in data:
                regions_list = data["regions"]
            elif "pages" in data and len(data["pages"]) > 0:
                regions_list = data["pages"][0].get("regions", [])
            else:
                regions_list = []

            self.regions = self._parse_regions(regions_list)

            self.history = []
            self.btn_undo.setEnabled(False)
            self.image_viewer.load_image(self.image_path)
            self.image_viewer.draw_regions(self.regions)
            self.image_viewer.render_translations(self.regions)
            self.refresh_region_list()
            if self.visible_regions:
                self.select_region(self.visible_regions[0])
                self.region_list.setCurrentRow(0)
            elif self.regions:
                self.select_region(self.regions[0])
            self.lbl_status.setText(
                f"Loaded project from {path}"
            )
        except Exception as e:
            self.lbl_status.setText(
                f"Load failed: {e}"
            )

    def load_page(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Page",
            "",
            "JSON (*.json)"
        )

        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)

            regions_list = data.get("regions", [])

            loaded_regions = self._parse_regions(regions_list)

            self.regions = loaded_regions

            if getattr(self, 'cbz_members', None) and 0 <= self.cbz_index < len(self.cbz_members):
                current_member = self.cbz_members[self.cbz_index]
                self.cbz_page_regions[current_member] = copy.deepcopy(self.regions)
                try:
                    self.set_page_status(current_member, 'saved')
                except Exception:
                    pass

            self.history = []
            self.btn_undo.setEnabled(False)
            self.image_viewer.load_image(self.image_path)
            self.image_viewer.draw_regions(self.regions)
            self.image_viewer.render_translations(self.regions)
            self.refresh_region_list()

            if self.visible_regions:
                self.select_region(self.visible_regions[0])
                self.region_list.setCurrentRow(0)
            elif self.regions:
                self.select_region(self.regions[0])
            else:
                self.selected_region = None
                self.image_viewer.selected_region_id = None

            self.lbl_status.setText(f"Loaded page from {Path(path).name}")
        except Exception as e:
            self.lbl_status.setText(f"Load page failed: {e}")

    def clear_render(self):

        # Try to get selected items from region list
        selected_items = self.region_list.selectedItems()
        regions_to_clear = []

        # If items selected in list, use those
        if selected_items:
            for item in selected_items:
                row = self.region_list.row(item)
                if 0 <= row < len(self.visible_regions):
                    region = self.visible_regions[row]
                    regions_to_clear.append(region)
        # Otherwise, use currently selected region
        elif self.selected_region:
            regions_to_clear.append(self.selected_region)
        else:
            self.lbl_status.setText(
                "Select region(s) first to clear outline."
            )
            return

        self.push_history()

        # Clear outline for all selected regions
        for region in regions_to_clear:
            region.render_outline = False

        self.image_viewer.load_image(self.image_path)
        self.image_viewer.draw_regions(self.regions)
        self.image_viewer.render_translations(self.regions)

        try:
            if getattr(self, 'cbz_members', None):
                member = self.cbz_members[self.cbz_index]
                self.set_page_status(member, 'editing')
        except Exception:
            pass

        count = len(regions_to_clear)
        self.lbl_status.setText(
            f"Cleared outline for {count} region(s)"
        )

        # Deselect after clearing
        self.selected_region = None
        self.image_viewer.selected_region_id = None
        self.image_viewer.load_image(self.image_path)
        self.image_viewer.draw_regions(self.regions)
        self.image_viewer.render_translations(self.regions)

    def clear_all_render(self):

        if not self.regions:
            self.lbl_status.setText(
                "No regions to clear."
            )
            return

        self.push_history()

        # Clear outline for all regions
        for region in self.regions:
            region.render_outline = False

        self.image_viewer.load_image(self.image_path)
        self.image_viewer.draw_regions(self.regions)
        self.image_viewer.render_translations(self.regions)

        try:
            if getattr(self, 'cbz_members', None):
                member = self.cbz_members[self.cbz_index]
                self.set_page_status(member, 'editing')
        except Exception:
            pass

        self.lbl_status.setText(
            f"Cleared outline for all {len(self.regions)} region(s)"
        )

        # Deselect after clearing
        self.selected_region = None
        self.image_viewer.selected_region_id = None
        self.image_viewer.load_image(self.image_path)
        self.image_viewer.draw_regions(self.regions)
        self.image_viewer.render_translations(self.regions)

    def push_history(self):

        if not self.regions:
            return

        self.history.append(
            copy.deepcopy(self.regions)
        )

        if len(self.history) > 20:
            self.history.pop(0)

        self.btn_undo.setEnabled(
            len(self.history) > 0
        )

        # mark CBZ page as edited (unsaved)
        try:
            if getattr(self, 'cbz_members', None):
                member = self.cbz_members[self.cbz_index]
                self.set_page_status(member, 'editing')
        except Exception:
            pass

    def set_page_status(self, member, status):

        if not member:
            return

        self.cbz_page_status[member] = status

        # update thumbnail item text to show status marker
        try:
            idx = self.cbz_members.index(member)
            item = self.thumbnail_list.item(idx)
            if not item:
                return
            badge = ''
            if status == 'editing':
                badge = ' ●'
            elif status == 'saved':
                badge = ' ✓'
            else:
                badge = ''
            item.setText(f"{idx+1}{badge}")
        except Exception:
            pass

    def undo(self):

        if not self.history:
            return

        self.regions = self.history.pop()
        self.btn_undo.setEnabled(
            len(self.history) > 0
        )
        self.image_viewer.load_image(
            self.image_path
        )
        self.image_viewer.draw_regions(
            self.regions
        )
        self.refresh_region_list()
        if self.regions:
            self.select_region(self.regions[0])

    def region_list_item_clicked(self, item):

        self.save_current_region_edits()
        row = self.region_list.row(item)

        region = self.visible_regions[row]

        self.select_region(region)