module Token
open Source

type TokenType = int
type TokenValue = I of int | F of float | None

let tchar2s(t : TCHAR) : string =
    match t with 
        | EOL | EOF -> ""
        | _ -> string(C)    

[<AbstractClass>]
type Token(source : Source) = 
    class
        let mutable _type : TokenType = 0
        let mutable _text : string = ""
        let mutable _value : TokenValue = I 0
        let mutable _source = source
        let mutable _line_num = _source.line_num
        let mutable _position = _source.current_pos
        
        member this.extract()  = 
            _text <- this.currnet_char() |> tchar2s
            _value <- None
            this.next_char()
                    
        member this.currnet_char() : TCHAR =
            _source.current_char()
    
        member this.next_char() : TCHAR  =
            _source.next_char()
            
        member this.peek_char() : TCHAR =
            _source.peek_char()
    end

[<Class>]
type EodOfToken(source : Source) =
    inherit Token(source)
    

    member this.extract() = 
        base.extract()

