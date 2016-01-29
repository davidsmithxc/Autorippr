"""
HandBrake CLI Wrapper


Released under the MIT license
Copyright (c) 2012, Jason Millward

@category   misc
@version    $Id: 1.7-test4, 2015-11-09 12:30:44 ACDT $;
@author     Jason Millward
@license    http://opensource.org/licenses/MIT
"""

import os
import sys
import re
import subprocess
import logger
import database
import guihelper
from PyQt4 import QtCore


class HandBrake(object):

    def __init__(self, debug, compressionpath, vformat, silent, outHandle=None):
        self.log = logger.Logger("HandBrake", debug, silent)
        self.compressionPath = compressionpath
        self.vformat = vformat
        self.os = sys.platform
        self.outHandle = outHandle
        self.display = lambda x: self.outHandle(QtCore.SIGNAL('shell_line(PyQt_PyObject)'), x)
        # ToDo fix argument passing for Handbrake; requires .cmd file
        self.tmpFolder = 'C:\\Users\\David\\Documents\\Projects\\autorippr\\tmp'
        print 'init HB with comp path', compressionpath

    def compress(self, nice, args, dbvideo, outHandle=None, threaded=False):
        """
            Passes the necessary parameters to HandBrake to start an encoding
            Assigns a nice value to allow give normal system tasks priority

            Inputs:
                nice    (Int): Priority to assign to task (nice value)
                args    (Str): All of the handbrake arguments taken from the
                                settings file
                output  (Str): File to log to. Used to see if the job completed
                                successfully

            Outputs:
                Bool    Was convertion successful
        """
        if outHandle is not None:
            print 'set out handle'
            self.outHandle = outHandle

        checks = 0

        # Check if TV show is already named
        c = re.compile('-[ ]{0,1}[0-9]{0,1}x[0-999][ ]{0,1}-')
        m = c.findall(dbvideo.vidname)

        if (dbvideo.vidtype == "tv") and m is None:
            # Query the SQLite database for similar titles (TV Shows)
            vidname = re.sub(r'D(\d)', '', dbvideo.vidname)
            vidqty = database.search_video_name(vidname)
            if vidqty == 0:
                vidname = "%sE1.%s" % (vidname, self.vformat)
            else:
                vidname = "%sE%s.%s" % (vidname, str(vidqty + 1), self.vformat)
        else:
            # ToDo: Add regex search for Rental or Rental NA at END of str
            vidname = "%s.%s" % (dbvideo.vidname, self.vformat)

        invid = "%s/%s" % (dbvideo.path, dbvideo.filename)
        outvid = "%s/%s" % (dbvideo.path, vidname)

        if self.os == 'win32':
            cmd = '{0}HandBrakeCLI.exe --verbose -i "{1}" -o "{2}" {3}'.format(
                self.compressionPath,
                invid,
                outvid,
                ' '.join(args)
            )
            
            with open(self.tmpFolder+'\\tmp.cmd', 'wb+') as f:
                f.write(cmd)

            # cmd = [self.tmpFolder+'\\tmp.cmd']

        elif self.os == 'Unix':
            cmd = 'nice -n {0} {1}HandBrakeCLI --verbose -i "{2}" -o "{3}" {4}'.format(
                nice,
                self.compressionPath,
                invid,
                outvid,
                ' '.join(args)
            )

        if threaded is True:
            print 'calling threaded subprocess'
            print cmd
            self.display('Testing Handbrake outHandle')
            (errors, results, returncode) = guihelper.streamingsubprocess(cmd, self.outHandle, QtCore.SIGNAL('shell_line(PyQt_PyObject)'))
        else:
            proc = subprocess.Popen(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                shell=True
            )
            
            (errors, results) = proc.communicate()
            returncode = proc.returncode
        
        self.display('{} done w/ return code {}'.format(vidname, returncode))
        if returncode is not 0:
            self.log.error(
                "HandBrakeCLI (compress) returned status code: %d" % returncode)

        if results is not None and len(results) is not 0:
            lines = results.split("\n")
            for line in lines:
                if "Encoding: task" not in line:
                    self.log.debug(line.strip())

                if "average encoding speed for job" in line:
                    checks += 1
                    self.display('Avg speed check')

                if "Encode done!" in line:
                    checks += 1
                    self.display('Encode done! check')

                if "ERROR" in line and "opening" not in line:
                    self.log.error(
                        "HandBrakeCLI encountered the following error: ")
                    self.log.error(line)
                    self.display('Handbrake error detected')

                    return False

        if checks >= 2:
            self.log.debug("HandBrakeCLI Completed successfully")
            self.display('{} info: {}'.format(vidname, 'Success!'))

            database.update_video(
                dbvideo, 6, filename="%s" % (
                    vidname
                ))

            return True
        else:
            self.display('{} info: {}'.format(vidname, 'Some error!'))
            return False
