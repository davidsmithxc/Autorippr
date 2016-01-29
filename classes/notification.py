"""
Notification Class


Released under the MIT license
Copyright (c) 2014, Jason Millward

@category   misc
@version    $Id: 1.7-test4, 2015-11-09 12:30:44 ACDT $;
@author     Jason Millward
@license    http://opensource.org/licenses/MIT
"""

import os
import logger
import importlib
import pprint


class Notification(object):

    def __init__(self, config, debug, silent):
        self.config = config['notification']
        self.debug = debug
        self.silent = silent
        self.log = logger.Logger("Notification", debug, silent)

    def import_from(self, module, name, config):
        module = __import__(module, fromlist=[name])
        class_ = getattr(module, name)
        return class_(config, self.debug, self.silent)

    def _send(self, status):
        for method in self.config['methods']:
            if bool(self.config['methods'][method]['enable']):
                try:
                    method_class = self.import_from('classes.{}'.format(
                        method), method.capitalize(), self.config['methods'][method])
                    method_class.send_notification(status)
                    del method_class
                except ImportError as e:
                    print 'Traceback:', e
                    self.log.error(
                        "Error loading notification class: {}".format(method))

    def rip_complete(self, dbvideo, info=''):

        if info != '':
            info = ' '+info
            
        status = 'Rip of %s complete' % dbvideo.vidname
        status = 'Rip of {} complete{}'.format(dbvideo.vidname, info)
        self._send(status)

    def rip_fail(self, dbvideo):

        status = 'Rip of %s failed' % dbvideo.vidname
        self._send(status)

    def compress_complete(self, dbvideo, info=''):
        if info != '':
            info = ' '+info

        status = 'Compress of %s complete' % dbvideo.vidname
        status = 'Compress of {} complete{}'.format(dbvideo.vidname, info)
        self._send(status)

    def compress_fail(self, dbvideo):

        status = 'Compress of %s failed' % dbvideo.vidname
        self._send(status)

    def extra_complete(self, dbvideo, info=''):
        if info != '':
            info = ' '+info

        status = 'Extra of %s complete' % dbvideo.vidname
        status = 'Extra of {} complete{}'.format(dbvideo.vidname, info)
        self._send(status)

if __name__ == '__main__':
    import yaml

    class dbVideo():
        def __init__(self, name):
            self.vidname = name

    CONFIG_FILE = "C:/Users/David/Documents/Projects/autorippr/settings.cfg"
    config = yaml.safe_load(open(CONFIG_FILE))

    notify = Notification(config, True, False)
    notify.rip_complete(dbVideo('Predestination'))