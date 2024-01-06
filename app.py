# from ultralytics import YOLO
import io
import json
from gtts import gTTS
import torch
import statistics
import pandas as pd
from PIL import Image
from flask import Flask, render_template, request, Response, jsonify, send_file

app = Flask(__name__, template_folder="templates", static_folder="static")

model = torch.hub.load('ultralytics/yolov5', 'custom', path='best.pt')  # local model
# model.conf = 0.60

@app.route('/')
def home():
    data = {
        "name": 'Zuo'
    }
    return render_template('index.html', data=data)

@app.post('/detect')
def detect():
    try:
        im = request.files['image']
        im = Image.open(im)
        text, positions, y_diff = detect_object(im)

        return jsonify({'success': True, 'message': text, 'positions': positions, 'y_diff': y_diff})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def detect_object(im):
    results = model(im)
    df = results.pandas().xyxy[0]

    x_diff = []
    y_diff = []
    for index, row in df.iterrows():
        _x = row['xmax'] - row['xmin']
        _y = row['ymax'] - row['ymin']
        x_diff.append(_x)
        y_diff.append(_y)

    # use median instead of average is to prevent outliers
    x_diff = statistics.median(x_diff)
    y_diff = statistics.median(y_diff)

    # assign another df so that previous df is not affected
    df2 = df.sort_values(by='ymin').reset_index(drop=True)


    current_y = y_diff * -1.5   # offset the first y level
    sub_df = pd.DataFrame()     # to store df of a row
    df_list = []                # to store all df by row

    for index, row in df2.iterrows():
        # y level does not lower than first y of row for more than 50% of text height -> consider as same row
        if row['ymin'] - current_y <= y_diff * 0.5:
            sub_df.loc[len(sub_df)] = row
        else:
            current_y = row['ymin']     # redefine current y level
            df_list.append(sub_df)      # add current sub_df to df_list
            sub_df = pd.DataFrame(row).transpose()  # clear sub_df by redeclare

    df_list.append(sub_df)  # add the last row

    text = ""

    for i in range(len(df_list)):
        # if empty item, then skip
        if len(df_list[i]) == 0:
            continue
        # sort the row by x
        df_row = df_list[i].sort_values(by='xmin').reset_index(drop=True)
        sub_text = df_row.loc[0]['name']
        for j in range(1, len(df_row)):
            if df_row.loc[j]['xmin'] - df_row.loc[j-1]['xmax'] > x_diff:
                sub_text += " "     # add space in between text that are far
            sub_text += df_row.loc[j]['name']   # concat the text

        text += f"\n{sub_text}"

    positions = pd.DataFrame({
        'x': (df['xmin'] + df['xmax']) / 2,
        'y': (df['ymin'] + df['ymax']) / 2,
        'name': df['name']
    }).to_json(orient='records')

    return text.strip(), positions, y_diff

@app.post('/voice')
def text_to_speech():

    # text to be converted
    text = request.get_json()

    audio_stream = io.BytesIO()

    # language of text
    language = 'en'

    # convert the text
    speech = gTTS(text=text, lang=language, slow=True)     # slow is for slower pace
    speech.write_to_fp(audio_stream)
    audio_data = audio_stream.getvalue()

    # Send audio stream as response
    return send_file(io.BytesIO(audio_data), mimetype='audio/mp3', as_attachment=True, download_name='audio.mp3')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)