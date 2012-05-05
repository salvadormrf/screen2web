#!/usr/bin/env python

""" Take screenshot > Upload to internet > Open in browser """

__author__      = "Salvador Faria"
__copyright__   = "Copyright 1984, Planet Earth"

import os
import io
import time
import logging
import ConfigParser
from os import system as command

import urllib
import urllib2
import base64
import json

sample_config = """
[configuration]
extension = png
create_screen_cmd = sleep 0.2; scrot -s %s 
open_url_cmd = chromium-browser %s &

[imgur]
upload_key = 83caf5dfbeb3aacd906bad402358bc68
upload_url = http://api.imgur.com/2/upload.json
"""

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler()) # by default, sys.stderr

# load configuration
config = ConfigParser.ConfigParser()
config.readfp(io.BytesIO(sample_config))


class Screen2Web(object):
    """ Generic class """
    
    def __init__(self, config):
        self.url = None
        self.config = config
        self.filename = "%s.%s" % (int(time.time()), config.get("configuration", "extension"))
	self.images_path = os.path.expanduser('~/.screens/')
        self.file_path = self.images_path + self.filename

	if not os.path.exists(self.images_path):
	    os.makedirs(self.images_path)
	    logger.debug("Creating image path...")
    
    def create_screen(self, file_path=None):
        res = None
	file_path = file_path if file_path else self.file_path
	
        try:
            logger.debug("Saving image on: %s ...." % file_path)
            raw_cmd = self.config.get("configuration", "create_screen_cmd")
            res = command(raw_cmd % file_path)
        except:
            logger.exception("Unable to create image file")
	
        return self.file_path if (res >= 0) else None
    
    def upload(self, file_path=None):
	if not hasattr(self, "_upload"):
	    raise NotImplementedError("_upload")
	logger.debug("Uploading image...")
        self.url = self._upload(file_path)
	return self.url

    def open_url(self, url=None):
        url = url if url else self.url
	logger.debug("Opening url: %s" % url)
        raw_cmd = self.config.get("configuration", "open_url_cmd")
        command(raw_cmd % url)
    
    def run(self):
        file_path = self.create_screen()
	url = self.upload()
        self.open_url()
        return url


class Screen2imgur(Screen2Web):
    def __init__(self, config):
        super(Screen2imgur, self).__init__(config)
        self.api_upload_endpoint = self.config.get("imgur", "upload_url")
        self.api_key = self.config.get("imgur", "upload_key")
        
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


o = Screen2imgur(config)
o.run()
