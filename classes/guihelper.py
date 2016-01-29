"""
Gui Helper Functions and Classes
"""

from PyQt4 import QtCore, QtGui
import subprocess
import shlex


class ValidTvTitle(QtGui.QValidator):
    def __init__(self, parent):
        QtGui.QValidator.__init__(self, parent)

    def validate(self, s, pos):
    	containsLine = ('\n' in s) or ('\r' in s)

        if containsLine:
            return (QtGui.QValidator.Invalid, pos)

        elif containsLine is False:
        	return (QtGui.QValidator.Acceptable, pos)
            
    	else:
            return (QtGui.QValidator.Intermediate, pos)


    def fixup(self, s):
        s = s.replace('\r','')
        s = s.replace('\n','')

        return s

class GenericThread(QtCore.QThread):
    def __init__(self, function, *args, **kwargs):
        QtCore.QThread.__init__(self)
        self.function = function
        self.args = args
        self.kwargs = kwargs
     
    def __del__(self):
        self.wait()

    def run(self):
        self.function(*self.args,**self.kwargs)
        return


def streamingsubprocess(cmd, outHandle, signal):
    if type(cmd) is str:
        # exe = shlex.split(cmd)[0]
        # args = shlex.split(cmd)[1:]

        # print 'exe', exe
        # print 'args', args

        outHandle(signal, 'Starting proc w/ shell') # yield line
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            bufsize=-1
        )
        outHandle(signal, 'Proc started') # yield line
    elif type(cmd) is list:

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    else:
        raise TypeError, 'Input to subprocess must be str or list'

    outHandle(signal, 'Create iterators') # yield line
    lines_iterator = iter(proc.stdout.readline, b"")
    # err_iterator = iter(proc.stdout.readline, b"")
    
    results = ''
    errors = ''

    outHandle(signal, 'stdout') # yield line
    for line in lines_iterator:
        outHandle(signal, line.strip()) # yield line
        results += line
        print line

    # outHandle(signal, 'stderr') # yield line
    # for line in err_iterator:
    #     outHandle(signal, line.strip()) # yield line
    #     errors += line
    #     print line

    proc.communicate()
    return errors, results, proc.returncode
    # return errors, results, 0