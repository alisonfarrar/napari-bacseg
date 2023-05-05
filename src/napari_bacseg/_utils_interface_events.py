import os
import tempfile
import traceback

import cv2
import numpy as np
from napari.utils.notifications import show_info


def find_contours(img):
    # finds contours of shapes, only returns the external contours of the shapes
    contours, hierarchy = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    return contours


def fill_holes(mask, colour):
    try:
        fill_mask = mask.copy()
        fill_mask[fill_mask != colour] = 0
        fill_mask[fill_mask == colour] == 255
        fill_mask = fill_mask.astype(np.uint8)

        cnt = find_contours(fill_mask.astype(np.uint8))
        cv2.drawContours(fill_mask, [cnt[0]], -1, 255, -1)

        mask[fill_mask == 255] = colour

    except:
        pass

    return mask


def _segmentationEvents(self, viewer, event):
    try:
        if "Control" in event.modifiers:
            self._modifyMode(mode="delete")

        if "Shift" in event.modifiers:
            self._modifyMode(mode="add")

        if self.interface_mode == "segment":
            # add segmentation
            if self.segmentation_mode in ["add", "extend"]:
                self.segLayer.mode = "paint"
                self.segLayer.brush_size = 1

                stored_mask = self.segLayer.data.copy()
                stored_class = self.classLayer.data.copy()
                meta = self.segLayer.metadata.copy()

                if self.segmentation_mode == "add":
                    new_colour = _newSegColour(self)
                else:
                    data_coordinates = self.segLayer.world_to_data(event.position)
                    coord = np.round(data_coordinates).astype(int)
                    new_colour = self.segLayer.get_value(coord)

                    self.segLayer.selected_label = new_colour
                    new_colour = self.segLayer.get_value(coord)

                    new_class = self.classLayer.get_value(coord)

                    if new_class != None:
                        self.class_colour = new_class

                dragged = False
                coordinates = []

                yield

                # # on move
                while event.type == "mouse_move":
                    coordinates.append(event.position)
                    dragged = True
                    yield

                # on release
                if dragged:
                    if (new_colour != 0 and new_colour != None and self.class_colour != None):
                        coordinates = np.round(np.array(coordinates)).astype(np.int32)

                        mask_dim = tuple(list(coordinates[0][:-2]) + [...])

                        cnt = coordinates[:, -2:]

                        cnt = np.fliplr(cnt)
                        cnt = cnt.reshape((-1, 1, 2))

                        seg_stack = self.segLayer.data

                        seg_mask = seg_stack[mask_dim]

                        cv2.drawContours(seg_mask, [cnt], -1, int(new_colour), -1)

                        seg_mask = fill_holes(seg_mask, new_colour)

                        seg_stack[mask_dim] = seg_mask

                        self.segLayer.data = seg_stack

                        # update class

                        class_stack = self.classLayer.data
                        class_colour = self.class_colour
                        seg_stack = self.segLayer.data

                        seg_mask = seg_stack[mask_dim]
                        class_mask = class_stack[mask_dim]

                        class_mask[seg_mask == int(new_colour)] = class_colour
                        class_stack[mask_dim] = class_mask

                        self.classLayer.data = class_stack

                        # update metadata

                        meta["manual_segmentation"] = True
                        self.segLayer.metadata = meta
                        self.segLayer.mode = "pan_zoom"
                        self.update_image_folds()

                    else:
                        self.segLayer.data = stored_mask
                        self.classLayer.data = stored_class
                        self.segLayer.mode = "pan_zoom"

            # join segmentations
            if self.segmentation_mode == "join":
                self.segLayer.mode = "paint"
                self.segLayer.brush_size = 1

                stored_mask = self.segLayer.data.copy()
                stored_class = self.classLayer.data.copy()
                meta = self.segLayer.metadata.copy()

                data_coordinates = self.segLayer.world_to_data(event.position)
                coord = np.round(data_coordinates).astype(int)
                new_colour = self.segLayer.get_value(coord)

                self.segLayer.selected_label = new_colour
                new_colour = self.segLayer.get_value(coord)

                new_class = self.classLayer.get_value(coord)

                if new_class != None:
                    self.class_colour = new_class

                dragged = False
                colours = []
                classes = []
                coords = []
                yield

                # on move
                while event.type == "mouse_move":
                    data_coordinates = self.segLayer.world_to_data(event.position)
                    coord = np.round(data_coordinates).astype(int)
                    mask_val = self.segLayer.get_value(coord)
                    class_val = self.classLayer.get_value(coord)
                    colours.append(mask_val)
                    classes.append(class_val)
                    coords.append(coord)
                    dragged = True
                    yield

                # on release
                if dragged:
                    colours = np.array(colours)
                    colours = np.unique(colours)
                    colours = np.delete(colours, np.where(colours == 0))

                    if new_colour in colours:
                        colours = np.delete(colours, np.where(colours == new_colour))

                    if (len(colours) == 1 and new_colour not in colours and new_colour != None):
                        mask_stack = self.segLayer.data

                        mask_dim = tuple(list(coords[0][:-2]) + [...])

                        mask = mask_stack[mask_dim]

                        mask[mask == colours[0]] = new_colour

                        mask = fill_holes(mask, new_colour)

                        mask_stack[mask_dim] = mask

                        self.segLayer.data = mask_stack

                        # update class

                        class_stack = self.classLayer.data
                        seg_stack = self.segLayer.data

                        seg_mask = seg_stack[mask_dim]
                        class_mask = class_stack[mask_dim]

                        class_mask[seg_mask == new_colour] = 2
                        class_stack[mask_dim] = class_mask

                        self.classLayer.data = class_stack

                        # update metadata

                        meta["manual_segmentation"] = True
                        self.segLayer.metadata = meta
                        self.segLayer.mode = "pan_zoom"
                        self.update_image_folds()

                    else:
                        self.segLayer.data = stored_mask
                        self.classLayer.data = stored_class
                        self.segLayer.mode = "pan_zoom"

            # split segmentations
            if self.segmentation_mode == "split":
                self.segLayer.mode = "paint"
                self.segLayer.brush_size = 1

                new_colour = _newSegColour(self)
                stored_mask = self.segLayer.data.copy()
                stored_class = self.classLayer.data
                meta = self.segLayer.metadata.copy()

                dragged = False
                colours = []
                yield

                # on move
                while event.type == "mouse_move":
                    data_coordinates = self.segLayer.world_to_data(event.position)
                    coords = np.round(data_coordinates).astype(int)
                    mask_val = self.segLayer.get_value(coords)
                    colours.append(mask_val)
                    dragged = True
                    yield

                # on release
                if dragged:
                    colours = np.array(colours)
                    colours = np.delete(colours, np.where(colours == new_colour))

                    colours[colours == None] = 0

                    num_colours = len(np.unique(colours))

                    if num_colours == 2 or num_colours == 3:
                        if num_colours == 2:
                            maskref = colours[colours != 0][0]
                        else:
                            maskref = sorted(set(colours.tolist()), key=lambda x: colours.tolist().index(x), )[1]

                        bisection = (colours[0] != maskref and colours[-1] != maskref)

                        if bisection and new_colour != None:
                            mask_dim = tuple(list(coords[:-2]) + [...])
                            shape_mask = stored_mask[mask_dim].copy()

                            class_mask = stored_class[mask_dim].copy()
                            class_mask[shape_mask == maskref] = 3
                            stored_class[mask_dim] = class_mask
                            self.classLayer.data = stored_class

                            shape_mask[shape_mask != maskref] = 0
                            shape_mask[shape_mask == maskref] = 255
                            shape_mask = shape_mask.astype(np.uint8)

                            line_mask = self.segLayer.data.copy()
                            line_mask = line_mask[mask_dim]
                            line_mask[line_mask != new_colour] = 0
                            line_mask[line_mask == new_colour] = 255
                            line_mask = line_mask.astype(np.uint8)

                            overlap = cv2.bitwise_and(shape_mask, line_mask)

                            shape_mask_split = cv2.bitwise_xor(shape_mask, overlap).astype(np.uint8)

                            # update labels layers with split shape
                            split_mask = stored_mask[mask_dim]
                            split_mask[overlap == 255] = new_colour
                            stored_mask[mask_dim] = split_mask
                            self.segLayer.data = stored_mask

                            # fill one have of the split shape with the new colour
                            indices = np.where(shape_mask_split == 255)
                            split_dim = list(list(mask_dim[:-1]) + [indices[0][0], indices[1][0]])
                            split_dim = np.array(split_dim).flatten().tolist()

                            self.segLayer.fill(split_dim, new_colour)

                            meta["manual_segmentation"] = True
                            self.segLayer.metadata = meta
                            self.segLayer.mode = "pan_zoom"
                            self.update_image_folds()

                        else:
                            self.segLayer.data = stored_mask
                            self.segLayer.mode = "pan_zoom"
                    else:
                        self.segLayer.data = stored_mask
                        self.segLayer.mode = "pan_zoom"
                else:
                    self.segLayer.data = stored_mask
                    self.segLayer.mode = "pan_zoom"

            # delete segmentations
            if self.segmentation_mode == "delete":
                self.segLayer.mode = "paint"
                self.segLayer.brush_size = 1

                new_colour = _newSegColour(self)
                stored_mask = self.segLayer.data.copy()
                stored_class = self.classLayer.data
                meta = self.segLayer.metadata.copy()

                dragged = False
                coordinates = []
                yield

                # on move
                while event.type == "mouse_move":
                    coordinates.append(event.position)
                    dragged = True
                    yield

                # on release
                if dragged:
                    self.segLayer.data = stored_mask

                    coordinates = np.round(np.array(coordinates)).astype(np.int32)
                    cnt = coordinates[:, -2:]

                    cnt = np.fliplr(cnt)
                    cnt = cnt.reshape((-1, 1, 2))

                    mask_dim = tuple(list(coordinates[0][:-2]) + [...])

                    seg_stack = self.segLayer.data.copy()
                    class_stack = self.classLayer.data.copy()

                    seg_mask = seg_stack[mask_dim]
                    class_mask = class_stack[mask_dim]

                    delete_mask = np.zeros_like(seg_mask)
                    cv2.drawContours(delete_mask, [cnt], -1, 255, -1)

                    delete_colours = np.unique(seg_mask[delete_mask == 255])

                    for colour in delete_colours:
                        seg_mask[seg_mask == colour] = 0

                    class_mask[seg_mask == 0] = 0

                    seg_stack[mask_dim] = seg_mask
                    class_stack[mask_dim] = class_mask

                    self.segLayer.data = seg_stack
                    self.classLayer.data = class_stack

                else:
                    self.segLayer.data = stored_mask
                    self.segLayer.mode = "pan_zoom"
                    self.update_image_folds()

                    meta = self.segLayer.metadata.copy()

                    data_coordinates = self.segLayer.world_to_data(event.position)
                    coord = np.round(data_coordinates).astype(int)
                    mask_val = self.segLayer.get_value(coord)

                    if mask_val != 0:
                        mask_dim = tuple(list(coord[:-2]) + [...])[0]

                        mask_stack = self.segLayer.data
                        class_stack = self.classLayer.data

                        mask = mask_stack[mask_dim]
                        class_mask = class_stack[mask_dim]

                        class_mask[mask == mask_val] = 0
                        mask[mask == mask_val] = 0

                        class_stack[mask_dim] = class_mask
                        mask_stack[mask_dim] = mask

                        self.classLayer.data = class_stack
                        self.segLayer.data = mask_stack

                        # update metadata

                        meta["manual_segmentation"] = True
                        self.segLayer.metadata = meta
                        self.segLayer.mode = "pan_zoom"
                        self.update_image_folds()

            if self.segmentation_mode == "refine":
                layer_names = [layer.name for layer in self.viewer.layers if layer.name not in ["Segmentations", "Classes", "center_lines"]]

                self.segLayer.mode == "pan_zoom"
                self.segLayer.brush_size = 1

                data_coordinates = self.segLayer.world_to_data(event.position)
                coord = np.round(data_coordinates).astype(int)
                mask_id = self.segLayer.get_value(coord)

                self.segLayer.selected_label = mask_id

                if mask_id != 0:
                    current_fov = self.viewer.dims.current_step[0]

                    channel = self.refine_channel.currentText()
                    channel = channel.replace("Mask + ", "")

                    label_stack = self.classLayer.data
                    mask_stack = self.segLayer.data

                    mask = mask_stack[current_fov, :, :].copy()
                    label = label_stack[current_fov, :, :].copy()

                    image = []
                    for layer in layer_names:
                        image.append(self.viewer.layers[layer].data[current_fov])
                    image = np.stack(image, axis=0)

                    cell_mask = np.zeros(mask.shape, dtype=np.uint8)

                    mask[mask != mask_id] = 0
                    cell_mask[mask != mask_id] = 0
                    cell_mask[mask == mask_id] = 1

                    from napari_bacseg._utils_colicoords import (process_colicoords, run_colicoords, )
                    from napari_bacseg._utils_statistics import get_cell_images

                    colicoords_dir = os.path.join(tempfile.gettempdir(), "colicoords")

                    cell_images_path = get_cell_images(self, image, mask, cell_mask, mask_id, layer_names, colicoords_dir, )

                    cell_data = {"cell_images_path": cell_images_path}

                    colicoords_data = run_colicoords(self, cell_data=[cell_data], colicoords_channel=channel, multithreaded=True, )

                    process_colicoords(self, colicoords_data)

        if self.interface_mode == "classify":
            self.segLayer.mode == "pan_zoom"
            self.segLayer.brush_size = 1

            data_coordinates = self.segLayer.world_to_data(event.position)
            coord = np.round(data_coordinates).astype(int)
            mask_val = self.segLayer.get_value(coord).copy()

            self.segLayer.selected_label = mask_val

            if mask_val != 0:
                stored_mask = self.segLayer.data.copy()
                stored_class = self.classLayer.data.copy()

                if len(stored_mask.shape) > 2:
                    current_fov = self.viewer.dims.current_step[0]

                    seg_mask = stored_mask[current_fov, :, :]
                    class_mask = stored_class[current_fov, :, :]

                    class_mask[seg_mask == mask_val] = self.class_colour

                    stored_class[current_fov, :, :] = class_mask

                    self.classLayer.data = stored_class
                    self.segLayer.mode = "pan_zoom"

                else:
                    stored_class[stored_mask == mask_val] = self.class_colour

                    self.classLayer.data = stored_class
                    self.segLayer.mode = "pan_zoom"

        if self.interface_mode == "panzoom":
            mouse_button = event.button

            data_coordinates = self.segLayer.world_to_data(event.position)
            coord = np.round(data_coordinates).astype(int)

        if self.modify_auto_panzoom.isChecked() == True:
            self.interface_mode = "panzoom"
            self.modify_panzoom.setEnabled(False)
            self.modify_segment.setEnabled(True)
            self.modify_classify.setEnabled(True)

    except:
        print(traceback.format_exc())


def _newSegColour(self):
    mask_stack = self.segLayer.data

    current_fov = self.viewer.dims.current_step[0]

    if len(mask_stack.shape) > 2:
        mask = mask_stack[current_fov, :, :]
    else:
        mask = mask_stack

    colours = np.unique(mask)
    new_colour = max(colours) + 1

    self.segLayer.selected_label = new_colour

    return new_colour


def _modifyMode(self, mode, viewer=None):
    def _event(viewer):
        if mode == "panzoom":
            self.segLayer.mode = "pan_zoom"

            self.interface_mode = "panzoom"
            self.modify_panzoom.setEnabled(False)
            self.modify_panzoom.setEnabled(False)
            self.modify_segment.setEnabled(True)
            self.modify_classify.setEnabled(True)

        if mode == "segment":
            self.viewer.layers.selection.select_only(self.segLayer)

            self.interface_mode = "segment"
            self.segmentation_mode = "add"
            self.modify_panzoom.setEnabled(True)
            self.modify_segment.setEnabled(False)
            self.modify_classify.setEnabled(True)

        if mode == "classify":
            self.viewer.layers.selection.select_only(self.segLayer)

            self.interface_mode = "classify"
            self.segmentation_mode = "add"
            self.class_mode = 1
            self.modify_panzoom.setEnabled(True)
            self.modify_segment.setEnabled(True)
            self.modify_classify.setEnabled(False)

        if mode == "clicktozoom":
            self.viewer.layers.selection.select_only(self.segLayer)

            self.interface_mode = "segment"
            self.segmentation_mode = "clicktozoom"  # self.modify_panzoom.setEnabled(True)  # self.modify_segment.setEnabled(True)  # self.modify_classify.setEnabled(True)

        if mode == "add":
            self.viewer.layers.selection.select_only(self.segLayer)

            self.interface_mode = "segment"
            self.segmentation_mode = "add"
            self.modify_panzoom.setEnabled(True)
            self.modify_segment.setEnabled(False)
            show_info("Add (click/drag to add)")

        if mode == "extend":
            self.viewer.layers.selection.select_only(self.segLayer)

            self.interface_mode = "segment"
            self.segmentation_mode = "extend"
            self.modify_panzoom.setEnabled(True)
            self.modify_segment.setEnabled(False)
            show_info("Extend (click/drag to extend)")

        if mode == "join":
            self.viewer.layers.selection.select_only(self.segLayer)

            self.interface_mode = "segment"
            self.segmentation_mode = "join"
            self.modify_panzoom.setEnabled(True)
            self.modify_segment.setEnabled(False)
            show_info("Join (click/drag to join)")

        if mode == "split":
            self.viewer.layers.selection.select_only(self.segLayer)

            self.interface_mode = "segment"
            self.segmentation_mode = "split"
            self.modify_panzoom.setEnabled(True)
            self.modify_segment.setEnabled(False)
            show_info("Split (click/drag to split)")

        if mode == "delete":
            self.viewer.layers.selection.select_only(self.segLayer)

            self.interface_mode = "segment"
            self.segmentation_mode = "delete"
            self.modify_panzoom.setEnabled(True)
            self.modify_segment.setEnabled(False)
            show_info("Delete (click/drag to delete)")

        if mode == "edit_vertex":
            self.viewer.layers.selection.select_only(self.shapeLayer)

            self.interface_mode = "shapes"
            self.segmentation_mode = "edit_vertex"

            self.modify_panzoom.setEnabled(True)
            self.modify_segment.setEnabled(False)

        if mode == "refine":
            self.viewer.layers.selection.select_only(self.segLayer)

            self.interface_mode = "segment"
            self.segmentation_mode = "refine"
            self.modify_panzoom.setEnabled(True)
            self.modify_segment.setEnabled(False)
            show_info("Refine (click to refine)")

        if self.interface_mode == "segment":
            self.viewer.layers.selection.select_only(self.segLayer)

        if mode == "single":
            self.viewer.layers.selection.select_only(self.segLayer)

            self.class_mode = mode
            self.class_colour = 1
            self.interface_mode = "classify"
            self.modify_panzoom.setEnabled(True)
            self.modify_segment.setEnabled(True)
            self.modify_classify.setEnabled(False)
            show_info("Single (click to classify)")

        if mode == "dividing":
            self.viewer.layers.selection.select_only(self.segLayer)

            self.class_mode = mode
            self.class_colour = 2
            self.interface_mode = "classify"
            self.modify_panzoom.setEnabled(True)
            self.modify_segment.setEnabled(True)
            self.modify_classify.setEnabled(False)
            show_info("Dividing (click to classify)")

        if mode == "divided":
            self.viewer.layers.selection.select_only(self.segLayer)

            self.class_mode = mode
            self.class_colour = 3
            self.interface_mode = "classify"
            self.modify_panzoom.setEnabled(True)
            self.modify_segment.setEnabled(True)
            self.modify_classify.setEnabled(False)
            show_info("Divided (click to classify)")

        if mode == "vertical":
            self.viewer.layers.selection.select_only(self.segLayer)

            self.class_mode = mode
            self.class_colour = 4
            self.interface_mode = "classify"
            self.modify_panzoom.setEnabled(True)
            self.modify_segment.setEnabled(True)
            self.modify_classify.setEnabled(False)
            show_info("Vertical (click to classify)")

        if mode == "broken":
            self.viewer.layers.selection.select_only(self.segLayer)

            self.class_mode = mode
            self.class_colour = 5
            self.interface_mode = "classify"
            self.modify_panzoom.setEnabled(True)
            self.modify_segment.setEnabled(True)
            self.modify_classify.setEnabled(False)
            show_info("Broken (click to classify)")

        if mode == "edge":
            self.viewer.layers.selection.select_only(self.segLayer)

            self.class_mode = mode
            self.class_colour = 6
            self.interface_mode = "classify"
            self.modify_panzoom.setEnabled(True)
            self.modify_segment.setEnabled(True)
            self.modify_classify.setEnabled(False)
            show_info("Edge (click to classify)")

    return _event


def autocontrast_values(image, clip_hist_percent=0.001):
    # calculate histogram
    hist, bin_edges = np.histogram(image, bins=(2 ** 16) - 1)
    hist_size = len(hist)

    # calculate cumulative distribution from the histogram
    accumulator = cumsum(hist)

    # Locate points to clip
    maximum = accumulator[-1]
    clip_hist_percent *= maximum / 100.0
    clip_hist_percent /= 2.0

    # Locate left cut
    minimum_gray = 0
    try:
        while accumulator[minimum_gray] < clip_hist_percent:
            minimum_gray += 1
    except:
        pass

    # Locate right cut
    maximum_gray = hist_size - 1
    try:
        while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
            maximum_gray -= 1
    except:
        pass

    # Calculate alpha and beta values
    alpha = 255 / (maximum_gray - minimum_gray)
    beta = -minimum_gray * alpha

    # calculate gamma value
    img = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    mid = 0.5
    mean = np.mean(img)
    gamma = np.log(mid * 255) / np.log(mean)

    if gamma > 2:
        gamma = 2
    if gamma < 0.2:
        gamma = 0.2

    if maximum_gray > minimum_gray:
        contrast_limit = [minimum_gray, maximum_gray]
    else:
        contrast_limit = [np.min(image), np.max(image)]

    return contrast_limit, alpha, beta, gamma


def get_histogram(image, bins):
    """calculates and returns histogram"""

    # array with size of bins, set to zeros
    histogram = np.zeros(bins)

    # loop through pixels and sum up counts of pixels

    for pixel in image:
        try:
            histogram[pixel] += 1
        except:
            pass

    return histogram


def cumsum(a):
    """cumulative sum function"""

    a = iter(a)
    b = [next(a)]
    for i in a:
        b.append(b[-1] + i)
    return np.array(b)


def _viewerControls(self, key, viewer=None):
    def _event(viewer):
        if key == "h":
            self.viewer.reset_view()

        if key == "o":
            current_zoom = self.viewer.camera.zoom
            new_zoom = current_zoom - 2
            if new_zoom <= 0:
                self.viewer.reset_view()
            else:
                self.viewer.camera.zoom = new_zoom

        if key == "i":
            self.viewer.camera.zoom = self.viewer.camera.zoom + 2

        if key == "z":
            if self.segLayer.visible == True:
                self.segLayer.visible = False
                self.modify_viewmasks.setChecked(False)
            else:
                self.segLayer.visible = True
                self.modify_viewmasks.setChecked(True)

        if key == "x":
            if self.classLayer.visible == True:
                self.classLayer.visible = False
                self.modify_viewlabels.setChecked(False)
            else:
                self.classLayer.visible = True
                self.modify_viewlabels.setChecked(True)

        if key == "viewlabels":
            self.classLayer.visible = self.modify_viewlabels.isChecked()

        if key == "viewmasks":
            self.segLayer.visible = self.modify_viewmasks.isChecked()

        if key == "c":
            layer_names = [layer.name for layer in self.viewer.layers if layer.name not in ["Segmentations", "Classes", "center_lines"]]

            if len(layer_names) != 0:
                active_layer = layer_names[-1]

                image_dims = tuple(list(self.viewer.dims.current_step[:-2]) + [...])

                image = (self.viewer.layers[str(active_layer)].data[image_dims].copy())

                crop = self.viewer.layers[str(active_layer)].corner_pixels[:, -2:]

                [[y1, x1], [y2, x2]] = crop

                image_crop = image[y1:y2, x1:x2]

                contrast_limit = [np.min(image_crop), np.max(image_crop)]

                if contrast_limit[1] > contrast_limit[0]:
                    self.viewer.layers[str(active_layer)].contrast_limits = contrast_limit

    return _event


def _imageControls(self, key, viewer=None):
    def _event(viewer):
        print(True)

        if key == "Upload":
            self._uploadDatabase("active")

        if len(self.viewer.dims.current_step) == 3:
            current_frame = self.viewer.dims.current_step[0]
            frame_range = int(self.viewer.dims.range[0][1]) - 1

            if key == "Right" or "Upload":
                next_step = current_frame + 1
            if key == "Left":
                next_step = current_frame - 1

            if next_step < 0:
                next_step = 0
            if next_step > frame_range:
                next_step = frame_range

            self.viewer.dims.current_step = (next_step, 0, 0)
            self.viewer.reset_view()

        if len(self.viewer.dims.current_step) == 4:
            current_frame = self.viewer.dims.current_step[0]
            current_tile = self.viewer.dims.current_step[1]

            frame_range = int(self.viewer.dims.range[0][1]) - 1
            tile_range = int(self.viewer.dims.range[1][1]) - 1

            next_frame = current_frame
            next_tile = current_tile

            if key == "Right":
                next_tile = current_tile + 1
            if key == "Left":
                next_tile = current_tile - 1

            if next_tile < 0:
                next_tile = 0
                next_frame = current_frame - 1
            if next_tile > tile_range:
                next_tile = 0
                next_frame = current_frame + 1
            if next_frame < 0:
                next_frame = 0
            if next_frame > frame_range:
                next_frame = frame_range

            self.viewer.dims.current_step = (next_frame, next_tile, 0, 0)
            self.viewer.reset_view()
            self._autoContrast()

    return _event


def _clear_images(self):
    self.segLayer.data = np.zeros((1, 100, 100), dtype=np.uint16)

    layer_names = [layer.name for layer in self.viewer.layers]

    for layer_name in layer_names:
        if layer_name not in ["Segmentations", "Classes", "center_lines"]:
            self.viewer.layers.remove(self.viewer.layers[layer_name])


def _copymasktoall(self):
    current_fov = self.viewer.dims.current_step[0]

    mask = self.segLayer.data[current_fov]
    label = self.classLayer.data[current_fov]

    dim_range = int(self.viewer.dims.range[0][1])

    for i in range(dim_range):
        self.segLayer.data[i] = mask
        self.classLayer.data[i] = label


def _deleteallmasks(self, viewer=None, mode="all"):
    def _event(viewer):
        try:
            current_step = self.viewer.dims.current_step

            viewer_dims = np.array(self.viewer.dims.range[:-2]).astype(int)

            if mode == "active":
                mask = self.segLayer.data[current_step[:-2]].copy()
                mask_ids = np.unique(mask).tolist()

                if len(viewer_dims) == 2:
                    self.update_image_folds(mask_ids=mask_ids)

                else:
                    for mask_id in mask_ids:
                        mask[mask == mask_id] = 0

                    self.segLayer.data[current_step[:-2]] = mask
                    self.segLayer.refresh()

            else:
                for image_index in range(*viewer_dims[0]):
                    mask = self.segLayer.data[image_index].copy()
                    mask_ids = np.unique(mask)

                    if len(viewer_dims) == 2:
                        self.update_image_folds(mask_ids=mask_ids, image_index=image_index)

                    else:
                        for mask_id in mask_ids:
                            mask[mask == mask_id] = 0

                        self.segLayer.data[image_index] = mask
                        self.segLayer.refresh()

            if self.segLayer.visible == True:
                self.segLayer.visible = False
                self.segLayer.visible = True

            if self.classLayer.visible == True:
                self.classLayer.visible = False
                self.classLayer.visible = True

        except:
            print(traceback.format_exc())

    return _event


def _delete_active_image(self, viewer=None, mode="active"):
    def _event(viewer):
        try:
            current_fov = self.viewer.dims.current_step[0]

            dim_range = int(self.viewer.dims.range[0][1])

            if mode == "active":
                dim_delete_list = [current_fov]
            else:
                dim_delete_list = np.arange(dim_range).tolist()
                dim_delete_list.remove(current_fov)

            layer_names = [layer.name for layer in self.viewer.layers]

            if dim_range > 1:
                for layer_name in layer_names:
                    layer = self.viewer.layers[layer_name]

                    images = layer.data.copy()
                    metadata = layer.metadata.copy()

                    if mode == "active":
                        images = np.delete(images, current_fov, axis=0)
                    else:
                        images = images[current_fov]

                    for dim in dim_delete_list:
                        if dim in metadata.keys():
                            del metadata[dim]

                    new_meta = {}

                    for key, value in metadata.items():
                        new_meta[len(new_meta)] = value

                    metadata = new_meta

                    layer.data = images
                    layer.metadata = metadata

                    self._updateFileName()
                    self._updateSegmentationCombo()
                    self._updateSegChannels()
        except:
            pass

    return _event


def _doubeClickEvents(self, viewer, event):
    mouse_button = event.button

    data_coordinates = self.segLayer.world_to_data(event.position)
    coord = np.round(data_coordinates).astype(int)
    colour = self.segLayer.get_value(coord)

    if mouse_button == 1 and colour in [0, None]:
        if self.modify_viewmasks.isChecked() == True:
            self.modify_viewmasks.setChecked(False)
            self.segLayer.visible = False
        else:
            self.modify_viewmasks.setChecked(True)
            self.segLayer.visible = True

    if mouse_button == 1 and colour != 0:
        meta = self.segLayer.metadata.copy()

        self.segLayer.fill(coord, 0)
        self.classLayer.fill(coord, 0)
        self.segLayer.selected_label = 0

        # update metadata

        meta["manual_segmentation"] = True
        self.segLayer.metadata = meta
        self.segLayer.mode = "pan_zoom"
        self.update_image_folds()
