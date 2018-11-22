import os
import sys


LOCAL_BIN = f'{os.getenv("HOME")}/.local/bin'
LOCAL_BIN_PLAYLABS = f'{LOCAL_BIN}/playlabs'
BASH_PROFILE = f'{os.getenv("HOME")}/.bash_profile'
KEYPATH = '.ssh_private_key'

USER = os.getenv('USER')
PASSWORD = None
HOST = None

PLAYBOOKS = os.path.join(
    os.path.dirname(__file__),
    os.pardir
)

INVENTORY_FILE = None
INVENTORY_DIR = None

for i in [
            'inventory.yaml',
            'inventory.yml',
            'inventory/inventory.yaml',
            'inventory/inventory.yml'
        ]:
    if os.path.exists(i):
        INVENTORY_FILE = os.path.abspath(i)
        INVENTORY_DIR = os.path.abspath(os.path.dirname(i))

if '/' in sys.argv[0]:
    os.environ['PATH'] = ':'.join([
        os.path.dirname(sys.argv[0]),
        os.getenv('PATH')
    ])
