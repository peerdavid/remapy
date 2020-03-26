#!/usr/bin/env python3
#
# Script for converting a reMarkable tablet lines file to an SVG
# image.  Originally from
#
#    https://github.com/lschwetlick/maxio/tree/master/tools
#
# but hacked to allow for specification of desired size of resulting
# SVG image in terms of width and height.  Log of changes at the end
# of the file.
#
# Changed by Eric S Fraga;
# Changed by Peer David;
import sys
import struct
import os.path
import argparse


# Size
default_x_width = 1404
default_y_width = 1872

# Mappings
stroke_colour = {
    0: "darkblue",
    1: "yellow",
    2: "white",
    3: "yellow"
}


def rm2svg(path, output_name, coloured_annotations=False,
              x_width=default_x_width, y_width=default_y_width,
              background=None):

    if output_name.endswith(".svg"):
        output_name = output_name[:-4]

    used_pages = []
    # Iterate through pages (There is at least one)
    for f in os.listdir(path):
        if(not f.endswith(".rm")):
            continue

        input_file = "%s/%s" % (path, f)
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
        output.write('<svg xmlns="http://www.w3.org/2000/svg" height="{}" width="{}">\n'.format(y_width, x_width)) # BEGIN page
        
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
                    if(x_width == default_x_width and y_width == default_y_width):
                        width *= 1.8
                elif (pen == 3 or pen == 16): # Marker
                    width = 64 * width - 112
                    opacity = 0.9
                elif (pen == 5 or pen == 18): # Highlighter
                    width = 30
                    opacity = 0.2
                    if coloured_annotations:
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
                    ratio = (y_width/x_width)/(1872/1404)
                    if ratio > 1:
                        xpos = ratio*((xpos*x_width)/1404)
                        ypos = (ypos*y_width)/1872
                    else:
                        xpos = (xpos*x_width)/1404
                        ypos = (1/ratio)*(ypos*y_width)/1872
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


    # For every intermediate page that is empty create a blank page
    if len(used_pages) == 0:
        return

    for page in range(max(used_pages)+2):   # Note: last page is iterated by pdftk, so also add blank there
        if page in used_pages:
            continue

        output = open("{}{:05}.svg".format(output_name, page+1), 'w')
        output.write('<svg xmlns="http://www.w3.org/2000/svg" height="{}" width="{}">\n'.format(y_width, x_width)) # BEGIN page
        output.write('</svg>') # END page
        output.close()


if __name__ == "__main__":
    main()