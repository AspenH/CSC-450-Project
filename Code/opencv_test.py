import cv2, ujson, numpy

camera = cv2.VideoCapture(0)

#Get a frame
ret_val, frame = camera.read()

#Encode and convert to list
frame2 = cv2.imencode('.jpg', frame)[1].tolist()
frame3 = ujson.dumps(frame2)

#Convert and decode to numpy array
frame4 = ujson.loads(frame3)
frame5 = numpy.asarray(frame4, numpy.uint8)
frame6 = cv2.imdecode(frame5, cv2.IMREAD_COLOR)

#Display frame
cv2.imshow('test', frame6)
cv2.waitKey(0)
cv2.destroyAllWindows()