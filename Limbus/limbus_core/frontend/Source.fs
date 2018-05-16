module Source

open System.IO
open MessageIF
type  TCHAR =  C of char | EOL | EOF 

[<Class>]
type Source(reader : StreamReader )  = 
    let mutable rearch_eof : bool = false
    let mutable line = ""
    
    interface  MessageProducer with 
        member this.add_message_listener(ml: MessageListener) : unit = 1 |> ignore
        member this.remove_message_listener(ml : MessageListener) : unit = 1 |> ignore
        member this.send_message(m : Message) : unit = 1 |> ignore
    
    member this.reader = reader
    member val line_num = 0 with get, set
    member val current_pos = -2 with get, set
    
    member this.send_message(m : Message) : unit = 1 |> ignore
    
    member this.current_char() : TCHAR =
        let line_len = String.length line
        
        if rearch_eof 
        then EOF
        else 
            match this.line_num with 
                | -2 ->
                    // first time
                    this.read_line() 
                    this.next_char()
                | -1 -> EOL
                | _ when this.current_pos = line_len -> EOL
                | _ when this.current_pos > line_len ->
                    this.read_line() 
                    this.next_char()
                | _ -> C line.[this.current_pos]
        
    member this.read_line() : unit =
        line <- this.reader.ReadLine()
        this.current_pos <- 0

        if line = null then 
            rearch_eof <- true
            let m = {msg_type = PARSER_SUMMARY ; body = MSGS [string(this.line_num) ; line]}
            this.send_message(m)
            
        this.line_num <- this.line_num + 1
        
    
    member this.next_char() : TCHAR = 
        this.current_pos <- this.current_pos + 1
        this.current_char()
    
    member this.peek_char() : TCHAR = 
        this.current_char() |> ignore

        let next_pos = this.current_pos + 1        
        match rearch_eof with 
            | true -> EOF
            | false when next_pos >= String.length line -> EOL
            | false -> C line.[next_pos]
                
    member this.close() : unit =
        this.reader.Close()


        