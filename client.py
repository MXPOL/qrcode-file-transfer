#!/usr/bin/env python
import PySimpleGUI as sg
import cv2
import numpy as np
import imutils
import time
from pyzbar import pyzbar
from PIL import Image
import os
import json

from concurrent.futures import ThreadPoolExecutor
from io import BytesIO

from status import TransferStatus
from file_to_qr import qr_data_into_img_bytes, status_to_qr
from file_to_qr import write_qr_code
from qr_to_file import reconstruct_files_from_qr

from utils import delete_dir, get_qr_data, get_frame_from_camera, get_qr_from_camera, get_camera_list

from const import OUTPUT_DIR, TEMP_CLIENT_DIR, WEB_IMG_SIZE



def main():
    
    # Capture and Camera 
    video_capture = cv2.VideoCapture(0)
    cameras_list = [0,1] #get_camera_list()
    
    
    # Create the window
    sg.theme('BluePurple')
    cap = cv2.VideoCapture(0)
    
    configuration_layout = [
        [ sg.Text('Camera:  '), sg.Combo(cameras_list, default_value='0', key='caemra_index', size=(10, 1))],
        [
            sg.Text('QR Fill Color:  '), sg.Combo(['black', 'white'], default_value='black', key='qr_fill_color'),
            sg.Text('QR Back Color:  '), sg.Combo(['yellow', 'white'], default_value='white', key='qr_back_color'),
        ],
    ]
    
    layout = [
        [sg.Text('Client', size=(40, 1), justification='center', font='Helvetica 20')],
        [sg.Frame(title='Configurations:', size=(430,80),layout=configuration_layout)],
        [sg.Button('Start Client', size=(30, 1), font='Helvetica 14')],
        [sg.Frame(title='Status:', size=(430,70),layout=[ [sg.Text(key='current_chunk'),sg.Text('', key='current_status')] ])],
        [sg.Column([[sg.Image(key="web-image")]], element_justification='left', vertical_alignment='top'), sg.Column([[sg.Image(key="qr-image")]], element_justification='c')],  
        [
            sg.Button('Show Camera', size=(15, 1), font='Helvetica 14'),
            sg.Button('Stop Camera', size=(10, 1), font='Any 14'),
            sg.Button('Exit', size=(10, 1), font='Helvetica 14'), 
        ]
    ]
    
    window = sg.Window('Client2', layout, margins=(10, 0), size=(1100, 1100), element_justification='c')
    
    # Current Status
    status = TransferStatus.CLIENT_NOT_READY.value
    
    current_chunk = 0
    total_chunks = 0
    input_file_name = None
    qr_images_arr = []
    recived_file_path = None
    # Const
    
    output_folder = 'out_client'
    
    
    update_qr_img = False
    current_qr_status_img_bytes = None
    
      
    show_camera = False
    
    
    
    while True:
        event, values = window.read(timeout=20)
        
        # Print the current status to the GUI
        window["current_status"].update(f"Current Status: {status} \nFile Name: {input_file_name} \nCurrent Chunk: {current_chunk} \nTotal Chunks: {total_chunks} ")
        
        
        # Update the current status to the QR img in the GUI
        if update_qr_img:
            window["qr-image"].update(data=current_qr_status_img_bytes)
            update_qr_img = False
        
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        
        elif event == 'Stop Camera':
            show_camera = False
            window['web-image'].Update(visible=False)
            # window["qr-image"].update(data=current_qr_status_img_bytes)
            
        elif event == 'Show Camera':
            if video_capture is None:
                camera_index = int(values["caemra_index"])
                video_capture = cv2.VideoCapture(camera_index)
            show_camera = True
            window['web-image'].Update(visible=True)
        
        elif event == 'Start Client':
            status = status = TransferStatus.CLIENT_READY.value
            
        if status == TransferStatus.CLIENT_READY.value:
            status = TransferStatus.LOOKING_FOR_SERVER.value
            current_qr_status_img_bytes = qr_data_into_img_bytes(status)
            update_qr_img = True
            
        
        elif status == TransferStatus.LOOKING_FOR_SERVER.value:
            qr_obj = get_qr_from_camera(video_capture)
            if qr_obj:
                if qr_obj["status"] ==  TransferStatus.CONNECTION_START.value:
                    status = TransferStatus.WATTING_FOR_FILE_INFO.value
                    current_qr_status_img_bytes = qr_data_into_img_bytes(status)
                    update_qr_img = True
        
        elif status == TransferStatus.WATTING_FOR_FILE_INFO.value:
            qr_obj = get_qr_from_camera(video_capture)
            if qr_obj:
                if qr_obj["status"] ==  TransferStatus.DATA_INFO.value:
                    input_file_name = qr_obj["name"]
                    print(f"total_chunks: {qr_obj['totalChunks']}")
                    total_chunks = int(qr_obj["totalChunks"])
                    current_chunk = 0
                    
                    # update status for the next gui update
                    status = TransferStatus.WAIT_FOR_DATA_CHUNK.value
                    current_qr_status_img_bytes = qr_data_into_img_bytes(status,input_file_name, total_chunks, current_chunk)
                    update_qr_img = True
                
        elif status == TransferStatus.WAIT_FOR_DATA_CHUNK.value:
            frame = get_frame_from_camera(video_capture)
            qr_obj = get_qr_data(frame)
            
            if qr_obj:
                if qr_obj["status"] ==  TransferStatus.DATA_CHUNK.value:
                    # Add here more tests to check that its right??
                    if qr_obj["currentChunk"] == current_chunk:
                        qr_file_name = 'qr_chunk_{current_chunk}.png'.format(current_chunk=current_chunk)
                        qr_file = os.path.join(TEMP_CLIENT_DIR, qr_file_name)
                        qr_images_arr.append(qr_file)
                        write_qr_code(qr_file, qr_obj)
                        
                        
                        if (int(current_chunk) == (total_chunks - 1)):
                            status = TransferStatus.CLIENT_RECIVED_ALL_DATA_CHUNKS.value
                            current_qr_status_img_bytes = qr_data_into_img_bytes(status)
                            update_qr_img = True
                        else:
                            status = TransferStatus.RECIVED_DATA_CHUNK.value
                            current_qr_status_img_bytes = qr_data_into_img_bytes(status, input_file_name, total_chunks, current_chunk)
                            update_qr_img = True
                            current_chunk += 1
                    
        elif status == TransferStatus.RECIVED_DATA_CHUNK.value:
            qr_obj = get_qr_from_camera(video_capture)
            
            if qr_obj:
                if qr_obj["status"] ==  TransferStatus.READY_TO_SEND_NEXT_CHUNK.value:
                    if qr_obj["currentChunk"] == current_chunk:
                        status = TransferStatus.WAIT_FOR_DATA_CHUNK.value
                        current_qr_status_img_bytes = qr_data_into_img_bytes(status, input_file_name, total_chunks, current_chunk)
                        update_qr_img = True
                        
        elif status == TransferStatus.CLIENT_RECIVED_ALL_DATA_CHUNKS.value:
            recived_file_path =  reconstruct_files_from_qr(qr_images_arr, OUTPUT_DIR)
            status = TransferStatus.CLIENT_FINISHED.value
            delete_dir(TEMP_CLIENT_DIR)
            
        elif status == TransferStatus.CLIENT_FINISHED.value:
            sg.popup(f" Client finished reciving the file: {recived_file_path}")
            return
            
        
            

            
    
        if show_camera:
            frame = get_frame_from_camera(video_capture)
            resized_frame = cv2.resize(frame, WEB_IMG_SIZE)
            imgbytes = cv2.imencode('.png', resized_frame)[1].tobytes()
            window["web-image"].update(data=imgbytes)
                 



main()
    
    
    
    