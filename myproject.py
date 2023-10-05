from flask_sqlalchemy import SQLAlchemy
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from fractions import Fraction
from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import os
import piexif

app = Flask(__name__, static_folder="./static/")
IMAGE_DIR = './static/images'

class UploadForm(FlaskForm):
    photo = FileField('Choose a photo', validators=[FileRequired()])

# exif情報を取得し，DBに格納後exifを削除
def exif_info(image_path):
    # 画像を開く
    image = Image.open(image_path)
    file_name = image.filename

    # EXIF情報を取得（もし存在しない場合、新しい辞書を作成）
    exif_data = image._getexif() or {}

    # タグ名と値を表示
    for tag, value in exif_data.items():
        tag_name = TAGS.get(tag, tag)
        if tag_name == "LensModel":
            lens_model = value
        elif tag_name == "Make":
            make = value
        elif tag_name == "FocalLength":
            focal_length = str(value)
        elif tag_name == "Model":
            model = value
        elif tag_name == "FNumber":
            fnumber = str(value)
        elif tag_name == "ISOSpeedRatings":
            iso = str(value)
        elif tag_name == "ExposureTime":
            exposure_time = Fraction(value)

    photo_data = Post(file_name=file_name, maker=make, model=model, lens=lens_model, focal_length=focal_length, fnumber=fnumber, iso=iso, exposure_time=str(exposure_time))
    db.session.add(photo_data)
    db.session.commit()

    return lens_model, make, focal_length, model, fnumber, iso, str(exposure_time), file_name

def get_images():
    images = []
    for filename in os.listdir(IMAGE_DIR):
        if filename.endswith('.JPG'):
            images.append(os.path.join(IMAGE_DIR, filename))
    return images

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
    form = UploadForm()
    if request.method == 'POST' and form.validate_on_submit():
        # アップロードされた画像を保存
        photo = form.photo.data
        filename = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
        photo.save(filename)

        print(exif_info(filename))
        piexif.remove(filename)

        return redirect(url_for('upload_image'))

    return render_template('upload.html', form=form)

@app.route("/gallery")
def garally():
    images = get_images()
    images.sort(reverse=True)
    print(images)
    return render_template('gallery.html', images=images)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
