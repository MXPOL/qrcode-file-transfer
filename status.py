from enum import Enum

# Define an enumeration class
class TransferStatus(Enum):
    CLIENT_NOT_READY = "CLIENT_NOT_READY"
    CLIENT_READY = "CLIENT_READY"

    SERVER_NOT_READY = "SERVER_NOT_READY"
    SERVER_READY = "SERVER_READY"

    LOOKING_FOR_SERVER = "LOOKING_FOR_SERVER" 


    CONNECTION_START = "CONNECTION_START" 
    
    
    WATTING_FOR_CLIENT = "WATTING_FOR_CLIENT"

    WATTING_FOR_FILE_INFO = "WATTING_FOR_FILE_INFO"
    
    DATA_INFO = "DATA_INFO" 



    DATA_CHUNK = "DATA_CHUNK" 


    RECIVED_DATA_CHUNK = "RECIVED_DATA_CHUNK" 



    WAIT_FOR_DATA_CHUNK = "WAIT_FOR_DATA_CHUNK" # { "status": "WAIT_FOR_DATA_CHUNK", "wanntedChunk": 0 }
    
    READY_TO_SEND_NEXT_CHUNK = "READY_TO_SEND_NEXT_CHUNK" # { "status": "READY_TO_SEND_NEXT_CHUNK", "wanntedChunk": 0 }

    
    CLIENT_RECIVED_ALL_DATA_CHUNKS = "CLIENT_RECIVED_ALL_DATA_CHUNKS"
    
    CLIENT_FINISHED = "CLIENT_FINISHED"
    
    SERVER_FINISHED = "SERVER_FINISHED"

    

    