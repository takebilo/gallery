from flask_sqlalchemy import SQLAlchemy
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from fractions import Fraction
from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
import os
import piexif

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv

app = Flask(__name__, static_folder="./static/")
# セッション管理の秘密鍵を設定
app.config['SECRET_KEY'] = b''
# アップロードされた画像の保存ディレクトリ
app.config['UPLOAD_FOLDER'] = 'static/images'
# DBの設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///photo.db'
db = SQLAlchemy(app)
IMAGE_DIR = './static/images'

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

# ログイン機能(Auth0)の設定 
oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)

# DBのクラス
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(50), nullable=False)
    sumnail = db.Column(db.String(50), nullable=False)
    maker = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    lens = db.Column(db.String(50), nullable=False)
    focal_length = db.Column(db.String(50), nullable=False)
    fnumber = db.Column(db.String(50), nullable=False)
    iso = db.Column(db.String(50), nullable=False)
    exposure_time = db.Column(db.String(50), nullable=False)

class UploadForm(FlaskForm):
    photo = FileField('Choose a photo', validators=[FileRequired()])

# exif情報を取得し，DBに格納後exifを削除
def exif_info(image_path):
    # 画像を開く
    image = Image.open(image_path)
    file_name = image.filename
    file_name_list = file_name.split("/")
    # サムネイル用のファイル名
    sumnail = 'static/images/sumnail/' + file_name_list[2]

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

    # EXIF情報をDBに書き込む
    photo_data = Photo(file_name=file_name, sumnail=sumnail, maker=make, model=model, lens=lens_model, focal_length=focal_length, fnumber=fnumber, iso=iso, exposure_time=str(exposure_time))
    db.session.add(photo_data)
    db.session.commit()

    return lens_model, make, focal_length, model, fnumber, iso, str(exposure_time), file_name

# 写真の取得
def get_images():
    images = []
    for filename in os.listdir(IMAGE_DIR):
        if filename.endswith('.JPG'):
            images.append(os.path.join(IMAGE_DIR, filename))
    return images

# サムネイル用の画像を生成
def resize(image_path):
    image = Image.open(image_path)
    (width, height) = (600, 400)
    # 画像をリサイズする
    img_resized = image.resize((width, height))
    file_name = image.filename
    file_name_list = file_name.split("/")
    sumnail = 'static/images/sumnail/' + file_name_list[2]
    # ファイルを保存
    img_resized.save(sumnail, quality=90)

@app.route("/")
def top():
    return render_template('home.html')

@app.route("/gallery")
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_image():
    user = session.get('user')
    if user:
        form = UploadForm()
        if request.method == 'POST' and form.validate_on_submit():
            # アップロードされた画像を保存
            photo = form.photo.data
            filename = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
            photo.save(filename)

            # サムネイルを作成
            resize(filename)

            # exif情報を登録
            exif_info(filename)

            # exif情報を削除
            piexif.remove(filename)

            return redirect(url_for('upload_image'))

        return render_template('upload.html', form=form)
    else:
        return redirect("/login")

@app.route("/gallery_list")
def garally():
    photos = Photo.query.all()
    return render_template('gallery.html', photos=photos)

@app.route('/photo_delete')
def photo_list_delete():
    user = session.get('user')
    if user:
        photos = Photo.query.all()
        return render_template('delete.html', photos=photos)
    else:
        return redirect("/login")

# 写真の削除機能
@app.route('/photo/<int:id>/delete', methods=['POST'])
def photo_delete(id):
    user = session.get('user')
    if user:
        photo = Photo.query.get(id)
        os.remove(photo.file_name)
        os.remove(photo.sumnail)
        db.session.delete(photo)  
        db.session.commit()
        return redirect(url_for('photo_list_delete'))
    else:
        return redirect("/login")

# ログイン後の処理
@app.route("/photo_after_login", methods=["GET", "POST"])
def after_login():
    user = session.get('user')
    if user:
        return render_template("login.html")
    else:
        return redirect("/login")

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/photo_after_login")

# ログイン処理
@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

# ログアウト処理
@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("index", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0')
