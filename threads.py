# -*- coding: utf-8 -*-

import logging
import argparse
import time
from instagram import Instagram


class Application:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.instagram = Instagram(username, password)
        self.logged_in = False

    def exit_application(self):
        if self.logged_in:
            self.instagram.logout()

    def thread_list(self, sleep_time=2):
        next_page = ''
        while True:
            time.sleep(sleep_time)

            direct = self.instagram.direct_list(next_page=next_page)
            if direct:
                items = direct['inbox']['threads']
                for item in items:
                    yield item['thread_title']

                if not direct['inbox']['has_older']:
                    return

                next_page = direct['inbox']['oldest_cursor']

    def run(self):
        if not self.instagram.login():
            self.exit_application()
            return

        self.logged_in = True
        for thread_name in self.thread_list():
            print thread_name


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--username", required=True,
                    help="Instagram username")
    ap.add_argument("-p", "--password", required=True,
                    help="Instagram password")

    args = vars(ap.parse_args())

    app = Application(args['username'], args['password'])
    try:
        app.run()
    except KeyboardInterrupt:
        app.exit_application()
    except BaseException as err:
        app.exit_application()
        logging.error(err.message)

    app.exit_application()

