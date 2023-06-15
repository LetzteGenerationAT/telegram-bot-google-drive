# telegram-bot-google-drive

- Create a virtual python environemnt. 
- Activate the python environment. 
- Install the requirements into the environment.

## config

You need an API Token for Telgegram. Such a token can be created with the @Botfather bot from telegram. The bot needs to turn off group privacy mode. <br>
You need OAuth Client crendetials for Google Workspace. There is a project in the [google cloud console](https://console.cloud.google.com/) named TelegramGoogleDriveBot. You can use the credentials from there. See [this](https://developers.google.com/drive/api/quickstart/python) guide for further information. In the oAuthScreen login with the apps@letztegeneration.at workspace account.

If using docker add environment variables for the config values.