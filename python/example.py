import os
import motion_heatmap


if __name__ == '__main__':
    image_path = 'frames'
    images = sorted([
        image_path + '/' + f for f in os.listdir(image_path)
        if os.path.isfile(os.path.join(image_path, f)) and f.endswith('.jpg')
    ])
    mh = motion_heatmap.MotionHeatmap(
        num_vertical_divisions=36,
        num_horizontal_divisions=64,
        images=images,
    )
    mh.generate_motion_heatmap()
