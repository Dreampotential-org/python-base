import tensorflow as tf
import numpy as np
import cv2
import os
#from web.settings import BASE_DIR
BASE_DIR = "/codes"

os.environ['TF_XLA_FLAGS'] = '--tf_xla_enable_xla_devices'
# RetinaFace face detector
saved_model_dir = f"{BASE_DIR}/faceswap/tf_retinaface/"
detector_model = tf.saved_model.load(saved_model_dir)


def one_face(frame, bbs, pointss):
    # process only one face (center ?)
    offsets = [(bbs[:,0]+bbs[:,2])/2-frame.shape[1]/2,
               (bbs[:,1]+bbs[:,3])/2-frame.shape[0]/2]
    offset_dist = np.sum(np.abs(offsets),0)
    index = np.argmin(offset_dist)
    bb = bbs[index]
    points = pointss[:,index]
    return bb, points


def draw_landmarks(frame, bb, points):
    # draw rectangle and landmarks on face
    cv2.rectangle(frame,(int(bb[0]),int(bb[1])),(int(bb[2]),int(bb[3])),orange,2)
    cv2.circle(frame, (int(points[0]), int(points[5])), 2, (255,0,0), 2)# eye
    cv2.circle(frame, (int(points[1]), int(points[6])), 2, (255,0,0), 2)
    cv2.circle(frame, (int(points[2]), int(points[7])), 2, (255,0,0), 2) # nose
    cv2.circle(frame, (int(points[3]), int(points[8])), 2, (255,0,0), 2) # mouth
    cv2.circle(frame, (int(points[4]), int(points[9])), 2, (255,0,0), 2)

    w = int(bb[2])-int(bb[0]) # width
    h = int(bb[3])-int(bb[1]) # height
    w2h_ratio = w/h # ratio
    eye2box_ratio = (points[0]-bb[0]) / (bb[2]-points[1])
  
def face_detector(image, image_shape_max=640, score_min=None, pixel_min=None, pixel_max=None, Ain_min=None):
    '''
    Performs face detection using retinaface method with speed boost and initial quality checks based on whole image size
    
    Parameters
    ----------
    image : uint8
        image for face detection.
    image_shape_max : int, optional
        maximum size (in pixels) of image. The default is None.
    score_min : float, optional
        minimum detection score (0 to 1). The default is None.
    pixel_min : int, optional
        mininmum face size based on heigth of bounding box. The default is None.
    pixel_max : int, optional
        maximum face size based on heigth of bounding box. The default is None.
    Ain_min : float, optional
        minimum area of face in bounding box. The default is None.

    Returns
    -------
    float array
        landmarks.
    float array
        bounding boxes.
    flaot array
        detection scores.
    float array
        face area in bounding box.

    '''

    image_shape = image.shape[:2]
    
    # perform image resize for faster detection    
    if image_shape_max:
        scale_factor = max([1, max(image_shape)/image_shape_max])
    else:
        scale_factor = 1
        
    if scale_factor > 1:        
        scaled_image = cv2.resize(image, (0, 0), fx=1/scale_factor, fy=1/scale_factor)
        bbs_all, points_all = retinaface(scaled_image)
        bbs_all[:,:4]*=scale_factor
        points_all*=scale_factor
    else:
        bbs_all, points_all = retinaface(image)
    
    bbs=bbs_all.copy()
    points=points_all.copy()
    
    # check detection score
    if score_min:
        mask=np.array(bbs[:,4]>score_min)
        bbs=bbs[mask]
        points=points[mask]
        if len(bbs)==0:
            return [],[],[],[]           

    # check pixel height
    if pixel_min: 
        pixel=bbs[:,3]-bbs[:,1]
        mask=np.array(pixel>pixel_min)
        bbs=bbs[mask]
        points=points[mask]
        if len(bbs)==0:
            return [],[],[],[]           

    if pixel_max: 
        pixel=bbs[:,3]-bbs[:,1]
        mask=np.array(pixel<pixel_max)
        bbs=bbs[mask]
        points=points[mask]
        if len(bbs)==0:
            return [],[],[],[]           

    # check face area in bounding box
    Ains = []
    for bb in bbs:
        Win=min(image_shape[1],bb[2])-max(0,bb[0])
        Hin=min(image_shape[0],bb[3])-max(0,bb[1])
        Abb=(bb[2]-bb[0])*(bb[3]-bb[1])
        Ains.append(Win*Hin/Abb*100 if Abb!=0 else 0)
    Ains = np.array(Ains)

    if Ain_min:
        mask=np.array(Ains>=Ain_min)
        bbs=bbs[mask]
        points=points[mask]
        Ains=Ains[mask]
        if len(bbs)==0:
            return [],[],[],[]           
    
    scores = bbs[:,-1]
    bbs = bbs[:, :4]
    
    return points, bbs, scores, Ains

def retinaface(image):

    height = image.shape[0]
    width = image.shape[1]
    
    image_pad, pad_params = pad_input_image(image)    
    image_pad = tf.convert_to_tensor(image_pad[np.newaxis, ...])
    image_pad = tf.cast(image_pad, tf.float32)  
   
    outputs = detector_model(image_pad).numpy()

    outputs = recover_pad_output(outputs, pad_params)
    Nfaces = len(outputs)
    
    bbs = np.zeros((Nfaces,5))
    lms = np.zeros((Nfaces,10))
    
    bbs[:,[0,2]] = outputs[:,[0,2]]*width
    bbs[:,[1,3]] = outputs[:,[1,3]]*height
    bbs[:,4] = outputs[:,-1]
    
    lms[:,0:5] = outputs[:,[4,6,8,10,12]]*width
    lms[:,5:10] = outputs[:,[5,7,9,11,13]]*height
    
    return bbs, lms

def pad_input_image(img, max_steps=32):
    """pad image to suitable shape"""
    img_h, img_w, _ = img.shape

    img_pad_h = 0
    if img_h % max_steps > 0:
        img_pad_h = max_steps - img_h % max_steps

    img_pad_w = 0
    if img_w % max_steps > 0:
        img_pad_w = max_steps - img_w % max_steps

    padd_val = np.mean(img, axis=(0, 1)).astype(np.uint8)
    img = cv2.copyMakeBorder(img, 0, img_pad_h, 0, img_pad_w,
                             cv2.BORDER_CONSTANT, value=padd_val.tolist())
    pad_params = (img_h, img_w, img_pad_h, img_pad_w)

    return img, pad_params

def recover_pad_output(outputs, pad_params):
    """recover the padded output effect"""
    img_h, img_w, img_pad_h, img_pad_w = pad_params
    recover_xy = np.reshape(outputs[:, :14], [-1, 7, 2]) * \
        [(img_pad_w + img_w) / img_w, (img_pad_h + img_h) / img_h]
    outputs[:, :14] = np.reshape(recover_xy, [-1, 14])

    return outputs


font = cv2.FONT_HERSHEY_COMPLEX # Text in video
font_size = 0.4
blue = (225,0,0)
green = (0,128,0)
red = (0,0,255)
orange = (0,140,255)


def send_face(frame):
   
    frame = np.array(frame)
    frame = cv2.flip(frame,1)
    
    res_crop = np.asarray(frame.shape)[0:2]# ?   
    
    #bbs_all, pointss_all = detector.detect_faces(frame)# face detection
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pointss_all, bbs_all, scores_all, _ = face_detector(frame_rgb, image_shape_max=640, score_min=0.95,
                                                        pixel_min=20, pixel_max=1000, Ain_min=90)
    
    
    
    if len(bbs_all) > 0:# if at least one face is detected
        #process only one face (center ?)  

        # print(bbs_all)
        bbs_all = np.insert(bbs_all,bbs_all.shape[1],scores_all,axis=1)
        pointss_all = np.transpose(pointss_all)
        
        bbs = bbs_all.copy()
        pointss = pointss_all.copy()

        bb,points = one_face(frame, bbs, pointss)
        
        draw_landmarks(frame, bb, points)# draw land marks on face   
            
    # cv2.imshow('Pose Detection - Retina Face',frame)
    return frame
