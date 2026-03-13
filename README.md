App Information 

This app is a simple to-do list app, tracking personal tasks for users using the SQLite database and a simple command-line interface. I chose this because a to do list can very naturally be applied to CRUD operations, and as students, to-do lists are essential for completing work. My database schema involved various columns: 

Column	Type	Purpose
id	INTEGER PRIMARY KEY	unique task identifier
title	TEXT	main description
description	TEXT	optional details
status	TEXT	pending / completed /in progress
priority	INTEGER (1-5)	optional importance (5 is most urgent)
created_at	DATETIME	when task was created
due_date	DATETIME	optional deadline

How To Run

To run this app, no installations are needed as it uses Python’s built in sqlite module. Save the todo.py file and then run the command: python3 todo.py.
This launches an interactive prompt and the database todo.db is created automatically. These are the commands to use the app: 

Operation	Command	Description
Create	add <title> [options]	Adds a new task. Optional flags: -d "description", -p 1-5 for priority, --due YYYY-MM-DD for deadline.
Read	list [options]	Lists all tasks. Sort with --sort (smart/priority/due/created/status). Filter with --status or --priority. Hide done tasks with --hide-done.
Read	get <id>	Displays full details for a single task by its ID.
Update	update <id> [options]	Edits any field on an existing task. Flags: -t (title), -d (description), -s (status), -p (priority), --due (due date).
Update	complete <id>	Shortcut to mark a task as 'completed' without using the full update command.
Delete	delete <id>	Removes a task after confirming the task title in a yes/no prompt.

C: Create. The user can create a new task by using the add ___ prompt which will add the task to their personal list.
R: Read. The user can list all their current tasks by using the list command. They can sort their tasks in different ways, such as by priority number or urgency level, due date, date created, status, etc. 
U: Update. The user can update their tasks, changing either the title, description, status, priority, or due date.
D: Delete. The user can delete their task if needed, and will be asked to confirm before the data is erased. 
