import uuid
import xmltodict

class PrimitiveElements(object):
    STRING = "S"


class PrimitiveObject(object):
    def __init__(self, element=None, value=None):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.5.1.1 Serialization of Primitive Type Objects

        A Primitive Type Object is an object that contains only a value of a
        primitive type.

        This class is designed to encompass all the primitive type objects
        defined in sectoin 2.2.5.1 in MS-PSRP.

        :param element: If specified will set the XML element character
        :param value: If specified will initialise the object with a value
        """
        self.element = element
        self.value = value


    def parse(self, xml):
        if self.element is not None or self.value is not None:
            raise Exception("Cannot parse primitive object when it has already been initialised")

        object = xmltodict.parse(xml)
        if len(object) != 1:
            raise Exception("XML string %s not a primitive object, cannot parse" % xml)

        for o in object:
            self.element = o
            self.value = object[o]

    def get_object(self):
        if self.element is None or self.value is None:
            raise Exception("Cannot create primitive object when it has not been initialised")
        object = {
            self.element: self.value
        }

        return object


class Ref(object):
    def __init__(self, ref_id=None):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.5.2.1.2 <Ref> Element

        When a particular object has been already serialized by a given
        instance of the serializer, the serializer SHOULD choose to output
        only <Ref> relemnt (instead of <Obj> element with full object data).

        :param ref_id: If set will initialise object with the reference id
        """
        self.ref_id = ref_id


    def parse(self, xml):
        if self.ref_id is not None:
            raise Exception("Cannot parse <Ref> obj when it has already been initialised")

        object = xmltodict.parse(xml)
        self.ref_id = object["Ref"]["@RefId"]


    def get_object(self):
        if self.ref_id is not None:
            raise Exception("Cannot create <Ref> obj when it has not been initialised")

        object = {
            "Ref": {
                "@RefId": self.ref_id
            }
        }

        return object


class ComplexObject(object):
    def parse(self, xml):
        if self.ref_id is not None:
            raise Exception("Cannot parse <%s> obj when it has already been initialised" % self.ref_id)

        object = xmltodict.parse(xml)
        elements = []
        for element_key in object[self.element_name]:
            # Check if the object has a reference id
            if element_key == "@RefId":
                self.ref_id = object[self.element_name][element_key]

            # Check if the element is a primitive object
            if element_key in vars(PrimitiveElements).values():
                elements.append(PrimitiveObject(element_key, object[self.element_name][element_key]))

            # Check if the element is a extended property
            if element_key == "MS":
                extended_properties = ExtendedProperties(object[self.element_name][element_key])
                #extended_properties_dict = { "MS": object[self.element_name][element_key] }
                #extended_properties.parse(xmltodict.unparse(extended_properties_dict))
                elements.append(extended_properties)

            # Check if the element is an object
            if element_key == "Obj":
                obj = Obj(object[self.element_name][element_key])
                #obj_dict = { "Obj": object[self.element_name][element_key] }
                #obj.parse(xmltodict.unparse(obj_dict))
                elements.append(obj)

        self.elements = elements


    def get_object(self):
        object = {
            self.element_name: {}
        }
        if self.ref_id is not None:
            object[self.element_name]["@RefId"] = self.ref_id

        if self.attribute is not None:
            object[self.element_name]["@N"] = self.attribute

        for element in self.elements:
            # Check if the element is a primitive object
            if isinstance(element, PrimitiveObject):
                object[self.element_name][element.element] = element.value

            # Check if the element is an extended property
            if isinstance(element, ExtendedProperties):
                object[self.element_name]["MS"] = element.get_object().values()

            # Check if the element is an Obj
            if isinstance(element, Obj):
                object[self.element_name]["Obj"] = element.get_object().values()

        return object


class Obj(ComplexObject):
    def __init__(self, elements=None):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.5.2.2 <Obj> Element

        The <Obj> element can include multiple subelements in any order

        :param elements: If specified will set the elements as a sub element
        """
        self.element_name = "Obj"
        self.elements = elements
        self.attribute = None
        if elements is not None:
            self.ref_id = uuid.uuid4()
        else:
            self.ref_id = None


class ExtendedProperties(ComplexObject):
    def __init__(self, elements=None, attribute=None):
        """
        [MS-PSRP] v16.0 2016-07-14
        2.2.5.2.9 Extended Properties
        """
        self.element_name = "MS"
        self.elements = elements
        self.attribute = attribute
        self.ref_id = None


string = '<S>This is a string</S>'
string_object = PrimitiveObject()
string_object.parse(string)
parse_string_object = PrimitiveObject(PrimitiveElements.STRING, "This is a string")

ref_xml = '<Ref RefId="RefID-0" />'
ref_object = Ref()
ref_object.parse(ref_xml)
ref_object2 = Ref("RefID-0")

extended_properties_xml = '<MS><S>Test String</S><Obj RefId="reference"><S>Another string</S></Obj></MS>'
extended_properties = ExtendedProperties()
extended_properties.parse(extended_properties_xml)

obj_xml = '<Obj RefId="RefId-0"><S>This is a string</S></Obj>'
obj_object = Obj()
obj_object.parse(obj_xml)
obj_object2 = Obj([string_object])
obj_test = obj_object.get_object()


a = ''


