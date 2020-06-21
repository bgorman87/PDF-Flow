import json

filename = r"C:\Users\gormbr\OneDrive - EnGlobe Corp\Desktop\sorter_data.json"

# Read JSON data into the datastore variable
if filename:
    with open(filename, 'r') as f:
        datastore = json.load(f)

for i in datastore:
    print('Project: {0}\nDesc: {1}'.format(i['project_number'], i['project_description']))