import json
import time


dic_list = [

]

with open('flights_record.json', 'w') as json_file:
    json.dump(dic_list, json_file)

print('Start detecting:', time.asctime(time.localtime()))
