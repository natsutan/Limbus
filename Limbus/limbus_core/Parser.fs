module Parser

open Token
open Scanner

[<AbstractClass>]
type Parser(scanner : Scanner) = 
    member this.symTab = null 
    member this.iCode = null 
    member this.scanner = scanner 
    
    abstract member parse : unit
    abstract member get_error_count : int
    
    member this.current_token() : Token = this.scanner.cuurent_token()
        
    member this.next_token() : Token = this.scanner.next_token()
    