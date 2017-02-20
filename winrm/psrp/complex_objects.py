class TypeNames(object):

    def __init__(self):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.5.2.3 Type Names
        """
        self.xml_element = "TN"
        self.properties = []

    def __add__(self, property):
        self.properties.append({"T": property})

    def parse_properties(self, string):
        a = ''

    def get_dict(self):
        dict = {
            self.xml_element: {
                "@RefId": "RefId-0",
                "#text": self.properties
            }
        }

        return dict

class ToString(object):

    def __init__(self):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.5.2.4 ToString
        """
        self.xml_element = "ToString"


class ExtendedProperties(object):

    def __init__(self):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.5.2.9 Extended Properties
        """
        self.xml_element = "MS"
        self.properties = []

    def __add__(self, property):
        self.properties.append(property)

    def parse_properties(self, string):
        a = ''

    def get_dict(self):
        dict = {
            self.xml_element: self.properties
        }

        return dict