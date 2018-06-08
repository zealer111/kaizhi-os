data = {
            "key": "1ad0c2b0-7370-47c0-9e1d-d6bc08e39737",
            "pid": 0,
            "index": -1,
            "is_assistant": 0,
            "title": "z",
            "type": 0,
            "children": [
                {
                    "key": "a1336c66-9084-4b4d-8916-c831ee610240",
                    "pid": "1ad0c2b0-7370-47c0-9e1d-d6bc08e39737",
                    "index": -1,
                    "is_assistant": 0,
                    "title": "z1",
                    "type": 0,
                    "children": [
                        {
                            "key": "2a5bf6d1-3870-4561-923e-ff0f04f19515",
                            "pid": "a1336c66-9084-4b4d-8916-c831ee610240",
                            "index": -1,
                            "is_assistant": 0,
                            "title": "z.md",
                            "type": 1,
                            "children": [
                                {
                                    "key": "2a5bf6d1-3870-4561-923e-ff0f04f19515",
                                    "pid": "a1336c66-9084-4b4d-8916-c831ee610240",
                                    "index": 1,
                                    "is_assistant": 0,
                                    "title": "z.md",
                                    "type": 1,
                                    "children": []
                                }
                            ]
                        }
                    ]
                }
            ]
        }

def TreeEach(data):
    d = data['children']
    print(d, "****")
    for child in d:
        child_data = child.get('children')
        # 1 create Card => pid
        # 2 params = {child, pid}
        if child_data:
            TreeEach(child)

TreeEach(data)
