import sys
import os
import argparse

import json
import re
import pprint


def printout(s):
    if (args.verbose):
        sys.stderr.write(str(s) + '\n')

# Load arguments from the command line.
argparser = argparse.ArgumentParser(
    description="Turns C/C++ files into an #include dependency graph in .dot format",
    epilog="Regex expressions in the JSON config.cinclude2dot2 file use Python regex format"
)

# --include will do the current directory by default.
argparser.add_argument(
    "-I", "--include",
    nargs=1,
    default="./",
    metavar="IPATH",
    help="The path to include in the search (current dir as default)"
)

# --recursive will recursively search through directories.
argparser.add_argument(
    "-r", "--recursive",
    action="store_true",
    default=False,
    help="Recursively search through the included directories",
)

# --file will select a non-default configuration file to select
argparser.add_argument(
    "-f", "--file",
    default="./config.cinclude2dot2",
    help="The configuration file to run (default: config.cinclude2dot)"
)

# --output will specify the file to output a .dot file to.
argparser.add_argument(
    "-o", "--output",
    action="store",
    default="./output.dot",
    help="The filename to output to (default: output.dot)"
)

# --stdout will specify the script to instead emit to stdout
argparser.add_argument(
    "-O", "--stdout",
    action="store_true",
    default=False,
    help="Emit to stdout instead of the output file"
)

# --suffix will specify valid file suffixes to use.
argparser.add_argument(
    "-s", "--suffix",
    nargs="+",
    default=['.cpp', '.h', '.cxx', '.c', '.hpp'],
    help="The filename suffixes to parse (default: .cpp, .h, .cxx, .c, .hpp)"
)

# --verbose will emit verbose warnings to stderr.
argparser.add_argument(
    "-v", "--verbose",
    action="store_true",
    default=False,
    help="Enable verbose output to stderr"
)

# --filepath will specify whether you want the full name of the
# file in the node or not. The default is only the filename.
#
# Regex matches will use the filenames that are adjusted by this
# --filepath option as well.
argparser.add_argument(
    "-p", "--filepath",
    choices=['relative', 'filename'],
    default='filename',
    help="The filepath to use as the name of the file nodes"
)

# --no-system-headers will not search for system headers
argparser.add_argument(
    "--parse-system-headers",
    action="store_true",
    default=False,
    help="Do not parse system header #includes"
)

# --reverse-edge-dir will reverse the direction of edges
argparser.add_argument(
    "--reverse-edge-dir",
    action="store_true",
    default=False,
    help="Reverse the order of edges in the graph"
)

# Parse in the arguments
args = argparser.parse_args()
printout(args)

# Read in the configuration file as JSON
try:
    config_file = open(args.file)
    config = json.load(config_file)
    config_file.close()
except IOError:
    printout(sys.argv[0] + ": Could not open configuration file: " + args.file, file=sys.stderr)
    exit()

# Pretty print the JSON
# pprint.pprintout(config)

# Emit a single string to the output file in info['fout']
# with various other automatic formatting as decided by info.
def emit_str(info, s):
    if (not args.stdout):
        info['fout'].write(
            info['indent_string'] * info['indent_level'] + s
        )
    else:
        sys.stdout.write(
            info['indent_string'] * info['indent_level'] + s
        )


# Increments the indent level in the info dictionary
def inc_indent(info):
    info["indent_level"] = info['indent_level']+1

# Decrements the indent level in the info dictionary
def dec_indent(info):
    info["indent_level"] = info['indent_level']-1

# Emits the property with the name
def emit_property(info, property_tree, name):
    emit_str(info, name + '[\n')
    s = name + '['
    # Write all the properties
    inc_indent(info)
    for pair in property_tree:
        emit_str(info, pair + '=\"' + str(property_tree[pair]) + '\"\n')
    dec_indent(info)
    emit_str(info, ']\n')


def log_cluster(log, cluster_name, node_name):
    # If there is no cluster there yet, create it.
    if (not (cluster_name in log['clusters'].keys())):
        printout(cluster_name + " is not in log['clusters']'s keys")
        log['clusters'].update({ cluster_name : [] })

    # Append the node_name to the cluster.
    if (not (node_name in log['clusters'][cluster_name])):
        printout(node_name + " is not in log['clusters'][cluster_name]'s keys")
        log['clusters'][cluster_name].append(node_name)

# Logs a cluster filter function using Python regex
def config_cluster(info, cluster_tree):
    name = cluster_tree['name']
    regex = cluster_tree['regex']
    #print(name + " :: " + regex)
    printout("config_cluster: " + name + '::' + regex)
    # Add a filtering function to the info['cluster_filters'] list:
    def filter_cluster(log, filename, name=name, regex=regex):
        if (re.match(regex, filename)):
            log_cluster(log, name, filename)
    # Append the filtering function to the list.
    info['cluster_filters'].append(filter_cluster)

# Gets all of the valid source files.
def get_source_files():
    list_files = []
    for item in args.include:
        # Get all of the files recursively or not in the included path.
        if (args.recursive):
            for root, dirs, files in os.walk(item):
                for filename in files:
                    for suffix in args.suffix:
                        if (filename.endswith(suffix)):
                            list_files.append(os.path.join(root, filename))
                            break
        else:
            for filename in os.listdir(item):
                for suffix in args.suffix:
                    if (filename.endswith(suffix)):
                        list_files.append(os.path.join(item, filename))
                        break
    return list_files

# Process the cluster filters by applying all the filter functions to
# the filename.
def process_cluster_filters(info, log, filename):
    for func in info['cluster_filters']:
        func(log, filename)

# Process the node filters by applying all the filter functions to
# the filename.
def process_node_filters(info, log, filename):
    for func in info['node_filters']:
        func(log, filename)

# Parse the files and emit the edges.
def parse_files_and_emit_edges(info, log, source_files):
    printout(info)
    printout(log)
    # Change the regex string to match system headers if needed.
    if (not args.parse_system_headers):
        regex_string = "#include\s+\".*\""
    else:
        regex_string = "#include\s+((\<.*\>)|(\".*\"))"
    # For all filenames, process filter functions and then
    for filename in source_files:
        with open(filename) as filein:
            # Get the adjusted current_filename
            if (args.filepath == 'filename'):
                current_filename = os.path.basename(filename)
            elif (args.filepath == 'relative'):
                current_filename = filename
            # Process the filters for the current filename.
            process_cluster_filters(info, log, current_filename)
            process_node_filters(info, log, current_filename)
            for line in filein:
                # Find a match if its there.
                regex_match = re.match(regex_string, line)
                if (regex_match != None):
                    # Find the included filename.
                    included_filename = regex_match.group(0).split()[1]
                    included_filename = included_filename.replace('\"', '')
                    filter_filename = included_filename.replace('<', '')
                    filter_filename = filter_filename.replace('>', '')
                    # Process filters for the current filename.
                    process_cluster_filters(info, log, filter_filename)
                    process_node_filters(info, log, current_filename)
                    # Write the current edge.
                    if (not args.reverse_edge_dir):
                        emit_str(
                            info,
                            '\"' + current_filename + '\" -> \"' + filter_filename + '\"\n')
                    else:
                        emit_str(
                            info,
                            '\"' + filter_filename + '\" -> \"' + current_filename + '\"\n')

# Emit cluster information
def emit_clusters(info, log):
    for cluster in log['clusters'].keys():
        emit_str(info, "subgraph cluster_" + cluster + "{\n")
        inc_indent(info)
        for node_name in log['clusters'][cluster]:
            emit_str(info, '\"' + node_name + '\"\n')
        dec_indent(info)
        emit_str(info, "}\n")

# Log a node that has been filtered.
def log_node(log, name, tree):
    if (not (name in log['logged_nodes'])):
        log['logged_nodes'].append(name)
        property_string = ""
        printout(name + " :: match :: " + tree['regex'])
        for key in tree.keys():
            if (not (key == 'regex')):
                property_string = property_string + key + '=\"' + tree[key] + '\",'
        property_string = property_string[0:-1]
        emit_str(log, '\"' + name + '\" [' + property_string + ']\n')

# Attach a regex filter according to a node.
def config_node(info, config_tree):
    regex = config_tree['regex']
    tree = config_tree
    #print(name + " :: " + regex)
    printout("config_node: " + regex)
    # Add a filtering function to the info['node_filters'] list:
    def filter_node(log, filename, tree=tree, regex=regex):
        if (re.match(regex, filename)):
            log_node(log, filename, tree)
    # Append the filtering function to the list.
    info['node_filters'].append(filter_node)


# The root tree traversal function.
def emit_output(info, log, config_tree):
    emit_str(info, "digraph cinclude2dot2 {\n")
    # For each JSON pair in the config, choose the
    # correct emission function according to the name.
    inc_indent(info)
    for pair in config_tree:
        # If it's a property, emit it
        if (pair == "graph" or
            pair == "node" or
            pair == "edge"):
            emit_property(info, config_tree[pair], pair)
        # If it's a $cluster filter, read in the info
        elif (pair == "$cluster"):
            config_cluster(info, config_tree[pair])
        # If it's a $node filter, read in the info
        elif (pair == "$node"):
            config_node(info, config_tree[pair])
        # Otherwise, let's see what it is.
        else:
            emit_str(info, pair + '=' + config_tree[pair] + '\n')
        # Then, emit a space in the line
        emit_str(info, '\n')
    # Then, parse the selected files and emit the edges.
    source_files = get_source_files()
    parse_files_and_emit_edges(info, log, source_files)
    # Now, emit clusters
    emit_str(info, '\n')
    emit_clusters(info, log)
    # Emit the ending of the .dot file.
    dec_indent(info)
    emit_str(info, '}')

######################################################################
######################################################################
######################################################################

# Traverse the JSON & output the .dot file..
with open(args.output, "w") as output_file:
    # The configuration info dictionary to be filled
    info = {
        "indent_level"          : 0,
        "indent_string"         : '  ',
        "fout"                  : output_file,
        "cluster_filters"       : [],
        "node_filters"          : []
    }
    log = {
        "indent_level"          : info['indent_level'],
        "indent_string"         : info['indent_string'],
        "clusters"              : {},
        "logged_nodes"          : [],
        "fout"                  : output_file,
    }

    # Emit the output .dot file.
    emit_output(info, log, config)
    printout("Done.")

