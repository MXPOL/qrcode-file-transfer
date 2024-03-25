# qrcode-file-transfer

This Python-based client-server application facilitates data transfer using QR codes. It employs cameras on both the server and client sides to scan QR codes, enabling seamless data transmission.

# Protocol diagram

![diagram](./diagram.png)

# Usage


## Arguments


## Example

### Client
![client](./client.png)

### Server
![server](./server.png)


## Tips



# Installation
## Requirements
* Python 3
* Encode
  * qrcode
  * Image
* Decode
  * Pillow
  * numpy
  * zbar-py

## From source
1. Clone the repository
2. Run `make install`
    * This command uses pip to install a wheel. If you are using a python virtual environment, be sure to activate it before installing.

## From source without installing
1. Clone the repo
2. Install dependencies via `pip install -r requirements.txt`