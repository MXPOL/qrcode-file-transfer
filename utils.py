import logging
import os
import sys
import cv2
from contextlib import contextmanager
import json
from pyzbar import pyzbar
import shutil

LOGGER = logging.getLogger(__name__)

LOGGER.level = logging.DEBUG

def delete_dir(dir):
    ''' Deletes a directory and all of its contents.

    Parameters:
      dir <string> The directory to delete.
    '''
    try:
        shutil.rmtree(dir)
        print('Deleted directory: {d}'.format(d=dir))
    except OSError as e:
        print('Unable to delete directory. More info below:')
        print('\t{e}'.format(e=e))
        

def confirm_dir(dir):
    ''' Confirms that a directory can be written to.

    This function does the following:
      (1) If `dir` doesn't exist, to creates it.
      (2) If `dir` exists, checks that it is a directory.

    If this function returns True, then the directory exists.
    '''
    if dir == '':
        return True
    elif not os.path.exists(dir):
        LOGGER.debug('Ouput directory doesn\'t exist! Creating.')
        try:
            os.makedirs(dir)
            return True
        except OSError as e:
            print('Unable to create output directory. More info below:')
            print('\t{e}'.format(e=e))
            return False
    elif not os.path.isdir(dir):
        print('Output directory already exists and is not a directory. ({d})'.format(d=dir))
        return False
    else:
        return True

@contextmanager
def open_file(filename, mode='r'):
    '''Attempt to open a file.

    Yields (file_handle, error) depending on outcome.

    Adapted from: https://stackoverflow.com/a/6090497
    '''
    try:
        f = open(filename, mode)
    except OSError as err:
        yield None, err
    else:
        try:
            yield f, None
        finally:
            f.close()


def get_qr_data(input_frame):
    '''
    This function decodes the QR code from the input frame
    :param input_frame: The frame from which the QR code is to be decoded
    :return: The decoded QR code data

    '''
    try:
        res = pyzbar.decode(input_frame)
        if len(res) > 0:
            # print(f"QR code detected with data: {res[0]}")
            qr_obj = res[0]
            qr_data = qr_obj.data.decode("utf-8")
            
            LOGGER.debug(f"***QR code data: {qr_data}")
            # print(f"QR code data: {qr_data}")
            return json.loads(qr_data)
        else:
            print("No QR code detected")
            return None
    except Exception as e:
        print(e)
        print("Error while decoding QR code")
        return None


def get_frame_from_camera(video_capture):
    _, frame = video_capture.read()
    return frame

def get_qr_from_camera(video_capture):
    frame = get_frame_from_camera(video_capture)
    qr_obj = get_qr_data(frame)
    # qr_obj = get_qr_data(get_frame_from_camera(video_capture))
    print(f"QR code object: {qr_obj}")
    return qr_obj
        
        
def get_camera_list():
    index = 0
    camera_list = []

    while True:
        video_capture = cv2.VideoCapture(index)
        if not video_capture.read()[0]:
            break
        else:
            camera_list.append(index)
        video_capture.release()
        index += 1

    return camera_list
    