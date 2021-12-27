import io
import json
import os
import os.path
import re
import struct

from pdfrw import PdfReader, PdfWriter, PageMerge
from reportlab.lib import colors
from reportlab.pdfgen import canvas

# Size
DEFAULT_IMAGE_WIDTH = 1404
DEFAULT_IMAGE_HEIGHT = 1872

# Mappings
default_stroke_color = {
    0: (0 / 255., 0 / 255., 0 / 255.),        # Pen color 1 black
    1: (100 / 255., 100 / 255., 100 / 255.),        # Pen color 2 grey
    2: (255 / 255., 255 / 255., 255 / 255.),      # Eraser white
    3: (255 / 255., 255 / 255., 0 / 255.),               # Highlighter yellow
    4: (0 / 255., 255 / 255., 0 / 255.),          # Highlighter green
    5: (255 / 255., 0 / 255., 255 / 255.), # Highlighter pink
    6: (50 / 255., 50 / 255., 255 / 255.), # blue
    7: (255 / 255., 50 / 255., 50 / 255.) # red
}


class PDFPageLayout:
    def __init__(self, pdf_page=None, is_landscape=False, default_layout=None):
        if not pdf_page:
            if is_landscape:
                self.layout = [0, 0, DEFAULT_IMAGE_HEIGHT, DEFAULT_IMAGE_WIDTH]
            else:
                self.layout = [0, 0, DEFAULT_IMAGE_WIDTH, DEFAULT_IMAGE_HEIGHT]
        else:
            self.layout = pdf_page.CropBox or pdf_page.BleedBox or pdf_page.TrimBox or pdf_page.MediaBox or pdf_page.ArtBox

            if self.layout is None and default_layout is not None:
                self.layout = default_layout
            elif self.layout is None and default_layout is None:
                return

        self.layout = [float(self.layout[0]), float(self.layout[1]), float(self.layout[2]), float(self.layout[3])]
        self.x_start = self.layout[0]
        self.y_start = self.layout[1]
        self.x_end = self.layout[2]
        self.y_end = self.layout[3]
        self.width = self.x_end - self.x_start
        self.height = self.y_end - self.y_start
        self.is_landscape = self.width > self.height

        if self.is_landscape:
            default_width = DEFAULT_IMAGE_HEIGHT
            default_height = DEFAULT_IMAGE_WIDTH
        else:
            default_width = DEFAULT_IMAGE_WIDTH
            default_height = DEFAULT_IMAGE_HEIGHT
        if self.width / self.height > default_width / default_height:
            # height is shorter
            self.height = self.width * default_height / default_width
        else:
            # width is shorter
            self.width = self.height * default_width / default_height
        self.scale = self.width / default_width

    def __str__(self):
        if self.layout:
            return "PDFPageLayout: %s, scale=%f" % (self.layout, self.scale)
        else:
            return "PDFPageLayout: None"


def pdf(rm_files_path, path_highlighter, pages, path_original_pdf, path_annotated_pdf, path_oap_pdf):
    """ Render pdf with annotations. The path_oap_pdf defines the pdf
        which includes only annotated pages.
    """

    base_pdf = PdfReader(open(path_original_pdf, "rb"))

    # Parse remarkable files and write into pdf
    annotations_pdf = []
    offsets = []

    for page_nr in range(base_pdf.numPages):
        rm_file_name = "%s/%d" % (rm_files_path, page_nr)
        rm_file = "%s.rm" % rm_file_name
        if not os.path.exists(rm_file):
            annotations_pdf.append(None)
            offsets.append(None)
            continue

        if hasattr(base_pdf, "Root") and hasattr(base_pdf.Root, "Pages") and hasattr(base_pdf.Root.Pages, "MediaBox"):
            default_layout = base_pdf.Root.Pages.MediaBox
        else:
            default_layout = None
        page_layout = PDFPageLayout(base_pdf.pages[page_nr], default_layout=default_layout)
        if page_layout.layout is None:
            annotations_pdf.append(None)
            offsets.append(None)
            continue

        page_file = os.path.join(path_highlighter, f"{pages[page_nr]}.json")
        annotated_page, offset = _render_rm_file(
            rm_file_name,
            page_layout=page_layout,
            page_file=page_file,)

        if len(annotated_page.pages) <= 0:
            annotations_pdf.append(None)
        else:
            page = annotated_page.pages[0]
            annotations_pdf.append(page)
        offsets.append(offset)

    # Merge annotations pdf and original pdf
    writer_full = PdfWriter()
    writer_oap = PdfWriter()
    for i in range(base_pdf.numPages):
        annotations_page = annotations_pdf[i]

        if annotations_page is not None:
            # The annotations page is at least as large as the base PDF page,
            # so we merge the base PDF page under the annotations page.
            merger = PageMerge(annotations_page)
            pdf = merger.add(base_pdf.pages[i], prepend=True)[0]
            pdf.x -= offsets[i][0]
            pdf.y -= offsets[i][1]
            merger.render()
            writer_oap.addpage(annotations_page)
            writer_full.addpage(annotations_page)
        else:
            writer_full.addpage(base_pdf.pages[i])

    writer_full.write(path_annotated_pdf)
    writer_oap.write(path_oap_pdf)


def notebook(path, uuid, path_annotated_pdf, is_landscape, path_templates=None):
    rm_files_path = "%s/%s" % (path, uuid)
    annotations_pdf = []

    p = 0
    while True:
        rm_file_name = "%s/%d" % (rm_files_path, p)
        rm_file = "%s.rm" % rm_file_name

        if not os.path.exists(rm_file):
            break

        overlay, _ = _render_rm_file(rm_file_name, PDFPageLayout(is_landscape=is_landscape))
        annotations_pdf.append(overlay)
        p += 1

    # Write empty notebook notes containing blank pages or templates
    writer = PdfWriter()
    templates = _get_templates_per_page(path, uuid, path_templates)
    for template in templates:
        if template is None:
            writer.addpage(_blank_page())
        else:
            writer.addpage(template.pages[0])
    writer.write(path_annotated_pdf)

    # Overlay empty notebook with annotations
    templates_pdf = PdfReader(path_annotated_pdf)
    for i in range(len(annotations_pdf)):
        templates_pdf.pages[i].Rotate = 90 if is_landscape else 0
        is_empty_page = len(annotations_pdf[i].pages) <= 0
        if is_empty_page:
            continue

        annotated_page = annotations_pdf[i].pages[0]
        annotated_page.Rotate = -90 if is_landscape else 0
        merger = PageMerge(templates_pdf.pages[i])
        merger.add(annotated_page).render()

    writer = PdfWriter()
    writer.write(path_annotated_pdf, templates_pdf)


def _get_templates_per_page(path, uuid, path_templates):
    pagedata_file = "%s/%s.pagedata" % (path, uuid)
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
    blank.mbox = [0, 0, width, height]  # 8.5 x 11
    blank = blank.render()
    return blank


def _render_rm_file(rm_file_name, page_layout=None, page_file=None):
    """ Render the .rm files (old .lines). See also
    https://plasma.ninja/blog/devices/remarkable/binary/format/2017/12/26/reMarkable-lines-file-format.html
    """

    rm_file = "%s.rm" % rm_file_name
    rm_file_metadata = "%s-metadata.json" % rm_file_name

    # Is this a reMarkable .lines file?
    with open(rm_file, 'rb') as f:
        data = f.read()
    offset = 0
    expected_header_v3 = b'reMarkable .lines file, version=3          '
    expected_header_v5 = b'reMarkable .lines file, version=5          '
    if len(data) < len(expected_header_v5) + 4:
        print('File too short to be a valid file')
        os.abort()

    fmt = '<{}sI'.format(len(expected_header_v5))
    header, nlayers = struct.unpack_from(fmt, data, offset)
    offset += struct.calcsize(fmt)
    is_v3 = (header == expected_header_v3)
    is_v5 = (header == expected_header_v5)
    if (not is_v3 and not is_v5) or nlayers < 1:
        print('Not a valid reMarkable file: <header={}><nlayers={}>'.format(header, nlayers))
        os.abort()


    # Load name of layers; if layer name starts with # we use this color
    # for this layer
    layer_colors = [None for _ in range(nlayers)]
    if os.path.exists(rm_file_metadata):
        with open(rm_file_metadata, "r") as meta_file:
            layers = json.loads(meta_file.read())["layers"]

        for l in range(len(layers)):
            layer = layers[l]

            matches = re.search(r"#([^\s]+)", layer["name"], re.M | re.I)
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

    # Iterate through layers on the page (There is at least one) to collect annotation data to render
    layer_data_list = []
    all_x = [page_layout.x_start, page_layout.x_end]
    all_y = [page_layout.y_start, page_layout.y_end]
    for layer in range(nlayers):
        fmt = '<I'
        (strokes_count,) = struct.unpack_from(fmt, data, offset)
        offset += struct.calcsize(fmt)

        # Iterate through the strokes in the layer (If there is any)
        highlighter_stroke_list = []
        other_stroke_list = []
        for stroke in range(strokes_count):
            if is_v3:
                fmt = '<IIIfI'
                pen_nr, color, i_unk, width, segments_count = struct.unpack_from(fmt, data, offset)
                offset += struct.calcsize(fmt)
            if is_v5:
                fmt = '<IIIffI'
                pen_nr, color, i_unk, width, unknown, segments_count = struct.unpack_from(fmt, data, offset)
                offset += struct.calcsize(fmt)

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
                pen = Mechanical_Pencil(page_layout.scale, width, color)
            if is_brush:
                pen = Brush(page_layout.scale, width, color)
            elif is_ballpoint:
                pen = Ballpoint(page_layout.scale, width, color)
            elif is_fineliner:
                pen = Fineliner(page_layout.scale, width, color)
            elif is_marker:
                pen = Marker(page_layout.scale, width, color)
            elif is_calligraphy:
                pen = Calligraphy(page_layout.scale, width, color)
            elif is_highlighter:
                pen = Highlighter(page_layout.scale, 30, color)
            elif is_eraser:
                pen = Eraser(page_layout.scale, width, color)
            elif is_eraser_area:
                pen = EraseArea(page_layout.scale, width, color)
            elif is_tilt_pencil:
                pen = Pencil(page_layout.scale, width, color)
            elif is_sharp_pencil:
                pen = Mechanical_Pencil(page_layout.scale, width, color)
            else:
                print('Unknown pen: {}'.format(pen_nr))
                opacity = 0.

            # Iterate through the segments to form a polyline
            last_width = 0
            segment_points = []
            segment_widths = []
            segment_opacities = []
            segment_colors = []
            for segment in range(segments_count):
                fmt = '<ffffff'
                x_pos, y_pos, speed, tilt, width, pressure = struct.unpack_from(fmt, data, offset)
                offset += struct.calcsize(fmt)

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

                if page_layout.is_landscape:
                    render_xpos = page_layout.x_end - page_layout.scale * y_pos
                    render_ypos = page_layout.y_end - page_layout.scale * x_pos
                else:
                    render_xpos = page_layout.x_start + page_layout.scale * x_pos
                    render_ypos = page_layout.y_end - page_layout.scale * y_pos
                segment_points.extend([render_xpos, render_ypos])
                last_width = segment_width

            if is_eraser_area or is_eraser:
                continue

            stroke_data = {}
            stroke_data["x_coordinates"] = segment_points[0::2]
            stroke_data["y_coordinates"] = segment_points[1::2]
            stroke_data["segment_widths"] = segment_widths
            stroke_data["segment_opacities"] = segment_opacities
            stroke_data["segment_colors"] = segment_colors
            if is_highlighter:
                highlighter_stroke_list.append(stroke_data)
            else:
                other_stroke_list.append(stroke_data)
            all_x.extend(stroke_data["x_coordinates"])
            all_y.extend(stroke_data["y_coordinates"])

        layer_data = {}
        layer_data["highlighter_strokes"] = highlighter_stroke_list
        layer_data["other_strokes"] = other_stroke_list
        layer_data_list.append(layer_data)

    # Preprocess collected data to determine canvas size and offset
    min_x = min(all_x)
    max_x = max(all_x)
    min_y = min(all_y)
    max_y = max(all_y)
    canvas_width = max_x - min_x
    canvas_height = max_y - min_y
    canvas_offset = (min_x, min_y)
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(canvas_width, canvas_height))
    can.translate(-canvas_offset[0], -canvas_offset[1])

    # Special handling to plot snapped highlights
    if(page_file and os.path.exists(page_file)):
        with open(page_file, "r") as f:
            highlights = json.loads(f.read())["highlights"]
            for h in highlights[0]:
                can.setStrokeColor(default_stroke_color[h["color"]])
                can.setStrokeAlpha(0.3)

                p = can.beginPath()
                for rects in h["rects"]:
                    if page_layout.is_landscape:
                        render_xpos = page_layout.x_end - page_layout.scale * rects["y"]
                        render_ypos = page_layout.y_end - page_layout.scale * rects["x"]
                        width = rects["height"] * page_layout.scale
                        height = rects["width"] * page_layout.scale
                        render_xpos -= width
                        render_ypos -= height / 2
                    else:
                        render_xpos = page_layout.x_start + page_layout.scale * rects["x"]
                        render_ypos = page_layout.y_end - page_layout.scale * rects["y"]
                        width = rects["width"] * page_layout.scale
                        height = rects["height"] * page_layout.scale
                        render_ypos -= height / 2

                    can.setLineWidth(height)

                    p.moveTo(render_xpos, render_ypos)
                    p.lineTo(render_xpos+width, render_ypos)
                p.close()
                can.drawPath(p)

    # Iterate over collected data to draw annotations
    for layer in layer_data_list:
        for stroke in layer["highlighter_strokes"]:
            can.setLineCap(1)
            for i in range(1, len(stroke["x_coordinates"])):
                can.setStrokeColor(stroke["segment_colors"][i])
                can.setLineWidth(stroke["segment_widths"][i])
                can.setStrokeAlpha(0.1)
                p = can.beginPath()
                p.moveTo(stroke["x_coordinates"][i-1], stroke["y_coordinates"][i-1])
                p.lineTo(stroke["x_coordinates"][i], stroke["y_coordinates"][i])
                p.moveTo(stroke["x_coordinates"][i], stroke["y_coordinates"][i])
                p.close()
                can.drawPath(p)
        for stroke in layer["other_strokes"]:
            can.setLineCap(1)
            for i in range(1, len(stroke["x_coordinates"])):
                can.setStrokeColor(stroke["segment_colors"][i])
                can.setLineWidth(stroke["segment_widths"][i])
                can.setStrokeAlpha(stroke["segment_opacities"][i])
                p = can.beginPath()
                p.moveTo(stroke["x_coordinates"][i-1], stroke["y_coordinates"][i-1])
                p.lineTo(stroke["x_coordinates"][i], stroke["y_coordinates"][i])
                p.moveTo(stroke["x_coordinates"][i], stroke["y_coordinates"][i])
                p.close()
                can.drawPath(p)

    can.save()
    packet.seek(0)
    overlay = PdfReader(packet)

    return overlay, canvas_offset


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
        self.ratio = ratio
        self.name = "Basic Pen"

    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        return self.base_width * self.ratio

    def get_segment_color(self, speed, tilt, width, pressure, last_width):
        return _get_color(self.base_color)

    def get_segment_opacity(self, speed, tilt, width, pressure, last_width):
        return self.base_opacity

    def cutoff(self, value):
        """return value in [0, 1]"""
        return max(0, min(1, value))


class Fineliner(Pen):
    def __init__(self, ratio, base_width, base_color):
        super().__init__(ratio, base_width, base_color)
        self.base_width = ((0.5 * base_width) ** 10) * 3
        self.name = "Fineliner"


class Ballpoint(Pen):
    def __init__(self, ratio, base_width, base_color):
        super().__init__(ratio, base_width, base_color)
        self.segment_length = 5
        self.name = "Ballpoint"

    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        segment_width = (0.5 + pressure) + (1 * width) - 0.5 * (speed / 50)
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
        super().__init__(ratio, base_width, base_color)
        self.segment_length = 2
        self.name = "Pencil"

    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        segment_width = 0.5 * ((((0.8 * self.base_width) + (0.5 * pressure)) * (1 * width)) - (
                0.25 * tilt ** 1.8))  # - (0.6 * speed / 50))
        # segment_width = 1.3*(((self.base_width * 0.4) * pressure) - 0.5 * ((tilt ** 0.5)) + (0.5 * last_width))
        max_width = self.base_width * 10
        segment_width = segment_width if segment_width < max_width else max_width
        return segment_width * self.ratio

    def get_segment_opacity(self, speed, tilt, width, pressure, last_width):
        segment_opacity = max(0.05, min(0.7, pressure ** 3))
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
        segment_width = 0.7 * (
                ((1 + (1.4 * pressure)) * (1 * width)) - (0.5 * tilt) - (0.5 * speed / 50))  # + (0.2 * last_width)
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
        super().__init__(ratio, base_width, base_color)
        self.stroke_cap = "square"
        self.base_opacity = 0.0
        self.name = "Highlighter"
        self.segment_length = 2

    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        return self.base_width * self.ratio


class Eraser(Pen):
    def __init__(self, ratio, base_width, base_color):
        super().__init__(ratio, base_width, 2)
        self.stroke_cap = "square"
        self.base_width = self.base_width * 2
        self.name = "Eraser"


class EraseArea(Pen):
    def __init__(self, ratio, base_width, base_color):
        super().__init__(ratio, base_width, base_color)
        self.stroke_cap = "square"
        self.base_opacity = 0
        self.name = "Erase Area"


class Calligraphy(Pen):
    def __init__(self, ratio, base_width, base_color):
        super().__init__(ratio, base_width, base_color)
        self.segment_length = 2
        self.name = "Calligraphy"

    def get_segment_width(self, speed, tilt, width, pressure, last_width):
        segment_width = 0.5 * (((1 + pressure) * (1 * width)) - 0.3 * tilt) + (0.2 * last_width)
        return segment_width * self.ratio
