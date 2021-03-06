"""
Project: FACE MASK RECOGNITION, DISTANCE AND CROWD DENSITY
Member: DA0 DUY NGU, LE VAN THIEN
Instructor: PhD. TRAN THI MINH HANH
*************** CONTACT INFORMATION ***********************************
THE UNIVERSITY OF DA NANG
THE UNIVERSITY OF SCIENCE AND TECHNOLOGY
THE FACULTY OF ELECTRONIC AND TELECOMMUNICATION
Major: Computer engineering
Address: 54 Nguyen Luong Bang Street, Lien Chieu District, Da Nang city
***********************************************************************
"""

import argparse
import time
import cv2
from yolov5.detect import *
import numpy as np
import yaml
from functions_processing import get_transform, point_distance, compute_transform_matrix,\
    check_point_in_polygon
from pathlib import Path
from classification.utils.load_model import Model
from retinaface.detector import FaceDetection

# ******************************** ROOT PATH *****************************
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]
WEIGHTS = ROOT / 'weight'

# ************************************************************************
list_point_area = []


def draw_bbox(image, bboxs):
    """
    function: Draw bounding box of face
    :param image: image or frame
    :param bboxs: list bounding box and class
    :return: image
    """
    for label, bbox in bboxs:
        if label.split(':')[0] == 'without_mask':
            color = (0, 0, 255)
        else:
            color = (0, 255, 0)
        x1, y1, x2, y2 = bbox
        cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness=2, lineType=cv2.LINE_AA)
        #cv2.putText(image, label, (x1, y1+10),
        #            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2, cv2.LINE_AA)
    return image


def get_pixel(event, x, y, flags, param):
    """
    Function: Get coordinates of bird eye view
    Parameters
    ----------
    event
    x
    y
    flags
    param

    Returns
    -------
    """
    global list_point_area
    if event == cv2.EVENT_LBUTTONUP:
        if len(list_point_area) <= 3:
            cv2.circle(image_set, (x, y), 5, (0, 0, 255), 10)
        else:
            cv2.circle(image_set, (x, y), 5, (255, 0, 0), 10)
        if (len(list_point_area) >= 1) and (len(list_point_area) <= 3):
            cv2.line(image_set, (x, y), list_point_area[len(list_point_area)-1], (70, 70, 70), 2)
            if len(list_point_area) == 3:
                cv2.line(image_set, (x, y), list_point_area[0], (70, 70, 70, 2))
        if 'list_point_area' not in globals():
            list_point_area = []
        if len(list_point_area) < 8:
            list_point_area.append((x, y))


def detect_5k(url_video, path_model, path_model_cls, flag_save=False, fps=None, name_video='video.avi'):
    """
    function: detect 5k, distance, face mask, total person
    :param url_video: url of video
    :param path_model: path model detect yolov5
    :param flag_save: flag save video True or False
    :param fps: value fps
    :param name_video: name of video
    :return: None
    """
    count = 0
    # ********************** LOAD MODEL ******************************************
    y5_model = Y5Detect(weights=path_model)
    # load model face mask classification
    model = Model(path_model_cls)

    # load model face detect
    detector = FaceDetection(net='resnet50').detect_faces

    # ********************** GET CAMERA ******************************************
    if url_video == '':
        cap = cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(url_video)

    # get size
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    if frame_height > 1080 and frame_width > 1920:
        frame_width = 1920
        frame_height = 1080
    # get fps of camera
    if fps is None:
        fps = cap.get(cv2.CAP_PROP_FPS)
    # save video
    if flag_save is True:
        video_writer = cv2.VideoWriter(name_video,
                                       cv2.VideoWriter_fourcc(*'MJPG'), fps, (frame_width, frame_height))

    global image_set, list_point_area

    # ************************************* GET FRAME *************************************************
    total_frame = 0
    time_start_all = time.time()
    while True:
        start = time.time()
        ret, frame = cap.read()
        if not ret:
            break
        if cv2.waitKey(1) == ord('q'):
            break
        if cv2.waitKey(1) == ord('p'):
            while True:
                if cv2.waitKey(1) == ord('c'):
                    break

        h, w, _ = frame.shape

        if h > 1080 and w > 1920:
            frame = cv2.resize(frame, (1366, 768), interpolation=cv2.INTER_AREA)
            h, w, _ = frame.shape

        if count == 0:
            # ******************* AREA LOAD CONFIG **************************
            list_point_data = []
            with open('bird_eyes_view.yaml', 'r') as yaml_file:
                cfg = yaml.safe_load(yaml_file)
            if cfg is not None:
                for item, doc in cfg.items():
                    if doc['url'] == url_video:
                        w_cm = doc['w_cm']
                        h_cm = doc['h_cm']
                        for key in doc.keys():
                            if key == 'url' or key == 'w_cm' or key == 'h_cm':
                                continue
                            list_point_data.append(doc[key])
            if len(list_point_data) != 7:
                print('Setting ROI area and ratio width, height (cm).')
                while True:
                    image_set = frame
                    cv2.imshow('video', image_set)
                    cv2.waitKey(1)
                    if len(list_point_area) == 8:
                        break
                list_point_area.remove(list_point_area[len(list_point_area)-1])
                # ************** SETUP CAMERA ******************
                # Setup width, height of object (cm)
                w_cm = input('Enter ratio for width(cm): ')
                h_cm = input('Enter ratio for height(cm): ')
                if w_cm == '':
                    w_cm = 100
                else:
                    w_cm = int(w_cm)
                if h_cm == '':
                    h_cm = 100
                else:
                    h_cm = int(h_cm)
                if cfg is None:
                    cfg = []

                data = {f'image_parameters{len(cfg)+1}':
                            {'url': url_video,
                            'top_left': list(list_point_area[0]),
                            'top_right': list(list_point_area[1]),
                            'bottom_right': list(list_point_area[2]),
                            'bottom_left': list(list_point_area[3]),
                            'coor_1': list(list_point_area[4]),
                            'coor_2': list(list_point_area[5]),
                            'coor_3': list(list_point_area[6]),
                             'w_cm': w_cm,
                             'h_cm': h_cm}}
                with open('bird_eyes_view.yaml', 'a') as outfile:
                    yaml.dump(data, outfile, sort_keys=False)
            if len(list_point_area) != 7:
                list_point_area = list_point_data
            # ******************** AREA COMPUTE DATA ********************************
            list_bbox_frame = [[0, 0], [w, 0], [w, h], [0, h]]
            transform, h_frame, w_frame = compute_transform_matrix(list_point_area[:4], list_bbox_frame)
            # compute number pixel on distance(cm) at bird-eye map
            pts = np.float32([np.array(list_point_area[4:7])])
            tran_pts = cv2.perspectiveTransform(pts, transform)[0]
            distance_w = np.sqrt(np.sum((tran_pts[0] - tran_pts[1]) ** 2))
            distance_h = np.sqrt(np.sum((tran_pts[0] - tran_pts[2]) ** 2))
        # ************************************************************************************

        # initial coordinate spatial bottom center and x, y (pixel)
        list_transform = dict()
        list_bbox_body = dict()

        # detect body of person
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        bbox, label, score = y5_model.predict(image)
        bboxs, labels, scores = np.array(bbox), np.array(label), np.array(score)

        # *********************** GET ID PERSON AND AREA TRANSFORM ********************
        if len(bbox) > 0:
            id_person = (labels == 'person')
            bbox_person = bboxs[id_person]
            if len(bbox_person) > 0:
                # initial idx for dict
                idx = 0
                for box in bbox_person:
                    if check_point_in_polygon(box[:4], list_point_area[:4]) != 360:
                        continue
                    list_bbox_body[idx] = box[:4]
                    # transform point about bird-eyes-view
                    coors_transform = get_transform(box[:4], transform)
                    list_transform[idx] = coors_transform
                    idx += 1

        # ************************ DRAW POLYGON **********************************************
        for idx, point in enumerate(list_point_area[:4]):
            cv2.circle(frame, point, 5, (0, 0, 255), 10)
            if idx < len(list_point_area[:4]) - 1:
                cv2.line(frame, list_point_area[idx], list_point_area[idx + 1], (255, 0, 0), 2)
            else:
                cv2.line(frame, list_point_area[idx], list_point_area[0], (255, 0, 0), 2)

        # ************************ AREA TRANSFORM AND DRAW FACE MASK ************************
        bboxs_face, landmark = detector(frame)
        list_predict = []
        count_without_mask = 0
        thresh = 0
        for index, bbox in enumerate(bboxs_face):
            x1, y1, x2, y2 = [round(a) for a in bbox[0:4]]
            x1, y1, x2, y2 = max(x1 - thresh // 2, 0), max(y1 + thresh, 0), min(x2 + thresh // 2, w - 1), min(
                y2 - thresh, h - 1)
            pred = model.predict(frame[y1:y2, x1:x2])
            if pred[0] == 'without_mask':
                count_without_mask += 1
            list_predict.append((pred[0] + ': %d%%' % (round(max(pred[1])*bbox[4])), (x1, y1, x2, y2)))
        draw_bbox(frame, list_predict)

        # *************** CREATE BIRD EYES VIEW ****************************
        # set size view, map
        width_map = w_frame
        height_map = h_frame
        # draw bounding of person
        view_map = np.zeros((height_map, width_map, 3), dtype='uint8')

        # ******************************* CHECK VIOLATES **********************
        # compute distance between every person detect in a frame
        # initial set contain the index of the person that violates the distance
        violates_person = set()
        for i in list_transform.keys():
            for j in list_transform.keys():
                if i < j:
                    # compute distance between two people
                    distance = point_distance(list_transform[i], list_transform[j], distance_w, distance_h, w_cm, h_cm)
                    # check distance (2m == 200cm)
                    if distance < 200:
                        # append set index
                        violates_person.add(i)
                        violates_person.add(j)
                        x1, y1 = list_transform[i]
                        x1, y1 = int(x1 * width_map / w_frame), int(y1 * height_map / h_frame)
                        x2, y2 = list_transform[j]
                        x2, y2 = int(x2 * width_map / w_frame), int(y2 * height_map / h_frame)
                        cv2.line(view_map, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(view_map, '{} cm'.format(distance), ((x1 + x2)//2, (y1 + y2)//2),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(view_map, 'High risk: ' + str(len(violates_person)), (0, 20), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(view_map, 'Total person: ' + str(len(list_bbox_body)), (0, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 0, 255), 2, cv2.LINE_AA)

        image_transform = cv2.warpPerspective(frame, transform, (w_frame, h_frame), flags=cv2.INTER_AREA,
                                              borderMode=cv2.BORDER_WRAP)
        # ********** DRAW BOUNDING BOX AND CIRCLE ON BIRD EYE VIEWS **********
        for i in list_transform.keys():
            if i in violates_person:
                color = (0, 0, 255)
            else:
                color = (0, 255, 0)

            # convert pixel w, h about size view map
            x1, y1, x2, y2 = list_bbox_body[i]
            p_x, p_y = list_transform[i]
            cv2.circle(image_transform, (p_x, p_y), 5, color, 10)
            p_x, p_y = int(p_x*width_map/w_frame), int(p_y*height_map/h_frame)
            # draw
            cv2.circle(view_map, (p_x, p_y), 5, color, 10)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # image_transform = cv2.resize(image_transform, (1280, 720), interpolation=cv2.INTER_AREA)
        # ****************************************************************************8

        fps = int(1/(time.time()-start))
        # draw total without mask, distance violates, person, fps
        cv2.putText(frame, 'FPS:' + str(fps), (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255),
                    2, cv2.LINE_AA)
        cv2.putText(frame, 'without mask: ' + str(count_without_mask), (0, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, 'High risk: ' + str(len(violates_person)), (0, 60), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, 'Total person: ' + str(len(list_bbox_body)), (0, 80), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 0, 255), 2, cv2.LINE_AA)

        # paste frame and bird eyes view
        # frame = np.concatenate((frame, view_map), axis=1)
        frame = cv2.resize(frame, (w, h), interpolation=cv2.INTER_AREA)
        cv2.imshow('video1', view_map)
        cv2.imshow('video', frame)
        # cv2.imshow('transform', image_transform)
        cv2.waitKey(1)
        count += 1
        total_frame += 1
        if flag_save is True:
            video_writer.write(frame)

    print('FPS average: {:d}'.format(int(total_frame/(time.time()-time_start_all))))
    cap.release()
    if flag_save is True:
        video_writer.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Detect Face On Video')
    parser.add_argument("-fn", "--file_name", help="video file name or rtsp", default='', type=str)
    parser.add_argument("-op", "--option", help="if save video then choice option = 1", default=False, type=bool)
    parser.add_argument("-o", "--output", help="path to output video file", default='face_recording.avi', type=str)
    parser.add_argument("-f", "--fps", default=20, help="FPS of output video", type=int)
    args = parser.parse_args()

    # path model
    path_models = WEIGHTS / 'result_yolov5/yolov5s.pt'
    path_models_cls = WEIGHTS / 'result_mobilenetv2'
    # path video test
    url = '/home/duyngu/Downloads/Do_An/video_test/output2.avi'
    url = '/home/duyngu/Downloads/Do_An/video_test/facemask3.mp4'

    source = args.file_name
    cv2.namedWindow('video')
    cv2.resizeWindow('video', 1280, 720)
    cv2.setMouseCallback('video', get_pixel)
    # if run  as terminal, replace url = source
    detect_5k(url_video=url, path_model=path_models, path_model_cls=path_models_cls,
              flag_save=args.option, fps=args.fps, name_video=args.output)
