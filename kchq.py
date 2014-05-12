#!/usr/bin/env python
#coding=utf-8

import kcdb, kcwidget, kcwindow
import threading, sys
from gi.repository import Gtk as gtk, GObject as gobj

threads = {}

threads['listener'] = threading.Thread(target = kcdb.listener.main, name = 'kcListener')
threads['listener'].daemon = True
threads['listener'].start()

gobj.timeout_add(2000, kcwidget.widget.main)
gobj.timeout_add(50, kcdb.db.main)

gtk.main()