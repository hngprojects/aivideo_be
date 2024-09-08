import json
with open('resources.json', 'r') as file:
    data = json.load(file)

# Access and print the value associated with the key 'data'
data = [ i for i in data if i['is_published'] == True ]
with open('resources.json', 'w') as file:
    # Write the list of dictionaries to the file
    json.dump(data, file, indent=4)
print("Savessuccesfully written")