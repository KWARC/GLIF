define([
        'base/js/namespace',
        'base/js/events',
        'notebook/js/codecell',
        'codemirror/lib/codemirror',
        'require'
    ], function(Jupyter, events, codecell, CodeMirror,require) {
        "use strict";

        return {onload: function(){
                CodeMirror.defineMode("gf", function() {
                function words(array) {
                        var keys = {};
                        for (var i = 0; i < array.length; ++i) {
                                keys[array[i]] = true;
                        }
                        return keys;
                }
                
                var keywords = words(["abstract", "concrete", "flags", "startcat", "cat", "fun", "of", "lin", "lincat"]);
                var builtins = words(["Phrase", "Item", "Kind", "Quality", "Item"]);
                var isOperatorChar = /=|\+|>|\-|\|/;
                var isSeparatorChar = /[,;:]/;
        
                function tokenBase(stream, state) {
        
                        var ch = stream.next();
                        var next = stream.peek();
                        if (ch == "-" && next == "-") {
                                stream.skipToEnd();
                                return "comment";
                        }

                        if (ch == '"' || ch == "'") {
                                state.tokenize = tokenString(ch);
                                return state.tokenize(stream, state);
                        }

                        if (/[\[\]\(\),]/.test(ch)) {
                                return "bracket";
                        }

                        if (isOperatorChar.test(ch)) {
                                stream.eatWhile(isOperatorChar);
                                return "operator";
                        }

                        if(isSeparatorChar.test(ch))
                        {
                                stream.eatWhile(isSeparatorChar);
                                return "separator"
                        }

                        if (/\d/.test(ch)) {
                                stream.eatWhile(/\d/);
                                if(isOperatorChar.test(stream.peek()) || stream.peek() == " " || stream.peek() == ";" || stream.peek() == null){
                                        return "number";
                                }
                
                        }
                
                        stream.eatWhile(/[\w_]/);
                        var word = stream.current();
        
                        if (keywords.hasOwnProperty(word)){
                                if(word == "abstract" || word == "concrete"){
                                        return 'def';
                                }
                                return 'keyword';
                        }
                        if (builtins.hasOwnProperty(word)) {
                                return 'builtin';
                        }
                        return 'variable';
                }
        
                function tokenString(quote) {
                        return function(stream, state) {
                                var escaped = false, next, end = false;
                                while ((next = stream.next()) != null) {
                                        if (next == quote && !escaped) {
                                                end = true;
                                                break;
                                        }
                                        escaped = !escaped && next == "\\";
                                }
                                if (end || !escaped){
                                        state.tokenize = null;
                                } 
                                return "string";
                        };
                }
        
                // Interface

                return {
                startState: function() {
                        return {tokenize: null};
                },

                token: function(stream, state) {
                        if (stream.eatSpace()) return null;
                                var style = (state.tokenize || tokenBase)(stream, state);
                                if (style == "comment" || style == "meta") return style;
                                return style;
                        }
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
        }}
    

    });