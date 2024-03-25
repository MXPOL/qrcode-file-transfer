#!/usr/bin/env python
import PySimpleGUI as sg
import cv2
import numpy as np
from imutils.video import VideoStream
import imutils
import time
from pyzbar import pyzbar
from PIL import Image
import os
import json

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

from status import TransferStatus
from utils import delete_dir, get_qr_data, get_frame_from_camera, get_qr_from_camera, get_camera_list
from file_to_qr import status_to_qr, data_info_to_qr, qr_data_into_img_bytes
from const import QR_IMG_SIZE, DATA_PER_CHUNK_BYTES_OPTION, TEMP_SERVER_DIR, WEB_IMG_SIZE

    
def main():
    
    # Capture and Camera 
    video_capture = None
    cameras_list = [0,1]  # get_camera_list()

    # Create the window
    sg.theme('LightGreen')
    layout = [
        [sg.Text('Server3', size=(40, 1), justification='center', font='Helvetica 20')],
        [sg.Text('Path to file'), sg.In(size=(50,10), key='input', enable_events=True), sg.FileBrowse()],
        [sg.Frame(title='Configurations:', size=(430,80),layout=[
            [ sg.Text('Camera:  '), sg.Combo(cameras_list, default_value='0', key='caemra_index', size=(10, 1))],
            [
                sg.Text('QR Fill Color:  '), sg.Combo(['black', 'white'], default_value='black', key='qr_fill_color'),
                sg.Text('QR Back Color:  '), sg.Combo(['yellow', 'white'], default_value='white', key='qr_back_color'),
            ],
            [ sg.Text('Data Per Chunk Bytes:  '), sg.Combo(DATA_PER_CHUNK_BYTES_OPTION, default_value=DATA_PER_CHUNK_BYTES_OPTION[0], key='data_per_chunk_selection'),]
            ])
         ],
        [sg.Button('Start Server', size=(40, 1), font='Helvetica 14')],
        [sg.Frame(title='Status:', size=(430,70),layout=[
            [sg.Text(key='current_chunk'),sg.Text('', key='current_status')],
            ])
        ],
        [sg.Column([[sg.Image(key="web-image")]], element_justification='left', vertical_alignment='top'), sg.Column([[sg.Image(key="qr-image")]], element_justification='c')],
        [
        sg.Button('Show Camera', size=(15, 1), font='Helvetica 14'),
        sg.Button('Stop Camera', size=(10, 1), font='Any 14'),
        sg.Button('Exit', size=(10, 1), font='Helvetica 14'), 
        ],
    ]
    window = sg.Window('Server', layout, margins=(10, 0),size=(1000, 1100), element_justification='c')

    # Initial status of the server
    status = TransferStatus.SERVER_NOT_READY.value
    


    # CURRENT STATUS
    # current file being transfered
    is_file_selected = False
    current_chunk = 0
    total_chunks = 0
    file_full_path = None
    input_file_name = None
    qr_images_arr = []

    update_qr_img = False
    current_gui_img_in_bytes = None
    
    
    show_camera = False
    

    while True:
        # read values from GUI
        event, values = window.read(timeout=20)
                    
        # Print the current status to the GUI
        window["current_status"].update(f"Current Status: {status} \nFile Name: {input_file_name} \nCurrent Chunk: {current_chunk} \nTotal Chunks: {total_chunks} ")


        # Update the current status to the QR img in the GUI
        if update_qr_img:
            window["qr-image"].update(data=current_gui_img_in_bytes)
            update_qr_img = False

        # if file path is selected
        if event == "input":
            file_full_path = values["input"]
            if file_full_path:
                input_file_name = os.path.basename(file_full_path)
                is_file_selected = True
                
        if show_camera:
            frame = get_frame_from_camera(video_capture)
            resized_frame = cv2.resize(frame, WEB_IMG_SIZE)
            imgbytes = cv2.imencode('.png', resized_frame)[1].tobytes()
            window["web-image"].update(data=imgbytes)




        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        
        elif event == 'caemra_index':
            print(f"Camera index: {values['caemra_index']}")
        
    
        elif event == 'Stop Camera':
            show_camera = False
            window['web-image'].Update(visible=False)
            
        elif event == 'Show Camera':
            if video_capture is None:
                camera_index = int(values["caemra_index"])
                video_capture = cv2.VideoCapture(camera_index)
            show_camera = True
            window['web-image'].Update(visible=True)

        elif event == 'Start Server':
            
            if not is_file_selected:
                sg.popup("Please select a file!")
                continue
            
            # Users selected configurations
            data_per_chunk_bytes = values["data_per_chunk_selection"]
            qr_fill_color = values["qr_fill_color"]
            qr_back_color = values["qr_back_color"]
            camera_index = int(values["caemra_index"])
            
            from file_to_qr import convert_file_to_qr
            # array of path to qr images with metadata
            qr_images_arr = convert_file_to_qr(file_full_path, TEMP_SERVER_DIR, data_per_chunk_bytes, qr_fill_color, qr_back_color)
            total_chunks = len(qr_images_arr)
            current_chunk = 0
            print(f"Total Chunks: {total_chunks}")
            status = TransferStatus.SERVER_READY.value

                
    
        elif status == TransferStatus.SERVER_READY.value:
            print("Server is ready")
            # init caputre instance with camera index
            video_capture = cv2.VideoCapture(camera_index)
            
            # after camera is ready, we are waiting for client
            status = TransferStatus.WATTING_FOR_CLIENT.value

        
        elif status == TransferStatus.WATTING_FOR_CLIENT.value:
            print("WATTING_FOR_CLIENT")
            qr_obj = get_qr_from_camera(video_capture)
            if qr_obj:
                 if qr_obj["status"] ==  TransferStatus.LOOKING_FOR_SERVER.value:
                    status = TransferStatus.CONNECTION_START.value
                    # update GUI img in the next iteration
                    # create a qr image with CONNECTION_START status
                    current_gui_img_in_bytes = qr_data_into_img_bytes(status,input_file_name,total_chunks, current_chunk)
                    # in the next GUI iteration, gui image will be updated
                    update_qr_img = True

        elif status == TransferStatus.CONNECTION_START.value:            
            # wait till the client recived connection started qr and wait for waiting for file info QR from client
            qr_obj = get_qr_from_camera(video_capture)
            if qr_obj:
                if qr_obj["status"] ==  TransferStatus.WATTING_FOR_FILE_INFO.value:
                    status = TransferStatus.DATA_INFO.value
                    # update GUI img in the next iteration
                    # create a qr image with DATA_INFO status
                    current_gui_img_in_bytes = qr_data_into_img_bytes(status,input_file_name,total_chunks, current_chunk)
                    # in the next GUI iteration, gui image will be updated
                    update_qr_img = True
                    
        
        elif status == TransferStatus.DATA_INFO.value:
            print("DATA_INFO")
            # Create a qr image with DATA_INFO status and input file name and total chunks
            # current_gui_img_in_bytes = qr_data_into_img_bytes(status, input_file_name, total_chunks)
            # in the next GUI iteration, we will update the qr image
            # update_qr_img = True
            
            qr_obj = get_qr_from_camera(video_capture)
            if qr_obj:
                # wait till the client recived data info QR and wait for client request for data chunk
                if qr_obj["status"] ==  TransferStatus.WAIT_FOR_DATA_CHUNK.value:
                    # check that the client waits for the first data chunk
                    if current_chunk == qr_obj["currentChunk"]:
                        status = TransferStatus.DATA_CHUNK.value

                    
        elif status == TransferStatus.DATA_CHUNK.value:
            
            # read the data chunk qr image and convert it to bytes to the GUI
            qr_img_path = qr_images_arr[current_chunk]
            print(f"DATA CHUNK qr_img_path: {qr_img_path}")
            # read the image from the qr_img 
            original_image = Image.open(qr_img_path)
            resized_image = original_image.resize(QR_IMG_SIZE)
            img_bytes = BytesIO()
            resized_image.save(img_bytes, format='PNG')
            
            
            # don't update the qr image in GUI if the image is the same as the previous one
            if img_bytes.getvalue() != current_gui_img_in_bytes:
                current_gui_img_in_bytes = img_bytes.getvalue()
                update_qr_img = True
            
            qr_obj = get_qr_from_camera(video_capture)
            if qr_obj:
                # transfer is not finished, client recived data chunk and wait for the next data chunk
                if qr_obj["status"] ==  TransferStatus.RECIVED_DATA_CHUNK.value:
                    if qr_obj["currentChunk"] == current_chunk:
                        current_chunk += 1
                        status = TransferStatus.READY_TO_SEND_NEXT_CHUNK.value
                        current_gui_img_in_bytes = qr_data_into_img_bytes(status,input_file_name,total_chunks, current_chunk)
                        # in the next GUI iteration, gui image will be updated
                        update_qr_img = True
                        
                
                # tranfer is finished, client recived all data chunks
                elif qr_obj["status"] ==  TransferStatus.CLIENT_RECIVED_ALL_DATA_CHUNKS.value:
                    status = TransferStatus.SERVER_FINISHED.value
   
        elif status == TransferStatus.READY_TO_SEND_NEXT_CHUNK.value:
                        
            qr_obj = get_qr_from_camera(video_capture)
            if qr_obj:
                # wait till the client recived data info QR and wait for client request for data chunk
                if qr_obj["status"] ==  TransferStatus.WAIT_FOR_DATA_CHUNK.value:
                    status = TransferStatus.DATA_CHUNK.value
        
        elif status == TransferStatus.CLIENT_RECIVED_ALL_DATA_CHUNKS.value:
            status = TransferStatus.SERVER_FINISHED.value

            
        
        elif status == TransferStatus.SERVER_FINISHED.value:
            delete_dir(TEMP_SERVER_DIR)
            sg.popup("Server Finished")
            return
                                
        
                





main()