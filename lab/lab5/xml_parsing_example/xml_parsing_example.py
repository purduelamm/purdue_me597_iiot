import xml.etree.ElementTree as ET

tree = ET.parse('xml_parsing_example.xml')  # create element tree object 
root = tree.getroot()  # Get root element. root is the highest level of an xml tree which includes all the elements with lower levels.

print(root[0].attrib['instanceId'])  # Header is the element with index 0 under root. root[0].attrib is a dictionary with keys of "creationTime", "sender", etc.

