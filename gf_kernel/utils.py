def to_display_data(message,omdoc=None):
    """wraps the message into the display_data format"""
    if(omdoc):
        return {
            'data': {
                'text/html': message,
                'application/omdoc' : omdoc
            },
            'metadata': {},
            'transient': {},
        }
    else:
        return {
            'data': {
                'text/html': message,
            },
            'metadata': {},
            'transient': {}
        }

def parse_command(command):
    """
    Parses the input `command`

    Outputs a dictionnary with the following fields:

    `type` : 
        is either `command` or `content`

    `name` : the name of the grammar or the command

    Outputs `None` if the command couldn't be parsed
    """
    if command.startswith('abstract') or command.startswith('concrete'):
        try:
            _, grammar_name, _ = command.split(" ",2)
            return {
                'type' : 'content',
                'name' : grammar_name
            }
        except:
            return None
    else:
        try:
            command_name, _ = command.split(" ",1)
            return {
                'type' : 'command',
                'name' : command_name
            }
        except:
            command_name = command.replace(' ','').replace('\n','')
            return {
                'type' : 'command',
                'name' : command_name
            }
