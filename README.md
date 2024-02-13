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

Use <https://t.me/BotFather> to create and manage your Telegram bots.
You get your Telegram API Token from BotFather.

## Environment Variables

Environment variables are used to store API tokens.

### TELEGRAM_API_TOKEN 

The token from Botfather for the Telgram API

### LOCATION_IQ_API_TOKEN 

Token for Location IQ API get the location of a pictures or videos.
Possibly needed in the future.

### TELEGRAM_API_ID 

Token for the local API, get it from [here](https://core.telegram.org/api/obtaining_api_id)

### TELEGRAM_API_HASH

Hash for the local API, get it from [here](https://core.telegram.org/api/obtaining_api_id)

## Telegram Token API

You need an API Token for Telegram. Such a token can be created with the @Botfather bot from telegram. The bot needs to turn off group privacy mode.

## Google Drive API

You need OAuth Client credentials for Google Workspace. There is a project in the [google cloud console](https://console.cloud.google.com/) named telegram-Google-drive-bot. You can use the credentials from there. See [this](https://developers.google.com/drive/api/quickstart/python) guide for further information. In the oAuthScreen login with the apps@letztegeneration.at workspace account.

Should be handled with Service Account in the future.

## Location IQ API Token

Location IQ could be used in the future to get the location of a picture or video taken by its longitude and latitude.

## Telegram Bot API

File download functions (download_as_bytearray, download_to_drive, download_to_memory) of the [python-telegram-bot](https://docs.python-telegram-bot.org/en/stable/index.html) library won't work anymore when using the local telegram-bot-api. The files should be loaded from the filesystem instead. Hence use a shared volume for all container which want to access the telegram-bot-api's data folder.

To use a shared volume be aware of the permissions of the telegram-bot-api's data folder. The telegram-bot-api is deployed in its own docker container. The data (images, videos) of the telegram-bot-api are saved to the mounted volume folder. This folder's owner's group id (101) needs to be added as group id to every docker image user who wants to access this folder.

The port of the telegram-bot-api needs to be opened to be used by telegram bots.

To use the API locally for development open the port for the Telegram API in your router.

## Docker

Build

```console
docker build . -t lastgenat/telegram-bot-google-drive:tag
```

Build and compose

```console
docker compose up --build telegram-bot-google-drive telegram-bot-api
```

Push to Hub

```console
docker push lastgenat/telegram-bot-google-drive:tag
```

Preconfigured config files can be found in the [Google Drive](https://drive.google.com/drive/folders/1s0WdrocS--smVNOP8CWSjwzansrxmJ6J). This docker compose file can be used with the `-f` flag.

```console
docker compose -f docker-composeDEV.yml up
```

## Deploy

Before each deploy the telegram-bot-api-data folder on the host system needs to be delted. The folder needs to be delted because of permission resitrictions between container deploys. Set the correct time zone on system level, since the application looks up the current local time to assign time stamps. TODO: solve permission restrictions.