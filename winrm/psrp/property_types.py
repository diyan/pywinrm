
class PropertyType(object):
    """
    Helper class for all property types
    """
    attribute_key = None
    attribute_value = None
    value = None

    def __init__(self, value=None, attribute_key=None, attribute_value=None):
        # allow you to initialise an empty object to parse later
        if value is not None:
            self.value = value

            if attribute_key is not None:
                self.attribute_key = attribute_key
                self.attribute_value = attribute_value


    def get_data(self):
        if self.value is None:
            raise Exception("Cannot get data of property type as the value has not been initialised")
        data = {
            "#text": self.value
        }

        if self.attribute_key is not None:
            data["@" + self.attribute_key] = self.attribute_value

        return data


    def parse_data(self, data, attribute_key=None):
        self.value = data["#text"]
        if attribute_key is not None:
            self.attribute_key = attribute_key
            self.attribute_value = data["@" + attribute_key]

class Version(PropertyType):
    """
    [MS-PSRP] v16.0 2016-07-14
    2.2.5.1.21 Version

    Represents a version number that consists of two to four components: major,
    minor, build, and revisions
    """