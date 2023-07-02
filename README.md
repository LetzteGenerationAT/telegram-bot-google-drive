# telegram-bot-google-drive

## Getting Started 

- Create a virtual python environment. 
- Activate the python environment. 
- Install the requirements into the environment.
- Run the bot.py


## Environment Variables
Environment variables are used to store API tokens.

TELEGRAM_API_TOKEN ... with Telgram API Token

possible needed in the future:
LOCATION_IQ_API_TOKEN

## Telegram Token API 

You need an API Token for Telegram. Such a token can be created with the @Botfather bot from telegram. The bot needs to turn off group privacy mode. <br>
You need OAuth Client credentials for Google Workspace. There is a project in the [google cloud console](https://console.cloud.google.com/) named telegram-Google-drive-bot. You can use the credentials from there. See [this](https://developers.google.com/drive/api/quickstart/python) guide for further information. In the oAuthScreen login with the apps@letztegeneration.at workspace account.

## Location IQ API Token

Location IQ could be used in the future to get the location of a picture or video taken by its longitude and latitude.

