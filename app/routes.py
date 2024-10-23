from app import app
from flask import render_template, send_from_directory, flash, redirect, url_for, request
import matplotlib.pyplot as plt
import matplotlib, os
from app.analyze import start_func
import re

matplotlib.use('Agg')

app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['UPLOAD_FOLDER2'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'txt_images')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.secret_key = os.urandom(24)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['UPLOAD_FOLDER2']):
    os.makedirs(app.config['UPLOAD_FOLDER2'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def sort_key(file_name):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', file_name)]


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/message')
def message():
    image_list = sorted(os.listdir(app.config["UPLOAD_FOLDER"]), key=sort_key)
    image_path = [f'uploads/{img}' for img in image_list if img.endswith(('png', 'jpg', 'jpeg'))]
    return render_template("message.html", images=image_path)
    


@app.route('/message/<filename>')
def download_txt(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER2'], filename, as_attachment=True)


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/delete/<filename>', methods=['POST', 'GET'])
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    name_without_extension = filename.split('.')[0]
    txt_path = os.path.join(app.config['UPLOAD_FOLDER2'], name_without_extension + ".txt")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            os.remove(txt_path)
            flash(f'Файл {filename} успешно удален', 'success')
        except Exception as e:
            flash(f'Ошибка при удалении файла: {str(e)}', 'error')
    else:
        flash(f'Файл {filename} не найден', 'error')

    return redirect(url_for("message"))


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Файл не выбран', 'error')
        return redirect(url_for('message'))

    file = request.files['file']
    print(file)
    
    if file and allowed_file(file.filename):
        filename = file.filename
        print(filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        flash(f'Файл {filename} успешно загружен', 'success')
        
        image_list = sorted(os.listdir(app.config["UPLOAD_FOLDER"]), key=sort_key)
        for item in image_list:
            result_file = os.path.join(app.config['UPLOAD_FOLDER2'], f"{os.path.splitext(item)[0]}.txt")
            print(result_file, "good")
            if not os.path.exists(result_file):
                start_func.delay(filename, app.config["UPLOAD_FOLDER"])
                
        return redirect(url_for('message'))
    else:
        
        flash('Недопустимый формат файла', 'error')
        return redirect(url_for('message'))


@app.route('/')
def main():
    return render_template("main.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
