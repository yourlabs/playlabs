import os
import shutil
import sys


def help():
    '''
    Print playlabs usage
    '''
    helptext = None
    with open(os.path.join(os.path.dirname(__file__), 'help.txt')) as f:
        helptext = f.read()
    print(helptext)


def scaffold(target):
    '''
    Create a inventory directory from template

    example:
        playlabs scaffold [target];

    param: target - the target dir which you want to scaffold in
    '''
    if os.path.exists(target):
        print(f'Drop existing {target}?')
        if input().lower() in ['y', 'yes']:
            shutil.rmtree(target)
        else:
            print('Aborting')
            sys.exit(1)

    print(f'Provisioning {target} from inventory template')
    shutil.copytree(
        os.path.join(
            os.path.dirname(__file__),
            os.pardir,
            'inventory_template',
        ),
        target,
    )
