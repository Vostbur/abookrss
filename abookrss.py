#!/usr/bin/env python
# coding: utf-8

import os
import stat
import datetime
import time
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import getopt
from codecs import open
import socket
from SocketServer import TCPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
try:
    from hsaudiotag import mpeg
except ImportError:
    print("Needs module 'hsaudiotag'. Install with 'pip install hsaudiotag'.")
    sys.exit()

class RSSBook:
    """Generate rss feed with chapters of mp3 audiobook"""
    def __init__(self, folder, ip, port):
        if os.path.exists(folder):
            self.folder = folder
        else:
            print(u'Указанный каталог не существует')
            sys.exit()
        self.ip = ip
        self.port = port
        self.rfc822 = '%a, %d %b %Y %H:%M:%S +0000'
        self.common = {}
        self.items = []
        self.rss = ''
        
    def get_items(self):
        """Анализ файлов в каталоге и подкаталогах"""
        for root, dirs, files in os.walk(self.folder):
            for i in filter(lambda x: x.lower().endswith('.mp3'), sorted(files)):
                dict_files = {}
                path_to_file = os.path.join(root, i)
                audio_metadata = mpeg.Mpeg(path_to_file)
                link = os.path.relpath(os.path.join(root, i), self.folder).replace('\\', '/')
                dict_files['album'] = audio_metadata.tag.album if audio_metadata.tag else i
                dict_files['title'] = audio_metadata.tag.title if audio_metadata.tag else i
                dict_files['enclosure'] = 'http://%s:%d/%s' % (self.ip, self.port, link)
                dict_files['length'] = os.path.getsize(path_to_file)
                dict_files['link'] = '/' + link
                dict_files['guid'] = link + '.uid'
                dict_files['description'] = audio_metadata.tag.comment if audio_metadata.tag else ''
                dict_files['pubdate'] = time.strftime(self.rfc822, time.localtime(os.stat(path_to_file)[stat.ST_MTIME]))
                dict_files['itunes_author'] = audio_metadata.tag.artist if audio_metadata.tag else ''
                dict_files['itunes_subtitle'] = ''
                dict_files['itunes_summary'] = dict_files['description']
                dict_files['itunes_duration'] = unicode(audio_metadata.duration)
                dict_files['itunes_keywords'] = ''
                self.items.append(dict_files)

    def get_top(self):
        """Общие парменты rss-канала"""
        pub_date = time.strftime(self.rfc822, time.localtime())
        self.common['title'] = self.items[0]['album']
        self.common['description'] = self.items[0]['description']
        self.common['link'] = u'http://%s:%d' % (self.ip, self.port)
        self.common['copyright'] = datetime.date.today().year
        self.common['lastbuilddate'] = pub_date
        self.common['pubdate'] = pub_date
        self.common['webmaster'] = self.items[0]['itunes_author']
        self.common['itunes_author'] = self.common['webmaster']
        self.common['itunes_subtitle'] = self.common['title']
        self.common['itunes_summary'] = self.common['description']
        self.common['itunes_name'] = self.common['webmaster']
        self.common['itunes_email'] = u'mail@mail.com'
        self.common['itunes_image'] = u'http://%s:%d/image.jpg' % (self.ip, self.port)

    def generate(self):
        self.get_items()
        if not self.items:
            print(u'В каталоге %s и подкаталогах нет mp3 файлов' % self.folder)
            sys.exit()
        self.get_top()
        self.rss = open('xmltop.xml', 'U').read() % self.common
        for i in self.items:
            self.rss += open('xmlitem.xml', 'U').read() % i
        self.rss += '</channel></rss>'
        rss_path = os.path.normpath(os.path.join(self.folder, u'rss.xml'))
        with open(rss_path, encoding='utf-8', mode='w') as rss:
            rss.write(self.rss)

def main(argv):
    IP = socket.gethostbyname(socket.getfqdn())
    PORT = 8080
    try:
        opts, args = getopt.getopt(argv,"hd:i:p:",["dir=","ip=","port="])
    except getopt.GetoptError:
       print 'abookrss.py -d/--dir= <dir_with_mp3> [-i/--ip=<ip_to_bind>] [-p/--port=8080]'
       sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'abookrss.py -d/--dir= <dir_with_mp3> [-i/--ip=<ip_to_bind>] [-p/--port=port]'
            sys.exit()
        elif opt in ("-d", "--dir"):
            FOLDER = arg
        elif opt in ("-i", "--ip"):
            IP = arg
        elif opt in ("-p", "--port"):
            PORT = int(arg)

    RES = RSSBook(FOLDER, IP, PORT)
    RES.generate()
    os.chdir(FOLDER)
    SERV = TCPServer(('', PORT), SimpleHTTPRequestHandler)
    print('serving at %s:%d' % (IP, PORT))
    SERV.serve_forever()

if __name__ == '__main__':
    main(sys.argv[1:])
