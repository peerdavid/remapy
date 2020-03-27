import sys
import struct
import os.path
import argparse
import io
from PyPDF2 import PdfFileWriter, PdfFileReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


# Size
DEFAULT_IMAGE_WIDTH = 1404
DEFAULT_IMAGE_HEIGHT = 1872


# Mappings
stroke_colour = {
    0: "darkblue",  # Pen color 1
    1: "grey",      # Pen color 2
    2: "white",     # Eraser
    3: "yellow"     # Highlighter
}


def rm_to_svg(rm_files_path, output_name, image_width=DEFAULT_IMAGE_WIDTH, 
              image_height=DEFAULT_IMAGE_HEIGHT, background=None):

    if output_name.endswith(".svg"):
        output_name = output_name[:-4]

    used_pages = []
    # Iterate through pages (There is at least one)
    for f in os.listdir(rm_files_path):
        if(not f.endswith(".rm")):
            continue

        input_file = "%s/%s" % (rm_files_path, f)
        page = int(f[:-3])
        used_pages.append(page)

        with open(input_file, 'rb') as f:
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

        output = open("{}{:05}.svg".format(output_name, page), 'w')
        output.write('<svg xmlns="http://www.w3.org/2000/svg" height="{}" width="{}">\n'.format(image_height, image_width)) # BEGIN page

        if background != None:
           output.write('<rect width="100%%" height="100%%" fill="%s"/>' % background)


        # Iterate through layers on the page (There is at least one)
        for layer in range(nlayers):
            fmt = '<I'
            (nstrokes,) = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)

            # Iterate through the strokes in the layer (If there is any)
            for stroke in range(nstrokes):
                if is_v3:
                    fmt = '<IIIfI'
                    pen, colour, i_unk, width, nsegments = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)
                if is_v5:
                    fmt = '<IIIffI'
                    pen, colour, i_unk, width, unknown, nsegments = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)
                    #print('Stroke {}: pen={}, colour={}, width={}, unknown={}, nsegments={}'.format(stroke, pen, colour, width, unknown, nsegments))
                
                opacity = 1
                last_x = -1.; last_y = -1.

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
                elif (pen == 5 or pen == 18): # Highlighter
                    width = 30
                    opacity = 0.2
                    colour = 3
                elif (pen == 6): # Eraser
                    width = 1280 * width * width - 4800 * width + 4510
                    colour = 2
                elif (pen == 7 or pen == 13) or (pen == 1 or pen == 14): # Sharp Pencil | Tilt Pencil
                    width = 16 * width - 27
                    opacity = 0.9
                elif (pen == 8): # Erase area
                    opacity = 0.
                else: 
                    print('Unknown pen: {}'.format(pen))
                    opacity = 0.

                width /= 2.3 # adjust for transformation to A4
                
                #print('Stroke {}: pen={}, colour={}, width={}, nsegments={}'.format(stroke, pen, colour, width, nsegments))
                output.write('<polyline style="fill:none;stroke:{};stroke-width:{:.3f};opacity:{}" points="'.format(stroke_colour[colour], width, opacity)) # BEGIN stroke

                # Iterate through the segments to form a polyline
                for segment in range(nsegments):
                    fmt = '<ffffff'
                    xpos, ypos, pressure, tilt, i_unk2, _ = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)
                    #xpos += 60
                    #ypos -= 20
                    ratio = (image_height/image_width)/(1872/1404)
                    if ratio > 1:
                        xpos = ratio*((xpos*image_width)/1404)
                        ypos = (ypos*image_height)/1872
                    else:
                        xpos = (xpos*image_width)/1404
                        ypos = (1/ratio)*(ypos*image_height)/1872
                    if pen == 0:
                        if 0 == segment % 8:
                            segment_width = (5. * tilt) * (6. * width - 10) * (1 + 2. * pressure * pressure * pressure)
                            #print('    width={}'.format(segment_width))
                            output.write('" /><polyline style="fill:none;stroke:{};stroke-width:{:.3f}" points="'.format(
                                        stroke_colour[colour], segment_width)) # UPDATE stroke
                            if last_x != -1.:
                                output.write('{:.3f},{:.3f} '.format(last_x, last_y)) # Join to previous segment
                            last_x = xpos; last_y = ypos
                    elif pen == 1:
                        if 0 == segment % 8:
                            segment_width = (10. * tilt -2) * (8. * width - 14)
                            segment_opacity = (pressure - .2) * (pressure - .2)
                            #print('    width={}, opacity={}'.format(segment_width, segment_opacity))
                            output.write('" /><polyline style="fill:none;stroke:{};stroke-width:{:.3f};opacity:{:.3f}" points="'.format(
                                        stroke_colour[colour], segment_width, segment_opacity)) # UPDATE stroke
                            if last_x != -1.:
                                output.write('{:.3f},{:.3f} '.format(last_x, last_y)) # Join to previous segment
                            last_x = xpos; last_y = ypos

                    output.write('{:.3f},{:.3f} '.format(xpos, ypos)) # BEGIN and END polyline segment

                output.write('" />\n') # END stroke

        output.write('</svg>') # END page
        output.close()





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
                    pen, colour, i_unk, width, nsegments = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)
                if is_v5:
                    fmt = '<IIIffI'
                    pen, colour, i_unk, width, unknown, nsegments = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)
                    #print('Stroke {}: pen={}, colour={}, width={}, unknown={}, nsegments={}'.format(stroke, pen, colour, width, unknown, nsegments))
                
                opacity = 1
                last_x = -1.; last_y = -1.

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
                elif (pen == 5 or pen == 18): # Highlighter
                    width = 30
                    opacity = 0.2
                    colour = 3
                elif (pen == 6): # Eraser
                    width = 1280 * width * width - 4800 * width + 4510
                    colour = 2
                elif (pen == 7 or pen == 13) or (pen == 1 or pen == 14): # Sharp Pencil | Tilt Pencil
                    width = 16 * width - 27
                    opacity = 0.9
                elif (pen == 8): # Erase area
                    opacity = 0.
                else: 
                    print('Unknown pen: {}'.format(pen))
                    opacity = 0.

                width /= 2.0
                
                #print('Stroke {}: pen={}, colour={}, width={}, nsegments={}'.format(stroke, pen, colour, width, nsegments))
                # output.write('<polyline style="fill:none;stroke:{};stroke-width:{:.3f};opacity:{}" points="'.format(stroke_colour[colour], width, opacity)) # BEGIN stroke
                
                # Iterate through the segments to form a polyline
                last_x = -1
                last_y = -1
                for segment in range(nsegments):
                    fmt = '<ffffff'
                    xpos, ypos, pressure, tilt, i_unk2, _ = struct.unpack_from(fmt, data, offset); offset += struct.calcsize(fmt)
                    
                    if ratio > 1:
                        xpos = ratio*((xpos*image_width)/DEFAULT_IMAGE_WIDTH)
                        ypos = (ypos*image_height)/DEFAULT_IMAGE_HEIGHT
                    else:
                        xpos = (xpos*image_width)/DEFAULT_IMAGE_WIDTH
                        ypos = (1/ratio)*(ypos*image_height)/DEFAULT_IMAGE_HEIGHT
                    
                    if last_x != -1:
                        is_highlighter = pen == 5 or pen == 18
                        if is_highlighter:
                            can.setFillAlpha(0)
                            can.setStrokeAlpha(0.2)
                            can.setLineWidth(width)
                            can.setStrokeColorRGB(255.,255.,0.)
                            can.line(last_x, image_height - last_y, xpos, image_height - ypos)
                            
                        else:
                            can.setFillAlpha(1)
                            can.setStrokeAlpha(1)
                            can.setStrokeColorRGB(0.,0.,0.)
                            can.setLineWidth(width)
                            can.line(last_x, image_height - last_y, xpos, image_height - ypos)
                    
                    last_x = xpos
                    last_y = ypos

                    if pen == 0:
                        if 0 == segment % 8:
                            segment_width = (5. * tilt) * (6. * width - 10) * (1 + 2. * pressure * pressure * pressure)
                            #print('    width={}'.format(segment_width))
                            # output.write('" /><polyline style="fill:none;stroke:{};stroke-width:{:.3f}" points="'.format(
                            #             stroke_colour[colour], segment_width)) # UPDATE stroke
                            if last_x != -1.:
                                # output.write('{:.3f},{:.3f} '.format(last_x, last_y)) # Join to previous segment
                                can.line(last_x, last_y, xpos, ypos)
                            last_x = xpos; last_y = ypos
                    elif pen == 1:
                        if 0 == segment % 8:
                            segment_width = (10. * tilt -2) * (8. * width - 14)
                            segment_opacity = (pressure - .2) * (pressure - .2)
                            #print('    width={}, opacity={}'.format(segment_width, segment_opacity))
                            # output.write('" /><polyline style="fill:none;stroke:{};stroke-width:{:.3f};opacity:{:.3f}" points="'.format(
                            #             stroke_colour[colour], segment_width, segment_opacity)) # UPDATE stroke
                            if last_x != -1.:
                                # output.write('{:.3f},{:.3f} '.format(last_x, last_y)) # Join to previous segment
                                can.line(last_x, last_y, xpos, ypos)
                            last_x = xpos; last_y = ypos

                    #output.write('{:.3f},{:.3f} '.format(xpos, ypos)) # BEGIN and END polyline segment



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