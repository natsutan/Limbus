module CodeGenerator

open common

[<Class>]
type CodeGenerator(iCode : iCode, symTab : SymTab) = 
    let mutable iCode = iCode
    let mutable symTab = symTab
    member val instruction_count = 0 with set, get
    
    member this.lprocess( iCode : iCode, symTab : SymTab) : unit =
        this.instruction_count <- 0
        //sendmessage
        let m = 
        1 |> ignore
        
     
    