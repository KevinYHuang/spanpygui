import re

def increment_name(name, existing_names):
    while name in existing_names:
        counter = 0
        match = re.match(r'^(.+)\((\d+)\)$', name)
        if match:
            name, counter = match.groups()
            counter = int(counter)
        name = f'{name}({counter+1})'
    return name