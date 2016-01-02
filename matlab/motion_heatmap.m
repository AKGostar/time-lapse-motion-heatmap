% CONFIGURATION
% Resolution of the heatmap
num_vertical_divisions = 36;
num_horizontal_divisions = 64;
% Scales intensity of the heatmap's red/blue tint: higher values will
% exaggerate the tinting
color_intensity_factor = 7;
% Set to true to construct an "average" image used for the final overlay
% image. Otherwise, the first frame of the sequence will be used
use_average_image_overlay = 1;

fprintf('Loading images and initializing\n');
frame_files = dir('*.jpg');
[height, width, null] = size(imread(frame_files(1).name));  % Dimensions of images
[num_frames, null] = size(frame_files);  % Number of total frames
num_blocks = num_horizontal_divisions * num_vertical_divisions;
image_locations = zeros(1, 2, num_blocks);  % Stores pixel locations of each block
intensities = zeros(num_blocks, num_frames);  % Vertical index corresponds to block; horizonal index corresponds to intensity for a pixel within that block
average_image = zeros(height, width, 3);
average_image_red = zeros(height, width);
average_image_green = zeros(height, width);
average_image_blue = zeros(height, width);

% Select a random pixel location for each block and keep track of it
% This allows us to imread each image once, and examine the same pixel
% location every time for each new image
fprintf('Selecting random pixel locations for each block; total %i\n', num_blocks);
for block_index = 1:num_blocks
    block_row = ceil(block_index/num_horizontal_divisions);
    block_col = block_index - num_horizontal_divisions * (block_row - 1);
    random_row = (block_row - 1) * (height/num_vertical_divisions) + floor(rand * height/num_vertical_divisions) + 1;
    random_col = (block_col - 1) * (width/num_horizontal_divisions) + floor(rand * width/num_horizontal_divisions) + 1;
    image_locations(1, :, block_index) = [random_row, random_col];
end

% Iterate through every frame and keep track of the grayscale intensity at
% the randomly selected pixel above. Also construct an average image, if
% enabled.
for frame_index = 1:num_frames
    fprintf('Processing frame %i of %i\n', frame_index, num_frames);
    image = imread(frame_files(frame_index).name);
    if (use_average_image_overlay)
        average_image_red = average_image_red + double(image(:, :, 1))/num_frames;
        average_image_green = average_image_green + double(image(:, :, 2))/num_frames;
        average_image_blue = average_image_blue + double(image(:, :, 3))/num_frames;
    end
    image = double(rgb2gray(image));
    for block_index = 1:num_blocks
        pixel = image_locations(1, :, block_index);
        intensities(block_index, frame_index) = image(pixel(1), pixel(2));
    end
end
if (use_average_image_overlay)
    average_image(:, :, 1) = average_image_red;
    average_image(:, :, 2) = average_image_green;
    average_image(:, :, 3) = average_image_blue;
end

% Generate a heatmap by considering the standard deviation of the signal at
% each block
fprintf('Generating standard deviation heatmap\n');
heatmap = zeros(num_vertical_divisions, num_horizontal_divisions);
for block_index = 1:num_blocks
    block_row = ceil(block_index/num_horizontal_divisions);
    block_col = block_index - num_horizontal_divisions * (block_row - 1);
    heatmap(block_row, block_col) = std(intensities(block_index, :));
end
heatmap_filt = imgaussfilt(heatmap, 1.5);
figure, mesh(heatmap_filt);
title(sprintf('Time-averaged spatial concentration of motion; Gaussian-filtered (\\sigma = 1.5, N = %i)', num_frames));
xlabel('Horizontal block index');
ylabel('Vertical block index');
zlabel('Standard deviation of grayscale intensity');

% Create the final output image by adjusting the RGB channel values of each
% pixel according to the heatmap's value
fprintf('Creating output image with heatmap overlay\n');
mean_std = mean(mean(heatmap_filt));
if (use_average_image_overlay)
    overlay_image = uint8(average_image);
else
    overlay_image = imread(frame_files(1).name);
end
output_image = overlay_image;
for i = 1:height
    for j = 1:width
        vertical_index = ceil(num_vertical_divisions * i/height);
        horizontal_index = ceil(num_horizontal_divisions * j/width);
        output_image(i, j, :) = overlay_image(i, j, :);
        output_image(i, j, 1) = overlay_image(i, j, 1) + color_intensity_factor*(heatmap_filt(vertical_index, horizontal_index) - mean_std);
        if (output_image(i, j, 1) > 255)
            output_image(i, j, 1) = 255;
        end
        output_image(i, j, 3) = overlay_image(i, j, 3) - color_intensity_factor*(heatmap_filt(vertical_index, horizontal_index) - mean_std);
        if (output_image(i, j, 3) < 0)
            output_image(i, j, 3) = 0;
        end
    end
end
figure, imshow(output_image);
title('Motion heatmap');