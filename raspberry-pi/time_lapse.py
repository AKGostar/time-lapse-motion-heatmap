"""
This Python script simply takes a picture and saves it to a directory with a proper file name.
It's intended to be put in cron, to run every n minutes.
"""

import os
import sys
import argparse
import picamera


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--save-directory', help='Path at which frames should be saved')
    args = parser.parse_args()

    if not args.save_directory:
        print 'No save directory parameter passed; exiting.'
        print 'Please pass a directory to the -d or --save-directory argument.'
        sys.exit()

    camera = picamera.PiCamera()
    camera.hflip = True
    camera.vflip = True
    existing_frames = sorted(os.listdir(args.save_directory))
    if len(existing_frames) == 0:
        save_index = 0
    else:
        save_index = int(existing_frames[-1].split('.')[0].split('-')[1])  # Expect file names to be of form 'frame-00001.jpg'
    camera.capture(os.path.join(args.save_directory, 'frame-%05d.jpg' % (save_index + 1,)))

