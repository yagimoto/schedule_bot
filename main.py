import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import os
import subprocess
import shlex
import fitz

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive"]

FOLDER = "schedule"

remote_id = "1dc4za_6u9XGp7y3L3JblsZoDsmo_8lAF"

def sync():
  cmd = "rclone sync remote:/02_教務係/2025年度/03_各週時間割 schedule/"
  tokens = shlex.split(cmd) # => ['ls', 'tmp']
  subprocess.run(tokens)

def get_drive_service():
  """Shows basic usage of the Drive v3 API.
  Prints the names and ids of the first 10 files the user has access to.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first

  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())


  return build("drive", "v3", credentials=creds)
    
def upload():
  
  service = get_drive_service()

  #scheduleフォルダにあるファイル名を配列に入れる
  files_file = [
    f for f in os.listdir(FOLDER) if os.path.isfile(os.path.join(FOLDER, f))
  ]

  for f in files_file:
    file_name = f
    file_metadata = {
      'name': file_name,
      'parents': [remote_id],  # ファイルID(ドライブURIの’folders/’に続く値)
    }

    media = MediaFileUpload(FOLDER + "/" + file_name, mimetype="image/jpeg")

    file = service.files().create(
      body=file_metadata,
      media_body=media,
      fields='id',
    ).execute()

def delete_file(file_id):
  service = get_drive_service()
  service.files().delete(fileId=file_id).execute()

def delete_files_in_folder(folder_id):
  
  service = get_drive_service()
  
  # フォルダ内のファイルを検索
  query = f"'{folder_id}' in parents and trashed = false"
  results = service.files().list(
      q=query,
      fields="files(id, name)"
  ).execute()
  
  items = results.get('files', [])
  
  if not items:
      return
  
  for item in items:
      delete_file(item['id'])
  
def convert_pdf_to_jpg():
  dir_path = FOLDER

  files_file = [
      f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
  ]

  for count, f in enumerate(files_file):
    doc = fitz.open(os.path.join(FOLDER, f))
    page = doc.load_page(0)

    mat = fitz.Matrix(3, 3)
    pix = page.get_pixmap(matrix=mat)

    filename = str(count) + ".jpg"
    pix.save(os.path.join(FOLDER, filename))

    doc.close()

    os.remove(os.path.join(FOLDER, f))
    
  
if __name__ == "__main__":
  sync()
  delete_files_in_folder(remote_id)
  convert_pdf_to_jpg()
  upload()