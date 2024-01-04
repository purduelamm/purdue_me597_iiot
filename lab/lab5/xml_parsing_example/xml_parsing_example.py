import xml.etree.ElementTree as ET

tree = ET.parse('xml_parsing_example.xml')
root = tree.getroot()

print(root[0].attrib['instanceId'])

