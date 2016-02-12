#!/usr/bin/env python

"""\
Dump the minimal amount of metadata needed to speed up BioImgInputFormat.
"""
# TODO:
#  * support multiple fields
#  * turn into a server script

# FIXME: assumes that omero.data.dir is also mounted on the client!

import sys
import os
import getpass
import argparse
import ConfigParser

from omero.gateway import BlitzGateway


DEFAULT_USER = getpass.getuser()


def dump_conn_info(conn):
    user = conn.getUser()
    print "Current user:"
    print "   ID:", user.getId()
    print "   Username:", user.getName()
    print "   Full Name:", user.getFullName()
    print "Member of:"
    for g in conn.getGroupsMemberOf():
        print "   ID:", g.getName(), " Name:", g.getId()
    group = conn.getGroupFromContext()
    print "Current group: ", group.getName()


def get_plate_info(conn, plate_id,
                   setup_fn=None, screen_fn=None, verbose=False):
    plate = conn.getObject("Plate", plate_id)
    if plate is None:
        raise RuntimeError("no plate with id: %r" % (plate_id,))
    data_dir = conn.getConfigService().getConfigValue("omero.data.dir")
    absp = lambda p: os.path.join(data_dir, "ManagedRepository", p)
    path_map = {}  # (row, column) => dir_name
    old_screen_path = ""
    plane_counts = set()
    for well in plate.listChildren():
        img = well.getImage()
        if img is None:
            continue
        plane_counts.add(img.getSizeZ() * img.getSizeT() * img.getSizeC())
        for f in img.getFileset().listFiles():
            basename = f.getName()
            abs_dir = absp(f.getPath())
            if basename.endswith(".screen"):
                old_screen_path = os.path.join(abs_dir, basename)
                if screen_fn is None:
                    screen_fn = basename
            else:
                # assumes all files in the pattern are in the same dir
                path_map[(well.row, well.column)] = abs_dir
    screen_fn = os.path.abspath(screen_fn)
    assert len(plane_counts) == 1
    if setup_fn is None:
        setup_fn = "%s.tsv" % plate.getName()
    if verbose:
        print "writing job setup to %s" % setup_fn
    with open(setup_fn, "w") as fo:
        fo.write("%s\t%d\t%d\n" % (
            screen_fn, plate.countChildren(), plane_counts.pop()
        ))
    return old_screen_path, screen_fn, path_map


# FIXME: this does not work because keys in path_map are individual
# file basenames, while the .screen contains patterns. What's needed
# is a map from well (row, col) to directories.
def regenerate_screen(old_screen_path, new_screen_path, path_map):
    parsers = {
        'in': ConfigParser.ConfigParser(),
        'out': ConfigParser.ConfigParser()
    }
    for p in parsers.itervalues():
        p.optionxform = str  # case-sensitive option names
    with open(old_screen_path) as f:
        parsers['in'].readfp(f)
    for sec in parsers['in'].sections():
        parsers['out'].add_section(sec)
        for opt in parsers['in'].options(sec):
            value = parsers['in'].get(sec, opt)
            if opt.startswith('Field_'):
                row = parsers['in'].getint(sec, 'Row')
                column = parsers['in'].getint(sec, 'Column')
                d = path_map[(row, column)]
                bn = os.path.basename(value)
                parsers['out'].set(sec, opt, os.path.join(d, bn))
            else:
                parsers['out'].set(sec, opt, value)
    with open(new_screen_path, "w") as fo:
        parsers['out'].write(fo)


def make_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('id', metavar="PLATE_ID", type=int)
    parser.add_argument("-H", "--host", metavar="HOST", default="localhost")
    parser.add_argument("-P", "--port", metavar="PORT", default=4064)
    parser.add_argument("-U", "--user", metavar="USER", default=DEFAULT_USER)
    parser.add_argument("-G", "--group", metavar="GROUP")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--setup", metavar="FILE",
                        help="write job setup file to this path")
    parser.add_argument("--screen", metavar="FILE",
                        help="write regenerated screen file to this path")
    return parser


def main(argv):
    parser = make_parser()
    args = parser.parse_args(argv[1:])
    passwd = getpass.getpass()
    conn = BlitzGateway(
        args.user, passwd, host=args.host, port=args.port, group=args.group
    )
    conn.connect()
    if args.verbose:
        dump_conn_info(conn)
    # with open(args.setup, 'w') as setupf, open(args.screen, 'w') as screenf:
        # dump_setup(conn, args.id, setupf, screenf)
    old_screen_path, new_screen_path, path_map = get_plate_info(
        conn, args.id, args.setup, args.screen, args.verbose
    )
    if args.verbose:
        print "writing regenerated screen file to %s" % new_screen_path
    regenerate_screen(old_screen_path, new_screen_path, path_map)



if __name__ == "__main__":
    main(sys.argv)
