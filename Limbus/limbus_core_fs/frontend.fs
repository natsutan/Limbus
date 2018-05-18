module Frontend

open System.IO
open common

// Source
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

//Token
type TokenType = int
type TokenValue = I of int | F of float | None

let tchar2s(t : TCHAR) : string =
    match t with 
        | EOL | EOF -> ""
        | _ -> string(C)    

[<Class>]
type Token(src : Source) = 
    class
        let mutable _type : TokenType = 0
        member val text : string = "" with get, set
        member val value : TokenValue = I 0 with get, set
        member val source = src with get, set
        member val line_num = src.line_num with get
        member val position = src.current_pos with get
        
        member this.extract()  = 
            this.text <- this.currnet_char() |> tchar2s
            this.value <- None
            this.next_char()
                    
        member this.currnet_char() : TCHAR =
            this.source.current_char()
    
        member this.next_char() : TCHAR  =
            this.source.next_char()
            
        member this.peek_char() : TCHAR =
            this.source.peek_char()
    end

[<Class>]
type EofOfToken(source : Source) =
    inherit Token(source)

    member this.extract() = 
        base.extract()

[<Class>]
type DummyToken(source : Source) =
    inherit Token(source)

    member this.extract() = 
        base.extract()



//Scanner
[<AbstractClass>]
type Scanner(source : Source) =
    class
        let mutable current_token : Token = EofOfToken  (source) :> Token
    
        member this.source = source
        
        abstract member extra_token : unit -> Token

        member this.cuurent_token() : Token = 
            current_token
            
        member this.next_token() : Token = 
            current_token <- this.extra_token()
            current_token
            
        member this.currnet_char() : TCHAR =
            this.source.current_char()
            
        member this.next_char() : TCHAR =
            this.source.next_char()
    
    end 
        

[<AbstractClass>]
type Parser(scanner : Scanner) = 
    member this.message_handler = MessegeHandller()    

    interface  MessageProducer with 
        member this.add_message_listener(ml: MessageListener) : unit = 
            this.message_handler.add_message_listener(ml)
        member this.remove_message_listener(ml : MessageListener) : unit = 
            this.message_handler.remove_message_listener(ml)
        member this.send_message(m : Message) : unit = 
            this.message_handler.send_message(m)


    member this.symTab = null 
    member this.iCode = null 
    member this.scanner = scanner 
    
    abstract member parse : unit -> unit
    abstract member get_error_count : unit -> int 
    
    member this.current_token() : Token = this.scanner.cuurent_token()
        
    member this.next_token() : Token = this.scanner.next_token()
    
    member this.send_message(m : Message) : unit = 
        this.message_handler.send_message(m)
