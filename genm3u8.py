import requests
import re

def generate_m3u8(channels, epgurl, urls, title_filters, url_filters):
    output = f"#EXTM3U url-tvg=\"{epgurl}\"\n"
    global_unique_m3u8 = set()

    for url_data in urls:
        url = url_data["url"]
        custom_stream_name = url_data.get("displayname", None)
        epgname = url_data.get("tvg-name", None)

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
            
            for filter_ in title_filters:
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
        channels.append(epgname if epgname else lc_stream_name)
    return output
