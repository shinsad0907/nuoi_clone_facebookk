import sys
import json

class ActionInteraction:
    def __init__(self) -> None:
        self.data = json.loads(sys.argv[1])
        with open('data/action.json', 'r') as f:
            self.data_actions = json.load(f)
        # print(self.data)
    def main(self):
        # Xử lý dữ liệu ở đây
        new_data = {
            'name': f'{self.data['actionName']['name']}',
            'timeRange':{
                'start': f"{self.data['timeRange']['start']}",
                'end': f"{self.data['timeRange']['end']}",
            },
            'likeVideo':{
                "count": f"{self.data['likeVideos']['count']}",
                "delay": f"{self.data['likeVideos']['delay']}",
            },
            'followUsers':{
                "count": f"{self.data['followUsers']['count']}",
                "delay": f"{self.data['followUsers']['delay']}",
            },
            'commentVideos':{
                "count": f"{self.data['commentVideos']['count']}",
                "delay": f"{self.data['commentVideos']['delay']}",
            },
            'readCommentsDuration': f"{self.data['readCommentsDuration']}",
            'watchVideoDuration': f"{self.data['watchVideoDuration']}",
            'commentVideos':{
                "count": f"{self.data['commentVideos']['count']}",
                "delay": f"{self.data['commentVideos']['delay']}",
            },
            'readCommentsDuration': f"{self.data['readCommentsDuration']}",
            'uploadVideos':{
                "count": f"{self.data['uploadVideos']['count']}",
                "delay": f"{self.data['uploadVideos']['delay']}",
            },
            'viewStories':{
                "count": f"{self.data['viewStories']['count']}",
                "delay": f"{self.data['viewStories']['delay']}",
            },
            'shareVideos':{
                "count": f"{self.data['shareVideos']['count']}",
                "delay": f"{self.data['shareVideos']['delay']}",
            },
        }
        for data_action in self.data_actions['database']:
            if data_action['name'] == self.data['actionName']['name']:
                data_action.update(new_data)
                break
        with open('data/action.json', 'w') as f:
            json.dump(self.data_actions, f, indent=4)
        # Thêm xử lý khác tại đây nếu cần

if __name__ == "__main__":
    ActionInteraction().main()