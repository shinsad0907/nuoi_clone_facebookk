import sys, json

class save_action():
    def __init__(self):
        self.data = json.loads(sys.argv[1])
        self.action = sys.argv[2]
        try:
            with open('data/action.json', 'r') as f:
                self.data_action = json.load(f)
        except FileNotFoundError:
            self.data_action = []

    def create_nameaction(self):
        new_data = {
            'name': self.data
        }
        self.data_action['database'].append(new_data)
        print(f"created_successfully.")
        
    def save_settingaction(self):
        print(self.data,type(self.data))
        # Xử lý dữ liệu ở đây
        
        for data_action in self.data_action['database']:
            if data_action['name'] == self.data[0]['configName']:
                for data_action2 in self.data:
                    if data_action2['actionType'] == 'newfeed':
                        new_data = {
                            'name': f'{data_action2['configName']}',
                            'newfeed': {
                                'time': data_action2['time']
                            }
                        }
                    elif data_action2['actionType'] == 'ketban':
                        new_data = {
                            'name': f'{data_action2['configName']}',
                            'addfriend': {
                                'amount': data_action2['amount'],
                                'delay': data_action2['delay']
                            }
                        }
                    data_action.update(new_data)
    def save_data(self):
        with open('data/action.json', 'w') as f:
            json.dump(self.data_action, f, indent=4)

    def main(self):
        if self.action == 'create_nameaction':
            self.create_nameaction()
            self.save_data()
        elif self.action == 'save_settingaction':
            self.save_settingaction()
            self.save_data()
            

# Uncomment the following line to test the code
save_action().main()