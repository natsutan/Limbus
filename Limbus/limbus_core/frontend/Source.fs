module Source

open System.IO
type  TCHAR =  C of char | EOL | EOF 

[<Class>]
type Source(reader : StreamReader )  = 
    let mutable _line_num : int = 0
    let mutable rearch_eof : bool = false
    let mutable _current_pos = - 2 
    let mutable line = ""
    
    member this.reader = reader

    
    member this.current_char() : TCHAR =
        let line_len = String.length line
        
        if rearch_eof 
        then EOF
        else 
            match _line_num with 
                | -2 ->
                    // first time
                    this.read_line() 
                    this.next_char()
                | -1 -> EOL
                | _ when _current_pos = line_len -> EOL
                | _ when _current_pos > line_len ->
                    this.read_line() 
                    this.next_char()
                | _ -> C line.[_current_pos]
        
    member this.read_line() : unit =
        line <- this.reader.ReadLine()
        _current_pos <- _current_pos - 1

        if line = null then rearch_eof <- true
            
        _line_num <- _line_num + 1
    
    member this.next_char() : TCHAR = 
        _current_pos <- _current_pos + 1
        this.current_char()
    
    member this.peek_char() : TCHAR = 
        this.current_char() |> ignore

        let next_pos = _current_pos + 1        
        match rearch_eof with 
            | true -> EOF
            | false when next_pos >= String.length line -> EOL
            | false -> C line.[next_pos]
                
    member this.close() : unit =
        this.reader.Close()

    member this.line_num() : int =
        _line_num
        
    member this.current_pos() : int =
        _current_pos
   
        