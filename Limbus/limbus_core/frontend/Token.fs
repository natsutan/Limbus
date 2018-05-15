module Token
open Source

type TokenType = INT | FLOAT
type TokenValue = I of int | F of float

type Token = { Type : TokenType ; text : string ; value : TokenValue ;  sourse : string ; line_num : int ; position : int}


let tchar2s(t : TCHAR) : string =
    match t with 
        | EOL | EOF -> ""
        | _ -> string(C)    

let extract(source : Source) : string =
    let text = source.current_char() |> tchar2s
    source.next_char() |> ignore
    
    text


let make_token(source : Source) : Token =
    let t = INT
    let text = extract(source)
                   
    let value = I 10
    let src = ""
    let line_num = source.line_num()
    let position = source.current_pos()
    
    { Type = t; text = text; value = value; sourse = src; line_num = line_num; position = position }

let make_dummy_token() : Token =
    let t = INT
    let text = ""
    let value = I 0
    let src = ""
    let line_num = 0
    let position = 0
    { Type = t; text = text; value = value; sourse = src; line_num = line_num; position = position }
