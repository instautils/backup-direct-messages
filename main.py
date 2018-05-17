# -*- coding: utf-8 -*-

import logging
import urllib2
import os
import argparse
import csv
from instagram import Instagram, safe_string


class Application:
    def __init__(self, username, password, thread_name, output_dir,
                 debug_mode=False):
        self.username = username
        self.password = password
        self.selected_thread_name = thread_name
        self.logged_in = False
        self.debug_mode = debug_mode
        self.media_folder = output_dir
        self.instagram = Instagram(username, password, debug_mode=debug_mode)
        self.selected_thread_id = ''

        if not os.path.exists(output_dir):
            os.mkdir(output_dir, 0755)

        self.dump_file = open(os.path.join(output_dir, 'dump_file.csv'), 'wb')
        self.csv_handler = csv.writer(self.dump_file)

    def exit_application(self, error):
        if self.debug_mode:
            logging.error(error)
        self.dump_file.close()
        if self.logged_in:
            self.instagram.logout()

    def find_thread_id(self, thread_title):
        next_page = ''
        while True:
            direct = self.instagram.direct_list(next_page=next_page)
            if direct:
                items = direct['inbox']['threads']
                for item in items:
                    if item['thread_title'] == thread_title:
                        return item['thread_id']

                if not direct['inbox']['more_available']:
                    return

                next_page = direct['inbox']['next_max_id']

    @staticmethod
    def download(url, target):
        if os.path.exists(target):
            return
        image_file = urllib2.urlopen(url)
        with open(target, 'wb') as output:
            output.write(image_file.read())

    def dump_message(self, message):
        self.csv_handler.writerow([message['user_id'],
                                   safe_string(message['text']),
                                   message['item_id'],
                                   message['timestamp']])

    def thread_message_generator(self):
        next_page = ''
        while True:
            thread = self.instagram.direct_thread(self.selected_thread_id, next_page=next_page)
            if not thread:
                self.exit_application('Could not select thread')
                return

            for message in thread['thread']['items']:
                yield message

            if not thread['thread']['more_available_max']:
                return

            next_page = thread['thread']['next_max_id']

    def run(self):
        if self.debug_mode:
            logging.info('Logging into {}'.format(self.username))

        if not self.instagram.login():
            self.exit_application('Login failed')
            return

        self.logged_in = True
        self.selected_thread_id = self.find_thread_id(self.selected_thread_name)
        if not self.selected_thread_id:
            self.exit_application('Could not find thread_id')
            return

        if self.debug_mode:
            logging.info(
                'Thread id for {} has been founded, id={}'.format(self.selected_thread_name, self.selected_thread_id))

        for message in self.thread_message_generator():
            if message['item_type'] == 'media':
                media_type = message['media']['media_type']
                if media_type == 1:
                    self.download(message['media']['image_versions2']['candidates'][0]['url'],
                                  os.path.join(self.media_folder, message['item_id'] + '.jpg'))
                elif media_type == 2:
                    self.download(message['media']['video_versions'][0]['url'],
                                  os.path.join(self.media_folder, message['item_id'] + '.mp4'))
            elif message['item_type'] == 'text':
                self.dump_message(message)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--username", required=True,
                    help="Instagram username")
    ap.add_argument("-p", "--password", required=True,
                    help="Instagram password")
    ap.add_argument("-t", "--thread-title", required=True,
                    help="Thread (direct chat) title")
    ap.add_argument("-d", "--debug", type=bool, default=False,
                    help="Debug mode")
    ap.add_argument("-o", "--output", type=str, default='output',
                    help="Output directory")
    ap.add_argument("-l", "--log-file", type=str, default='',
                    help="Log file")

    args = vars(ap.parse_args())

    if args["debug"]:
        if args['log_file']:
            logging.basicConfig(filename=args['log_file'], format='%(levelname)s: %(message)s', level=logging.DEBUG)
        else:
            logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

    app = Application(args['username'], args['password'], args['thread_title'], args['output'],
                      debug_mode=args["debug"])
    try:
        app.run()
    except KeyboardInterrupt:
        app.exit_application('Keyboard Interrupt')
    except BaseException as err:
        app.exit_application('Unknown error')
        logging.error(err.message)
