def to_display_data(message, mimetype='text/plain'):
    """wraps the message into the display_data format"""
    return {
        'data': {
            mimetype: message
        },
        'metadata': {},
        'transient': {},
    }


gfKeywords = ['flags', 'startcat', 'cat', 'fun', 'of', 'lin', 'lincat', 'with',
              'open', 'in', 'param', 'linref', 'table', 'let', 'case', 'overload']
gfBuiltins = ['Str']
gfDefiners = ['abstract', 'concrete', 'resource',
              'incomplete', 'instance', 'interface']
GF_commands = ['abstract_info', 'ai', 'align_words', 'al', 'clitic_analyse', 'ca', 'compute_conctete', 'cc',
               'define_command', 'dc', 'depencency_graph', 'dg', 'define_tree', 'dt', 'empty', 'e', 'example_based', 'eb',
               'execute_history', 'eh', 'generate_random', 'gr', 'generate_trees', 'gt', 'h', 'import', 'i',
               'linearize', 'l', 'linearize_chunks', 'lc', 'morpho_analyse', 'ma', 'morpho_quiz', 'mq', 'parse', 'p',
               'print_grammar', 'pg', 'print_history', 'ph', 'put_string', 'ps', 'put_tree', 'pt', 'quit', 'q', 'reload',
               'r', 'read_file', 'rf', 'rank_trees', 'rt', 'show_dependencies', 'sd', 'set_encoding', 'se', 'show_operations',
               'so', 'system_pipe', 'sp', 'show_source', 'ss', 'translation_quiz', 'tq', 'to_trie', 'tt', 'unicode_table',
               'ut', 'visualize_dependency', 'vd', 'visualize_parse', 'vp', 'view_parse', 'visualize_tree', 'view_tree', 'vt', 'write_file', 'wf']
kernel_commands = ['show', 'clean', 'export', 'help', 'grammar-path']
MMT_commands = ['archive', 'archives', 'construct', 'subdir', 'elpigen']
ELPI_commands = ['elpi']
mmtDefiners = ['theory', 'view']
mmtDelimiters = ['\u2758', '\u2759', '\u275A']
commonCommands = GF_commands + kernel_commands + MMT_commands + ELPI_commands

allKeywords = gfKeywords + gfBuiltins + \
    gfDefiners + commonCommands + mmtDefiners


def check_port(host, port):
    """checks if the given port is free"""
    import socket
    from contextlib import closing
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex((host, port)) == 0:
            res = True
        else:
            res = False
    return res


def generate_port(h="localhost", start=8080, end=30000,jumpmax=4):
    import time, random
    p = start + random.randint(0,jumpmax)
    while p < end:
        if not check_port(h, p):
            return p
        p += random.randint(1,jumpmax)
        time.sleep(0.5)


def parse(code):
    lines = code.split('\n')
    parseDict = {
        'type': None,
        'name': None,
        'commands': []
    }
    isMMTContent = False
    isGFContent = False
    isELPIContent = False
    for line in lines:
        words = line.strip().split(' ')
        lastWord = ''
        for word in words:
            if word in gfDefiners:
                isGFContent = True
                lastWord = word
                continue
            if (word in mmtDefiners and contains(code, mmtDelimiters))or word == 'namespace':
                isMMTContent = True
                lastWord = word
                continue
            if isGFContent and word not in gfDefiners and lastWord in gfDefiners:
                parseDict['type'] = 'GFContent'
                parseDict['name'] = word
                parseDict['commands'] = []
                return parseDict
            if isMMTContent and word not in mmtDefiners and lastWord in mmtDefiners:
                parseDict['type'] = 'MMTContent'
                parseDict['name'] = word
                if lastWord == 'theory':
                    parseDict['mmt_type'] = 'theory'
                else:
                    parseDict['mmt_type'] = 'view'
                parseDict['commands'] = []
                return parseDict
            if word == 'elpi:':
                isELPIContent = True
                lastWord = word
                continue
            if isELPIContent:
                parseDict['type'] = 'ELPIContent'
                parseDict['name'] = word
                return parseDict
            if not isGFContent and not isMMTContent and word in commonCommands and word == words[0]:
                pipe_commands = list(map(str.strip, line.split('|')))
                pipe_commands_dicts = []
                for pipe_command in pipe_commands:
                    pipe_command_type = get_command_type(pipe_command)
                    if not pipe_command_type:
                        parseDict['type'] = None
                        return parseDict
                    pipe_command_dict = {
                        'type': pipe_command_type,
                        'command': pipe_command
                    }
                    pipe_commands_dicts.append(pipe_command_dict)
                command = {
                    'pipe_commands': pipe_commands_dicts
                }
                parseDict['type'] = 'commands'
                parseDict['commands'].append(command)
    return parseDict


def get_command_type(command):
    """
        returns the type of command
    """
    name = get_name(command)
    if name in MMT_commands:
        return "MMT_command"
    elif name in GF_commands:
        return "GF_command"
    elif name in kernel_commands:
        return "kernel_command"
    elif name in ELPI_commands:
        return "ELPI_command"
    else:
        return None


def get_name(command):
    """returns the name of the command"""
    return command.split(' ')[0]


def get_args(command):
    """returns the arguments of the command or None if none exist"""
    try:
        return command.split(' ')[1:]
    except:
        return None


def contains(string, set):
    """checks if the given string contains any characters from set"""
    return True in [char in string for char in set]


def to_message_format(message=None, graph=None, trees=None):
    return {
        'message': message,
        'graph': graph,
        'trees': trees
    }


def create_nested_dir(cwd, new_dir):
    import os
    """
        Creates a nested directory from cwd

        `cwd`: absolute path to the current directory
        `new_dir`: the name of the new directory

        returns the path to the new directory
    """
    cwd_path = cwd
    subdirs = new_dir.split(os.path.sep)
    for d in subdirs:
        cwd_path = os.path.join(cwd_path, d)
        if os.path.isdir(cwd_path):
            continue
        os.mkdir(cwd_path)
    return cwd_path


def get_current_word(code, cursorPos):
    """Returns the word before the `cursorPos`"""
    import re
    last_word = []
    wordChar = re.compile("[a-zA-Z]")
    for i in range(cursorPos-1, -1, -1):
        if wordChar.match(code[i]):
            last_word.append(code[i])
        else:
            break
    return "".join(reversed(last_word))


def get_matches(last_word):
    import re
    matches = []
    regex = re.compile("%s" % (last_word))
    for word in allKeywords:
        if regex.match(word):
            matches.append(word)
    return matches



# original code from https://stackoverflow.com/a/36253753
def tree(dir, padding='', print_files=True, isLast=False, isFirst=True, displayFullPath=False, archive_name=None):
    # TODO make this into a sring so output order doesn't get screwed
    from os import listdir, sep
    from os.path import abspath, basename, isdir, splitext
    from sys import argv
    from IPython.display import display
    from ipywidgets import widgets

    show_ext = ['.gf']
    hide_dir = ['content','META-INF','narration','relational','content']

    if isFirst:
        if displayFullPath:
            print(padding[:-1]+ dir)
        else:
            print(padding[:-1]+ archive_name)
    else:
        if isLast:
            print(padding[:-1] + '└── ' + basename(abspath(dir)))
        else:
            print(padding[:-1] + '├── ' + basename(abspath(dir)))
    files = []
    if print_files:
        all_files = listdir(dir)
        files = []
        for file in all_files:
            path = dir + sep + file
            if isdir(path):
                if file not in hide_dir:
                    files.append(file)
                continue
            else:
                _, ext = splitext(file)
                if ext in show_ext:
                    files.append(file)
    else:
        files = [x for x in listdir(dir) if isdir(dir + sep + x) and x not in hide_dir]
    if not isFirst:
        padding = padding + '   '
    files = sorted(files, key=lambda s: s.lower())
    count = 0
    last = len(files) - 1
    for i, file in enumerate(files):  
        count += 1
        path = dir + sep + file
        isLast = i == last
        if isdir(path):
            if count == len(files):
                if isFirst:
                    tree(path, padding, print_files, isLast, False)
                else:
                    tree(path, padding + ' ', print_files, isLast, False)
            else:
                tree(path, padding + '│', print_files, isLast, False)
        else:
            if isLast:
                print(padding + '└── ' + file)
            else:
                print(padding + '├── ' + file)
