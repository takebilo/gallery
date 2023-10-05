from flask import Flask, render_template
import os
from PIL import Image, ExifTags

app = Flask(__name__, static_folder="./static/")
IMAGE_DIR = './static/images'

def get_images():
    images = []
    for filename in os.listdir(IMAGE_DIR):
        if filename.endswith('.JPG'):
            images.append(os.path.join(IMAGE_DIR, filename))
    return images

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/gallery")
def garally():
    images = get_images()
    images.sort(reverse=True)
    print(images)
    return render_template('gallery.html', images=images)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
