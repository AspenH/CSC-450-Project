"""
Project: Project Slate
Programmed by: David Williams
Last Modified:
Description: Client for the camera
Notes:
    1. camera_client needs to be installed and ran on the machine
       that will be sending the frames to the server.



Liscense:
Copyright (c) 2017, FandRec Dev Team
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the FandRec Dev Team nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL FandRec Dev Team BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
#==============================Imports=======================================
import sys, ujson, cv2

from twisted.python import log

from twisted.protocols.basic import NetstringReceiver

from autobahn.twisted.websocket import WebSocketClientFactory, \
     WebSocketClientProtocol, connectWS

from twisted.internet import reactor

#=======================Slate Interface===========================

class CameraClientProtocol(WebSocketClientProtocol):
    """
    Programmed by: David Williams
    Description: Handles the receiving messages from the 
                 server and sends the frames back.
    Notes: 
        1. 
        2.
    """
    def onMessage(self, data, isBinary):
        """
        Programmed by: David Williams
        Description: Gets a frame from the camera then 
                     encodes it as a jason then sends it.
        Notes: 
            1. This is the protocol associated with the CameraClientFactory
        """
        #STEP 1: Get frame
        _, frame = self.factory.camera.read()

        #STEP 2: Compress and Package frame
        frame = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])[1].tolist()
        frame = ujson.dumps(frame)

        #STEP 3: Send frame
        self.sendMessage(frame.encode("utf8"))

class CameraClientFactory(WebSocketClientFactory):
    """
    Programmed by: David Williams
    Description: Starts the video capture from the local camera.
    """
    def __init__(self, addr, cam_port):
        WebSocketClientFactory.__init__(self, addr)
        print("Starting Camera")
        self.camera = cv2.VideoCapture(cam_port)

#=================Client Main===================================

def main():
    """
    Programmed by: David Williams
    Description: Starts CameraClientProtocol defined above which sends
                 the frames from the camera to the server
    """
    #STEP 1: Setup the factory
    log.startLogging(sys.stdout)
    ip_address = "127.0.0.1"
    port_num = 8091

    factory = CameraClientFactory("ws://" + ip_address + ":" + str(port_num), 0)
    factory.protocol = CameraClientProtocol
    reactor.connectTCP(ip_address, port_num, factory)

    #STEP 2: Start the reactor
    reactor.run()

if __name__ == '__main__':
    main()