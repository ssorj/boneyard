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

import argparse as _argparse
import collections.abc as _abc
import mistune as _mistune
import os as _os
import shutil as _shutil
import sys as _sys
import yaml as _yaml
import yamlinclude as _yamlinclude

from xml.sax.saxutils import escape as _xml_escape

class Epithet:
    def __init__(self, config_dir, input_dir, output_dir, verbose=False, quiet=False):
        self.config_dir = config_dir
        self.input_dir = input_dir
        self.output_dir = output_dir

        self.verbose = verbose
        self.quiet = quiet

        self.config = {
            "app": self,
        }

    def init(self):
        try:
            with open(_os.path.join(self.config_dir, "config.py")) as f:
                exec(f.read(), self.config)
        except Exception as e:
            self.warn("Failed to load configuration: {}", e)

        _yamlinclude.YamlIncludeConstructor.add_to_loader_class(loader_class=_yaml.FullLoader, base_dir=self.input_dir)

        with open(_os.path.join(self.input_dir, "model.yaml")) as f:
            data = _yaml.load(f, Loader=_yaml.FullLoader)

        self.model = _Model(self, data)
        self.model.load()
        self.model.process()

    def render(self):
        renderer = _HtmlRenderer(self, static_dir=self.config.get("static_dir"))
        renderer.render(self.model)

    def info(self, message, *args):
        if self.verbose:
            print(message.format(*args))

    def notice(self, message, *args):
        if not self.quiet:
            print(message.format(*args))

    def warn(self, message, *args):
        print("Warning:", message.format(*args))

class _ModelObject:
    def __init__(self, model, parent, name, data):
        assert isinstance(model, _Model), model
        assert isinstance(parent, _ModelObject) or parent is None, parent
        assert isinstance(name, str), name
        assert isinstance(data, dict), data

        self.model = model
        self.parent = parent
        self.name = name
        self.data = data

        self.child_attributes = list()
        self.children = list()
        self.children_by_name = dict()

    def __repr__(self):
        return f"{self.__class__.__name__[1:]}({self.name})"

    def load(self):
        self.model.app.info("Loading {}", self)

        self.summary = self.data.get("summary")
        self.description = self.data.get("description")

        if self.description and self.summary is None:
            try:
                self.summary = self.description[0:self.description.index(".")]
            except ValueError:
                pass

    def load_children(self, attribute, cls):
        children = list()
        children_by_name = dict()

        if self.data and attribute in self.data:
            child_data = self.data[attribute]

            if child_data is not None:
                for name, value in child_data.items():
                    if value is None:
                        value = {}

                    obj = cls(self.model, self, name, value)

                    children.append(obj)
                    children_by_name[name] = obj

        setattr(self, attribute, children)
        setattr(self, f"{attribute}_by_name", children_by_name)

        self.child_attributes.append(attribute)
        self.children.extend(children)
        self.children_by_name.update(children_by_name)

        for child in children:
            child.load()

    def process(self):
        self.model.app.info("Processing {}", self)

        for child in self.children:
            child.process()

    def lookup(self, path):
        assert self is not self.model

        if path is None:
            return

        obj = self.parent

        if path.startswith("/"):
            obj = self.model
            path = path[1:]

        for elem in path.split("/"):
            obj = obj.children_by_name[elem]

        return obj

class _Model(_ModelObject):
    def __init__(self, app, data):
        super().__init__(self, None, data.get("name"), data)

        self.app = app

    def load(self):
        super().load()

        self.load_children("namespaces", _Namespace)

class _Namespace(_ModelObject):
    def load(self):
        super().load()

        self.load_children("functions", _Function)
        self.load_children("types", _Type)
        self.load_children("enumerations", _Enumeration)
        self.load_children("constants", _Constant)

class _Parameter(_ModelObject):
    def load(self):
        super().load()

        self.type = self.data.get("type")
        self.item_type = self.data.get("item_type")
        self.key_type = self.data.get("key_type")
        self.value = self.data.get("value")
        self.mutable = self.data.get("mutable", False)
        self.nullable = self.data.get("nullable", False)

    def process(self):
        super().process()

        self.type = self.lookup(self.type)
        self.item_type = self.lookup(self.item_type)
        self.key_type = self.lookup(self.key_type)

class _Constant(_Parameter):
    pass

class _Function(_ModelObject):
    def load(self):
        super().load()

        self.load_children("inputs", _Input)
        self.load_children("outputs", _Output)
        self.load_children("error-conditions", _ErrorCondition)

class _Input(_Parameter):
    def load(self):
        super().load()

        self.optional = self.data.get("optional", False)

class _Output(_Parameter):
    pass

class _ErrorCondition(_Parameter):
    pass

class _Type(_ModelObject):
    def load(self):
        super().load()

        self.type = self.data.get("type")

        self.load_children("properties", _Property)
        self.load_children("methods", _Method)

    def process(self):
        super().process()

        self.type = self.lookup(self.type)

    def get_types(self):
        types = list()
        type = self

        while type is not None:
            types.append(type)
            type = type.type

        return types[::-1]

    @property
    def virtual_properties(self):
        for type in self.get_types():
            for prop in type.properties:
                yield prop

    @property
    def virtual_methods(self):
        for type in self.get_types():
            for meth in type.methods:
                yield meth

class _Property(_Parameter):
    pass

class _Method(_Function):
    pass

class _Enumeration(_ModelObject):
    def load(self):
        super().load()

        self.load_children("values", _EnumerationValue)

class _EnumerationValue(_ModelObject):
    pass

class _HtmlRenderer:
    def __init__(self, app, static_dir=None):
        self.app = app
        self.static_dir = static_dir

        self.render_functions = {
            _Type: self.render_type,
        }

    def get_ancestors(self, obj):
        ancestors = list()
        ancestor = obj.parent

        while ancestor is not None:
            ancestors.append(ancestor)
            ancestor = ancestor.parent

        return ancestors[::-1]

    def get_path(self, obj):
        return _os.path.join('output', *(x.name for x in self.get_ancestors(obj)), f"{obj.name}.html")

    def get_href(self, obj):
        return f"file:{_os.path.abspath(self.get_path(obj))}"

    def get_title(self, obj):
        return f"{obj.__class__.__name__[1:]} <span class=\"object-name\">{obj.name}</span>"

    def get_short_title(self, obj):
        return obj.name

    def get_link(self, obj):
        return f"<a href=\"{self.get_href(obj)}\">{self.get_title(obj)}</a>"

    def get_short_link(self, obj):
        return f"<a href=\"{self.get_href(obj)}\">{self.get_short_title(obj)}</a>"

    def get_type_link(self, obj):
        if isinstance(obj.type, str):
            return self.get_short_title(obj)
        else:
            return f"<a href=\"{self.get_href(obj.type)}\">{self.get_short_title(obj)}</a>"

    def get_path_nav(self, obj):
        pieces = list()

        for ancestor in self.get_ancestors(obj):
            pieces.append(self.get_link(ancestor))
            pieces.append(" <span class=\"path-separator\">&#8250;</span> ")

        pieces.append(self.get_title(obj))

        return "<nav>{}</nav>".format("".join(pieces))

    def get_summary(self, obj):
        return _mistune.html(obj.summary)

    def get_type(self, obj):
        return self.get_short_link(obj.type)

    def get_description(self, obj):
        return _mistune.html(obj.description)

    def get_value(self, obj):
        return _mistune.html(obj.value) if isinstance(obj.value, str) else obj.value

    def render(self, model):
        for name in _os.listdir(self.static_dir):
            from_path = _os.path.join(self.static_dir, name)
            to_path = _os.path.join(self.app.output_dir, name)

            _os.makedirs(_os.path.dirname(to_path), exist_ok=True)

            if _os.path.isdir(from_path):
                _shutil.copytree(from_path, to_path, dirs_exist_ok=True)
            else:
                _shutil.copy(from_path, to_path)

        self.render_object(model)

    def render_object(self, obj):
        self.render_functions.get(type(obj), self.render_object_default)(obj)

    def render_object_default(self, obj):
        with _HtmlPage(self, obj) as out:
            self.render_object_overview(obj, out)
            self.render_object_children(obj, out)

        for child in obj.children:
            self.render(child)

    def render_object_overview(self, obj, out):
        out.write(_html_elem("h1", self.get_title(obj)))
        out.write(self.get_description(obj))

    def render_object_children(self, obj, out):
        for attribute in obj.child_attributes:
            if not getattr(obj, attribute):
                continue

            out.write(_html_elem("h3", attribute.capitalize()))

            headings = "Name", "Summary"
            rows = ((self.get_short_link(child), self.get_summary(child)) for child in getattr(obj, attribute))

            out.write(_html_table(rows, headings=headings, class_="epithet children"))

    def render_type(self, obj):
        with _HtmlPage(self, obj) as out:
            self.render_object_overview(obj, out)

            properties = list(obj.virtual_properties)
            methods = list(obj.virtual_methods)

            if properties:
                self.render_type_properties(properties, out)

            if methods:
                self.render_type_methods(methods, out)

        for child in obj.children:
            self.render(child)

    def render_type_properties(self, properties, out):
        out.write(_html_elem("h3", "Properties"))

        headings = "Name", "Summary", "Type", "Default value", "Mutable", "Nullable"
        rows = ((self.get_short_link(prop),
                 self.get_summary(prop),
                 self.get_type(prop),
                 self.get_value(prop),
                 _html_tick_box(prop.mutable),
                 _html_tick_box(prop.nullable),
                 ) for prop in properties)

        out.write(_html_table(rows, headings=headings, class_="epithet properties"))

    def render_type_methods(self, methods, out):
        out.write(_html_elem("h3", "Methods"))

        def params(meth, attribute):
            for param in getattr(meth, attribute):
                if getattr(param, "optional", False):
                    yield _html_elem("span", "[{}]".format(self.get_type_link(param)), class_="optional-input")
                else:
                    yield self.get_type_link(param)

        headings = "Name", "Summary", "Inputs", "Outputs"
        rows = ((self.get_short_link(meth),
                 self.get_summary(meth),
                 ", ".join(params(meth, "inputs")),
                 ", ".join(params(meth, "outputs")),
                 ) for meth in methods)

        out.write(_html_table(rows, headings=headings, class_="epithet methods"))

class _HtmlPage:
    def __init__(self, renderer, obj):
        self.renderer = renderer
        self.obj = obj

        self.pieces = list()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        path = self.renderer.get_path(self.obj)
        parent_dir = _os.path.dirname(path)

        if parent_dir and not _os.path.exists(parent_dir):
            _os.makedirs(parent_dir)

        with open(path, "w") as f:
            f.write(_html_page.format(site_url=f"file:{_os.path.abspath(self.renderer.app.output_dir)}",
                                      nav=self.renderer.get_path_nav(self.obj),
                                      body="".join(self.pieces)))

    def write(self, content):
        self.pieces.append(content)

class _Command(object):
    def __init__(self, home=None, name=None, standard_args=True):
        self.home = home
        self.name = name
        self.standard_args = standard_args

        self.parser = _argparse.ArgumentParser()
        self.parser.formatter_class = _argparse.RawDescriptionHelpFormatter

        self.args = None

        if self.name is None:
            self.name = self.parser.prog

        self.id = self.name

        self.quiet = False
        self.verbose = False
        self.init_only = False

    def add_argument(self, *args, **kwargs):
        self.parser.add_argument(*args, **kwargs)

    def add_subparsers(self, *args, **kwargs):
        return self.parser.add_subparsers(*args, **kwargs)

    @property
    def description(self):
        return self.parser.description

    @description.setter
    def description(self, text):
        self.parser.description = text.strip()

    @property
    def epilog(self):
        return self.parser.epilog

    @epilog.setter
    def epilog(self, text):
        self.parser.epilog = text.strip()

    def load_config(self):
        dir_ = _os.path.expanduser("~")
        config_file = _os.path.join(dir_, ".config", self.name, "config.py")
        config = dict()

        if _os.path.exists(config_file):
            entries = _runpy.run_path(config_file, config)
            config.update(entries)

        return config

    def init(self, args=None):
        assert self.args is None

        self.args = self.parser.parse_args(args)

        if self.standard_args:
            self.quiet = self.args.quiet
            self.verbose = self.args.verbose
            self.init_only = self.args.init_only

    def run(self):
        raise NotImplementedError()

    def main(self, args=None):
        self.init(args)

        assert self.args is not None

        if self.init_only:
            return

        try:
            self.run()
        except KeyboardInterrupt: # pragma: nocover
            pass

    def info(self, message, *args):
        if self.verbose:
            self.print_message(message, *args)

    def notice(self, message, *args):
        if not self.quiet:
            self.print_message(message, *args)

    def warn(self, message, *args):
        message = "Warning: {0}".format(message)
        self.print_message(message, *args)

    def error(self, message, *args):
        message = "Error! {0}".format(message)
        self.print_message(message, *args)

    def fail(self, message, *args):
        self.error(message, *args)
        _sys.exit(1)

    def print_message(self, message, *args):
        message = message[0].upper() + message[1:]
        message = message.format(*args)
        message = "{0}: {1}".format(self.id, message)

        _sys.stderr.write("{0}\n".format(message))
        _sys.stderr.flush()

class EpithetCommand(_Command):
    def __init__(self, home=None):
        super().__init__(home=home, name="epithet", standard_args=False)

        self.description = "Generate static websites from Markdown and Python"

        subparsers = self.add_subparsers(title="subcommands")

        common = _argparse.ArgumentParser()
        common.add_argument("--verbose", action="store_true",
                            help="Print detailed logging to the console")
        common.add_argument("--quiet", action="store_true",
                            help="Print no logging to the console")
        common.add_argument("--init-only", action="store_true",
                            help=_argparse.SUPPRESS)

        common_io = _argparse.ArgumentParser(add_help=False)
        common_io.add_argument("config_dir", metavar="CONFIG-DIR",
                        help="Read config files from CONFIG-DIR")
        common_io.add_argument("input_dir", metavar="INPUT-DIR",
                        help="The base directory for input files")
        common_io.add_argument("output_dir", metavar="OUTPUT-DIR",
                        help="The base directory for output files")

        init = subparsers.add_parser("init", parents=(common,), add_help=False,
                                     help="Prepare an input directory")
        init.set_defaults(command_fn=self.init_command)
        init.add_argument("config_dir", metavar="CONFIG-DIR",
                          help="Read config files from CONFIG-DIR")
        init.add_argument("input_dir", metavar="INPUT-DIR",
                          help="Place default input files in INPUT-DIR")

        render = subparsers.add_parser("render", parents=(common, common_io), add_help=False,
                                       help="Generate output files")
        render.set_defaults(command_fn=self.render_command)
        render.add_argument("--serve", type=int, metavar="PORT",
                            help="Serve the site and rerender when input files change")

    def init(self, args):
        super().init(args)

        if "command_fn" not in self.args:
            self.fail("Missing subcommand")

        if self.args.command_fn != self.init_command:
            self.lib = Epithet(self.args.config_dir, self.args.input_dir, self.args.output_dir,
                               verbose=self.args.verbose, quiet=self.args.quiet)
            self.lib.init()

            if self.args.init_only:
                self.parser.exit()

    def run(self):
        self.args.command_fn()

    def init_command(self):
        if self.home is None:
            self.fail("I can't find the default input files")

        def copy(file_name, to_path):
            if _os.path.exists(to_path):
                self.notice("Skipping '{}'. It already exists.", to_path)
                return

            _copy_file(_os.path.join(self.home, "files", file_name), to_path)

            self.notice("Creating '{}'", to_path)

        if self.args.init_only:
            self.parser.exit()

        copy("config.py", _os.path.join(self.args.config_dir, "config.py"))
        copy("main.css", _os.path.join(self.args.input_dir, "main.css"))
        copy("main.js", _os.path.join(self.args.input_dir, "main.js"))

    def render_command(self):
        self.lib.render()

_html_page = """
<html>
  <head>
    <title>Epithet</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <link rel="stylesheet" href="{site_url}/main.css" type="text/css"/>
    <link rel="icon" href="" type="image/png"/>
  </head>
  <body>
    <section>
      <div>

{nav}

{body}

      </div>
    </section>
  </body>
</html>
"""

def _html_table(data, headings=None, **attrs):
    return _html_elem("table", _html_elem("tbody", _html_table_rows(data, headings)), **attrs)

def _html_table_rows(data, headings):
    if headings:
        yield _html_elem("tr", (_html_elem("th", x) for x in headings))

    for row in data:
        yield _html_elem("tr", (_html_elem("td", str(x if x is not None else "")) for x in row))

def _html_elem(tag, content, **attrs):
    if isinstance(content, _abc.Iterable) and not isinstance(content, str):
        content = "".join(content)

    return f"<{tag}{''.join(_html_attrs(attrs))}>{content or ''}</{tag}>"

def _html_attrs(attrs):
    for name, value in attrs.items():
        name = "class" if name in ("class_", "_class") else name
        value = name if value is True else value

        if value is not False:
            yield f" {name}=\"{_xml_escape(value)}\""

def _html_tick_box(value):
    return "&#x2612;" if value else "&#x2610;"

if __name__ == "__main__":
    command = EpithetCommand()
    command.main()

# if __name__ == "__main__":
#     config_dir, input_dir, output_dir = _sys.argv[1:]

#     epithet = Epithet(config_dir, input_dir, output_dir)
#     epithet.run()
