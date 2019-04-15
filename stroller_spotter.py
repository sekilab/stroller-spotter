import sys
import os
import glob
import math
import scipy.io

from numpy import ndarray, uint8, array
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen
from PyQt5.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel, QFileDialog, QMessageBox,
                             QScrollBar, QGraphicsScene, QListWidget, QPushButton, QVBoxLayout,
                             QWidget, QSizePolicy, QGraphicsView, QSplitter)

class Image_annotator_view(QGraphicsView):
    def __init__(self,owner_app):
        super().__init__()
        self.owner_app = owner_app
        

    def mousePressEvent(self, event):
        if self.owner_app.add_points_button.isChecked():
            scene_coords = self.mapToScene(event.pos())
            if self.sceneRect().contains(scene_coords):
                self.owner_app.add_new_point(scene_coords.x(),scene_coords.y())
        if self.owner_app.select_points_button.isChecked():
            scene_coords = self.mapToScene(event.pos())
            if self.sceneRect().contains(scene_coords):
                self.owner_app.handle_select_click(scene_coords.x(),scene_coords.y())


    def keyPressEvent(self,event):
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_D:
            self.owner_app.delete_selected_points()


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Stroller spotter'
        
        self.setMinimumSize(940,480)
        self.img_folder_name = None
        self.save_dir = None
        self.scene = None
        self.current_annotation = {}
        self.pending_changes = False
        self.initUI()


    def initUI(self):
        self.layout = QHBoxLayout()

        self.setWindowTitle(self.title)
        self.buttons_layout = QVBoxLayout()
        self.expand_policy = QSizePolicy(QSizePolicy.Fixed,QSizePolicy.Expanding)
        self.open_folder_button = QPushButton('Open folder')
        self.set_save_dir_button = QPushButton('Set save directory')
        self.save_button = QPushButton('Save')
        self.add_points_button = QPushButton('Add points mode')
        self.select_points_button = QPushButton('Select points mode')
        self.open_folder_button.setSizePolicy(self.expand_policy)
        self.open_folder_button.setFixedWidth(100)
        self.open_folder_button.clicked.connect(self.open_folder_clicked)
        self.set_save_dir_button.setSizePolicy(self.expand_policy)
        self.set_save_dir_button.setFixedWidth(100)
        self.set_save_dir_button.clicked.connect(self.set_save_folder_clicked)
        self.save_button.setSizePolicy(self.expand_policy)
        self.save_button.setFixedWidth(100)
        self.save_button.clicked.connect(self.save_clicked)
        self.add_points_button.setSizePolicy(self.expand_policy)
        self.add_points_button.setFixedWidth(100)
        self.add_points_button.setCheckable(True)
        self.add_points_button.clicked.connect(self.add_points_clicked)
        self.select_points_button.setSizePolicy(self.expand_policy)
        self.select_points_button.setFixedWidth(100)
        self.select_points_button.setCheckable(True)
        self.select_points_button.clicked.connect(self.select_points_clicked)
        self.buttons_layout.addWidget(self.open_folder_button)
        self.buttons_layout.addWidget(self.set_save_dir_button)
        self.buttons_layout.addWidget(self.save_button)
        self.buttons_layout.addWidget(self.add_points_button)
        self.buttons_layout.addWidget(self.select_points_button)
        
        self.image_area_view = Image_annotator_view(self)
        self.image_area_view.setMinimumWidth(200)
        self.image_area_view.setMaximumSize(1024,768)

        self.image_list_layout = QVBoxLayout()
        self.current_dir_name_label = QLabel("<current directory>")
        self.current_dir_name_label.setMinimumWidth(200)
        self.current_dir_name_label.setWordWrap(True)
        self.self_image_list = QListWidget()
        self.self_image_list.currentItemChanged.connect(self.image_selected)
        self.self_image_list.setMinimumWidth(200)
        self.current_save_dir_name_label = QLabel("<current save directory>")
        self.current_save_dir_name_label.setMinimumWidth(200)
        self.current_save_dir_name_label.setWordWrap(True)
        self.image_list_layout.addWidget(self.current_dir_name_label)
        self.image_list_layout.addWidget(self.self_image_list)
        self.image_list_layout.addWidget(self.current_save_dir_name_label)
        self.image_list_widget = QWidget()
        self.image_list_widget.setLayout(self.image_list_layout)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.image_area_view)
        self.splitter.addWidget(self.image_list_widget)
        self.splitter.setSizes([600,200])
        self.splitter.setChildrenCollapsible(False)

        self.layout.addLayout(self.buttons_layout)
        #self.layout.addWidget(self.image_area_view)
        #self.layout.addLayout(self.image_list_layout)
        self.layout.addWidget(self.splitter)

        self.setLayout(self.layout)
        self.show()

    def show_not_saved_warning(self, op):
        qm = QMessageBox
        ret = qm.question(self,'', "There are pending changes which will be lost. Do you still want to %s?" % op, qm.Yes | qm.No)
        return (ret == qm.Yes)


    def open_folder_clicked(self):
        if self.pending_changes and not self.show_not_saved_warning("open new folder"):
            return
        self.uncheck_add_button()
        self.uncheck_select_button()
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        dlg.setNameFilter("*.jpg *.gif *.png")

        if dlg.exec_():
            self.img_folder_name = dlg.selectedFiles()[0]
            files = glob.glob(os.path.join(self.img_folder_name,'*.jpg'))            
            files.extend(glob.glob(os.path.join(self.img_folder_name,'*.gif')))
            files.extend(glob.glob(os.path.join(self.img_folder_name,'*.png')))
            self.current_dir_name_label.setText(self.img_folder_name)
            self.self_image_list.clear()
            self.self_image_list.addItems(files)
            if self.scene:
                self.scene.clear()
            for f in files:
                self.current_annotation[f] = {}
            self.save_dir = os.path.join(self.img_folder_name, "mat_files")
            if os.path.exists(self.save_dir):
                self.load_annotations()
                self.current_save_dir_name_label.setText("Saving to: " + self.save_dir)
                


    def image_selected(self, curr, prev):
        if curr and os.path.exists(curr.text()):
            self.load_image(curr.text())
            self.clear_selections()
            self.load_current_image_points()


    def load_image(self, image_path):
        self.scene = QGraphicsScene()
        self.image = QPixmap(image_path)
        self.scene.addPixmap(self.image)
        self.image_area_view.setScene(self.scene)    


    def set_save_folder_clicked(self):
        self.uncheck_add_button()
        self.uncheck_select_button()
        if not self.img_folder_name:
            QMessageBox.warning(self, "Oh, geee!", "You must open an image directory before setting save directory!")
            return
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)

        if dlg.exec_():
            if self.scene:
                self.scene.clear()
            files = self.current_annotation.keys()
            for f in files:
                self.current_annotation[f] = {}
            self.save_dir = dlg.selectedFiles()[0]
            self.current_save_dir_name_label.setText("Saving to: " + self.save_dir)
            self.load_annotations()


    def save_clicked(self):
        if not self.img_folder_name:
            return
        if not os.path.exists(self.save_dir):
            self.set_save_folder_clicked()
        self.save_annotations()


    def add_points_clicked(self):
        self.uncheck_select_button()
        if not self.img_folder_name:
            QMessageBox.warning(self, "Oh, geee!", "You must open an image directory before adding points!")
            self.add_points_button.toggle()


    def select_points_clicked(self):
        self.uncheck_add_button()
        if not self.select_points_button.isChecked():
            self.clear_selections()
        if not self.img_folder_name:
            QMessageBox.warning(self, "Oh, geee!", "You must open an image directory before selecting points!")
            self.select_points_button.toggle()
        

    def uncheck_add_button(self):
        self.add_points_button.setChecked(False)


    def uncheck_select_button(self):
        self.select_points_button.setChecked(False)
        self.clear_selections()


    def add_new_point(self,x,y):
        current_file = self.self_image_list.currentItem().text()
        if current_file not in self.current_annotation.keys():
            self.current_annotation[current_file] = {}
        if (x,y) in self.current_annotation[current_file].keys():
            return
        self.current_annotation[current_file][(x,y)] = False
        self.draw_crosshair(x,y)
        self.pending_changes = True


    def handle_select_click(self,x,y):
        current_file = self.self_image_list.currentItem().text()
        if current_file in self.current_annotation.keys():
            closest_point = None
            closest_point_dist = None
            for point in self.current_annotation[current_file].keys():
                dist = math.sqrt((point[0] - x) ** 2 + (point[1] - y) ** 2)
                if (not closest_point and dist < 6) or (closest_point and dist < closest_point_dist):
                    closest_point = point
                    closest_point_dist = dist
            if closest_point:
                self.current_annotation[current_file][closest_point] = not self.current_annotation[current_file][closest_point]
                self.draw_crosshair(closest_point[0], closest_point[1], self.current_annotation[current_file][closest_point])


    def load_current_image_points(self):
        currentItem = self.self_image_list.currentItem()
        if currentItem:
            current_file = currentItem.text()
            if current_file in self.current_annotation.keys():
                for point in self.current_annotation[current_file].keys():
                    self.draw_crosshair(point[0], point[1], self.current_annotation[current_file][point])


    def clear_selections(self):
        for _key, points in self.current_annotation.items():
            for point in points.keys():
                points[point] = False
        if self.img_folder_name:
            self.load_current_image_points()


    def draw_crosshair(self,x,y,selected=False):
        if self.image:
            painter = QPainter(self.image)
            if selected:
                painter.setPen(QPen(QColor(255,0,0)))
            else:
                painter.setPen(QPen(QColor(0,255,0)))
            painter.drawLine(x,y-4,x,y+4)
            painter.drawLine(x-4,y,x+4,y)
            self.scene.clear()
            self.scene.addPixmap(self.image)

    def delete_selected_points(self):
        if self.select_points_button.isChecked():
            for _key, points in self.current_annotation.items():
                points_to_delete = []
                for point in points.keys():
                    if points[point]:
                        points_to_delete.append(point)
                for point in points_to_delete:
                    del points[point]
            self.load_image(self.self_image_list.currentItem().text())
            self.load_current_image_points()
            self.pending_changes = True

    
    def save_annotations(self):
        if not self.save_dir:
            raise Exception("save called with save directory unset")
        if not os.path.exists(self.save_dir):
            raise Exception("save directory does not exist")
        mdict = {}
        mdict['__header__'] = b'MATLAB 5.0 MAT-file'
        mdict['__version__'] = 0x0100
        mdict['__globals__'] = []
        mdict['image_info'] = ndarray((1,1), dtype=object)
        mdict['image_info'][0][0] = ndarray((1,1), dtype=[('location', 'O'), ('number', 'O')])
        mdict['image_info'][0][0][0][0][1] = ndarray((1,1),  dtype=uint8)
        for image_path, points in self.current_annotation.items():
            mat_file_name = os.path.basename(image_path)
            mat_file_path = os.path.join(self.save_dir, mat_file_name)
            point_array = []
            for point in points.keys():
                point_array.append([point[0], point[1]])
            mdict['image_info'][0][0][0][0][0] = array(point_array)
            mdict['image_info'][0][0][0][0][1][0] = len(point_array)
            scipy.io.savemat(mat_file_path, mdict)
        self.pending_changes = False


    def load_annotations(self):
        if not self.save_dir:
            raise Exception("load called with save directory unset")
        if not os.path.exists(self.save_dir):
            raise Exception("save directory does not exists")
        for image_path in self.current_annotation.keys():
            mat_file_name = os.path.basename(image_path) + ".mat"
            mat_file_path = os.path.join(self.save_dir, mat_file_name)
            if os.path.exists(mat_file_path):
                mdict = scipy.io.loadmat(mat_file_path)
                for point in mdict['image_info'][0][0][0][0][0]:
                    self.current_annotation[image_path][(float(point[0]),float(point[1]))] = False

    def closeEvent(self, event):
        if self.pending_changes and not self.show_not_saved_warning("quit"):
            event.ignore()
        else:
            event.accept()

                         

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
