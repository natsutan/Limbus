module frontend.pascal
open System.Diagnostics

open common
open Frontend

[<Class>]
type PascalParserTD(scanner : Scanner) = 
    inherit Parser(scanner)
    
    override this.get_error_count() = 0

    override this.parse() =  
        let src = this.scanner.source
    
        let mutable token : Token = this.next_token()
        let mutable break_cond = false 
        while not break_cond do 
            match token with
            | :? EofOfToken -> break_cond <- true
            | _ -> 
                token <- this.next_token()
        
        let ln : string = string(token.line_num)
        let en : string = string(this.get_error_count())
            
        let m : Message = {msg_type = SOURCE_LINE ; body = MSGS [ln ;en]}
        base.send_message(m)
         
[<Class>]
type PascalScanner(source : Source) = 
    inherit Scanner(source)
        
    override this.extra_token() =
        let cc = this.currnet_char()
        match cc with 
        | EOF -> EofOfToken(base.source) :> Token
        | _ -> Token(base.source)
        
