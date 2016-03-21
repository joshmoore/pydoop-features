# BEGIN_COPYRIGHT
#
# Copyright (C) 2014-2016 CRS4.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# END_COPYRIGHT

"""\
Integrate bioimage analysis with Bio-Formats and Hadoop.
"""

import os
import glob
import shutil
import subprocess as sp
from distutils.command.build import build as BaseBuild
from distutils.errors import DistutilsSetupError
from distutils.core import setup


NAME = "pyfeatures"
DESCRIPTION = __doc__
URL = "https://github.com/simleo/pydoop-features.git"
CLASSIFIERS = [
    "Programming Language :: Python",
    "Topic :: Scientific/Engineering :: Bio-Informatics",
    "Intended Audience :: Science/Research",
]


def build_java():
    sp.check_call(["mvn", "clean", "compile", "assembly:single"])


def write_schema_module():
    with open(os.path.join("pyfeatures", "schema.py"), "w") as fo:
        fo.write("# GENERATED BY setup.py\n")
        fnames = glob.glob(os.path.join("src", "main", "avro", "*.avsc"))
        if not fnames:
            raise DistutilsSetupError("Avro schema files not found!")
        for fn in fnames:
            name = os.path.basename(os.path.splitext(fn)[0])
            with open(fn) as f:
                fo.write('\n%s = """\\\n%s"""\n' % (name, f.read()))


def write_config(append=False, **config):
    mode = "a" if append else "w"
    with open(os.path.join("pyfeatures", "config.py"), mode) as fo:
        fo.write("# GENERATED BY setup.py\n")
        for k, v in config.iteritems():
            fo.write("%s = %r\n" % (k.upper(), v))


class Build(BaseBuild):

    def __find_jar(self):
        jars = glob.glob("target/pydoop-features-*.jar")
        if len(jars) != 1:
            raise DistutilsSetupError(
                "Exactly one pydoop-features jar expected in target/"
            )
        return jars[0]

    def __add_jar(self, src_path):
        bn = os.path.basename(src_path)
        dst_path = os.path.join(self.build_lib, "pyfeatures", bn)
        shutil.copyfile(src_path, dst_path)

    def run(self):
        build_java()
        jar_path = self.__find_jar()
        write_config(jar_name=os.path.basename(jar_path))
        write_schema_module()
        BaseBuild.run(self)
        self.__add_jar(jar_path)


setup(
    name=NAME,
    description=DESCRIPTION,
    url=URL,
    classifiers=CLASSIFIERS,
    packages=[
        "pyfeatures",
        "pyfeatures.app",
    ],
    scripts=["scripts/pyfeatures"],
    cmdclass={"build": Build}
)
