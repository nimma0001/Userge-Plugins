
from userge import userge, Message
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import subprocess
from datetime import date
# Insert your own values for the credentials variables
# from .. import ll_in_one as test


@userge.on_start
async def _init() -> None:
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile('/app/token.json')
    drive = GoogleDrive(gauth)

@userge.on_cmd("gdown2", about="my first command")
async def first_command(message: Message) -> None:
    """ this thing will be used as command doc string """
    message
    today = date.today().strftime("%d")
    await message.edit(message.input_str.split('=')[1])
    file = drive.CreateFile({'id': message.input_str.split('=')[1]})
    name = file['title']
    #await message.send_message(message.text)
    name = name.lower().replace('1337xhd.', '').replace('mlsbd.shop', ' ').replace('shop',' ').replace('-', ' ').replace('  ', '').strip()
    await message.edit(f"{name} downloading file...")  
    file.GetContentFile(name, acknowledge_abuse=True)
    subprocess.call(['bash', 'did.sh', name, str(today)])
