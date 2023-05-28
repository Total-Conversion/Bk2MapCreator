import os
import cv2
import math
from PIL import Image
import struct


HEADER_LENGTH = 38
HEIGHT_FOOTER_LENGTH = 22
POST_HEIGHT_SECTOR_FOOTER_LENGTH = 88
BEFORE_TEXTURE_SECTOR_FOOTER_LENGTH = 88
TEXTURE_FOOTER_LENGTH = 28
FILE_CONTROL_SUM_OFFSET = 31
SECOND_FILE_CONTROL_SUM_OFFSET = 10
POST_HEIGHT_FIRST_VALUE_CONST = 37
POST_HEIGHT_LAST_VALUE_CONST = 34
TIMESTAMP = 18940734
GRAPHIC_FILE = 'input/map.png'
MAP_FILE = 'input/map.b2m'
MAP_FILE_N = 21
IMPORT_FROM_FILES = "b2m"  # none/png/b2m


def get_rolling_integer(int):
    rolling_int = []
    for i in range(0, int // 255):
        rolling_int.append(255)
    rolling_int.append(int % 255)
    return rolling_int


class MapCreator:
    n = -1
    header = []
    height = []
    height_footer = []
    post_height_sector = []
    post_height_sector_footer = []
    before_texture_sector = []
    before_texture_sector_footer = []
    texture_data_sector = []
    texture_footer = []
    post_texture_sector = []
    footer = []
    map_length = -1

    def get_side_tiles_count(self):
        return 16 * self.n + 1

    def get_tiles_count(self):
        return self.get_side_tiles_count() ** 2

    def get_third_header_value(self):
        n = self.n
        return 8 * n ** 2 + n

    def get_lengths_of_footer_bytes(self):
        n = self.n
        len_a = 1
        len_b = 4
        len_c = 1
        if n > 10:
            len_a = 4
        if n > 11:
            len_c = 4
        return [len_a, len_b, len_c]

    def get_footer_length(self):
        n = self.n
        const = 10
        bytes_lengths = self.get_lengths_of_footer_bytes()
        len_a = bytes_lengths[0]
        len_b = bytes_lengths[1]
        len_c = bytes_lengths[2]

        control_sum = 34 * n + (n - 1) ** 2
        rolling_length = len(get_rolling_integer(control_sum))
        length = const + len_a + len_b + len_c + rolling_length + n ** 2
        return length

    def get_file_length(self):
        length = HEADER_LENGTH + HEIGHT_FOOTER_LENGTH + POST_HEIGHT_SECTOR_FOOTER_LENGTH + BEFORE_TEXTURE_SECTOR_FOOTER_LENGTH + TEXTURE_FOOTER_LENGTH
        tiles_count = self.get_tiles_count()
        height_map_length = 4 * tiles_count
        post_height_sector_length = 4 * tiles_count
        before_texture_sector_length = tiles_count
        texture_data_sector_length = tiles_count
        post_texture_sector_length = 4 * tiles_count
        footer_length = self.get_footer_length()
        length += height_map_length + post_height_sector_length + before_texture_sector_length + texture_data_sector_length + post_texture_sector_length + footer_length
        return length

    def create_header(self):
        PADDING1 = [4,  8,  4,  0,  0,  0,  1]
        PADDING2 = [1]
        PADDING3 = [2,  43]
        PADDING4 = [1,  8]
        PADDING5 = [2,  8]
        PADDING6 = [3,  9]
        file_length = self.get_file_length()
        first_file_length_control_sum = file_length * 2 - FILE_CONTROL_SUM_OFFSET
        second_file_length_control_sum = first_file_length_control_sum - SECOND_FILE_CONTROL_SUM_OFFSET
        self.header = []
        self.header += PADDING1
        self.header += create_u32(first_file_length_control_sum)
        self.header += PADDING2
        self.header += create_u32(second_file_length_control_sum)
        self.header += PADDING3
        self.header += create_u24(self.get_third_header_value())
        self.header += PADDING4
        self.header += create_u32(self.get_side_tiles_count())
        self.header += PADDING5
        self.header += create_u32(self.get_side_tiles_count())
        self.header += PADDING6
        self.header += create_u24(self.get_third_header_value())

    # NOTE: LEAVE FOR FUTURE TESTING
    def xxx(self, number_a, number_b):
        return int((math.log(1.01**((255 * number_b) + number_a - 16448))*50 + 16448))

    def create_height(self):
        if os.path.isfile(GRAPHIC_FILE) and IMPORT_FROM_FILES == "png":
            self.height = self.read_height_from_png()
        elif os.path.isfile(MAP_FILE) and IMPORT_FROM_FILES == "b2m":
            self.height = self.read_height_from_b2m()
        else:
            self.height = [0, 0, 128, 64] * self.get_tiles_count()

    def create_height_footer(self):
        PADDING1 = [3,  43]
        PADDING2 = [1,  8]
        PADDING3 = [2,  8]
        PADDING4 = [3,  9]
        self.height_footer = []
        self.height_footer += PADDING1
        self.height_footer += create_u24(self.get_third_header_value())
        self.height_footer += PADDING2
        self.height_footer += create_u32(self.get_side_tiles_count())
        self.height_footer += PADDING3
        self.height_footer += create_u32(self.get_side_tiles_count())
        self.height_footer += PADDING4
        self.height_footer += create_u24(self.get_third_header_value())

    def create_post_height_sector(self):
        self.post_height_sector = [0] * self.get_tiles_count()*4

    def get_post_height_sector_footer_long_padding(self):
        ret = []
        ret += [255,    255,	255,     255,   20]
        for i in range(21,24):
            ret += [12,	2,	8,	0,	0,	0,	0, i]
        for i in range(25, 28):
            ret += [12, 2, 8, 0, 0, 0, 0, i]
        return ret

    def get_post_height_sector_footer_first_value(self):
        n = self.n
        return 512*n**2 + 64*n + POST_HEIGHT_FIRST_VALUE_CONST

    def create_post_height_sector_footer(self):
        PADDING1 = [4,  8]
        PADDING2 = [5,  8]
        PADDING3 = [6,  8] + self.get_post_height_sector_footer_long_padding()
        PADDING4 = [1,  8]
        PADDING5 = [2,  8]
        PADDING6 = [3]

        self.post_height_sector_footer = []
        self.post_height_sector_footer += PADDING1
        self.post_height_sector_footer += create_u32(self.n)
        self.post_height_sector_footer += PADDING2
        self.post_height_sector_footer += create_u32(self.n)
        self.post_height_sector_footer += PADDING3
        self.post_height_sector_footer += create_u32(self.get_post_height_sector_footer_first_value())
        self.post_height_sector_footer += PADDING4
        self.post_height_sector_footer += create_u32(self.get_side_tiles_count())
        self.post_height_sector_footer += PADDING5
        self.post_height_sector_footer += create_u32(self.get_side_tiles_count())
        self.post_height_sector_footer += PADDING6
        self.post_height_sector_footer += create_u32(self.get_post_height_sector_footer_first_value() - POST_HEIGHT_LAST_VALUE_CONST)

    def create_before_texture_sector(self):
        if os.path.isfile(MAP_FILE) and IMPORT_FROM_FILES == "b2m":
            self.before_texture_sector = self.read_before_texture_data_sector_from_b2m()
        else:
            self.before_texture_sector = [0] * self.get_tiles_count()

    def get_before_texture_sector_footer_long_padding(self):
        ret = []
        ret += [28]
        for i in range(31, 33):
            ret += [12, 2, 8, 0, 0, 0, 0, i]
        ret +=[24,1,8,0,0,0,0,2,8,0,0,0,0,33,24,1,8,0,0,0,0,2,8,0,0,0,0,34,40,1,8,0,0,0,0,2,24,1,8,0,0,0,0,2,8,0,0,0,0,35]
        return ret

    def create_before_texture_sector_footer(self):
        PADDING1 = self.get_before_texture_sector_footer_long_padding()
        PADDING2 = [1, 8]
        PADDING3 = [2, 8]
        PADDING4 = [3]
        self.before_texture_sector_footer = []
        self.before_texture_sector_footer += PADDING1
        self.before_texture_sector_footer += create_u32(self.get_post_height_sector_footer_first_value())
        self.before_texture_sector_footer += PADDING2
        self.before_texture_sector_footer += create_u32(self.get_side_tiles_count())
        self.before_texture_sector_footer += PADDING3
        self.before_texture_sector_footer += create_u32(self.get_side_tiles_count())
        self.before_texture_sector_footer += PADDING4
        self.before_texture_sector_footer += create_u32(self.get_post_height_sector_footer_first_value() - POST_HEIGHT_LAST_VALUE_CONST)

    def create_texture_data_sector(self):
        if os.path.isfile(GRAPHIC_FILE) and IMPORT_FROM_FILES == "png":
            self.texture_data_sector = [0] * self.get_tiles_count()
        elif os.path.isfile(MAP_FILE) and IMPORT_FROM_FILES == "b2m":
            self.texture_data_sector = self.read_texture_data_sector_from_b2m()
        else:
            self.texture_data_sector = [0] * self.get_tiles_count()

    def create_texture_footer(self):
        PADDING1 = [36, 8]
        PADDING2 = [37, 43]
        PADDING3 = [1,  8]
        PADDING4 = [2,  8]
        PADDING5 = [3,  9]
        self.texture_footer = []
        self.texture_footer += PADDING1
        self.texture_footer += create_u32(TIMESTAMP)
        self.texture_footer += PADDING2
        self.texture_footer += create_u24(self.get_third_header_value())
        self.texture_footer += PADDING3
        self.texture_footer += create_u32(self.get_side_tiles_count())
        self.texture_footer += PADDING4
        self.texture_footer += create_u32(self.get_side_tiles_count())
        self.texture_footer += PADDING5
        self.texture_footer += create_u24(self.get_third_header_value())

    def create_post_texture_sector(self):
        if os.path.isfile(MAP_FILE) and IMPORT_FROM_FILES == "b2m":
            # self.post_texture_sector = self.read_post_texture_data_sector_from_b2m()
            self.post_texture_sector = [0] * self.get_tiles_count() * 4
        else:
            self.post_texture_sector = [0] * self.get_tiles_count() * 4

    def create_footer(self):
        n = self.n
        PADDING1 = [39]
        PADDING2 = [1,  8]
        PADDING3 = [2]
        PADDING4 =[0,   0,  2,  0,  5,  0]
        lengths = self.get_lengths_of_footer_bytes()
        footer_length = self.get_footer_length()
        first_footer_control_sum = 2*footer_length - 14
        first_footer_control_sum -= 5 * int(first_footer_control_sum>255)

        second_footer_control_sum = footer_length - 15
        second_footer_control_sum -= 3* int(lengths[0]>1)
        second_footer_control_sum -= 3* int(lengths[2]>1)
        third_footer_control_sum = 2*second_footer_control_sum
        third_footer_control_sum += int(third_footer_control_sum>255)
        fourth_footer_control_sum = 34 * n + (n - 1) ** 2
        self.footer = []
        self.footer += PADDING1
        self.footer += create_u_custom(first_footer_control_sum,lengths[0])
        self.footer += PADDING2
        self.footer += create_u_custom(second_footer_control_sum,lengths[1])
        self.footer += PADDING3
        self.footer += create_u_custom(third_footer_control_sum,lengths[2])
        self.footer += [255]*n**2 + get_rolling_integer(fourth_footer_control_sum)
        self.footer += PADDING4

    def create_map(self):
        self.create_header()
        self.create_height()
        self.create_height_footer()
        self.create_post_height_sector()
        self.create_post_height_sector_footer()
        self.create_before_texture_sector()
        self.create_before_texture_sector_footer()
        self.create_texture_data_sector()
        self.create_texture_footer()
        self.create_post_texture_sector()
        self.create_footer()
        return self.header + self.height + self.height_footer + self.post_height_sector + self.post_height_sector_footer + self.before_texture_sector + self.before_texture_sector_footer + self.texture_data_sector + self.texture_footer + self.post_texture_sector + self.footer

    def read_height_from_png(self):
        img = cv2.imread(GRAPHIC_FILE, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, (self.get_side_tiles_count(), self.get_side_tiles_count()), interpolation=cv2.INTER_AREA)
        img = cv2.flip(img, 0)
        rows, cols = img.shape
        height = []
        for i in range(rows):
            for j in range(cols):
                offset = 2 * (img[i, j] - 64)
                height.append(0)
                height.append(0)
                height.append((128 + offset) % 255)
                height.append(64 + (128 + offset) // 255)
        return height

    def read_height_from_b2m(self):
        b2m_map = open(MAP_FILE, 'rb')
        b2m_bytes = [byte for byte in bytearray(b2m_map.read())]
        offset = 0
        offset += 38  # header
        height_bytes = b2m_bytes[offset:offset + (((MAP_FILE_N * 16 + 1) ** 2) * 4)]
        height_values = [(height_bytes[i] << 24) + (height_bytes[i + 1] << 16) + (height_bytes[i + 2] << 8) + height_bytes[i + 3] for i in range(0, len(height_bytes), 4)]
        height_values = self.resize_height(height_values)
        height_bytes = list(map(lambda x: create_u32(x, direction="big"), height_values))
        height_bytes = [item for sublist in height_bytes for item in sublist]
        return height_bytes

    def resize_height(self, height_values):
        resized_height = []
        current_size = int(len(height_values) ** 0.5)  # Assuming square surface
        scale_factor = self.get_side_tiles_count() / current_size

        for row in range(self.get_side_tiles_count()):
            for col in range(self.get_side_tiles_count()):
                orig_row = round(row / scale_factor)
                orig_col = round(col / scale_factor)
                height = height_values[orig_row * current_size + orig_col]
                resized_height.append(height)

        return resized_height

    def read_texture_data_sector_from_b2m(self):
        b2m_map = open(MAP_FILE, 'rb')
        b2m_bytes = [byte for byte in bytearray(b2m_map.read())]
        offset = 0
        offset += 38                                # header
        offset += 4 * ((MAP_FILE_N * 16 + 1) ** 2)  # height
        offset += 22                                # height footer
        offset += 4 * ((MAP_FILE_N * 16 + 1) ** 2)  # post height sector
        offset += 88                                # post height sector footer
        offset += ((MAP_FILE_N * 16 + 1) ** 2)      # before texture sector
        offset += 88                                # before texture sector footer
        texture_ids = bytearray(b2m_bytes[offset:offset + ((MAP_FILE_N * 16 + 1) ** 2)])
        resized_texture_ids = self.resize_texture_ids(texture_ids)
        return resized_texture_ids

    def read_before_texture_data_sector_from_b2m(self):
        b2m_map = open(MAP_FILE, 'rb')
        b2m_bytes = [byte for byte in bytearray(b2m_map.read())]
        offset = 0
        offset += 38                                # header
        offset += 4 * ((MAP_FILE_N * 16 + 1) ** 2)  # height
        offset += 22                                # height footer
        offset += 4 * ((MAP_FILE_N * 16 + 1) ** 2)  # post height sector
        offset += 88                                # post height sector footer
        texture_ids = bytearray(b2m_bytes[offset:offset + ((MAP_FILE_N * 16 + 1) ** 2)])
        resized_texture_ids = self.resize_texture_ids(texture_ids)
        return resized_texture_ids

    def read_post_texture_data_sector_from_b2m(self):
        b2m_map = open(MAP_FILE, 'rb')
        b2m_bytes = [byte for byte in bytearray(b2m_map.read())]
        offset = 0
        offset += 38                                # header
        offset += 4 * ((MAP_FILE_N * 16 + 1) ** 2)  # height
        offset += 22                                # height footer
        offset += 4 * ((MAP_FILE_N * 16 + 1) ** 2)  # post height sector
        offset += 88                                # post height sector footer
        offset += ((MAP_FILE_N * 16 + 1) ** 2)      # before texture sector
        offset += 88                                # before texture sector footer
        offset += ((MAP_FILE_N * 16 + 1) ** 2)      # texture sector
        offset += 28                                # texture sector footer
        texture_ids = bytearray(b2m_bytes[offset:offset + 4*((MAP_FILE_N * 16 + 1) ** 2)])
        resized_texture_ids = self.resize_texture_ids(texture_ids)
        return resized_texture_ids

    def resize_texture_ids(self, texture_ids):
        resized_texture_ids = []
        current_size = int(len(texture_ids) ** 0.5)
        scale_factor = self.get_side_tiles_count() / current_size

        for row in range(self.get_side_tiles_count()):
            for col in range(self.get_side_tiles_count()):
                orig_row = round(row / scale_factor)
                orig_col = round(col / scale_factor)
                texture_id = texture_ids[orig_row * current_size + orig_col]
                resized_texture_ids.append(texture_id)

        return resized_texture_ids


def create_u32(a, direction="little"):
    return [byte for byte in bytearray(a.to_bytes(4, direction))]


def create_u24(a, direction="little"):
    return [byte for byte in bytearray(a.to_bytes(3, direction))]


def create_u16(a, direction="little"):
    return [byte for byte in bytearray(a.to_bytes(2, direction))]


def create_u_custom(a,size, direction="little"):
    return [byte for byte in bytearray(a.to_bytes(size, direction))]


def run_tests():
    assert create_u32(256) ==  [0, 1, 0, 0]
    assert create_u24(256 * 256) ==  [0, 0, 1]
    assert create_u16(1) == [1,0]
    assert get_rolling_integer(256) == [255,1]
    for i in range(1,21):
        map = MapCreator()
        map.n = i
        map.create_header()
        map.create_height()
        map.create_height_footer()
        map.create_post_height_sector()
        map.create_post_height_sector_footer()
        map.create_before_texture_sector()
        map.create_before_texture_sector_footer()
        map.create_texture_data_sector()
        map.create_texture_footer()
        map.create_post_texture_sector()
        map.create_footer()
        assert len(map.height_footer) == HEIGHT_FOOTER_LENGTH
        assert len(map.header) == HEADER_LENGTH
        assert len(map.height) == map.get_tiles_count()*4
        assert len(map.post_height_sector) == map.get_tiles_count()*4
        assert len(map.post_height_sector_footer) == POST_HEIGHT_SECTOR_FOOTER_LENGTH
        assert len(map.before_texture_sector) == map.get_tiles_count()
        assert len(map.before_texture_sector_footer) == BEFORE_TEXTURE_SECTOR_FOOTER_LENGTH
        assert len(map.texture_data_sector) == map.get_tiles_count()
        assert len(map.texture_footer) == TEXTURE_FOOTER_LENGTH
        assert len(map.post_texture_sector) == map.get_tiles_count() * 4
        assert len(map.footer) == map.get_footer_length()
        assert map.get_file_length() == len(map.create_map())


if __name__ == '__main__':
    # run_tests()
    map_creator = MapCreator()
    map_creator.n = 20
    root = os.path.abspath(os.curdir)
    newFile = open(f'{root}\output\map.b2m', "wb")
    newFile.write(bytearray(map_creator.create_map()))
    # write to file
