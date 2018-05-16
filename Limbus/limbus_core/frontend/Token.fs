module Token
open Source

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
