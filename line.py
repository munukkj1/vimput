import subprocess
import re
import sys


delay = '50'
turbo = '50'
cursor_x = 1
cursor_y = 1
lines = []

def do_horizontal_cursor_navigation(target_x):
	global delay, turbo, cursor_x, cursor_y, lines
	while cursor_x < target_x:
			print('normal l')
			print('redraw')
			print('sleep '+delay+'m')
			cursor_x += 1
	while cursor_x > target_x:
			print('normal h')
			print('redraw')
			print('sleep '+delay+'m')
			cursor_x -= 1


def do_vertical_cursor_navigation(target_y):
	global delay, turbo, cursor_x, cursor_y, lines
	while cursor_y < target_y:
		print('normal j')
		print('redraw')
		print('sleep '+delay+'m')
		cursor_y += 1
	while cursor_y > target_y:
		print('normal k')
		print('redraw')
		print('sleep '+delay+'m')
		cursor_y -= 1


def pause():
	global delay, turbo, cursor_x, cursor_y, lines
	print('sleep 500m')
	


def type_line(line):
	"""
	Produce character sequence to type the given line on a new empty line in the editor.
	The new line should be created beforehand by e.g. the 'o' or 'O' commands.
	The same goes for after.
	"""
	global delay, turbo, cursor_x, cursor_y, lines
	assert cursor_x == 1
	print("type line: typing line ", line, file=sys.stderr)

	for c in line:
		print('normal a'+c)
		print('redraw')
		print('sleep '+delay+'m')
		cursor_x += 1

	# The last escape moves the cursor back
	cursor_x -= 1



def edit_line(oldline, newline):
	""" 29.5.24 Switch to use diff normal format.  The commands are as follows:

	<l>a<m>,<n>

	Go to line l in file1 (the editor). Add the following lines in
	range <m>,<n> of the second file. The range can be ignored though as the
	added lines are printed out as well.

	<k>,<l>c<m>,<n>
	
	Change lines in range <k>,<l> in file1 (the editor) to
	lines in range <m>,<n> of the second file. The range can be ingored as
	before. However we get a list of "old lines" and "new lines". If l-k < n-m
	i.e. there are less lines than there was before, just delete the remaining
	ones. But again we can just pop until the end of the command is reached and
	not bother with the second range.

	<k>,<l>d<m>

	Delete lines in range <k>,<l>. <m> is just a number and can be
	ignored. It tells where the lines were would have been in the second file
	
	Hunks:

	>	denotes lines (added) in the second file
	<	denotes lines removed from file1 and not present in file2
	---	between the hunks can be ignored.

	"""
	global delay, turbo, cursor_x, cursor_y, lines
	print("Changing line ", oldline, " to ", newline, file=sys.stderr)
	oldline = oldline.replace("\"","\\\"")
	newline = newline.replace("\"","\\\"")
	command = subprocess.run('echo \"'+oldline+'\" | sed \"s/./\\0\\n/g\" > tmp1', shell=True)
	command = subprocess.run('echo \"'+newline+'\" | sed \"s/./\\0\\n/g\" > tmp2', shell=True)
	command = subprocess.run('diff -d tmp1 tmp2', shell=True, capture_output=True)
	diffstr = command.stdout.decode('utf-8').split('\n')
	print(diffstr, file=sys.stderr)





	while not not diffstr:
		token = diffstr.pop(0)
		
		if   re.match("[0-9]*,[0-9]*[acd][0-9]*,[0-9]*", token):
			k,l,m,n = [int(p) for p in re.split("a|c|d|,",token)]
		elif re.match(       "[0-9]*[acd][0-9]*,[0-9]*", token):
			l,m,n	= [int(p) for p in re.split("a|c|d|,",token)]
			k = l
		elif re.match("[0-9]*,[0-9]*[acd][0-9]*"       , token):
			k,l,m   = [int(p) for p in re.split("a|c|d|,",token)]
			n = m
		elif re.match(       "[0-9]*[acd][0-9]*"       , token):
			l,m     = [int(p) for p in re.split("a|c|d|,",token)]
			n = m
			k = l
		else:
			print("Invalid diff command ", token, file=sys.stderr)

		append_command = 'a' in token
		change_command = 'c' in token
		delete_command = 'd' in token
		
		# Append command, add characters after column target_x
		old_lines = []
		new_lines = []
		if append_command:
			print("edit_line: matched append command ", token, file=sys.stderr)
			
			while m <= n: # The range in the append command gives the number of new lines to expect.
				# the [2:] removes < and > in diff output
				new_lines.append(diffstr.pop(0)[2:])
				m += 1
			
			print(old_lines, file=sys.stderr)
			print(new_lines, file=sys.stderr)

			
			target_x = l
			do_horizontal_cursor_navigation(target_x)
			while not not new_lines:
				c = new_lines.pop(0)
				print('normal a'+c)
				print('redraw')
				print('sleep '+delay+'m')
				cursor_x += 1
		# Change command, replace a characters from begin and then delete until end if range is larger than given characters.
		if change_command:
			print("edit_line: matched change command ", token, file=sys.stderr)
			
			while diffstr[0] != '---':
				old_lines.append(diffstr.pop(0)[2:])

			diffstr.pop(0)
			while m <= n:
				new_lines.append(diffstr.pop(0)[2:])
				m += 1

			print(old_lines, file=sys.stderr)
			print(new_lines, file=sys.stderr)
			
			begin = k
			end = l
			
			

			do_horizontal_cursor_navigation(begin)

			print('cursor at ', cursor_x, file=sys.stderr)
			print('hello stdout')
			print('hello stderr', file=sys.stderr)

			print('\n'.join(old_lines), file=sys.stderr, flush=true)
			print('\n'.join(new_lines), file=sys.stderr, flush=true)
			

			while not not new_lines:
				old = old_lines.pop(0)
				new = new_lines.pop(0)
				if begin > end:
					print('normal i'+new)
					print('redraw')
					print('sleep '+delay+'m')
					
					print('normal l')
					print('redraw')
					print('sleep '+delay+'m')
				else:
					print('normal R'+new)
					print('redraw')
					print('sleep '+delay+'m')
					
					print('normal l')
					print('redraw')
					print('sleep '+delay+'m')

				cursor_x += 1
				begin += 1
			
			# It's a good idea to replace the text from the beginning, but consider also the alternative
			# of deleting text first from the back if possible.
			# Consider the possibility of changing the change command into append and delete commands and add them to the stack.
			#while begin <= end:
			while not not old_lines:
				print('normal x')
				print('redraw')
				print('sleep '+delay+'m')
				begin += 1

			
		if delete_command:
			print("edit_line: matched delete command ", token, file=sys.stderr)
			
			begin = k
			end = l
			
			# Decide whether use backspace or delete (go forward or backward)
			if cursor_x <= begin:
				do_horizontal_cursor_navigation(begin)
				
				while begin < end:
					print('normal x')
					print('redraw')
					print('sleep '+delay+'m')
					begin += 1
					diffstr.pop(0)
			else:
				do_horizontal_cursor_navigation(end)
				
				while begin < end:
					print('normal x')
					print('normal h')
					print('redraw')
					print('sleep '+delay+'m')
					end -= 1
					cursor_x -= 1 
					diffstr.pop(0)

				print('normal x')
				print('redraw')
				print('sleep '+delay+'m')
			


	# This function only deals with one line.
	lines[cursor_y-1] = newline



def edit_file(f1, f2):
	global delay, turbo, cursor_x, cursor_y, lines
	command = subprocess.run('diff -d '+f1+' '+f2, shell=True, capture_output=True)
	diffstr = command.stdout.decode('utf-8').split('\n')
	print(diffstr, file=sys.stderr)
	while not not diffstr:
		token = diffstr.pop(0)
		
		if   re.match("[0-9]*,[0-9]*[acd][0-9]*,[0-9]*", token):
			k,l,m,n = [int(p) for p in re.split("a|c|d|,",token)]
		elif re.match(       "[0-9]*[acd][0-9]*,[0-9]*", token):
			l,m,n	= [int(p) for p in re.split("a|c|d|,",token)]
			k = l
		elif re.match("[0-9]*,[0-9]*[acd][0-9]*"       , token):
			k,l,m   = [int(p) for p in re.split("a|c|d|,",token)]
			n = m
		elif re.match(       "[0-9]*[acd][0-9]*"       , token):
			l,m     = [int(p) for p in re.split("a|c|d|,",token)]
			n = m
			k = l
		else:
			print("Invalid diff command ", token, file=sys.stderr)

		append_command = 'a' in token
		change_command = 'c' in token
		delete_command = 'd' in token

		print("append_command", append_command, "change_command", change_command, "delete_command", delete_command, file=sys.stderr)


		print("", token, file=sys.stderr)
		
		# Append command, add characters after column target_x
		old_lines = []
		new_lines = []
		if append_command:
			print("edit_line: matched append command ", token, file=sys.stderr)
			
			while m <= n: # The range in the append command gives the number of new lines to expect. The [2:] removes < and > in diff output
				new_lines.append(diffstr.pop(0)[2:])
				m += 1

			print(old_lines, file=sys.stderr)
			print(new_lines, file=sys.stderr)
			
			target_y = l
			do_vertical_cursor_navigation(target_y)

			while not not new_lines:
				new = new_lines.pop(0)
				print('normal o')
				print('redraw')
				print('sleep '+delay+'m')
				cursor_y += 1
				cursor_x  = 1
				type_line(new)
				
				# insert into middle of array
				# print(cursor_y, file=sys.stderr)
				lines = lines[:cursor_y-1] + [new] + lines[cursor_y-1:]

		# Change command, replace a characters from begin and then delete until end if range is larger than given characters.
		if change_command:
			print("edit_file: change command ", token, file=sys.stderr)
			
			while diffstr[0] != '---':
				old_lines.append(diffstr.pop(0)[2:])

			diffstr.pop(0)
			while m <= n:
				new_lines.append(diffstr.pop(0)[2:])
				m += 1

			print(old_lines, file=sys.stderr)
			print(new_lines, file=sys.stderr)
			
			begin = k
			end = l
			
			

			do_vertical_cursor_navigation(begin)
			

			while not not new_lines:
				old = old_lines.pop(0)
				new = new_lines.pop(0)
				if begin > end:
					print('Appending ', new, ' after line ', cursor_y, file=sys.stderr)
					
					print('normal o')
					print('redraw')
					print('sleep '+delay+'m')
				
					cursor_y += 1
					cursor_x  = 1
					
					type_line(new)
					# insert into middle of array
					lines = lines[:cursor_y-1] + [new] + lines[cursor_y-1:]
					
				else:
					#old = lines[cursor_y-1]
					print('Replacing line ', old, ' at ', cursor_y, ' with ', new, file=sys.stderr)
					edit_line(old, new)
					
					# Change line if the next line is a replacement i.e. the end has not been reached.
					if begin <= end:
						print('normal j')
						print('redraw')
						print('sleep '+delay+'m')
					
						cursor_y += 1
						# Reset cursor x
						unsure = True
						if unsure:
							print('normal 0')
							print('redraw')
							print('sleep '+delay+'m')
							cursor_x = 1
						else:
							# adjust cursor x if next line is shorter
							cursor_x = min(cursor_x, len(lines[cursor_y-1]))


				
				begin += 1
			
			# It's a good idea to replace the text from the beginning, but consider also the alternative
			# of deleting text first from the back if possible.
			# Consider the possibility of changing the change command into
			# append and delete commands and add them to the stack.
			
			# If there are lines left in the range delete them. The begin <= end
			# condition was met earlier so we are already on the line that
			# needs to be deleted.
			#while begin <= end:
			while not not old_lines:
				print('normal dd')
				print('redraw')
				print('sleep '+delay+'m')
				
				lines.pop(cursor_y)
				
				begin += 1

			
		if delete_command:
			print("edit_line: matched delete command ", token, file=sys.stderr)
			
			begin = k
			end = l
			
			# Decide whether use backspace or delete (go forward or backward)
			if cursor_y <= begin:
				do_vertical_cursor_navigation(begin)
				
				print('matched delete command, moving cursor to ', cursor_y, file=sys.stderr)
				
				while begin < end:
					print('normal dd')
					print('redraw')
					print('sleep '+delay+'m')
					lines.pop(cursor_y)
					diffstr.pop(0)
					begin += 1
			else:
				do_vertical_cursor_navigation(end)
				
				print('matched delete command, moving cursor to ', cursor_y, file=sys.stderr)
				
				while begin < end:
					print('normal dd')
					print('redraw')
					print('sleep '+delay+'m')

					lines.pop(cursor_y)

					print('normal k')
					print('redraw')
					print('sleep '+delay+'m')
					end -= 1
					cursor_y -= 1 
					diffstr.pop(0)

				print('normal dd')
				print('redraw')
				print('sleep '+delay+'m')
				lines.pop(cursor_y)



versions = ["empty.txt",
			"version1.cc",
			"version2.cc",
			"version3.cc",
			"version4.cc",
			"version4.cc",
			"version5.cc",
			"version6.cc",
			"version7.cc",
			"version8.cc",
			"version9.cc",
			"version10.cc"]


# Load the first version into memory.
fp = open(versions[0], "r")
lines = fp.read().split('\n')
fp.close()

print('\n'.join(lines), file=sys.stderr)

"""
This is the main program and entry point. The program goes through all versions of the text
and finds a natural sequence of edits between the versions. The versions serve as guides for
which order to input the lines and when to edit lines. The comparing is done by the diff program
for the most part.
"""
for f1,f2 in zip(versions[:-1], versions[1:]):
	edit_file(f1,f2)
	pause()

exit

"""
oldline = "for(unsigned k = 0; k < m; ++k)"
newline = "for(unsigned j = 0; j < m; ++j)"

cursor_x = type_line(oldline, cursor_x)

print('typed line, cursor at ', cursor_x, file=sys.stderr)
pause()

cursor_x = edit_line(oldline, newline, cursor_x, cursor_y)
pause()

print('normal o')
print('redraw')
print('sleep '+delay+'m')

"""
"""

oldline = "i broke my back"
newline = "my back is broken"
newline2 = "spinal"
newline3 = "medical"


type_line(oldline)
pause()

print('typed line, cursor at ', cursor_x, file=sys.stderr)

edit_line(oldline, newline)
pause()

print('changed line, cursor at ', cursor_x, file=sys.stderr)

edit_line(newline, newline2)
pause()

print('changed line, cursor at ', cursor_x, file=sys.stderr)

# edit_line(newline2, newline3)


print('normal o')
print('redraw')
print('sleep '+delay+'m')

cursor_x = 1

oldline = "makkara maantien poikki loikki"
newline = "makkara loikki maantien poikki"


type_line(oldline)
pause()

print('typed line, cursor at ', cursor_x, file=sys.stderr)

edit_line(oldline, newline)
pause()
"""
