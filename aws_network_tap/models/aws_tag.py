from typing import Dict, List


class AWSTag:
    NAME_KEY = 'Name'
    TAGS_KEY = 'Tags'

    Delete = None

    @staticmethod
    def to_dict(aws_tags: List[Dict]) -> Dict:
        response = {}
        if not aws_tags:
            return response
        for item in aws_tags:
            response[item['Key']] = item.get('Value', AWSTag.Delete)
        return response

    @staticmethod
    def to_tags(python_dict: Dict) -> List[Dict]:
        response = []
        for key in python_dict:
            _ = {'Key': key}
            if python_dict[key] != AWSTag.Delete:
                _['Value'] = python_dict[key]
            response.append(_)
        return response