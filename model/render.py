import sys
import struct
import os.path
import argparse
import math
import json
import io
import time
import re
import numpy as np
from pdfrw import PdfReader, PdfWriter, PageMerge, IndirectPdfDict, PdfDict
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.graphics.shapes import PolyLine, Drawing, Line


# Size
DEFAULT_IMAGE_WIDTH = 1404
DEFAULT_IMAGE_HEIGHT = 1872


# Mappings
default_stroke_color = {
    0: (48/255., 63/255., 159/255.),        # Pen color 1
    1: (211/255., 47/255., 47/255.),        # Pen color 2
    2: (255/255., 255/255., 255/255.),      # Eraser
    3: (255/255., 255/255., 0),             # Highlighter
    4: (50/255., 50/255., 50/255.)          # Pencil
}


def pdf(rm_files_path, path_original_pdf, path_annotated_pdf, path_oap_pdf):
    """ Render pdf with annotations. The path_oap_pdf defines the pdf 
        which includes only annotated pages.
    """

    base_pdf = PdfReader(open(path_original_pdf, "rb"))

    # Parse remarkable files and write into pdf
    annotations_pdf = []

    for page_nr in range(base_pdf.numPages):
        rm_file_name = "%s/%d" % (rm_files_path, page_nr)
        rm_file = "%s.rm" % rm_file_name
        if not os.path.exists(rm_file):
            annotations_pdf.append(None)
            continue
            
        page_layout = base_pdf.pages[page_nr].MediaBox
        crop_box = base_pdf.pages[page_nr].CropBox
        if page_layout is None:
            page_layout = base_pdf.pages[page_nr].ArtBox

            if page_layout is None:
                annotations_pdf.append(None)
                continue
            
        image_width, image_height = float(page_layout[2]), float(page_layout[3])
        annotated_page = _render_rm_file(rm_file_name, image_width=image_width, image_height=image_height, crop_box=crop_box)
        if len(annotated_page.pages) <= 0:
            annotations_pdf.append(None)
        else:
            page = annotated_page.pages[0]
            annotations_pdf.append(page)
       
    # Merge annotations pdf and original pdf
    writer_full = PdfWriter()
    writer_oap = PdfWriter()
    for i in range(base_pdf.numPages):          
        annotations_page = annotations_pdf[i]

        if annotations_page != None:
            merger = PageMerge(base_pdf.pages[i])
            merger.add(annotations_page).render()
            writer_oap.addpage(base_pdf.pages[i])

        writer_full.addpage(base_pdf.pages[i])

    writer_full.write(path_annotated_pdf)
    writer_oap.write(path_oap_pdf)


def notebook(path, id, path_annotated_pdf, is_landscape, path_templates=None):
    rm_files_path = "%s/%s" % (path, id)
    annotations_pdf = []

    p = 0
    while True:
        rm_file_name = "%s/%d" % (rm_files_path, p)
        rm_file = "%s.rm" % rm_file_name

        if not os.path.exists(rm_file):
            break

        overlay = _render_rm_file(rm_file_name)
        annotations_pdf.append(overlay)
        p += 1  
    
    # Write empty notebook notes containing blank pages or templates
    writer = PdfWriter()
    templates = _get_templates_per_page(path, id, path_templates)
    for template in templates:
        if template == None:
            writer.addpage(_blank_page())
        else:
            writer.addpage(template.pages[0])
    writer.write(path_annotated_pdf)
    
    # Overlay empty notebook with annotations
    templates_pdf = PdfReader(path_annotated_pdf)
    for i in range(len(annotations_pdf)):
        templates_pdf.pages[i].Rotate = 90 if is_landscape else 0
        empty_page = len(annotations_pdf[i].pages) <= 0
        if empty_page:
            continue 

        annotated_page = annotations_pdf[i].pages[0]
        if templates != None:
            merger = PageMerge(templates_pdf.pages[i])
            merger.add(annotated_page).render()
        else:
            output_pdf.addPage(annotated_page)
    
    writer = PdfWriter()
    writer.write(path_annotated_pdf, templates_pdf)



def _get_templates_per_page(path, id, path_templates):

    pagedata_file = "%s/%s.pagedata" % (path, id)
    with open(pagedata_file, 'r') as f:
        template_paths = ["%s/%s.png" % (path_templates, l.rstrip('\n')) for l in f] 
        
    templates = []
    for template_path in template_paths:
        if not os.path.exists(template_path):
            templates.append(None)
            continue

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(DEFAULT_IMAGE_WIDTH, DEFAULT_IMAGE_HEIGHT))
        can.drawImage(template_path, 0, 0)
        can.save()
        packet.seek(0)
        templates.append(PdfReader(packet))

    return templates


def _blank_page(width=DEFAULT_IMAGE_WIDTH, height=DEFAULT_IMAGE_HEIGHT):
    blank = PageMerge()
    blank.mbox = [0, 0, width, height] # 8.5 x 11
    blank = blank.render()
    return blank


def _render_rm_file(rm_file_name, image_width=DEFAULT_IMAGE_WIDTH, 
        image_height=DEFAULT_IMAGE_HEIGHT, crop_box=None):
    """ Render the .rm files (old .lines). See also 
    https://plasma.ninja/blog/devices/remarkable/binary/format/2017/12/26/reMarkable-lines-file-format.html
    """
    
    rm_file = "%s.rm" % rm_file_name
    rm_file_metadata = "%s-metadata.json" % rm_file_name

    is_landscape = image_width > image_height
    if is_landscape:
        image_height, image_width = image_width, image_height

    crop_box = [0.0, 0.0, image_width, image_height] if crop_box is None else crop_box

    # Calculate the image height and width that we use for the overlay
    if is_landscape:
        image_width = float(crop_box[2]) - float(crop_box[0])
        image_height = max(image_height, image_width * DEFAULT_IMAGE_HEIGHT / DEFAULT_IMAGE_WIDTH)
        ratio = (image_height) / (DEFAULT_IMAGE_HEIGHT)
    else:    
        image_height = float(crop_box[3]) - float(crop_box[1])
        image_width = max(image_width, image_height * DEFAULT_IMAGE_WIDTH / DEFAULT_IMAGE_HEIGHT)
        ratio = (image_width) / (DEFAULT_IMAGE_WIDTH)
    
    # Is this a reMarkable .lines file?
    with open(rm_file, 'rb') as f:
        data = f.read()
    offset = 0
    expected_header_v3=b'reMarkable .lines file, version=3          '
    expected_header_v5=b'reMarkable .lines file, version=5          '
    if len(data) < len(expected_header_v5) + 4:
        abort('File too short to be a valid file')

    fmt = '<{}sI'.format(len(expected_header_v5))
    header, nlayers = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)
    is_v3 = (header == expected_header_v3)
    is_v5 = (header == expected_header_v5)
    if (not is_v3 and not is_v5) or  nlayers < 1:
        abort('Not a valid reMarkable file: <header={}><nlayers={}>'.format(header, nlayers))
        return
    
    # Load name of layers; if layer name starts with # we use this color 
    # for this layer
    layer_colors = [None for l in range(nlayers)]
    if os.path.exists(rm_file_metadata):
        with open(rm_file_metadata, "r") as meta_file:
            layers = json.loads(meta_file.read())["layers"]
        
        for l in range(len(layers)):
            layer = layers[l]

            matches = re.search(r"#([^\s]+)", layer["name"], re.M|re.I)
            if not matches:
                continue 
            color_code = matches[0].lower()

            # Try to parse hex code
            try:
                has_alpha = len(color_code) > 7
                layer_colors[l] = colors.HexColor(color_code, hasAlpha=has_alpha)
                continue
            except:
                pass
            
            # Try to get from name
            color_code = color_code[1:]
            color_names = colors.getAllNamedColors()
            if color_code in color_names:
                layer_colors[l] = color_names[color_code]
            
            # No valid color found... automatic fallback to default


    # Iterate through layers on the page (There is at least one)
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(image_width, image_height))
    for layer in range(nlayers):
        fmt = '<I'
        (nstrokes,) = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)

        # Iterate through the strokes in the layer (If there is any)
        for stroke in range(nstrokes):
            if is_v3:
                fmt = '<IIIfI'
                pen_nr, color, i_unk, width, nsegments = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)
            if is_v5:
                fmt = '<IIIffI'
                pen_nr, color, i_unk, width, unknown, nsegments = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)
            
            opacity = 1
            last_x = -1.; last_y = -1.
            last_width = 0

            # Check which tool is used for both, v3 and v5 and set props
            # https://support.remarkable.com/hc/en-us/articles/115004558545-5-1-Tools-Overview
            is_highlighter = (pen_nr == 5 or pen_nr == 18)
            is_eraser = pen_nr == 6
            is_eraser_area = pen_nr == 8
            is_sharp_pencil = (pen_nr == 7 or pen_nr == 13) 
            is_tilt_pencil = (pen_nr == 1 or pen_nr == 14)
            is_marker = (pen_nr == 3 or pen_nr == 16)
            is_ballpoint = (pen_nr == 2 or pen_nr == 15)
            is_fineliner = (pen_nr == 4 or pen_nr == 17)
            is_brush = (pen_nr == 0 or pen_nr == 12)
            is_calligraphy = pen_nr == 21

            if is_sharp_pencil or is_tilt_pencil:
                pen = Mechanical_Pencil(ratio, width, color)
            if is_brush:
                pen = Brush(ratio, width, color)
            elif is_ballpoint:
                pen = Ballpoint(ratio, width, color)
            elif is_fineliner:
                pen = Fineliner(ratio, width, color)
            elif is_marker:
                pen = Marker(ratio, width, color)
            elif is_calligraphy:
                pen = Caligraphy(ratio, width, color)
            elif is_highlighter:
                pen = Highlighter(ratio, 30, color)
            elif is_eraser:
                pen = Eraser(ratio, width, color)
            elif is_eraser_area:
                pen = Erase_Area(ratio, width, color)
            elif is_tilt_pencil:
                pen = Pencil(ratio, width, color)
            elif is_sharp_pencil:
                pen = Mechanical_Pencil(ratio, width, color)
            else: 
                print('Unknown pen: {}'.format(pen_nr))
                opacity = 0.

            # Iterate through the segments to form a polyline
            segment_points = []
            segment_widths = []
            segment_opacities = []
            segment_colors = []
            for segment in range(nsegments):
                fmt = '<ffffff'
                xpos, ypos, speed, tilt, width, pressure = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)
                
                if segment % pen.segment_length == 0:
                    segment_color = pen.get_segment_color(speed, tilt, width, pressure, last_width)
                    segment_width = pen.get_segment_width(speed, tilt, width, pressure, last_width)
                    segment_opacity = pen.get_segment_opacity(speed, tilt, width, pressure, last_width)
                
                segment_widths.append(segment_width)
                segment_opacities.append(segment_opacity)
                if layer_colors[layer] is None:
                    segment_colors.append(segment_color)
                else:
                    segment_colors.append(layer_colors[layer])                

                xpos = ratio * xpos + float(crop_box[0])
                ypos = image_height - ratio * ypos + float(crop_box[1])
                segment_points.extend([xpos, ypos])
                last_width = segment_width

            if is_eraser_area or is_eraser:
                continue
            
            # Render lines after the arrays are filled
            # such that we have access to the next and previous points
            drawing = Drawing(image_width, image_height)
            can.setLineCap(0 if is_highlighter else 1)
            for i in range(2, len(segment_points), 2):
                can.setStrokeColor(segment_colors[int(i/2)])
                can.setLineWidth(segment_widths[int(i/2)])
                can.setStrokeAlpha(segment_opacities[int(i/2)])
                
                p = can.beginPath()
                p.moveTo(segment_points[i-2], segment_points[i-1])
                p.lineTo(segment_points[i], segment_points[i+1])
                p.moveTo(segment_points[i], segment_points[i+1])
                p.close()
                can.drawPath(p)

            #p.close()
            #can.drawPath(p)
        Pen
    can.save()
    packet.seek(0)
    overlay = PdfReader(packet)

    if is_landscape:
        for page in overlay.pages:
            page.Rotate=90

    return overlay


def _get_color(color):
    if len(color) == 3:
        return colors.Color(color[0], color[1], color[2])
    else:
        return colors.Color(color[0], color[1], color[2], color[3])


#
# Credit: https://github.com/lschwetlick/maxio
#
class Pen:
    def __init__(self, ratio, base_width, base_color):
        self.base_width = base_width
        self.base_color = default_stroke_color[base_color]
        self.segment_length = 1000
        self.base_opacity = 1
        self.ratio = ratio**2
        self.name = "Basic Pen"

    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        return self.base_width * self.ratio

    def get_segment_color(self, speed, tilt, width, pressure, last_width):
        return _get_color(self.base_color)

    def get_segment_opacity(self, speed, tilt, width, pressure, last_width):
        return self.base_opacity

    def cutoff(self, value):
        """return value \in [0, 1]"""
        return max(0, min(1, value))

class Fineliner(Pen):
    def __init__(self, ratio, base_width, base_color):
        super().__init__(ratio, base_width, base_color)
        self.base_width = ((0.5*base_width) ** 2) * 3
        self.name = "Fineliner"


class Ballpoint(Pen):
    def __init__(self, ratio, base_width, base_color):
        super().__init__(ratio, base_width, base_color)
        self.segment_length = 5
        self.name = "Ballpoint"

    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        segment_width = (0.5 + pressure) + (1 * width) - 0.5*(speed/50)
        return segment_width * self.ratio

    # def get_segment_color(self, speed, tilt, width, pressure, last_width):
    #     intensity = (0.1 * -(speed / 35)) + (1.2 * pressure) + 0.5
    #     intensity = self.cutoff(intensity)
    #     # using segment color not opacity because the dots interfere with each other.
    #     # Color must be 255 rgb
    #     segment_color = [abs(intensity - 1)] * 3
    #     return _get_color(segment_color)

class Marker(Pen):
    def __init__(self, ratio, base_width, base_color):
        super().__init__(ratio, base_width, base_color)
        self.segment_length = 3
        self.name = "Marker"

    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        segment_width = 0.9 * (((1 * width)) - 0.4 * tilt) + (0.1 * last_width)
        return segment_width * self.ratio


class Pencil(Pen):
    def __init__(self, ratio, base_width, base_color):
        super().__init__(ratio, base_width, 4)
        self.segment_length = 2
        self.name = "Pencil"

    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        segment_width = 0.7 * ((((0.8*self.base_width) + (0.5 * pressure)) * (1 * width)) - (0.25 * tilt**1.8) - (0.6 * speed / 50))
        #segment_width = 1.3*(((self.base_width * 0.4) * pressure) - 0.5 * ((tilt ** 0.5)) + (0.5 * last_width))
        max_width = self.base_width * 10
        segment_width = segment_width if segment_width < max_width else max_width
        return segment_width * self.ratio

    def get_segment_opacity(self, speed, tilt, width, pressure, last_width):
        segment_opacity = max(0.05, min(0.7, pressure**3))
        return self.cutoff(segment_opacity)


class Mechanical_Pencil(Pen):
    def __init__(self, ratio, base_width, base_color):
        super().__init__(ratio, base_width, base_color)
        self.base_width = self.base_width ** 2
        self.base_opacity = 0.7
        self.name = "Machanical Pencil"


class Brush(Pen):
    def __init__(self, ratio, base_width, base_color):
        super().__init__(ratio, base_width, base_color)
        self.segment_length = 2
        self.stroke_cap = "round"
        self.opacity = 1
        self.name = "Brush"

    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        segment_width = 0.7 * (((1 + (1.4 * pressure)) * (1 * width)) - (0.5 * tilt) - (0.5 * speed / 50))  #+ (0.2 * last_width)
        return segment_width * self.ratio

    # def get_segment_color(self, speed, tilt, width, pressure, last_width):
    #     intensity = (pressure ** 1.5  - 0.2 * (speed / 50))*1.5
    #     intensity = self.cutoff(intensity)
    #     # using segment color not opacity because the dots interfere with each other.
    #     # Color must be 255 rgb
    #     rev_intensity = abs(intensity - 1)
    #     segment_color = [(rev_intensity-1.0) * (self.base_color[0]),
    #                      (rev_intensity-1.0) * (self.base_color[1]),
    #                      (rev_intensity-1.0) * (self.base_color[2])]

    #     return _get_color(segment_color)


class Highlighter(Pen):
    def __init__(self, ratio, base_width, base_color):
        super().__init__(ratio, base_width, 3)
        self.stroke_cap = "square"
        self.base_opacity = 0.2
        self.name = "Highlighter"
        self.segment_length = 2
    
    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        return self.base_width * math.sqrt(self.ratio)
        


class Eraser(Pen):
    def __init__(self, ratio, base_width, base_color):
        super().__init__(ratio, base_width, 2)
        self.stroke_cap = "square"
        self.base_width = self.base_width * 2
        self.name = "Eraser"

class Erase_Area(Pen):
    def __init__(self, ratio, base_width, base_color):
        super().__init__(ratio, base_width, base_color)
        self.stroke_cap = "square"
        self.base_opacity = 0
        self.name = "Erase Area"


class Caligraphy(Pen):
    def __init__(self, ratio, base_width, base_color):
        super().__init__(ratio, base_width, base_color)
        self.segment_length = 2
        self.name = "Calligraphy"

    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        segment_width = 0.5 * (((1 + pressure) * (1 * width)) - 0.3 * tilt) + (0.1 * last_width)
        return segment_width * self.ratio