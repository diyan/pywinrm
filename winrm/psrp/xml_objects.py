import six
import xmltodict

class PrimitiveElements(object):
    """
    [MS-PSRP] v16.0 2016-07-14
    2.2.5.1.1 Serialization of Primitive Type Objects

    The following sections specify a complete list of primitive types
    """
    STRING = "S"
    CHARACTER = "C"
    BOOLEAN = "B"
    DATE_TIME = "DT"
    DURATION = "TS"
    UNSIGNED_BYTE = "By"
    SIGNED_BYTE = "SB"
    UNSIGNED_SHORT = "U16"
    SIGNED_SHORT = "I16"
    UNSIGNED_INT = "U32"
    SIGNED_INT = "I32"
    UNSIGNED_LONG = "U64"
    SIGNED_LONG = "I64"
    FLOAT = "Sg"
    DOUBLE = "Db"
    DECIMAL = "D"
    ARRAY_OF_BYTES = "BA"
    GUID = "G"
    URI = "URI"
    NULL_VALUE = "Nil"
    VERSION = "Version"
    XML_DOCUMENT = "XD"
    SCRIPT_BLOCK = "SBK"
    SECURE_STRING = "SS"

    # The following variables are not primitive as denoted by PSRP but have the same structure
    REF = "Ref"
    TN_REF = "TNRef"
    TYPE = "T"
    TO_STRING = "ToString"

class ComplexElements(object):
    """
    [MS-PSRP] v16.0 2016-07-14
    2.2.5.2.1 Referencing Earlier Objects

    The following sections specify a list of complex types
    """
    OBJ = "Obj"
    ADAPTED_PROPERTIES = "Props"
    EXTENDED_PROPERTY = "MS"
    TYPE_NAME = "TN"
    LIST = "LST"
    DICTIONARY = "DCT"
    DICTIONARY_ENTRY = "En"
    STACK = "STK"
    QUEUE = "QUE"


class PrimitiveObject(object):
    def __init__(self, element_name):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.5.1.1 Serialization of Primitive Type Objects

        A Primitive Type Object is an object that contains only a value of a
        primitive type.

        This class is designed to encompass all the primitive type objects
        defined in section 2.2.5.1 in MS-PSRP. As well as a few others that fit
        the same description.

        :param element_name: The XML element key, from PrimitiveElements
        """
        self.element_name = element_name
        self.attributes = {}
        self.elements = None

    def add_attribute(self, key, value):
        """
        Will add an attribute to the primitive object

        :param key: The key of the attribute
        :param value: The value of the attribute
        """
        xml_key = "@%s" % key
        if xml_key in self.attributes.keys():
            raise Exception("Cannot add an attribute with key '%s' when one is already set" % key)
        else:
            self.attributes[xml_key] = value

    def set_element(self, element):
        """
        Sets the element of the primitive object.

        :param element: The element to set
        """
        if self.elements is None:
            self.elements = element
        else:
            raise Exception("Cannot set a value when it has already been initialised")

    def parse_raw_object(self, object):
        """
        Takes in a raw dict object from an xml conversion and converts the
        entries to a PrimitiveObject

        :param object: The raw dict object from xmltodict unparse
        """

        if isinstance(object, six.string_types):
            self.set_element(object)
        else:
            for key in object:
                value = object[key]
                if key.startswith("@"):
                    self.add_attribute(key[1:], value)
                else:
                    self.set_element(value)

    def get_xml(self):
        """
        Converts the PrimitiveObject to an xml string

        :return: xml string of the PrimitiveObject
        """
        object = self.get_raw_object()
        return xmltodict.unparse(object, full_document=False)

    def get_raw_object(self):
        """
        Converts the PrimitiveObject to a raw dict to be used for later
        xml conversion

        :return: raw dict of the PrimitiveObject
        """
        object = {
            self.element_name: {}
        }

        for attribute_key in self.attributes:
            object[self.element_name][attribute_key] = self.attributes[attribute_key]

        if self.elements is not None:
            object[self.element_name]["#text"] = self.elements

        return object


class ComplexObject(object):
    def __init__(self, element_name):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.5.2 Serialization of Complex Objects

        A Complex Type Object is an object that can contain multiple objects
        as an element.

        This class is designed to encompass all the complex type objects
        defined in section 2.2.5.2 in MS-PSRP as well as a few others that fit
        the same description.

        :param element_name: The XML element key, from ComplexElements
        """
        self.element_name = element_name
        self.attributes = {}
        self.elements = {}

    def add_attribute(self, key, value):
        """
        Will add an attribute to the complex object

        :param key: The key of the attribute
        :param value: The value of the attribute
        """
        xml_key = "@%s" % key
        if xml_key in self.attributes.keys():
            raise Exception("Cannot add an attribute with key '%s' when one is already set" % key)
        else:
            self.attributes[xml_key] = value

    def add_raw_element(self, element_type, element_value, attribute_key=None, attribute_value=None):
        """
        Will create a new Object ad add the element to the ComplexObject.
        Use this method if the object has not been created.

        :param element_type: The Primitive or Complex element type
        :param element_value: The value of the element to create
        :param attribute_key: Optional: Add this optional key to the element attributes
        :param attribute_value: Optiona: Add this optional value to the element attributes
        """
        raw_primitive_elements = []
        raw_complex_elements = []
        for key, value in PrimitiveElements.__dict__.items():
            raw_primitive_elements.append(value)
        for key, value in ComplexElements.__dict__.items():
            raw_complex_elements.append(value)

        if element_type in raw_primitive_elements:
            element = PrimitiveObject(element_type)
            element.set_element(element_value)
        elif element_type in raw_complex_elements:
            element = element_value
        else:
            raise Exception("Unknown element type '%s', cannot add element" % element_type)

        if attribute_key is not None and attribute_value is None:
            raise Exception("The attribute value needs to be set when adding an attribute")
        elif attribute_key is None and attribute_value is not None:
            raise Exception("The attribute key needs to be set when adding an attribute")
        elif attribute_key is not None and attribute_value is not None:
            element.add_attribute(attribute_key, attribute_value)

        self.add_initialised_element(element)

    def add_initialised_element(self, element):
        """
        Will add the element to the ComplexObject. Use this method if the
        object is already a ComplexObject or PrimitiveObject

        :param element: A Complex or Primitive Object
        """
        existing_value = self.elements.get(element.element_name, None)
        if existing_value is not None:
            if isinstance(existing_value, list):
                existing_value.append(element)
                new_value = existing_value
            else:
                new_value = [existing_value, element]
            self.elements[element.element_name] = new_value
        else:
            self.elements[element.element_name] = element

    def parse_raw_object(self, object):
        """
        Takes in a raw dict object from an xml conversion and converts the
        entries to a ComplexObject

        :param object: The raw dict object from xmltodict unparse
        """
        for element_key in object:
            element_value = object[element_key]

            raw_primitive_elements = []
            raw_complex_elements = []
            for key, value in PrimitiveElements.__dict__.items():
                raw_primitive_elements.append(value)
            for key, value in ComplexElements.__dict__.items():
                raw_complex_elements.append(value)

            # Check if the entry is an attribute
            if element_key.startswith("@"):
                self.add_attribute(element_key[1:], element_value)
            elif element_key in raw_primitive_elements:
                if isinstance(element_value, list):
                    for primitive_entry in element_value:
                        primitive_object = PrimitiveObject(element_key)
                        primitive_object.parse_raw_object(primitive_entry)
                        self.add_initialised_element(primitive_object)
                else:
                    primitive_object = PrimitiveObject(element_key)
                    primitive_object.parse_raw_object(element_value)
                    self.add_initialised_element(primitive_object)
            elif element_key in raw_complex_elements:
                if isinstance(element_value, list):
                    for complex_entry in element_value:
                        complex_object = ComplexObject(element_key)
                        complex_object.parse_raw_object(complex_entry)
                        self.add_initialised_element(complex_object)
                else:
                    complex_object = ComplexObject(element_key)
                    complex_object.parse_raw_object(element_value)
                    self.add_initialised_element(complex_object)
            else:
                raise Exception("Could not determine xml key '%s'" % element_key)

    def parse_xml(self, xml):
        """
        Takes in a raw xml string and converts the string to a ComplexObject

        :param xml: The xml string to convert
        """
        if self.elements != {} or self.attributes != {}:
            raise Exception("Cannot parse %s xml string when it has already been initialised" % self.element_name)

        raw_object = xmltodict.parse(xml)
        self.parse_raw_object(raw_object[self.element_name])

    def get_xml(self):
        """
        Converts the ComplexObject to an xml string

        :return: xml string of the ComplexObject
        """
        object = self.get_raw_object()
        return xmltodict.unparse(object, full_document=False)

    def get_raw_object(self):
        """
        Converts the ComplexObject to a raw dict to be used for later
        xml conversion

        :return: raw dict of the ComplexObject
        """
        object = {
            self.element_name: {}
        }

        for attribute_key in self.attributes:
            object[self.element_name][attribute_key] = self.attributes[attribute_key]

        for child_element_name in self.elements:
            child_element = self.elements[child_element_name]
            if isinstance(child_element, list):
                value = []
                for element in child_element:
                    new_value = element.get_raw_object()[child_element_name]
                    value.append(new_value)
            else:
                value = child_element.get_raw_object()[child_element_name]

            object[self.element_name][child_element_name] = value

        return object
