concrete GrammarGer of Grammar = {
    lincat
        Person = Str ;
        Action = Str ;
        Sentence = Str ;
    lin
        john = "Johann" ;
        mary = "Maria" ;
        run = "rennt" ;
        be_happy = "ist glücklich" ;
        make_sentence person action = person ++ action ;
        and a b = a ++ "und" ++ b ;
}