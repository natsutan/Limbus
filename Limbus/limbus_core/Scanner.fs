module Scanner
open Token

[<Class>]
type Scanner() =
    member this.cuurent_token() : Token = { Val = "aa" }
    
    member this.next_token() : Token = { Val = "aa" }
    