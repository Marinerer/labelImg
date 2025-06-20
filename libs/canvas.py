
try:
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
except ImportError:
    from PyQt4.QtGui import *
    from PyQt4.QtCore import *

# from PyQt4.QtOpenGL import *

from libs.shape import Shape
from libs.utils import distance

CURSOR_DEFAULT = Qt.ArrowCursor
CURSOR_POINT = Qt.PointingHandCursor
CURSOR_DRAW = Qt.CrossCursor
CURSOR_MOVE = Qt.ClosedHandCursor
CURSOR_GRAB = Qt.OpenHandCursor

# Global clipboard for cross-image copy/paste
GLOBAL_CLIPBOARD = []

# class Canvas(QGLWidget):


class Canvas(QWidget):
    zoomRequest = pyqtSignal(int)
    lightRequest = pyqtSignal(int)
    scrollRequest = pyqtSignal(int, int)
    newShape = pyqtSignal()
    selectionChanged = pyqtSignal(bool)
    shapeMoved = pyqtSignal()
    drawingPolygon = pyqtSignal(bool)

    CREATE, EDIT = list(range(2))

    epsilon = 24.0

    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)
        # Initialise local state.
        self.mode = self.EDIT
        self.shapes = []
        self.current = None
        self.selected_shapes = []  # save the selected shapes here as an array
        self.selected_shape_copy = None
        self.drawing_line_color = QColor(0, 0, 255)
        self.drawing_rect_color = QColor(0, 0, 255)
        self.line = Shape(line_color=self.drawing_line_color)
        self.prev_point = QPointF()
        self.offsets = QPointF(), QPointF()
        self.scale = 1.0
        self.overlay_color = None
        self.label_font_size = 8
        self.pixmap = QPixmap()
        self.visible = {}
        self._hide_background = False
        self.hide_background = False
        self.h_shape = None
        self.h_vertex = None
        self._painter = QPainter()
        self._cursor = CURSOR_DEFAULT
        # Menus:
        self.menus = (QMenu(), QMenu())
        # Set widget options.
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.WheelFocus)
        self.verified = False
        self.draw_square = False

        # initialisation for panning
        self.pan_initial_pos = QPoint()
        
        # initialisation for selection box
        self.selection_box_enabled = False
        self.selection_box_start = QPoint()
        self.selection_box_end = QPoint()
        
        # !For compatibility with existing code
        self._selected_shape = None
        
        # History system for undo functionality
        self.history = []
        self.max_history_size = 50

    def set_drawing_color(self, qcolor):
        self.drawing_line_color = qcolor
        self.drawing_rect_color = qcolor

    def enterEvent(self, ev):
        self.override_cursor(self._cursor)

    def leaveEvent(self, ev):
        self.restore_cursor()

    def focusOutEvent(self, ev):
        self.restore_cursor()

    def isVisible(self, shape):
        return self.visible.get(shape, True)

    def drawing(self):
        return self.mode == self.CREATE

    def editing(self):
        return self.mode == self.EDIT

    def set_editing(self, value=True):
        self.mode = self.EDIT if value else self.CREATE
        if not value:  # Create
            self.un_highlight()
            self.de_select_shape()
        self.prev_point = QPointF()
        self.repaint()

    def un_highlight(self, shape=None):
        if shape == None or shape == self.h_shape:
            if self.h_shape:
                self.h_shape.highlight_clear()
            self.h_vertex = self.h_shape = None

    def selected_vertex(self):
        return self.h_vertex is not None

    def mouseMoveEvent(self, ev):
        """Update line with last point and current coordinates."""
        pos = self.transform_pos(ev.pos())

        # Update coordinates in status bar if image is opened
        window = self.parent().window()
        if window.file_path is not None:
            self.parent().window().label_coordinates.setText(
                'X: %d; Y: %d' % (pos.x(), pos.y()))

        # Polygon drawing.
        if self.drawing():
            self.override_cursor(CURSOR_DRAW)
            if self.current:
                # Display annotation width and height while drawing
                current_width = abs(self.current[0].x() - pos.x())
                current_height = abs(self.current[0].y() - pos.y())
                self.parent().window().label_coordinates.setText(
                        'Width: %d, Height: %d / X: %d; Y: %d' % (current_width, current_height, pos.x(), pos.y()))

                color = self.drawing_line_color
                if self.out_of_pixmap(pos):
                    # Don't allow the user to draw outside the pixmap.
                    # Clip the coordinates to 0 or max,
                    # if they are outside the range [0, max]
                    size = self.pixmap.size()
                    clipped_x = min(max(0, pos.x()), size.width())
                    clipped_y = min(max(0, pos.y()), size.height())
                    pos = QPointF(clipped_x, clipped_y)
                elif len(self.current) > 1 and self.close_enough(pos, self.current[0]):
                    # Attract line to starting point and colorise to alert the
                    # user:
                    pos = self.current[0]
                    color = self.current.line_color
                    self.override_cursor(CURSOR_POINT)
                    self.current.highlight_vertex(0, Shape.NEAR_VERTEX)

                if self.draw_square:
                    init_pos = self.current[0]
                    min_x = init_pos.x()
                    min_y = init_pos.y()
                    min_size = min(abs(pos.x() - min_x), abs(pos.y() - min_y))
                    direction_x = -1 if pos.x() - min_x < 0 else 1
                    direction_y = -1 if pos.y() - min_y < 0 else 1
                    self.line[1] = QPointF(min_x + direction_x * min_size, min_y + direction_y * min_size)
                else:
                    self.line[1] = pos

                self.line.line_color = color
                self.prev_point = QPointF()
                self.current.highlight_clear()
            else:
                self.prev_point = pos
            self.repaint()
            return

        # Polygon copy moving.
        if Qt.RightButton & ev.buttons():
            if self.selected_shape_copy and self.prev_point:
                self.override_cursor(CURSOR_MOVE)
                self.bounded_move_shape(self.selected_shape_copy, pos)
                self.repaint()
            elif self.selected_shapes:
                # Create a copy of the first selected shape
                self.selected_shape_copy = self.selected_shapes[0].copy() if self.selected_shapes else None
                self.repaint()
            return

        # Selection box drawing
        if self.selection_box_enabled and Qt.LeftButton & ev.buttons():
            self.selection_box_end = pos
            self.update()
            return

        # Polygon/Vertex moving.
        if Qt.LeftButton & ev.buttons():
            if self.selected_vertex():
                self.bounded_move_vertex(pos)
                self.shapeMoved.emit()
                self.repaint()

                # Display annotation width and height while moving vertex
                point1 = self.h_shape[1]
                point3 = self.h_shape[3]
                current_width = abs(point1.x() - point3.x())
                current_height = abs(point1.y() - point3.y())
                self.parent().window().label_coordinates.setText(
                        'Width: %d, Height: %d / X: %d; Y: %d' % (current_width, current_height, pos.x(), pos.y()))
            elif self.selected_shapes and self.prev_point:
                self.override_cursor(CURSOR_MOVE)
                # Use the first selected shape for bounded_move_shape
                # The method will handle moving all selected shapes if needed
                if self.selected_shapes:
                    self.bounded_move_shape(self.selected_shapes[0], pos)
                self.shapeMoved.emit()
                self.repaint()

                # Display annotation width and height while moving shape
                # Use the first selected shape for display
                if self.selected_shapes:
                    point1 = self.selected_shapes[0][1]
                    point3 = self.selected_shapes[0][3]
                    current_width = abs(point1.x() - point3.x())
                    current_height = abs(point1.y() - point3.y())
                    self.parent().window().label_coordinates.setText(
                            'Width: %d, Height: %d / X: %d; Y: %d' % (current_width, current_height, pos.x(), pos.y()))
            else:
                # pan
                delta = ev.pos() - self.pan_initial_pos
                self.scrollRequest.emit(delta.x(), Qt.Horizontal)
                self.scrollRequest.emit(delta.y(), Qt.Vertical)
                self.update()
            return

        # Just hovering over the canvas, 2 possibilities:
        # - Highlight shapes
        # - Highlight vertex
        # Update shape/vertex fill and tooltip value accordingly.
        self.setToolTip("Image")
        priority_list = self.shapes + ([self.selected_shape] if self.selected_shape else [])
        for shape in reversed([s for s in priority_list if self.isVisible(s)]):
            # Look for a nearby vertex to highlight. If that fails,
            # check if we happen to be inside a shape.
            index = shape.nearest_vertex(pos, self.epsilon)
            if index is not None:
                if self.selected_vertex():
                    self.h_shape.highlight_clear()
                self.h_vertex, self.h_shape = index, shape
                shape.highlight_vertex(index, shape.MOVE_VERTEX)
                self.override_cursor(CURSOR_POINT)
                self.setToolTip("Click & drag to move point")
                self.setStatusTip(self.toolTip())
                self.update()
                break
            elif shape.contains_point(pos):
                if self.selected_vertex():
                    self.h_shape.highlight_clear()
                self.h_vertex, self.h_shape = None, shape
                self.setToolTip(
                    "Click & drag to move shape '%s'" % shape.label)
                self.setStatusTip(self.toolTip())
                self.override_cursor(CURSOR_GRAB)
                self.update()

                # Display annotation width and height while hovering inside
                point1 = self.h_shape[1]
                point3 = self.h_shape[3]
                current_width = abs(point1.x() - point3.x())
                current_height = abs(point1.y() - point3.y())
                self.parent().window().label_coordinates.setText(
                        'Width: %d, Height: %d / X: %d; Y: %d' % (current_width, current_height, pos.x(), pos.y()))
                break
        else:  # Nothing found, clear highlights, reset state.
            if self.h_shape:
                self.h_shape.highlight_clear()
                self.update()
            self.h_vertex, self.h_shape = None, None
            self.override_cursor(CURSOR_DEFAULT)

    def mousePressEvent(self, ev):
        pos = self.transform_pos(ev.pos())

        if ev.button() == Qt.LeftButton:
            if self.drawing():
                self.handle_drawing(pos)
            else:
                # Check if Shift key is pressed for selection box
                if ev.modifiers() & Qt.ShiftModifier:
                    self.selection_box_enabled = True
                    self.selection_box_start = pos
                    self.selection_box_end = pos
                    self.update()
                else:
                    # Check if Ctrl key is pressed for multi-selection
                    multi_select = ev.modifiers() & Qt.ControlModifier
                    selection = self.select_shape_point(pos, multi_select)
                    self.prev_point = pos
                    
                    # 如果选中了形状，保存移动前的状态
                    if selection and self.selected_shapes:
                        self.save_history_state('move', {'moved_shapes': [shape.copy() for shape in self.selected_shapes]})

                    if selection is None and not multi_select:
                        # pan
                        QApplication.setOverrideCursor(QCursor(Qt.OpenHandCursor))
                        self.pan_initial_pos = ev.pos()

        elif ev.button() == Qt.RightButton and self.editing():
            # Right click doesn't support multi-select
            self.select_shape_point(pos)
            self.prev_point = pos
        self.update()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.LeftButton and self.selection_box_enabled:
            # Finish selection box
            self.finish_selection_box()
            self.selection_box_enabled = False
            self.update()
            return
            
        if ev.button() == Qt.RightButton:
            menu = self.menus[bool(self.selected_shape_copy)]
            self.restore_cursor()
            if not menu.exec_(self.mapToGlobal(ev.pos()))\
               and self.selected_shape_copy:
                # Cancel the move by deleting the shadow copy.
                self.selected_shape_copy = None
                self.repaint()
        elif ev.button() == Qt.LeftButton and self.selected_shapes:
            if self.selected_vertex():
                self.override_cursor(CURSOR_POINT)
            else:
                self.override_cursor(CURSOR_GRAB)
        elif ev.button() == Qt.LeftButton:
            pos = self.transform_pos(ev.pos())
            if self.drawing():
                self.handle_drawing(pos)
            else:
                # pan
                QApplication.restoreOverrideCursor()

    def finish_selection_box(self):
        """Select all shapes within the selection box."""
        # Create selection rectangle
        min_x = min(self.selection_box_start.x(), self.selection_box_end.x())
        max_x = max(self.selection_box_start.x(), self.selection_box_end.x())
        min_y = min(self.selection_box_start.y(), self.selection_box_end.y())
        max_y = max(self.selection_box_start.y(), self.selection_box_end.y())
        
        selection_rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
        
        # Clear current selection
        self.de_select_shape()
        
        # Select shapes that intersect with the selection box
        for shape in self.shapes:
            if self.isVisible(shape) and self.shape_intersects_rect(shape, selection_rect):
                self.select_shape(shape, multi_select=True)
    
    def shape_intersects_rect(self, shape, rect):
        """Check if a shape intersects with a rectangle."""
        shape_rect = shape.bounding_rect()
        return rect.intersects(shape_rect)

    def end_move(self, copy=False):
        assert self.selected_shapes and self.selected_shape_copy
        shape = self.selected_shape_copy
        # del shape.fill_color
        # del shape.line_color
        if copy:
            self.shapes.append(shape)
            # Deselect all shapes
            for s in self.selected_shapes:
                s.selected = False
            self.selected_shapes = [shape]
            self._selected_shape = shape
            shape.selected = True
            self.repaint()
        else:
            # Only move the first selected shape
            if self.selected_shapes:
                self.selected_shapes[0].points = [p for p in shape.points]
        self.selected_shape_copy = None

    def hide_background_shapes(self, value):
        self.hide_background = value
        if self.selected_shapes:
            # Only hide other shapes if there is a current selection.
            # Otherwise the user will not be able to select a shape.
            self.set_hiding(True)
            self.repaint()

    def handle_drawing(self, pos):
        if self.current and self.current.reach_max_points() is False:
            init_pos = self.current[0]
            min_x = init_pos.x()
            min_y = init_pos.y()
            target_pos = self.line[1]
            max_x = target_pos.x()
            max_y = target_pos.y()
            self.current.add_point(QPointF(max_x, min_y))
            self.current.add_point(target_pos)
            self.current.add_point(QPointF(min_x, max_y))
            self.finalise()
        elif not self.out_of_pixmap(pos):
            self.current = Shape()
            self.current.add_point(pos)
            self.line.points = [pos, pos]
            self.set_hiding()
            self.drawingPolygon.emit(True)
            self.update()

    def set_hiding(self, enable=True):
        self._hide_background = self.hide_background if enable else False

    def can_close_shape(self):
        return self.drawing() and self.current and len(self.current) > 2

    def mouseDoubleClickEvent(self, ev):
        # We need at least 4 points here, since the mousePress handler
        # adds an extra one before this handler is called.
        if self.can_close_shape() and len(self.current) > 3:
            self.current.pop_point()
            self.finalise()

    @property
    def selected_shape(self):
        """For backward compatibility. Returns the first selected shape."""
        return self._selected_shape
        
    @selected_shape.setter
    def selected_shape(self, shape):
        """For backward compatibility. Sets the first selected shape."""
        self.selected_shapes = [shape] if shape else []
        self._selected_shape = shape
        
    def select_shape(self, shape, multi_select=False):
        """Select shape. If multi_select is True, add to selection instead of replacing."""
        if not multi_select:
            self.de_select_shape()
        
        if shape not in self.selected_shapes:
            shape.selected = True
            self.selected_shapes.append(shape)
            self._selected_shape = self.selected_shapes[0] if self.selected_shapes else None
            self.set_hiding()
            self.selectionChanged.emit(bool(self.selected_shapes))
            self.update()

    def select_shape_point(self, point, multi_select=False):
        """Select the first shape created which contains this point."""
        if not multi_select:
            self.de_select_shape()
            
        if self.selected_vertex():  # A vertex is marked for selection.
            index, shape = self.h_vertex, self.h_shape
            shape.highlight_vertex(index, shape.MOVE_VERTEX)
            self.select_shape(shape, multi_select)
            return self.h_vertex
            
        for shape in reversed(self.shapes):
            if self.isVisible(shape) and shape.contains_point(point):
                # If multi-selecting and shape is already selected, deselect it
                if multi_select and shape in self.selected_shapes:
                    self.de_select_shape(shape)
                else:
                    self.select_shape(shape, multi_select)
                    self.calculate_offsets(shape, point)
                return shape if shape in self.selected_shapes else None
        return None

    def calculate_offsets(self, shape, point):
        rect = shape.bounding_rect()
        x1 = rect.x() - point.x()
        y1 = rect.y() - point.y()
        x2 = (rect.x() + rect.width()) - point.x()
        y2 = (rect.y() + rect.height()) - point.y()
        self.offsets = QPointF(x1, y1), QPointF(x2, y2)

    def snap_point_to_canvas(self, x, y):
        """
        Moves a point x,y to within the boundaries of the canvas.
        :return: (x,y,snapped) where snapped is True if x or y were changed, False if not.
        """
        if x < 0 or x > self.pixmap.width() or y < 0 or y > self.pixmap.height():
            x = max(x, 0)
            y = max(y, 0)
            x = min(x, self.pixmap.width())
            y = min(y, self.pixmap.height())
            return x, y, True

        return x, y, False

    def bounded_move_vertex(self, pos):
        index, shape = self.h_vertex, self.h_shape
        point = shape[index]
        if self.out_of_pixmap(pos):
            size = self.pixmap.size()
            clipped_x = min(max(0, pos.x()), size.width())
            clipped_y = min(max(0, pos.y()), size.height())
            pos = QPointF(clipped_x, clipped_y)

        if self.draw_square:
            opposite_point_index = (index + 2) % 4
            opposite_point = shape[opposite_point_index]

            min_size = min(abs(pos.x() - opposite_point.x()), abs(pos.y() - opposite_point.y()))
            direction_x = -1 if pos.x() - opposite_point.x() < 0 else 1
            direction_y = -1 if pos.y() - opposite_point.y() < 0 else 1
            shift_pos = QPointF(opposite_point.x() + direction_x * min_size - point.x(),
                                opposite_point.y() + direction_y * min_size - point.y())
        else:
            shift_pos = pos - point

        shape.move_vertex_by(index, shift_pos)

        left_index = (index + 1) % 4
        right_index = (index + 3) % 4
        left_shift = None
        right_shift = None
        if index % 2 == 0:
            right_shift = QPointF(shift_pos.x(), 0)
            left_shift = QPointF(0, shift_pos.y())
        else:
            left_shift = QPointF(shift_pos.x(), 0)
            right_shift = QPointF(0, shift_pos.y())
        shape.move_vertex_by(right_index, right_shift)
        shape.move_vertex_by(left_index, left_shift)

    def bounded_move_shape(self, shape, pos):
        if self.out_of_pixmap(pos):
            return False  # No need to move
        o1 = pos + self.offsets[0]
        if self.out_of_pixmap(o1):
            pos -= QPointF(min(0, o1.x()), min(0, o1.y()))
        o2 = pos + self.offsets[1]
        if self.out_of_pixmap(o2):
            pos += QPointF(min(0, self.pixmap.width() - o2.x()),
                           min(0, self.pixmap.height() - o2.y()))
        # The next line tracks the new position of the cursor
        # relative to the shape, but also results in making it
        # a bit "shaky" when nearing the border and allows it to
        # go outside of the shape's area for some reason. XXX
        # self.calculateOffsets(self.selectedShape, pos)
        dp = pos - self.prev_point
        if dp:
            # If this is one of the selected shapes and we have multiple shapes selected,
            # move all selected shapes
            if shape.selected and len(self.selected_shapes) > 1 and shape in self.selected_shapes:
                for s in self.selected_shapes:
                    s.move_by(dp)
            else:
                shape.move_by(dp)
                
            self.prev_point = pos
            return True
        return False

    def de_select_shape(self, shape=None):
        """Deselect shape. If shape is None, deselect all shapes."""
        if shape is None:
            for shape in self.selected_shapes:
                shape.selected = False
            self.selected_shapes = []
            self._selected_shape = None
            self.set_hiding(False)
            self.selectionChanged.emit(False)
            self.update()
        elif shape in self.selected_shapes:
            shape.selected = False
            self.selected_shapes.remove(shape)
            self._selected_shape = self.selected_shapes[0] if self.selected_shapes else None
            self.selectionChanged.emit(bool(self.selected_shapes))
            self.update()

    def delete_selected(self):
        if not self.selected_shapes:
            return None
        
        # 保存删除前的状态
        self.save_history_state('delete', {'deleted_shapes': [shape.copy() for shape in self.selected_shapes]})
            
        deleted_shapes = []
        for shape in self.selected_shapes.copy():  # Use copy to safely iterate while removing
            self.un_highlight(shape)
            self.shapes.remove(shape)
            deleted_shapes.append(shape)
            
        self.selected_shapes = []
        self._selected_shape = None
        self.update()
        return deleted_shapes

    def copy_selected_shape(self):
        if not self.selected_shapes:
            return
        
        # 保存复制前的状态
        self.save_history_state('copy', {'copied_shapes': [shape.copy() for shape in self.selected_shapes]})
            
        copied_shapes = []
        for shape in self.selected_shapes:
            copied_shape = shape.copy()
            self.shapes.append(copied_shape)
            copied_shape.selected = True
            copied_shapes.append(copied_shape)
            
        self.de_select_shape()  # Deselect all shapes
        
        # Select all copied shapes
        self.selected_shapes = copied_shapes
        if copied_shapes:  # For backward compatibility
            self._selected_shape = copied_shapes[0]
            self.bounded_shift_shape(self._selected_shape)
            
        self.update()
        return copied_shapes
    
    def copy_selected_to_clipboard(self):
        """Copy selected shapes to global clipboard for cross-image paste"""
        global GLOBAL_CLIPBOARD
        if not self.selected_shapes:
            return False
        
        # Clear previous clipboard content
        GLOBAL_CLIPBOARD = []
        
        # Copy selected shapes to clipboard
        for shape in self.selected_shapes:
            shape_data = {
                'label': shape.label,
                'points': [QPointF(p.x(), p.y()) for p in shape.points],
                'line_color': shape.line_color,
                'fill_color': shape.fill_color,
                'difficult': shape.difficult,
                'paint_label': shape.paint_label
            }
            GLOBAL_CLIPBOARD.append(shape_data)
        
        return True
    
    def paste_from_clipboard(self):
        """Paste shapes from global clipboard to current image"""
        global GLOBAL_CLIPBOARD
        if not GLOBAL_CLIPBOARD:
            return []
        
        # Save state before pasting
        self.save_history_state('paste')
        
        pasted_shapes = []
        offset = QPointF(0, 0)  # Default offset for pasted shapes
        
        # Clear current selection
        self.de_select_shape()
        
        for shape_data in GLOBAL_CLIPBOARD:
            # Create new shape from clipboard data
            new_shape = Shape(label=shape_data['label'])
            
            # Copy points with offset
            for point in shape_data['points']:
                new_shape.points.append(QPointF(point.x() + offset.x(), point.y() + offset.y()))
            
            # Copy other properties
            new_shape.line_color = shape_data['line_color']
            new_shape.fill_color = shape_data['fill_color']
            new_shape.difficult = shape_data['difficult']
            new_shape.paint_label = shape_data['paint_label']
            new_shape.close()
            
            # Add to canvas
            self.shapes.append(new_shape)
            new_shape.selected = True
            pasted_shapes.append(new_shape)
        
        # Select all pasted shapes
        self.selected_shapes = pasted_shapes
        if pasted_shapes:
            self._selected_shape = pasted_shapes[0]
        
        self.update()
        return pasted_shapes

    def bounded_shift_shape(self, shape):
        # No offset for copied shapes - keep them in the same position
        point = shape[0]
        offset = QPointF(0.0, 0.0)  # 去掉复制后偏移 Changed from (2.0, 2.0) to (0.0, 0.0)
        self.calculate_offsets(shape, point)
        self.prev_point = point
        if self.bounded_move_shape(shape, point - offset):
            return
        self.bounded_move_shape(shape, point + offset)

    def paintEvent(self, event):
        if not self.pixmap:
            return super(Canvas, self).paintEvent(event)

        p = self._painter
        p.begin(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        p.scale(self.scale, self.scale)
        p.translate(self.offset_to_center())

        temp = self.pixmap
        if self.overlay_color:
            temp = QPixmap(self.pixmap)
            painter = QPainter(temp)
            painter.setCompositionMode(painter.CompositionMode_Overlay)
            painter.fillRect(temp.rect(), self.overlay_color)
            painter.end()

        p.drawPixmap(0, 0, temp)
        Shape.scale = self.scale
        Shape.label_font_size = self.label_font_size
        for shape in self.shapes:
            if (shape.selected or not self._hide_background) and self.isVisible(shape):
                shape.fill = shape.selected or shape == self.h_shape
                shape.paint(p)
        if self.current:
            self.current.paint(p)
            self.line.paint(p)
        if self.selected_shape_copy:
            self.selected_shape_copy.paint(p)

        # Paint rect
        if self.current is not None and len(self.line) == 2:
            left_top = self.line[0]
            right_bottom = self.line[1]
            rect_width = right_bottom.x() - left_top.x()
            rect_height = right_bottom.y() - left_top.y()
            p.setPen(self.drawing_rect_color)
            brush = QBrush(Qt.BDiagPattern)
            p.setBrush(brush)
            p.drawRect(int(left_top.x()), int(left_top.y()), int(rect_width), int(rect_height))

        # Paint selection box
        if self.selection_box_enabled:
            min_x = min(self.selection_box_start.x(), self.selection_box_end.x())
            max_x = max(self.selection_box_start.x(), self.selection_box_end.x())
            min_y = min(self.selection_box_start.y(), self.selection_box_end.y())
            max_y = max(self.selection_box_start.y(), self.selection_box_end.y())
            
            selection_rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
            
            # Draw selection box with dashed line
            pen = QPen(QColor(0, 120, 215), 2)
            pen.setStyle(Qt.DashLine)
            p.setPen(pen)
            
            # Draw selection box with semi-transparent fill
            brush = QBrush(QColor(0, 120, 215, 50))
            p.setBrush(brush)
            p.drawRect(selection_rect)

        if self.drawing() and not self.prev_point.isNull() and not self.out_of_pixmap(self.prev_point):
            p.setPen(QColor(0, 0, 0))
            p.drawLine(int(self.prev_point.x()), 0, int(self.prev_point.x()), int(self.pixmap.height()))
            p.drawLine(0, int(self.prev_point.y()), int(self.pixmap.width()), int(self.prev_point.y()))

        self.setAutoFillBackground(True)
        if self.verified:
            pal = self.palette()
            pal.setColor(self.backgroundRole(), QColor(184, 239, 38, 128))
            self.setPalette(pal)
        else:
            pal = self.palette()
            pal.setColor(self.backgroundRole(), QColor(232, 232, 232, 255))
            self.setPalette(pal)

        p.end()

    def transform_pos(self, point):
        """Convert from widget-logical coordinates to painter-logical coordinates."""
        return point / self.scale - self.offset_to_center()

    def offset_to_center(self):
        s = self.scale
        area = super(Canvas, self).size()
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPointF(x, y)

    def out_of_pixmap(self, p):
        w, h = self.pixmap.width(), self.pixmap.height()
        return not (0 <= p.x() <= w and 0 <= p.y() <= h)

    def finalise(self):
        assert self.current
        if self.current.points[0] == self.current.points[-1]:
            self.current = None
            self.drawingPolygon.emit(False)
            self.update()
            return

        self.current.close()
        self.shapes.append(self.current)
        self.current = None
        self.set_hiding(False)
        self.newShape.emit()
        self.update()

    def close_enough(self, p1, p2):
        # d = distance(p1 - p2)
        # m = (p1-p2).manhattanLength()
        # print "d %.2f, m %d, %.2f" % (d, m, d - m)
        return distance(p1 - p2) < self.epsilon

    # These two, along with a call to adjustSize are required for the
    # scroll area.
    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self.pixmap:
            return self.scale * self.pixmap.size()
        return super(Canvas, self).minimumSizeHint()

    def wheelEvent(self, ev):
        qt_version = 4 if hasattr(ev, "delta") else 5
        if qt_version == 4:
            if ev.orientation() == Qt.Vertical:
                v_delta = ev.delta()
                h_delta = 0
            else:
                h_delta = ev.delta()
                v_delta = 0
        else:
            delta = ev.angleDelta()
            h_delta = delta.x()
            v_delta = delta.y()

        mods = ev.modifiers()
        if int(Qt.ControlModifier) | int(Qt.ShiftModifier) == int(mods) and v_delta:
            self.lightRequest.emit(v_delta)
        elif Qt.ControlModifier == int(mods) and v_delta:
            self.zoomRequest.emit(v_delta)
        else:
            v_delta and self.scrollRequest.emit(v_delta, Qt.Vertical)
            h_delta and self.scrollRequest.emit(h_delta, Qt.Horizontal)
        ev.accept()

    def keyPressEvent(self, ev):
        key = ev.key()
        if key == Qt.Key_Escape:
            if self.current:
                print('ESC press')
                self.current = None
                self.drawingPolygon.emit(False)
                self.update()
            elif self.drawing():
                # 绘制状态喜下，Esc则取消 Cancel creation mode when ESC is pressed in CREATE mode
                print('ESC press - Cancel creation mode')
                self.set_editing(True)
                # Re-enable create action for beginner mode
                window = self.parent().window()
                if hasattr(window, 'actions') and hasattr(window.actions, 'create'):
                    window.actions.create.setEnabled(True)
                self.update()
        elif key == Qt.Key_Return and self.can_close_shape():
            self.finalise()
        elif key == Qt.Key_Left and self.selected_shapes:
            self.move_one_pixel('Left')
        elif key == Qt.Key_Right and self.selected_shapes:
            self.move_one_pixel('Right')
        elif key == Qt.Key_Up and self.selected_shapes:
            self.move_one_pixel('Up')
        elif key == Qt.Key_Down and self.selected_shapes:
            self.move_one_pixel('Down')

    def move_one_pixel(self, direction):
        if not self.selected_shapes:
            return
            
        # Check if any selected shape would move out of bounds
        move_out_of_bounds = False
        offset = None
        
        if direction == 'Left':
            offset = QPointF(-1.0, 0)
        elif direction == 'Right':
            offset = QPointF(1.0, 0)
        elif direction == 'Up':
            offset = QPointF(0, -1.0)
        elif direction == 'Down':
            offset = QPointF(0, 1.0)
            
        if offset is None:
            return
            
        # Check if any shape would move out of bounds
        for shape in self.selected_shapes:
            points = [p + offset for p in shape.points]
            if any(self.out_of_pixmap(p) for p in points):
                move_out_of_bounds = True
                break
                
        if not move_out_of_bounds:
            # Move all selected shapes
            for shape in self.selected_shapes:
                for i in range(len(shape.points)):
                    shape.points[i] += offset
                    
            self.shapeMoved.emit()
            self.repaint()

    def move_out_of_bound(self, step):
        if not self.selected_shapes:
            return False
            
        # For backward compatibility, check if we're using the old selected_shape property
        if self._selected_shape is not None:
            points = [p1 + p2 for p1, p2 in zip(self._selected_shape.points, [step] * 4)]
            return True in map(self.out_of_pixmap, points)
            
        # Check all selected shapes
        for shape in self.selected_shapes:
            points = [p1 + p2 for p1, p2 in zip(shape.points, [step] * 4)]
            if True in map(self.out_of_pixmap, points):
                return True
                
        return False

    def set_last_label(self, text, line_color=None, fill_color=None):
        assert text
        self.shapes[-1].label = text
        if line_color:
            self.shapes[-1].line_color = line_color

        if fill_color:
            self.shapes[-1].fill_color = fill_color

        return self.shapes[-1]

    def undo_last_line(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.set_open()
        self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)

    def reset_all_lines(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.set_open()
        self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)
        self.current = None
        self.drawingPolygon.emit(False)
        self.update()

    def load_pixmap(self, pixmap):
        self.pixmap = pixmap
        self.shapes = []
        self.repaint()

    def load_shapes(self, shapes):
        self.shapes = list(shapes)
        self.current = None
        self.repaint()

    def set_shape_visible(self, shape, value):
        self.visible[shape] = value
        self.repaint()

    def current_cursor(self):
        cursor = QApplication.overrideCursor()
        if cursor is not None:
            cursor = cursor.shape()
        return cursor

    def override_cursor(self, cursor):
        self._cursor = cursor
        if self.current_cursor() is None:
            QApplication.setOverrideCursor(cursor)
        else:
            QApplication.changeOverrideCursor(cursor)

    def restore_cursor(self):
        QApplication.restoreOverrideCursor()

    def reset_state(self):
        self.de_select_shape()
        self.un_highlight()
        self.selected_shape_copy = None

        self.restore_cursor()
        self.pixmap = None
        self.update()

    def set_drawing_shape_to_square(self, status):
        self.draw_square = status
    
    def save_history_state(self, action_type, data=None):
        """保存当前状态到历史记录"""
        # 深拷贝当前所有形状
        shapes_copy = []
        for shape in self.shapes:
            shape_copy = shape.copy()
            shapes_copy.append(shape_copy)
        
        history_item = {
            'action': action_type,
            'shapes': shapes_copy,
            'data': data
        }
        
        self.history.append(history_item)
        
        # 限制历史记录大小
        if len(self.history) > self.max_history_size:
            self.history.pop(0)
    
    def undo(self):
        """撤销上一个操作"""
        if not self.history:
            return False
        
        # 获取上一个状态
        last_state = self.history.pop()
        
        # 恢复形状列表
        self.shapes = []
        for shape in last_state['shapes']:
            shape_copy = shape.copy()
            self.shapes.append(shape_copy)
        
        # 清除选择状态
        self.de_select_shape()
        self.un_highlight()
        
        # 更新显示
        self.update()
        return True
    
    def clear_history(self):
        """清空历史记录"""
        self.history = []
    
    def clear_all_shapes(self):
        """清空当前图片的所有形状"""
        if not self.shapes:
            return False
        
        # 保存清空前的状态
        self.save_history_state('clear_all')
        
        # 清空所有形状
        self.shapes = []
        self.de_select_shape()
        self.un_highlight()
        
        # 更新显示
        self.update()
        return True
