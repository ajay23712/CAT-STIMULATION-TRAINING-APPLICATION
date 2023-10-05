import csv
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import cv2
import numpy as np
from io import BytesIO
import shutil
from PIL import Image
import datetime
import secrets

secret_key = secrets.token_hex(16)
app = Flask(__name__)
app.secret_key = secret_key
app.config["IMAGE_UPLOADS"] = "static/upload/"
app.config["IMAGE_UPLOADS_2"] = "static/second_folder/"
files = " "
update_image_name = ''
test_image_name = ''
score = 0
user_name = ' '
percent = 0
total_click = ''
total_score = ''
test_file_name = ''
correct_index = []

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def del_coordinates_update(remaining_coordinates, image):
    path = 'static/second_folder/%s' % image
    images = cv2.imread(path)
    for coord in remaining_coordinates:
        x, y, text = coord
        center_coordinates = (x, y)
        radius = 10
        color = (255, 0, 0)
        thickness = 2
        images = cv2.circle(images, center_coordinates, radius, color, thickness)
        org = (x + 15, y - 15)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1.0
        color = (255, 0, 0)
        thickness = 2
        images = cv2.putText(images, str(text), org, font, font_scale, color, thickness, cv2.LINE_AA)
    save_path = 'static/upload/%s' % image
    cv2.imwrite(save_path, images)
    print(f"Image with text saved to {save_path}")


def coordinates_test_details(name, date, mark, image, model, points, ques, mis_points):
    image_with_text = ""
    image_with_value = ""
    path = 'static/test_photos/%s' % image
    img = cv2.imread(path)
    h, w, c = img.shape
    extended_img = np.zeros([h, w + 500, c], dtype=np.uint8)
    extended_img.fill(255)
    extended_img[:, :w] = img
    data_to_print = [
        "Name: ",
        "Date: ",
        "total",
        "Ques:",
        "Score: ",
        "Model:",
        "Correct",
        "points:",
        "Mis Click",
        "points:",
    ]
    data_value = [
        str(name),
        str(date),
        "",
        str(ques),
        str(mark),
        str(model),
        "",
        str(points),
        "",
        str(mis_points),

    ]
    padding = 9
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.9
    color = (255, 0, 0)
    thickness = 2
    x = w + padding
    y = 50
    x1 = w + padding
    y1 = 50
    line_spacing = 30
    for item in data_to_print:
        org = (x, y)
        image_with_text = cv2.putText(extended_img, item, org, font, font_scale, color, thickness, cv2.LINE_AA)
        y += line_spacing
    for item in data_value:
        org = (x1 + 100, y1)
        image_with_value = cv2.putText(image_with_text, item, org, font, font_scale, color, thickness, cv2.LINE_AA)
        y1 += line_spacing
    save_path = 'static/test_photos/%s' % image
    cv2.imwrite(save_path, image_with_value)
    print(f"Image with text saved to {save_path}")
def coordinates_test(x, y, image, text):
    path = 'static/test_photos/%s' % image
    images = cv2.imread(path)
    center_coordinates = (x, y)
    radius = 10
    color = (255, 0, 0)
    thickness = 2
    image_with_circle = cv2.circle(images, center_coordinates, radius, color, thickness)
    org = (x + 15, y - 15)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    color = (255, 0, 0)
    thickness = 2
    image_with_text = cv2.putText(image_with_circle, str(text), org, font, font_scale, color, thickness, cv2.LINE_AA)
    save_path = 'static/test_photos/%s' % image
    cv2.imwrite(save_path, image_with_text)
    print(f"Image with text saved to {save_path}")


def coordinates(x, y, image, text):
    path = 'static/upload/%s' % image
    images = cv2.imread(path)
    center_coordinates = (x, y)
    radius = 10
    color = (255, 0, 0)
    thickness = 2
    image_with_circle = cv2.circle(images.copy(), center_coordinates, radius, color, thickness)
    org = (x + 15, y - 15)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.0
    color = (255, 0, 0)
    thickness = 2
    image_with_text = cv2.putText(image_with_circle, str(text), org, font, font_scale, color, thickness, cv2.LINE_AA)
    save_path = 'static/upload/%s' % image
    cv2.imwrite(save_path, image_with_text)
    print(f"Image with text saved to {save_path}")


def save_to_csv(data):
    with open('coordinates.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([data['x'], data['y'], data['value']])


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        user = cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?",
                              (username, password)).fetchone()
        admin = cursor.execute("SELECT * FROM admins WHERE username = ? AND password = ?",
                               (username, password)).fetchone()
        conn.close()
        if user :
            global user_name
            user_name = user[2]
            return redirect(url_for('user_page'))
        elif admin:
            return redirect(url_for('admin_page'))
        else:
            return "Login Failed"
    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    global percent, score
    percent, score = 0, 0
    session.clear()
    print(session)
    correct_index.clear()
    return redirect(url_for('login'))
@app.route('/admin_page')
def admin_page():
    return render_template("admin_home_screen.html")


@app.route('/reports', methods=['POST', 'GET'])
def reports():
    if request.method == "GET":
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        languages = cur.execute('select Model_Name from Test_Details').fetchall()
        unique_words = []
        seen_words = set()
        for language_tuple in languages:
            language = language_tuple[0]
            if language not in seen_words:
                seen_words.add(language)
                unique_words.append(language)
        return render_template("reports.html", languages=unique_words)

    if request.method == 'POST':
        report_name = request.form['messages']
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        report_details = cur.execute('Select * from Test_Details where Model_Name = ? or username = ? ', (report_name,
                                                                                                          report_name))
        if len(str(report_details)) >= 0:
            report_details = cur.fetchall()
            cur.close()
            return render_template('reports.html', report_details=report_details)
        return render_template("reports.html")
    return render_template("reports.html")


@app.route('/user_page')
def user_page():
    global user_name
    print(user_name)
    return render_template("user_home_screen.html",user_name=user_name)


@app.route('/admin_index')
def admin_index():
    global files
    image = files
    return render_template("admin_index.html", uploaded_image=image)


@app.route('/upload-image', methods=['GET', 'POST'])
def upload_image():
    if request.method == "POST":
        if request.files:
            image = request.files["image"]
            image_path = os.path.join(app.config["IMAGE_UPLOADS"], image.filename)
            image.save(image_path)
            new_width = 800
            new_height = 350
            img = Image.open(image_path)
            img = img.resize((new_width, new_height), Image.BILINEAR)
            img.save(image_path)
            image_path_2 = os.path.join(app.config["IMAGE_UPLOADS_2"], image.filename)
            shutil.copy(image_path, image_path_2)
            global files
            files = image.filename
            return redirect(url_for("admin_index"))
    return render_template("upload.html")


@app.route('/uploads/<filename>')
def send_uploaded_file(filename=''):
    from flask import send_from_directory
    return send_from_directory(app.config["IMAGE_UPLOADS"], filename)


@app.route('/click', methods=['POST'])
def handle_click():
    data = request.get_json()
    x = data['x']
    y = data['y']
    value = data['value']
    defectArea = data['defectArea']
    response_data = {'x': x, 'y': y, 'value': value, defectArea: 'defectArea'}
    global files
    image = files
    model_name = os.path.splitext(image)
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO coordinates (x, y, Description,Model_Name, Image,Defect_Area) "
                "VALUES (?,?,?,?,?,?)", (x, y, value, model_name[0], image, defectArea))
    details = cur.execute("select id from coordinates where(x=? and  y=? and  Description=? and"
                          " Model_Name=? and Image=? and Defect_Area=?)",
                          (x, y, value, model_name[0], image, defectArea))
    for i in details:
        coordinates(x, y, image, i[0])
    cur.connection.commit()
    cur.close()
    # save_to_csv(response_data)
    return jsonify(response_data)


@app.route('/create_account', methods=['POST', 'GET'])
def create_account():
    if request.method == 'POST':
        username = request.form["username"]
        password = request.form["password"]
        name = request.form["name"]
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, password, name) VALUES (?,?,?)', (username, password, name))
        cur.connection.commit()
        cur.close()
        return render_template("create_account.html")
    return render_template("create_account.html")


@app.route('/edit_models', methods=['GET', 'POST'])
def edit_models():
    img = ''
    if request.method == "GET":
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        languages = cur.execute('select Model_Name from coordinates').fetchall()
        unique_words = []
        seen_words = set()
        for language_tuple in languages:
            language = language_tuple[0]
            if language not in seen_words:
                seen_words.add(language)
                unique_words.append(language)
        return render_template("edit_models.html", languages=unique_words)

    if request.method == "POST":
        model_name = request.form["messages"]
        conn = get_db_connection()
        cur = conn.cursor()
        result = cur.execute('select id ,X,Y, Description,Image,Defect_Area from coordinates WHERE Model_Name=?',
                             (model_name,))
        if len(str(result)) > 0:
            result_all = cur.fetchall()
            conn.close()
            for detail in result_all:
                global update_image_name
                img = detail[4]
                update_image_name = img
                return render_template('edit_models.html', result_all=result_all, img=img)
            return render_template('edit_models.html', result_all=result_all, img=img)
    return render_template("edit_models.html", img=img)


@app.route('/delete_data/<int:id>', methods=['POST'])
def delete_data(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM coordinates WHERE id = ?', (id,))
    print(update_image_name)
    model_name = os.path.splitext(update_image_name)
    print(model_name)
    del_remaining = cursor.execute('select id,x,y,Image from coordinates where Model_Name= ?',
                                   (model_name[0],))
    images_dict = {}
    for i in del_remaining:
        print(i)
        x, y, image, text = i[1], i[2], i[3], i[0]
        if image not in images_dict:
            images_dict[image] = []
        images_dict[image].append((int(x), int(y), text))
    for image in images_dict:
        del_coordinates_update(images_dict[image], image)
    conn.commit()
    conn.close()
    return render_template("edit_models.html")


@app.route('/update_models', methods=['GET', 'POST'])
def update_models():
    global update_image_name
    update_name = update_image_name
    print(update_name)
    return render_template("update_models.html", update_name=update_name)


@app.route('/update_click', methods=['POST'])
def update_click():
    data = request.get_json()
    x = data['x']
    y = data['y']
    value = data['value']
    defectArea = data['defectArea']
    response_data = {'x': x, 'y': y, 'value': value, defectArea: 'defectArea'}
    global update_image_name
    update_name = update_image_name

    model_name = os.path.splitext(update_name)
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO coordinates (x, y, Description,Model_Name, Image,Defect_Area)"
                " VALUES (?,?,?,?,?,?)", (x, y, value, model_name[0], update_name, defectArea))
    details = cur.execute("select id from coordinates where(x=? and  y=? and  Description=? and"
                          " Model_Name=? and Image=? and Defect_Area=?)",
                          (x, y, value, model_name[0], update_name, defectArea))
    for i in details:
        coordinates(x, y, update_name, i[0])
    cur.connection.commit()
    cur.close()
    save_to_csv(response_data)
    return jsonify(response_data)


@app.route('/take_test', methods=['GET', 'POST'])
def take_test():
    test_details = ""
    file_name = ""
    global user_name
    print(user_name)
    if request.method == "GET":
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        languages = cur.execute('select Model_Name from coordinates').fetchall()
        unique_words = []
        seen_words = set()
        for language_tuple in languages:
            language = language_tuple[0]
            if language not in seen_words:
                seen_words.add(language)
                unique_words.append(language)
        return render_template("take_test.html", languages=unique_words)

    if request.method == "POST":
        search_test = request.form["messages"]
        conn = get_db_connection()
        cur = conn.cursor()
        test_detail = cur.execute('select Model_Name,Image from coordinates WHERE Model_Name=?',
                                  (search_test,))
        if len(str(test_detail)) > 0:
            test_details = cur.fetchone()
            conn.close()
            global test_image_name, test_file_name
            img = cv2.imread('static/second_folder/%s' % test_details[1])
            current_date = datetime.date.today()
            formatted_date = current_date.strftime("%d-%m-%Y")
            file_ext = os.path.splitext(test_details[1])
            file_name = search_test + "_" + formatted_date + "_" + user_name + file_ext[1]
            test_file_name = file_name
            test_image_name = search_test
            copied_image = img.copy()
            save_path = ('static/test_photos/%s' % file_name)
            cv2.imwrite(save_path, copied_image)
            print(session)
        return render_template('take_test.html', test_details=test_details, file_name=file_name,
                               user_name=user_name)
    return render_template("take_test.html", test_details=test_details, file_name=file_name, user_name=user_name)


@app.route('/model_test', methods=['GET', 'POST'])
def model_test():
    global test_file_name, user_name
    return render_template("test_page.html", update_name=test_file_name, user_name=user_name)


@app.route('/model_test_click', methods=['POST'])
def model_test_click():
    data = request.get_json()
    x = data['x']
    y = data['y']
    index_number = data.get('index')
    response_data = {'x': x, 'y': y, 'index': index_number}
    data_list = [x, y]
    global test_image_name, total_score, user_name, test_file_name, correct_index, total_click
    model_name = os.path.splitext(test_image_name)
    coordinates_test(x, y, test_file_name, index_number+1)
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    details = cur.execute('select X,Y from coordinates WHERE Model_Name = ?', (model_name[0],)).fetchall()
    total_score = len(details)
    total_click = index_number+1
    global score, percent
    for i in details:
        if score <= total_score:
            if (int(i[0]) - 50 <= int(data_list[0]) <= (int(i[0]) + 50)) and (
                    int(i[1]) - 50 <= int(data_list[1]) <= (int(i[1]) + 50)):
                score += 1
                print(session)
                print(index_number + 1)
                correct_index.append(index_number+1)
                percent = (score / total_score) * 10
    cur.connection.commit()
    cur.close()
    return jsonify(response_data)


@app.route('/test_score')
def Test_score():
    global percent, total_score, user_name, test_image_name, test_file_name, correct_index, total_click
    percent = int(percent)
    current_date = datetime.date.today()
    date = current_date.strftime("%d-%m-%Y")
    model_name = os.path.splitext(test_image_name)
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO Test_Details (Model_Name,username,score,Total_Question,Test_img) VALUES (?,?,?,?,?)",
                (model_name[0], user_name, percent, total_score, test_file_name))
    cur.connection.commit()
    cur.close()
    mis_points = abs(int(len(correct_index)) - int(total_click))
    coordinates_test_details(user_name, date, percent, test_file_name, model_name, correct_index, total_score,
                             mis_points)
    return render_template("test_score.html", score=percent)


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')

