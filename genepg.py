import requests
from lxml import etree
import logging
import re
import base64
from datetime import datetime

# Configure the logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_string(s):
    """Normalize a string by converting to lowercase, removing special characters and stripping spaces."""
    return re.sub(r'[^a-z0-9]', '', s.lower()).strip()

def convert_image_to_data_uri(url: str) -> str:
    """Convert an image from a URL to a data URI."""
    response = requests.get(url)
    response.raise_for_status()

    # Get the image type from the Content-Type header (e.g., 'image/png', 'image/jpeg')
    image_type = response.headers.get('content-type', '').split('/')[-1]
    
    # Convert image content to base64
    encoded_image = base64.b64encode(response.content).decode('utf-8')

    # Return the data URI
    return f"data:image/{image_type};base64,{encoded_image}"

def reduce_epg(fetch_epg_url: str, channels: list) -> str:
    """Fetch the XMLTV EPG data and reduce it to include only the specified channels."""

    # Normalize channel list for comparison
    normalized_channels = [normalize_string(channel) for channel in channels]

    logger.info(f"Fetching EPG data from: {fetch_epg_url}")
    
    # Fetch EPG XML data
    response = requests.get(fetch_epg_url)
    response.raise_for_status()  # Raise exception if not a 2xx response

    # Parse EPG XML data using lxml
    root = etree.fromstring(response.content)

    # Process each channel
    removed_channels_count = 0
    retained_channels = []
    for channel in root.xpath('//channel'):
        display_name = channel.xpath('display-name/text()')[0] if channel.xpath('display-name/text()') else "Unknown"
        normalized_display_name = normalize_string(display_name)

        # Log channel properties and attributes
        # logger.info(f"Processing channel: {display_name}")
        # logger.info(f"Attributes: {channel.attrib}")
        # for child in channel:
        #     logger.info(f"Property {child.tag}: {child.text}")

        if normalized_display_name not in normalized_channels:
            root.remove(channel)
            removed_channels_count += 1
        else:
            # Handle icon
            icon = channel.find('icon')
            if icon is not None and 'src' in icon.attrib:
                try:
                    icon_url = icon.attrib['src']
                    #logger.info(f"Processing icon for channel {display_name}: {icon_url}")
                    icon.attrib['src'] = convert_image_to_data_uri(icon_url)
                except Exception as e:
                    logger.warning(f"Failed to process icon for channel {display_name}: {str(e)}")                    
            retained_channels.append(display_name)

        # Remove display-name child elements containing only numbers
        for display_name in channel.findall('display-name'):
            if display_name.text and display_name.text.isdigit():
                channel.remove(display_name)

    logger.info(f"Removed {removed_channels_count} unwanted channels.")
    logger.info(f"Retained channels: {', '.join(retained_channels)}")

    # Gather IDs of remaining channels
    channel_ids = [channel.get('id') for channel in root.xpath('//channel')]

    # Remove programs of channels that aren't in our list
    removed_programs_count = 0
    for program in root.xpath('//programme'):
        if program.get('channel') not in channel_ids:
            root.remove(program)
            removed_programs_count += 1

    logger.info(f"Removed {removed_programs_count} programs not associated with the desired channels.")

    # Remove children of remaining programmes where lang is not "gre"
    for program in root.xpath('//programme'):
        for child in list(program):  # Using list() to ensure we're not modifying while iterating
            if child.get('lang') != "gre":
                program.remove(child)
    
    # Remove lang attributes from children of the programme elements
    for program in root.xpath('//programme'):
        for child in program:
            if 'lang' in child.attrib:
                del child.attrib['lang']

    root.set("generator-info-name", "Greek TV")
    root.set("generator-info-url", "https://gbozo.github.io/tv")
    
     # Add generation timestamp at the end
    timestamp_comment = etree.Comment(f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    root.append(timestamp_comment)

    # Serialize with the XML declaration and the DOCTYPE definition
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    doctype = '<!DOCTYPE tv SYSTEM "xmltv.dtd">\n'
    serialized_xml = etree.tostring(root, encoding='utf-8', pretty_print=True).decode('utf-8')
    
    # Return redacted XML as string
    return xml_declaration + doctype + serialized_xml    
