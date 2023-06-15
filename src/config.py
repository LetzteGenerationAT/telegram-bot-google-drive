"""
Configurations for the scripts
"""
import os

if os.environ['TELEGRAM_API_TOKEN']:
    TELEGRAM_API_TOKEN = os.environ['TELEGRAM_API_TOKEN']
else: TELEGRAM_API_TOKEN = ""

if os.environ['LOCATION_IQ_API_TOKEN']:
    LOCATION_IQ_API_TOKEN = os.environ['LOCATION_IQ_API_TOKEN']
else: LOCATION_IQ_API_TOKEN = ""

# folder id of the drive folder ./Pressemitteilungen/Protest in KommAG
# can be set to None if testing to use root folder of the signed in user.
# PROTEST_FOLDER_ID = "19nJVk6IIK58lq4eX4K-_ynJ4jrJjg9uZ"
if os.environ['PROTEST_FOLDER_ID']:
    PROTEST_FOLDER_ID = os.environ['PROTEST_FOLDER_ID']
else: PROTEST_FOLDER_ID = "None"

if os.environ['TIMEZONE']:
    TIMEZONE = os.environ['TIMEZONE']
else: TIMEZONE = "Europe/Vienna"
