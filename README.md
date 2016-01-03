Time-Lapse Motion Heatmap
=================

This is a simple computer vision algorithm implemented in Python and MATLAB that generates a visual heatmap indicating the spatial concentration of motion across several frames of a time-lapse sequence.

Given a sequence of frames, the algorithm determines regions of the image that exhibit motion throughout the sequence. Then, it overlays a colored heatmap over one of the frames (or the "average" frame in the entire sequence) that denotes the frequency of motion in that region. The heatmap's color spectrum is continuous from full red, indicating high motion frequency, to full blue, indicating no motion for the duration of the time-lapse sequence.

![Example result](http://i.imgur.com/mJT5htX.jpg "Motion heatmap overlay")
![Example result](http://i.imgur.com/vZt3TYC.jpg "Motion heatmap mesh")

## Usage

### Python

#### Prerequisites

In order to use the Python script, you must have OpenCV, `scipy`, and `numpy` installed.

`scipy` and `numpy` are available via `pip`:

```bash
pip install numpy scipy
```

Please refer to the [official OpenCV installation instructions](http://docs.opencv.org/2.4/doc/tutorials/introduction/linux_install/linux_install.html) to install OpenCV.

#### The MotionHeatmap class

At minimum, the Python script requires two inputs:

1. A list of paths of images, to be used as the input sequence of frames.
2. Two constants, `num_vertical_divisions` and `num_horizontal_divisions`, to indicate the resolution of the heatmap to generate.

Optional configuration parameters are:

1. `use_average_image_overlay`, to specify whether the resulting overlay image should be an "averaged" image of the entire sequence, or simply the first frame of the sequence.
2. `sigma`, the value of the parameter of the Gaussian low-pass filter applied to the two-dimensional heatmap
3. `color_intensity_factor`, which controls the sensitivity of the heatmap overlay to motion throughout the frames. A higher value would result in redder reds and bluer blues for the same amount of motion.

To use the `MotionHeatmap` class, you must first instantiate an object of the class with the required inputs as described above. Then, simply call `generate_motion_heatmap()` to generate the heatmap overlay image.

For a full example file, see `example.py` in the `python` directory.

```python
import motion_heatmap

images = ['/path/to/an/image.jpg', '/path/to/an/image.jpg', '/path/to/an/image.jpg', ...]
mh = motion_heatmap.MotionHeatmap(
	num_vertical_divisions=36,
	num_horizontal_divisions=64,
	images=images,
)
mh.generate_motion_heatmap(file_name='my-awesome-heatmap.jpg')
```

This will write a file named `my-awesome-heatmap.jpg` to the working directory.

### MATLAB

Tune the input configuration constants, `num_vertical_divisions`, `num_horizontal_divisions`, `color_intensity_factor`, `use_average_image_overlay`, and `sigma` as you see fit. These constants have the same definitions as is described above in the Python usage instructions.

By default, the script will look for all `.jpg` images in the current working directory. You can modify this as is necessary by changing the line reading

```
frame_files = dir('*.jpg');
```

Then, simply run the script. After completion, it will display figures for the spatial concentration of motion and the heatmap overlay.

## Theory

### Segmenting the input into motion regions

Motion in an image is best described in terms of the general regions of the frame in which motion exists. This algorithm takes the approach of segmenting the frame into equal-sized rectangular blocks, and considering a randomly selected pixel within each of these regions to be representative of that block. The extent of motion calculated from that single pixel across all frames in the sequence is the approximate estimate of motion within that rectangular region.

The limit of this approach (e.g. a maximally precise segmentation of the input image) is the case when the rectangular region is exactly one pixel in size. While this is computationally achievable, such a segmentation no longer conveys the concept of having "regions" of motion, since each pixel from the input image is in itself the motion region.

### Extracting motion data from frames

The core problem this algorithm attempts to solve can be summarized as

> Given a sequence of N frames, each of constant dimensions, how can the amount of motion at each region of the image across the entire sequence be quantified and visualized in an intuitive way?

On a high level, the input is a three-dimensional matrix of dimensions w x h x N, where each index (i, j, k) represents the grayscale intensity of the image at the pixel (i, j) of frame k. The output is a two-dimensional matrix of dimensions w x h, with each pixel (i, j) color-adjusted by applying appropriate offsets to the red and blue channels that represent the extent of motion at (i, j).

Given the segmentation above, we can generate `num_horizontal_divisions * num_vertical_divisions` signals representing the grayscale intensity at a particular pixel as a function of the frame number (a discrete-time axis). Signals with mostly low-frequency content can be considered to have little or no motion, whereas signals with significant high-frequency content can be considered to have more motion.

![Comparison of signals](http://i.imgur.com/Y8cFHCk.jpg "Grayscale intensity comparison: low motion and high motion regions")

### Quantifying per-pixel variance and generating a heatmap

This algorithm considers only the standard deviation of each of the signals as described above across all frames as a quantitative measure of the amount of motion at any particular pixel. (A more interesting approach might take the FFT of each of these signals for frequency-domain analysis; the amount of power within different "bins" of frequency might correspond to the amount of RGB offset on each motion region.)

From this data, we can generate a three-dimensional heatmap indicating the standard deviation at each of the motion regions (a spatial plane). The values on this heatmap at each motion region correlate directly to the amount of red and blue offset in the final heatmap overlay image. However, in order to reduce the visual inconsistency caused by regions with a high standard deviation relative to its neighbors (e.g. high-frequency content), we apply a low-pass Gaussian filter to the heatmap before using it as input to generating the heatmap overlay image.

![Comparison of heatmap mesh](http://i.imgur.com/K08SvVT.jpg "Heatmap mesh comparison: with and without Gaussian filter")
![Comparison of heatmap overlay](http://i.imgur.com/fHVTU7C.jpg "Heatmap overlay comparison: with and without Gaussian filter")

In this approach, the red and blue channels of the entire motion region are offset by a linearly scaled version the standard deviation of the signal of that motion region. A red channel increase/blue channel decrease should correspond to a high standard deviation, whereas a red channel decrease/blue channel increase should correspond to a low standard deviation. In order to "normalize" the standard deviation of all `num_horizontal_divisions * num_vertical_divisions` signals, the red and blue channel offsets are relative to the average standard deviation across all the signals.

```python
mean_stdev = np.mean(self.heatmap)
...
offset = self.color_intensity_factor * (self.heatmap[vertical_index][horizontal_index] - mean_stdev)
output_image[row][col][2] = self._clip_rgb(output_image[row][col][2] + offset)  # Red channel
output_image[row][col][0] = self._clip_rgb(output_image[row][col][0] - offset)  # Blue channel
```