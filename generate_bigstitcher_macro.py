import os
import os.path as osp
from datetime import datetime


class BigStitcherMacro:
    def __init__(self):
        self.img_dir = ''
        self.out_dir = ''
        self.xml_file_name = 'dataset.xml'
        self.pattern = '1_{xxxxx}_Z{ttt}_CH{c}.tif'

        # range: 1-5 or list: 1,2,3,4,5
        self.num_z_planes = 1
        self.num_channels = 1
        self.num_tiles = 1

        self.num_tiles_x = 1
        self.num_tiles_y = 1

        # overlap in percent
        self.overlap_x = 10
        self.overlap_y = 10
        self.overlap_z = 1

        # distance in um
        self.pixel_distance_x = 1
        self.pixel_distance_y = 1
        self.pixel_distance_z = 1

        self.reference_channel = 1
        self.reference_z_plane = 1


    def generate(self):
        macro_template = self.read_macro_template()
        formatted_macro = self.replace_values(macro_template)
        macro_file_path = self.write_to_temp_macro_file(formatted_macro)
        return macro_file_path

    def read_macro_template(self):
        macro_template_file = 'bigstitcher_macro_template.ijm'
        with open(macro_template_file, 'r') as f:
            macro_file = f.read()
        return macro_file


    def replace_values(self, macro_template):
        formatted_macro = macro_template.format(img_dir=self.img_dir,
                                                out_dir=self.out_dir,
                                                xml_file_name=self.xml_file_name,
                                                pattern=self.pattern,
                                                num_z_planes=self.num_z_planes,
                                                num_channels=self.make_range(self.num_channels),
                                                num_tiles=self.make_range(self.num_tiles),
                                                num_tiles_x=self.num_tiles_x,
                                                num_tiles_y=self.num_tiles_y,
                                                overlap_x=self.overlap_x,
                                                overlap_y=self.overlap_y,
                                                overlap_z=self.overlap_z,
                                                pixel_distance_x=self.pixel_distance_x,
                                                pixel_distance_y=self.pixel_distance_y,
                                                pixel_distance_z=self.pixel_distance_z,
                                                reference_channel=self.reference_channel,
                                                reference_z_plane=self.reference_z_plane
                                                )
        return formatted_macro


    def write_to_temp_macro_file(self, formatted_macro):
        #current_date_time_list = list(datetime.timetuple(datetime.now()))[:7]
        #current_date_time_str = ''.join((str(val) for val in current_date_time_list))
        macro_file_name = 'bigstitcher_macro.ijm'
        macro_file_path = osp.join(os.getcwd(), macro_file_name)
        with open(macro_file_path, 'w') as f:
            f.write(formatted_macro)
        return macro_file_path

    def make_range(self, number):
        return ','.join([str(n) for n in range(1, number+1)])

