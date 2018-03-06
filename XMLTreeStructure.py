from lxml import etree
from collections import Counter
 
xml = '''\
<data>
    <timestamp>...</timestamp>
    <people>
        <person>
            <name>...</name>
            <age>...</age>
        </person>
        <person>
            <name>...</name>
            <age>...</age>
            <degree />
        </person>
        <person>
            <name>...</name>
            <age>...</age>
            <degree />
            <siblings>
                <brother>...</brother>
                <brother>...</brother>
                <sister>...</sister>
            </siblings>
        </person>
    </people>
    <cities>
        <city>
            <name>...</name>
            <country>...</country>
            <continent>...</continent>
            <capital />
        </city>
        <city>
            <name>...</name>
            <country>...</country>
            <continent>...</continent>
        </city>
    </cities>
</data>
'''
 
root = etree.fromstring(xml)
 
for tag in root.iter():
    path = tree.getpath(tag)
    path = path.replace('/', '    ')
    spaces = Counter(path)
    tag_name = path.split()[-1].split('[')[0]
    tag_name = ' ' * (spaces[' '] - 4) + tag_name
    print(tag_name)