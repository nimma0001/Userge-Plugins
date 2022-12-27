

# here you can do the main thing like registering handlers, ...

from userge import userge, Message, get_collection
import google.auth
from googleapiclient.discovery import build
import pickle
from googleapiclient.errors import HttpError
import subprocess
from datetime import date
# Insert your own values for the credentials variables
# from .. import ll_in_one as test
_SAVED_SETTINGS = get_collection("CONFIGS")


@userge.on_start
async def _init() -> None:
    global service  # pylint: disable=global-statement
    result = await _SAVED_SETTINGS.find_one({'_id': 'GDRIVE'}, {'creds': 1})
    _CREDS = pickle.loads(result['creds']) if result else None  # nosec
    service = build('drive', 'v3', credentials=_CREDS)
    

def download_file(file_id):
    try:
        response = service.files().get(
                fileId=file_id, fields='name', supportsTeamDrives=True).execute()

        name = response['name']
        today = date.today().strftime("%d")
        name = name.lower().replace('1337xhd.shop-big ', str(today)).replace('mlsbd.shop', '')
        request = service.files().get_media(fileId=file_id, name=name)
        file = request.execute()
        with open(save_path, 'wb') as f:
            f.write(file)
        subprocess.call(['bash', 'did.sh', name, str(today)])
        return True
    except HttpError as error:
        print(f'An error occurred: {error}')
        return False
    

@userge.on_cmd("gdown2", about="my first command")
async def first_command(message: Message) -> None:
    """ this thing will be used as command doc string """
    message
    await message.edit(message.input_str.split('=')[1])
#     await message.send_message(message.text)
    await message.edit("downloading file...")  
    success = download_file(message.input_str.split('=')[1])

