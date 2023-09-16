import configparser
import re
import requests
import sys

CONFIG_PATH = 'iptv.ini'

# Load configuration file
config = configparser.ConfigParser()
config.read(CONFIG_PATH)

# Retrieve epgurl
epgurl = config['General']['epgurl']

# URLs section
urls = sorted(config['URLs'].items(), key=lambda x: int(re.search(r'\d+', x[0]).group()))

# Stream title filters section
title_filters = sorted(config['StreamTitleFilters'].items(), key=lambda x: int(re.search(r'\d+', x[0]).group()))

# Retrieve patterns
url_filters = [re.compile(filter) for filter in config['URLFilters'].values()]

def generate_m3u8():
    output = f"#EXTM3U url-tvg=\"{epgurl}\"\n"
    global_unique_m3u8 = set()

    for key, url_line in urls:
        url_parts = url_line.split('|', 2)
        url = url_parts[0].strip() if len(url_parts) > 0 else None
        custom_stream_name = url_parts[1].strip() if len(url_parts) > 1 else None
        epgname = url_parts[2].strip() if len(url_parts) > 2 else None

        response = requests.get(url)
        if not response.ok:
            continue

        content = response.text
        if custom_stream_name:
            stream_name = custom_stream_name
        else:
            stream_name_match = re.search(r'<title>([^<]+)<\/title>', content, re.I)
            stream_name = stream_name_match.group(1) if stream_name_match else 'Unknown Stream'
            stream_name = ''.join(filter(lambda x: ord(x) < 128, stream_name))
            
            for _, filter_ in title_filters:
                stream_name = re.sub(r'\b' + re.escape(filter_) + r'\b', '', stream_name, flags=re.I)
            
            stream_name = stream_name.replace('|', '').strip()

        lc_stream_name = stream_name.lower()
        if re.search(r'\.m3u8?$', url, re.I):
            output_line = f"#EXTINF:-1 tvg-name=\"{epgname if epgname else lc_stream_name}\",{stream_name}\n{url}\n"
            output += output_line
        else:                     
            # Check each link against all patterns
            for link in re.findall(r'(https?:\/\/[^\s]+?\.m3u8?)', content, re.I):
                if any(filter.match(link) for filter in url_filters):                    
                    continue
                if link not in global_unique_m3u8:
                    output_line = f"#EXTINF:-1 tvg-name=\"{epgname if epgname else lc_stream_name}\",{stream_name}\n{link}\n"
                    output += output_line
                    global_unique_m3u8.add(link)
    return output


# Execution starts here
m3u8_data = generate_m3u8()

# Check if stdout is redirected
if sys.stdout.isatty():
    # Not redirected, write to a file
    with open('iptv.m3u8', 'w') as output_file:
        output_file.write(m3u8_data)
else:
    # Redirection or piping is occurring, print to stdout
    print(m3u8_data)
    
