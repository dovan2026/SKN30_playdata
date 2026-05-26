from ultralytics import YOLO
import cv2
import math

# 비디오 캡쳐 객체 생성(웹캠 사용)
cap = cv2.VideoCapture(0)

# YOLO 모델 로드
model = YOLO('yolo11n.pt')


class_name = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", 
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", 
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", 
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", 
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", 
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", 
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", 
    "chair", "couch", "potted plant", "bed", "dining table", "toilet", "TV", "laptop", 
    "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", 
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", 
    "toothbrush"
]

# 무한 루프(웹캠으로 실시한 영상 처리)
while True:
    # 비디오 캡처 객체에서 프레임을 읽어옴
    success, img = cap.read()

    # 모델을 통해 이미지를 처리하고 결과를 가져옴
    results = model(img, stream=True)

    for r in results:
        # 감지된 객체들이 경계 상자들
       boxes = r.boxes

    for box in boxes:

        # 경계 상자 좌표
        x1, y1, x2, y2 = box.xyxy[0]

        # 좌표값을 int로
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

        # 감지된 객체 주위에 박스 그리기
        cv2.rectangle(img, (x1, y1), (x2, y2), (255,0,255), 3)

        # 해당 객체의 신뢰도 가져옴(0~1)
        confidence = box.conf[0]

        # 객체 클래스 인덱쇼 가져오기
        cls_index = int(box.cls[0])

        # 텍스트 위치 지정
        org = [x1, y1]

        # 텍스트 폰트, 크기, 생색,두께 등 설정
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontscale = 1
        color = (255,0,0)
        thickness = 2

        cv2. putText(img,
                     class_name[cls_index] + ' ' + str(confidence),
                     org,
                     font,
                     fontscale,
                     color,
                     thickness
                     )
                
    # 처리된 이미지를 윈도우에 띄우기        
    cv2.imshow('AIcctv', img)

    # q버튼을 누르면 루프 종료
    if cv2.waitKey(1) == ord('q'):
        break

# 비디오 캡처 객체를 해제하고, 모든 OpencCV 닫기
cap.release()
cv2.destroyAllWindows()
