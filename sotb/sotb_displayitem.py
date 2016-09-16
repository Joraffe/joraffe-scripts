#!/usr/bin/env humblepy
import math
import unidecode
import urllib

from libraries.cdn import signurl
from mutagen.mp3 import MP3


class SOTBDisplayItem(object):
  """
  A DisplayItem constructed from information from a given SOTB

  Attributes:
    machine_name        (str): A str to rep a DI's machine_name
    human_name          (str): A str to rep a DI's human_name (also used for
                               box-art-human-name)
    description         (str): A str to rep a DI's description-text
    slideout_image      (str): A str to denote true ('1') or false ('0') if
                               the DI needs a preview-image
    background_image    (str): A str to denote true ('1') or false ('0') if
                               the DI needs a slideshow-background
    dev_name            (str): A str to rep a DI's developer-name; '0' if N/A
    dev_url             (str): A str to rep a DI's developer-url; '0' if N/A
    pub_name            (str): A str to rep a DI's publisher-name; '0' if N/A
    pub_url             (str): A str to rep a DI's publisher-url; '0' if N/A
    callout             (str): A str to rep a DI's front-page-subtitle; '0' if
                               N/A
    devices            (list): A list of str to rep a DI's applicable devices
                               (game or mobile); used for a DI's content, ['0']
                               if N/A
    drms               (list): A list of str to rep a DI's applicable drms
                               (steam, download, etc); used for a DI's content,
                               ['0'] if N/A
    platforms          (list): A list of str to rep a DI's applicable platforms
                               (windows, mac, linux, etc); used for a DI's
                               content, ['0'] if N/A
    youtube_link        (str): A str to rep a DI's youtube-link; '0' if N/A
    pdf_preview         (str): A str to denote true ('1') or false ('0') if
                               the DI needs an image_extra
    soundtrack_listing  (str): A str to denote true ('1') or false ('0') if
                               the DI needs a soundtrack-listing; used for
                               audiobooks
    override            (str): A str to rep a DI's override. Most of the time
                               equal to 'bundle'; otherwise equal to a specific
                               bundle machine_name
    di_dict            (dict): A python dict to rep the actual DI to be imported
                               via Model Importer. Constructed from the other
                               attributes via self.process()
  """
  PLAT_ICONS = {
    'game': {
      'steam': ['windows', 'mac', 'linux'],
      'download': ['windows', 'mac', 'linux'],
      'other-key': ['windows', 'mac', 'linux'],
      'uplay': ['windows', 'mac', 'linux'],
      'origin': ['windows', 'mac', 'linux'],
      'wiiu': ['wiiu'],
      '3DS': ['3DS'],
      'ps3': ['ps3'],
      'ps4': ['ps4'],
      'xboxone': ['xboxone']
    },
    'mobile': {
      'android': ['android'],
      'iOS': ['iOS']
    }
  }

  def __init__(self, sotb_info):
    """Prepares a SOTBDisplayItem based off of a template"""
    self.machine_name = sotb_info['machine_name']
    self.description = sotb_info['description']
    self.dev_name = sotb_info['dev_name']
    self.dev_url = sotb_info['dev_url']
    self.callout = sotb_info['callout']
    self.human_name = sotb_info['human_name']
    self.devices = sotb_info['device'].split("+")
    self.drms = sotb_info['drm'].split("+")
    self.platforms = sotb_info['platform'].split("+")
    self.pdf_preview = sotb_info['pdf_preview']
    self.pub_name = sotb_info['pub_name']
    self.pub_url = sotb_info['pub_url']
    self.slideout_image = sotb_info['slideout_image']
    self.background_image = sotb_info['background_image']
    self.soundtrack_listing = sotb_info['audio']
    self.youtube_link = sotb_info['youtube']
    self.override = sotb_info['override']

    self.di_dict = {
      'struct': {
        'default': {},
        'bundle': {}
      }
    }

  @classmethod
  def existing_di(cls, sotb_info, existing_dict):
    """Prepares a SOTBDisplayItem based off of existing data"""
    obj = cls(sotb_info)
    obj.di_dict = existing_dict
    if obj.override != 'bundle':
      obj.di_dict['struct'][obj.override] = {}
    return obj

  def process(self):
    """
    Constructs/adds the relevant info to SOTBDisplayItem's di_dict attribute.
    Does so by calling all of the other update() functions
    """
    self.update_machine_name()
    self.update_human_names()
    self.update_front_page_art()
    self.update_preview_image()
    self.update_slideshow_background()
    self.update_description_text()
    self.update_platform_icons()
    self.update_developers()
    self.update_publishers()
    self.update_front_page_subtitle()
    self.update_youtube_link()
    self.update_image_extra()
    self.update_soundtrack_listing()

  def remove_existing_at(self):
    """Removes the 'exported_at' key/value for an existing DisplayItem"""
    del self.di_dict['exported_at']

  def update_description_text(self):
    """Updates a DisplayItem's 'description-text' value."""
    if self.description != '0':
      self.di_dict['struct'][self.override]['description-text'] = (
        self.no_unicode(self.description)
      )

  def update_developers(self):
    """Updates a DisplayItem's 'developers'"""
    if self.dev_name != '0' and self.dev_url != '0':
      self.di_dict['struct'][self.override]['developers'] = [
        {
          'developer-name': self.dev_name,
          'developer-url': self.dev_url
        }
      ]

  def update_front_page_art(self):
    """Updates a DisplayItem's 'front-page-art'"""
    if self.override == 'bundle':
      self.di_dict['struct'][self.override]['front-page-art'] = (
        'images/displayitems/%s.png' % self.machine_name
      )
    else:
      self.di_dict['struct'][self.override]['front-page-art'] = (
        'images/displayitems/%s_%s.png' % (self.machine_name, self.override)
      )

  def update_front_page_subtitle(self):
    """Updates a DisplayItem's 'front-page-subtitle' (callout)"""
    if self.callout != '0':
      self.di_dict['struct'][self.override]['front-page-subtitle'] = (
        self.no_unicode(self.callout)
      )

  def update_human_names(self):
    """Updates a DisplayItem's 'box-art-human-name' and 'human-name'"""
    self.di_dict['struct']['default']['human-name'] = (
      self.no_unicode(self.human_name)
    )
    self.di_dict['struct'][self.override]['box-art-human-name'] = (
      self.no_unicode(self.human_name)
    )

  def update_image_extra(self):
    """Updates a DisplayItem's 'image_extra' (preview pdf)"""
    if self.pdf_preview != '0':
      url = signurl('ops/pdfs/%s_preview.pdf' % self.machine_name)
      metadata = urllib.urlopen(url)
      filesize = metadata.headers['content-length']
      self.di_dict['struct'][self.override]['image_extra'] = {
        'link': 'ops/pdfs/%s_preview.pdf' % self.machine_name,
        'overlay': {
          'size': self.pretty_filesize(filesize),
          'type': 'PDF'
        }
      }

  def update_machine_name(self):
    """Updates a DisplayItem's 'machine_name'"""
    self.di_dict['machine_name'] = self.machine_name

  def update_platform_icons(self):
    """
    Updates a DisplayItem's 'content' and 'unavailable-platforms'
    (platform icons)
    """
    devices = self.devices
    drms = self.drms
    plats = self.platforms
    if devices != ['0']:
      temp_icons = {}
      for device in devices:
        if device != '0':
          temp_icons[device] = {}
          for drm in drms:
            temp_icons[device][drm] = []
            for plat in plats:
              if plat in self.PLAT_ICONS[device][drm]:
                temp_icons[device][drm].append(plat)
      self.di_dict['struct'][self.override]['content'] = temp_icons

      temp_unavailable = {}
      for drm in drms:
        if drm != 'android' and drm != ['0']:
          temp_unavailable[drm] = []
          for plat in self.PLAT_ICONS['game'][drm]:
            if plat not in temp_icons['game'][drm] and plat != 'android':
              temp_unavailable[drm].append(plat)
          if temp_unavailable[drm] == []:
            del temp_unavailable[drm]
      if temp_unavailable != {}:
        self.di_dict['struct'][self.override]['unavailable-platforms'] = (
          temp_unavailable
        )

  def update_preview_image(self):
    """Updates a DisplayItem's 'preview-image (slideout image)'"""
    if self.slideout_image != '0':
      self.di_dict['struct'][self.override]['preview-image'] = (
        'images/popups/%s_slideout.jpg' % self.machine_name
      )

  def update_publishers(self):
    """Updates a DisplayItem's 'publisher-name'"""
    if self.pub_name != '0' and self.pub_url != '0':
      self.di_dict['struct'][self.override]['publishers'] = [
        {
          'publisher-name': self.pub_name,
          'publisher-url': self.pub_url
        }
      ]

  def update_slideshow_background(self):
    """Updates a DisplayItem's 'slideshow-background' (background image)"""
    if self.background_image != '0':
      if self.override == 'bundle':
        self.di_dict['struct'][self.override]['slideshow-background'] = (
          'images/bg/%s_background.jpg' % self.machine_name
        )
      else:
        self.di_dict['struct'][self.override]['slideshow-background'] = (
          'images/bg/%s_%s_background.jpg' % (self.machine_name, self.override)
        )

  def update_soundtrack_listing(self):
    """
    Updates a DisplayItem's 'soundtrack-listing' and 'soundtrack-hide-tracklist'
    """
    if self.soundtrack_listing != '0':
      self.di_dict['struct'][self.override]['soundtrack-hide-tracklist'] = True
      mp3_path = 'ops/audio/%s_preview.mp3' % self.machine_name
      url = signurl(mp3_path)
      filename, headers = urllib.urlretrieve(url)
      audiofile = MP3(filename)
      self.di_dict['struct'][self.override]['soundtrack-listing'] = [
        {
          'preview-length': str(int(math.ceil(audiofile.info.length))),
          'preview-url': mp3_path,
          'track-name': 'Excerpt',
          'track-number': '1'
        }
      ]

  def update_youtube_link(self):
    """Updates a DisplayItem's 'youtube-link'"""
    if self.youtube_link != '0':
      self.di_dict['struct'][self.override]['youtube-link'] = self.youtube_link

  def pretty_filesize(self, size):
    """
    This is a helper function for add_new_displayitem_info() and
    edit_existing_displayitem_info() to transform filesize from an int or long
    to a formatted string with a human readable filesize.

    Args:
      size (int/long): The size of a file in bytes

    Examples:
      >> pretty_filesize(100000000)
      '95.37 MB'
      >> pretty_filesize(20000000000)
      '18.63 GB'
    """
    if (size == 0):
      return '0B'
    size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB',)
    i = int(math.floor(math.log(int(size), 1024)))
    p = math.pow(1024, i)
    s = round(int(size) / p, 2)
    return '%s %s' % (s, size_name[i])

  def no_unicode(self, text):
    """
    This is a helper function for add_new_displayitem_info() and
    edit_existing_displayitem_info() to transform unicode text to their closest
    plain-formatted text equivalent for any text-related fields, most notably:
    - description-text
    - human-name
    - box-art-human-name
    - front-page-subtitle

    Args:
      text (str): A String that may or may not have Unicode (UTF-8) characters

    Returns:
      A String without any Unicode (UTF-8 characters) that the Model Importer
      can process. All '\n' characters are also replaced with <br />
    """
    return unidecode.unidecode(unicode(text, encoding="utf-8")).replace(
      '\n', '<br />')
