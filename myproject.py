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
