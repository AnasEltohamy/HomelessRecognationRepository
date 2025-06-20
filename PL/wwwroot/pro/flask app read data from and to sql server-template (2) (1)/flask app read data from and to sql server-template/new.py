import os
from flask import Flask, request, jsonify, render_template
import pandas as pd
import face_recognition
import cv2
import glob
from werkzeug.utils import secure_filename
import pyodbc
import json

app = Flask(__name__)

# Directory to save uploaded files
UPLOAD_FOLDER = 'static/uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

RESULTS_FILE = 'results.json'

def save_encoding_to_file(encoding, output_file_path):
    with open(output_file_path, 'w') as file:
        for value in encoding:
            file.write(str(value) + '\n')

def convert_images_to_matrices(directory_path, save_directory):
    photo_paths = glob.glob(os.path.join(directory_path, "*.jpg"))
    for photo_path in photo_paths:
        unknown_image = face_recognition.load_image_file(photo_path)
        unknown_encodings = face_recognition.face_encodings(unknown_image)

        if unknown_encodings:
            unknown_encoding = unknown_encodings[0]
            unknown_image_name = os.path.basename(photo_path).split(".jpg")[0]
            unknown_encoding_file_path = os.path.join(save_directory, f"{unknown_image_name}.txt")
            save_encoding_to_file(unknown_encoding, unknown_encoding_file_path)

def load_encodings_from_folder(folder_path):
    encodings = {}
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".txt"):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r') as file:
                lines = file.readlines()
                encodings[file_name[:-4]] = [float(line.strip()) for line in lines]
    return encodings

def find_nearest_match(unknown_encoding, known_encodings):
    best_match_name = None
    best_distance = float('inf')
    for name, known_encoding in known_encodings.items():
        distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
        if distance < best_distance:
            best_distance = distance
            best_match_name = name
    
    if best_distance > 0.4:
        return "No matching child found", None
    
    return best_match_name, best_distance

def recognize_faces_in_image(image_path, known_encodings_folder):
    known_encodings = load_encodings_from_folder(known_encodings_folder)
    image = cv2.imread(image_path)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_image)
    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

    recognized_names = []

    for i, (face_location, face_encoding) in enumerate(zip(face_locations, face_encodings)):
        best_match_name, _ = find_nearest_match(face_encoding, known_encodings)
        recognized_names.append(best_match_name)
        top, right, bottom, left = face_location
        cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)

    return recognized_names

def fetch_data_from_sql_server(image_name):
    source_cnxn_str = ("Driver={SQL Server};"
                       "Server=.;"
                       "Database=project_v19;"
                       "Trusted_Connection=yes;")

    try:
        source_cnxn = pyodbc.connect(source_cnxn_str)
        source_cursor = source_cnxn.cursor()
                  
        query = """
        SELECT 
        p.*, 
        f.Name AS Father_Name, 
        f.PhoneNumber1 AS Father_PhoneNumber1, 
        f.PhoneNumber2 AS Father_PhoneNumber2, 
        f.HomePhoneNumber AS Father_HomePhoneNumber, 
        f.Gender AS Father_Gender, 
        f.AliveOrNo AS Father_AliveOrNo, 
        f.Address AS Father_Address, 
        f.DateOfBirth AS Father_DateOfBirth, 
        f.ImageName AS Father_ImageName, 
        f.Nots AS Father_Notes, 
        m.Name AS Mother_Name, 
        m.PhoneNumber1 AS Mother_PhoneNumber1, 
        m.PhoneNumber2 AS Mother_PhoneNumber2, 
        m.HomePhoneNumber AS Mother_HomePhoneNumber, 
        m.Gender AS Mother_Gender, 
        m.AliveOrNo AS Mother_AliveOrNo, 
        m.Address AS Mother_Address, 
        m.DateOfBirth AS Mother_DateOfBirth, 
        m.ImageName AS Mother_ImageName, 
        m.Nots AS Mother_Notes 
       
    FROM 
        project_v19.dbo.Persons p 
    LEFT JOIN 
        project_v19.dbo.Father f ON f.National_Father_Id = p.National_Father_Id_FK 
    LEFT JOIN 
        project_v19.dbo.Mother m ON m.National_Mother_Id = p.National_Mother_Id_FK
    WHERE 
        p.ImageNameAI = ?

    """

        source_cursor.execute(query, (image_name,))

        rows = source_cursor.fetchall()          
       
 
        columns = [column[0] for column in source_cursor.description]

        df = pd.DataFrame.from_records(rows, columns=columns)

        return df

    except pyodbc.Error as ex:
        print("Error fetching data from SQL Server:", ex)
        return None

    finally:
        if source_cnxn:
            source_cnxn.close()

def save_df_to_sql_server(df, table_name="RecognitionResults"):
    destination_cnxn_str = ("Driver={SQL Server};"
                            "Server=.;"
                            "Database=face_recognition_db;"
                            "Trusted_Connection=yes;")

    try:
        destination_cnxn = pyodbc.connect(destination_cnxn_str)
        destination_cursor = destination_cnxn.cursor()

        delete_query = f"DELETE FROM {table_name}"
        destination_cursor.execute(delete_query)

        create_table_query = f"IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table_name}') CREATE TABLE {table_name} ("
        for col, dtype in zip(df.columns, df.dtypes):
            sql_dtype = "VARCHAR(MAX)"
            if "int" in str(dtype):
                sql_dtype = "INT"
            elif "float" in str(dtype):
                sql_dtype = "FLOAT"
            elif "datetime" in str(dtype):
                sql_dtype = "DATETIME"
            create_table_query += f"{col} {sql_dtype}, "
        create_table_query = create_table_query[:-2]
        create_table_query += ")"
        destination_cursor.execute(create_table_query)

        for index, row in df.iterrows():
            placeholders = ', '.join(['?'] * len(row))
            insert_query = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({placeholders})"
            destination_cursor.execute(insert_query, tuple(row))

        destination_cnxn.commit()

        print("Data saved to destination database successfully.")

    except pyodbc.Error as ex:
        print("Error saving data to destination database:", ex)

    finally:
        if destination_cnxn:
            destination_cnxn.close()

def clear_and_rename_output_folder(output_folder, new_filename="out.jpg"):
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')
    for filename in os.listdir(output_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            old_file_path = os.path.join(output_folder, filename)
            new_file_path = os.path.join(output_folder, new_filename)
            os.rename(old_file_path, new_file_path)
            break


@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        filename, file_extension = os.path.splitext(file.filename)
        file_extension = file_extension.lower()
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']  #
        if file_extension not in allowed_extensions:
            return jsonify({"error": "Only image files are allowed"}), 400

        filename = secure_filename(filename + file_extension)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        output_file_path = os.path.join(OUTPUT_FOLDER, "out.jpg")
        with open(file_path, 'rb') as f:
            with open(output_file_path, 'wb') as out_f:
                out_f.write(f.read())

        known_encodings_folder = r'D:\Final\project V 26\project V 25\project V 25\PL\wwwroot\pro\flask app read data from and to sql server-template (2) (1)\Children Images to Arrays4'
        recognized_names = recognize_faces_in_image(file_path, known_encodings_folder)
        
        results = []

        for image_name in recognized_names:
            if image_name != "No matching child found":
                df = fetch_data_from_sql_server(image_name)
                if df is not None:
                    save_df_to_sql_server(df)
                    result = df.to_dict(orient='records')
                    for r in result:
                        r['ImagePath'] = 'uploads/' + image_name + file_extension  # Add image path
                        
        
                    results.append(result)
                    

        if not results:
            return render_template('results.html', message="There is no matching")
        else:
            return render_template('results.html', message="Results saved successfully!", results=results, file_extension=file_extension)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/results')
def results():
    with open(RESULTS_FILE, 'r') as file:
        data = json.load(file)
    return render_template('results.html', results=data)


if __name__ == '__main__':
    app.run(debug=True)
