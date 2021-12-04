from cryptography.fernet import Fernet
import pathlib
import os
from dotenv import load_dotenv
load_dotenv()


def generate_keys():
    return Fernet.generate_key().decode('UTF-8')


def encrypt_dir(input_dir,output_dir):
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    if not ENCRYPTION_KEY:
        raise Exception('Key is not found')
    fer = Fernet(ENCRYPTION_KEY)
    input_dir = pathlib.Path(input_dir)
    output_dir = pathlib.Path(output_dir)
    input_dir.mkdir(exist_ok=True,parents=True)
    output_dir.mkdir(exist_ok=True,parents=True)
    
    for path in input_dir.glob('*'):
        _path_bytes = path.read_bytes()
        data = fer.encrypt(_path_bytes)
        rel_path = path.relative_to(input_dir)
        dest_path = output_dir / rel_path
        dest_path.write_bytes(data)
        
def decrypt_dir(secure_dir,output_dir):
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
    if not ENCRYPTION_KEY:
        raise Exception('Key is not found')
    fer = Fernet(ENCRYPTION_KEY)
    secure_dir = pathlib.Path(secure_dir)
    output_dir = pathlib.Path(output_dir)
    secure_dir.mkdir(exist_ok=True,parents=True)
    output_dir.mkdir(exist_ok=True,parents=True)
    
    for path in secure_dir.glob('*'):
        _path_bytes = path.read_bytes()
        data = fer.decrypt(_path_bytes)
        rel_path = path.relative_to(secure_dir)
        dest_path = output_dir / rel_path
        dest_path.write_bytes(data)
    





