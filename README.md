# WebVid2Text: Video-to-Text Conversion System

WebVid2Text is a robust AI-driven system designed for efficient video content processing.

## Key Features

1. **Audio-to-Subtitle Conversion:** Transforms video audio into text-based subtitles.
2. **G4F Summary Generation:** Utilizes G4F to generate concise summaries based on subtitles.
3. **Language-Agnostic Subtitles:** Choose your preferred language, and WebVid2Text generates subtitles accordingly.

## Instructions for Windows:

1. Install requirements using the following command:
    ```bash
    pip install -r requirements.txt
    ```

2. Run the main application:
    ```bash
    python main.py
    ```

3. Open the application through either of the following links:
    - [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
    - [http://192.168.231.162:5000/](http://192.168.231.162:5000/)

### Install Chocolatey:

1. Run PowerShell as administrator.
2. Execute the following command:
    ```powershell
    Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    ```

### Install ffmpeg (Chocolatey required):

1. Run the following command:
    ```bash
    choco install ffmpeg
    ```

### Install ngrok to get a free domain (Chocolatey required):

1. Get your AUTHTOKEN from [ngrok.com](https://ngrok.com/).
2. Run the following commands:
    ```bash
    choco install ngrok
    ngrok config add-authtoken [YOUR_AUTHTOKEN]
    ```

### Run domain (ngrok required):

1. Run the following command:
    ```bash
    ngrok http 5000
    ```

## Acknowledgements

Special thanks to the following authors and their projects:

- [xtekky/gpt4free](https://github.com/xtekky/gpt4free): The official gpt4free repository | various collection of powerful language models.

- [Carleslc/AudioToText](https://github.com/Carleslc/AudioToText): Transcribe and translate audio to text using Whisper and DeepL.

I express my gratitude to these authors for their valuable contributions to the open-source community.
