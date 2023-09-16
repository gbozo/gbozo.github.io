import yaml
import re
import sys
import xml.etree.ElementTree as ET
from genm3u8 import generate_m3u8
from genepg import reduce_epg

CONFIG_PATH = 'iptv.yaml'

# Load configuration from YAML file
with open(CONFIG_PATH, 'r') as file:
    config = yaml.safe_load(file)

# Retrieve epgurl
epgurl = config['general']['epgurl']

# Fetch EPG URL
fetch_epg_url = config['general']['fetchepgurl']

# URLs section
urls = config['urls']

# Stream title filters section
title_filters = config['stream_title_filters']

# Retrieve URL filters and compile them
url_filters = [re.compile(filter) for filter in config['url_filters']]

# m3u8 channels
channels = []

# Execution starts here
m3u8_data = generate_m3u8(channels, epgurl, urls, title_filters, url_filters)

with open('iptv.m3u8', 'w') as output_file:
    output_file.write(m3u8_data)

# Fetch and parse EPG data
redacted_epg = reduce_epg(fetch_epg_url,channels)
with open('epg.xml', 'wb') as output_file:
    output_file.write(redacted_epg.encode('utf-8'))
# Sample: Print all fetched program titles
# for title in program_titles:
#     print(title)
