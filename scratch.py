tasks = [
    {"id": 5, "title": "Do Laundry", "done": False},
    {"id": 2, "title": "Go Groceries Shopping", "done": False},
    {"id": 3, "title": "Clean the Kitchen", "done": True},
]

for task in tasks:
    print(task["id"])

# loop variables leak out of the loop and persist afterwards in python!

print(max(t["id"] for t in tasks))

row = [("id", 1), ("title", "Hi"), ("done", 0)]
row_dict = dict(row)

print(row_dict)
row_dict["done"] = bool(row_dict["done"])  # 0 => False

print(row_dict)
