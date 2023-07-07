# telegram-bot-google-drive

# telegram-bot-google-drive

## Getting Started 

Create a virtual python environment
```console
python -m venv .venv
```
Activate the python environment. 
```console
.\.venv\Scripts\activate
```
Install the requirements into the environment.
```console
pip install -r .\requirements.txt
```
Run the bot.py
```console
python 
.\src\bot.py
```

## BotFather
Use https://t.me/BotFather to create and manage your Telegram bots.
You get your Telegram API Token from BotFather.

## Environment Variables
Environment variables are used to store API tokens.

### TELEGRAM_API_TOKEN 
The token from Botfather for the Telgram API

### LOCATION_IQ_API_TOKEN 
Token for Location IQ API get the location of a pictures or videos.
Possibly needed in the future.

## Telegram Token API 

You need an API Token for Telegram. Such a token can be created with the @Botfather bot from telegram. The bot needs to turn off group privacy mode.

## Google Drive API

You need OAuth Client credentials for Google Workspace. There is a project in the [google cloud console](https://console.cloud.google.com/) named telegram-Google-drive-bot. You can use the credentials from there. See [this](https://developers.google.com/drive/api/quickstart/python) guide for further information. In the oAuthScreen login with the apps@letztegeneration.at workspace account.

Should be handeled with Service Account in the future.

## Location IQ API Token

Location IQ could be used in the future to get the location of a picture or video taken by its longitude and latitude.

## Dokcer

Build
```console
docker build . -t lastgenat/telegram-bot-google-drive:tag
```

Build and compose 
```console
docker compose up --build telegram-bot-google-drive
```
Push to Hub
```console
docker push lastgenat/telegram-bot-google-drive:tag
```