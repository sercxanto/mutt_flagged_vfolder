#!/usr/bin/python
#
#    mutt_flagged_vfolder_jump.py
#
#    Generates mutt command file to jump to the source of a symlinked mail
#
#    Copyright (C) 2009 Georg Lutz <georg AT NOSPAM georglutz DOT de>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

import optparse
import os
import re
import sys
import types

VERSIONSTRING = "0.1"


def parseMessageId(file):
    '''Returns the message id for a given file. It is assumed that file represents a valid RFC822 message'''
    prog = re.compile("^Message-ID: (.+)", re.IGNORECASE)
    msgId = ""
    for line in file:
       # Stop after Header
	if len(line) < 2:
	    break
	result = prog.search(line)
	if type(result) != types.NoneType and len(result.groups()) == 1:
	    msgId = result.groups()[0]
	    break
    return msgId.strip("<>")


def parseMaildir(filename):
    '''Returns the maildir folder for a given file in a maildir'''
    (head,tail) = os.path.split(os.path.dirname(filename))
    return head


def writeMuttCmdFile(filename, maildir, msgId):
    '''Writes a file which can be directly sourced by mutt. The file causes
       mutt to change to the given maildir and search there for the given
       message id. Returns true on success, otherwise false.'''
    try:
	file = open(filename, "w")
    except:
	return False

    cmd = "push \"<change-folder> " + maildir + "<enter>/~i "
    # Helps if matching something like 123@[1.2.3.4]
    regex = re.escape(msgId)
    # Replace dollar sign "$" with ".+" as mutt has problems with push
    # commands and a dollar sign followed with a non numeric value e.g. like "$u".
    # This seems to reference a variable and cannot be escaped apparently.
    # Something like "$1" does not oppose problems when escaped.
    regex = regex.replace("\\$",".+")
    # According to mutt manual "4.1 Regular Expressions" backslashes must
    # be quoted for a regular expression in initialization command
    regex = regex.replace("\\","\\\\\\\\")
    # For some unknown reason "=" must not be escaped twice
    regex = regex.replace("\\\\=","=")
    cmd += regex + "<enter>\""
    file.write(cmd)
    file.close()
    return True


########### MAIN PROGRAM #############

parser = optparse.OptionParser(
	usage="%prog [options] vfolder cmdFile",
	version="%prog " + VERSIONSTRING + os.linesep +
	"Copyright (C) 2010 Georg Lutz <georg AT NOSPAM georglutz DOT de")


(options, args) = parser.parse_args()

if len(args) != 2:
    parser.print_help()
    sys.exit(2)

optVFolder = os.path.expanduser(args[0])
optCmdFile = os.path.expanduser(args[1])


if not os.path.isdir(optVFolder):
    print "Could not find given vfolder"
    sys.exit(1)

try:
    os.unlink(optCmdFile)
except:
    pass

msgId = parseMessageId(sys.stdin)
if len(msgId) > 0:
    found = False
    cmdFileWritten = False
    for entry in os.listdir(os.path.join(optVFolder, "cur")):
	entry = os.path.join(optVFolder, "cur", entry)
	if os.path.islink(entry):
	    file = None
	    try:
		file = open(entry, "r")
	    except:
		print "Could not open " + entry
	    if type(file) != types.NoneType:
		msgId2 = parseMessageId(file)
		file.close()
		if msgId == msgId2:
		    found = True
		    sourcefile = os.path.realpath(entry)
		    maildir = parseMaildir(sourcefile)
		    cmdFileWritten = writeMuttCmdFile(optCmdFile, maildir, msgId)
		    if not cmdFileWritten:
			print "Could not write to file %s" % optCmdFile
		    break

    if found and cmdFileWritten:
	sys.exit(0)
    else:
	if not found:
	    print "Could not find given email"
	# mutt waits for key press if external command returns with code != 0
        # even if wait_key is not set. This is good for us as we want to see
        # the error messages
	sys.exit(1)
else:
    sys.exit(1)
