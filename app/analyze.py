import os, cv2, pytesseract
import matplotlib.pyplot as plt 
from app import app
from app import celery


app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['UPLOAD_FOLDER2'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'txt_images')


if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
    
if not os.path.exists(app.config['UPLOAD_FOLDER2']):
    os.makedirs(app.config['UPLOAD_FOLDER2'])

def open_img(img_path):

    carplate_img = cv2.imread(img_path)
    carplate_img = cv2.cvtColor(carplate_img, cv2.COLOR_BGR2RGB)
    plt.axis('off')
    plt.imshow(carplate_img)
    # plt.show()
    plt.close()

    return carplate_img


def carplate_extract(image, carplate_haar_cascade):
    carplate_rects = carplate_haar_cascade.detectMultiScale(image, scaleFactor=1.1, minNeighbors=1)
    if len(carplate_rects) == 0:
        print("Номерной знак не найден")
        return None
    try:
        for x, y, w, h in carplate_rects:
            # carplate_img = image[y+15:y+h-10, x+10:x+w-5]
            carplate_img = image[y+10:y+h-10, x+10:x+w-5]
    except:
        pass
    
    return carplate_img

def enlarge_img(image, scale_percent):
    try:
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)
        plt.axis('off')
        resized_image = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
        return resized_image
    except:
        return None
    
@celery.task
def start_func(image , path_to_folder_img):
    carplate_img_rgb = open_img(img_path=path_to_folder_img + "\\" + image)
    cascade_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'haarcascade_russian_plate_number.xml')
    carplate_haar_cascade = cv2.CascadeClassifier(cascade_path)

    carplate_extract_img = carplate_extract(carplate_img_rgb, carplate_haar_cascade)

    path_to_write = app.config['UPLOAD_FOLDER2']
    
    if carplate_extract_img is None:
        with open(os.path.join(path_to_write, f"{os.path.splitext(image)[0]}.txt"), 'w') as f:
            f.write(f"Не удалось извлечь номерной знак для {image}")
        return

    carplate_extract_img = enlarge_img(carplate_extract_img, 150)

    if carplate_extract_img is None:
        with open(os.path.join(path_to_write, f"{os.path.splitext(image)[0]}.txt"), 'w') as f:
            f.write(f"Не удалось увеличить изображение для {image}")
        return

    carplate_extract_img_gray = cv2.cvtColor(carplate_extract_img, cv2.COLOR_RGB2GRAY)

    car_info = pytesseract.image_to_string(
        carplate_extract_img_gray,
        config='--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    )

    if not car_info.strip():
        with open(os.path.join(path_to_write, f"{os.path.splitext(image)[0]}.txt"), 'w') as f:
            f.write(f"Не удалось распознать номер для {image}")
        return

    # print(f'Номер авто: {car_info}')
    
    with open(os.path.join(path_to_write, f"{os.path.splitext(image)[0]}.txt"), 'w') as f:
        f.write(car_info)
        
