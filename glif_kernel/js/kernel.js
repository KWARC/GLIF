define([
        'base/js/namespace',
        'base/js/events',
        'notebook/js/codecell',
        'codemirror/lib/codemirror',
        'require'
], function (Jupyter, events, codecell, CodeMirror, require) {
        "use strict";

        return {
                onload: function () {
                        "use strict";
                        var CODE_CELL;

                        
                        CodeMirror.defineMode("gf", function (conf, parserConf) {
                                function wordRegexp(words) {
                                        return new RegExp("^((" + words.join(")|(") + "))\\b");
                                }
                        
                                // GF Keywords
                                var GFKeywordsList = ["flags", "startcat", "cat", "fun",
                                        "of", "lin", "lincat", "with", "open", "in", "param", "linref",
                                        "table", "let", "case", "overload", "lindef", "def", "data", "oper"];
                                var GFBuiltinsList = ["Str"];
                                var GFDefinersList = ["abstract", "concrete", "resource", "incomplete", "instance", "interface"];
                        
                                // MMT Keywords
                                var MMTKeywordsList = ["include"];
                                var MMTBuiltinsList = ["prop", "type"];
                                var MMTDefinersList = ['theory', 'view'];
                        
                        
                                // Commands
                                var GFCommandsList = ["abstract_info", "align_words", "clitic_analyse",
                                        "compute_conctete", "define_command", "depencency_graph",
                                        "define_tree", "empty", "example_based", "execute_history",
                                        "generate_random", "generate_trees", "import",
                                        "linearize", "linearize_chunks", "morpho_analyse", "morpho_quiz",
                                        "parse", "print_grammar", "print_history", "put_string",
                                        "put_tree", "quit", "reload", "read_file", "rank_trees",
                                        "show_dependencies", "set_encoding", "show_operations",
                                        "system_pipe", "show_source", "translation_quiz", "to_trie",
                                        "unicode_table", "visualize_dependency", "visualize_parse",
                                        "visualize_tree", "write_file"];
                                var GFCommandsAbbrList = ["ai", "al", "ca", "cc", "dc", "dg", "dt", "e", "eb", "eh",
                                        "gr", "gt", "h", "i", "l", "lc", "ma", "mq", "p", "pg", "ph", "ps", "pt", "q",
                                        "r", "rf", "rt", "sd", "se", "so", "sp", "ss", "tq", "tt", "ut", "vd", "vp",
                                        "vt", "wf"];
                                var KernelCommandsList = ["show", "archive", "subdir", "clean", "help", "export", "construct"];
                        
                                // Regexes
                                var Operators = /^([-+*/%\/&|^]=?|[<>=]+|\/\/=?|\*\*=?|!=|[~!@])/;
                                var Identifiers = parserConf.identifiers || /^[_A-Za-z\u00A1-\uFFFF][_A-Za-z0-9\u00A1-\uFFFF]*/;
                        
                        
                                // GFRegexes
                                var GFKeywords = wordRegexp(GFKeywordsList);
                                var GFBuiltins = wordRegexp(GFBuiltinsList);
                                var GFDefiners = wordRegexp(GFDefinersList);
                                var GFSeparators = /[:;]/;
                        
                                // MMTRegexes
                                var MMTDefiners = wordRegexp(MMTDefinersList);
                                var MMTKeywords = wordRegexp(MMTKeywordsList);
                                var MMTBuiltins = wordRegexp(MMTBuiltinsList);
                                var MMTSeparators = /[:?]/;
                                var objectDelimiter = /\u2758/;
                                var declarationDelimiter = /\u2759/;
                                var moduleDelimiter = /\u275A/;
                        
                        
                                function push(tokenizer, stream, state) {
                                        state.tokenize.push(tokenizer);
                                        return tokenizer(stream, state);
                                }
                        
                                function tokenBase(stream, state) {
                                        if (stream.eatSpace()) return null;
                        
                                        // handle GF content
                                        if (state.GFContent) {
                                                // builtins
                                                if (stream.match(GFBuiltins)) return "builtin";
                        
                                                // GF Keywords
                                                if (stream.match(GFKeywords) || stream.match(GFDefiners)) return "keyword";
                        
                                                // Handle multi line GF comments
                                                if (stream.match(/{-/)) return push(tokenGFComment, stream, state);
                        
                                                // Handle single line GF comments
                                                if (stream.match(/--.*/)) {
                                                        stream.skipToEnd();
                                                        return "comment";
                                                }
                        
                                                // handle identifiers / words
                                                if (stream.match(Identifiers)) {
                                                        if (GFDefinersList.includes(state.lastToken)) return "def";
                                                        if (state.lastToken == "of") return "meta";
                                                        return "variable";
                                                }
                        
                                                // handle separators
                                                if (stream.match(GFSeparators)) return "meta";
                                        }
                        
                                        // handle MMT content
                                        if (state.MMTContent) {
                        
                                                // handle MMT delimiters
                                                if (stream.match(objectDelimiter)) return "variable-3";
                                                if (stream.match(declarationDelimiter)) return "meta";
                                                if (stream.match(moduleDelimiter)) return "atom";
                        
                                                // builtins
                                                if (stream.match(MMTBuiltins)) return "builtin";
                        
                                                // MMT Keywords
                                                if (stream.match(MMTKeywords) || stream.match(MMTDefiners)) return "keyword";
                        
                                                // Handle single line MMT comments
                                                if (stream.match(/\\T/)) {
                                                        stream.skipToEnd();
                                                        return "comment";
                                                }
                        
                                                // handle identifiers / words
                                                if (stream.match(Identifiers)) {
                                                        if (MMTDefinersList.includes(state.lastToken)) return "def";
                                                        return "variable";
                                                }
                        
                                                // handle separators
                                                if (stream.match(MMTSeparators)) return "meta";
                                        }
                        
                                        if (!state.MMTContent && !state.GFContent) {
                                                // detect GF content
                                                if (stream.match(GFDefiners)) {
                                                        state.GFContent = true;
                                                        return "keyword";
                                                }
                        
                                                // detect MMT content
                                                if (stream.match(MMTDefiners)) {
                                                        state.MMTContent = true;
                                                        return "keyword";
                                                }
                        
                                                // handle commands
                                                if (stream.match(Identifiers)) {
                                                        if (KernelCommandsList.includes(stream.current())) return "keyword";
                                                        if (GFCommandsList.includes(stream.current())) return "tag";
                                                        if (GFCommandsAbbrList.includes(stream.current())) return "tag";
                                                        if (state.lastToken == "variable-2" || state.lastToken == "export" || state.lastToken == "import") return "def";
                                                        return null;
                                                }
                        
                                                // handle command options
                                                if (stream.match(/-\w*=\w*/)) return "variable-2";
                                                if (stream.match(/-v|-c/)) return "variable-2";
                                        }
                        
                                        // handle numbers
                                        if (stream.match(/\d/)) return "number";
                        
                                        // handle operators
                                        if (stream.match(Operators)) return "operator";
                        
                                        // handle strings 
                                        var ch = stream.next();
                                        if (ch == '"' || ch == "'") return push(handleStrings(ch), stream, state);
                        
                                        // don't style unknown stuff
                                        return null;
                                }
                        
                                function tokenGFComment(stream, state) {
                                        if (stream.match(/-}/)) {
                                                state.tokenize.pop();
                                                return "comment";
                                        }
                                        stream.next();
                                        return "comment";
                                }
                        
                                function handleStrings(char) {
                                        return function (stream, state) {
                                                if (stream.match(char)) {
                                                        state.tokenize.pop();
                                                        return "string"
                                                }
                                                stream.next();
                                                return "string";
                                        }
                                }
                        
                                return {
                                        startState: function () {
                                                return {
                                                        tokenize: [tokenBase],
                                                        MMTContent: false,
                                                        GFContent: false,
                                                        lastToken: null
                                                };
                                        },
                        
                                        token: function (stream, state) {
                                                var style = state.tokenize[state.tokenize.length - 1](stream, state);
                                                if (style)
                                                        state.lastToken = (style == "keyword" || style == "atom" || style == "punctuation") ? stream.current() : style;
                                                return style;
                                        },
                                        lineComment: "--"
                                };
                        });
                        

                        CodeMirror.defineMIME("text/gf", "gf");
                        console.info('GF mode loaded');

                        var gfStlye = document.createElement("link");
                        gfStlye.type = "text/css";
                        gfStlye.rel = "stylesheet";
                        gfStlye.href = require.toUrl("./gf.css");
                        gfStlye.id = "gf-css";
                        document.getElementsByTagName("head")[0].appendChild(gfStlye);

                        codecell.CodeCell.options_default.cm_config.theme = "gf";
                        var cells = Jupyter.notebook.get_cells().forEach(function (cell) {
                                if (cell instanceof codecell.CodeCell) {
                                        cell.code_mirror.setOption("theme", "gf");
                                }
                        });

                        var words = function (str) { return str.split(" "); };


                }
        }


});
