Instruction for Windows:
1) install requirements.txt "pip install -r requirements.txt"
2) run main.py
3) open link "http://127.0.0.1:5000/" or "http://192.168.231.162:5000"


Install ffmpeg (Chocolatey required):
1) run "choco install ffmpeg"


Install Chocolatey:
1) PowerShell run as administrator
2) Run the following command:
"Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"


Install ngrok get free domain (Chocolatey required):
1) open link "https://ngrok.com/"
2) run "choco install ngrok"
3) run "ngrok config add-authtoken [YOUR_AUTHTOKEN]". For example, "ngrok config add-authtoken thIs_is_A_sAmPleSF64d64v89ds4vD64vD"


Run domain (ngrok required):
1) run "ngrok http 5000"
