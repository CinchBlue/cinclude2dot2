# cinclude2dot2 - C/C++ dependency graph generator Python script

`cinclude2dot2` is intended to be an original, clean-house, remaking and 
"remastering" of the Perl-based [cinclude2dot](https://www.flourish.org/cinclude2dot/) tool. 

Using `cinclude2dot` requires using Python. This script was developed using
Python 2.7 and 3.3, and should be compatible with both.

`cinclude2dot2` uses a JSON configuration file, which, by convention,
is named `config.cinclude2dot2`. In this file, you may:

- Specify nodes to cluster based on Python regular expressions
- Search for and style nodes based on Python regular expressions

`cinclude2dot2` also uses the Python `argparse` module in order to
provide a full-featured command line interface.

# Using `cinclude2dot2`

To use, download the script and its `config.cinclude2dot2` JSON configuration
file to the root directory that you wish to create a graph of. Then, run:

    python cinclude2dot2.py

This will produce a file named `output.dot` by default. To emit .dot output
to stdout, instead call:

    python cinclude2dot2.py -O

or, instead, to output to a certain file name in the current directory:

    python cinclude2dot.py -o FILENAME

To set the root directory of focus to antoher directory, use:

    python cinclude2dot2.py -Irelative/path/to/file

To recursively search the root directory and its folders for C/C++ files
to analyze, use:

    python cinclude2dot2.py -r

To only allow certain files with certain suffixes to be analyzed, use:

    python cinclude2dot2.py --suffix .ONE .TWO .THREE

To use another JSON configuration file, use:

    python cinclude2dot2.py --config CONFIG_FILENAME

# The `config.cinclude2dot2` Configuration File:

The JSON configuration file should consist of a single JSON object,
with 5 possible different top-level pair labels:

## node, edge, graph

These correspond to the `node[], edge[], graph[]` settings as seen
in the dot file.

## $cluster_NAME

These cluster filenames that match the regex into a node cluster.

## $node_NAME

This command will apply a style to nodes that match the regex.
Tags besides "regex" will be applied.

# This project is frozen (since August 31, 2018) due to inactivity. Please fork if you wish to take ownership.
