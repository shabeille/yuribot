import json
import os

class StatsManager:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._total_sent = 0
        self._tag_counts: dict[str, int] = {}
        
        if os.path.exists(self.file_path):
            self.read_file()
            print("loaded stats file!")
            
    def get_posts_sent(self):
        return self._total_sent
        
    def record_post_sent(self):
        self._total_sent += 1
        
    def get_tags_used(self) -> dict[str, int]:
        return self._tag_counts
        
    def record_tag_used(self, tag: str):
        if tag in self._tag_counts.keys():
            self._tag_counts[tag] += 1
        else:
            self._tag_counts[tag] = 1
    
    def read_file(self):
        obj: dict
        
        with open(self.file_path, "r") as file:
            obj = json.loads(file.read())
        
        if "sent" in obj.keys():
            self._total_sent = obj["sent"]
            
        if "tags" in obj.keys():
            self._tag_counts = obj["tags"]
            
            
    def write_file(self):
        obj = {
            "sent": self._total_sent,
            "tags": self._tag_counts
        }
        
        with open(self.file_path, "w") as file:
            file.write(json.dumps(obj))
