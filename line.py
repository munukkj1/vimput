import subprocess
import re
import sys
import random


RANDOM = False
TURBO  = False
SLOW	 = True
verbosity = 5
indent_level = 0
cursor_x = 1
cursor_y = 1
lines = []
buffer = []

def indent():
	global indent_level
	indent_level += 1

def unindent():
	global indent_level
	indent_level -= 1

def report(*args):
	"""
	"""
	global verbosity, SCRIPT_DEBUG, indent_level
	s = "".join(str(args))
	print(("\t"*indent_level)+s, file=sys.stderr, flush=True)
	if verbosity > 7:
		print("\""+s)


def substr(a,b,min_ss_len = 3):
	"""
		Find substring
		returns: the column where the substring starts and the length of the substring.
	"""
	if verbosity > 8:
		report("substr: comparing "+a+" and "+b)
	min_ss_len -= 1
	max_ss_len = min(len(a),len(b))
	best = ""
	# starting column and length
	# indexing into the second string
	# (the line that has already been typed)
	best_col = -10000;
	best_len = -10000;
	for w in range(min_ss_len, max_ss_len):
		for start_a in range(len(a)-w):
			for start_b in range(len(b)-w):
				v = w + 1
				end_a = start_a + v
				end_b = start_b + v
				sub_a = a[start_a:end_a]
				sub_b = b[start_b:end_b]

				if verbosity > 8:
					indent()
					report("substr: comparing "+sub_a+" and "+sub_b)
					unindent()
				
				if sub_a == sub_b:
					if v > best_len:
						best_col = start_b
						best_len = v

	return best_col, best_len
				


def delay():
	"""
	Add delay to vimscript based on global variables.
	Random: normally distributed values for the delay.
	Turbo: if set type at turbo speed.
	"""
	if RANDOM:
		if TURBO:
			mean = 10
			std = 0
		else:
			mean = 40
			std = 10
		amount = round(random.gauss(mean,std))
	else:
		if TURBO:
			amount = 10
		elif SLOW:
			amount = 100
		else:
			amount = 40

	print('sleep' + str(amount) + 'm')

def redraw():
	"""
	Force vim to redraw the screen.
	"""
	print('redraw')

def pause(amount=500):
	"""
	Insert a pause in the vimscript
	"""
	print('sleep %dm' % amount)

def editor():
	"""
	Print the contents of the editor.
	"""
	global lines, verbosity
	if verbosity > 2:
		print('\n'.join(lines), file=sys.stderr, flush=True)
	
	
def scan_nearby_whole_lines(new):
	"""
	See if any nearby lines match 'new'.
	Return line number or -1 if no match.
	Test the line itself too.
	TODO generate the range automatically e.g. sort with abs key
	TODO penalty
	"""
	global cursor_x, cursor_y, lines, verbosity
	best_linenum = -1
	# look for pm 3 lines 
	for dy in [0, 1, -1, 2, -2, 3, -3]:
		linenum = cursor_y + dy
		
		# Skip invalid lines
		if linenum <= 0 or linenum > len(lines):
			continue
		
		if lines[linenum-1] == new:
			best_linenum = linenum

	return best_linenum

def scan_nearby_lines(new, min_ss_len = 3):
	"""
	See if any nearby lines contain substring.
	Right now
	TODO generate the range automatically e.g. sort with abs key
	TODO penalty
	new: the new line
	"""
	global cursor_x, cursor_y, lines, verbosity
	# Initialize optimisation variables.
	best_linenum = -1
	best_col = -1
	best_len = -1
	length = -1
	# look for pm 3 lines but not the line itself (TODO implement this.)
	for dy in [1, -1, 2, -2, 3, -3]:
		linenum = cursor_y + dy
		
		# Skip invalid lines
		if linenum <= 0 or linenum > len(lines):
			continue

		col, length = substr(new, lines[linenum-1], min_ss_len)

		if length > min_ss_len and length > best_len:
			best_col = col
			best_len = length
			best_linenum = linenum
		
	return best_linenum, best_col, best_len

def copy_line(linenum, replace=False):
	"""
	Copy the line on linenum and paste it after the current line. Reset cursor.
	"""
	global cursor_x, cursor_y, lines, verbosity
	current_line = cursor_y
	if verbosity > 2:
		report("copy_line: copying line ", linenum, " to ", current_line)
	
	do_vertical_cursor_navigation(linenum)
	print('normal V')
	delay()
	print('redraw')

	print('normal y')
	delay()
	print('redraw')
	
	do_vertical_cursor_navigation(current_line)

	if replace: # Replace the whole line: select and then paste
		print('normal V')
		delay()
		print('redraw')
		print('normal p')
		cursor_y += 1
		delay()
		print('redraw')
	else:
		# Normally paste after the current line. TODO paste after.
		print('normal p')
		cursor_y += 1
		delay()
		print('redraw')
	
	
	print('normal 0')
	cursor_x  = 1

def paste_after():
	"""
	Put text in buffer after the cursor.
	"""
	global cursor_x, cursor_y, lines, verbosity, buffer
	print('normal p')
	cursor_y += 1
	delay()
	print('redraw')
	lines = lines[:cursor_y-1] + buffer + lines[cursor_y:]

def paste_before():
	"""
	Put text in buffer before the cursor.
	"""
	global cursor_x, cursor_y, lines, verbosity, buffer
	print('normal P')
	delay()
	print('redraw')
	lines = lines[:cursor_y-2] + buffer + lines[cursor_y-1:]

def select_lines(start, end):
	"""
	Select lines from start to end.
	"""
	global cursor_x, cursor_y, lines, verbosity
	do_vertical_cursor_navigation(start)
	print("normal V")
	delay()
	redraw()
	do_vertical_cursor_navigation(end)

def copy_lines(start, end):
	"""
	Select lines from start to end and yank them.
	"""
	global cursor_x, cursor_y, lines, verbosity, buffer

	current_line = cursor_y

	if verbosity > 2:
		report("copy_lines: copying lines in range ", start, " to ", end)

	select_lines(start, end)
	print('normal y')
	buffer = lines[start:end]
	delay()
	redraw()
	do_vertical_cursor_navigation(current_line)

def delete_lines(start, end):
	"""
	Select lines from start to end and delete them.
	"""
	global cursor_x, cursor_y, lines, verbosity, buffer
	current_line = cursor_y
	if verbosity > 2:
		report("delete_lines: deleting lines in range ", start, " to ", end)
	select_lines(start, end)
	print('normal d')
	buffer = lines[start:end]
	lines = lines[:start] + lines[end:]
	delay()
	redraw()
	do_vertical_cursor_navigation(current_line)

def select_chars(start, end):
	"""
	Select chars from start to end on the current line.
	"""
	do_horizontal_cursor_navigation(start)
	print("normal v")
	delay()
	redraw()
	do_horizontal_cursor_navigation(end)

def copy_chars(start, end):
	"""
	Select chars from start to end on the current line and yank them.
	"""
	global cursor_x, cursor_y, lines, verbosity
	
	current_line = cursor_y
	
	if verbosity > 2:
		report("copy_chars: copying characters in range ", start, " to ", end, " on the current line.")
	
	select_chars(start, end)
	print('normal y')
	delay()
	redraw()

def delete_chars(start, end):
	"""
	Select chars from start to end on the current line and delete them.
	"""
	global cursor_x, cursor_y, lines, verbosity
	
	current_x = cursor_x
	
	if verbosity > 2:
		report("delete_chars: deleting characters in range ", start, " to ", end, " on the current line.")

	select_chars(start, end)
	print('normal d')
	delay()
	redraw()
	do_horizontal_cursor_navigation(current_x)



def do_horizontal_cursor_navigation(target_x):
	global delay, turbo, cursor_x, cursor_y, lines, verbosity
	if verbosity > 3:
		report("do_horizontal_cursor_navigation: moving cursor from x = ", cursor_x, " to x = ", target_x)
	while cursor_x < target_x:
		print('normal l')
		print('redraw')
		delay()
		cursor_x += 1
	while cursor_x > target_x:
		print('normal h')
		print('redraw')
		delay()
		cursor_x -= 1


def do_vertical_cursor_navigation(target_y):
	global delay, turbo, cursor_x, cursor_y, lines, verbosity
	original_x = cursor_x

	if verbosity > 3:
		report("do_vertical_cursor_navigation: moving cursor from y = ", cursor_y, " to y = ", target_y)
	
	while cursor_y < target_y:
		print('normal j')
		print('redraw')
		delay()
		cursor_y += 1
		cursor_x = min(original_x, len(lines[cursor_y-1]))
	while cursor_y > target_y:
		print('normal k')
		print('redraw')
		delay()
		cursor_y -= 1
		cursor_x = min(original_x, len(lines[cursor_y-1]))

	if verbosity > 3:
		report("do_vertical_cursor_navigation: leaving cursor x = ", cursor_x)
	


def type_text(text):
	"""
	Produce character sequence to type the given line on a new empty line in the editor.
	The new line should be created beforehand by e.g. the 'o' or 'O' commands.
	The same goes for after.
	"""
	global delay, turbo, cursor_x, cursor_y, lines, verbosity

	if verbosity > 2:
		report("type_text: typing text", text, " cursor_x = ", cursor_x, " cursor_y = ", cursor_y)

	for c in text:
		print('normal a'+c)
		print('redraw')
		delay()
		cursor_x += 1

	# The last escape moves the cursor back
	cursor_x -= 1

def type_line(line):
	"""
	Produce character sequence to type the given line on a new empty line in the editor.
	The new line should be created beforehand by e.g. the 'o' or 'O' commands.
	The same goes for after.
	"""
	global delay, turbo, cursor_x, cursor_y, lines, verbosity
	print('normal o')
	print('redraw')
	delay()
	cursor_y += 1
	cursor_x  = 1

	if verbosity > 2:
		report("type line: typing line ", line, " cursor_y = ", cursor_y)

	type_text(line)

	lines = lines[:cursor_y-1] + [line] + lines[cursor_y-1:]



def edit_line(oldline, newline):
	""" 29.5.24 Switch to use diff normal format.  The commands are as follows:

	<l>a<m>,<n>

	Go to line l in file1 (the editor). Add the following lines in
	range <m>,<n> of the second file. The range can be ignored though as the
	added lines are printed out as well.

	<k>,<l>c<m>,<n>
	
	Change lines in range <k>,<l> in file1 (the editor) to
	lines in range <m>,<n> of the second file. The latter range can be ingored as
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
	global delay, turbo, cursor_x, cursor_y, lines, verbosity
	oldline = oldline.replace("\"","\\\"")
	newline = newline.replace("\"","\\\"")
	command = subprocess.run('echo \"'+oldline+'\" | sed \"s/./\\0\\n/g\" > tmp1', shell=True)
	command = subprocess.run('echo \"'+newline+'\" | sed \"s/./\\0\\n/g\" > tmp2', shell=True)
	command = subprocess.run('diff -d tmp1 tmp2', shell=True, capture_output=True)
	diffstr = command.stdout.decode('utf-8').split('\n')

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
			pass

		append_command = 'a' in token
		change_command = 'c' in token
		delete_command = 'd' in token
		
		# Append command, add characters after column target_x
		old_lines = []
		new_lines = []
		if append_command:
			if verbosity > 2:
				report("edit_line: matched append command ", token)
			
			while m <= n: # The range in the append command gives the number of new lines to expect.
				# the [2:] removes < and > in diff output
				new_lines.append(diffstr.pop(0)[2:])
				m += 1
			
			target_x = l
			do_horizontal_cursor_navigation(target_x)
			
			substring = "".join(new_lines)
			line, col, length = scan_nearby_lines(substring)

			if line > 0 and col > 0 and length > 0:
				report("Potentially copy "+substring+"from nearby line.")
			
			type_text(substring)
			"""
			while not not new_lines:
				c = new_lines.pop(0)
				print('normal a'+c)
				print('redraw')
				delay()
				cursor_x += 1
			"""

		# Change command, replace a characters from begin and then delete until end if range is larger than given characters.
		if change_command:
			if verbosity > 2:
				report("edit_line: matched change command ", token)
			
			while diffstr[0] != '---':
				old_lines.append(diffstr.pop(0)[2:])

			diffstr.pop(0)
			while m <= n:
				new_lines.append(diffstr.pop(0)[2:])
				m += 1

			
			begin = k
			end = l
			
			do_horizontal_cursor_navigation(begin)
			
			substring = "".join(new_lines)
			line, col, length = scan_nearby_lines(substring)

			if line > 0 and col > 0 and length > 0:
				report("Potentially copy "+substring+"from nearby line.")

			while not not new_lines:
				new = new_lines.pop(0)
				if begin > end:
					print('normal i'+new)
					print('redraw')
					delay()
					
					print('normal l')
					print('redraw')
					delay()
				else:
					old = old_lines.pop(0)
					print('normal R'+new)
					print('redraw')
					delay()
					
					print('normal l')
					print('redraw')
					delay()

				cursor_x += 1
				begin += 1
			
			# It's a good idea to replace the text from the beginning, but consider also the alternative
			# of deleting text first from the back if possible.
			# Consider the possibility of changing the change command into append and delete commands and add them to the stack.
			#while begin <= end:
			delete_chars(begin,end)
			"""
			while not not old_lines:
				print('normal x')
				print('redraw')
				delay()
				old_lines.pop(0)
				#begin += 1
			"""

			
		if delete_command:
			if verbosity > 2:
				report("edit_line: matched delete command ", token)
			
			begin = k
			end = l
			
			delete_chars(begin,end)
			"""
			# Decide whether use backspace or delete (go forward or backward)
			if cursor_x <= begin:
				do_horizontal_cursor_navigation(begin)
				
				while begin < end:
					print('normal x')
					print('redraw')
					delay()
					begin += 1
					diffstr.pop(0)
			else:
				do_horizontal_cursor_navigation(end)
				
				while begin < end:
					print('normal x')
					print('normal h')
					print('redraw')
					delay()
					end -= 1
					cursor_x -= 1 
					diffstr.pop(0)

				print('normal x')
				print('redraw')
				delay()
				"""
			


	# This function only deals with one line.
	lines[cursor_y-1] = newline



def edit_file(f1, f2):
	global delay, turbo, cursor_x, cursor_y, lines
	command = subprocess.run('diff -d '+f1+' '+f2, shell=True, capture_output=True)
	diffstr = command.stdout.decode('utf-8').split('\n')
	report('\n'.join(diffstr))
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
			pass

		append_command = 'a' in token
		change_command = 'c' in token
		delete_command = 'd' in token

		# Append command, add characters after column target_x
		old_lines = []
		new_lines = []
		if append_command:
			if verbosity > 2:
				report("edit_file: matched append command ", token)
			
			while m <= n: # The range in the append command gives the number of new lines to expect. The [2:] removes < and > in diff output
				new_lines.append(diffstr.pop(0)[2:])
				m += 1

			target_y = l
			do_vertical_cursor_navigation(target_y)

			while not not new_lines:
				new = new_lines.pop(0)

				# See if the whole line can be copied.
				# The idea here is that you type the same line multiple times
				# in the version files. The edit line function will do the rest.


				linenum = scan_nearby_whole_lines(new)
				line_copied = linenum == -1

				if line_copied:
					type_line(new)
				else:
					copy_lines(linenum, linenum)
					paste_after()
				
				report("cursor_y = ",cursor_y)
				lines = lines[:cursor_y-1] + [new] + lines[cursor_y-1:]

		# Change command, replace a characters from begin and then delete until end if range is larger than given characters.
		if change_command:
			if verbosity > 2:
				report("edit_file: change command ", token)
			
			while diffstr[0] != '---':
				old_lines.append(diffstr.pop(0)[2:])

			diffstr.pop(0)
			while m <= n:
				new_lines.append(diffstr.pop(0)[2:])
				m += 1

			begin = k
			end = l
			
			do_vertical_cursor_navigation(begin)
			
			#print("Old_lines\n"+"\n".join(old_lines), "\nNew_lines\n"+"\n".join(new_lines), file=sys.stderr)	
			while not not new_lines:
				new = new_lines.pop(0)
				if begin <= end:
					old = old_lines.pop(0)
					edit_line(old, new)
					
					# Change line if the next line is a replacement i.e. the end has not been reached.
					if begin < end:
						print('normal j')
						print('redraw')
						delay()
						
						cursor_y += 1
						
						# adjust cursor x if next line is shorter
						cursor_x = min(cursor_x, len(lines[cursor_y-1]))
				else:
					linenum = scan_nearby_whole_lines(new)
					not_copyable = linenum == -1

					# Copy and paste line after
					# or type line after.
					if not_copyable:
						type_line(new)
					else:
						copy_lines(linenum, linenum)
						paste_after()
					
					if verbosity > 5:
						report("cursor_y = ",cursor_y)
					
					lines = lines[:cursor_y-1] + [new] + lines[cursor_y-1:]
				
				begin += 1
			

				
			# It's a good idea to replace the text from the beginning, but consider also the alternative
			# of deleting text first from the back if possible.
			# Consider the possibility of changing the change command into
			# append and delete commands and add them to the stack.
			
			# If there are lines left in the range delete them. The begin <= end
			# condition was met earlier so we are already on the line that
			# needs to be deleted.
			#while begin <= end:
			if begin <= end:
				delete_lines(begin, end)

			"""
			while not not old_lines:
				print('normal dd')
				print('redraw')
				delay()

				old_lines.pop()
				
				begin += 1
			"""
				
		if delete_command:
			if verbosity > 2:
				report("edit_file: matched delete command ", token)
			
			begin = k
			end = l

			#delete_chars(begin, end)
			delete_lines(begin, end)
			"""
			# Decide whether use backspace or delete (go forward or backward)
			if cursor_y <= begin:
				do_vertical_cursor_navigation(begin)
				
				while begin < end:
					print('normal dd')
					print('redraw')
					delay()
					lines.pop(cursor_y-1)
					diffstr.pop(0)
					begin += 1
			else:
				do_vertical_cursor_navigation(end)
				
				while begin < end:
					print('normal dd')
					print('redraw')
					delay()

					lines.pop(cursor_y-1)

					print('normal k')
					print('redraw')
					delay()
					end -= 1
					cursor_y -= 1 
					diffstr.pop(0)

				print('normal dd')
				print('redraw')
				delay()
				lines.pop(cursor_y-1)
			"""



versions = ["empty.txt",
			"version0.cc",
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

editor()

"""
This is the main program and entry point. The program goes through all versions of the text
and finds a natural sequence of edits between the versions. The versions serve as guides for
which order to input the lines and when to edit lines. The comparing is done by the diff program
for the most part.
"""
for f1,f2 in zip(versions[:-1], versions[1:]):
	edit_file(f1,f2)
	pause()


"""
pääskynen muutti etelään
vaari sitä jäi ikävöimään
räystäällä näkyy lunta
vaari pääskystä näki unta
kevät koitti
pääskynen tutun laulun soitti
vaaria vain nauratti
"""



exit
