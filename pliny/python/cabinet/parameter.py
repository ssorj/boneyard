#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

"""
Classes for defining L{Parameters<Parameter>}
"""

from page import *

_log = logger("cabinet.parameter")

class Parameter(object):
    """
    Capture and validate named state from the request

    Parameter instances are children of L{Page}.  Parameter values are
    stored on the L{PageSession} of the current request.

    Parameter values are produced by parsing named fields from the request
    query string and L{unmarshaling<unmarshal>} them.  The raw input
    for a parameter is an array of strings, from the query-string
    variables having the L{name} of this parameter.  The parameter then
    converts the string array to a native Python object.

    Once unmarshaled, parameters are L{validated<validate>}.  During
    validation, parameters can accumulate errors.  Error information is
    used when rendering forms.

    Once validated, unmarshaled parameter values are ready for use via
    L{get} and L{set}.

    @type page: L{Page}
    @ivar page: The parent page

    @type name: basestring
    @ivar name: The parameter name

    @type app: L{Application}
    @ivar app: The application of this parameter

    @type required: boolean
    @ivar required: If C{True}, report an error on null values
    (default C{True})

    @type default_value: object
    @ivar default_value: The value produced if none is set
    (default C{None})

    @group Setup: __init__, init, delete
    @group Page attributes: get*, set*, add_error
    @group Request processing: unmarshal, validate
    @group Response generation: marshal

    @undocumented: __repr__
    """

    def __init__(self, page, name):
        """
        Create a parameter
        """

        self._page = page
        self._name = name

        self.required = True
        self.default_value = None

        assert self.app._initialized is False
        assert self.name not in self.page.parameters_by_name

        self.page.parameters.append(self)
        self.page.parameters_by_name[self.name] = self

    @property
    def page(self):
        return self._page

    @property
    def name(self):
        return self._name

    @property
    def app(self):
        return self.page.app

    def delete(self):
        """
        Delete the parameter
        """

        self.page.parameters.remove(self)
        del self.page.parameters_by_name[self.name]

    def init(self):
        """
        Initialize the parameter
        """

        _log.debug("Initializing %s", self)

        inputs_name = "render_%s_form_inputs" % self.name
        errors_name = "render_%s_errors" % self.name

        def inputs_meth(obj, session):
            return self._render_form_inputs(session)

        def errors_meth(obj, session):
            return self._render_errors(session)

        self.page.add_render_method(inputs_name, xml(inputs_meth))
        self.page.add_render_method(errors_name, xml(errors_meth))

    def get(self, session):
        """
        Get the unmarshaled value of this parameter

        If the value is None, return the result of L{get_default_value}.

        @rtype: object
        @return: The parameter value
        """

        value = self._get_value(session)

        if value.object is None:
            return self.get_default_value(session)

        return value.object

    def _get_value(self, session):
        return session._parameter_values_by_parameter[self]

    def set(self, session, _object):
        """
        Set the unmarshaled value of this parameter

        @type _object: object
        @param _object: The new parameter value
        """

        value = self._get_value(session)
        value.object = _object

    def get_default_value(self, session):
        """
        A fallback value for use if none is set on the session

        By default, this returns L{default_value}.

        @rtype: object
        @return: A default value
        """

        return self.default_value

    def get_errors(self, session):
        """
        Get all of this parameter's errors

        @rtype: iterable<L{ParameterErrorMessage}>
        @return: The errors of this parameter
        """

        value = self._get_value(session)
        return value.errors

    def add_error(self, session, message):
        """
        Add an error for this parameter

        This internally creates a L{ParameterErrorMessage}.

        @type message: basestring
        @param message: The error message
        """

        ParameterErrorMessage(session, self, message)

    def load(self, session):
        """
        Load parameter values from the request

        This internally calls L{unmarshal}.
        """

        value = self._get_value(session)

        if value.strings is None or len(value.strings) == 0:
            return

        try:
            value.object = self.unmarshal(session, value.strings)
        except Exception, e:
            args = e.__class__.__name__, str(e)
            msg = "%s: %s" % args
            self.add_error(session, msg)

    def validate(self, session):
        """
        Check the parameter value for correctness, accumulating any errors

        This internally calls L{do_validate} if a value is set on the
        request.

        If a required value is not set, this method adds an error
        indicating so and returns immediately.  Otherwise, accumulated
        errors are available from L{get_errors}.
        """

        value = self._get_value(session)

        if value.object is None:
            if self.required:
                self.add_error(session, "This input is required")

            return

        self.do_validate(session, value.object)

    def unmarshal(self, session, strings):
        """
        Convert raw query-string values to a native Python object

        Parameter subclasses must implement this method.

        @type strings: iterable<basestring>
        @param strings: String values from the query string of the request

        @rtype: object
        @return: The unmarshaled object
        """

        raise NotImplementedError()

    def marshal(self, session, _object):
        """
        Convert the native Python value to an array of strings

        Parameter subclasses must implement this method.

        @type _object: object
        @param _object: The unmarshaled object

        @rtype: iterable<basestring>
        @return: Strings for producing an HTTP query string
        """

        raise NotImplementedError()

    def do_validate(self, session, _object):
        """
        A standard extension point for parameter validation

        This is called from L{validate} after checking for missing required
        values.  Implementations should call L{add_error} if problems are
        found.

        @type _object: object
        @param _object: The unmarshaled parameter value
        """

        pass

    def __repr__(self):
        args = self.__class__.__name__, self.name
        return "%s(%s)" % args

class ParameterErrorMessage(object):
    """
    @type session: L{PageSession}
    @ivar session: The page session for which the error exists

    @type message: basestring
    @ivar message: The error message

    @undocumented: __init__, __repr__
    """

    def __init__(self, session, parameter, message):
        assert isinstance(session, PageSession)
        assert isinstance(parameter, Parameter)

        self.session = session
        self.parameter = parameter
        self.message = message

        value = self.parameter._get_value(session)
        value.errors.append(self)

    def __repr__(self):
        name = self.__class__.__name__
        args = name, self.session, self.parameter, self.message
        return "%s(%s,%s,%s)" % args

class StringParameter(Parameter):
    """
    A parameter for strings

    @type max_length: int
    @ivar max_length: The maximum allowed string length (default 256)
    """

    def __init__(self, page, name):
        super(StringParameter, self).__init__(page, name)

        self.max_length = 256

    def unmarshal(self, session, strings):
        return strings[0]

    def marshal(self, session, _object):
        return [_object]

    def do_validate(self, session, _object):
        if len(_object) > self.max_length:
            self.add_error(session, "String exceeds maximum length")

class SymbolParameter(StringParameter):
    """
    A restricted string parameter allowing only symbol characters

    Allowed characters are numbers, letters, and underscore.
    """

    def do_validate(self, session, _object):
        string = _object.replace("_", "")

        if not string.isalnum():
            self.add_error(session, "Symbol has illegal characters")

class SecretParameter(StringParameter):
    """
    A string parameter whose debug output is hidden
    """

    pass

class IntegerParameter(Parameter):
    """
    A parameter for integers
    """

    def unmarshal(self, session, strings):
        return int(strings[0])

    def marshal(self, session, _object):
        return [str(_object)]

class FloatParameter(Parameter):
    """
    A parameter for floats
    """

    def unmarshal(self, session, strings):
        return float(strings[0])

    def marshal(self, session, _object):
        return [str(_object)]

class BooleanParameter(Parameter):
    """
    A parameter for C{True} and C{False}
    """

    def unmarshal(self, session, strings):
        return strings[0] == "t"

    def marshal(self, session, _object):
        if _object is True:
            return ["t"]
        else:
            return ["f"]

class LookupParameter(Parameter):
    """
    A parameter that finds its value in a dictionary

    On marshaling, the key is retrieved from the object by its
    L{key_attribute}. 

    @type key_attribute: basestring
    @ivar key_attribute: The name of the object attribute that serves
    as the key (default "name")

    @type dictionary: dict
    @ivar dictionary: The source of lookup values; this must be set
    before L{initialization<init>}
    """

    def __init__(self, page, name):
        super(LookupParameter, self).__init__(page, name)

        self.key_attribute = "name"
        self.dictionary = None

    def init(self):
        super(LookupParameter, self).init()

        assert isinstance(self.dictionary, dict), self.dictionary

    def marshal(self, session, _object):
        return [getattr(_object, self.key_attribute)]

    def unmarshal(self, session, strings):
        key = strings[0]

        try:
            return self.dictionary[key]
        except KeyError:
            msg = "Key '%s' is not found" % key
            self.add_error(session, msg)
