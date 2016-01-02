import os
import collections
import math
import random
import cv2
import scipy.ndimage
import numpy as np


class MotionHeatmap:
    """
    This class is used to generate a motion heatmap from a directory of images representing frames in a time-lapse
    sequence. Instantiate this class with the necessary parameters, then generate the actual motion heatmap using
    the generate_motion_heatmap() method.

    Initialization does the following:
    (1) Divide the input image canvas into the desired number of blocks.
    (2) Pick a random pixel location within each block, to be used as the indicator of motion in that block's region.
    (3) Build a heatmap by quantifying, for each frame, the amount of motion (in the time domain) for each block.
    (4) Construct the average image across all frames in the sequence, if the user specifies this option
    (5) Low-pass filter the heatmap with a Gaussian kernel (with a configurable sigma parameter)
    Generation of the motion heatmap does the following:
    (1) Go through each pixel and determine the heatmap intensity at the block corresponding to the pixel
    (2) Apply positive or negative offsets to the red and blue channels at each pixel depending on the heatmap intensity
    """

    def __init__(
        self,
        # Resolution of the heatmap
        num_vertical_divisions,
        num_horizontal_divisions,
        # Path to images
        image_path,
        # Function or lambda used to filter files in image_path (useful if only certain files in the directory should be chosen)
        file_filter_func=lambda f: True,
        # Set to True to construct an "average" image used for the final overlay image; otherwise, the first frame of the sequence will be used
        use_average_image_overlay=True,
        # Value of sigma for Gaussian filter of the heatmap
        sigma=1.5,
        # Scales intensity of the heatmap's red/blue tint: higher values will exaggerate the tinting
        color_intensity_factor=7,
    ):
        self.num_vertical_divisions = num_vertical_divisions
        self.num_horizontal_divisions = num_horizontal_divisions
        self.color_intensity_factor = color_intensity_factor
        self.use_average_image_overlay = use_average_image_overlay
        self.image_path = image_path

        self.frame_files = filter(
            file_filter_func,
            sorted([f for f in os.listdir(self.image_path) if os.path.isfile(os.path.join(self.image_path, f))]),
        )
        sample_image = cv2.imread(os.path.join(self.image_path, self.frame_files[0]))
        self.height = len(sample_image)
        self.width = len(sample_image[0])

        # Initialize random pixel locations for each block
        self.pixel_locations = {}
        for row in range(self.num_vertical_divisions):
            for col in range(self.num_horizontal_divisions):
                self.pixel_locations[(row, col)] = (
                    int(row * self.height/num_vertical_divisions + math.floor(random.random() * self.height/num_vertical_divisions)),
                    int(col * self.width/num_horizontal_divisions + math.floor(random.random() * self.width/num_horizontal_divisions)),
                )

        # Initialize block intensities for each block and construct average image
        self.block_intensities = collections.defaultdict(list)
        self.average_image = np.zeros((self.height, self.width, 3))
        for index, file_name in enumerate(self.frame_files):
            print 'Processing input frame {index} of {total}'.format(index=index + 1, total=len(self.frame_files))
            frame = cv2.imread(os.path.join(self.image_path, file_name), cv2.IMREAD_COLOR)
            if self.use_average_image_overlay:
                self.average_image += frame
            for row in range(self.num_vertical_divisions):
                for col in range(self.num_horizontal_divisions):
                    pixel_row, pixel_col = self.pixel_locations[(row, col)]
                    self.block_intensities[(row, col)].append(round(np.mean(frame[pixel_row][pixel_col])))
        if self.use_average_image_overlay:
            self.average_image /= len(self.frame_files)

        # Calculate heatmap
        unfiltered_heatmap = np.zeros((self.num_vertical_divisions, self.num_horizontal_divisions))
        for row in range(self.num_vertical_divisions):
            for col in range(self.num_horizontal_divisions):
                unfiltered_heatmap[row][col] = np.std(self.block_intensities[(row, col)])
        self.heatmap = scipy.ndimage.filters.gaussian_filter(unfiltered_heatmap, sigma=sigma)

    def generate_motion_heatmap(self, file_name='motion_heatmap.jpg'):
        """
        Generates the motion heatmap for this sequence of frames.

        :param file_name: The name of the file to save to disk.
        :return: True or False denoting success of the operation. The method will write the output image to disk.
        """
        output_image = self.average_image if self.use_average_image_overlay else cv2.imread(os.path.join(self.image_path, self.frame_files[0]), cv2.IMREAD_COLOR)
        mean_stdev = np.mean(self.heatmap)

        for vertical_index in range(self.num_vertical_divisions):
            for horizontal_index in range(self.num_horizontal_divisions):
                print 'Processing output block {index} of {total}'.format(
                    index=vertical_index * self.num_horizontal_divisions + horizontal_index + 1,
                    total=self.num_horizontal_divisions * self.num_vertical_divisions,
                )
                offset = self.color_intensity_factor * (self.heatmap[vertical_index][horizontal_index] - mean_stdev)
                for i in range(self.height/self.num_vertical_divisions):
                    for j in range(self.width/self.num_horizontal_divisions):
                        row = vertical_index * self.height/self.num_vertical_divisions + i
                        col = horizontal_index * self.width/self.num_horizontal_divisions + j
                        # Apparently indices [0 1 2] correspond to [B G R].
                        # Why, OpenCV?
                        output_image[row][col][2] = self._clip_rgb(output_image[row][col][2] + offset)
                        output_image[row][col][0] = self._clip_rgb(output_image[row][col][0] - offset)

        return cv2.imwrite(file_name, output_image)

    @staticmethod
    def _clip_rgb(value):
        """
        Clips the value to be within the bounds of an 8-bit color image, e.g. in the range [0, 255].

        :param value: The value to clip.
        :return: An integer of the value clipped, as necessary.
        """
        return int(max(min(value, 255), 0))
