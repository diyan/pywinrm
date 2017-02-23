import pytest

from winrm.psrp.xml_objects import PrimitiveElements, PrimitiveObject, ComplexElements, ComplexObject


def test_generate_primitive_object():
    expected = '<S>string</S>'

    actual_object = PrimitiveObject(PrimitiveElements.STRING)
    actual_object.set_element("string")
    actual = actual_object.get_xml()

    assert actual == expected


def test_generate_primitive_object_with_attributes():
    expected = '<C Key="Value">string</C>'

    actual_object = PrimitiveObject(PrimitiveElements.CHARACTER)
    actual_object.set_element("string")
    actual_object.add_attribute("Key", "Value")
    actual = actual_object.get_xml()

    assert actual == expected


def test_generate_primitive_object_no_value():
    expected = '<Nil></Nil>'

    actual_object = PrimitiveObject(PrimitiveElements.NULL_VALUE)
    actual = actual_object.get_xml()

    assert actual == expected


def test_generate_primitive_object_fail_with_same_attribute():
    with pytest.raises(Exception) as excinfo:
        o = PrimitiveObject(PrimitiveElements.STRING)
        o.add_attribute("Key", "Value")
        o.add_attribute("Key", "Value")

    assert "Cannot add an attribute with key 'Key' when one is already set" in str(excinfo.value)


def test_generate_primitive_object_fail_set_two_elements():
    with pytest.raises(Exception) as excinfo:
        o = PrimitiveObject(PrimitiveElements.STRING)
        o.set_element("a")
        o.set_element("a")

    assert "Cannot set a value when it has already been initialised" in str(excinfo.value)


def test_complex_object():
    test_xml = """
    <Obj RefId="0">
        <MS>
            <Obj N="ApplicationPrivateData" RefId="1">
                <TN RefId="0">
                    <T>System.Management.Automation.PSPrimitiveDictionary</T>
                    <T>System.Collections.Hashtable</T>
                    <T>System.Object</T>
                </TN>
                <DCT>
                    <En>
                        <S N="Key">BashPrivateData</S>
                        <Obj N="Value" RefId="2">
                            <TNRef RefId="0" />
                            <DCT>
                                <En>
                                    <S N="Key">BashVersion</S>
                                    <Version N="Value">2.0</Version>
                                </En>
                            </DCT>
                        </Obj>
                    </En>
                </DCT>
            </Obj>
            <Obj N="SecondPrivateData" RefId="2">
                <LST>
                    <S>test string</S>
                    <S>second test string</S>
                </LST>
            </Obj>
        </MS>
    </Obj>
    """
    actual_object = ComplexObject(ComplexElements.OBJ)
    actual_object.parse_xml(test_xml)
    actual_exported_object = actual_object.get_raw_object()

    assert actual_object.attributes == {"@RefId": "0"}
    assert actual_object.element_name == 'Obj'
    assert actual_exported_object == {
        'Obj': {
            '@RefId': '0',
            'MS': {
                'Obj': [
                    {
                        '@N': 'ApplicationPrivateData',
                        '@RefId': '1',
                        'DCT': {
                            'En': {
                                'Obj': {
                                    '@N': 'Value',
                                    '@RefId': '2',
                                    'DCT': {
                                        'En': {
                                            'S': {
                                                '#text': 'BashVersion',
                                                '@N': 'Key'
                                            },
                                            'Version': {
                                                '#text': '2.0',
                                                '@N': 'Value'
                                            }
                                        }
                                    },
                                    'TNRef': {
                                        '@RefId': '0'
                                    }
                                },
                                'S': {
                                    '#text': 'BashPrivateData',
                                    '@N': 'Key'
                                }
                            }
                        },
                        'TN': {
                            '@RefId': '0',
                            'T': [
                                {'#text': 'System.Management.Automation.PSPrimitiveDictionary'},
                                {'#text': 'System.Collections.Hashtable'},
                                {'#text': 'System.Object'}
                            ]
                        }
                    }, {
                        '@N': 'SecondPrivateData',
                        '@RefId': '2',
                        'LST': {
                            'S': [
                                {'#text': 'test string'},
                                {'#text': 'second test string'}
                            ]
                        }
                    }
                ]
            }
        }
    }


def test_complex_object_nested_types():
    test_xml = """
    <Obj RefId="0">
        <MS>
            <TN RefId="0">
                <T>System.Management.Automation.PSPrimitiveDictionary</T>
                <T>System.Collections.Hashtable</T>
                <T>System.Object</T>
            </TN>
            <S N="Key">BashVersion</S>
        </MS>
    </Obj>
    """
    actual_object = ComplexObject(ComplexElements.OBJ)
    actual_object.parse_xml(test_xml)
    extended_property = actual_object.elements['MS']
    string = extended_property.elements['S']
    type_names = extended_property.elements['TN']
    type_name = type_names.elements['T'][0]

    assert isinstance(actual_object, ComplexObject)
    assert isinstance(extended_property, ComplexObject)
    assert isinstance(string, PrimitiveObject)
    assert isinstance(type_names, ComplexObject)
    assert isinstance(type_name, PrimitiveObject)


def test_add_raw_primitive_element_no_attributes():
    actual_object = ComplexObject(ComplexElements.LIST)
    actual_object.add_raw_element(PrimitiveElements.DATE_TIME, "2017")
    assert actual_object.attributes == {}
    assert actual_object.element_name == 'LST'
    assert isinstance(actual_object.elements['DT'], PrimitiveObject)
    assert actual_object.get_raw_object() == {
        'LST': {
            'DT': {
                '#text': '2017'
            }
        }
    }


def test_add_raw_complex_element_with_attribute():
    test_type_name = ComplexObject(ComplexElements.TYPE_NAME)
    test_type_name.add_raw_element(PrimitiveElements.TYPE, "System.Object")
    actual_object = ComplexObject(ComplexElements.LIST)
    actual_object.add_raw_element(ComplexElements.TYPE_NAME, test_type_name, "RefId", "1")
    assert actual_object.attributes == {}
    assert actual_object.element_name == 'LST'
    assert isinstance(actual_object.elements['TN'], ComplexObject)
    assert actual_object.get_raw_object() == {
        'LST': {
            'TN': {
                '@RefId': "1",
                'T': {
                    '#text': 'System.Object'
                }
            }
        }
    }


def test_add_raw_complex_element_with_invalid_type():
    with pytest.raises(Exception) as excinfo:
        test_type_name = ComplexObject(ComplexElements.LIST)
        test_type_name.add_raw_element('Fake', '')

    assert "Unknown element type 'Fake', cannot add element" in str(excinfo.value)


def test_add_raw_element_with_attribute_key_no_value():
    with pytest.raises(Exception) as excinfo:
        test_type_name = ComplexObject(ComplexElements.LIST)
        test_type_name.add_raw_element(PrimitiveElements.DATE_TIME, "2017", 'a')

    assert "The attribute value needs to be set when adding an attribute" in str(excinfo.value)


def test_add_raw_element_with_attribute_value_no_key():
    with pytest.raises(Exception) as excinfo:
        test_type_name = ComplexObject(ComplexElements.LIST)
        test_type_name.add_raw_element(PrimitiveElements.DATE_TIME, "2017", attribute_value="a")

    assert "The attribute key needs to be set when adding an attribute" in str(excinfo.value)


def test_generate_complex_object_fail_with_same_attribute():
    with pytest.raises(Exception) as excinfo:
        o = ComplexObject(ComplexElements.OBJ)
        o.add_attribute("Key", "Value")
        o.add_attribute("Key", "Value")

    assert "Cannot add an attribute with key 'Key' when one is already set" in str(excinfo.value)


def test_parse_complex_object_with_invalid_element_type():
    test_xml = "<Obj><a></a></Obj>"
    with pytest.raises(Exception) as excinfo:
        o = ComplexObject(ComplexElements.OBJ)
        o.parse_xml(test_xml)

    assert "Could not determine xml key 'a'" in str(excinfo.value)


def test_parse_complex_object_already_initialised():
    with pytest.raises(Exception) as excinfo:
        o = ComplexObject(ComplexElements.OBJ)
        o.parse_xml("<Obj><S>a</S></Obj>")
        o.parse_xml("<Obj><S>a</S></Obj>")

    assert "Cannot parse Obj xml string when it has already been initialised" in str(excinfo.value)


def test_get_complex_object_xml():
    test_type_name = ComplexObject(ComplexElements.TYPE_NAME)
    test_type_name.add_raw_element(PrimitiveElements.TYPE, "System.Test")
    test_type_name.add_raw_element(PrimitiveElements.TYPE, "System.Object")

    test_object = ComplexObject(ComplexElements.EXTENDED_PROPERTY)
    test_object.add_initialised_element(test_type_name)

    expected = '<MS><TN><T>System.Test</T><T>System.Object</T></TN></MS>'
    actual = test_object.get_xml()

    assert actual == expected
