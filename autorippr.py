"""
Autorippr

Ripping
    Uses MakeMKV to watch for videos inserted into DVD/BD Drives

    Automaticly checks for existing directory/video and will NOT overwrite existing
    files or folders

    Checks minimum length of video to ensure video is ripped not previews or other
    junk that happens to be on the DVD

    DVD goes in > MakeMKV gets a proper DVD name > MakeMKV Rips

Compressing
    An optional additional used to rename and compress videos to an acceptable standard
    which still delivers quality audio and video but reduces the file size
    dramatically.

    Using a nice value of 15 by default, it runs HandBrake (or FFmpeg) as a background task
    that allows other critical tasks to complete first.

Extras


Released under the MIT license
Copyright (c) 2014, Jason Millward

@category   misc
@version    $Id: 1.7-test4, 2015-11-09 12:30:44 ACDT $;
@author     Jason Millward
@license    http://opensource.org/licenses/MIT

Usage:
    autorippr.py   ( --rip | --compress | --extra )  [options]
    autorippr.py   ( --rip [ --compress ] )          [options]
    autorippr.py   --all                             [options]
    autorippr.py   --test

Options:
    -h --help       Show this screen.
    --version       Show version.
    --debug         Output debug.
    --rip           Rip disc using makeMKV.
    --compress      Compress using HandBrake or FFmpeg.
    --extra         Lookup, rename and/or download extras.
    --all           Do everything
    --test          Tests config and requirements
    --silent        Silent mode

"""

import os
import sys
import yaml
import errno
import subprocess
from collections import defaultdict
from classes import *
from tendo import singleton
from PyQt4 import QtCore, QtGui
from pytvdbapi import api



__version__ = "1.8-gui"

me = singleton.SingleInstance()
CONFIG_FILE = "{}/settings.cfg".format(
    os.path.dirname(os.path.abspath(__file__)))

tvdb = api.TVDB('B43FF87DE395DF56')
notify = None

class AutoRippr(QtGui.QMainWindow, gui.Ui_MainWindow):
    def __init__(self, config, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.config = config
        
        # initialize Autoripper objects
        log.debug("Ripping initialised")
        self.mkv_api = makemkv.MakeMKV(self.config)
        self.dvds = None

        # initialize threaded GUI functions
        self.discInfo_thread = guihelper.discInfo(self.mkv_api)

        # connect signals to slots
        self.buttonRip.clicked.connect(self.rip)
        self.buttonCompress.clicked.connect(self.compress)
        self.buttonDiscInfo.clicked.connect(self.discInfo)
        self.buttonFB.clicked.connect(self.extras)
        self.buttonTvInfo.clicked.connect(self.tvInfo)
        self.checkTV.stateChanged.connect(self.tvCheckBox)
        self.comboShowTitle.currentIndexChanged.connect(self.showSelected)

        self.textEditShowTitle.setValidator(guihelper.ValidTvTitle(self))
        self.textEditShowTitle.setDisabled(True)
        self.textEditShowTitle.returnPressed.connect(self.showNameEdited)
        self.comboSeasons.setDisabled(True)
        self.comboShowTitle.setDisabled(True)
        self.lineEditNumbers.setDisabled(True)

        # This is the visual element to enter TV show titles
        table_header = ['Index', 'Disc Title','Episode #', 'Duration', 'Episode Name', 'Filename']
        self.tableWidget.setColumnCount(len(table_header))
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.setHorizontalHeaderLabels(table_header)

        self.showTVDB = None



    def eject(self, config, drive):
        """
            Ejects the DVD drive
            Not really worth its own class
        """
        log = logger.Logger("Eject", config['debug'], config['silent'])

        log.debug("Ejecting drive: " + drive)
        log.debug("Attempting OS detection")

        try:
            if self.config['os'] == 'win32':
                import ctypes
                ctypes.windll.winmm.mciSendStringW(
                    u"set cdaudio door open", None, drive, None)

            elif self.config['os'] == 'darwin':
                p = os.popen("drutil eject " + drive)

                while 1:
                    line = p.readline()
                    if not line:
                        break
                    log.debug(line.strip())

            elif self.config['os'] == 'Unix':
                p = os.popen("eject -vm " + drive)

                while 1:
                    line = p.readline()
                    if not line:
                        break
                    log.debug(line.strip())

        except Exception as ex:
            log.error("Could not detect OS or eject CD tray")
            log.ex("An exception of type {} occured.".format(type(ex).__name__))
            log.ex("Args: \r\n {}".format(ex.args))

        finally:
            del log


    def rip(self):
        """
            Main function for ripping
            Does everything
            Returns nothing
        """
        log = logger.Logger("Rip", self.config['debug'], self.config['silent'])

        mkv_save_path = self.config['makemkv']['savePath']

        # if TV Show box is checked, don't clear data!
        if self.dvds is not None:
            dvds = self.dvds
        else:
            log.debug("Checking for DVDs")
            dvds = self.mkv_api.find_disc()

        log.debug("{} DVD(s) found".format(len(dvds)))

        if len(dvds) > 0:
            # Best naming convention ever
            for dvd in dvds:
                self.mkv_api.set_title(dvd["discTitle"])
                self.mkv_api.set_index(dvd["discIndex"])

                if self.checkTV.isChecked():
                    disc_type = self.mkv_api.set_type('tv')
                    print 'setting type to tv', disc_type
                else:
                    disc_type = self.mkv_api.get_type()
                    print 'auto detecting type'
                    
                if self.checkTV.isChecked():
                    disc_title = '{} - S{}'.format(self.textEditShowTitle.text(), self.comboSeasons.currentIndex() + 1)
                    self.mkv_api.set_title(disc_title)
                else:
                    disc_title = self.mkv_api.get_title()
                

                disc_path = '{}/{}'.format(mkv_save_path, disc_title)
                if not os.path.exists(disc_path) or self.checkTV.isChecked():
                    os.makedirs(disc_path)

                    if self.dvds is None:
                        self.mkv_api.get_disc_info()

                    saveFiles = self.mkv_api.get_savefiles()

                    if len(saveFiles) != 0:
                        filebot = self.config['filebot']['enable']

                        for x, dvdTitle in enumerate(saveFiles):

                            if self.checkTV.isChecked():
                                disc_title = self.tableWidget.item(x, 5).text()
                                
                            dbvideo = database.insert_video(
                                disc_title,
                                disc_path,
                                disc_type,
                                dvdTitle['index'],
                                filebot
                            )

                            database.insert_history(
                                dbvideo,
                                "Video added to database"
                            )

                            database.update_video(
                                dbvideo,
                                3,
                                dvdTitle['title']
                            )

                            log.debug("Attempting to rip {} from {}".format(
                                dvdTitle['title'],
                                disc_title
                            ))

                            with stopwatch.StopWatch() as t:
                                database.insert_history(
                                    dbvideo,
                                    "Video submitted to MakeMKV"
                                )
                                status = self.mkv_api.rip_disc(
                                    mkv_save_path, dvdTitle['index'])

                            if status:
                                log.info("It took {} minute(s) to complete the ripping of {} from {}".format(
                                    t.minutes,
                                    dvdTitle['title'],
                                    disc_title
                                ))

                                database.update_video(dbvideo, 4)

                                if 'rip' in self.config['notification']['notify_on_state']:
                                    notify.rip_complete(dbvideo)


                            else:
                                database.update_video(dbvideo, 2)

                                database.insert_history(
                                    dbvideo,
                                    "MakeMKV failed to rip video"
                                )
                                notify.rip_fail(dbvideo)

                                log.info(
                                    "MakeMKV did not did not complete successfully")
                                log.info("See log for more details")

                        if self.config['makemkv']['eject']:
                            self.eject(self.config, dvd['location'])
                    else:
                        log.info("No video titles found")
                        log.info(
                            "Try decreasing 'minLength' in the config and try again")

                else:
                    log.info("Video folder {} already exists".format(disc_title))

        else:
            log.info("Could not find any DVDs in drive list")


    def compress(self):
        """
            Main function for compressing
            Does everything
            Returns nothing
        """
        log = logger.Logger("Compress", self.config['debug'], self.config['silent'])

        comp = compression.Compression(self.config)

        log.debug("Compressing initialised")
        log.debug("Looking for videos to compress")

        dbvideos = database.next_video_to_compress()

        for dbvideo in dbvideos:
            if comp.check_exists(dbvideo) is not False:

                database.update_video(dbvideo, 5)

                log.info("Compressing {} from {}" .format(
                    dbvideo.filename, dbvideo.vidname))

                with stopwatch.StopWatch() as t:
                    status = comp.compress(
                        args=self.config['compress']['com'],
                        nice=int(self.config['compress']['nice']),
                        dbvideo=dbvideo
                    )

                if status:
                    log.info("Video was compressed and encoded successfully")

                    log.info("It took {} minutes to compress {}".format(
                        t.minutes, dbvideo.filename
                    )
                    )

                    database.insert_history(
                        dbvideo,
                        "Compression Completed successfully"
                    )

                    if 'compress' in config['notification']['notify_on_state']:
                        notify.compress_complete(dbvideo)

                    comp.cleanup()

                else:
                    database.update_video(dbvideo, 5)

                    database.insert_history(dbvideo, "Compression failed", 4)

                    notify.compress_fail(dbvideo)

                    log.info("Compression did not complete successfully")
            else:
                database.update_video(dbvideo, 2)

                database.insert_history(
                    dbvideo, "Input file no longer exists", 4
                )

        else:
            log.info("Queue does not exist or is empty")


    def extras(self):
        """
            Main function for filebotting
            Does everything
            Returns nothing
        """
        log = logger.Logger("Extras", self.config['debug'], self.config['silent'])

        fb = filebot.FileBot(self.config['debug'], self.config['silent'], self.plainTextEdit)

        dbvideos = database.next_video_to_filebot()

        for dbvideo in dbvideos:
            log.info("Attempting video rename")

            database.update_video(dbvideo, 7)

            movePath = dbvideo.path
            if self.config['filebot']['move']:
                if dbvideo.vidtype == "tv":
                    movePath = self.config['filebot']['tvPath']
                else:
                    movePath = self.config['filebot']['moviePath']

            status = fb.rename(dbvideo, movePath)

            if status[0]:
                log.info("Rename success")

                database.update_video(dbvideo, 6)

                if self.config['filebot']['subtitles']:
                    log.info("Grabbing subtitles")

                    status = fb.get_subtitles(
                        dbvideo, self.config['filebot']['language'])

                    if status:
                        log.info("Subtitles downloaded")
                        database.update_video(dbvideo, 8)

                    else:
                        log.info("Subtitles not downloaded, no match")
                        database.update_video(dbvideo, 8)

                    log.info("Completed work on {}".format(dbvideo.vidname))

                    if self.config['commands'] is not None and len(self.config['commands']) > 0:
                        for com in self.config['commands']:
                            subprocess.Popen(
                                [com],
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                shell=True
                            )

                else:
                    log.info("Not grabbing subtitles")
                    database.update_video(dbvideo, 8)

                if 'extra' in self.config['notification']['notify_on_state']:
                    notify.extra_complete(dbvideo)

                log.debug("Attempting to delete %s" % dbvideo.path)

                try:
                    os.rmdir(dbvideo.path)
                except OSError as ex:
                    if ex.errno == errno.ENOTEMPTY:
                        log.debug("Directory not empty")

            else:
                log.info("Rename failed")

        else:
            log.info("No videos ready for filebot")

    def _test(self, text):
        print text

    def discInfo(self):
        """
        Main function for displaying disk info
        Gets title information
        Returns nothing
        """

        self.clearTable()

        log.debug("Checking for DVDs")
        dvds = self.mkv_api.find_disc()

        self.dvds = dvds

        if self.checkTV.isChecked():
            disc_type = self.mkv_api.set_type('tv')
        else:
            disc_type = self.mkv_api.get_type()
        disc_title = self.mkv_api.get_title()

        self.mkv_api.get_disc_info()

        titles = self.mkv_api.get_savefiles()
        titles = sorted(titles, key=lambda k: k['index']) 

        epNums = self.lineEditNumbers.text()

        if ',' in epNums:
            epNums = [int(str(x).strip()) for x in epNums.split(',')]
            epNums.sort()
        elif '-' in epNums:
            epNums = epNums.split('-')
            epNums = [int(x.strip()) for x in epNums.split(',')]
            epNums.sort()
            epNums = range(epNums[0], epNums[1])
        elif epNums != 'Episode Numbers':
            epNums = int(epNums.strip())
        else:
            epNums = [-1] * len(titles)


        seasonNum = self.comboSeasons.currentIndex()+1

        for title in titles:
            epNum = epNums[int(title['index'])]
            rowPosition = self.tableWidget.rowCount()
            self.tableWidget.insertRow(rowPosition)

            # after that you have empty row that you can populate like this for example( if you have 3 columns):
            item = QtGui.QTableWidgetItem('{}'.format(title['index']))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(rowPosition , 0, item)

            item = QtGui.QTableWidgetItem('{}'.format(title['title']))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(rowPosition , 1, item)
            
            if epNum == -1:
                item = QtGui.QTableWidgetItem('{}'.format(title['title']))
                self.tableWidget.setItem(rowPosition , 2, item)
            else:
                item = QtGui.QTableWidgetItem(str(epNum))
                self.tableWidget.setItem(rowPosition , 2, item)

            item = QtGui.QTableWidgetItem('{}'.format(title['dur']))
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.tableWidget.setItem(rowPosition , 3, item)

            if epNum == -1:
                item = QtGui.QTableWidgetItem('')
                self.tableWidget.setItem(rowPosition , 4, item)
            else:
                epName = self.showTVDB[seasonNum][epNum].EpisodeName
                item = QtGui.QTableWidgetItem(epName)
                self.tableWidget.setItem(rowPosition , 4, item)

            if epNum == -1:
                item = QtGui.QTableWidgetItem('')
                self.tableWidget.setItem(rowPosition , 5, item)
            else:
                fname = '{} - {} - S{}E{}'.format(self.textEditShowTitle.text(), epName, seasonNum, epNum)
                item = QtGui.QTableWidgetItem(fname)
                self.tableWidget.setItem(rowPosition , 5, item)
                # title['title'] = fname


        self.tableWidget.resizeColumnsToContents()
        # self.tableWidget.sortByColumn(0)

        # self.mkv_api.set_savefiles(titles)


    def tvCheckBox(self):
        self.clearTable()

        if self.checkTV.isChecked():
            self.textEditShowTitle.setDisabled(False)
            self.lineEditNumbers.setDisabled(False)
            self.comboSeasons.clear()
            self.comboSeasons.setDisabled(False)
            self.comboShowTitle.clear()
            self.comboShowTitle.setDisabled(False)
            self.showTVDB = None
            self.textEditShowTitle.setText('')
            self.textEditShowTitle.setFocus()
            self.textEditShowTitle.setCursorPosition(0)
        else:
            self.textEditShowTitle.setText('Show Title')
            self.lineEditNumbers.setText('Episode Numbers')
            self.textEditShowTitle.setDisabled(True)
            self.comboSeasons.setDisabled(True)
            self.comboShowTitle.setDisabled(True)
            self.lineEditNumbers.setDisabled(True)


    def clearTable(self):
        while (self.tableWidget.rowCount() > 0):
            self.tableWidget.removeRow(0);


    def tvInfo(self):
        allRows = self.tableWidget.rowCount()

        newSaveTitles = defaultdict(dict)
        curSaveTitles = self.mkv_api.get_savefiles()

        for row in xrange(0,allRows):
            discIndex = self.tableWidget.item(row, 0)
            epNum = self.tableWidget.item(row, 1)
            epTitle = self.tableWidget.item(row, 3)
            fname = self.tableWidget.item(row, 4)

            seasonNum = self.comboSeasons.currentIndex()+1
            epName = self.showTVDB[seasonNum][int(epNum.text())].EpisodeName
            epTitle.setText(epName)

            fname.setText('{} - {}x{:02d}.mkv - {}'.format(self.textEditShowTitle.text(), seasonNum, epNum.text()), epName)

            newSaveTitles[str(discIndex.text())] = str(fname.text())

            # self.tableWidget.setItem(row, 1, epNum)
            # self.tableWidget.setItem(row, 3, epTitle)
            # self.tableWidget.setItem(row, 4, fname)

        self.tableWidget.resizeColumnsToContents()
        self.tableWidget.sortByColumn(0)


        for title in curSaveTitles:
            title['title'] = newSaveTitles[title['index']]

        # self.mkv_api.set_savefiles(curSaveTitles)


    def showNameEdited(self):
        self.comboSeasons.clear()

        name = str(self.textEditShowTitle.text())
        result = tvdb.search(name, 'en')
        self.showTVDB = result[0]
        self.showsTVDB = result

        for x in result:
            self.comboShowTitle.addItem('{}'.format(x.SeriesName))


    def showSelected(self):
        show = self.showsTVDB[self.comboShowTitle.currentIndex()]
        numseasons = len(show)
        self.comboSeasons.clear()
        
        for x in range(0, numseasons):
            self.comboSeasons.addItem('S{}'.format(x+1))

        self.lineEditNumbers.setText('')
        self.lineEditNumbers.setFocus()


if __name__ == '__main__':
    # arguments = docopt.docopt(__doc__, version=__version__)
    config = yaml.safe_load(open(CONFIG_FILE))

    # skip original argv parsing
    if False:
        config['debug'] = arguments['--debug']

        config['silent'] = arguments['--silent']

        notify = notification.Notification(
            config, config['debug'], config['silent'])

        if bool(config['analytics']['enable']):
            analytics.ping(__version__)

        if arguments['--test']:
            testing.perform_testing(config)

        if arguments['--rip'] or arguments['--all']:
            rip(config)

        if arguments['--compress'] or arguments['--all']:
            compress(config)

        if arguments['--extra'] or arguments['--all']:
            extras(config)

    else:
        config['debug'] = True

        config['silent'] = False

        # testing.perform_testing(config)

        notify = notification.Notification(
            config, config['debug'], config['silent'])

        log = logger.Logger("Start up", config['debug'], config['silent'])

        print sys.platform

        try:
            if sys.platform == 'win32':
                log.debug("OS detected as Windows")
                config['os'] = 'win32'

            elif sys.platform == 'darwin':
                log.debug("OS detected as OSX")
                config['os'] = 'OSX'

            else:
                log.debug("OS detected as Unix")
                config['os'] = 'Unix'

        except Exception as ex:
            log.error("Could not detect OS")
            log.ex("An exception of type {} occured.".format(type(ex).__name__))
            log.ex("Args: \r\n {}".format(ex.args))

    app = QtGui.QApplication(sys.argv)
    MainApp = AutoRippr(config)
    MainApp.show()
    sys.exit(app.exec_())