#!/usr/bin/env python

""" Take screenshot > Upload to internet > Open in browser """
# http://sveinbjorn.org/platypus

__author__      = "Salvador Faria"
__copyright__   = "Copyright 1984, Planet Earth"

import os
import platform
import time
import logging
from os import system as command

import urllib
import urllib2
import base64
import json

# imgurl upload keys
imgur_key = "83caf5dfbeb3aacd906bad402358bc68"
default_config = {"cmd_screenshot": "", "cmd_open_url": ""}

os_name =  platform.uname()[0].lower()
if os_name == "darwin":
    default_config["cmd_screenshot"] = "screencapture -i %s"
    default_config["cmd_open_url"] = "open -e %s"
elif os_name == "linux":
    default_config["cmd_screenshot"] = "sleep 0.2; scrot -s %s"
    default_config["cmd_open_url"] = "chromium-browser %s &"
else:
    raise NotImplemented("Script was not yet developed for your system.... send me an email to support it :)")

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler()) # by default, sys.stderr

class Screen2Web(object):
    """ Generic class """
    def __init__(self, config, extension="png"):
        self.url = None
        self.config = config
        self.filename = "%s.%s" % (int(time.time()), extension)
        self.images_path = os.path.expanduser('~/.screens/')
        self.file_path = self.images_path + self.filename

        if not os.path.exists(self.images_path):
            os.makedirs(self.images_path)
            logger.debug("Creating image path...")
    
    def create_screen(self, file_path=None):
        file_path = file_path if file_path else self.file_path
        res = None
        
        try:
            logger.debug("Saving image on: %s ...." % file_path)
            res = command(self.config["cmd_screenshot"] % file_path)
        except:
            logger.exception("Unable to create image file")
	
        return self.file_path if (res >= 0) else None
    
    def upload(self, file_path=None):
        if not hasattr(self, "_upload"): raise NotImplementedError("_upload")
        logger.debug("Uploading image...")
        self.url = self._upload(file_path)
        return self.url

    def open_url(self, url=None):
        url = url if url else self.url
        logger.debug("Opening url: %s" % url)
        command(self.config["cmd_open_url"] % url)
    
    def run(self):
        file_path = self.create_screen()
        url = self.upload()
        self.open_url()
        return url

class Screen2imgur(Screen2Web):
    def __init__(self, api_key, config):
        super(Screen2imgur, self).__init__(config)
        self.api_upload_endpoint = "http://api.imgur.com/2/upload.json"
        self.api_key = api_key
        
    def _upload(self, file_path=None):
        file_path = file_path if file_path else self.file_path
        
        # check API documentation
        # http://api.imgur.com/resources_anon#upload
        with file(file_path, 'rb') as f:
            data = urllib.urlencode({'key': self.api_key, 'image': base64.b64encode(f.read())})
        
        # do call
        req = urllib2.Request(self.api_upload_endpoint, data)
        res = urllib2.urlopen(req).read()
        
        # parse response
        response = json.loads(res)
        
        link = None
        if "error" in response:
            logger.debug("Unable to upload image, reason: %s" % response["error"]["message"])
        
        link = response['upload']['links']['original']
        return link


o = Screen2imgur(imgur_key, default_config)
o.run()
