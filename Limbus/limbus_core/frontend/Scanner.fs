module Scanner
open System.Runtime.CompilerServices
open Token
open Source

[<AbstractClass>]
type Scanner(source : Source) =
    class
        let mutable current_token : Token = EodOfToken  (source) :> Token
    
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