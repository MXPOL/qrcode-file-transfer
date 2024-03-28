''' Contains utilities to convert files to QR codes.
'''
import json
import logging
import math
import os
import sys
import uuid
from base64 import b64encode
from status import TransferStatus
from PIL import Image, ImageDraw, ImageFont
from const import QR_IMG_SIZE

import qrcode

from io import BytesIO

from utils import confirm_dir, open_file

LOGGER = logging.getLogger(__name__)

# The number of bytes of file data allowed per QR code.
# The zbar parser can only handle so much data per QR code.
DATA_PER_CHUNK_BYTES = 250

# def qr_code_to_bytes(data, fill_color='black', back_color='white'):
#     ''' Converts the data to a QR code, which is returned as a PNG.

#     Paramters:
#       data <string> The data to encode into the QR code.
#     '''
#     qr = qrcode.QRCode(version = 1, box_size = 10, border = 1 )
#     qr.add_data(data)
#     qr.make(fit=True)
#     img = qr.make_image(fill_color=fill_color, back_color=back_color)
#     return img.tobytes()

def write_qr_code(output_file, data, fill_color='black', back_color='white'):
    ''' Writes the data to a QR code, which is saved to the indicated file as a PNG.

    Paramters:
      output_file <string> The file to save the QR code to, encoded as PNG.
      data <string> The data to encode into the QR code.
    '''
    # img = qrcode.make(data)
    # img.save(output_file, scale=100)
    
    # get folder name from output_file
    folder_name = os.path.dirname(output_file)
    
    if not confirm_dir(folder_name):
        LOGGER.warn('Failed to create output directory: %s', folder_name)
        return
    
    # create folder if it doesn't exist
    

    qr = qrcode.QRCode(version = 1, box_size = 10, border = 1 )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    
    img.save(output_file)

def convert_file_to_qr(input_file, output_directory='', data_per_chunk_bytes=500, fill_color='black', back_color='white'):
    ''' Converts the specified file to a series of QR code images.

    The images are saved in the output directory.

    Parameters:
      input_file <string> The file to convert to QR codes.
      output_directory <string> [Optional] The directory to save the generated QR codes to.
        This directory is created if it doesn't exist.
    '''
    # Try to create the output directory if it doesn't exist.
    if not confirm_dir(output_directory):
        LOGGER.warn('Failed to create output directory: %s', output_directory)
        return

    with open_file(input_file, 'rb') as (f, err):
        # Bad file open handling
        if err:
            print('Unable to read input file {f}. More info below:'.format(f=input_file))
            print('\t{e}'.format(e=err))
            return

        # Read the file as binary and convert to b64
        data = f.read()

        b64_data = b64encode(data).decode('ascii')
        b64_data_len = len(b64_data)

        # Split into chunks.
        # This is required to keep QR codes to a parseable size.
        num_bytes = data_per_chunk_bytes
        num_chunks = math.ceil(len(b64_data) / num_bytes)
        input_file_name = os.path.basename(input_file)

        print('Encoding file {f}...'.format(f=input_file_name))
        LOGGER.debug('b64_data_len: %d', b64_data_len)
        LOGGER.debug('num_chunks: %d', num_chunks)
        LOGGER.debug('input_file_name: %s', input_file_name)

        output_files_arr = []

        # Write each chunk into a QR code
        for i in range(0, num_chunks):
            # Start and stop indicies of the b64 string for this chunk
            start_index = num_bytes * i
            end_index = num_bytes * (i + 1)

            LOGGER.debug('start_index: %d', start_index)
            LOGGER.debug('end_index: %d', end_index)

            # Construct payload to be placed into the QR code
            payload = { # len = 38 w/o name and data
                'status': TransferStatus.DATA_CHUNK.value,
                'currentChunk': i, # This chunk of the file
                'totalChunks': num_chunks - 1, # Total chunks of the file
                'name': input_file_name, # File name
                'data': b64_data[start_index:end_index] # limit is ~650. Go 625 to be safe
            }
            # Dump to JSON with special separators to save space
            payload_json = json.dumps(payload, separators=(',',':'))
            LOGGER.debug('json dumps length {test}'.format(test=len(payload_json)))

            # Write QR code to file
            qr_file_name = '{file}_q{count}.png'.format(file=input_file_name, count=i)
            qr_file = os.path.join(output_directory, qr_file_name)
            LOGGER.debug('qr_file: %s', qr_file)

            write_qr_code(qr_file, payload_json, fill_color, back_color)
            output_files_arr.append(qr_file)

        # Status msg
        print('Encoded file {f} in {n} QR codes.'.format(f=input_file_name, n=num_chunks))
        return output_files_arr

def status_to_qr(status, currentPic, qr_fill_color, qr_back_color):

    payload = { # len = 38 w/o name and data
        'status': status, # This chunk of the file
        'currentPic': currentPic, # Total chunks of the file
    }
    # Dump to JSON with special separators to save space
    payload_json = json.dumps(payload, separators=(',',':'))
    LOGGER.debug('json dumps length {test}'.format(test=len(payload_json)))

    # Write QR code to file
    qr_file_name = '{status}_q{currentPic}.png'.format(status=status, currentPic=currentPic)
    qr_file = os.path.join("out", qr_file_name)
    LOGGER.debug('qr_file: %s', qr_file)

    write_qr_code(qr_file, payload_json, qr_fill_color, qr_back_color)
    return qr_file


def data_info_to_qr(status, name, total_chunks, qr_fill_color, qr_back_color):

    payload = { # len = 38 w/o name and data
        'status': status, # This chunk of the file
        'name': name,
        'totalChunks': total_chunks
    }
    # Dump to JSON with special separators to save space
    payload_json = json.dumps(payload, separators=(',',':'))
    LOGGER.debug('json dumps length {test}'.format(test=len(payload_json)))

    # Write QR code to file
    qr_file_name = '{status}_name_{name}_total_{total_chunks}.png'.format(status=status, name=name, total_chunks=total_chunks)
    qr_file = os.path.join("out", qr_file_name)
    LOGGER.debug('qr_file: %s', qr_file)

    write_qr_code(qr_file, payload_json, qr_fill_color, qr_back_color)
    return qr_file
            

def qr_data_into_img_bytes(fill_color, back_color, status, name = "", total_chunks = "", current_chunk=0, data = ""):
    
    payload = { 
        'status': status,
        'name': name,
        'totalChunks': total_chunks,
        'currentChunk': current_chunk,
        'data': data,
    }
    
    
    # Dump to JSON with special separators to save space
    payload_json = json.dumps(payload, separators=(',',':'))

    qr = qrcode.QRCode(version = 1, box_size = 10, border = 1 )
    qr.add_data(payload_json)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    
    resized_img = img.resize(QR_IMG_SIZE)
    
    img_bytes = BytesIO()
    
    resized_img.save(img_bytes, format="PNG")
    
    

    return img_bytes.getvalue()