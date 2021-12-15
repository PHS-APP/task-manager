from flask import Flask
from flask import render_template as render
import flask_socketio
SocketIO = flask_socketio.SocketIO
send = flask_socketio.send
emit = flask_socketio.emit
from werkzeug.exceptions import abort

server = Flask(__name__, static_folder="assets")
server.config["TEMPLATES_AUTO_RELOAD"] = True
socketio = SocketIO(server)

def mkTask (value, priority="med", labels=None, subtasks=None, locked=False):
	task = {"name":value, "priority":priority, "labels":labels if labels else [], "subtasks":subtasks if subtasks else [], "locked":True if locked else False}
	return task

project1tasks = [
	{"name":"anoutrageouslylongtaskname", "priority":"low", "desc":"a testing task", "labels":[], "subtasks":[], "locked":False, "completed":False},
	{"name":"task2", "priority":"high", "desc":"a testing task", "labels":[], "subtasks":[], "locked":False, "completed":False}
]

projects = {"project1":project1tasks}


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

# @server.context_processor
# def useful_functions():
# 	def task_html(task):
# 		if "subtasks" in task:
# 			html = "<p class=\'task\'>" + task["name"] + "</p>" + "<ul>"
# 			for subtask in task["subtasks"]:
# 				html += f"<li>" + task_html(subtask) + "</li>"
# 			html += "</ul>"
# 			return html
# 		else:
# 			return "<p class=\'task\'>" + task["name"] + "</p>"
# 	return dict(task_html=task_html)

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

# server.register_error_handler(404, handle_bad_request)

@socketio.on("connection")
def hand_connect (*a):
	pass

@socketio.on("boot")
def boot_client (data):
	print(data)
	flask_socketio.join_room(data["project"])
	print(flask_socketio.rooms())
	print(str(flask_socketio.has_request_context()), "boot")
	print(dir(flask_socketio.flask.request), "request")
	print(flask_socketio.flask.request.sid)
	emit("boot-res", {"tasks":projects[data["project"]]})

@socketio.on("remove-subtask")
def remove_subtask (data):
	origin = data["origin"]
	search = projects[origin]
	path = data["path"]
	for i in range(len(path)-1):
		step = path[i]
		index = task_index(search, step)
		task = search[index]
		search = task["subtasks"]
	search.pop(task_index(search, path[-1]))
	print(projects[origin])
	data["id"] = 6
	emit("update", data, to=origin)

@socketio.on("add-subtask")
def add_subtask (data):
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
	emit("update", data, to=origin)

@socketio.on("rename-proj")
def rename_proj (data):
	print(f"project rename by {flask_socketio.flask.request.sid}")
	origin = data["origin"]
	name = data["name"]
	proj = projects[origin]
	projects[name] = proj
	projects.pop(origin)
	data["id"] = 0
	emit("update", data, to=origin)

@socketio.on("rename-task")
def rename_task (data):
	print(f"task rename by {flask_socketio.flask.request.sid}")
	origin = data["origin"]
	oldname = data["name"]
	newname = data["newname"]
	proj = projects[origin]
	index = -1
	for i in range(len(proj)):
		if (proj[i]["name"] == oldname):
			index = i
			break
	if (index < 0):
		return
	proj[i]["name"] = newname
	projects[origin] = proj
	data["id"] = 1
	emit("update", data, to=origin)

@socketio.on("task-pri")
def task_pri (data):
	print(f"task priority change by {flask_socketio.flask.request.sid}")
	origin = data["origin"]
	name = data["name"]
	priority = data["priority"]
	proj = projects[origin]
	index = -1
	for i in range(len(proj)):
		if (proj[i]["name"] == name):
			index = i
			break
	if (index < 0):
		return
	proj[i]["priority"] = priority
	data["id"] = 4
	emit("update", data, to=origin)

@socketio.on("task-desc")
def task_desc (data):
	print(f"task description change by {flask_socketio.flask.request.sid}")
	origin = data["origin"]
	name = data["name"]
	desc = data["desc"]
	proj = projects[origin]
	index = -1
	for i in range(len(proj)):
		if (proj[i]["name"] == name):
			index = i
			break
	if (index < 0):
		return
	proj[i]["desc"] = desc
	data["id"] = 5
	emit("update", data, to=origin)

@socketio.on("remove-task")
def remove_task (data):
	print(f"task removal by {flask_socketio.flask.request.sid}")
	origin = data["origin"]
	name = data["name"]
	proj = projects[origin]
	found = True
	for i in range(len(proj)):
		if (proj[i]["name"] == name):
			found = False
			proj.pop(i)
			break
	if (found):
		return
	data["id"] = 2
	emit("update", data, to=origin)

@socketio.on("add-task")
def add_task (data):
	print(f"task addition by {flask_socketio.flask.request.sid}")
	origin = data["origin"]
	task = data["task"]
	proj = projects[origin]
	if (task_index(proj, task["name"]) != -1):
		return
	proj.append(task)
	data["id"] = 3
	emit("update", data, to=origin)

@socketio.on("leav-proj")
def leave_project ():
	# id = flask_socketio.flask.request.sid
	rooms = flask_socketio.rooms()
	flask_socketio.leave_room(rooms[1])

# server
socketio.run(server, host="127.0.0.1", port="3000", debug=True)