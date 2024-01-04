#!/usr/bin/env python
# coding: utf-8
# In[1]:

from flask import Flask, request, render_template, redirect, url_for, flash, session
from converter.converter import convert_to_mp4, convert_to_wav
import g4f
import base64
import shutil
import time
import os
import sqlite3
import json
import cv2
import subprocess
from pytube import YouTube

# Set with provider
stream = False

# In[2]:

# File upload address
app = Flask(__name__)
app.secret_key = '123456'
app.config['UPLOAD_SRC'] = 'static/src'
app.config['UPLOAD_USER'] = 'static/user'
app.config['UPLOAD_VIDEOS'] = 'static/videos'
app.config['UPLOAD_AUDIOS'] = 'static/audios'
app.config['UPLOAD_SUBTITLES'] = 'static/subtitles'
app.config['UPLOAD_IMAGES'] = 'static/images'

# In[3]:

# Connect database
data_base = sqlite3.connect('database', check_same_thread=False)
cursor = data_base.cursor()
cursor.execute('create table if not exists uploads(info text)')
cursor.execute('create table if not exists users(info text)')
data_base.commit()

# Model List
modelList = ['tiny', 'base', 'small', 'medium', 'large-v1', 'large-v2']


# In[4]:

def getLanguagesList():
    with open('static/languages.txt', 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file]
    return lines


def getLanguageTarget(filename):
    languageList = getLanguagesList()
    languageTarget = []

    for list in languageList:
        pathSubLang = app.config['UPLOAD_SUBTITLES'] + "/" + filename + "_" + list + ".vtt"

        if os.path.exists(pathSubLang):
            languageTarget.append(list)

    return languageTarget


def getrecords():
    cursor.execute('select * from uploads')
    results = cursor.fetchall()
    records = []
    for r in results:
        records.append(eval(r[0]))
    return records


def getuserdata():
    cursor.execute('select * from users')
    results = cursor.fetchall()
    records = []
    for r in results:
        records.append(eval(r[0]))
    return records


def setSubtitle(filename, subtitle):
    subtitle_path = app.config['UPLOAD_SUBTITLES'] + "/" + filename + ".vtt"
    with open(subtitle_path, 'wb') as file:
        file.write(subtitle.encode('utf-8'))


def nameReplace(videoName):
    filename = videoName.replace(' ', '')
    filename = filename.replace('.', '-')
    filename = filename.replace('|', '-')
    filename = filename.replace('"', '-')
    filename = filename.replace('/', '-')
    filename = filename.replace('?', '-')
    filename = filename.replace('(', '-')
    filename = filename.replace(')', '-')
    return filename


def generateSubtitle(filename, models, languages):
    command = [
        "python",  # 或 'python3'，具体取决于你的环境
        "converter/audiototext.py",
        app.config['UPLOAD_AUDIOS'] + "/" + filename + ".wav",
        "--model",
        models,
        "--language",
        languages,
        "--output_format",
        "vtt",
        "--output_dir",
        app.config['UPLOAD_SUBTITLES'],
        "--skip-install"
    ]
    subprocess.run(command, check=True, text=True)


def openSubtitleFile(filename):
    with open(
            app.config['UPLOAD_SUBTITLES'] + "/" + filename + '.vtt', 'r') as f:
        text = f.read()
    return text


# Summarize the text
def summarize(subtitle, title, lang):
    # Open prompt txt
    with open("static/prompt.txt", 'r') as f:
        prompt = f.read()

    messages = ""
    input_text = (prompt + "The language in which you generate results must be " + lang + ". "
                  + "The video original title is '" + title + "'. "
                  + "You can only answer the results. "
                  + "The following content is the .VTT file:\n" + subtitle)

    # Provider(ChatBase, ChatForAi, ChatgptAi, FakeGpt, Hashnode, DeepInfra)
    response = g4f.ChatCompletion.create(model='gpt-3.5-turbo', provider=g4f.Provider.ChatgptAi,
                                         messages=[{"role": "user", "content": input_text}],
                                         stream=g4f.Provider.ChatgptAi.supports_stream)

    for message in response:
        messages += message
        print(message, flush=True, end='')

    return messages


# In[5]:

@app.route('/', methods=['GET', 'POST'])
def index():
    user = session.get('user')
    records = getrecords()
    search = ""

    if request.method == 'GET':
        if records:
            return render_template('index.html', pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'],
                                   pathImages=app.config['UPLOAD_IMAGES'], pathVideos=app.config['UPLOAD_VIDEOS'],
                                   pathSubtitles=app.config['UPLOAD_SUBTITLES'], records=records[::-1], user=user)
        else:
            flash('There are currently no videos uploaded!')

    else:
        search = request.form.get('searchBox').lower()
        target = []

        for record in records:
            if search in record['title'].lower() or "#" + search in record['summarize'].lower():
                target.append(record)

        if not target:  # No relevant titles found
            flash('No relevant titles found!')

        else:
            return render_template('index.html', pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'],
                                   pathImages=app.config['UPLOAD_IMAGES'], pathVideos=app.config['UPLOAD_VIDEOS'],
                                   pathSubtitles=app.config['UPLOAD_SUBTITLES'], records=target[::-1], search=search,
                                   user=user)

    return render_template('index.html', pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'],
                           search=search, user=user)


# In[6]:

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userdata = getuserdata()
        username = request.form.get('username')
        password = request.form.get('password')

        for users in userdata:
            if username == users['username'] and password == users['password']:
                session['user'] = username
                return redirect(url_for('index'))

        flash('The username or password incorrect!')
        return render_template('login.html', pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'],
                               username=username, password=password)

    return render_template('login.html', pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'])


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        userdata = getuserdata()
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        re_password = request.form.get('repassword')

        err = ""

        for users in userdata:
            if username == users['username']:
                err = 'The username already exists!'
            elif email == users['email']:
                err = 'The email already exists!'
            elif password != re_password:
                err = 'The password does not match!'

            if err:
                flash(err)
                return render_template('register.html', pathSrc=app.config['UPLOAD_SRC'],
                                       pathUser=app.config['UPLOAD_USER'], username=username, email=email,
                                       password=password, repassword=re_password)

        # Save data
        date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        record = {"username": username, "email": email, "password": password, "date": date}
        record_json = json.dumps(record)
        cursor.execute('INSERT INTO users (info) VALUES (?)', (record_json,))
        data_base.commit()

        # Create photo
        defaultPic = app.config['UPLOAD_SRC'] + "/profile.png"
        savePath = app.config['UPLOAD_USER'] + "/" + username + ".png"
        shutil.copy(defaultPic, savePath)

        return render_template('login.html', username=username, password=password,
                               pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'])

    return render_template('register.html', pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'])


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session['user'] = None
    return redirect(url_for('index'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user = session.get('user')

    if request.method == 'POST':
        cropped_image_data = request.form.get('croppedImage')
        print("Cropped Image Data:", cropped_image_data)
        user_path = os.path.join(app.config['UPLOAD_USER'], user)

        with open(user_path + '.png', 'wb') as f:
            f.write(base64.b64decode(cropped_image_data.split(',')[1]))

    return render_template('profile.html', pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'],
                           user=user)


@app.route('/youtube', methods=['GET', 'POST'])
def youtube():
    user = session.get('user')
    languageList = getLanguagesList()
    languageDetect = False
    modelDetect = False
    urlDetect = True

    if request.method == 'POST':
        url = request.form.get('url')
        languages = request.form.get('languages')
        models = request.form.get('models')

        if languages == "Auto-Detect":
            languageDetect = True

        for language in languageList:
            if language == languages:
                languageDetect = True

        for model in modelList:
            if model == models:
                modelDetect = True

        try:
            yt = YouTube(url)
        except:
            urlDetect = False

        if urlDetect and languageDetect and modelDetect:
            video_stream = yt.streams.get_highest_resolution()
            videoName = yt.title
            filename = nameReplace(videoName)

            # Download YouTube Video
            save_path = os.path.join(app.config['UPLOAD_VIDEOS'])
            video_stream.download(output_path=save_path, filename=filename + '.mp4')

            # Resolve naming duplicate
            records = getrecords()
            for record in records:
                if filename == record['filename']:
                    flash('The video already exists!')
                    return redirect(url_for('youtube'))

            # Covert to wav
            video_path = os.path.join(app.config['UPLOAD_VIDEOS'], filename)
            audio_path = os.path.join(app.config['UPLOAD_AUDIOS'], filename)
            wav_output_file = f"{audio_path}.wav"
            convert_to_wav(video_path + ".mp4", wav_output_file)

            # Convert to Text
            start_subtitle_time = time.time()
            generateSubtitle(filename, models, languages)
            end_subtitle_time = time.time()

            # Open subtitle file
            text = openSubtitleFile(filename)

            # Summarizing
            start_summarize_time = time.time()
            messages = summarize(text, videoName, languages)
            end_summarize_time = time.time()

            # Calculate the time
            print()
            run_subtitle_time = end_subtitle_time - start_subtitle_time
            subtitle_hours = int(run_subtitle_time // 3600)
            subtitle_minutes = int((run_subtitle_time % 3600) // 60)
            subtitle_seconds = int(run_subtitle_time % 60)

            if subtitle_hours > 0:
                print(f"Generate Subtitle Total Time：{subtitle_hours}H {subtitle_minutes}M {subtitle_seconds}")
            elif subtitle_minutes > 0:
                print(f"Generate Subtitle Total Time：{subtitle_minutes}M {subtitle_seconds}S")
            else:
                print(f"Generate Subtitle Total Time：{subtitle_seconds}S")

            run_summarize_time = end_summarize_time - start_summarize_time
            summarize_hours = int(run_summarize_time // 3600)
            summarize_minutes = int((run_summarize_time % 3600) // 60)
            summarize_seconds = int(run_summarize_time % 60)

            if summarize_hours > 0:
                print(f"Generate Summarize Total Time：{summarize_hours}H {summarize_minutes}M {summarize_seconds}")
            elif summarize_minutes > 0:
                print(f"Generate Summarize Total Time：{summarize_minutes}M {summarize_seconds}S")
            else:
                print(f"Generate Summarize Total Time：{summarize_seconds}S")

            run_time = end_summarize_time - start_subtitle_time
            hours = int(run_time // 3600)
            minutes = int((run_time % 3600) // 60)
            seconds = int(run_time % 60)

            if hours > 0:
                print(f"Total Time：{hours}H {minutes}M {seconds}")
            elif minutes > 0:
                print(f"Total Time：{minutes}M {seconds}S")
            else:
                print(f"Total Time：{seconds}S")

            # Return
            return render_template('videoInfo.html', pathSrc=app.config['UPLOAD_SRC'],
                                   pathUser=app.config['UPLOAD_USER'], pathVideos=app.config['UPLOAD_VIDEOS'],
                                   pathSubtitles=app.config['UPLOAD_SUBTITLES'], filename=filename, title=yt.title,
                                   subtitle=text, messages=messages, languageList=languageList, user=user, web='upload')
        elif not url:
            flash('Please enter YouTube URL!')
        elif not languages:
            flash('Please select a language!')
        elif not models:
            flash('Please select a model!')
        elif not urlDetect:
            flash('Please enter valid YouTube URL!')
        elif not languageDetect:
            flash('Please enter the valid language!')
        elif not modelDetect:
            flash('Please enter the valid model!')

    return render_template('youtube.html', pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'],
                           languageList=languageList, user=user)


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    user = session.get('user')
    languageList = getLanguagesList()
    languageDetect = False
    modelDetect = False

    if request.method == 'POST':
        file = request.files['file']
        languages = request.form.get('languages')
        models = request.form.get('models')

        if languages == "Auto-Detect":
            languageDetect = True

        for language in languageList:
            if language == languages:
                languageDetect = True

        for model in modelList:
            if model == models:
                modelDetect = True

        if file and languageDetect and modelDetect:
            videoName = file.filename.rsplit('.', 1)[0]
            filetype = file.filename.rsplit('.', 1)[1]
            filename = nameReplace(videoName)

            # Resolve naming duplicate
            records = getrecords()
            for record in records:
                if filename == record['filename']:
                    flash('The file already exists!')
                    return redirect(url_for('upload_file'))

            # Covert to mp4 & wav
            video_path = os.path.join(app.config['UPLOAD_VIDEOS'], filename)
            file.save(video_path + "." + filetype)

            if filetype != "mp4":
                mp4_output_file = f"{video_path}.mp4"
                convert_to_mp4(video_path + "." + filetype, mp4_output_file)
                os.remove(video_path + "." + filetype)

            audio_path = os.path.join(app.config['UPLOAD_AUDIOS'], filename)
            wav_output_file = f"{audio_path}.wav"
            convert_to_wav(video_path + ".mp4", wav_output_file)

            # Convert to Text
            start_subtitle_time = time.time()
            generateSubtitle(filename, models, languages)
            end_subtitle_time = time.time()

            # Open subtitle file
            text = openSubtitleFile(filename)

            # Summarizing
            start_summarize_time = time.time()
            messages = summarize(text, videoName, languages)
            end_summarize_time = time.time()

            # Calculate the time
            print()
            run_subtitle_time = end_subtitle_time - start_subtitle_time
            subtitle_hours = int(run_subtitle_time // 3600)
            subtitle_minutes = int((run_subtitle_time % 3600) // 60)
            subtitle_seconds = int(run_subtitle_time % 60)

            if subtitle_hours > 0:
                print(f"Generate Subtitle Total Time：{subtitle_hours}H {subtitle_minutes}M {subtitle_seconds}")
            elif subtitle_minutes > 0:
                print(f"Generate Subtitle Total Time：{subtitle_minutes}M {subtitle_seconds}S")
            else:
                print(f"Generate Subtitle Total Time：{subtitle_seconds}S")

            run_summarize_time = end_summarize_time - start_summarize_time
            summarize_hours = int(run_summarize_time // 3600)
            summarize_minutes = int((run_summarize_time % 3600) // 60)
            summarize_seconds = int(run_summarize_time % 60)

            if summarize_hours > 0:
                print(f"Generate Summarize Total Time：{summarize_hours}H {summarize_minutes}M {summarize_seconds}")
            elif summarize_minutes > 0:
                print(f"Generate Summarize Total Time：{summarize_minutes}M {summarize_seconds}S")
            else:
                print(f"Generate Summarize Total Time：{summarize_seconds}S")

            run_time = end_summarize_time - start_subtitle_time
            hours = int(run_time // 3600)
            minutes = int((run_time % 3600) // 60)
            seconds = int(run_time % 60)

            if hours > 0:
                print(f"Total Time：{hours}H {minutes}M {seconds}")
            elif minutes > 0:
                print(f"Total Time：{minutes}M {seconds}S")
            else:
                print(f"Total Time：{seconds}S")

            # Return
            return render_template('videoInfo.html', pathSrc=app.config['UPLOAD_SRC'],
                                   pathUser=app.config['UPLOAD_USER'], pathVideos=app.config['UPLOAD_VIDEOS'],
                                   pathSubtitles=app.config['UPLOAD_SUBTITLES'], filename=filename, title=videoName,
                                   subtitle=text, messages=messages, languageList=languageList, user=user, web='upload')
        elif not file:
            flash('Please select a video!')
        elif not languages:
            flash('Please select a language!')
        elif not models:
            flash('Please select a model!')
        elif not languageDetect:
            flash('Please enter the valid language!')
        elif not modelDetect:
            flash('Please enter the valid model!')

    return render_template('upload.html', pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'],
                           languageList=languageList, user=user)


@app.route('/refresh', methods=['GET', 'POST'])
def refresh():
    user = session.get('user')
    languageList = getLanguagesList()

    if request.method == 'POST':
        filename = request.form.get('filename')
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        sumLang = request.form.get('summaryLanguages')
        messages = request.form.get('summarize')
        date = request.form.get('date')
        web = request.form.get('web')

        setSubtitle(filename, subtitle)

        return render_template('videoInfo.html', pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'],
                               pathVideos=app.config['UPLOAD_VIDEOS'], pathSubtitles=app.config['UPLOAD_SUBTITLES'],
                               filename=filename, title=title, subtitle=subtitle, sumLang=sumLang, messages=messages,
                               date=date, languageList=languageList, user=user, web=web)


@app.route('/regenerate', methods=['GET', 'POST'])
def regenerateSummarize():
    user = session.get('user')
    languageList = getLanguagesList()
    languageDetect = False

    if request.method == 'POST':
        filename = request.form.get('filename')
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        sumLang = request.form.get('summaryLanguages')
        messages = request.form.get('summarize')
        date = request.form.get('date')
        web = request.form.get('web')

        for language in languageList:
            if language == sumLang:
                languageDetect = True

        setSubtitle(filename, subtitle)

        if not filename:
            flash('Please select a video!')
            return redirect(url_for('upload_file'))
        elif not title:
            flash('Please fill in the title!')
            return render_template('videoInfo.html', pathSrc=app.config['UPLOAD_SRC'],
                                   pathUser=app.config['UPLOAD_USER'], pathVideos=app.config['UPLOAD_VIDEOS'],
                                   pathSubtitles=app.config['UPLOAD_SUBTITLES'], filename=filename, subtitle=subtitle,
                                   sumLang=sumLang, messages=messages, date=date, languageList=languageList, user=user,
                                   web=web)
        elif not languageDetect:
            flash('Please enter the valid language!')
            return render_template('videoInfo.html', pathSrc=app.config['UPLOAD_SRC'],
                                   pathUser=app.config['UPLOAD_USER'], pathVideos=app.config['UPLOAD_VIDEOS'],
                                   pathSubtitles=app.config['UPLOAD_SUBTITLES'], filename=filename, title=title,
                                   subtitle=subtitle, messages=messages, date=date, languageList=languageList,
                                   user=user, web=web)

        # Re-summarize
        messages = summarize(subtitle, title, sumLang)

        return render_template('videoInfo.html', pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'],
                               pathVideos=app.config['UPLOAD_VIDEOS'], pathSubtitles=app.config['UPLOAD_SUBTITLES'],
                               filename=filename, title=title, subtitle=subtitle, sumLang=sumLang, messages=messages,
                               date=date, languageList=languageList, user=user, web=web)

    return redirect(url_for('upload_file'))


@app.route('/uploadVideo', methods=['GET', 'POST'])
def upload_video():
    user = session.get('user')
    languageList = getLanguagesList()

    if request.method == 'POST':
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        filename = request.form.get('filename')
        messages = request.form.get('summarize')
        web = request.form.get('web')

        fileDuplicate = False
        records = getrecords()
        for record in records:
            if filename == record['filename']:
                fileDuplicate = True

        if not filename:
            flash('Please select a video!')
            return redirect(url_for('upload_file'))
        elif not title:
            flash('Please fill in the title!')
            return render_template('videoInfo.html', pathSrc=app.config['UPLOAD_SRC'],
                                   pathUser=app.config['UPLOAD_USER'], pathVideos=app.config['UPLOAD_VIDEOS'],
                                   pathSubtitles=app.config['UPLOAD_SUBTITLES'], filename=filename, subtitle=subtitle,
                                   messages=messages, languageList=languageList, user=user, web=web)
        elif fileDuplicate:
            flash('The file already exists!')
            return redirect(url_for('index'))

        setSubtitle(filename, subtitle)

        # Capture Video Frame
        cap = cv2.VideoCapture(app.config['UPLOAD_VIDEOS'] + "/" + filename + ".mp4")

        for _ in range(59):
            ret, _ = cap.read()
            if not ret:
                print("Error reading frame")
                cap.release()
                return

        ret, frame = cap.read()

        if not ret:
            print("Error reading frame")
            cap.release()
            return

        cv2.imwrite(app.config['UPLOAD_IMAGES'] + "/" + filename + ".png", frame, [cv2.IMWRITE_PNG_COMPRESSION, 0])
        cap.release()

        # Save data
        date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        record = {"username": user, "title": title, "filename": filename, "date": date, "summarize": messages}
        record_json = json.dumps(record)
        cursor.execute('INSERT INTO uploads (info) VALUES (?)', (record_json,))
        data_base.commit()

        return redirect(url_for('index'))

    return redirect(url_for('upload_file'))


@app.route("/manageVideo", methods=['GET', 'POST'])
def manageVideo():
    user = session.get('user')
    languageList = getLanguagesList()
    records = getrecords()
    targets = []

    for record in records:
        if user == record['username']:
            targets.append(record)

    if not targets:
        flash("There are currently no videos uploaded!")
        return render_template('manageVideo.html', pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'],
                               user=user)

    if request.method == 'POST':
        filename = request.form.get('filename')
        for target in targets:
            if filename == target['filename']:
                subtitle = openSubtitleFile(filename)
                return render_template('videoInfo.html', pathSrc=app.config['UPLOAD_SRC'],
                                       pathUser=app.config['UPLOAD_USER'], pathVideos=app.config['UPLOAD_VIDEOS'],
                                       pathSubtitles=app.config['UPLOAD_SUBTITLES'], filename=filename,
                                       title=target['title'], subtitle=subtitle, messages=target['summarize'],
                                       date=target['date'], languageList=languageList, user=user, web='edit')

    return render_template('manageVideo.html', pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'],
                           pathImages=app.config['UPLOAD_IMAGES'], targets=targets[::-1], user=user)


@app.route("/edit", methods=['POST'])
def edit():
    user = session.get('user')
    languageList = getLanguagesList()

    if request.method == 'POST':
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        filename = request.form.get('filename')
        messages = request.form.get('summarize')
        date = request.form.get('date')
        web = request.form.get('web')

        if not title:
            flash('Please fill in the title!')
            return render_template('videoInfo.html', pathSrc=app.config['UPLOAD_SRC'],
                                   pathUser=app.config['UPLOAD_USER'], pathVideos=app.config['UPLOAD_VIDEOS'],
                                   pathSubtitles=app.config['UPLOAD_SUBTITLES'], filename=filename, subtitle=subtitle,
                                   messages=messages, date=date, languageList=languageList, user=user, web=web)

        setSubtitle(filename, subtitle)

        record = {"username": user, "title": title, "filename": filename, "date": date, "summarize": messages}
        record_json = json.dumps(record)
        update_statement = '''
            UPDATE uploads
            SET info = ?
            WHERE json_extract(info, "$.filename") = ?
        '''
        cursor.execute(update_statement, (record_json, filename))
        data_base.commit()

        return redirect(url_for('index'))


@app.route("/addSubtitle", methods=['POST'])
def addSubtitle():
    user = session.get('user')
    filename = request.form.get('filename')
    subtitle = request.form.get('subtitle')
    languageList = getLanguagesList()
    records = getrecords()
    languageTarget = getLanguageTarget(filename)

    for record in records:
        if filename == record['filename']:
            return render_template('addSubtitle.html', pathSrc=app.config['UPLOAD_SRC'],
                                   pathUser=app.config['UPLOAD_USER'], pathVideos=app.config['UPLOAD_VIDEOS'],
                                   pathSubtitles=app.config['UPLOAD_SUBTITLES'], filename=filename,
                                   title=record['title'], subtitle=subtitle, languageList=languageList,
                                   languageTarget=languageTarget, user=user)


@app.route("/selectSubLang", methods=['POST'])
def selectSubLang():
    user = session.get('user')
    filename = request.form.get('filename')
    title = request.form.get('title')
    subtitle = request.form.get('subtitle')
    oldSubLang = request.form.get('oldSubLang')
    subLang = request.form.get('subLang')
    languageList = getLanguagesList()
    languageTarget = getLanguageTarget(filename)

    if subLang and oldSubLang:
        setSubtitle(filename + "_" + oldSubLang, subtitle)
    elif not subLang:
        flash('Select subtitle language!')
        return render_template('addSubtitle.html', pathSrc=app.config['UPLOAD_SRC'],
                               pathUser=app.config['UPLOAD_USER'], pathVideos=app.config['UPLOAD_VIDEOS'],
                               pathSubtitles=app.config['UPLOAD_SUBTITLES'], filename=filename, title=title,
                               languageList=languageList, languageTarget=languageTarget, user=user)

    for list in languageTarget:
        if subLang == list:
            subtitle = openSubtitleFile(filename + "_" + subLang)
            return render_template('addSubtitle.html', pathSrc=app.config['UPLOAD_SRC'],
                                   pathUser=app.config['UPLOAD_USER'], pathVideos=app.config['UPLOAD_VIDEOS'],
                                   pathSubtitles=app.config['UPLOAD_SUBTITLES'], filename=filename, title=title,
                                   subtitle=subtitle, subLang=subLang, languageList=languageList,
                                   languageTarget=languageTarget, user=user)

    # Open prompt txt
    with open("static/subtitlePrompt.txt", 'r') as f:
        prompt = f.read()

    subtitle = openSubtitleFile(filename)
    messages = ""
    input_text = (prompt + "The language in which you generate results must be " + subLang + ". "
                  + "You can only answer the results. "
                  + "The following content is the .VTT file:\n" + subtitle)

    # Provider(ChatBase, ChatForAi, ChatgptAi, FakeGpt, Hashnode, DeepInfra)
    response = g4f.ChatCompletion.create(model='gpt-3.5-turbo', provider=g4f.Provider.ChatgptAi,
                                         messages=[{"role": "user", "content": input_text}],
                                         stream=g4f.Provider.ChatgptAi.supports_stream)

    for message in response:
        messages += message
        print(message, flush=True, end='')

    setSubtitle(filename + "_" + subLang, messages)

    languageTarget = getLanguageTarget(filename)

    return render_template('addSubtitle.html', pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'],
                           pathVideos=app.config['UPLOAD_VIDEOS'], pathSubtitles=app.config['UPLOAD_SUBTITLES'],
                           filename=filename, title=title, subtitle=messages, subLang=subLang,
                           languageList=languageList, languageTarget=languageTarget, user=user)


@app.route("/refreshSubtitle", methods=['POST'])
def refreshSubtitle():
    user = session.get('user')
    languageList = getLanguagesList()

    if request.method == 'POST':
        filename = request.form.get('filename')
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        subLang = request.form.get('subLang')
        languageTarget = getLanguageTarget(filename)

        if subLang:
            setSubtitle(filename + "_" + subLang, subtitle)
        else:
            flash('Select subtitle language!')

        return render_template('addSubtitle.html', pathSrc=app.config['UPLOAD_SRC'],
                               pathUser=app.config['UPLOAD_USER'], pathVideos=app.config['UPLOAD_VIDEOS'],
                               pathSubtitles=app.config['UPLOAD_SUBTITLES'], filename=filename,
                               title=title, subtitle=subtitle, subLang=subLang, languageList=languageList,
                               languageTarget=languageTarget, user=user)


@app.route("/addSub", methods=['POST'])
def addSub():
    if request.method == 'POST':
        filename = request.form.get('filename')
        subtitle = request.form.get('subtitle')
        subLang = request.form.get('subLang')

        if subLang:
            setSubtitle(filename + "_" + subLang, subtitle)

        return redirect(url_for('manageVideo'))


@app.route("/delete", methods=['POST'])
def delete():
    filename = request.form.get('filename')
    delete_statement = 'DELETE FROM uploads WHERE json_extract(info, "$.filename") = ?'
    cursor.execute(delete_statement, (filename,))
    data_base.commit()

    files = os.listdir(app.config['UPLOAD_SUBTITLES'])

    # 遍历并删除包含 "mikumiku" 的文件
    for file in files:
        if filename in file:
            file_path = os.path.join(app.config['UPLOAD_SUBTITLES'], file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"{file} 已删除")
                else:
                    print(f"{file} 不是文件")
            except Exception as e:
                print(f"删除 {file} 时发生错误: {e}")

    return redirect(url_for('manageVideo'))


# In[7]:

@app.route("/player/<filename>", methods=['GET'])
def player(filename):
    user = session.get('user')
    pathVideo = "../" + app.config['UPLOAD_VIDEOS'] + "/" + filename + ".mp4"
    pathSubtitle = "../" + app.config['UPLOAD_SUBTITLES'] + "/" + filename
    target = []
    records = getrecords()

    for record in records:
        if filename == record['filename']:
            target.append(record)

    # If target not null，get first node
    targets = target[0] if target else None

    languageTarget = getLanguageTarget(filename)

    return render_template('player.html', pathSrc=app.config['UPLOAD_SRC'], pathUser=app.config['UPLOAD_USER'],
                           pathImages=app.config['UPLOAD_IMAGES'], pathVideo=pathVideo, pathSubtitle=pathSubtitle,
                           targets=targets, records=records[::-1], languageList=languageTarget, user=user)


# In[8]:

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
