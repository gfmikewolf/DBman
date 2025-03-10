from enum import Enum

class ClauseAction(Enum):
    ADD = 'add'
    REMOVE = 'remove'
    UPDATE = 'update'

class test:
    x : ClauseAction = ClauseAction.ADD

if __name__ == "__main__":
    print(f'{test.x.__class__('add').value}')