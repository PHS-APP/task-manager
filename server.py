#!/usr/bin/env python3
from flask import Flask
from flask import render_template as render
from flask_sock import Sock
import json
from werkzeug.exceptions import abort

server = Flask(__name__, static_folder="assets")
sock = Sock(server)
#socketio = SocketIO(server)

def mkTask (value, priority="med", labels=None, subtasks=None, locked=False):
	task = {"name":value, "priority":priority, "labels":labels if labels else [], "subtasks":subtasks if subtasks else [], "locked":True if locked else False}
	return task

project1tasks = [
	{"name":"anoutrageouslylongtaskname", "priority":"low", "desc":"a testing task", "labels":[], "subtasks":[], "locked":False, "completed":False},
	{"name":"task2", "priority":"high", "desc":"a testing task", "labels":[], "subtasks":[], "locked":False, "completed":False}
]

testservertasks = [
	{"name":"test1", "priority":"low", "desc":"subtask testing", "labels":["bug"], "subtasks":[{"name":"subtask1", "priority":"low", "desc":"subtask testing", "labels":[], "subtasks":[], "locked":False, "completed":False}], "locked":False, "completed":False},
	{"name":"general", "priority":"high", "desc":"general testing", "labels":[], "subtasks":[], "locked":False, "completed":False}
]

projects = {"project1":project1tasks, "xyz":testservertasks}
icons = {"project1":{}, "xyz":{"bug":"/assets/label-icons/bug.svg"}}


# helper function to get index of task in a list
def task_index (search, task):
	if (type(task) == dict):
		task = task["name"]
	for i in range(len(search)):
		if (search[i]["name"] == task):
			return i
	return -1

@server.endpoint("index")
def projectsf ():
	return render("projects-template.html", projects=projects)

server.add_url_rule("/", endpoint="index")
server.add_url_rule("/projects", endpoint="index")

@server.route("/help")
def help_page ():
	return render("help.html")

@server.route("/projects/<project>")
def projectf (project):
	if (project not in projects.keys()):
		abort(404)
	return render("manager-template.html", project_name=project, project=projects[project])

@server.route("/err/<code>")
def errorredirect (code):
	if (code == 0):
		abort(404)
	else:
		abort(500)

@server.errorhandler(404)
def handle_bad_request (e):
	return render("errors/400.html"), 404

@server.errorhandler(500)
def handle_internal_error (e):
	return render("errors/500.html"), 500

# @socketio.on("connection")
# def hand_connect (*a):
#	pass

# @socketio.on("pboot")
# def boot_project_client ():
#	flask_socketio.join_room("project-view")
#	emit("boot-res")

# @socketio.on("leav-proj")
# def leave_project ():
#	print("leaving")
#	# id = flask_socketio.flask.request.sid
#	rooms = flask_socketio.rooms()
#	flask_socketio.leave_room(rooms[1])

def _taskform (lst, indent=0):
	final = ""
	for task in lst:
		keys = list(task.keys())
		for i in range(len(keys)):
			final += "    "*indent
			key = keys[i]
			final += f"{key} : "
			if (key == "subtasks"):
				final += f"[\n{_taskform(task[key], indent+1)}\n],\n" if len(task[key]) > 0 else "[],\n"
			else:
				final += f"{task[key]}"+(",\n" if i < len(keys)-1 else "")
	if (indent == 0):
		return f"\n[\n{final}\n]\n"
	return final

def _projform ():
	f = "[\n"
	for key in projects.keys():
		f += f"{key} : "
		f += _taskform(projects[key])
		f += ",\n"
	f += "\n]"
	return f

# @socketio.on("dump--db")
# def dump__db (*a):
#	if (not a):
#		print(_projform())
#	else:
#		print(_taskform(projects[a[0]["name"]]))

# websocket server
@sock.route("/ws")
def handle_request(websocket):
	while True:
		request = json.loads(websocket.receive())
		data = request["data"]
		if request["name"] == "boot":
			data["id"] = 0
			data["project"] = {"tasks":projects[data["project"]], "icons":icons[data["project"]]}
			websocket.send(json.dumps(data))
		elif request["name"] == "change-task-property":
			origin = data["origin"]
			path = data["path"]
			proj = projects[origin]
			value = data["value"]
			task = None
			for step in path:
				task = proj[task_index(proj, step)]
				proj = task["subtasks"]
			task[data["property"]] = value;
			print(task)
			data["id"] = 2
			websocket.send(json.dumps(data))
		elif request["name"] == "rename-proj":
			origin = data["origin"]
			name = data["newname"]
			proj = projects[origin]
			projects[name] = proj
			projects.pop(origin)
			icos = icons[origin]
			icons[name] = icos
			icons.pop(origin)
			data["id"] = 1
			websocket.send(json.dumps(data))
		elif request["name"] == "add-task":
			origin = data["origin"]
			search = projects[origin]
			task = data["task"]
			path = data["path"]
			for i in range(len(path)):
				step = path[i]
				index = task_index(search, step)
				search = search[index]["subtasks"]
			if (task_index(search, task["name"]) != -1):
				return
			search.append(task)
			print(projects[origin])
			data["id"] = 7
			websocket.send(json.dumps(data))
		elif request["name"] == "remove-task":
			origin = data["origin"]
			search = projects[origin]
			path = data["path"]
			for i in range(len(path)-1):
				step = path[i]
				index = task_index(search, step)
				task = search[index]
				search = task["subtasks"]
			name = path[-1]
			print(search, name, "XYZ")
			search.pop(task_index(search, name))
			print(projects[origin])
			data["id"] = 6
			websocket.send(json.dumps(data))
	
# server
if __name__ == "__main__":
	server.run(host="0.0.0.0", port=3000, debug=True)
