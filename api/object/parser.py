import sys
import struct
import os.path
import argparse
import io
from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.graphics.shapes import PolyLine, Drawing


# Size
DEFAULT_IMAGE_WIDTH = 1404
DEFAULT_IMAGE_HEIGHT = 1872


# Mappings
stroke_color = {
    0: colors.darkblue,  # Pen color 1
    1: colors.gray,      # Pen color 2
    2: colors.white,     # Eraser
    3: colors.yellow     # Highlighter
}


def rm_to_pdf(rm_files_path, path_original_pdf, path_annotated_pdf):
    
    input_pdf = PdfFileReader(open(path_original_pdf, "rb"))

    # Parse remarkable files and write into pdf
    annotations_pdf = []
    for page_nr in range(input_pdf.getNumPages()):
        rm_file = "%s/%d.rm" % (rm_files_path, page_nr)
        if not os.path.exists(rm_file):
            annotations_pdf.append(None)
            continue
        
        #######################################################
        packet = io.BytesIO()
        page_layout = input_pdf.getPage(0).mediaBox
        image_width, image_height = page_layout[2], page_layout[3]
        can = canvas.Canvas(packet, pagesize=(image_width, image_height))
        ratio = (image_height/image_width) / (DEFAULT_IMAGE_HEIGHT/DEFAULT_IMAGE_WIDTH)

        with open(rm_file, 'rb') as f:
            data = f.read()
        offset = 0

        # Is this a reMarkable .lines file?
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

        can.drawString(0, 0, "Created with RemaPy")

        # Iterate through layers on the page (There is at least one)
        for layer in range(nlayers):
            fmt = '<I'
            (nstrokes,) = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)

            # Iterate through the strokes in the layer (If there is any)
            for stroke in range(nstrokes):
                if is_v3:
                    fmt = '<IIIfI'
                    pen, color, i_unk, width, nsegments = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)
                if is_v5:
                    fmt = '<IIIffI'
                    pen, color, i_unk, width, unknown, nsegments = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)
                
                opacity = 1
                last_x = -1.; last_y = -1.

                is_highlighter = (pen == 5 or pen == 18)

                # See also https://support.remarkable.com/hc/en-us/articles/115004558545-5-1-Tools-Overview
                if (pen == 0 or pen == 12): # Brush
                    pass
                elif (pen == 2 or pen == 15) or (pen == 4 or pen == 17): # BallPoint | Fineliner
                    width = 32 * width * width - 116 * width + 107
                    if(image_width == DEFAULT_IMAGE_WIDTH and image_height == DEFAULT_IMAGE_HEIGHT):
                        width *= 1.8
                elif (pen == 3 or pen == 16): # Marker
                    width = 64 * width - 112
                    opacity = 0.9
                elif (is_highlighter):
                    width = 30
                    opacity = 0.2
                    color = 3
                elif (pen == 6): # Eraser
                    width = 1280 * width * width - 4800 * width + 4510
                    color = 2
                elif (pen == 7 or pen == 13) or (pen == 1 or pen == 14): # Sharp Pencil | Tilt Pencil
                    width = 16 * width - 27
                    opacity = 0.9
                elif (pen == 8): # Erase area
                    opacity = 0.
                else: 
                    print('Unknown pen: {}'.format(pen))
                    opacity = 0.

                width /= 2.0
                
                # Iterate through the segments to form a polyline
                points = []
                for segment in range(nsegments):
                    fmt = '<ffffff'
                    xpos, ypos, pressure, tilt, i_unk2, _ = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)
                    
                    if ratio > 1:
                        xpos = ratio*((xpos*image_width)/DEFAULT_IMAGE_WIDTH)
                        ypos = (ypos*image_height)/DEFAULT_IMAGE_HEIGHT
                    else:
                        xpos = (xpos*image_width)/DEFAULT_IMAGE_WIDTH
                        ypos = (1/ratio)*(ypos*image_height)/DEFAULT_IMAGE_HEIGHT

                    points.extend([xpos, image_height-ypos])

                drawing = Drawing(image_width, image_height)
                opacity = 0.2 if is_highlighter else 1.0
                poly_line = PolyLine(
                    points, 
                    strokeWidth=width, 
                    strokeColor=stroke_color[color],
                    strokeOpacity=opacity)

                drawing.add(poly_line)
                renderPDF.draw(drawing, can, 0, 0)
        
        can.save()
        #######################################################
        
        annotations_pdf.append(PdfFileReader(packet))
        packet.seek(0)



    # Merge annotations pdf and original pdf
    new_pdf = PdfFileReader(packet)
    output_pdf = PdfFileWriter()

    for page_nr in range(input_pdf.getNumPages()):
        page = input_pdf.getPage(page_nr)
        if annotations_pdf[page_nr] != None:
            page.mergePage(annotations_pdf[page_nr].getPage(0))
        output_pdf.addPage(page)

    outputStream = open(path_annotated_pdf, "wb")
    output_pdf.write(outputStream)
    outputStream.close()


if __name__ == "__main__":
    main()