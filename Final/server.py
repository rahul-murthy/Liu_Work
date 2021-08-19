from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import pyqrcode, png, qrcode, base64, os, sys, json, requests, gzip, zlib
from pyqrcode import QRCode
import psycopg2
import urllib.parse
from urllib.request import urlopen
from urllib.parse import unquote
from io import StringIO, BytesIO

ACCESS_TOKEN = '7bfb7ec112c874c7bb2db80eaf45c4a9cbc16164'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'imageandqrcode'
#app.secret_key = "super secret key"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

t_host = "localhost"
t_port = "5432"
t_dbname = "image_test"
t_name_user = "postgres"
t_password = "murthy123"
#data_conn = psycopg2.connect(host=t_host, port=t_port, dbname=t_dbname, user=t_name_user, password=t_password)
#cursor = data_conn.cursor()
# -------------------------------------------------------------------------------------------------

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def compressStringToBytes(inputString):
    """
    read the given string, encode it in utf-8,
    compress the data and return it as a byte array.
    """
    bio = BytesIO()
    bio.write(inputString.encode("utf-8"))
    bio.seek(0)
    stream = BytesIO()
    compressor = gzip.GzipFile(fileobj=stream, mode='w')
    while True:  # until EOF
        chunk = bio.read(8192)
        if not chunk:  # EOF?
            compressor.close()
            return stream.getvalue()
        compressor.write(chunk)
        
# -------------------------------------------------------------------------------------------------

@app.route("/upload", methods=["POST"])
def upload():
    data_conn = psycopg2.connect(
        host=t_host, port=t_port, dbname=t_dbname, user=t_name_user, password=t_password)
    cursor = data_conn.cursor()
    file = request.files["inputFile"]
    data = file.read()

    cursor.execute("INSERT INTO data (image) VALUES (%s)", (data, ))
    data_conn.commit()
    cursor.close()
    data_conn.close()

    return "Saved " + file.filename + " to the database"

# -------------------------------------------------------------------------------------------------

def SaveToDatabase(id_image, blob_file):
    data_conn = psycopg2.connect(
        host=t_host, port=t_port, dbname=t_dbname, user=t_name_user, password=t_password)
    cursor = data_conn.cursor()
    s = ""
    s += "INSERT INTO data"
    s += "("
    s += "id_image"
    s += ", blob_file"
    s += ") VALUES ("
    s += "(%id_image)"
    s += ", '(%blob_file)'"
    s += ")"
    #s = "INSERT INTO data (id, image) VALUES ((%id_item), '(%FileImage)')"
    cursor.execute(s, [id_image, blob_file])
    data_conn.commit()
    cursor.close()
    data_conn.close()
    
# -------------------------------------------------------------------------------------------------

# Get the Picture from the Database and show on screen
@app.route('/retrieve', methods=['POST', 'GET'])
def RetrieveImage():
    text = request.form['Image_Number']
    data_conn = psycopg2.connect(
        host=t_host, port=t_port, dbname=t_dbname, user=t_name_user, password=t_password)
    cursor = data_conn.cursor()

    ID = text
    query = "SELECT * FROM data WHERE id = '{0}'"
    cursor.execute(query.format(ID))
    Result = cursor.fetchone()[1]

    base64_img = base64.b64encode(Result).decode('utf-8')
    img_tag = '<img src="data:image/png;base64,{0}">'.format(base64_img)

    data_conn.commit()
    cursor.close()
    data_conn.close()
    return img_tag

# -------------------------------------------------------------------------------------------------

@app.route('/delete', methods=['POST', 'GET'])
def deleteImage():
    data_conn = psycopg2.connect(
        host=t_host, port=t_port, dbname=t_dbname, user=t_name_user, password=t_password)
    cursor = data_conn.cursor()

    text = request.form['Image_Number']
    cursor.execute("DELETE FROM data WHERE id = %s", (text, ))

    data_conn.commit()
    cursor.close()
    data_conn.close()

    return render_template("Database_page.html")

# -------------------------------------------------------------------------------------------------

@app.route('/DB_display')
def DB_display():
    data_conn = psycopg2.connect(
        host=t_host, port=t_port, dbname=t_dbname, user=t_name_user, password=t_password)
    cursor = data_conn.cursor()

    cursor.execute("SELECT * FROM data")
    data = cursor.fetchall()

    data_conn.commit()
    cursor.close()
    data_conn.close()
    # for all data[#][1] change more mem to base64
    count = 0
    for row in data:
        base64_img = base64.b64encode(data[count][1]).decode('utf-8')
        img_tag = '<img src="data:image/png;base64, {0}">'.format(base64_img)
        #data[count][1] = img_tag
        data[count] = (data[count][0], img_tag, data[count][2])
        count = count + 1
    return render_template('database.html', data=data)

# -------------------------------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/QR_Code_page')
def QR_Code_page():
    return render_template('QR_Code_page.html')

@app.route('/Database_page')
def Database_page():
    return render_template('Database_page.html')

# -------------------------------------------------------------------------------------------------

@app.route('/QR_Code', methods=['POST', 'GET'])
def QR_Code():
    text = request.form['Image_Number']
    url = pyqrcode.create(text)
    # print(type(text))
    url.png('VCQR.png', scale=6)
#    return render_template('index.html')
    data_uri = base64.b64encode(
        open('VCQR.png', 'rb').read()).decode('utf-8')
    img_tag = '<img src="data:image/png;base64,{0}">'.format(data_uri)
    return img_tag

# -------------------------------------------------------------------------------------------------

@app.route('/ShowQRCode/')
def my_link():
    # img = qrcode.make("https://pypi.org/project/qrcode/")
    # img.save("qrcode.jpg")

    data_uri = base64.b64encode(
        open('VCQR.png', 'rb').read()).decode('utf-8')
    img_tag = '<img src="data:image/png;base64,{0}">'.format(data_uri)

    return img_tag

# -------------------------------------------------------------------------------------------------

@app.route("/JSONUpload", methods=["POST"])
def JSONUpload():
    # data_conn = psycopg2.connect(
    # host=t_host, port=t_port, dbname=t_dbname, user=t_name_user, password=t_password)
    # cursor = data_conn.cursor()
    file = request.files["inputFile"]
    data = file.read()
    dict = json.loads(data)
    dict_str = json.dumps(dict)

    url = urllib.parse.quote(data)

    comp_dict = compressStringToBytes(dict_str)

    b_url = str.encode(url)
    comp_url = zlib.compress(b_url)

    if (qrcode.make(dict)):
        img = qrcode.make(dict)
        img.save("VC.jpg")

        data_uri = base64.b64encode(
            open('VC.jpg', 'rb').read()).decode('utf-8')
        img_tag = '<img src="data:image/jpg;base64,{0}">'.format(data_uri)
        return img_tag
    else:
        return "OverflowError"
#    return "Didn't Work"

# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
# -------------------------------------------------------------------------------------------------